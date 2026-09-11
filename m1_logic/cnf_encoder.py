"""
M1 Logic: CNF Encoder

Encodes hard rules from dataset into CNF clauses for SAT solver.

Hard rules (from brief):
1. No double-booking: ∀i∀j∀k (Overlap(j,k) ∧ Assign(i,j) → ¬Assign(i,k))
2. Availability: ∀i∀j (Busy(i,j) → ¬Assign(i,j))
3. Capacity: ∀j (exactly capacity[j] people assigned to shift j)

For efficiency and demo, we encode a SMALL SLICE of the data, not the full dataset.
"""

from typing import List, Dict, Tuple, Set


class CNFEncoder:
    """Encodes FOL rules to CNF clauses for SAT solver."""
    
    def __init__(self, predicates: PredicateEvaluator, subset_I=None, subset_J=None):
        """
        predicates: PredicateEvaluator instance
        subset_I: list of invigilators to include (for demo, use subset)
        subset_J: list of shifts to include (for demo, use subset)
        """
        self.pred = predicates
        self.I = subset_I if subset_I else predicates.I
        self.J = subset_J if subset_J else predicates.J
        
        # Variable numbering: assign unique int > 0 to each Assign(i,j)
        self.var_counter = 1
        self.var_map = {}  # (i, j) -> var_id
        self.inv_map = {}  # var_id -> (i, j)
        self._build_var_map()
    
    def _build_var_map(self):
        """Assign variable IDs to all Assign(i, j) propositions."""
        for i in self.I:
            for j in self.J:
                self.var_map[(i, j)] = self.var_counter
                self.inv_map[self.var_counter] = (i, j)
                self.var_counter += 1
    
    def _get_var(self, i: str, j: str) -> int:
        """Get variable ID for Assign(i, j)."""
        return self.var_map.get((i, j), None)
    
    def encode_hard_rules(self) -> List[List[int]]:
        """Encode all hard rules into CNF clauses."""
        clauses = []
        
        # Rule 1: No double-booking
        # ∀i∀j∀k (Overlap(j,k) → (¬Assign(i,j) ∨ ¬Assign(i,k)))
        for i in self.I:
            overlaps = []
            for j1 in self.J:
                for j2 in self.J:
                    if j1 < j2 and self.pred.Overlap(j1, j2):
                        overlaps.append((j1, j2))
            
            for j1, j2 in overlaps:
                var_j1 = self._get_var(i, j1)
                var_j2 = self._get_var(i, j2)
                if var_j1 and var_j2:
                    # ¬Assign(i,j1) ∨ ¬Assign(i,j2) = [-var_j1, -var_j2]
                    clauses.append([-var_j1, -var_j2])
        
        # Rule 2: Availability (Busy → ¬Assign)
        # ∀i∀j (Busy(i,j) → ¬Assign(i,j))
        for i in self.I:
            for j in self.J:
                if self.pred.Busy(i, j):
                    var_ij = self._get_var(i, j)
                    if var_ij:
                        clauses.append([-var_ij])  # ¬Assign(i,j)
        
        # Rule 3: Capacity (at-least and at-most)
        # ∀j (exactly capacity[j] people assigned)
        for j in self.J:
            cap = self.pred.capacity.get(j, 1)
            
            # At-least: ORing all Assign(i,j) for i in I
            at_least_clause = [self._get_var(i, j) for i in self.I if self._get_var(i, j)]
            if at_least_clause:
                clauses.append(at_least_clause)
            
            # At-most (simplified for demo): if cap < |I|, add pairwise ¬(Assign(i1,j) ∧ Assign(i2,j))
            # Full cardinality constraints would need O(|I|^cap) clauses; we skip for demo.
            # ASSUMPTION: Keep it simple; assume capacity is ~2-3 people/shift in baseline.
            if cap <= 3:
                for idx1, i1 in enumerate(self.I):
                    for i2 in self.I[idx1+1:]:
                        var_i1j = self._get_var(i1, j)
                        var_i2j = self._get_var(i2, j)
                        if var_i1j and var_i2j and cap == 1:
                            # At most 1: ¬(a ∧ b) = ¬a ∨ ¬b
                            clauses.append([-var_i1j, -var_i2j])
        
        return clauses
    
    def print_summary(self):
        """Print encoding summary."""
        print(f"CNF Encoder summary:")
        print(f"  Subset: |I|={len(self.I)}, |J|={len(self.J)}")
        print(f"  Total variables: {len(self.var_map)}")
        print(f"  Sample var_map (first 5): {dict(list(self.var_map.items())[:5])}")


if __name__ == "__main__":
    from data.loader import load_full_data
    
    # Load full data
    df_clean, params, seed = load_full_data()
    pred = PredicateEvaluator(df_clean, params)
    
    # Demo on small subset for speed
    subset_I = pred.I[:3]  # 3 invigilators
    subset_J = pred.J[:4]  # 4 shifts
    
    encoder = CNFEncoder(pred, subset_I, subset_J)
    clauses = encoder.encode_hard_rules()
    
    print(f"Encoded {len(clauses)} clauses from hard rules")
    encoder.print_summary()
    print(f"First 5 clauses: {clauses[:5]}")
