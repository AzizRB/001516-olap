import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import sqlite3
import pandas as pd
from datetime import datetime
import functools
import os
import logging
import pytz

# Database path from environment variable
DB_PATH = os.getenv('DB_PATH', 'warehouse/warehouse.db')

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = "Healthcare appointments dashboard"

# Cache data retrieval to improve performance
@functools.lru_cache(maxsize=1)
def get_data():
    try:
        conn = sqlite3.connect(DB_PATH)
        query = """
            SELECT fa.*, dd.year, dd.month, dd.weekday,
                   das.status_title, dds.specialty_title,
                   dic.insurance_company_name, dct.coverage_title as coverage_type,
                   dp.gender,
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
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print(f"Database path: {DB_PATH}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Directory contents: {os.listdir('.')}")
        raise

# Cache filter options to improve performance
@functools.lru_cache(maxsize=1)
def get_filter_options():
    conn = sqlite3.connect(DB_PATH)
    years = pd.read_sql("SELECT DISTINCT year FROM dim_date ORDER BY year", conn)["year"]
    months = pd.read_sql("SELECT DISTINCT month FROM dim_date ORDER BY month", conn)["month"]
    weekdays = pd.read_sql("SELECT DISTINCT weekday FROM dim_date", conn)["weekday"]
    statuses = pd.read_sql("SELECT DISTINCT status_title FROM dim_appointment_status", conn)["status_title"]
    specialties = pd.read_sql("SELECT DISTINCT specialty_title FROM dim_doctor_specialty", conn)["specialty_title"]
    insurance = pd.read_sql("SELECT DISTINCT insurance_company_name FROM dim_insurance_company", conn)["insurance_company_name"]
    genders = pd.Series(["Male", "Female"])
    doctor_genders = pd.Series(["Male", "Female"])
    # Get coverage types from the dim_coverage_type table
    coverage_types = pd.read_sql("SELECT DISTINCT coverage_title FROM dim_coverage_type", conn)["coverage_title"]
    age_range = pd.read_sql("SELECT MIN(patient_age) as min_age, MAX(patient_age) as max_age FROM fact_appointment", conn).iloc[0]
    conn.close()
    return {
        "years": years,
        "months": months,
        "weekdays": weekdays,
        "statuses": statuses,
        "specialties": specialties,
        "insurance": insurance,
        "genders": genders,
        "doctor_genders": doctor_genders,
        "coverage_types": coverage_types,  # Add coverage types
        "age_range": (age_range["min_age"], age_range["max_age"])
    }

def build_filters(options):
    return dbc.Row([
        dbc.Col([
        ], width=1),
        dbc.Col([
            
            html.Label("Year", className="fw-bold"),
            dcc.Dropdown(
                id="year-filter",
                options=[{"label": "All Years", "value": "All"}] + [{"label": str(y), "value": str(y)} for y in options["years"]],
                value="All",
                clearable=False
            ),
            html.Label("Month", className="fw-bold mt-2"),
            dcc.Dropdown(
                id="month-filter",
                options=[{"label": "All Months", "value": "All"}] + [{"label": str(m), "value": str(m)} for m in options["months"]],
                value="All",
                clearable=False
            ),
            html.Label("Weekday", className="fw-bold mt-2"),
            dcc.Dropdown(
                id="weekday-filter",
                options=[{"label": "All Weekdays", "value": "All"}] + [{"label": str(w), "value": str(w)} for w in options["weekdays"]],
                value="All",
                clearable=False
            )
        ], width=2),
        
        dbc.Col([
            # First row with Doctor specialty and Insurance company
            dbc.Row([
                dbc.Col([
                    html.Label("Doctor specialty", className="fw-bold"),
                    dcc.Dropdown(
                        id="specialty-filter",
                        options=[{"label": "All Specialties", "value": "All"}] + [{"label": s, "value": s} for s in options["specialties"]],
                        value="All",
                        clearable=False
                    ),
                ], width=6),
                dbc.Col([
                    html.Label("Insurance company", className="fw-bold"),            
                    dcc.Dropdown(
                        id="insurance-filter",
                        options=[{"label": "All Insurance", "value": "All"}] + [{"label": i, "value": i} for i in options["insurance"]],
                        value="All",
                        clearable=False
                    ),
                ], width=6),
            ], className="mb-3"),
            
            # Second row with Coverage type
            dbc.Row([
                dbc.Col([
                    html.Label("Coverage type", className="fw-bold"),
                    dcc.Checklist(
                        id="coverage-type-filter",
                        options=[{"label": " All", "value": "All"}] + [{"label": " " + c, "value": c} for c in options["coverage_types"]],
                        value=["All"],
                        labelStyle={'display': 'inline-block', 'marginRight': '15px'},
                        className="mt-2"
                    ),
                ], width=12),
            ], className="mb-3"),
            
            # Third row with Patient age slider
            dbc.Row([
                dbc.Col([
                    html.Label("Patient age range", className="fw-bold"),
                    dcc.RangeSlider(
                        id="age-range-filter",
                        min=options["age_range"][0],
                        max=options["age_range"][1],
                        step=1,
                        value=[options["age_range"][0], options["age_range"][1]],                
                        marks={i: str(i) for i in range(int(options["age_range"][0]), int(options["age_range"][1]) + 1, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], width=12),
            ]),
        ], width=5),
        
        dbc.Col([
            html.Label("Appointment status", className="fw-bold"),
            dcc.RadioItems(
                id="status-filter",
                options=[{"label": " All", "value": "All"}] + [{"label": " " + s, "value": s} for s in options["statuses"]],
                value="All",
                labelStyle={'display': 'block'}
            )
        ], width=1),
        dbc.Col([
            html.Label("Patient gender", className="fw-bold mt-2"),
            dcc.Dropdown(
                id="gender-filter",
                options=[{"label": "All Genders", "value": "All"}, {"label": "Male", "value": "Male"}, {"label": "Female", "value": "Female"}],
                value="All",
                clearable=False
            ),
            html.Label("Doctor gender", className="fw-bold mt-2"),  # Add doctor gender filter
            dcc.Dropdown(
                id="doctor-gender-filter",
                options=[{"label": "All Genders", "value": "All"}, {"label": "Male", "value": "Male"}, {"label": "Female", "value": "Female"}],
                value="All",
                clearable=False
            ),
        ], width=2)
    ], className="mb-4")

def filter_data(df, year, month, weekday, status, specialty, insurance, gender, age_range, doctor_gender, coverage_type):
    if year != "All":
        df = df[df["year"].astype(str) == year]
    if month != "All":
        df = df[df["month"].astype(str) == month]
    if weekday != "All":
        df = df[df["weekday"] == weekday]
    if status != "All":
        df = df[df["status_title"] == status]
    if specialty != "All":
        df = df[df["specialty_title"] == specialty]
    if insurance != "All":
        df = df[df["insurance_company_name"] == insurance]
    if gender != "All":
        df = df[df["gender"] == gender]
    if doctor_gender != "All":  # Add doctor gender filtering
        df = df[df["doctor_gender"] == doctor_gender]
    if coverage_type != "All":  # Add coverage type filtering
        # Handle multiple selected coverage types
        if isinstance(coverage_type, list):
            if "All" not in coverage_type:
                df = df[df["coverage_type"].isin(coverage_type)]
        else:
            df = df[df["coverage_type"] == coverage_type]
    if age_range:
        df = df[(df["patient_age"] >= age_range[0]) & (df["patient_age"] <= age_range[1])]        
    return df

def create_layout():
    df = get_data()
    options = get_filter_options()
    
    # Calculate default year range (last 4 years)
    max_year = max(options["years"])
    min_year = max_year - 3  # Last 4 years
    
    # Calculate summary statistics
    total_appointments = len(df)
    total_doctors = df['doctor_id'].nunique()
    
    return html.Div([
        dcc.Store(id="auto-refresh-enabled", data=True),
        dcc.Interval(id="interval-refresh", interval=54000, n_intervals=0, disabled=False),  # Set to 15 min (54000 ms)
        dbc.Row([
            dbc.Col([
                dcc.Loading(
                    id="loader",
                    type="circle",
                    color="#17a2b8",
                    children=html.Div(id="last-updated"),
                )
            ], width=2),
            dbc.Col([
                html.H2("Healthcare appointments Dashboard", className="text-center mb-0"),
            ], width=8),
            dbc.Col([
                html.Div([
                    dbc.Label("Auto Refresh", className="fw-bold me-2"),
                    dbc.Checklist(
                        id="refresh-toggle",
                        options=[{"label": "", "value": "enabled"}],
                        value=["enabled"],
                        switch=True,
                        inline=True
                    )
                ], className="d-flex justify-content-end align-items-center")
            ], width=2)
        ], align="center"),
        html.Br(),
        html.Hr(),
        build_filters(options),
        html.Hr(),
        html.Div(id="charts-container"),
        html.Hr(),
        # Drill-down section
        dbc.Row([
            dbc.Col([
                dcc.Loading(
                    id="drilldown-loader",
                    type="circle",
                    color="#17a2b8",
                    children=dcc.Graph(id="drilldown-chart", style={"width": "100%", "height": "100%"})
                ),
            ], width=10),
            dbc.Col([
                html.Div([
                    html.Label("Select year range", className="fw-bold"),
                    dcc.RangeSlider(
                        id="drilldown-year-range",
                        min=min(options["years"]),
                        max=max(options["years"]),
                        step=1,
                        value=[min_year, max_year],  # Default to last 4 years
                        marks={i: str(i) for i in range(min(options["years"]), max(options["years"]) + 1)},
                        tooltip={"placement": "bottom", "always_visible": True},
                        vertical=True,
                        verticalHeight=400
                    ),
                ], className="mt-3 d-flex flex-column align-items-center")
            ], width=2)
        ], className="mb-4 align-items-center"),
        html.Hr()
    ], className="p-4")

@app.callback(
    [Output("charts-container", "children"),
     Output("last-updated", "children")],
    [Input("interval-refresh", "n_intervals"),
     Input("year-filter", "value"),
     Input("month-filter", "value"),
     Input("weekday-filter", "value"),
     Input("status-filter", "value"),
     Input("specialty-filter", "value"),
     Input("insurance-filter", "value"),
     Input("gender-filter", "value"),
     Input("age-range-filter", "value"),
     Input("doctor-gender-filter", "value"),
     Input("coverage-type-filter", "value")]  # Add coverage type filter input
)
def update_charts(_, year, month, weekday, status, specialty, insurance, gender, age_range, doctor_gender, coverage_type):
    df = get_data()
    df = filter_data(df, year, month, weekday, status, specialty, insurance, gender, age_range, doctor_gender, coverage_type)

    # Calculate summary statistics
    total_appointments = len(df)
    total_doctors = df['doctor_id'].nunique()
    total_patients = df['patient_id'].nunique()

    # Original charts with loaders
    charts = dbc.Row([
         # Add summary statistics column
        dbc.Col([
            html.Div([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Total appointments", className="card-title text-center text-muted"),
                        html.H2(f"{total_appointments:,}".replace(',', ' '), className="text-center text-dark")
                    ])
                ], className="mb-3 shadow-sm"),
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Doctors", className="card-title text-center text-muted"),
                        html.H2(f"{total_doctors:,}".replace(',', ' '), className="text-center text-dark")
                    ])
                ], className="mb-3 shadow-sm"),
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Patients", className="card-title text-center text-muted"),
                        html.H2(f"{total_patients:,}".replace(',', ' '), className="text-center text-dark")
                    ])
                ], className="shadow-sm")
            ])
        ], width=2),
        dbc.Col([
            dcc.Loading(
                id="gender-loader",
                type="circle",
                color="#17a2b8",
                children=dcc.Graph(
                    id="gender-pie-chart",
                    figure=px.pie(df, names="gender", title="Appointments by Patient gender", hole=0.5)
                    .update_traces(textinfo='label+percent+value')
                    .update_layout(
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="left",
                            x=0
                        )
                    )
                )
            ),
        ], width=5),
        dbc.Col([
            dcc.Loading(
                id="status-loader",
                type="circle",
                color="#17a2b8",
                children=dcc.Graph(
                    id="status-pie-chart",
                    figure=px.pie(df, names="status_title", title="Appointments by Status", hole=0.5)
                    .update_traces(textinfo='label+percent+value')
                )
            ),
        ], width=5),
       
    ])
    
    # Gender distribution charts
    # Insurance chart with gender distribution
    insurance_by_gender = df.groupby(['insurance_company_name', 'gender']).size().reset_index(name='count')
    
    # Calculate totals for each insurance company
    insurance_totals = df.groupby('insurance_company_name').size().reset_index(name='total')
    
    insurance_gender_fig = px.bar(
        insurance_by_gender, 
        x='insurance_company_name', 
        y='count', 
        color='gender',
        title='Appointments by Insurance Company',
        labels={'insurance_company_name': 'Insurance Company', 'count': 'Number of Appointments', 'gender': 'Gender'},
        barmode='stack',
        text=None  # Remove count labels on bars
    )
    
    insurance_gender_fig.update_layout(
        xaxis_tickangle=-45,
        height=500,
        legend_title="Gender",
        #xaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        # Move legend to top left
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        )
    )
    
    # Add total annotations above each bar
    for i, row in insurance_totals.iterrows():
        insurance_gender_fig.add_annotation(
            x=row['insurance_company_name'],
            y=row['total'],
            text=str(row['total']),
            showarrow=False,
            yshift=10,  # Position above the bar
            font=dict(size=12, color="black")
        )
    
    insurance_gender_chart = dbc.Row([
        dbc.Col([            
            dcc.Loading(
                id="insurance-gender-loader",
                type="circle",
                color="#17a2b8",
                children=dcc.Graph(
                    id="insurance-gender-chart",
                    figure=insurance_gender_fig
                )
            ),
        ], width=6),
        # Add top 7 profitable specialties chart
        dbc.Col([            
            dcc.Loading(
                id="profitable-specialties-loader",
                type="circle",
                color="#17a2b8",
                children=dcc.Graph(
                    id="profitable-specialties-chart",
                    figure=create_profitable_specialties_chart(df)
                )
            ),
        ], width=6)
    ])
    
    # Specialty chart with gender distribution
    gender_by_specialty = df.groupby(['specialty_title', 'gender']).size().reset_index(name='count')
    # Calculate totals for each insurance company
    specialty_totals = df.groupby('specialty_title').size().reset_index(name='total')

    specialty_gender_fig = px.bar(
        gender_by_specialty, 
        x='specialty_title', 
        y='count', 
        color='gender',
        title='Appointments by Specialty',
        labels={'specialty_title': 'Specialty', 'count': 'Number of Appointments', 'gender': 'Gender'},
        barmode='stack',
        text=None  # Remove count labels on bars
    )
    
    specialty_gender_fig.update_layout(
        xaxis_tickangle=-45,
        height=500,
        legend_title="",
        #xaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        # Move legend to top left
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        )
    )
    # Add total annotations above each bar
    for i, row in specialty_totals.iterrows():
        specialty_gender_fig.add_annotation(
            x=row['specialty_title'],
            y=row['total'],
            text=str(row['total']),
            showarrow=False,
            yshift=10,  # Position above the bar
            font=dict(size=12, color="black")
        )
    specialty_gender_chart = dbc.Row([
        dbc.Col([            
            dcc.Loading(
                id="specialty-gender-loader",
                type="circle",
                color="#17a2b8",
                children=dcc.Graph(
                    id="specialty-gender-chart",
                    figure=specialty_gender_fig
                )
            ),
        ], width=12)
    ])

    updated_time = f"Last updated at: {datetime.now(pytz.timezone('Asia/Tashkent')).strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Return all charts in a clear order
    return [charts, 
            html.Hr(),  # Add a separator before gender distribution charts            
            insurance_gender_chart, 
            specialty_gender_chart], updated_time

# Function to create the top 5 profitable specialties chart
def create_profitable_specialties_chart(df):
    # Calculate revenue by specialty (appointment count * appointment fee)
    specialty_revenue = df.groupby('specialty_title').agg(
        total_revenue=('appointment_fee', 'sum'),
        appointment_count=('appointment_id', 'count')
    ).reset_index()
    
    # Sort by revenue and get top 7
    top_7_specialties = specialty_revenue.sort_values('total_revenue', ascending=False).head(7)
    
    # Create vertical bar chart
    fig = px.bar(
        top_7_specialties,
        y='specialty_title',
        x='total_revenue',
        orientation='h',  # Horizontal bars for better readability
        title='Top 7 profitable specialties',
        labels={'specialty_title': 'Specialty', 'total_revenue': 'Total Revenue ($)'},
        text='total_revenue',  # Show revenue on bars
        color_discrete_sequence=['#2ecc71']  # Use a green color
    )
    
    # Format the text to show currency
    fig.update_traces(texttemplate='$%{text:,.0f}', textposition='auto')
    
    # Update layout
    fig.update_layout(
        height=500,
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray'),
        yaxis=dict(categoryorder='total ascending'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        yaxis_title='',
        xaxis_title='Total Revenue ($)'
    )
    
    return fig

# Separate callback for the drill-down chart that only responds to year range changes
@app.callback(
    Output("drilldown-chart", "figure"),
    [Input("drilldown-year-range", "value"),
     Input("year-filter", "value"),
     Input("month-filter", "value"),
     Input("weekday-filter", "value"),
     Input("status-filter", "value"),
     Input("specialty-filter", "value"),
     Input("insurance-filter", "value"),
     Input("gender-filter", "value"),
     Input("age-range-filter", "value"),
     Input("doctor-gender-filter", "value"),
     Input("coverage-type-filter", "value")]  # Add coverage type filter input
)
def update_drilldown_chart(drilldown_year_range, year, month, weekday, status, specialty, insurance, gender, age_range, doctor_gender, coverage_type):
    df = get_data()
    
    # Apply all filters to the data
    df = filter_data(df, year, month, weekday, status, specialty, insurance, gender, age_range, doctor_gender, coverage_type)
    
    # Filter by selected year range
    drilldown_df = df[(df['year'] >= drilldown_year_range[0]) & (df['year'] <= drilldown_year_range[1])]
    
    # Group by year and month (using month numbers for calculations)
    drilldown_df = drilldown_df.groupby(['year', 'month']).size().reset_index(name='count')
    
    # Create a mapping for month names (for display only)
    month_names = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    
    # Create a month order for sorting (using month numbers)
    month_order = list(range(1, 13))
    
    # Create the figure using month numbers
    drilldown_fig = px.line(drilldown_df, x='month', y='count', color='year',
                           title='Drill-down: Monthly Appointments by Year',
                           labels={'count': 'Number of Appointments', 'month': 'Month'})
    
    # Update layout for better visualization
    drilldown_fig.update_layout(
        height=500,
        width=None,  # Allow the figure to take the full width of its container
        xaxis_title="Month",
        yaxis_title="Number of Appointments",
        legend_title="Year",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            categoryorder='array',
            categoryarray=month_order,
            tickmode='array',
            ticktext=[month_names[m] for m in month_order],
            tickvals=month_order
        ),
        # Improve line visibility
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified'
    )
    
    # Make lines thicker and add markers
    for trace in drilldown_fig.data:
        trace.line.width = 3
        trace.mode = 'lines+markers'
        trace.marker.size = 8
        trace.marker.line.width = 1
        trace.marker.line.color = 'white'
    
    # Add grid lines for better readability
    drilldown_fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    drilldown_fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    
    return drilldown_fig

@app.callback(
    Output("interval-refresh", "disabled"),
    Input("refresh-toggle", "value")
)
def toggle_auto_refresh(value):
    return "enabled" not in value

# Add this new callback for handling chart clicks
@app.callback(
    [Output("year-filter", "value"),
     Output("month-filter", "value"),
     Output("weekday-filter", "value"),
     Output("status-filter", "value"),
     Output("specialty-filter", "value"),
     Output("insurance-filter", "value"),
     Output("gender-filter", "value"),
     Output("age-range-filter", "value"),
     Output("doctor-gender-filter", "value"),
     Output("coverage-type-filter", "value")],  # Add coverage type filter output
    [Input("gender-pie-chart", "clickData"),
     Input("status-pie-chart", "clickData"),
     Input("insurance-gender-chart", "clickData"),
     Input("specialty-gender-chart", "clickData"),
     Input("profitable-specialties-chart", "clickData")],
    [State("year-filter", "value"),
     State("month-filter", "value"),
     State("weekday-filter", "value"),
     State("status-filter", "value"),
     State("specialty-filter", "value"),
     State("insurance-filter", "value"),
     State("gender-filter", "value"),
     State("age-range-filter", "value"),
     State("doctor-gender-filter", "value"),
     State("coverage-type-filter", "value")]  # Add coverage type filter state
)
def update_filters_from_chart_click(gender_click, status_click, insurance_click, specialty_click, profitable_click,
                                   year, month, weekday, status, specialty, insurance, gender, age_range, doctor_gender, coverage_type):
    ctx = dash.callback_context
    if not ctx.triggered:
        return year, month, weekday, status, specialty, insurance, gender, age_range, doctor_gender, coverage_type
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    click_data = ctx.triggered[0]['value']
    
    if not click_data:
        return year, month, weekday, status, specialty, insurance, gender, age_range, doctor_gender, coverage_type
    
    # Handle gender pie chart click
    if trigger_id == "gender-pie-chart":
        selected_gender = click_data['points'][0]['label']
        # Toggle behavior: if already selected, reset to "All"
        if gender == selected_gender:
            return year, month, weekday, status, specialty, insurance, "All", age_range, doctor_gender, coverage_type
        return year, month, weekday, status, specialty, insurance, selected_gender, age_range, doctor_gender, coverage_type
    
    # Handle status pie chart click
    elif trigger_id == "status-pie-chart":
        selected_status = click_data['points'][0]['label']
        # Toggle behavior: if already selected, reset to "All"
        if status == selected_status:
            return year, month, weekday, "All", specialty, insurance, gender, age_range, doctor_gender, coverage_type
        return year, month, weekday, selected_status, specialty, insurance, gender, age_range, doctor_gender, coverage_type
    
    # Handle insurance gender chart click
    elif trigger_id == "insurance-gender-chart":
        selected_insurance = click_data['points'][0]['x']
        # Toggle behavior: if already selected, reset to "All"
        if insurance == selected_insurance:
            return year, month, weekday, status, specialty, "All", gender, age_range, doctor_gender, coverage_type
        return year, month, weekday, status, specialty, selected_insurance, gender, age_range, doctor_gender, coverage_type
    
    # Handle specialty gender chart click
    elif trigger_id == "specialty-gender-chart":
        selected_specialty = click_data['points'][0]['x']
        # Toggle behavior: if already selected, reset to "All"
        if specialty == selected_specialty:
            return year, month, weekday, status, "All", insurance, gender, age_range, doctor_gender, coverage_type
        return year, month, weekday, status, selected_specialty, insurance, gender, age_range, doctor_gender, coverage_type
    
    # Handle profitable specialties chart click
    elif trigger_id == "profitable-specialties-chart":
        selected_specialty = click_data['points'][0]['y']
        # Toggle behavior: if already selected, reset to "All"
        if specialty == selected_specialty:
            return year, month, weekday, status, "All", insurance, gender, age_range, doctor_gender, coverage_type
        return year, month, weekday, status, selected_specialty, insurance, gender, age_range, doctor_gender, coverage_type
    
    return year, month, weekday, status, specialty, insurance, gender, age_range, doctor_gender, coverage_type

app.layout = create_layout()

if __name__ == "__main__":
    app.run(debug=True) 