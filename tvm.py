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
    "🔍 Universal TVM", 
    "⚙️ Wealth Accumulation (DCF)", 
    "💡 Key Concepts", 
    "📊 Deal Screener"
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
            st.error("Error in calculation. Check your cash flow sign conventions (outflows must be negative).")

# ==========================================
# TAB 2: DCF, IRR, & WEALTH ACCUMULATION
# ==========================================
with tab_dcf:
    st.header("Comprehensive Wealth Accumulation Model")
    
    st.markdown("### 1. The Triple Rate Inputs")
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    with col_r1:
        holding_period = st.number_input("Holding Period (Years)", min_value=1, max_value=20, value=5, step=1)
    with col_r2:
        discount_rate = st.number_input("Discount Rate (%)", value=10.0, step=0.5, help="Target Yield / Opportunity Cost")
    with col_r3:
        reinvest_rate = st.number_input("Reinvestment Rate (%)", value=6.0, step=0.5, help="Rate for active reinvestment of positive cash flows")
    with col_r4:
        safe_rate = st.number_input("Safe Rate (%)", value=4.0, step=0.5, help="Risk-free rate used to cover negative cash flows (Finance Rate)")

    st.markdown("### 2. Cash Flow Inputs")
    initial_investment = st.number_input("Year 0 (Initial Equity - Outflow)", value=-1000000.0, step=10000.0)

    st.markdown("#### Operational Cash Flows")
    operational_cfs = []
    ops_cols = st.columns(min(holding_period, 5)) 
    for year in range(1, holding_period + 1):
        col_idx = (year - 1) % 5
        with ops_cols[col_idx]:
            val = st.number_input(f"Year {year} CF", value=80000.0 + (year * 5000), step=1000.0, key=f"v_cf_{year}")
            operational_cfs.append(val)

    st.markdown("#### Disposition")
    sale_proceeds = st.number_input(f"Sale Proceeds (End of Yr {holding_period})", value=1300000.0, step=10000.0)

    if st.button("Run Wealth Analysis", type="primary"):
        # Build Cash Flow Array
        cash_flows = [initial_investment]
        for i in range(holding_period):
            if i == holding_period - 1:
                cash_flows.append(operational_cfs[i] + sale_proceeds)
            else:
                cash_flows.append(operational_cfs[i])
                
        # 1. Standard Calculations
        try:
            irr = npf.irr(cash_flows) * 100
        except:
            irr = 0.0
            
        npv = npf.npv(discount_rate / 100, cash_flows)
        
        # 2. Capital Accumulation Logic
        total_accumulated = 0
        reinvest_dec = reinvest_rate / 100
        for t, cf in enumerate(cash_flows):
            if cf > 0:
                # Compound positive cash flows forward to Year N
                total_accumulated += cf * ((1 + reinvest_dec) ** (holding_period - t))
        
        # 3. Compound Growth Rate (CGR)
        # ((Accumulated / Absolute Initial Investment) ^ (1/n)) - 1
        try:
            cgr = ((total_accumulated / abs(initial_investment)) ** (1 / holding_period) - 1) * 100
        except:
            cgr = 0.0
        
        # 4. Modified Internal Rate of Return (MIRR)
        # Uses Safe Rate as the finance rate for negative CFs, and Reinvest Rate for positive CFs
        try:
            mirr = npf.mirr(cash_flows, safe_rate/100, reinvest_rate/100) * 100
        except:
            mirr = 0.0

        # Display Results
        st.markdown("---")
        res_col1, res_col2 = st.columns(2)
        
        with res_col1:
            st.subheader("Standard Metrics")
            st.metric("Internal Rate of Return (IRR)", f"{irr:,.2f}%", help="Assumes all cash flows are reinvested at the IRR.")
            st.metric("Net Present Value (NPV)", f"${npv:,.2f}", help=f"Discounted at {discount_rate}%")
            
        with res_col2:
            st.subheader("Wealth Accumulation")
            st.metric("Total Capital Accumulated", f"${total_accumulated:,.2f}", help=f"Assumes interim cash flows grow at {reinvest_rate}%")
            st.metric("Modified IRR (MIRR)", f"{mirr:,.2f}%", help=f"Finance Rate: {safe_rate}% | Reinvest Rate: {reinvest_rate}%")
            st.metric("Compound Growth Rate (CGR)", f"{cgr:,.2f}%", help="Effective annual growth of your total wealth pool.")

        # Visualization
        st.markdown("### Net Cash Flow Timeline")
        df_plot = pd.DataFrame({
            "Year": [f"Yr {i}" for i in range(len(cash_flows))], 
            "Net Cash Flow": cash_flows
        })
        st.bar_chart(df_plot.set_index("Year"))

# ==========================================
# TAB 3 & 4: FUTURE EXPANSION
# ==========================================
with tab_concepts:
    st.info("Module 3: The Six Functions of the Dollar detailed calculators will go here.")

with tab_screener:
    st.info("Module 4: The full APOD Deal Screener will go here.")