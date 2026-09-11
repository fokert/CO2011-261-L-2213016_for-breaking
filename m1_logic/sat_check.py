"""
M1 Logic: SAT Checker

Uses python-sat (pysat) Glucose3 solver to check satisfiability and extract models/cores.
"""

from typing import List, Dict, Tuple, Optional
try:
    from pysat.solvers import Glucose3
    from pysat.formula import CNF
except ImportError:
    print("ERROR: python-sat not installed. Run: pip install python-sat")
    raise


class SATChecker:
    """Wraps python-sat solver for CNF feasibility checking."""
    
    def __init__(self, clauses: List[List[int]], var_map: Dict, inv_map: Dict):
        """
        clauses: list of clauses (each is list of ints, positive/negative var IDs)
        var_map: (i, j) -> var_id
        inv_map: var_id -> (i, j)
        """
        self.clauses = clauses
        self.var_map = var_map
        self.inv_map = inv_map
        self.num_vars = len(var_map)
        self.solver = None
    
    def check_sat(self) -> Tuple[bool, Optional[Dict]]:
        """
        Check satisfiability.
        Returns: (is_sat, model_dict)
        
        If SAT: model_dict = {(i, j): True/False}
        If UNSAT: model_dict = None
        """
        # Create CNF object and solver
        cnf = CNF(from_clauses=self.clauses)
        solver = Glucose3(bootstrap_with=cnf)
        
        is_sat = solver.solve()
        
        if is_sat:
            model = solver.get_model()
            # model is list of signed ints; convert to dict
            model_dict = {}
            for var_id in self.inv_map:
                i, j = self.inv_map[var_id]
                model_dict[(i, j)] = (var_id in model)  # True if present (positive literal)
            solver.delete()
            return True, model_dict
        else:
            solver.delete()
            return False, None
    
    def get_unsat_core(self) -> Optional[List[List[int]]]:
        """
        Get minimal unsatisfiable core (subset of clauses that is unsat).
        Returns list of clauses, or None if SAT.
        """
        cnf = CNF(from_clauses=self.clauses)
        solver = Glucose3(bootstrap_with=cnf)
        
        is_sat = solver.solve()
        
        if not is_sat:
            core = solver.get_core()
            solver.delete()
            return core
        else:
            solver.delete()
            return None
    
    def print_summary(self):
        """Print solver summary."""
        print(f"SAT Checker:")
        print(f"  Clauses: {len(self.clauses)}")
        print(f"  Variables: {self.num_vars}")


def check_toy_instance():
    """Demo: check toy instance from spec."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from m1_logic.toy_instance import toy_instance_to_cnf
    
    clauses, var_map, inv_map = toy_instance_to_cnf()
    
    print("=== Toy Instance SAT Check ===")
    print(f"Clauses: {clauses}")
    print(f"Expected: a1=False, a2=True")
    
    checker = SATChecker(clauses, var_map, inv_map)
    is_sat, model = checker.check_sat()
    
    if is_sat:
        print(f"\n✓ SAT")
        print(f"  Model:")
        for (i, j), val in model.items():
            print(f"    {i}, {j}: {val}")
    else:
        print(f"\n✗ UNSAT")
        core = checker.get_unsat_core()
        print(f"  Minimal core: {core}")


if __name__ == "__main__":
    check_toy_instance()
