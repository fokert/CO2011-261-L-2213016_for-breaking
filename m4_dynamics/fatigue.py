"""
M4 Dynamics: Discrete Dynamical Systems

Direction A (Closed-loop rolling-horizon fatigue):

Recurrence: F[n+1] = a*F[n] + b*load[n] - r*rest[n]

where:
  F[n] = fatigue level at week n
  load[n] = number of shifts assigned in week n
  rest[n] = rest factor (estimated from availability)
  0 < a < 1 = decay rate (fatigue decreases over time)
  b = load multiplier
  r = rest multiplier

Fixed point (equilibrium): F* = (b*load̄ - r*rest̄) / (1 - a)
Stability: stable iff |a| < 1
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple


class FatigueRecurrence:
    """
    Discrete dynamical system for fatigue over weeks.
    """
    
    def __init__(self, a: float, b: float, r: float):
        """
        Initialize recurrence parameters.
        
        a: decay rate (0 < a < 1)
        b: load multiplier
        r: rest multiplier
        """
        self.a = a
        self.b = b
        self.r = r
    
    def step(self, F_n: float, load_n: float, rest_n: float = 0) -> float:
        """
        Execute one iteration: F[n+1] = a*F[n] + b*load[n] - r*rest[n]
        """
        return self.a * F_n + self.b * load_n - self.r * rest_n
    
    def compute_equilibrium(self, load_mean: float, rest_mean: float = 0) -> float:
        """
        Compute fixed point: F* = (b*load̄ - r*rest̄) / (1 - a)
        """
        if abs(1 - self.a) < 1e-10:
            return float('inf')  # Non-unique or unbounded
        return (self.b * load_mean - self.r * rest_mean) / (1 - self.a)
    
    def is_stable(self) -> bool:
        """Check stability: |a| < 1"""
        return abs(self.a) < 1
    
    def simulate(self, loads: list, initial_F: float = 0, rest_values: list = None) -> Dict:
        """
        Simulate the recurrence over a sequence of weeks.
        
        loads: list of load values for each week
        initial_F: F[0]
        rest_values: list of rest values (default: 0 for all weeks)
        
        Returns: dict with trajectory, equilibrium, stability info
        """
        if rest_values is None:
            rest_values = [0] * len(loads)
        
        trajectory = [initial_F]
        F = initial_F
        
        for load, rest in zip(loads, rest_values):
            F = self.step(F, load, rest)
            trajectory.append(F)
        
        # Compute equilibrium
        load_mean = np.mean(loads) if loads else 0
        rest_mean = np.mean(rest_values) if rest_values else 0
        F_star = self.compute_equilibrium(load_mean, rest_mean)
        
        return {
            "trajectory": trajectory,
            "equilibrium": F_star,
            "stable": self.is_stable(),
            "decay_rate": self.a,
            "a": self.a,
            "b": self.b,
            "r": self.r,
        }


def estimate_weekly_loads(df_clean: pd.DataFrame) -> Tuple[list, list]:
    """
    Estimate weekly workload for each week in the dataset.
    
    Returns: (weeks, loads)
      weeks: list of week numbers
      loads: list of average load per invigilator per week
    """
    # Group by week
    df_clean["week"] = df_clean["date"].dt.isocalendar().week
    
    weekly_counts = df_clean.groupby(["week"]).size()
    n_invigilators = df_clean["invigilator_id"].nunique()
    
    # Average load per invigilator per week
    weeks = sorted(weekly_counts.index)
    loads = [weekly_counts[w] / n_invigilators for w in weeks]
    
    return weeks, loads


def fit_parameters_from_data(df_clean: pd.DataFrame) -> Tuple[float, float, float]:
    """
    Fit fatigue recurrence parameters (a, b, r) from data.
    
    ASSUMPTION: Simplified fit using heuristics:
      - a = 0.75 (reasonable decay rate)
      - b = 1.0 (load multiplier = 1)
      - r = 0.2 (small rest effect)
    
    Full implementation would use least-squares optimization, but for demo this suffices.
    """
    weeks, loads = estimate_weekly_loads(df_clean)
    
    # Fixed heuristic parameters
    a = 0.75  # Decay: fatigue decreases 25% each week
    b = 1.0   # Each shift adds 1 unit of fatigue
    r = 0.2   # Rest removes small amount (could be 0 for simplicity)
    
    print(f"Fitted parameters (heuristic): a={a}, b={b}, r={r}")
    return a, b, r


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from data.loader import load_full_data
    
    df_clean, params, seed = load_full_data()
    
    # Fit parameters
    a, b, r = fit_parameters_from_data(df_clean)
    
    # Create recurrence
    rec = FatigueRecurrence(a, b, r)
    
    # Simulate
    weeks, loads = estimate_weekly_loads(df_clean)
    result = rec.simulate(loads, initial_F=0)
    
    print(f"\nSimulation result:")
    print(f"  Equilibrium: F* = {result['equilibrium']:.2f}")
    print(f"  Stable: {result['stable']}")
    print(f"  Final fatigue (week {len(loads)}): {result['trajectory'][-1]:.2f}")
    print(f"  Trajectory length: {len(result['trajectory'])}")
