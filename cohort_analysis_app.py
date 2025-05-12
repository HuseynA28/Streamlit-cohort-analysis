import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("🧾 Cohort Analysis Dashboard")
st.markdown("""
This app provides a **Cohort Analysis** of customers based on their purchasing behavior. 
Explore customer retention trends and patterns through intuitive visualizations.
""")

@st.cache_data
def load_data():
    df = pd.read_csv("dataset/year_2009-2010.csv", encoding="latin-1")
    df = df[['InvoiceDate', 'Customer ID', 'Price', 'Quantity', 'Invoice', 'Description']]
    df.dropna(inplace=True)
    df.drop_duplicates(inplace=True)
    df['revenue'] = df['Price'] * df['Quantity']
    df.rename(columns={'Customer ID': 'customer_id', 
                       'InvoiceDate': 'order_date', 
                       'Invoice': 'order_id'}, inplace=True)
    df.drop(columns=['Price', 'Quantity'], inplace=True)
    df['customer_id'] = df['customer_id'].astype(int)
    df['order_date'] = pd.to_datetime(df['order_date'])
    return df

orders = load_data()

# ================================
# SIDEBAR FILTERS & CONTROLS
# ================================

st.sidebar.header("Filters")

# 1) Date Range Filter
min_date = orders["order_date"].min()
max_date = orders["order_date"].max()
selected_dates = st.sidebar.date_input(
    "Select Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# If user only picks one date, make sure it's handled
if len(selected_dates) == 1:
    start_date = selected_dates[0]
    end_date = selected_dates[0]
else:
    start_date, end_date = selected_dates[0], selected_dates[1]

# 2) Revenue Threshold Slider
min_revenue, max_revenue = float(orders["revenue"].min()), float(orders["revenue"].max())
revenue_threshold = st.sidebar.slider(
    "Minimum Revenue Threshold",
    min_value=min_revenue,
    max_value=max_revenue,
    value=min_revenue
)

# 3) Chart Selection
chart_option = st.sidebar.selectbox(
    "Choose a Chart",
    ("Retention Heatmap", "Monthly Revenue per Cohort")
)

# Filter the Data Based on User Input
orders_filtered = orders[
    (orders["order_date"] >= pd.to_datetime(start_date)) & 
    (orders["order_date"] <= pd.to_datetime(end_date)) & 
    (orders["revenue"] >= revenue_threshold)
]

# ================================
# COHORT PREPROCESSING
# ================================

orders_filtered["order_month"] = orders_filtered["order_date"].dt.to_period("M")
cohort_data = orders_filtered.groupby("customer_id")["order_month"].min().reset_index()
cohort_data.columns = ["customer_id", "cohort_month"]
orders_filtered = pd.merge(orders_filtered, cohort_data, on="customer_id")

orders_filtered["cohort_index"] = (
    (orders_filtered["order_month"].dt.year - orders_filtered["cohort_month"].dt.year) * 12 +
    (orders_filtered["order_month"].dt.month - orders_filtered["cohort_month"].dt.month) + 1
)

# Build Retention Matrix
retention = orders_filtered.groupby(["cohort_month", "cohort_index"])["customer_id"].nunique().reset_index()
cohort_sizes = retention[retention["cohort_index"] == 1][["cohort_month", "customer_id"]]
cohort_sizes.rename(columns={"customer_id": "cohort_size"}, inplace=True)
retention = pd.merge(retention, cohort_sizes, on="cohort_month")
retention["retention_rate"] = retention["customer_id"] / retention["cohort_size"]
retention_pivot = retention.pivot(index="cohort_month", columns="cohort_index", values="retention_rate")

# Prepare Revenue Data
monthly_revenue = orders_filtered.groupby(["cohort_month", "cohort_index"])["revenue"].sum().reset_index()
pivot_rev = monthly_revenue.pivot(index="cohort_index", columns="cohort_month", values="revenue")

# ================================
# MAIN DASHBOARD CONTENT
# ================================

st.markdown("**Filtered Date Range:** {} to {}".format(
    start_date.strftime("%Y-%m-%d"), 
    end_date.strftime("%Y-%m-%d"),
))
st.markdown(f"**Minimum Revenue:** {revenue_threshold:.2f}")

st.subheader("Data Preview (Filtered)")
if not orders_filtered.empty:
    st.write(orders_filtered.head())
    st.write(f"Total Records: {len(orders_filtered)}")
else:
    st.warning("No data available for the selected filters.")

# Show the chosen chart
if chart_option == "Retention Heatmap":
    st.subheader("📊 Retention Rate Heatmap")
    st.markdown("This heatmap shows the **retention rate** of customers per cohort over time.")
    if retention_pivot.empty:
        st.error("No retention data available for the selected filters.")
    else:
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.heatmap(retention_pivot, annot=True, fmt=".0%", cmap="Blues", ax=ax)
        plt.title("Customer Retention Rates")
        st.pyplot(fig)

elif chart_option == "Monthly Revenue per Cohort":
    st.subheader("💰 Monthly Revenue per Cohort")
    st.markdown("Line plot showing the **total revenue** generated by each cohort per month.")
    if pivot_rev.empty:
        st.error("No revenue data available for the selected filters.")
    else:
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        pivot_rev.plot(ax=ax2)
        plt.title("Monthly Revenue by Cohort")
        plt.xlabel("Cohort Index (Months)")
        plt.ylabel("Revenue")
        st.pyplot(fig2)