import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import numpy as np

# Set page configuration
st.set_page_config(
    page_title="Healthcare OLAP Dashboard",
    page_icon="🏥",
    layout="wide"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1E88E5;
    }
    .metric-label {
        font-size: 1rem;
        color: #424242;
    }
    .chart-container {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Database connection
@st.cache_data(ttl=3600)
def get_data():
    conn = sqlite3.connect('warehouse/warehouse.db')
    query = """
        SELECT fa.*, dd.year, dd.month, dd.weekday,
               das.status_title, dds.specialty_title,
               dic.insurance_company_name, dct.coverage_title as coverage_type,
               dp.gender, fa.patient_age,
               ddoc.years_of_experience, ddoc.appointment_fee,
               ddoc.gender as doctor_gender
        FROM fact_appointment fa
        JOIN dim_date dd ON fa.appointment_date_id = dd.date_id
        JOIN dim_appointment_status das ON fa.appointment_status_id = das.status_id
        JOIN dim_doctor ddoc ON fa.doctor_id = ddoc.doctor_id
        JOIN dim_doctor_specialty dds ON ddoc.specialty_id = dds.specialty_id
        JOIN dim_patient dp ON fa.patient_id = dp.patient_id
        JOIN dim_insurance_company dic ON dp.insurance_company_id = dic.insurance_company_id
        JOIN dim_coverage_type dct ON dp.coverage_type_id = dct.coverage_type_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Get filter options
@st.cache_data(ttl=3600)
def get_filter_options():
    conn = sqlite3.connect('warehouse/warehouse.db')
    years = pd.read_sql("SELECT DISTINCT year FROM dim_date ORDER BY year", conn)["year"]
    specialties = pd.read_sql("SELECT DISTINCT specialty_title FROM dim_doctor_specialty", conn)["specialty_title"]
    statuses = pd.read_sql("SELECT DISTINCT status_title FROM dim_appointment_status", conn)["status_title"]
    coverage_types = pd.read_sql("SELECT DISTINCT coverage_title FROM dim_coverage_type", conn)["coverage_title"]
    conn.close()
    return {
        "years": years,
        "specialties": specialties,
        "statuses": statuses,
        "coverage_types": coverage_types
    }

# Simple filter function
def apply_filters(df, year, specialty, status, gender, coverage_type):
    # Make a copy to avoid modifying the original dataframe
    df_filtered = df.copy()
    
    if year != "All":
        df_filtered = df_filtered[df_filtered["year"].astype(str) == year]
    if specialty != "All":
        df_filtered = df_filtered[df_filtered["specialty_title"] == specialty]
    if status != "All":
        df_filtered = df_filtered[df_filtered["status_title"] == status]
    if gender != "All":
        df_filtered = df_filtered[df_filtered["gender"] == gender]
    if coverage_type != "All":
        df_filtered = df_filtered[df_filtered["coverage_type"] == coverage_type]
    
    return df_filtered

# Function to create summary metrics
def create_summary_metrics(df):
    # Calculate metrics
    total_appointments = len(df)
    total_doctors = df['doctor_id'].nunique()
    total_patients = df['patient_id'].nunique()
    total_revenue = df['appointment_fee'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{:,}</div>
            <div class="metric-label">Total Appointments</div>
        </div>
        """.format(total_appointments), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{:,}</div>
            <div class="metric-label">Total Doctors</div>
        </div>
        """.format(total_doctors), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{:,}</div>
            <div class="metric-label">Total Patients</div>
        </div>
        """.format(total_patients), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">${:,.2f}</div>
            <div class="metric-label">Total Revenue</div>
        </div>
        """.format(total_revenue), unsafe_allow_html=True)

# Function to create time series chart (Roll-up operation)
def create_time_series_chart(df):
    # Group by year and month, count appointments
    monthly_counts = df.groupby(['year', 'month']).size().reset_index(name='count')
    
    # Create month names for better readability
    month_names = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    
    # Add month name for display
    monthly_counts['month_name'] = monthly_counts['month'].map(month_names)
    
    # Create line chart
    fig = px.line(
        monthly_counts,
        x='month',
        y='count',
        color='year',
        title='Monthly Appointment Trends by Year',
        labels={'count': 'Number of Appointments', 'month': 'Month', 'year': 'Year'},
        markers=True
    )
    
    # Update x-axis to show month names
    fig.update_xaxes(
        tickmode='array',
        ticktext=[month_names[m] for m in range(1, 13)],
        tickvals=list(range(1, 13))
    )
    
    fig.update_layout(
        height=500,
        xaxis=dict(
            tickangle=45
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.subheader("Time Series Analysis (Roll-up)")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Function to create dimension analysis chart (Slice operation)
def create_dimension_analysis_chart(df):
    # Group by specialty and count appointments
    specialty_counts = df.groupby('specialty_title', as_index=False).size()
    specialty_counts.columns = ['specialty_title', 'count']
    
    # Sort by count in descending order
    specialty_counts = specialty_counts.sort_values('count', ascending=False)
    
    # Create bar chart
    fig = px.bar(
        specialty_counts,
        x='specialty_title',
        y='count',
        title='Appointments by Specialty',
        labels={'specialty_title': 'Specialty', 'count': 'Number of Appointments'},
        color='specialty_title',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(
        height=500,
        xaxis=dict(
            categoryorder='total descending',
            tickangle=45
        ),
        showlegend=False
    )
    
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.subheader("Dimension Analysis (Slice)")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Function to create patient gender pie chart
def create_patient_gender_pie_chart(df):
    # Group by patient gender and count appointments
    gender_counts = df.groupby('gender', as_index=False).size()
    gender_counts.columns = ['gender', 'count']
    
    # Create pie chart
    fig = px.pie(
        gender_counts,
        values='count',
        names='gender',
        title='Patient Gender Distribution',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    # Update layout
    fig.update_layout(
        title_x=0.5,
        title_font_size=16,
        legend_title='Gender',
        legend_title_font_size=12,
        legend_font_size=10,
        margin=dict(t=50, l=20, r=20, b=20)
    )
    
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.subheader("Patient Gender Distribution")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Function to create coverage type pie chart
def create_coverage_type_pie_chart(df):
    # Group by coverage type and count appointments
    coverage_counts = df.groupby('coverage_type', as_index=False).size()
    coverage_counts.columns = ['coverage_type', 'count']
    
    # Create pie chart
    fig = px.pie(
        coverage_counts,
        values='count',
        names='coverage_type',
        title='Appointments by Coverage Type',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    # Update layout
    fig.update_layout(
        title_x=0.5,
        title_font_size=16,
        legend_title='Coverage Type',
        legend_title_font_size=12,
        legend_font_size=10,
        margin=dict(t=50, l=20, r=20, b=20)
    )
    
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.subheader("Appointments by Coverage Type")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Function to create slice and dice chart
def create_slice_dice_chart(df):
    # Group by specialty and status, count appointments
    specialty_status_counts = df.groupby(['specialty_title', 'status_title'], as_index=False).size()
    specialty_status_counts.columns = ['specialty_title', 'status_title', 'count']
    
    # Create stacked bar chart
    fig = px.bar(
        specialty_status_counts,
        x='specialty_title',
        y='count',
        color='status_title',
        title='Appointment Status by Specialty',
        labels={'specialty_title': 'Specialty', 'count': 'Number of Appointments', 'status_title': 'Status'},
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(
        height=500,
        xaxis=dict(
            categoryorder='total descending',
            tickangle=45
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.subheader("Slice and Dice Analysis")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Function to create pie chart for appointment status
def create_status_pie_chart(df):
    # Group by status and count appointments
    status_counts = df.groupby('status_title', as_index=False).size()
    status_counts.columns = ['status_title', 'count']
    
    # Sort by count in descending order
    status_counts = status_counts.sort_values('count', ascending=False)
    
    # Create pie chart
    fig = px.pie(
        status_counts,
        values='count',
        names='status_title',
        title='Appointment Status Distribution',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.subheader("Status Distribution (Pie Chart)")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Function to create pie chart for insurance company
def create_insurance_pie_chart(df):
    # Group by insurance company and count appointments
    insurance_counts = df.groupby('insurance_company_name', as_index=False).size()
    insurance_counts.columns = ['insurance_company_name', 'count']
    
    # Sort by count in descending order
    insurance_counts = insurance_counts.sort_values('count', ascending=False)
    
    # Create pie chart
    fig = px.pie(
        insurance_counts,
        values='count',
        names='insurance_company_name',
        title='Insurance Company Distribution',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.subheader("Insurance Company Distribution (Pie Chart)")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Main function
def main():
    # Header
    st.markdown("<h1 class='main-header'>Healthcare Appointment Analytics</h1>", unsafe_allow_html=True)
    
    # Info box
    st.markdown("""
    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 10px; margin-bottom: 1rem; border-left: 5px solid #1E88E5;">
        <strong>OLAP Dashboard:</strong> This interactive dashboard demonstrates OLAP operations including drill-down, roll-up, slice, and dice.
        Use the sidebar filters to analyze appointment data.
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar filters
    st.sidebar.markdown("<h2 style='font-size: 1.5rem; color: #1E88E5; margin-bottom: 1rem;'>Filters</h2>", unsafe_allow_html=True)
    
    # Load data and filter options
    try:
        df = get_data()
        options = get_filter_options()
        
        # Year filter
        year = st.sidebar.selectbox(
            "Year",
            ["All"] + list(options["years"]),
            index=0
        )
        
        # Specialty filter
        specialty = st.sidebar.selectbox(
            "Specialty",
            ["All"] + list(options["specialties"]),
            index=0
        )
        
        # Status filter
        status = st.sidebar.selectbox(
            "Appointment Status",
            ["All"] + list(options["statuses"]),
            index=0
        )
        
        # Gender filter
        gender = st.sidebar.selectbox(
            "Patient Gender",
            ["All", "Male", "Female"],
            index=0
        )
        
        # Coverage type filter
        coverage_type = st.sidebar.selectbox(
            "Insurance Coverage Type",
            ["All"] + list(options["coverage_types"]),
            index=0
        )
        
        # Apply filters
        filtered_df = apply_filters(df, year, specialty, status, gender, coverage_type)
        
        # Create summary metrics
        create_summary_metrics(filtered_df)
        
        # Create charts
        create_time_series_chart(filtered_df)
        create_dimension_analysis_chart(filtered_df)
        
        # Create two pie charts instead of the problematic drill-down chart
        col1, col2 = st.columns(2)
        with col1:
            create_patient_gender_pie_chart(filtered_df)
        with col2:
            create_coverage_type_pie_chart(filtered_df)
            
        create_slice_dice_chart(filtered_df)
        
        # Create pie charts
        create_status_pie_chart(filtered_df)
        create_insurance_pie_chart(filtered_df)
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error("Please check the logs for more details.")

# Run the app
if __name__ == "__main__":
    main() 