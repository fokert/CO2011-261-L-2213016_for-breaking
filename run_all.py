#!/usr/bin/env python3
"""
run_all.py  -  THE single entry point for the CO2011 SEM261 assignment.

Grading runs exactly:  python run_all.py --seed $(cat data/seed.txt)
It must reproduce EVERY number in your report from a clean clone, with no manual steps.

MVP Implementation: Integrated demo with all 4 modules + Streamlit app.
"""
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from data.loader import load_full_data
from m1_logic.toy_instance import toy_instance_to_cnf
from m1_logic.sat_check import SATChecker
from m2_ilp.model import ILPAssignmentModel
from m2_ilp.baseline import compute_baseline_workload, compute_fairness_metric
from m3_automata.dfa import create_dfa_no_2_consecutive
from m3_automata.strings_from_data import build_schedule_strings
from m4_dynamics.fatigue import FatigueRecurrence, estimate_weekly_loads, fit_parameters_from_data


def run_m1(df_clean, params, seed):
    """M1 Logic: SAT feasibility checking."""
    print("\n" + "="*80)
    print("M1 — Logic Module: SAT Feasibility")
    print("="*80)
    
    # Test toy instance
    print("\n1. Toy Instance (from spec):")
    clauses, var_map, inv_map = toy_instance_to_cnf()
    print(f"   Clauses: {clauses}")
    print(f"   Variables: {var_map}")
    
    checker = SATChecker(clauses, var_map, inv_map)
    is_sat, model = checker.check_sat()
    print(f"   SAT Result: {is_sat}")
    if model:
        print(f"   Model: {dict(sorted((inv_map.get(k, k), v) for k, v in model.items())[:5])}")
    
    print("[OK] M1 Complete")


def run_m2(df_clean, params, seed):
    """M2 ILP: Solver & fairness optimization."""
    print("\n" + "="*80)
    print("M2 — ILP Module: Fairness Optimization")
    print("="*80)
    
    # Baseline fairness
    print("\n1. Baseline Fairness Metrics:")
    baseline_workload = compute_baseline_workload(df_clean)
    baseline_metrics = compute_fairness_metric(baseline_workload)
    print(f"   Min workload: {baseline_metrics['min']}")
    print(f"   Max workload: {baseline_metrics['max']}")
    print(f"   Mean: {baseline_metrics['mean']:.2f}")
    print(f"   Spread (max-min): {baseline_metrics['spread']}")
    
    # ILP solver on subset
    print("\n2. ILP Solver (subset of 10 shifts):")
    subset_shifts = params["J"][:10]  # First 10 shifts
    model = ILPAssignmentModel(df_clean, params, subset_shifts=subset_shifts)
    model.build_model()
    is_feasible = model.solve()
    if is_feasible:
        workloads = model.get_workloads()
        print(f"   Solution Status: Feasible/Optimal")
        print(f"   Min workload: {min(workloads.values())}")
        print(f"   Max workload: {max(workloads.values())}")
        print(f"   Fairness (t): {model.get_objective_value():.2f}")
    else:
        print(f"   Solution Status: Infeasible")
    
    print("[OK] M2 Complete")


def run_m3(df_clean, params, seed):
    """M3 Automata: DFA acceptance & temporal rules."""
    print("\n" + "="*80)
    print("M3 — Automata Module: Temporal Rules")
    print("="*80)
    
    # Build schedule strings
    print("\n1. Schedule Strings (Σ = {M, A, N, -}):")
    schedule_strings = build_schedule_strings(df_clean)
    print(f"   Total invigilators: {len(schedule_strings)}")
    if schedule_strings:
        sample_id = list(schedule_strings.keys())[0]
        print(f"   Sample (inv {sample_id}): {schedule_strings[sample_id][:50]}...")
    
    # Test DFA: No >2 consecutive working days
    print("\n2. DFA: No >2 Consecutive Working Days")
    dfa = create_dfa_no_2_consecutive()
    print(f"   DFA: |Q|={len(dfa.states)}, |Σ|={len(dfa.alphabet)}, |F|={len(dfa.accepting)}")
    
    # Test on sample schedules
    accepted_count = 0
    for inv_id, schedule in list(schedule_strings.items())[:10]:
        # Convert schedule to W/- (W=working, -=rest)
        binary_str = "".join("W" if c in "MAN" else "-" for c in schedule)
        if dfa.run(binary_str):
            accepted_count += 1
    print(f"   Acceptance rate (first 10): {accepted_count}/10")
    
    print("[OK] M3 Complete")


def run_m4(df_clean, params, seed):
    """M4 Dynamics: Fatigue recurrence & equilibrium."""
    print("\n" + "="*80)
    print("M4 — Dynamics Module: Fatigue Equilibrium")
    print("="*80)
    
    # Estimate loads and fit parameters
    print("\n1. Parameter Fitting:")
    weeks, loads = estimate_weekly_loads(df_clean)
    a, b, r = fit_parameters_from_data(df_clean)
    print(f"   Parameters: a={a}, b={b}, r={r}")
    print(f"   Stability (|a| < 1): {abs(a) < 1}")
    
    # Simulate dynamics
    print("\n2. Fatigue Dynamics Simulation:")
    fr = FatigueRecurrence(a, b, r)
    result = fr.simulate(loads=loads[:4], initial_F=5.0, rest_values=[0.5]*len(loads[:4]))
    
    print(f"   Equilibrium: F* = {result['equilibrium']:.2f}")
    print(f"   Final fatigue (week {len(result['trajectory'])-1}): {result['trajectory'][-1]:.2f}")
    print(f"   Stable: {result['stable']}")
    
    print("[OK] M4 Complete")


def run_m5(df_clean, params, seed):
    """M5 Integration: Web app (precompute caches)."""
    print("\n" + "="*80)
    print("M5 — Integration: Streamlit Web App Ready")
    print("="*80)
    print("\nStreamlit app is ready at: app/app.py")
    print("Launch with: streamlit run app/app.py")
    print("[OK] M5 Ready")


def main():
    ap = argparse.ArgumentParser(
        description="IAP Demo Entry Point",
        epilog="Usage: python run_all.py --seed 393817108 [--stage all|m1|m2|m3|m4|m5]"
    )
    ap.add_argument("--seed", type=int, required=True, help="from data/seed.txt")
    ap.add_argument("--stage", default="all",
                    choices=["all", "m1", "m2", "m3", "m4", "m5"])
    a = ap.parse_args()

    print(f"[run_all] seed={a.seed} stage={a.stage}")
    
    # Load data once
    print("\nLoading data...")
    df_clean, params, loaded_seed = load_full_data()
    print(f"[OK] Data loaded: {len(df_clean)} rows, {len(params)} params, seed={loaded_seed}")
    
    # Run stages
    if a.stage in ("all", "m1"):
        run_m1(df_clean, params, a.seed)
    if a.stage in ("all", "m2"):
        run_m2(df_clean, params, a.seed)
    if a.stage in ("all", "m3"):
        run_m3(df_clean, params, a.seed)
    if a.stage in ("all", "m4"):
        run_m4(df_clean, params, a.seed)
    if a.stage in ("all", "m5"):
        run_m5(df_clean, params, a.seed)
    
    print(f"\n{'='*80}")
    print(f"[OK] run_all.py completed successfully")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
