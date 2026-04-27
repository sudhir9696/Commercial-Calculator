import streamlit as st
import numpy_financial as npf

st.set_page_config(page_title="Universal TVM Solver", layout="centered")

st.title("CCIM Universal TVM Calculator")
st.markdown("---")

# 1. UI: Define what we are solving for and the periodicity
solve_for = st.radio("Solve For:", ["PV", "FV", "PMT", "n (Periods)", "Rate (I/YR)"], horizontal=True)
compounding = st.radio("Compounding Frequency:", ["Annual", "Monthly"], horizontal=True)

st.markdown("### Inputs")
col1, col2 = st.columns(2)

# 2. UI: Dynamically hide the input field for the variable we are solving for
with col1:
    pv = st.number_input("PV (Present Value)", value=-100000.0, step=1000.0) if solve_for != "PV" else None
    pmt = st.number_input("PMT (Payment)", value=0.0, step=100.0) if solve_for != "PMT" else None
    fv = st.number_input("FV (Future Value)", value=0.0, step=1000.0) if solve_for != "FV" else None

with col2:
    n = st.number_input("n (Total Years)", value=5.0, step=1.0) if solve_for != "n (Periods)" else None
    i_yr = st.number_input("I/YR (Annual Interest Rate %)", value=10.0, step=0.1) if solve_for != "Rate (I/YR)" else None

st.markdown("---")

# 3. Logic: Adjust for Annual vs Monthly Compounding
if st.button("Calculate", type="primary"):
    
    # Set up the operational variables
    if solve_for != "n (Periods)" and solve_for != "Rate (I/YR)":
        periods = n * 12 if compounding == "Monthly" else n
        rate = (i_yr / 100) / 12 if compounding == "Monthly" else (i_yr / 100)
    
    st.markdown("### Result:")
    
    try:
        # 4. Math: Execute the appropriate financial function
        if solve_for == "PV":
            result = npf.pv(rate, periods, pmt, fv)
            st.success(f"**Present Value (PV):** ${result:,.2f}")
            
        elif solve_for == "FV":
            result = npf.fv(rate, periods, pmt, pv)
            st.success(f"**Future Value (FV):** ${result:,.2f}")
            
        elif solve_for == "PMT":
            result = npf.pmt(rate, periods, pv, fv)
            freq_label = "Monthly" if compounding == "Monthly" else "Annual"
            st.success(f"**{freq_label} Payment (PMT):** ${result:,.2f}")
            
        elif solve_for == "n (Periods)":
            rate = (i_yr / 100) / 12 if compounding == "Monthly" else (i_yr / 100)
            result = npf.nper(rate, pmt, pv, fv)
            if compounding == "Monthly":
                st.success(f"**Total Periods (n):** {result:,.2f} months ({result/12:,.2f} years)")
            else:
                st.success(f"**Total Periods (n):** {result:,.2f} years")
                
        elif solve_for == "Rate (I/YR)":
            periods = n * 12 if compounding == "Monthly" else n
            # npf.rate returns the periodic rate. We must annualize it for the final output.
            periodic_rate = npf.rate(periods, pmt, pv, fv)
            annual_rate = (periodic_rate * 12 * 100) if compounding == "Monthly" else (periodic_rate * 100)
            st.success(f"**Annual Interest Rate (I/YR):** {annual_rate:,.2f}%")
            
    except Exception as e:
        st.error("Error in calculation. Please check your cash flow sign conventions (outflows must be negative).")