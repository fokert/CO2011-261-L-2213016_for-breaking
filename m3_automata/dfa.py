"""
M3 Automata: DFA

Simple DFA implementation for defining and running temporal rules.

A DFA is defined by:
- alphabet Σ
- states Q
- start state q0
- accepting states F ⊆ Q
- transition function δ: Q × Σ → Q
"""

from typing import Set, Dict, Tuple
import json


class DFA:
    """Simple Deterministic Finite Automaton."""
    
    def __init__(self, states: Set[str], alphabet: Set[str], start: str, 
                 accepting: Set[str], transitions: Dict[Tuple[str, str], str]):
        """
        states: set of state names
        alphabet: set of symbols
        start: start state
        accepting: set of accepting states
        transitions: dict {(state, symbol) -> next_state}
        """
        self.states = states
        self.alphabet = alphabet
        self.start = start
        self.accepting = accepting
        self.transitions = transitions
    
    def run(self, string: str) -> bool:
        """
        Run the DFA on a string. Return True if accepted, False if rejected.
        """
        current = self.start
        for symbol in string:
            if symbol not in self.alphabet:
                return False  # reject on unknown symbol
            key = (current, symbol)
            if key not in self.transitions:
                return False  # no transition defined
            current = self.transitions[key]
        
        return current in self.accepting
    
    def to_dict(self) -> dict:
        """Export DFA to dict format (for JSON serialization)."""
        trans_list = []
        for (state, symbol), next_state in self.transitions.items():
            trans_list.append({
                "from": state,
                "on": symbol,
                "to": next_state,
            })
        
        return {
            "states": sorted(list(self.states)),
            "alphabet": sorted(list(self.alphabet)),
            "start": self.start,
            "accepting": sorted(list(self.accepting)),
            "transitions": trans_list,
        }
    
    @staticmethod
    def from_dict(d: dict) -> "DFA":
        """Load DFA from dict format."""
        states = set(d["states"])
        alphabet = set(d["alphabet"])
        start = d["start"]
        accepting = set(d["accepting"])
        
        transitions = {}
        for trans in d["transitions"]:
            transitions[(trans["from"], trans["on"])] = trans["to"]
        
        return DFA(states, alphabet, start, accepting, transitions)
    
    def save_json(self, filepath: str):
        """Save DFA to JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @staticmethod
    def load_json(filepath: str) -> "DFA":
        """Load DFA from JSON file."""
        with open(filepath, "r") as f:
            d = json.load(f)
        return DFA.from_dict(d)
    
    def __str__(self):
        return f"DFA(|Q|={len(self.states)}, |Σ|={len(self.alphabet)}, |F|={len(self.accepting)})"


def create_dfa_no_2_consecutive() -> DFA:
    """
    Rule: "No more than 2 consecutive working days"
    Alphabet: Σ = {W, -}  (W = working, - = off)
    
    Worked example from brief:
    States: q0, q1, q2 (current run of 0, 1, 2 working days) + dead state
    Transitions:
      q0 -W-> q1 -W-> q2 -W-> dead
      q0 ---> q0, q1 ---> q0, q2 ---> q0
    Accepting: {q0, q1, q2}
    
    Accepts: WW-WW, rejects: WWW
    """
    states = {"q0", "q1", "q2", "dead"}
    alphabet = {"W", "-"}
    start = "q0"
    accepting = {"q0", "q1", "q2"}
    
    transitions = {
        ("q0", "W"): "q1",
        ("q0", "-"): "q0",
        ("q1", "W"): "q2",
        ("q1", "-"): "q0",
        ("q2", "W"): "dead",
        ("q2", "-"): "q0",
        ("dead", "W"): "dead",
        ("dead", "-"): "dead",
    }
    
    return DFA(states, alphabet, start, accepting, transitions)


def create_dfa_night_rest() -> DFA:
    """
    Rule: "A night shift is followed by a rest day"
    Alphabet: Σ = {M, A, N, -}  (Morning, Afternoon, Night, off)
    
    States: normal, after_night
    Transitions:
      - From 'normal': N -> after_night, else -> normal
      - From 'after_night': - -> normal, else -> dead (error: no rest after night)
    Accepting: {normal}
    """
    states = {"normal", "after_night", "dead"}
    alphabet = {"M", "A", "N", "-"}
    start = "normal"
    accepting = {"normal"}
    
    transitions = {
        ("normal", "M"): "normal",
        ("normal", "A"): "normal",
        ("normal", "N"): "after_night",
        ("normal", "-"): "normal",
        ("after_night", "-"): "normal",
        ("after_night", "M"): "dead",
        ("after_night", "A"): "dead",
        ("after_night", "N"): "dead",
        ("dead", "M"): "dead",
        ("dead", "A"): "dead",
        ("dead", "N"): "dead",
        ("dead", "-"): "dead",
    }
    
    return DFA(states, alphabet, start, accepting, transitions)


def create_dfa_rolling_window(k: int = 3) -> DFA:
    """
    Rule: "At most k shifts in any rolling 7-day window"
    
    ASSUMPTION: For demo, we implement a simplified version using a counter.
    A proper DFA would need states for each possible count (0..k), which grows linearly.
    For full implementation, use specialized constraint in ILP (not as DFA).
    
    Here, return a trivial DFA that accepts all strings (placeholder).
    In M3.3, this would be converted to ILP constraint directly.
    """
    states = {"q0"}
    alphabet = {"M", "A", "N", "-"}
    start = "q0"
    accepting = {"q0"}
    transitions = {
        (s, a): "q0" for s in states for a in alphabet
    }
    return DFA(states, alphabet, start, accepting, transitions)


if __name__ == "__main__":
    # Test DFAs
    print("=== Testing DFAs ===\n")
    
    # Test 1: No 2 consecutive working days
    dfa1 = create_dfa_no_2_consecutive()
    print(f"DFA 1: {dfa1}")
    print(f"  Accept 'WW-WW': {dfa1.run('WW-WW')}")  # Should be True
    print(f"  Reject 'WWW': {dfa1.run('WWW')}")      # Should be False
    
    # Test 2: Night followed by rest
    dfa2 = create_dfa_night_rest()
    print(f"\nDFA 2: {dfa2}")
    print(f"  Accept 'MN-AM': {dfa2.run('MN-AM')}")  # Should be True
    print(f"  Reject 'MNA': {dfa2.run('MNA')}")      # Should be False
    
    # Export to JSON
    dfa1.save_json("m3_automata/dfa_no2cons_sample.json")
    print(f"\n✓ Saved DFA to JSON")
