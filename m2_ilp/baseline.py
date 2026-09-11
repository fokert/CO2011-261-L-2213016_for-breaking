"""
M2 ILP: Baseline

Computes fairness metric of the baseline (actual) assignment from dataset.
This is what we're trying to beat.
"""

import pandas as pd
from typing import Dict


def compute_baseline_workload(df_clean: pd.DataFrame) -> Dict[str, int]:
    """
    Compute workload (# shifts assigned) for each invigilator in baseline.
    """
    workload = df_clean.groupby("invigilator_id").size().to_dict()
    return workload


def compute_fairness_metric(workloads: Dict[str, int]) -> Dict:
    """
    Compute fairness metrics from workload dict.
    
    Returns dict with:
      - min: minimum workload
      - max: maximum workload
      - mean: average workload
      - variance: workload variance
      - spread: max - min
    """
    if not workloads:
        return {}
    
    vals = list(workloads.values())
    min_load = min(vals)
    max_load = max(vals)
    mean_load = sum(vals) / len(vals)
    variance = sum((v - mean_load) ** 2 for v in vals) / len(vals)
    spread = max_load - min_load
    
    return {
        "min": min_load,
        "max": max_load,
        "mean": mean_load,
        "variance": variance,
        "spread": spread,
    }


def print_baseline_summary(df_clean: pd.DataFrame):
    """Print baseline fairness summary."""
    workload = compute_baseline_workload(df_clean)
    fairness = compute_fairness_metric(workload)
    
    print("Baseline Fairness Metrics:")
    for key, val in fairness.items():
        print(f"  {key}: {val:.2f}")
    
    return workload, fairness


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from data.loader import load_full_data
    
    df_clean, params, seed = load_full_data()
    print_baseline_summary(df_clean)
