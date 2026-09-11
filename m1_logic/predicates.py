"""
M1 Logic: Predicates & Hard Rules

Implements the predicates and hard rules from the specification.
All predicates are pure functions over the dataset.

Hard rules:
1. Assign(i,j): invigilator i assigned to shift j
2. Busy(i,j): invigilator i is busy (unavailable) at shift j
3. Overlap(j,k): shifts j and k overlap (cannot assign same person)
4. AtCampus(j,c): shift j is at campus c
5. Prefer(i,c): invigilator i prefers campus c
"""

import pandas as pd
from typing import Dict, Set, Tuple


class PredicateEvaluator:
    """
    Evaluates predicates over the dataset.
    """
    
    def __init__(self, df_clean: pd.DataFrame, params: dict):
        """
        df_clean: cleaned dataset with columns [shift_id, invigilator_id, campus, ...]
        params: dict with I, J, C, capacity, campus
        """
        self.df = df_clean
        self.I = params["I"]
        self.J = params["J"]
        self.C = params["C"]
        self.capacity = params["capacity"]
        self.campus = params["campus"]
        
        # Build baseline assignments (who is actually assigned in the dataset)
        self.baseline_assign = set()
        for _, row in df_clean.iterrows():
            self.baseline_assign.add((row["invigilator_id"], row["shift_id"]))
    
    def Assign(self, i: str, j: str) -> bool:
        """Invigilator i is assigned to shift j (baseline truth)."""
        return (i, j) in self.baseline_assign
    
    def Busy(self, i: str, j: str) -> bool:
        """Invigilator i is busy at shift j (unavailable).
        
        For baseline data, this is implicit: if someone was NOT assigned
        to any shift at time t, they might be busy. For simplicity in this
        demo, we assume Busy(i,j) = False for all (it's a hard constraint
        that must be respected in the solver, not a predicate on baseline).
        
        ASSUMPTION: No explicit busy/unavailable info in dataset; we assume
        all invigilators in the dataset can work all shifts they're assigned to.
        """
        return False
    
    def Overlap(self, j1: str, j2: str) -> bool:
        """Shifts j1 and j2 overlap (cannot have same invigilator).
        
        Two shifts overlap if they happen on the same day+time slot.
        """
        j1_data = self.df[self.df["shift_id"] == j1].iloc[0]
        j2_data = self.df[self.df["shift_id"] == j2].iloc[0]
        
        # Same date + same slot → overlap
        return (j1_data["date"] == j2_data["date"] and 
                j1_data["slot"] == j2_data["slot"])
    
    def AtCampus(self, j: str, c: str) -> bool:
        """Shift j is at campus c."""
        return self.campus.get(j) == c
    
    def Prefer(self, i: str, c: str) -> bool:
        """Invigilator i prefers campus c.
        
        ASSUMPTION: Not tracked in baseline dataset; implemented as soft
        constraint in M2 (not as hard logic rule). For now, return False.
        """
        return False
    
    def get_overlap_pairs(self) -> Set[Tuple[str, str]]:
        """Return all (j1, j2) pairs where j1 < j2 and they overlap."""
        pairs = set()
        for j1 in self.J:
            for j2 in self.J:
                if j1 < j2 and self.Overlap(j1, j2):
                    pairs.add((j1, j2))
        return pairs
    
    def get_busy_pairs(self) -> Set[Tuple[str, str]]:
        """Return all (i, j) pairs where i is busy at j (baseline: empty)."""
        return set()
    
    def print_summary(self):
        """Print summary of predicates."""
        overlaps = self.get_overlap_pairs()
        print(f"Predicates summary:")
        print(f"  |I| = {len(self.I)}, |J| = {len(self.J)}, |C| = {len(self.C)}")
        print(f"  Overlapping shift pairs: {len(overlaps)}")
        print(f"  Baseline assignments: {len(self.baseline_assign)}")


if __name__ == "__main__":
    # Test on full dataset
    from data.loader import load_full_data
    df_clean, params, seed = load_full_data()
    
    pred = PredicateEvaluator(df_clean, params)
    pred.print_summary()
    
    # Test a few predicates
    if params["I"]:
        i = params["I"][0]
        j = params["J"][0]
        print(f"\nSample predicates:")
        print(f"  Assign({i}, {j}) = {pred.Assign(i, j)}")
        print(f"  Busy({i}, {j}) = {pred.Busy(i, j)}")
        print(f"  Overlap({j}, {params['J'][1] if len(params['J']) > 1 else j}) = {pred.Overlap(j, params['J'][1] if len(params['J']) > 1 else j)}")
        if params["C"]:
            c = params["C"][0]
            print(f"  AtCampus({j}, {c}) = {pred.AtCampus(j, c)}")
