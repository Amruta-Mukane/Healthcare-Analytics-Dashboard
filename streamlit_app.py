import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="USA Care and Reunification Analytics",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

    /* Main background */
    .stApp {
        background-color: #F7F9FC;
    }

    /* Main title */
    .main-title {
        color: #17365D;
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        color: #666666;
        font-size: 14px;
        margin-bottom: 20px;
    }

    /* KPI cards */
    .kpi-card {
        background-color: white;
        border-radius: 12px;
        padding: 15px 10px;
        text-align: center;
        min-height: 105px;
        border-left: 5px solid #17365D;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.08);
    }

    .kpi-value {
        color: #17365D;
        font-size: 27px;
        font-weight: 700;
        margin-top: 5px;
    }

    .kpi-label {
        color: #555555;
        font-size: 13px;
        line-height: 1.2;
    }

    /* Section title */
    .section-title {
        color: #17365D;
        font-size: 19px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    /* Chart containers */
    .chart-box {
        background-color: white;
        border-radius: 12px;
        padding: 10px;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #EAF3FC;
    }

</style>
""", unsafe_allow_html=True)

# ============================================================
# FIND APPLICATION DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).parent

# ============================================================
# FIND EXCEL FILE
# ============================================================

excel_files = list(BASE_DIR.glob("*.xlsx"))

if not excel_files:
    st.error("❌ No Excel file found in the application folder.")
    st.info(
        "Please upload your Excel dataset to the same GitHub repository "
        "as streamlit_app.py."
    )
    st.stop()

# Prefer cleaned file
cleaned_files = [
    file for file in excel_files
    if "clean" in file.name.lower()
]

if cleaned_files:
    file_path = cleaned_files[0]
else:
    file_path = excel_files[0]

# ============================================================
# LOAD ALL EXCEL SHEETS
# ============================================================

try:

    all_sheets = pd.read_excel(
        file_path,
        sheet_name=None
    )

except Exception as e:

    st.error("❌ Could not read the Excel file.")
    st.write(e)
    st.stop()

# ============================================================
# FIND THE CORRECT DATA SHEET
# ============================================================

df = None
selected_sheet = None

for sheet_name, sheet_data in all_sheets.items():

    sheet_data = sheet_data.copy()

    sheet_data.columns = (
        sheet_data.columns
        .astype(str)
        .str.strip()
    )

    has_date = any(
        "date" in column.lower()
        for column in sheet_data.columns
    )

    if has_date:

        df = sheet_data
        selected_sheet = sheet_name
        break

if df is None:

    st.error("❌ Could not find a sheet containing a Date column.")

    st.write(
        "Available sheets:",
        list(all_sheets.keys())
    )

    st.stop()

# ============================================================
# FIND DATE COLUMN
# ============================================================

date_column = None

# First try exact Date
for column in df.columns:

    if column.lower().strip() == "date":
        date_column = column
        break

# Otherwise find column containing date
if date_column is None:

    for column in df.columns:

        if "date" in column.lower():
            date_column = column
            break

if date_column is None:

    st.error("❌ Date column was not found.")
    st.stop()

# Rename to Date
df.rename(
    columns={
        date_column: "Date"
    },
    inplace=True
)

# ============================================================
# CONVERT DATE
# ============================================================

df["Date"] = pd.to_datetime(
    df["Date"],
    dayfirst=True,
    errors="coerce"
)

# Remove invalid dates
df = df.dropna(
    subset=["Date"]
).copy()

# ============================================================
# FIND DATA COLUMNS
# ============================================================

def find_column(keywords):

    if isinstance(keywords, str):
        keywords = [keywords]

    for column in df.columns:

        column_lower = column.lower()

        for keyword in keywords:

            if keyword.lower() in column_lower:
                return column

    return None


apprehended_col = find_column([
    "apprehended"
])

transferred_col = find_column([
    "transferred out",
    "transferred"
])

hhs_col = find_column([
    "hhs care",
    "hhs"
])

discharged_col = find_column([
    "discharged"
])

custody_col = find_column([
    "cbp custody",
    "custody"
])

# ============================================================
# CHECK REQUIRED COLUMNS
# ============================================================

required_columns = {
    "Children Apprehended": apprehended_col,
    "Children Transferred": transferred_col,
    "Children in HHS Care": hhs_col,
    "Children Discharged": discharged_col,
    "CBP Custody": custody_col
}

missing_columns = [
    name
    for name, column in required_columns.items()
    if column is None
]

if missing_columns:

    st.error("❌ Some required columns were not found.")

    st.write(
        "Missing columns:",
        missing_columns
    )

    st.write(
        "Columns available in Excel:"
    )

    st.write(
        list(df.columns)
    )

    st.stop()

# ============================================================
# CONVERT DATA COLUMNS TO NUMBERS
# ============================================================

data_columns = [
    apprehended_col,
    transferred_col,
    hhs_col,
    discharged_col,
    custody_col
]

for column in data_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    ).fillna(0)

# ============================================================
# CREATE TIME COLUMNS
# ============================================================

df["Year"] = df["Date"].dt.year

df["Month Number"] = df["Date"].dt.month

df["Month"] = df["Date"].dt.month_name()

month_order = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December"
]

# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">USA Care and Reunification Analytics</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Interactive dashboard for analyzing child care, custody, '
    'transfer, discharge and reunification-related data.'
    '</div>',
    unsafe_allow_html=True
)

# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.markdown("## 📅 Filters")

# Year selection
years = sorted(
    df["Year"].dropna().unique()
)

years = [int(year) for year in years]

latest_year = max(years)

selected_year = st.sidebar.selectbox(
    "Select Year",
    years,
    index=years.index(latest_year)
)

# Month selection
selected_month = st.sidebar.selectbox(
    "Select Month",
    ["All Months"] + month_order
)

# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = df[
    df["Year"] == selected_year
].copy()

if selected_month != "All Months":

    filtered_df = filtered_df[
        filtered_df["Month"] == selected_month
    ].copy()

# ============================================================
# KPI CALCULATIONS
# ============================================================

total_apprehended = filtered_df[
    apprehended_col
].sum()

total_transferred = filtered_df[
    transferred_col
].sum()

total_custody = filtered_df[
    custody_col
].sum()

total_hhs = filtered_df[
    hhs_col
].sum()

total_discharged = filtered_df[
    discharged_col
].sum()

# Peak monthly custody
year_data_for_peak = df[
    df["Year"] == selected_year
].copy()

monthly_custody = (
    year_data_for_peak
    .groupby("Month Number")[custody_col]
    .sum()
)

if len(monthly_custody) > 0:
    peak_monthly_custody = monthly_custody.max()
else:
    peak_monthly_custody = 0

# ============================================================
# KPI HEADER
# ============================================================

st.markdown(
    f"### 📊 Key Performance Indicators — {selected_year}"
)

k1, k2, k3, k4, k5, k6 = st.columns(6)

kpi_data = [
    (
        k1,
        "Children Apprehended",
        total_apprehended
    ),
    (
        k2,
        "Children Transferred",
        total_transferred
    ),
    (
        k3,
        "CBP Custody",
        total_custody
    ),
    (
        k4,
        "Children in HHS Care",
        total_hhs
    ),
    (
        k5,
        "Children Discharged",
        total_discharged
    ),
    (
        k6,
        "Peak Monthly Custody",
        peak_monthly_custody
    )
]

for col, label, value in kpi_data:

    with col:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">
                    {value:,.0f}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

st.write("")

# ============================================================
# ROW 1
# ANNUAL DISCHARGE | HHS CARE | STAGE OVERVIEW
# ============================================================

col1, col2, col3 = st.columns([1.25, 1, 1])

# ============================================================
# ANNUAL DISCHARGE OUTCOMES
# ============================================================

with col1:

    st.markdown(
        '<div class="section-title">'
        'Annual Discharge Outcomes'
        '</div>',
        unsafe_allow_html=True
    )

    annual_discharge = (
        df.groupby("Year")[discharged_col]
        .sum()
        .sort_index()
    )

    if len(annual_discharge) >= 2:

        years_list = list(
            annual_discharge.index
        )

        values = list(
            annual_discharge.values
        )

        measures = []
        x_values = []
        y_values = []

        previous = 0

        for i, (year, value) in enumerate(
            zip(years_list, values)
        ):

            if i == 0:

                measures.append("absolute")
                x_values.append(str(year))
                y_values.append(value)

            else:

                change = value - previous

                if change >= 0:
                    measure = "relative"
                else:
                    measure = "relative"

                measures.append(measure)
                x_values.append(str(year))
                y_values.append(change)

            previous = value

        fig = go.Figure(
            go.Waterfall(
                x=x_values,
                y=y_values,
                measure=measures,
                textposition="outside"
            )
        )

    else:

        annual_chart = pd.DataFrame({
            "Year": annual_discharge.index.astype(str),
            "Discharged": annual_discharge.values
        })

        fig = px.bar(
            annual_chart,
            x="Year",
            y="Discharged",
            text_auto=".2s"
        )

    fig.update_layout(
        height=320,
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10
        ),
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ============================================================
# HHS CARE BY YEAR
# ============================================================

with col2:

    st.markdown(
        '<div class="section-title">'
        'HHS Care by Year'
        '</div>',
        unsafe_allow_html=True
    )

    yearly_hhs = (
        df.groupby("Year")[hhs_col]
        .sum()
        .reset_index()
    )

    yearly_hhs.columns = [
        "Year",
        "HHS Care"
    ]

    fig = px.bar(
        yearly_hhs,
        x="Year",
        y="HHS Care",
        text_auto=".2s"
    )

    fig.update_layout(
        height=320,
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ============================================================
# STAGE OVERVIEW
# ============================================================

with col3:

    st.markdown(
        '<div class="section-title">'
        'Stage Overview'
        '</div>',
        unsafe_allow_html=True
    )

    stage_data = pd.DataFrame({
        "Stage": [
            "Children Apprehended",
            "Children Transferred",
            "Children in CBP Custody",
            "Children Discharged",
            "Children in HHS Care"
        ],
        "Value": [
            total_apprehended,
            total_transferred,
            total_custody,
            total_discharged,
            total_hhs
        ]
    })

    fig = px.bar(
        stage_data,
        x="Value",
        y="Stage",
        orientation="h",
        text_auto=".2s"
    )

    fig.update_layout(
        height=320,
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

st.divider()

# ============================================================
# ROW 2
# MONTHLY DISTRIBUTION | TRANSITION RATE | STAGE DISTRIBUTION
# ============================================================

col1, col2, col3 = st.columns([1.25, 1, 1])

# ============================================================
# MONTHLY STAGE DISTRIBUTION
# ============================================================

with col1:

    st.markdown(
        '<div class="section-title">'
        'Monthly Stage Distribution'
        '</div>',
        unsafe_allow_html=True
    )

    monthly = (
        df[
            df["Year"] == selected_year
        ]
        .groupby(
            ["Month Number", "Month"]
        )
        .agg({
            apprehended_col: "sum",
            transferred_col: "sum",
            discharged_col: "sum"
        })
        .reset_index()
        .sort_values("Month Number")
    )

    monthly = monthly.rename(
        columns={
            apprehended_col: "Apprehended",
            transferred_col: "Transferred",
            discharged_col: "Discharged"
        }
    )

    monthly_long = monthly.melt(
        id_vars=[
            "Month Number",
            "Month"
        ],
        value_vars=[
            "Apprehended",
            "Transferred",
            "Discharged"
        ],
        var_name="Stage",
        value_name="Children"
    )

    fig = px.bar(
        monthly_long,
        x="Month",
        y="Children",
        color="Stage",
        barmode="group"
    )

    fig.update_layout(
        height=320,
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10
        ),
        xaxis={
            "categoryorder": "array",
            "categoryarray": month_order
        }
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ============================================================
# HHS TRANSITION RATE
# ============================================================

with col2:

    st.markdown(
        '<div class="section-title">'
        'HHS Transition Rate'
        '</div>',
        unsafe_allow_html=True
    )

    # Transition rate calculation
    # Here discharge is compared with HHS Care.
    if total_hhs > 0:

        transition_rate = (
            total_discharged /
            total_hhs
        ) * 100

    else:

        transition_rate = 0

    # Keep value between 0 and 100 for gauge
    gauge_value = min(
        max(transition_rate, 0),
        100
    )

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=gauge_value,
            number={
                "suffix": "%",
                "font": {
                    "size": 30
                }
            },
            gauge={
                "axis": {
                    "range": [0, 100]
                },
                "bar": {
                    "thickness": 0.35
                },
                "steps": [
                    {
                        "range": [0, 50],
                    },
                    {
                        "range": [50, 75],
                    },
                    {
                        "range": [75, 100],
                    }
                ]
            }
        )
    )

    fig.update_layout(
        height=320,
        margin=dict(
            l=10,
            r=10,
            t=20,
            b=10
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.caption(
        "Calculated as discharged children divided by "
        "children in HHS care."
    )

# ============================================================
# STAGE DISTRIBUTION DONUT
# ============================================================

with col3:

    st.markdown(
        '<div class="section-title">'
        'Stage Distribution'
        '</div>',
        unsafe_allow_html=True
    )

    stage_distribution = pd.DataFrame({
        "Stage": [
            "Apprehended",
            "Transferred",
            "CBP Custody",
            "Discharged",
            "HHS Care"
        ],
        "Value": [
            total_apprehended,
            total_transferred,
            total_custody,
            total_discharged,
            total_hhs
        ]
    })

    # Remove zero values
    stage_distribution = stage_distribution[
        stage_distribution["Value"] > 0
    ]

    if len(stage_distribution) > 0:

        fig = px.pie(
            stage_distribution,
            names="Stage",
            values="Value",
            hole=0.55
        )

        fig.update_traces(
            textposition="outside",
            textinfo="percent"
        )

        fig.update_layout(
            height=320,
            margin=dict(
                l=10,
                r=10,
                t=10,
                b=10
            ),
            showlegend=True
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info("No stage data available.")

st.divider()

# ============================================================
# CBP CUSTODY TREND
# ============================================================

st.markdown(
    '<div class="section-title">'
    'CBP Custody Trend'
    '</div>',
    unsafe_allow_html=True
)

custody_trend = (
    df[
        df["Year"] == selected_year
    ]
    .groupby("Date")[custody_col]
    .sum()
    .reset_index()
    .sort_values("Date")
)

custody_trend.columns = [
    "Date",
    "CBP Custody"
]

fig = px.line(
    custody_trend,
    x="Date",
    y="CBP Custody",
    markers=True
)

fig.update_layout(
    height=380,
    xaxis_title="Date",
    yaxis_title="Children in CBP Custody",
    margin=dict(
        l=10,
        r=10,
        t=20,
        b=10
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.divider()

# ============================================================
# CBP CUSTODY DETAILS
# ============================================================

st.markdown(
    '<div class="section-title">'
    f'CBP Custody Details — {selected_year}'
    '</div>',
    unsafe_allow_html=True
)

# IMPORTANT:
# This table shows ONLY the selected/latest year.
# The default selected year is automatically the latest year.

table_data = df[
    df["Year"] == selected_year
].copy()

# If month is selected, apply month filter
if selected_month != "All Months":

    table_data = table_data[
        table_data["Month"] == selected_month
    ].copy()

display_columns = [
    "Date",
    apprehended_col,
    custody_col,
    transferred_col,
    hhs_col,
    discharged_col
]

table_data = table_data[
    display_columns
].copy()

# Rename columns
table_data.columns = [
    "Date",
    "Children Apprehended",
    "CBP Custody",
    "Children Transferred",
    "Children in HHS Care",
    "Children Discharged"
]

# Sort latest date first
table_data = table_data.sort_values(
    "Date",
    ascending=False
)

# Format date
table_data["Date"] = (
    table_data["Date"]
    .dt.strftime("%d %B %Y")
)

# Show table
st.dataframe(
    table_data,
    use_container_width=True,
    hide_index=True,
    height=420
)

# ============================================================
# TABLE TOTALS
# ============================================================

st.markdown("### 📌 Selected Period Summary")

s1, s2, s3, s4, s5 = st.columns(5)

s1.metric(
    "Apprehended",
    f"{total_apprehended:,.0f}"
)

s2.metric(
    "Transferred",
    f"{total_transferred:,.0f}"
)

s3.metric(
    "CBP Custody",
    f"{total_custody:,.0f}"
)

s4.metric(
    "HHS Care",
    f"{total_hhs:,.0f}"
)

s5.metric(
    "Discharged",
    f"{total_discharged:,.0f}"
)

# ============================================================
# DATA INFORMATION
# ============================================================

with st.expander("ℹ️ Dataset Information"):

    st.write(
        f"**Excel file:** {file_path.name}"
    )

    st.write(
        f"**Data sheet:** {selected_sheet}"
    )

    st.write(
        f"**Total records:** {len(df):,}"
    )

    st.write(
        f"**Available years:** "
        f"{', '.join(map(str, years))}"
    )

    st.write(
        f"**Date range:** "
        f"{df['Date'].min().strftime('%d %B %Y')} "
        f"to "
        f"{df['Date'].max().strftime('%d %B %Y')}"
    )

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Healthcare Analytics Dashboard | "
    "Python • Pandas • Streamlit • Plotly"
)
