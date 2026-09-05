import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Healthcare Analytics Dashboard",
    layout="wide"
)

# Load dataset
df = pd.read_excel("HHS_Cleaned_Dataset.xlsx")

# Convert date
df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

st.title("Healthcare Analytics Dashboard")
st.write(
    "Interactive dashboard for healthcare care, custody, "
    "transfer and discharge analysis."
)

# KPI calculations
total_apprehended = df[
    "Children apprehended and placed in CBP custody*"
].sum()

total_transferred = df[
    "Children transferred out of CBP custody"
].sum()

total_hhs = df[
    "Children in HHS Care"
].sum()

total_discharged = df[
    "Children discharged from HHS Care"
].sum()

# KPI cards
col1, col2, col3, col4 = st.columns(4)

col1.metric("Children Apprehended", f"{total_apprehended:,.0f}")
col2.metric("Children Transferred", f"{total_transferred:,.0f}")
col3.metric("Children in HHS Care", f"{total_hhs:,.0f}")
col4.metric("Children Discharged", f"{total_discharged:,.0f}")

st.divider()

# Monthly data
df["Month"] = df["Date"].dt.to_period("M").astype(str)

monthly = df.groupby("Month").agg({
    "Children apprehended and placed in CBP custody*": "sum",
    "Children transferred out of CBP custody": "sum",
    "Children discharged from HHS Care": "sum"
}).reset_index()

st.subheader("Monthly Stage Distribution")

monthly_chart = monthly.set_index("Month")

st.line_chart(monthly_chart)

st.divider()

# HHS Care trend
yearly_hhs = df.groupby(
    df["Date"].dt.year
)["Children in HHS Care"].sum()

st.subheader("HHS Care by Year")
st.bar_chart(yearly_hhs)

st.divider()

# CBP custody trend
st.subheader("CBP Custody Trend")

custody = df.set_index("Date")[
    "Children in CBP custody"
]

st.line_chart(custody)

st.divider()

# Data table
st.subheader("CBP Custody Details")

st.dataframe(
    df[
        [
            "Date",
            "Children apprehended and placed in CBP custody*",
            "Children in CBP custody",
            "Children transferred out of CBP custody",
            "Children in HHS Care",
            "Children discharged from HHS Care"
        ]
    ],
    use_container_width=True
)
