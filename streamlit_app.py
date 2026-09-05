import streamlit as st
import pandas as pd
from pathlib import Path

# -----------------------------------
# PAGE SETTINGS
# -----------------------------------

st.set_page_config(
    page_title="Healthcare Analytics Dashboard",
    layout="wide"
)

# -----------------------------------
# GET APP FOLDER
# -----------------------------------

BASE_DIR = Path(__file__).parent

# -----------------------------------
# FIND EXCEL FILE
# -----------------------------------

excel_files = list(BASE_DIR.glob("*.xlsx"))

if not excel_files:
    st.error("No Excel file found in the app folder.")
    st.stop()

file_path = excel_files[0]

# -----------------------------------
# READ EXCEL FILE
# -----------------------------------

all_sheets = pd.read_excel(
    file_path,
    sheet_name=None
)

# Find the sheet containing the actual data
df = None

for sheet_name, sheet_data in all_sheets.items():

    sheet_data.columns = (
        sheet_data.columns
        .astype(str)
        .str.strip()
    )

    # Check for Date column
    if any(
        "date" in column.lower()
        for column in sheet_data.columns
    ):
        df = sheet_data
        break

if df is None:
    st.error("Could not find the healthcare data sheet.")
    st.write("Sheets found:")
    st.write(list(all_sheets.keys()))
    st.stop()

# -----------------------------------
# FIND DATE COLUMN
# -----------------------------------

date_column = None

for column in df.columns:

    if column.lower() == "date":
        date_column = column
        break

if date_column is None:

    for column in df.columns:

        if "date" in column.lower():
            date_column = column
            break

if date_column is None:
    st.error("Date column was not found.")
    st.write(list(df.columns))
    st.stop()

df.rename(
    columns={date_column: "Date"},
    inplace=True
)

# Convert date
df["Date"] = pd.to_datetime(
    df["Date"],
    dayfirst=True,
    errors="coerce"
)

# Remove invalid dates
df = df.dropna(subset=["Date"])

# -----------------------------------
# FIND DATA COLUMNS
# -----------------------------------

def find_column(keyword):

    for column in df.columns:

        if keyword.lower() in column.lower():
            return column

    return None


apprehended_col = find_column("apprehended")

transferred_col = find_column("transferred out")

hhs_col = find_column("HHS Care")

discharged_col = find_column("discharged")

custody_col = find_column("CBP custody")

# -----------------------------------
# CHECK COLUMNS
# -----------------------------------

required_columns = {
    "Apprehended": apprehended_col,
    "Transferred": transferred_col,
    "HHS Care": hhs_col,
    "Discharged": discharged_col,
    "CBP Custody": custody_col
}

missing = [
    name
    for name, column in required_columns.items()
    if column is None
]

if missing:

    st.error("Some required columns were not found.")

    st.write("Missing columns:")
    st.write(missing)

    st.write("Columns found in Excel:")
    st.write(list(df.columns))

    st.stop()

# -----------------------------------
# CONVERT NUMBERS
# -----------------------------------

for column in [
    apprehended_col,
    transferred_col,
    hhs_col,
    discharged_col,
    custody_col
]:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    ).fillna(0)

# -----------------------------------
# TITLE
# -----------------------------------

st.title("Healthcare Analytics Dashboard")

st.write(
    "Interactive dashboard for healthcare care, custody, "
    "transfer and discharge analysis."
)

# -----------------------------------
# KPI CALCULATIONS
# -----------------------------------

total_apprehended = df[apprehended_col].sum()

total_transferred = df[transferred_col].sum()

total_hhs = df[hhs_col].sum()

total_discharged = df[discharged_col].sum()

# -----------------------------------
# KPI CARDS
# -----------------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Children Apprehended",
    f"{total_apprehended:,.0f}"
)

col2.metric(
    "Children Transferred",
    f"{total_transferred:,.0f}"
)

col3.metric(
    "Children in HHS Care",
    f"{total_hhs:,.0f}"
)

col4.metric(
    "Children Discharged",
    f"{total_discharged:,.0f}"
)

st.divider()

# -----------------------------------
# MONTHLY STAGE DISTRIBUTION
# -----------------------------------

df["Month"] = (
    df["Date"]
    .dt.to_period("M")
    .astype(str)
)

monthly = df.groupby("Month").agg({

    apprehended_col: "sum",

    transferred_col: "sum",

    discharged_col: "sum"

}).reset_index()

st.subheader("Monthly Stage Distribution")

monthly_chart = monthly.set_index("Month")

st.line_chart(monthly_chart)

st.divider()

# -----------------------------------
# HHS CARE BY YEAR
# -----------------------------------

yearly_hhs = df.groupby(
    df["Date"].dt.year
)[hhs_col].sum()

st.subheader("HHS Care by Year")

st.bar_chart(yearly_hhs)

st.divider()

# -----------------------------------
# CBP CUSTODY TREND
# -----------------------------------

st.subheader("CBP Custody Trend")

custody = (
    df
    .sort_values("Date")
    .set_index("Date")[custody_col]
)

st.line_chart(custody)

st.divider()

# -----------------------------------
# DATA TABLE
# -----------------------------------
st.subheader("CBP Custody Details")

display_columns = [
    "Date",
    apprehended_col,
    custody_col,
    transferred_col,
    hhs_col,
    discharged_col
]

# Create a clean copy for the table
table_data = df[display_columns].copy()

# Convert Date to text for safe display
table_data["Date"] = table_data["Date"].dt.strftime("%Y-%m-%d")

# Make sure numeric columns are numbers
for column in display_columns[1:]:
    table_data[column] = pd.to_numeric(
        table_data[column],
        errors="coerce"
    ).fillna(0)

# Display table
st.dataframe(
    table_data.sort_values("Date"),
    use_container_width=True
)
