import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="FinMate - Your Smart Money Friend", layout="wide")

# ---------- Custom CSS theme (background + cards + fonts) ---------- #
FINMATE_CSS = """
<style>
/* Overall app background */
.stApp {
    background: radial-gradient(circle at 0% 0%, #1e293b 0, #020617 45%, #000000 100%);
    color: #e5e7eb;
    font-family: "system-ui", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

/* Main content container (the center panel) */
.main .block-container {
    background: rgba(15, 23, 42, 0.92); /* slate-900 with opacity */
    border-radius: 24px;
    padding: 2.5rem 2.5rem 2.5rem 2.5rem;
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.7);
    border: 1px solid rgba(148, 163, 184, 0.25);
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617 0%, #0f172a 40%, #020617 100%);
    border-right: 1px solid rgba(148, 163, 184, 0.3);
}

[data-testid="stSidebar"] * {
    color: #e5e7eb;
}

/* Titles & headings */
h1, h2, h3, h4 {
    color: #f9fafb;
    letter-spacing: 0.03em;
}

/* KPI metric numbers */
[data-testid="stMetricValue"] {
    color: #f97316;  /* warm accent */
    font-weight: 700;
}

/* Tables */
[data-testid="stDataFrame"] {
    border-radius: 16px;
    overflow: hidden;
}

/* Links + accent elements */
a {
    color: #38bdf8;
}
a:hover {
    color: #f97316;
}

/* Small footer text */
.finmate-footer {
    color: #9ca3af;
    font-size: 0.75rem;
    text-align: center;
    margin-top: 1.5rem;
}
</style>
"""

st.markdown(FINMATE_CSS, unsafe_allow_html=True)

st.title("FinMate - Your Smart Money Friend")
st.write("ISOM 839 – Prescriptive Analytics Final Project")
st.write(
    "Upload your transaction file, use the built-in sample data, or try a quick manual scenario "
    "to see your spending breakdown and some simple budget recommendations."
)

# ----------------- Config: target budget shares ----------------- #
TARGET_BUDGET = {
    "Rent": 0.40,
    "Groceries": 0.15,
    "Eating Out": 0.10,
    "Transport": 0.10,
    "Shopping": 0.10,
    "Subscriptions": 0.05,
    "Other": 0.10,
}

# ----------------- Sidebar: data source + settings ----------------- #
st.sidebar.header("1. Data Input Mode")

data_mode = st.sidebar.radio(
    "Choose input mode",
    ["CSV / Sample file", "Quick manual test"],
)

def load_sample_data() -> pd.DataFrame:
    df = pd.read_csv("sample_data.csv")
    return df

df = None  # will hold the final dataframe

if data_mode == "CSV / Sample file":
    st.sidebar.subheader("From file")
    uploaded_file = st.sidebar.file_uploader(
        "Upload CSV (date, category, amount, type)", type=["csv"]
    )
    use_sample = st.sidebar.checkbox(
        "Use bundled sample data (sample_data.csv)", value=True
    )

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    elif use_sample:
        df = load_sample_data()
    else:
        st.warning("Please upload a CSV file or select the sample data option in the sidebar.")
        st.stop()

else:  # Manual quick test
    st.sidebar.subheader("Manual monthly scenario")
    st.sidebar.caption("Enter your monthly income and spending by category.")

    income_manual = st.sidebar.number_input(
        "Monthly income ($)", min_value=0.0, value=1800.0, step=50.0
    )

    rent = st.sidebar.number_input("Rent ($)", min_value=0.0, value=1200.0, step=25.0)
    groceries = st.sidebar.number_input("Groceries ($)", min_value=0.0, value=250.0, step=10.0)
    eating_out = st.sidebar.number_input("Eating Out ($)", min_value=0.0, value=150.0, step=10.0)
    transport = st.sidebar.number_input("Transport ($)", min_value=0.0, value=90.0, step=5.0)
    shopping = st.sidebar.number_input("Shopping ($)", min_value=0.0, value=150.0, step=10.0)
    subs = st.sidebar.number_input("Subscriptions ($)", min_value=0.0, value=30.0, step=5.0)
    other = st.sidebar.number_input("Other ($)", min_value=0.0, value=60.0, step=5.0)

    # Build a simple one-month dataframe with the same schema as the CSV
    rows = [{"date": "2025-11-01", "category": "Income", "amount": income_manual, "type": "income"}]

    def add_row(cat, amt):
        if amt > 0:
            rows.append(
                {"date": "2025-11-01", "category": cat, "amount": amt, "type": "expense"}
            )

    add_row("Rent", rent)
    add_row("Groceries", groceries)
    add_row("Eating Out", eating_out)
    add_row("Transport", transport)
    add_row("Shopping", shopping)
    add_row("Subscriptions", subs)
    add_row("Other", other)

    df = pd.DataFrame(rows)

# Ensure correct dtypes
df["date"] = pd.to_datetime(df["date"])

st.sidebar.header("2. Savings Goal")
desired_savings_rate = st.sidebar.slider(
    "Desired savings rate (% of income)", min_value=5, max_value=50, value=20, step=1
)

# ----------------- Analytics: KPIs ----------------- #
income = df.loc[df["type"] == "income", "amount"].sum()
expenses = df.loc[df["type"] == "expense", "amount"].sum()
net_savings = income - expenses
savings_rate = (net_savings / income * 100) if income > 0 else 0

st.subheader("Overview")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Income", f"${income:,.0f}")
kpi2.metric("Total Expenses", f"${expenses:,.0f}")
kpi3.metric("Net Savings", f"${net_savings:,.0f}")
kpi4.metric("Savings Rate", f"{savings_rate:,.1f}%")

if income <= 0:
    st.warning(
        "No income detected in the data. "
        "Please include at least one row with type = 'income' or enter income in manual mode."
    )

# ----------------- Spending by category ----------------- #
st.subheader("Spending by Category")

expense_df = df[df["type"] == "expense"].copy()
category_summary = (
    expense_df.groupby("category", as_index=False)["amount"].sum()
)
category_summary["share_of_income"] = (
    category_summary["amount"] / income if income > 0 else 0
)

def classify_category(row):
    cat = row["category"]
    actual = row["share_of_income"]
    target = TARGET_BUDGET.get(cat, 0.10)
    if actual <= target + 0.02:
        return "OK"
    elif actual <= target + 0.05:
        return "Caution"
    else:
        return "Critical"

if income > 0 and not category_summary.empty:
    category_summary["status"] = category_summary.apply(classify_category, axis=1)
else:
    category_summary["status"] = "N/A"

# -------- Bar chart (amount by category) -------- #
bar_col, pie_col = st.columns(2)

with bar_col:
    st.caption("Total spend ($) by category")
    if not category_summary.empty:
        bar_chart = (
            alt.Chart(category_summary)
            .mark_bar()
            .encode(
                x=alt.X("category:N", title="Category"),
                y=alt.Y("amount:Q", title="Total spend ($)"),
                tooltip=["category", "amount"],
            )
        )
        st.altair_chart(bar_chart, use_container_width=True)
    else:
        st.info("No expense data to display.")

# -------- Pie chart (share of income) -------- #
with pie_col:
    st.caption("Share of income by category")
    if income > 0 and not category_summary.empty:
        pie_data = category_summary.copy()
        pie_data["share_pct"] = pie_data["share_of_income"] * 100

        pie_chart = (
            alt.Chart(pie_data)
            .mark_arc()
            .encode(
                theta=alt.Theta("share_pct:Q", title="Share of income (%)"),
                color=alt.Color("category:N", legend=alt.Legend(title="Category")),
                tooltip=["category", alt.Tooltip("share_pct:Q", format=".1f")]
            )
        )
        st.altair_chart(pie_chart, use_container_width=True)
    else:
        st.info("Pie chart requires income and expense data to compute shares.")

# -------- Table with status -------- #
st.subheader("Budget Status by Category")

display_table = category_summary.copy()
display_table["share_of_income"] = (display_table["share_of_income"] * 100).round(1)
display_table = display_table.rename(
    columns={
        "amount": "Amount ($)",
        "share_of_income": "Share of Income (%)",
        "status": "Status",
    }
)
st.dataframe(display_table, hide_index=True)

# ----------------- Recommendations ----------------- #
st.subheader("Recommendations")

if income <= 0:
    st.warning(
        "Cannot compute recommendations without income. "
        "Add income rows or use manual mode to enter your monthly income."
    )
else:
    target_savings_amount = income * (desired_savings_rate / 100)
    savings_gap = target_savings_amount - net_savings

    if savings_gap <= 0:
        st.success(
            f"Great job! You're already meeting or exceeding your savings goal "
            f"of {desired_savings_rate}% 🎉"
        )
    else:
        st.write(
            f"To reach your savings goal of **{desired_savings_rate}%**, "
            f"you need to save about **${savings_gap:,.0f}** more in this period."
        )

        overspend = category_summary[category_summary["status"].isin(["Caution", "Critical"])].copy()
        overspend["target_share"] = overspend["category"].map(TARGET_BUDGET).fillna(0.10)
        overspend["target_amount"] = overspend["target_share"] * income
        overspend["excess_amount"] = (overspend["amount"] - overspend["target_amount"]).clip(lower=0)

        total_excess = overspend["excess_amount"].sum()

        if total_excess <= 0:
            st.info(
                "Your categories are close to the recommended targets. "
                "Consider small reductions in non-essential categories to close the savings gap."
            )
        else:
            overspend["suggested_cut"] = overspend["excess_amount"] * min(1, savings_gap / total_excess)

            st.write("Suggested category-wise adjustments:")
            suggestion_table = overspend[
                ["category", "amount", "target_amount", "excess_amount", "suggested_cut"]
            ].round(0)
            suggestion_table = suggestion_table.rename(
                columns={
                    "category": "Category",
                    "amount": "Current Spend ($)",
                    "target_amount": "Recommended Spend ($)",
                    "excess_amount": "Excess Spend ($)",
                    "suggested_cut": "Suggested Cut ($)",
                }
            )
            st.dataframe(suggestion_table, hide_index=True)

            st.markdown("**Suggestions:**")
for _, row in overspend.iterrows():
    if row["suggested_cut"] > 0:
        sentence = (
            f"- Reduce {row['category']} spending by about ${row['suggested_cut']:.0f}, "
            f"from ${row['amount']:.0f} to ${row['target_amount']:.0f}."
        )
        st.text(sentence)


st.markdown(
    '<div class="finmate-footer">'
    'FinMate – ISOM 839 Prescriptive Analytics (Track B) – '
    'Created by Vallariie Chindarkar'
    '</div>',
    unsafe_allow_html=True,
)
