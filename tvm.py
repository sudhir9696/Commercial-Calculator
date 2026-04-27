import streamlit as st
import numpy_financial as npf
import pandas as pd

# Set the page to be wide for better data table and chart viewing
st.set_page_config(page_title="CRE Financial Dashboard", layout="wide")

# Mimicking the professional header from the CCIM Institute
st.title("📈 Commercial Real Estate Financial Dashboard")
st.markdown("---")

# 1. Create the Tabs
tab_tvm, tab_dcf, tab_concepts, tab_screener = st.tabs([
    "🔍 Overview (Universal TVM)", 
    "⚙️ Operating (DCF & IRR)", 
    "💡 Key Concepts (Six Functions)", 
    "📊 Using the Calculator (Deal Screener)"
])

# ==========================================
# TAB 1: UNIVERSAL TVM SOLVER
# ==========================================
with tab_tvm:
    st.header("Universal TVM Solver")
    
    solve_for = st.radio("Solve For:", ["PV", "FV", "PMT", "n (Periods)", "Rate (I/YR)"], horizontal=True, key="tvm_solve")
    compounding = st.radio("Compounding Frequency:", ["Annual", "Monthly"], horizontal=True, key="tvm_comp")

    col1, col2 = st.columns(2)
    with col1:
        pv = st.number_input("PV (Present Value)", value=-100000.0, step=1000.0) if solve_for != "PV" else None
        pmt = st.number_input("PMT (Payment)", value=0.0, step=100.0) if solve_for != "PMT" else None
        fv = st.number_input("FV (Future Value)", value=0.0, step=1000.0) if solve_for != "FV" else None

    with col2:
        if solve_for != "n (Periods)":
            n_label = "n (Total Months)" if compounding == "Monthly" else "n (Total Years)"
            n_default = 60.0 if compounding == "Monthly" else 5.0
            n = st.number_input(n_label, value=n_default, step=1.0)
        else:
            n = None
            
        i_yr = st.number_input("I/YR (Annual Interest Rate %)", value=10.0, step=0.1) if solve_for != "Rate (I/YR)" else None

    if st.button("Calculate TVM", type="primary"):
        if solve_for != "n (Periods)" and solve_for != "Rate (I/YR)":
            periods = n 
            rate = (i_yr / 100) / 12 if compounding == "Monthly" else (i_yr / 100)
        
        st.markdown("### Result:")
        try:
            if solve_for == "PV":
                result = npf.pv(rate, periods, pmt, fv)
                st.success(f"**Present Value (PV):** ${result:,.2f}")
            elif solve_for == "FV":
                result = npf.fv(rate, periods, pmt, pv)
                st.success(f"**Future Value (FV):** ${result:,.2f}")
            elif solve_for == "PMT":
                result = npf.pmt(rate, periods, pv, fv)
                st.success(f"**Payment (PMT):** ${result:,.2f}")
            elif solve_for == "n (Periods)":
                rate = (i_yr / 100) / 12 if compounding == "Monthly" else (i_yr / 100)
                result = npf.nper(rate, pmt, pv, fv)
                st.success(f"**Total Periods (n):** {result:,.2f}")
            elif solve_for == "Rate (I/YR)":
                periods = n
                periodic_rate = npf.rate(periods, pmt, pv, fv)
                annual_rate = (periodic_rate * 12 * 100) if compounding == "Monthly" else (periodic_rate * 100)
                st.success(f"**Annual Interest Rate (I/YR):** {annual_rate:,.2f}%")
        except Exception as e:
            st.error("Error in calculation. Check your cash flow sign conventions.")

# ==========================================
# TAB 2: DCF & IRR MODEL
# ==========================================
# ==========================================
# TAB 2: DCF & IRR MODEL
# ==========================================
with tab_dcf:
    st.header("Discounted Cash Flow (DCF) & IRR")
    
    col_dcf1, col_dcf2 = st.columns(2)
    with col_dcf1:
        holding_period = st.number_input("Holding Period (Years)", min_value=1, max_value=20, value=5, step=1)
    with col_dcf2:
        discount_rate = st.number_input("Target Yield / Discount Rate (%)", min_value=0.0, max_value=30.0, value=10.0, step=0.5)

    st.markdown("### 1. Acquisition")
    initial_investment = st.number_input("Year 0 (Initial Equity - Outflow)", value=-1000000.0, step=10000.0)

    st.markdown("### 2. Operations (Annual Cash Flows)")
    operational_cfs = []
    
    # We create columns to make the inputs look cleaner
    ops_cols = st.columns(min(holding_period, 5)) 
    for year in range(1, holding_period + 1):
        col_idx = (year - 1) % 5
        with ops_cols[col_idx]:
            val = st.number_input(f"Year {year} CF", value=80000.0 + (year * 5000), step=1000.0, key=f"op_cf_{year}")
            operational_cfs.append(val)

    st.markdown("### 3. Disposition (Exit)")
    sale_proceeds = st.number_input(f"Sale Proceeds (Received end of Year {holding_period})", value=1200000.0, step=10000.0)

    if st.button("Calculate IRR & NPV", type="primary", key="btn_calc_irr"):
        
        # Build the final array for the numpy-financial calculator
        cash_flows = [initial_investment]
        
        for i in range(holding_period):
            if i == holding_period - 1:
                # Last year: Operations + Sale Proceeds
                cash_flows.append(operational_cfs[i] + sale_proceeds)
            else:
                cash_flows.append(operational_cfs[i])
                
        try:
            irr_pct = npf.irr(cash_flows) * 100 
        except:
            irr_pct = None
            
        rate_decimal = discount_rate / 100
        npv = npf.npv(rate_decimal, cash_flows)
        
        st.markdown("---")
        m1, m2 = st.columns(2)
        if irr_pct is not None:
            m1.metric("Internal Rate of Return (IRR)", f"{irr_pct:,.2f}%")
        m2.metric(f"Net Present Value (NPV) @ {discount_rate}%", f"${npv:,.2f}")
        
        st.markdown("### Cash Flow T-Bar")
        df_cf = pd.DataFrame({"Year": [f"Yr {i}" for i in range(len(cash_flows))], "Net Cash Flow": cash_flows})
        st.bar_chart(df_cf.set_index("Year"))

# ==========================================
# TAB 3 & 4: FUTURE EXPANSION
# ==========================================
with tab_concepts:
    st.info("Module 3: The Six Functions of the Dollar will be built here.")

with tab_screener:
    st.info("Module 4: The full APOD Deal Screener will be built here.")