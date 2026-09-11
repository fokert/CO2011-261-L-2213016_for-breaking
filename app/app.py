"""
M5 Integration: Streamlit Web App

Single integrated app with 5 tabs for all 4 modules + overview.
Runs locally; use: streamlit run app/app.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Import all modules
from data.loader import load_full_data
from m1_logic.predicates import PredicateEvaluator
from m1_logic.toy_instance import toy_instance_to_cnf
from m1_logic.sat_check import SATChecker
from m2_ilp.model import ILPAssignmentModel
from m2_ilp.baseline import compute_baseline_workload, compute_fairness_metric
from m3_automata.dfa import create_dfa_no_2_consecutive
from m3_automata.strings_from_data import build_schedule_strings
from m4_dynamics.fatigue import FatigueRecurrence, estimate_weekly_loads, fit_parameters_from_data


# ============================================================================
# Streamlit App Configuration
# ============================================================================

st.set_page_config(page_title="IAP Demo", layout="wide")
st.title("Invigilator Assignment Problem (IAP) — Demo")
st.markdown("""
**Integrated end-to-end demo** using all 4 mathematical modules:
1. **M1 Logic** — Specification & satisfiability  
2. **M2 ILP** — Solver & fairness optimization  
3. **M3 Automata** — Temporal rules validation  
4. **M4 Dynamics** — Term-wide fairness stability  
5. **Web app** — Decision support dashboard  
""")

# Load data once (cached)
@st.cache_data
def load_data():
    return load_full_data()

df_clean, params, seed = load_data()

# ============================================================================
# Tab 1: Data Overview
# ============================================================================

with st.tabs(["📊 Data", "🔍 M1: Logic", "📈 M2: ILP", "🤖 M3: Automata", "📉 M4: Dynamics"])[0]:
    st.header("Data Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Invigilators", params["n_invigilators"])
    col2.metric("Shifts", params["n_shifts"])
    col3.metric("Campuses", params["n_campuses"])
    col4.metric("Assignments", len(df_clean))
    
    st.subheader("Sample Data")
    st.dataframe(df_clean.head(10), use_container_width=True)
    
    st.subheader("Date Range")
    date_min = df_clean["date"].min()
    date_max = df_clean["date"].max()
    st.write(f"{date_min.date()} to {date_max.date()}")
    
    st.subheader("Shifts per Day")
    daily_shifts = df_clean.groupby("date").size()
    st.line_chart(daily_shifts)

# ============================================================================
# Tab 2: M1 Logic (SAT)
# ============================================================================

with st.tabs(["📊 Data", "🔍 M1: Logic", "📈 M2: ILP", "🤖 M3: Automata", "📉 M4: Dynamics"])[1]:
    st.header("M1: Logic & Satisfiability")
    
    st.subheader("Hard Rules Extracted")
    st.write("""
    - **No double-booking**: Overlapping shifts cannot have same invigilator
    - **Availability**: Busy invigilators cannot be assigned
    - **Capacity**: Each shift needs exact number of invigilators
    """)
    
    pred = PredicateEvaluator(df_clean, params)
    pred.print_summary()
    
    st.subheader("Toy Instance (from Brief)")
    st.write("""
    **Setup**: 2 invigilators {CB1, CB2}, 1 shift s needing exactly 1 person.  
    **Rule**: CB1 is busy at s.  
    **Expected result**: CB1 not assigned, CB2 assigned.
    """)
    
    if st.button("Run SAT Check on Toy Instance"):
        clauses, var_map, inv_map = toy_instance_to_cnf()
        checker = SATChecker(clauses, var_map, inv_map)
        is_sat, model = checker.check_sat()
        
        if is_sat:
            st.success("✓ **SAT** — Solution found!")
            st.write("**Model:**")
            for (i, j), val in model.items():
                st.write(f"  Assign({i}, {j}) = {val}")
        else:
            st.error("✗ **UNSAT** — No feasible solution")

# ============================================================================
# Tab 3: M2 ILP (Solver)
# ============================================================================

with st.tabs(["📊 Data", "🔍 M1: Logic", "📈 M2: ILP", "🤖 M3: Automata", "📉 M4: Dynamics"])[2]:
    st.header("M2: Linear & Integer Programming")
    
    # Baseline fairness
    st.subheader("Baseline (Current) Fairness")
    baseline_load = compute_baseline_workload(df_clean)
    baseline_fair = compute_fairness_metric(baseline_load)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Min Load", baseline_fair["min"])
    col2.metric("Max Load", baseline_fair["max"])
    col3.metric("Spread", baseline_fair["spread"])
    col4.metric("Variance", f"{baseline_fair['variance']:.2f}")
    
    st.write("Baseline fairness (max - min):", baseline_fair["spread"])
    
    # ILP Solver
    st.subheader("Optimize with ILP Solver")
    
    subset_size = st.slider("Number of shifts to optimize", 5, min(30, params["n_shifts"]), 10)
    subset_J = params["J"][:subset_size]
    
    if st.button("Solve ILP"):
        with st.spinner("Solving..."):
            model = ILPAssignmentModel(df_clean, params, subset_J)
            model.build_model()
            is_feasible = model.solve(time_limit=15)
            
            if is_feasible:
                st.success("✓ Feasible solution found")
                
                new_load = model.get_workloads()
                new_fair = compute_fairness_metric(new_load)
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Min Load", new_fair["min"])
                col2.metric("Max Load", new_fair["max"])
                col3.metric("Spread", new_fair["spread"])
                col4.metric("Objective (t)", f"{model.get_objective_value():.2f}")
                
                st.write(f"**Improvement**: Spread reduced from {baseline_fair['spread']} to {new_fair['spread']}")
                
                # Show assignment
                st.subheader("New Assignment")
                assign_df = model.get_assignment_df()
                st.dataframe(assign_df, use_container_width=True)
            else:
                st.error("✗ No feasible solution found (try more shifts)")

# ============================================================================
# Tab 4: M3 Automata (DFA)
# ============================================================================

with st.tabs(["📊 Data", "🔍 M1: Logic", "📈 M2: ILP", "🤖 M3: Automata", "📉 M4: Dynamics"])[3]:
    st.header("M3: Automata & Formal Languages")
    
    st.subheader("Temporal Rules as DFA")
    st.write("""
    **Rule**: "No more than 2 consecutive working days"  
    **Alphabet**: Σ = {M, A, N, -} (Morning, Afternoon, Night, off)  
    **States**: q0, q1, q2 (run length 0, 1, 2), + dead state
    """)
    
    # Build schedule strings
    strings = build_schedule_strings(df_clean)
    
    # Create DFA
    dfa = create_dfa_no_2_consecutive()
    
    # Select invigilator
    inv_list = list(strings.keys())
    selected_inv = st.selectbox("Select invigilator", inv_list)
    
    if selected_inv and selected_inv in strings:
        schedule_str = strings[selected_inv]
        # Shorten for display
        if len(schedule_str) > 100:
            schedule_str_disp = schedule_str[:100] + f"... (len={len(schedule_str)})"
        else:
            schedule_str_disp = schedule_str
        
        st.write(f"**Schedule string ({selected_inv})**: `{schedule_str_disp}`")
        
        # Check DFA acceptance
        is_accepted = dfa.run(schedule_str)
        if is_accepted:
            st.success(f"✓ **DFA accepts** — Schedule complies with rule")
        else:
            st.warning(f"✗ **DFA rejects** — Schedule violates rule")
    
    st.subheader("Test Custom String")
    test_string = st.text_input("Enter test string (over {W,-} for no-2-consecutive)", "WW-WW")
    if test_string:
        # Map M,A,N,- to W,-
        test_binary = "".join("W" if c in "MAN" else "-" for c in test_string)
        result = dfa.run(test_binary)
        st.write(f"Test: `{test_binary}` → {'**Accept**' if result else '**Reject**'}")

# ============================================================================
# Tab 5: M4 Dynamics (Equilibrium)
# ============================================================================

with st.tabs(["📊 Data", "🔍 M1: Logic", "📈 M2: ILP", "🤖 M3: Automata", "📉 M4: Dynamics"])[4]:
    st.header("M4: Discrete Dynamical Systems")
    
    st.subheader("Closed-loop Fatigue Recurrence")
    st.write("""
    **Model**: F[n+1] = a·F[n] + b·load[n] - r·rest[n]
    
    where F[n] is fatigue level, load[n] is weekly workload.
    """)
    
    # Fit parameters
    a, b, r = fit_parameters_from_data(df_clean)
    st.write(f"**Parameters**: a={a} (decay), b={b} (load), r={r} (rest)")
    
    # Estimate weekly loads
    weeks, loads = estimate_weekly_loads(df_clean)
    
    if st.button("Simulate Fatigue Dynamics"):
        # Create recurrence
        rec = FatigueRecurrence(a, b, r)
        result = rec.simulate(loads, initial_F=0)
        
        F_star = result["equilibrium"]
        traj = result["trajectory"]
        
        st.write(f"**Fixed point (equilibrium)**: F* = {F_star:.2f}")
        st.write(f"**Stability**: {'Stable (|a| < 1)' if result['stable'] else 'Unstable'}")
        
        # Plot trajectory
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(range(len(traj)), traj, "b-o", label="Fatigue trajectory", markersize=4)
        ax.axhline(y=F_star, color="r", linestyle="--", label=f"Equilibrium F*={F_star:.2f}")
        ax.set_xlabel("Week")
        ax.set_ylabel("Fatigue Level")
        ax.set_title("Fatigue Dynamics Over Term")
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        
        st.write(f"**Final fatigue (week {len(loads)})**: {traj[-1]:.2f}")

# ============================================================================
# Footer
# ============================================================================

st.divider()
st.markdown(f"""
---
**IAP Demo v1.0** | Seed: {seed} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

**Modules**: M1 (Logic) | M2 (ILP) | M3 (Automata) | M4 (Dynamics)  
**Data**: {len(df_clean)} assignments | {params['n_invigilators']} staff | {params['n_shifts']} shifts
""")
