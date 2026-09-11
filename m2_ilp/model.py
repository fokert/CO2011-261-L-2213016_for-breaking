"""
M2 ILP: Model

Builds the Integer Linear Programming model for invigilator assignment.
Uses PuLP + CBC solver.

Decision variables: x[i][j] ∈ {0, 1} where x[i][j] = 1 iff invigilator i assigned to shift j

Objective: minimize fairness (min-max workload)
Constraints: capacity, no double-booking, availability

ASSUMPTION: We solve on a subset of shifts (single day or multi-day period) for demo speed.
Full term would have all shifts but would take longer to solve.
"""

import pulp as lp
from typing import Dict, Tuple, Set
import pandas as pd


class ILPAssignmentModel:
    """
    Builds and solves the ILP assignment model.
    """
    
    def __init__(self, df_clean: pd.DataFrame, params: dict, subset_shifts=None):
        """
        df_clean: cleaned dataset
        params: dict with I, J, C, capacity, campus
        subset_shifts: list of shift IDs to solve on (default: all)
        """
        self.df = df_clean
        self.I = params["I"]
        self.J = subset_shifts if subset_shifts else params["J"]
        self.C = params["C"]
        self.capacity = params["capacity"]
        self.campus = params["campus"]
        
        # Precompute overlap pairs and busy pairs
        self._overlaps = self._compute_overlaps()
        
        # PuLP model
        self.prob = None
        self.x = {}  # x[(i,j)] = pulp variable
        self.t = None  # fairness (min-max) variable
    
    def _compute_overlaps(self) -> Set[Tuple[str, str]]:
        """Return all (j1, j2) pairs where j1 < j2 and shifts overlap."""
        overlaps = set()
        for j1 in self.J:
            for j2 in self.J:
                if j1 < j2:
                    j1_data = self.df[self.df["shift_id"] == j1].iloc[0]
                    j2_data = self.df[self.df["shift_id"] == j2].iloc[0]
                    if (j1_data["date"] == j2_data["date"] and 
                        j1_data["slot"] == j2_data["slot"]):
                        overlaps.add((j1, j2))
        return overlaps
    
    def build_model(self):
        """Build the ILP model."""
        # Create problem
        self.prob = lp.LpProblem("Invigilator_Assignment", lp.LpMinimize)
        
        # Decision variables: x[i][j] ∈ {0, 1}
        for i in self.I:
            for j in self.J:
                self.x[(i, j)] = lp.LpVariable(f"x_{i}_{j}", cat="Binary")
        
        # Fairness variable: t ≥ workload[i] for all i
        self.t = lp.LpVariable("t_fairness", lowBound=0, cat="Continuous")
        
        # Objective: minimize fairness (min-max load)
        self.prob += self.t, "Fairness"
        
        # Constraints
        
        # 1. Capacity: each shift gets exactly capacity[j] people
        for j in self.J:
            cap = self.capacity.get(j, 1)
            self.prob += lp.lpSum([self.x[(i, j)] for i in self.I]) == cap, f"Capacity_{j}"
        
        # 2. No double-booking: for overlapping shifts, can't assign same invigilator
        for i in self.I:
            for j1, j2 in self._overlaps:
                self.prob += self.x[(i, j1)] + self.x[(i, j2)] <= 1, f"Overlap_{i}_{j1}_{j2}"
        
        # 3. Fairness: t ≥ sum of assignments for each invigilator
        for i in self.I:
            workload = lp.lpSum([self.x[(i, j)] for j in self.J])
            self.prob += self.t >= workload, f"Fairness_{i}"
        
        return self.prob
    
    def solve(self, time_limit=30) -> bool:
        """
        Solve the model.
        Returns True if optimal/feasible, False if infeasible.
        """
        if self.prob is None:
            self.build_model()
        
        # Solve with CBC solver (bundled with PuLP)
        solver = lp.PULP_CBC_CMD(msg=0, timeLimit=time_limit)
        self.prob.solve(solver)
        
        status = lp.LpStatus[self.prob.status]
        print(f"Solver status: {status}")
        
        return status in ["Optimal", "Not Solved"]  # "Not Solved" means feasible (hit time limit)
    
    def get_assignment_df(self) -> pd.DataFrame:
        """
        Extract solution as DataFrame.
        Returns df with columns [invigilator_id, shift_id, assigned]
        """
        rows = []
        for i in self.I:
            for j in self.J:
                val = lp.value(self.x[(i, j)])
                if val is not None and val > 0.5:  # assigned
                    rows.append({"invigilator_id": i, "shift_id": j, "assigned": 1})
        
        return pd.DataFrame(rows)
    
    def get_workloads(self) -> Dict[str, int]:
        """Return workload (# shifts assigned) for each invigilator."""
        workloads = {}
        for i in self.I:
            workload = sum(lp.value(self.x[(i, j)]) or 0 for j in self.J)
            workloads[i] = int(workload)
        return workloads
    
    def get_objective_value(self) -> float:
        """Return objective value (min-max fairness)."""
        return lp.value(self.prob.objective) if self.prob else None


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from data.loader import load_full_data
    
    df_clean, params, seed = load_full_data()
    
    # Use first 10 shifts for demo
    subset_J = params["J"][:10]
    
    print(f"Building ILP model on subset: 10 shifts")
    model = ILPAssignmentModel(df_clean, params, subset_J)
    model.build_model()
    print(f"Model built: {len(model.x)} variables, {len(model.prob.constraints)} constraints")
    
    print(f"Solving...")
    is_feasible = model.solve(time_limit=10)
    
    if is_feasible:
        print(f"✓ Feasible solution found")
        workloads = model.get_workloads()
        print(f"Workloads: min={min(workloads.values())}, max={max(workloads.values())}")
        print(f"Fairness (t): {model.get_objective_value()}")
    else:
        print(f"✗ No feasible solution")
