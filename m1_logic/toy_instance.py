"""
M1 Logic: Toy Instance (worked example from brief)

Two invigilators {CB1, CB2}, one shift s needing exactly one person;
CB1 is busy at s. Rules:
  - Busy(CB1, s) → ¬Assign(CB1, s)
  - Exactly one assigned per shift
  
Expected SAT result: a1=0, a2=1 (CB2 assigned, CB1 not)
"""

def get_toy_instance():
    """Return toy instance as dict with I, J, capacity, busy constraints."""
    return {
        "I": ["CB1", "CB2"],
        "J": ["s"],
        "capacity": {"s": 1},
        "busy": {("CB1", "s")},  # CB1 is busy at s
        "overlap": set(),  # No overlaps in this toy instance
    }


def get_toy_rules():
    """
    Return rules as logical statements in first-order logic.
    Translated to CNF for SAT solver.
    
    Hard rules:
    1. Busy(CB1, s) → ¬Assign(CB1, s)  [fact: CB1 is busy]
    2. Exactly 1 person assigned to s: Assign(CB1,s) ∨ Assign(CB2,s)
                                       ∧ ¬(Assign(CB1,s) ∧ Assign(CB2,s))
    """
    rules = {
        "busy_rule": "Busy(CB1, s) → ¬Assign(CB1, s)",
        "capacity_rule": "Assign(CB1, s) ∨ Assign(CB2, s)  ∧  ¬(Assign(CB1, s) ∧ Assign(CB2, s))",
    }
    return rules


def toy_instance_to_cnf():
    """
    Convert toy instance to CNF for SAT solver.
    
    Variables:
      a1 = Assign(CB1, s)
      a2 = Assign(CB2, s)
    
    Rules:
      1. ¬a1  (from Busy(CB1, s))
      2. a1 ∨ a2  (at least 1 assigned)
      3. ¬(a1 ∧ a2) = ¬a1 ∨ ¬a2  (at most 1 assigned)
    
    CNF: (¬a1) ∧ (a1 ∨ a2) ∧ (¬a1 ∨ ¬a2)
    
    For SAT solver (pysat): use integers 1..n for vars, negative for negation.
    a1 = 1, a2 = 2
    
    Clauses (as lists):
      [-1]           (¬a1)
      [1, 2]         (a1 ∨ a2)
      [-1, -2]       (¬a1 ∨ ¬a2)
    """
    clauses = [
        [-1],         # ¬a1: CB1 is busy
        [1, 2],       # a1 ∨ a2: at least one assigned
        [-1, -2],     # ¬a1 ∨ ¬a2: at most one assigned (exactly one)
    ]
    
    var_map = {"a1": 1, "a2": 2}
    inv_map = {1: "a1", 2: "a2"}
    
    return clauses, var_map, inv_map


if __name__ == "__main__":
    import json
    toy = get_toy_instance()
    print("Toy instance:")
    print(json.dumps(toy, indent=2, default=str))
    
    print("\nRules:")
    for rule_name, rule_expr in get_toy_rules().items():
        print(f"  {rule_name}: {rule_expr}")
    
    clauses, var_map, inv_map = toy_instance_to_cnf()
    print(f"\nCNF clauses (for pysat):")
    for i, clause in enumerate(clauses, 1):
        print(f"  C{i}: {clause}")
    print(f"\nVariable mapping: {var_map}")
