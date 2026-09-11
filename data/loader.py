"""
Data loader for IAP demo.
Reads raw dataset + seed; cleans and structures data for all 5 modules.

ASSUMPTION: Dataset schema is fixed as defined in spec:
- Columns: Ca thi, Ngày, GIỜ, MS Ca thi, Nhiệm vụ, MS của CÁN BỘ COI THI, Thời gian, Thứ, Cơ sở
- Filter: only rows with Nhiệm vụ containing 'CBCT' (invigilators only, not secretaries/chairs)
- Campus NA → "Không rõ", no self-assignment of preference
- Time slots inferred from GIỜ column: 07g00/09g30 → M, 13g00/15g30 → A, 18g15 → N, else → -
- Seed: read from data/seed.txt (one integer per line)
"""

import os
import pandas as pd
from pathlib import Path


def load_seed() -> int:
    """Read seed from data/seed.txt. If missing, return fallback + warn."""
    seed_path = Path(__file__).parent / "seed.txt"
    if seed_path.exists():
        with open(seed_path, "r") as f:
            try:
                seed = int(f.read().strip())
                print(f"[OK] Seed loaded: {seed}")
                return seed
            except ValueError:
                print(f"[WARN] seed.txt invalid, using fallback 42")
                return 42
    else:
        print(f"[WARN] seed.txt not found, using fallback 42")
        return 42


def load_raw_dataset(xlsx_path: str) -> pd.DataFrame:
    """Load raw dataset from Excel, return as-is."""
    df = pd.read_excel(xlsx_path, sheet_name="Sheet1")
    print(f"[OK] Raw dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    return df


def _map_hour_to_slot(hour_str: str) -> str:
    """Map GIỜ string (e.g., '07g00') to slot symbol (M/A/N/-)."""
    if pd.isna(hour_str):
        return "-"
    hour_str = str(hour_str).strip()
    # Extract hour part (before 'g')
    try:
        h = int(hour_str.split('g')[0])
    except (ValueError, IndexError):
        return "-"
    
    if h in [7, 9]:  # 07g00, 09g30
        return "M"
    elif h in [13, 15]:  # 13g00, 15g30
        return "A"
    elif h == 18:  # 18g15
        return "N"
    else:
        return "-"


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean dataset:
    - Filter only CBCT role (invigilators)
    - Rename columns to English for easier handling
    - Infer time slot
    - Handle missing campus
    - Return cleaned DataFrame
    """
    # ASSUMPTION: Keep only rows with CBCT in Nhiệm vụ
    df_clean = df[df["Nhiệm vụ"].str.contains("CBCT", na=False, case=False)].copy()
    print(f"[OK] Filtered CBCT only: {df_clean.shape[0]} rows (was {df.shape[0]})")
    
    # Rename columns to English (internal use)
    rename_map = {
        "Ca thi": "session_name",
        "Ngày": "date",
        "GIỜ": "hour",
        "MS Ca thi": "shift_id",
        "Nhiệm vụ": "role",
        "MS của CÁN BỘ COI THI": "invigilator_id",
        "Thời gian": "duration_min",
        "Thứ": "day_of_week",
        "Cơ sở": "campus",
    }
    df_clean = df_clean.rename(columns=rename_map)
    
    # Infer time slot from hour
    df_clean["slot"] = df_clean["hour"].apply(_map_hour_to_slot)
    
    # Handle missing campus
    df_clean["campus"] = df_clean["campus"].fillna("Không rõ")
    
    # Parse date to datetime
    df_clean["date"] = pd.to_datetime(df_clean["date"], errors="coerce")
    
    print(f"[OK] Cleaned: {df_clean.shape[0]} rows, columns: {list(df_clean.columns)}")
    return df_clean


def extract_sets_and_params(df_clean: pd.DataFrame) -> dict:
    """
    Extract sets I (invigilators), J (shifts), C (campuses) and basic parameters.
    Return dict with:
      I, J, C, capacity[j], campus[j], campus_actual[j] (for filtering None)
    """
    I = sorted(df_clean["invigilator_id"].unique())
    J = sorted(df_clean["shift_id"].unique())
    C = sorted([c for c in df_clean["campus"].unique() if c != "Không rõ"])
    
    # Capacity: count how many invigilators assigned per shift in baseline
    capacity = df_clean.groupby("shift_id").size().to_dict()
    
    # Campus mapping: shift -> campus (filter Không rõ)
    campus_map = df_clean[df_clean["campus"] != "Không rõ"].drop_duplicates("shift_id").set_index("shift_id")["campus"].to_dict()
    
    params = {
        "I": I,
        "J": J,
        "C": C,
        "capacity": capacity,
        "campus": campus_map,
        "n_invigilators": len(I),
        "n_shifts": len(J),
        "n_campuses": len(C),
    }
    print(f"[OK] Sets extracted: |I|={len(I)}, |J|={len(J)}, |C|={len(C)}")
    return params


def load_full_data(xlsx_path: str = None) -> tuple:
    """
    Complete pipeline: load raw, clean, extract sets/params.
    Returns: (df_clean, params, seed)
    """
    if xlsx_path is None:
        # Auto-find xlsx in data/
        data_dir = Path(__file__).parent
        xlsx_files = list(data_dir.glob("*.xlsx"))
        if not xlsx_files:
            raise FileNotFoundError("No .xlsx file found in data/")
        xlsx_path = str(xlsx_files[0])
    
    seed = load_seed()
    df_raw = load_raw_dataset(xlsx_path)
    df_clean = clean_dataset(df_raw)
    params = extract_sets_and_params(df_clean)
    
    return df_clean, params, seed


if __name__ == "__main__":
    # Quick test
    df_clean, params, seed = load_full_data()
    print(f"\nSummary:")
    print(f"  Seed: {seed}")
    print(f"  Shape: {df_clean.shape}")
    print(f"  Invigilators: {params['n_invigilators']}")
    print(f"  Shifts: {params['n_shifts']}")
    print(f"  Sample rows:\n{df_clean.head(3)}")
