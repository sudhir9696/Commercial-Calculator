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
        
        # 2. CCIM Capital Accumulation Logic (The Sinking Fund Method)
        safe_dec = safe_rate / 100
        reinvest_dec = reinvest_rate / 100
        
        # Create a copy of cash flows to adjust backwards
        adjusted_cfs = cash_flows.copy()

        # Iterate backwards from end of hold to Year 1
        for t in range(len(adjusted_cfs) - 1, 0, -1):
            if adjusted_cfs[t] < 0:
                # Discount the deficit back 1 year at the safe rate
                cost_in_prev_year = adjusted_cfs[t] / (1 + safe_dec)
                # Apply it to the previous year's cash flow
                adjusted_cfs[t-1] += cost_in_prev_year
                # Zero out the current year since the deficit is now funded
                adjusted_cfs[t] = 0

        # Now compound the adjusted positive cash flows forward at Reinvest Rate
        total_accumulated = 0
        for t in range(1, len(adjusted_cfs)):
            if adjusted_cfs[t] > 0:
                total_accumulated += adjusted_cfs[t] * ((1 + reinvest_dec) ** (holding_period - t))
        
        # 3. Compound Growth Rate (CGR)
        # Use the adjusted Year 0 equity in case deficits were pushed all the way back to Day 1
        adjusted_initial_equity = abs(adjusted_cfs[0])
        try:
            cgr = ((total_accumulated / adjusted_initial_equity) ** (1 / holding_period) - 1) * 100
        except:
            cgr = 0.0
        
        # 4. Modified Internal Rate of Return (MIRR)
        # npf.mirr natively handles the exact textbook math for MIRR
        try:
            mirr = npf.mirr(cash_flows, safe_rate/100, reinvest_rate/100) * 100
        except:
            mirr = 0.0

        # Display Results
        st.markdown("---")
        res_col1, res_col2 = st.columns(2)
        
        with res_col1:
            st.subheader("Standard Metrics")
            st.metric("Internal Rate of Return (IRR)", f"{irr:,.2f}%")
            st.metric("Net Present Value (NPV)", f"${npv:,.2f}")
            
        with res_col2:
            st.subheader("Wealth Accumulation")
            st.metric("Total Capital Accumulated", f"${total_accumulated:,.2f}")
            st.metric("Modified IRR (MIRR)", f"{mirr:,.2f}%")
            st.metric("Compound Growth Rate (CGR)", f"{cgr:,.2f}%")

        # Visualization
        st.markdown("### Net Cash Flow Timeline")
        df_plot = pd.DataFrame({
            "Year": [f"Yr {i}" for i in range(len(cash_flows))], 
            "Net Cash Flow": cash_flows
        })
        st.bar_chart(df_plot.set_index("Year"))
        
        # ==========================================
        # VISUAL PROOFS (Add this to the bottom of Tab 2)
        # ==========================================
        st.markdown("---")
        st.markdown("### 🧮 Mathematical Proofs")
        
        # 1. Proof of MIRR Table
        with st.expander("Show Proof of MIRR"):
            st.caption(f"Negative cash flows discounted to Year 0 at Safe Rate ({safe_rate}%). Positive cash flows compounded to Year {holding_period} at Reinvestment Rate ({reinvest_rate}%).")
            mirr_data = []
            pv_outflows_total = 0
            fv_inflows_total = 0
            
            for t, cf in enumerate(cash_flows):
                if cf < 0:
                    pv = cf / ((1 + safe_rate/100) ** t)
                    fv = 0
                elif cf > 0:
                    pv = 0
                    fv = cf * ((1 + reinvest_rate/100) ** (holding_period - t))
                else:
                    pv, fv = 0, 0
                
                pv_outflows_total += pv
                fv_inflows_total += fv
                
                mirr_data.append({
                    "Year": f"Yr {t}",
                    "Cash Flow": f"${cf:,.2f}",
                    "PV of Outflows (Safe Rate)": f"${pv:,.2f}" if pv != 0 else "-",
                    "FV of Inflows (Reinvest Rate)": f"${fv:,.2f}" if fv != 0 else "-"
                })
            
            # Add Total Row
            mirr_data.append({
                "Year": "TOTALS",
                "Cash Flow": "-",
                "PV of Outflows (Safe Rate)": f"${pv_outflows_total:,.2f}",
                "FV of Inflows (Reinvest Rate)": f"${fv_inflows_total:,.2f}"
            })
            
            st.dataframe(pd.DataFrame(mirr_data), use_container_width=True)

        # 2. Proof of Capital Accumulation Table (Sinking Fund)
        with st.expander("Show Proof of Capital Accumulation (CGR)"):
            st.caption(f"Future negative cash flows are funded by discounting them back 1 year against previous positive cash flows at the Safe Rate ({safe_rate}%). Remaining positive cash flows are compounded forward at the Reinvestment Rate ({reinvest_rate}%).")
            
            cap_data = []
            total_fv_adj = 0
            
            for t in range(len(cash_flows)):
                orig_cf = cash_flows[t]
                adj_amount = adjusted_cfs[t] - orig_cf if t < len(adjusted_cfs) else 0
                adj_cf = adjusted_cfs[t]
                
                fv_adj = 0
                if t > 0 and adj_cf > 0:
                    fv_adj = adj_cf * ((1 + reinvest_rate/100) ** (holding_period - t))
                    total_fv_adj += fv_adj
                    
                cap_data.append({
                    "Year": f"Yr {t}",
                    "Original CF": f"${orig_cf:,.2f}",
                    "Sinking Fund Adj": f"${adj_amount:,.2f}" if adj_amount != 0 else "-",
                    "Adjusted CF": f"${adj_cf:,.2f}",
                    "FV of Adjusted CF": f"${fv_adj:,.2f}" if fv_adj != 0 else "-"
                })
                
            # Add Total Row
            cap_data.append({
                "Year": "TOTAL",
                "Original CF": "-",
                "Sinking Fund Adj": "-",
                "Adjusted CF": "-",
                "FV of Adjusted CF": f"${total_fv_adj:,.2f}"
            })
            
            st.dataframe(pd.DataFrame(cap_data), use_container_width=True)

# ==========================================
# TAB 3 & 4: FUTURE EXPANSION
# ==========================================
with tab_concepts:
    st.info("Module 3: The Six Functions of the Dollar detailed calculators will go here.")
    
# ==========================================
# TAB 4: THE CCIM APOD (Deal Screener)
# ==========================================
with tab_screener:
    st.header("Annual Property Operating Data (APOD)")
    st.markdown("Comprehensive Before-Tax Cash Flow Analysis")

    # --- SECTION 1: CAPITAL & FINANCING ---
    st.markdown("### 1. Acquisition & Financing")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        purchase_price = st.number_input("Purchase Price", value=3750000.0, step=50000.0)
        acq_costs = st.number_input("Acquisition Costs", value=80000.0, step=5000.0)
    with col_f2:
        loan_amount = st.number_input("Loan Amount (1st Mortgage)", value=0.0, step=50000.0, help="Leave 0 for All-Cash/Part I analysis")
        interest_rate = st.number_input("Interest Rate (%)", value=0.0, step=0.1)
    with col_f3:
        amortization = st.number_input("Amortization (Years)", value=0, step=1)
        loan_fees = st.number_input("Loan Fees/Costs", value=0.0, step=1000.0)

    # Initial Investment Math
    initial_investment = purchase_price + acq_costs + loan_fees - loan_amount

    # Annual Debt Service (ADS) Math
    if loan_amount > 0 and interest_rate > 0 and amortization > 0:
        monthly_rate = (interest_rate / 100) / 12
        months = amortization * 12
        monthly_pmt = npf.pmt(monthly_rate, months, -loan_amount)
        ads = monthly_pmt * 12
    else:
        ads = 0.0

    # --- SECTION 2: SPACE MARKET (REVENUE) ---
    st.markdown("### 2. Income")
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        pri = st.number_input("1. Potential Rental Income (PRI)", value=480000.0, step=10000.0)
        vacancy_pct = st.number_input("2. Vacancy & Credit Loss (%)", value=10.0, step=0.5)
    with col_i2:
        other_income = st.number_input("4. Plus: Other Income", value=0.0, step=1000.0)

    # Revenue Math
    vac_loss = pri * (vacancy_pct / 100)
    eri = pri - vac_loss  # Effective Rental Income
    goi = eri + other_income # Gross Operating Income

    # --- SECTION 3: OPERATING EXPENSES ---
    st.markdown("### 3. Operating Expenses")
    st.caption("Use the quick override for case studies, or expand to itemize.")
    
    opex_override = st.number_input("Total Operating Expenses (Quick Override)", value=165000.0, step=5000.0)
    
    with st.expander("Itemize Operating Expenses (Overrides quick total if > 0)"):
        c_ex1, c_ex2 = st.columns(2)
        with c_ex1:
            tax = st.number_input("Real Estate Taxes", value=0.0, step=1000.0)
            ins = st.number_input("Property Insurance", value=0.0, step=1000.0)
            mgt = st.number_input("Off Site Management", value=0.0, step=1000.0)
            maint = st.number_input("Repairs and Maintenance", value=0.0, step=1000.0)
        with c_ex2:
            util = st.number_input("Utilities (Total)", value=0.0, step=1000.0)
            payroll = st.number_input("Payroll", value=0.0, step=1000.0)
            misc = st.number_input("Accounting, Legal, Misc", value=0.0, step=1000.0)
        
        itemized_total = tax + ins + mgt + maint + util + payroll + misc
    
    # Determine which OpEx to use
    final_opex = itemized_total if itemized_total > 0 else opex_override

    # --- SECTION 4: THE APOD STATEMENT ---
    noi = goi - final_opex
    cfbt = noi - ads
    
    # KPIs
    cap_rate = (noi / purchase_price) * 100 if purchase_price > 0 else 0.0
    grm = purchase_price / pri if pri > 0 else 0.0

    st.markdown("---")
    st.markdown("## 📄 Annual Property Operating Data (APOD)")
    
    # Using columns to create the classic CCIM ledger look
    c1, c2, c3 = st.columns([2, 1, 1])
    
    # Top KPI Header
    c1.markdown(f"**Initial Investment:** ${initial_investment:,.0f}")
    c2.markdown(f"**Acq. Cap Rate:** {cap_rate:.2f}%")
    c3.markdown(f"**GRM:** {grm:.2f}")
    st.markdown("---")
    
    c1.markdown("**1 POTENTIAL RENTAL INCOME**")
    c3.markdown(f"**${pri:,.0f}**")
    
    c1.markdown(f"2 Less: Vacancy & Cr. Losses ({vacancy_pct}%)")
    c2.markdown(f"(${vac_loss:,.0f})")
    
    c1.markdown("**3 EFFECTIVE RENTAL INCOME**")
    c3.markdown(f"**${eri:,.0f}**")
    
    c1.markdown("4 Plus: Other Income")
    c2.markdown(f"${other_income:,.0f}")
    
    c1.markdown("#### 5 GROSS OPERATING INCOME")
    c3.markdown(f"#### ${goi:,.0f}")
    
    c1.markdown("29 TOTAL OPERATING EXPENSES")
    c2.markdown(f"(${final_opex:,.0f})")
    
    c1.markdown("#### 30 NET OPERATING INCOME")
    c3.markdown(f"#### ${noi:,.0f}")
    
    c1.markdown("31 Less: Annual Debt Service")
    c2.markdown(f"(${ads:,.0f})")
    
    st.markdown("---")
    c1.markdown("### 35 CASH FLOW BEFORE TAXES")
    c3.markdown(f"### ${cfbt:,.0f}")
