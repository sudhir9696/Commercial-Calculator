import streamlit as st
import numpy_financial as npf
import pandas as pd

# Set the page to be wide for better data table and chart viewing
st.set_page_config(page_title="CRE Financial Dashboard", layout="wide")

# Mimicking the professional header from the CCIM Institute
st.title("📈 Commercial Real Estate Financial Dashboard")
st.markdown("---")

# 1. Create the Tabs
tab_tvm, tab_dcf, tab_screener, tab_proforma, tab_financing = st.tabs([
    "🔍 Universal TVM", 
    "⚙️ Wealth Accumulation", 
    "📊 APOD (Year 1)",
    "📈 Multi-Year Pro Forma",
    "🏦 Financing (Loan Sizing)"
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
# TAB 3: THE CCIM APOD (Deal Screener)
# ==========================================
with tab_screener:
    st.header("Annual Property Operating Data (APOD)")
    st.markdown("Comprehensive Before-Tax Cash Flow Analysis")

    # --- SECTION 1: CAPITAL & FINANCING ---
    st.markdown("### 1. Acquisition & Financing")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        purchase_price = st.number_input("Purchase Price", value=0.0, step=50000.0)
        acq_costs = st.number_input("Acquisition Costs", value=0.0, step=5000.0)
    with col_f2:
        loan_amount = st.number_input("Loan Amount (1st Mortgage)", value=0.0, step=50000.0)
        interest_rate = st.number_input("Interest Rate (%)", value=0.0, step=0.1)
    with col_f3:
        amortization = st.number_input("Amortization (Years)", value=0, step=1)
        loan_fees = st.number_input("Loan Fees/Costs", value=0.0, step=1000.0)

    # Initial Investment & ADS Math
    initial_investment = purchase_price + acq_costs + loan_fees - loan_amount
    if loan_amount > 0 and interest_rate > 0 and amortization > 0:
        ads = npf.pmt((interest_rate / 100) / 12, amortization * 12, -loan_amount) * 12
    else:
        ads = 0.0

    # --- SECTION 2: SPACE MARKET (REVENUE) ---
    st.markdown("### 2. Income")
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        pri = st.number_input("1. Potential Rental Income (PRI)", value=435000.0, step=5000.0)
        vacancy_pct = st.number_input("2. Vacancy & Credit Loss (%)", value=3.5, step=0.5)
    with col_i2:
        other_income = st.number_input("4. Plus: Other Income", value=16200.0, step=500.0)

    # Revenue Math
    vac_loss = pri * (vacancy_pct / 100)
    eri = pri - vac_loss
    goi = eri + other_income

   # --- SECTION 3: OPERATING EXPENSES (DYNAMIC) ---
    st.markdown("### 3. Operating Expenses")

    # 1. Initialize all itemized variables to 0 up front. 
    # (This prevents the APOD table at the bottom from crashing if they are hidden)
    re_taxes = pp_taxes = insurance = management = payroll = benefits = 0.0
    workers_comp = repairs = electric = water = gas = accounting = 0.0
    licenses = advertising = supplies = hvac = landscaping = other_misc = 0.0

    # 2. The new Radio Toggle right at the top
    expense_method = st.radio(
        "How would you like to calculate Operating Expenses?",
        ["Direct Total ($)", "Market Ratio (% of GOI)", "Itemized List"],
        horizontal=True
    )

    # 3. Dynamic UI based on the selected method
    if expense_method == "Direct Total ($)":
        final_opex = st.number_input("Total Operating Expenses ($)", value=176500.0, step=1000.0)
        
    elif expense_method == "Market Ratio (% of GOI)":
        exp_ratio_override = st.number_input("Market Expense Ratio (% of GOI)", value=40.0, step=1.0)
        final_opex = goi * (exp_ratio_override / 100)
        
    else: # Itemized List
        st.caption("Enter itemized expenses below. The APOD ledger will dynamically update.")
        c_ex1, c_ex2, c_ex3 = st.columns(3)
        
        with c_ex1:
            re_taxes = st.number_input("Real Estate Taxes", value=0.0, step=1000.0)
            pp_taxes = st.number_input("Personal Property Taxes", value=0.0, step=100.0)
            insurance = st.number_input("Property Insurance", value=0.0, step=1000.0)
            management = st.number_input("Off Site Management", value=0.0, step=1000.0)
            payroll = st.number_input("Payroll", value=0.0, step=1000.0)
            benefits = st.number_input("Expenses/Benefits", value=0.0, step=1000.0)

        with c_ex2:
            workers_comp = st.number_input("Taxes/Worker's Comp", value=0.0, step=100.0)
            repairs = st.number_input("Repairs and Maintenance", value=0.0, step=1000.0)
            electric = st.number_input("Electric - Common Area", value=0.0, step=100.0)
            water = st.number_input("Water & Sewer", value=0.0, step=100.0)
            gas = st.number_input("Natural Gas", value=0.0, step=100.0)
            accounting = st.number_input("Accounting and Legal", value=0.0, step=100.0)

        with c_ex3:
            licenses = st.number_input("Licenses/Permits", value=0.0, step=100.0)
            advertising = st.number_input("Advertising", value=0.0, step=1000.0)
            supplies = st.number_input("Supplies", value=0.0, step=100.0)
            hvac = st.number_input("HVAC Repair/Filters", value=0.0, step=100.0)
            landscaping = st.number_input("Landscaping", value=0.0, step=100.0)
            other_misc = st.number_input("Other Miscellaneous", value=0.0, step=100.0)

        final_opex = sum([
            re_taxes, pp_taxes, insurance, management, payroll, benefits,
            workers_comp, repairs, electric, water, gas, accounting,
            licenses, advertising, supplies, hvac, landscaping, other_misc
        ])

    # --- AUTOMATIC % GOI CALCULATOR ---
    # Calculates the true ratio regardless of which method you chose above
    if goi > 0:
        actual_ratio = (final_opex / goi) * 100
    else:
        actual_ratio = 0.0
        
    st.metric("Effective Operating Expense Ratio", f"{actual_ratio:.2f}% of GOI", border=True)
    
    

    # --- SECTION 4: THE APOD STATEMENT ---
    noi = goi - final_opex
    cfbt = noi - ads
    
    cap_rate = (noi / purchase_price) * 100 if purchase_price > 0 else 0.0
    grm = purchase_price / pri if pri > 0 else 0.0

    st.markdown("---")
    st.markdown("## 📄 Annual Property Operating Data (APOD)")
    
    c_kpi1, c_kpi2, c_kpi3 = st.columns(3)
    c_kpi1.metric("Initial Investment", f"${initial_investment:,.0f}")
    c_kpi2.metric("Acq. Cap Rate", f"{cap_rate:.2f}%")
    c_kpi3.metric("GRM", f"{grm:.2f}")
    
    st.divider() 
    
    # Base Income Ledger
    apod_data = [
        {"Line Item": "POTENTIAL RENTAL INCOME", "Subtotal": "", "Total": f"${pri:,.0f}"},
        {"Line Item": f"Less: Vacancy & Cr. Losses ({vacancy_pct}%)", "Subtotal": f"(${vac_loss:,.0f})", "Total": ""},
        {"Line Item": "EFFECTIVE RENTAL INCOME", "Subtotal": "", "Total": f"${eri:,.0f}"},
        {"Line Item": "Plus: Other Income", "Subtotal": f"${other_income:,.0f}", "Total": ""},
        {"Line Item": "GROSS OPERATING INCOME", "Subtotal": "", "Total": f"${goi:,.0f}"},
        {"Line Item": "OPERATING EXPENSES:", "Subtotal": "", "Total": ""}
    ]
    
    # Master list of expense tuples
    all_expenses = [
        ("Real Estate Taxes", re_taxes), ("Personal Property Taxes", pp_taxes),
        ("Property Insurance", insurance), ("Off Site Management", management),
        ("Payroll", payroll), ("Expenses/Benefits", benefits),
        ("Taxes/Worker's Compensation", workers_comp), ("Repairs and Maintenance", repairs),
        ("Electric - Common Area", electric), ("Water & Sewer", water),
        ("Natural Gas", gas), ("Accounting and Legal", accounting),
        ("Licenses/Permits", licenses), ("Advertising", advertising),
        ("Supplies", supplies), ("HVAC Repair/Filters", hvac),
        ("Landscaping", landscaping), ("Other Miscellaneous", other_misc)
    ]
    
    # DYNAMIC INJECTION: Only add the expense to the ledger if it is > 0
    for name, amount in all_expenses:
        if amount > 0:
            apod_data.append({"Line Item": f"   • {name}", "Subtotal": f"(${amount:,.0f})", "Total": ""})
            
    # Add Bottom-Line Totals
    apod_data.extend([
        {"Line Item": "TOTAL OPERATING EXPENSES", "Subtotal": f"(${final_opex:,.0f})", "Total": ""},
        {"Line Item": "NET OPERATING INCOME", "Subtotal": "", "Total": f"${noi:,.0f}"},
        {"Line Item": "Less: Annual Debt Service", "Subtotal": f"(${ads:,.0f})", "Total": ""},
        {"Line Item": "CASH FLOW BEFORE TAXES", "Subtotal": "", "Total": f"${cfbt:,.0f}"}
    ])
    
    # Render pure Pandas static table
    df_apod = pd.DataFrame(apod_data)
    st.table(df_apod.set_index("Line Item"))

# ==========================================
# TAB 4: MULTI-YEAR PRO FORMA & AFTER-TAX MODEL
# ==========================================
with tab_proforma:
    st.header("Cash Flow Analysis Worksheet (After-Tax)")
    st.markdown("Multi-Year Forecast including Cost Recovery, Tax Liability, and Reversion.")

    # --- 1. ACQUISITION & TAX ASSUMPTIONS (Moved to top) ---
    st.markdown("### 1. Acquisition & Tax Assumptions")
    c_acq1, c_acq2, c_acq3 = st.columns(3)
    
    with c_acq1:
        purchase_price = st.number_input("Purchase Price", value=3750000.0, step=50000.0)
        acq_costs = st.number_input("Acquisition Costs", value=80000.0, step=5000.0)
        initial_investment = purchase_price + acq_costs
        
    with c_acq2:
        improvements_pct = st.number_input("Improvements Allocation (%)", value=70.0, step=5.0)
        property_class = st.selectbox("IRS Recovery Period", ["Non-Residential (39 Years)", "Residential (27.5 Years)"])
        
    with c_acq3:
        ordinary_tax_rate = st.number_input("Ordinary Income Tax Rate (%)", value=37.0, step=1.0)
        cg_tax_rate = st.number_input("Capital Gains Tax Rate (%)", value=20.0, step=1.0)
        recapture_tax_rate = st.number_input("Recapture Tax Rate (%)", value=25.0, step=1.0)

    # Calculate Original Basis & Improvements Basis
    st.info(f"**Original Basis:** ${initial_investment:,.0f} | **Depreciable Improvements:** ${(initial_investment * (improvements_pct / 100)):,.0f}")

    # --- 2. GROWTH ASSUMPTIONS ---
    st.markdown("### 2. Future Growth Assumptions")
    
    c_asm1, c_asm2, c_asm3 = st.columns(3)
    with c_asm1:
        st.metric("Year 1 PRI (Linked)", f"${pri:,.0f}")
        pri_growth = st.number_input("Annual PRI Growth Rate (%)", value=2.5, step=0.1)
    with c_asm2:
        st.metric("Year 1 Other Income (Linked)", f"${other_income:,.0f}")
        other_inc_growth = st.number_input("Other Income Growth (%)", value=0.0, step=0.1)
    with c_asm3:
        st.metric("Year 1 OpEx (Linked)", f"${final_opex:,.0f}")
        opex_growth = st.number_input("Annual OpEx Growth Rate (%)", value=3.0, step=0.1)
        
    hold_period = st.number_input("Anticipated Holding Period (Years)", value=5, min_value=1, max_value=15)

    # --- 3. BUILD THE MULTI-YEAR ENGINE ---
    forecast_years = int(hold_period) + 1 
    
    # --- REDEFINE EXPENSE RATIO ---
    # Calculate the dynamic Expense Ratio using the live data from Tab 4
    if goi > 0:
        calculated_expense_ratio = final_opex / goi
    else:
        calculated_expense_ratio = 0.0
    
    # Dictionaries for Before-Tax
    row_pri, row_vac, row_eri, row_other, row_goi = {}, {}, {}, {}, {}
    row_opex, row_noi, row_ads, row_cfbt = {}, {}, {}, {}
    
    # Dictionaries for After-Tax
    row_cost_recovery, row_taxable_income, row_tax_liability, row_cfat = {}, {}, {}, {}
    
    current_pri = pri
    current_other = other_income
    current_opex = final_opex # Start with Year 1 OpEx from Tab 4
    annual_ads = 0.0 
    
    basis_of_improvements = initial_investment * (improvements_pct / 100)
    total_cost_recovery_taken = 0.0

    # IRS Mid-Month Convention Rates (Assumes Month 1 Acq, Month 12 Disp)
    if property_class == "Non-Residential (39 Years)":
        acq_cr_pct, hold_cr_pct, disp_cr_pct = 0.02461, 0.02564, 0.02461
    else:
        acq_cr_pct, hold_cr_pct, disp_cr_pct = 0.03485, 0.03636, 0.03485
    
    for year in range(1, forecast_years + 1):
        col_name = f"Year {year}"
        
        # Operations (Before Tax)
        row_pri[col_name] = current_pri
        row_vac[col_name] = current_pri * (vacancy_pct / 100)
        row_eri[col_name] = current_pri - row_vac[col_name]
        row_other[col_name] = current_other
        row_goi[col_name] = row_eri[col_name] + row_other[col_name]
        
        # Calculate Expenses dynamically using the Ratio linked from Tab 4
        row_opex[col_name] = row_goi[col_name] * calculated_expense_ratio
        
        row_noi[col_name] = row_goi[col_name] - row_opex[col_name]
        row_ads[col_name] = annual_ads
        row_cfbt[col_name] = row_noi[col_name] - row_ads[col_name]
        
        # Tax Calculations (Cost Recovery)
        if year == 1:
            cr_deduction = basis_of_improvements * acq_cr_pct
        elif year == int(hold_period):
            cr_deduction = basis_of_improvements * disp_cr_pct
        else:
            cr_deduction = basis_of_improvements * hold_cr_pct
            
        if year <= int(hold_period):
            total_cost_recovery_taken += cr_deduction
            
        row_cost_recovery[col_name] = cr_deduction
        row_taxable_income[col_name] = row_noi[col_name] - cr_deduction
        
        # Tax Liability (Savings)
        tax_liab = row_taxable_income[col_name] * (ordinary_tax_rate / 100)
        row_tax_liability[col_name] = tax_liab
        
        # Cash Flow After Tax
        row_cfat[col_name] = row_cfbt[col_name] - tax_liab
        
        # Escalations for next year
        current_pri *= (1 + (pri_growth / 100))
        current_other *= (1 + (other_inc_growth / 100))
        

    # --- 4. RENDER THE OPERATIONS TABLE ---
    st.markdown("---")
    st.markdown("### 📊 Cash Flow Analysis Worksheet (Operations)")
    
    proforma_data = {
        "Potential Rental Income": row_pri,
        f" -Vacancy & Credit Losses": {k: -v for k, v in row_vac.items()}, 
        " =Effective Rental Income": row_eri,
        " =Gross Operating Income": row_goi,
        " -Operating Expenses": {k: -v for k, v in row_opex.items()},
        " =NET OPERATING INCOME": row_noi,
        " -Cost Recovery": {k: -v for k, v in row_cost_recovery.items()},
        " =Taxable Income": row_taxable_income,
        " -Tax Liability (Savings)": {k: -v for k, v in row_tax_liability.items()},
        " =CASH FLOW BEFORE TAXES": row_cfbt,
        " =CASH FLOW AFTER TAXES": row_cfat
    }
    
    df_proforma = pd.DataFrame(proforma_data).T
    st.dataframe(df_proforma.style.format("${:,.0f}"), use_container_width=True)

    # --- 5. REVERSION (SALE) CALCULATIONS ---
    st.markdown("---")
    st.markdown("### 🚪 Disposition & Alternative Cash Sales Worksheet")
    
    c_exit1, c_exit2 = st.columns(2)
    with c_exit1:
        terminal_cap_rate = st.number_input("Terminal Cap Rate (%)", value=7.5, step=0.25)
    with c_exit2:
        cost_of_sale_pct = st.number_input("Cost of Sale (%)", value=3.0, step=0.5)
        
    terminal_noi = row_noi.get(f"Year {forecast_years}", 0.0) 
    
    if terminal_cap_rate > 0:
        rounded_sale_price = round((terminal_noi / (terminal_cap_rate / 100)) / 1000) * 1000
    else:
        rounded_sale_price = 0.0
        
    cost_of_sale_dollars = rounded_sale_price * (cost_of_sale_pct / 100)
    proceeds_before_tax = rounded_sale_price - cost_of_sale_dollars

    # After-Tax Disposition Math
    adjusted_basis = initial_investment - total_cost_recovery_taken
    gain_on_sale = rounded_sale_price - cost_of_sale_dollars - adjusted_basis
    
    cap_gain_appreciation = max(0.0, gain_on_sale - total_cost_recovery_taken)
    
    # Recapture limited to total gain on sale
    recaptured_amount = min(total_cost_recovery_taken, max(0.0, gain_on_sale))
    tax_on_recapture = recaptured_amount * (recapture_tax_rate / 100)
    
    tax_on_cap_gain = cap_gain_appreciation * (cg_tax_rate / 100)
    total_tax_on_sale = tax_on_recapture + tax_on_cap_gain
    proceeds_after_tax = proceeds_before_tax - total_tax_on_sale
    
    # --- Professional Render of the CCIM Alternative Cash Sales Worksheet ---
    st.markdown("#### Alternative Cash Sales Worksheet")
    
    acsw_data = {
        "Line Item": [
            "CALCULATION OF ADJUSTED BASIS:",
            "1 Basis at Acquisition",
            "2 +Capital Additions",
            "3 -Cost Recovery (Depreciation) Taken",
            "4 -Basis in Partial Sales",
            "5 =Adjusted Basis at Sale",
            " ", # Blank row spacer
            "CALCULATION OF CAPITAL GAIN ON SALE:",
            "6 Sale Price",
            "7 -Cost of Sale",
            "8 -Adjusted Basis at Sale (Line 5)",
            "9 -Participation Payment on Sale",
            "10 =Gain or (Loss)",
            "11 -Straight Line Cost Recovery (limited to gain)",
            "12 -Suspended Losses",
            "13 =Capital Gain from Appreciation",
            "  ", # Blank row spacer
            "ITEMS TAXED AS ORDINARY INCOME:",
            "14 Unamortized Loan Fees/Costs",
            "15 + [Other]",
            "16 =Ordinary Taxable Income",
            "   ", # Blank row spacer
            "CALCULATION OF SALE PROCEEDS AFTER TAX:",
            "17 Sale Price",
            "18 -Cost of Sale",
            "19 -Participation Payment on Sale",
            "20 -Mortgage Balance(s)",
            "21 +Balance of Funded Reserves",
            "22 =Sale Proceeds Before Tax",
            f"23 -Tax (Savings) Ordinary Income at {ordinary_tax_rate:.0f}% of line 16",
            f"24 -Tax Straight Line Recapture at {recapture_tax_rate:.0f}% of line 11",
            f"25 -Tax on Capital Gains at {cg_tax_rate:.0f}% of line 13",
            "26 =SALE PROCEEDS AFTER TAX"
        ],
        "Amount": [
            None, # Header
            initial_investment,
            0.0,
            -total_cost_recovery_taken,
            0.0,
            adjusted_basis,
            None, # Spacer
            None, # Header
            rounded_sale_price,
            -cost_of_sale_dollars,
            -adjusted_basis,
            0.0,
            gain_on_sale,
            -recaptured_amount,
            0.0,
            cap_gain_appreciation,
            None, # Spacer
            None, # Header
            0.0,
            0.0,
            0.0,
            None, # Spacer
            None, # Header
            rounded_sale_price,
            -cost_of_sale_dollars,
            0.0,
            0.0,
            0.0,
            proceeds_before_tax,
            0.0,
            -tax_on_recapture,
            -tax_on_cap_gain,
            proceeds_after_tax
        ]
    }
    
    df_acsw = pd.DataFrame(acsw_data).set_index("Line Item")
    
    # Custom formatter to hide 'None' for headers/spacers and format numbers as currency
    def format_dollars(val):
        if pd.isna(val):
            return ""
        return f"${val:,.0f}"
        
    st.table(df_acsw.style.format({"Amount": format_dollars}))
    
    # --- 6. RETURN METRICS (T-BAR & IRR) ---
    st.markdown("---")
    st.markdown("### 📈 Investment Return Metrics")
    
    cfbt_stream = [-initial_investment]
    cfat_stream = [-initial_investment]
    
    for year in range(1, int(hold_period) + 1):
        if year == int(hold_period):
            cfbt_stream.append(row_cfbt[f"Year {year}"] + proceeds_before_tax)
            cfat_stream.append(row_cfat[f"Year {year}"] + proceeds_after_tax)
        else:
            cfbt_stream.append(row_cfbt[f"Year {year}"])
            cfat_stream.append(row_cfat[f"Year {year}"])

    def calculate_irr(cfs, max_iterations=1000, tolerance=1e-6):
        rate = 0.10 
        for _ in range(max_iterations):
            npv_calc = sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cfs))
            derivative = sum(-i * cf / ((1 + rate) ** (i + 1)) for i, cf in enumerate(cfs))
            if abs(derivative) < 1e-10: return 0.0 
            new_rate = rate - npv_calc / derivative
            if abs(new_rate - rate) < tolerance: return new_rate
            rate = new_rate
        return rate
        
    irr_bt = calculate_irr(cfbt_stream) * 100
    irr_at = calculate_irr(cfat_stream) * 100
    
    # CCIM Fix: Round to 2 decimals BEFORE calculating Effective Tax Rate
    irr_bt_rounded = round(irr_bt, 2)
    irr_at_rounded = round(irr_at, 2)
    
    if irr_bt_rounded > 0:
        effective_tax_rate = ((irr_bt_rounded - irr_at_rounded) / irr_bt_rounded) * 100
    else:
        effective_tax_rate = 0.0

    c_out1, c_out2, c_out3 = st.columns(3)
    c_out1.metric("Before-Tax IRR", f"{irr_bt:.2f}%")
    c_out2.metric("After-Tax IRR", f"{irr_at:.2f}%")
    c_out3.metric("Effective Tax Rate", f"{effective_tax_rate:.2f}%")
    
# ==========================================
# TAB 6: FINANCING & LOAN SIZING
# ==========================================
with tab_financing:
    st.header("Commercial Loan Sizing")
    st.markdown("Calculate the maximum loan amount by comparing LTV and DSCR constraints.")

    # Inputs based on Activity 6-3
    c_fin1, c_fin2 = st.columns(2)
    with c_fin1:
        st.markdown("#### Property & Income Constraints")
        prop_value = st.number_input("Property Estimate of Value", value=2000000.0, step=50000.0)
        prop_noi = st.number_input("Stabilized NOI", value=190000.0, step=5000.0)
        
    with c_fin2:
        st.markdown("#### Lender Underwriting Criteria")
        max_ltv = st.number_input("Maximum LTV Ratio (%)", value=75.0, step=1.0)
        min_dscr = st.number_input("Minimum DSCR", value=1.20, step=0.05)
        loan_rate = st.number_input("Interest Rate (%)", value=9.0, step=0.25)
        amort_years = st.number_input("Amortization Period (Years)", value=25, step=1)

    st.markdown("---")

    # --- STEP 1: CALCULATE LOAN AMOUNT USING LTV ---
    loan_amount_ltv = prop_value * (max_ltv / 100)

    # --- STEP 2: CALCULATE LOAN AMOUNT USING DSCR ---
    # a. Determine ADS
    max_ads = prop_noi / min_dscr
    
    # b. Determine monthly payment
    max_monthly_pmt = max_ads / 12
    
    # c. Construct T-bar & Solve for PV (Loan Amount)
    monthly_rate = (loan_rate / 100) / 12
    total_months = amort_years * 12
    
    if monthly_rate == 0:
        loan_amount_dscr = max_monthly_pmt * total_months
    else:
        # PV Formula: PV = PMT * ((1 - (1 + r)^-n) / r)
        loan_amount_dscr = max_monthly_pmt * ((1 - (1 + monthly_rate)**-total_months) / monthly_rate)

    # --- STEP 3: COMPARE AND SELECT THE LOWER AMOUNT ---
    import math
    lower_loan_amount = min(loan_amount_ltv, loan_amount_dscr)
    final_funded_loan = math.floor(lower_loan_amount / 1000) * 1000 # Round down to nearest $1,000

    # --- DISPLAY RESULTS MATCHING THE WORKBOOK ---
    st.markdown("### 📊 Loan Sizing Analysis")
    
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.info(f"**1. Loan Amount using LTV Ratio**\n\n"
                f"Value: \${prop_value:,.0f} × LTV: {max_ltv}%\n\n"
                f"**= \${loan_amount_ltv:,.0f}**")
                
    with col_res2:
        st.info(f"**2. Loan Amount using DSCR**\n\n"
                f"ADS: \${max_ads:,.0f} (PMT: \${max_monthly_pmt:,.2f})\n\n"
                f"**= \${loan_amount_dscr:,.0f}**")

    st.success(f"### 🏦 Final Recommended Loan Amount: \${final_funded_loan:,.0f}")
    st.caption("*(Based on the lower of the two calculations, rounded down to the nearest $1,000)*")
    
    # --- STEP 4: AMORTIZATION SCHEDULE (SAMPLE PROBLEM 6-9) ---
    st.markdown("---")
    st.markdown("### 📅 Annual Amortization Schedule")
    st.markdown("Calculates the principal and interest allocation based on *Sample Problem 6-9*.")

    # Dedicated inputs for the Amortization Schedule
    c_amort1, c_amort2, c_amort3, c_amort4 = st.columns(4)
    amort_pv = c_amort1.number_input("Loan Amount", value=100000.0, step=10000.0, key="amort_pv")
    amort_rate = c_amort2.number_input("Annual Interest Rate (%)", value=8.0, step=0.25, key="amort_rate")
    amort_years = c_amort3.number_input("Amortization Period (Years)", value=25, step=1, key="amort_years")
    
    # Calculate exact PMT
    r_monthly = (amort_rate / 100) / 12
    n_months = amort_years * 12
    
    if r_monthly > 0:
        monthly_pmt = amort_pv * (r_monthly * (1 + r_monthly)**n_months) / ((1 + r_monthly)**n_months - 1)
    else:
        monthly_pmt = amort_pv / n_months

    # Custom HTML/Markdown to fix and highlight the PMT font
    c_amort4.markdown(
        f"""
        <div style="text-align: left; padding: 10px; border-radius: 5px; background-color: rgba(255, 75, 75, 0.1);">
            <p style="font-size: 14px; margin-bottom: 0px; font-weight: 600;">Calculated Monthly PMT</p>
            <h2 style="color: #FF4B4B; margin-top: 0px; margin-bottom: 0px;">${monthly_pmt:,.2f}</h2>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # Build the Schedule
    amort_data = []
    chart_data = []
    current_balance = amort_pv
    
    for year in range(1, amort_years + 1):
        boy_balance = current_balance
        annual_interest = 0.0
        annual_principal = 0.0
        
        # Calculate 12 individual months to get exact annual buckets
        for month in range(12):
            if current_balance <= 0:
                break
            interest_payment = current_balance * r_monthly
            principal_payment = monthly_pmt - interest_payment
            
            annual_interest += interest_payment
            annual_principal += principal_payment
            current_balance -= principal_payment
            
        # Save ALL years for the table to show the full schedule
        amort_data.append({
            "Year": year,
            "BOY Balance": boy_balance,
            "Interest": annual_interest,
            "Principal": annual_principal,
            "EOY Balance": current_balance if current_balance > 0.01 else 0.0
        })
            
        # Save all years for the chart
        chart_data.append({
            "Year": year,
            "Interest": annual_interest,
            "Principal": annual_principal
        })

    # Render Table (Full Schedule, Scrollable embedded container)
    st.markdown("#### Full Amortization Table")
    df_amort = pd.DataFrame(amort_data)
    
    # The 'height' parameter makes it scrollable while taking up limited vertical space
    st.dataframe(df_amort.style.format({
        "BOY Balance": "${:,.2f}",
        "Interest": "${:,.2f}",
        "Principal": "${:,.2f}",
        "EOY Balance": "${:,.2f}"
    }), height=400, hide_index=True, use_container_width=True)

    # Render Chart (Figure 6.6)
    st.markdown("#### Figure 6.6: Allocation of ADS")
    df_chart = pd.DataFrame(chart_data).set_index("Year")
    st.area_chart(df_chart[["Interest", "Principal"]])