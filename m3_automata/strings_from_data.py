"""
M3 Automata: Schedule Strings

Convert each invigilator's actual schedule from the dataset into a string over Σ = {M, A, N, -}.

One symbol per day:
- M: morning shift
- A: afternoon shift
- N: night shift
- -: off (no shift that day)

If multiple shifts in one day, take the latest (priority N > A > M).
"""

import pandas as pd
from typing import Dict, Set


def build_schedule_strings(df_clean: pd.DataFrame) -> Dict[str, str]:
    """
    Build schedule string for each invigilator.
    
    Returns: dict {invigilator_id -> string over {M, A, N, -}}
    """
    # Group by invigilator and date
    grouped = df_clean.groupby(["invigilator_id", "date"]).agg({
        "slot": lambda x: max(x, key=lambda s: {"M": 0, "A": 1, "N": 2, "-": 0}.get(s, 0))
        if list(x) else "-"
    }).reset_index()
    
    # Build string for each invigilator
    strings = {}
    for inv_id, group_inv in grouped.groupby("invigilator_id"):
        # Sort by date
        group_inv = group_inv.sort_values("date")
        # Build string
        string = "".join(group_inv["slot"].tolist())
        strings[inv_id] = string
    
    return strings


def print_sample_strings(df_clean: pd.DataFrame, n_samples: int = 5):
    """Print sample schedule strings."""
    strings = build_schedule_strings(df_clean)
    
    print(f"Sample schedule strings (Σ = {{M, A, N, -}}):")
    for inv_id, string in list(strings.items())[:n_samples]:
        # Shorten for display
        if len(string) > 50:
            string_disp = string[:50] + f"... (len={len(string)})"
        else:
            string_disp = string
        print(f"  {inv_id}: {string_disp}")
    
    return strings


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from data.loader import load_full_data
    
    df_clean, params, seed = load_full_data()
    print_sample_strings(df_clean, n_samples=10)
