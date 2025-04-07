# Healthcare Appointment Management Data Warehouse

This project implements an ETL (Extract, Transform, Load) pipeline for a healthcare appointment management system. It processes data from multiple sources (flat files, SQLite database, and API) and loads it into a data warehouse for analysis.

## Project Structure

```
DWH_CW_1516/                           # Project root directory
├── config/                            # Configuration files
│   └── logging_config.py             # Logging configuration
├── data/                             # Data directory for source files
│   ├── appointments.csv              # Appointment records
│   ├── patients.csv                  # Patient information
│   ├── slots.csv                     # Available appointment slots
│   └── healthcare.db                 # Source database
├── db_init/                          # Database initialization
│   ├── sql_database_create.py        # Source database creation
│   └── warehouse_create.py           # Data warehouse creation
├── etl/                              # ETL process modules
│   ├── etl_extraction.py            # Data extraction module
│   ├── etl_transformation.py        # Data transformation module
│   └── etl_loading.py              # Data loading module
├── logs/                            # Log files directory
├── warehouse/                       # Data warehouse directory
│   └── warehouse.db                # Data warehouse database
├── Dockerfile                      # Docker configuration
├── docker-compose.yml              # Docker Compose configuration
├── dashboard.py                    # Dash dashboard application
├── dashboard_streamlit.py          # Streamlit dashboard application
├── main.py                         # Main entry point with scheduler
├── pipeline.py                     # ETL pipeline orchestration
└── requirements.txt                # Project dependencies
```

## Prerequisites

- Python 3.12 or higher (tested with Python 3.12.2150.1013)
- pip (Python package installer)

## Installation

1. Create and activate a virtual environment (IT IS NOT REQUIRED IF YOU HAVE PYTHON INSTALLED IN YOU PC):
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Project Setup

1. **Source Database Setup**:
   - The source database will be automatically created when you first run the pipeline
   - It will be created in the `data` directory as `healthcare.db`

2. **Data Warehouse Setup**:
   - The data warehouse will be automatically created in the `warehouse` directory
   - It will be created as `warehouse.db` when you first run the pipeline

3. **Logging Setup**:
   - Log files will be automatically created in the `logs` directory
   - Each module will have its own log file (e.g., `etl_extraction.log`, `etl_transformation.log`)

## Running the Project

### Option 1: Running the ETL Pipeline MANUALLY (Primary Method Without Docker)

#### 1. Running the ETL Pipeline

The recommended way to run the ETL pipeline is using the main script, which includes a scheduler for automated data processing:

```bash
python main.py
```

This will:
1. Run the ETL pipeline immediately
2. Set up a scheduler to run the pipeline automatically at configured intervals
3. Extract data from:
   - Flat files (CSV)
   - SQLite database
   - API (with fallback to local JSON)
4. Transform the data into appropriate dimensions and fact tables
5. Load the data into the data warehouse

#### 2. Running the Dash Dashboard

To view the interactive OLAP dashboard:
```bash
python dashboard.py
```

The dashboard will be available at `http://127.0.0.1:8050/`

#### 3. Running the Streamlit Dashboard

To view the interactive Streamlit dashboard:
```bash
streamlit run dashboard_streamlit.py
```

The dashboard will be available at `http://localhost:8501/`

### Option 2: Running with Docker (Recommended)

The easiest way to run the entire project is using Docker. This will set up the environment and run both the ETL pipeline and dashboards automatically.

#### Prerequisites
- Docker
- Docker Compose

#### Steps to Run

1. **Navigate to Project Root Directory**:
   ```bash
   # The directory containing Dockerfile and docker-compose.yml
   cd "DWH_CW_1516"
   ```

2. **Build and start the containers**:
   ```bash
   docker-compose up --build
   ```

3. **Access the dashboards**:
   - Dash Dashboard: http://localhost:8050
   - Streamlit Dashboard: http://localhost:8501

4. **To stop the containers**:
   ```bash
   docker-compose down
   ```

#### Docker Services

The Docker setup includes three services:

1. **Dashboard (Dash)**:
   - Runs on port 8050
   - Provides interactive OLAP dashboard
   - Accessible at http://localhost:8050

2. **Dashboard (Streamlit)**:
   - Runs on port 8501
   - Provides alternative interactive dashboard
   - Accessible at http://localhost:8501

3. **Scheduler**:
   - Runs the ETL pipeline daily at 00:00
   - Updates the data warehouse automatically
   - No direct user interface

#### Directory Structure for Docker
```
DWH_CW_1516/           # Run Docker commands here
├── Dockerfile                # Docker configuration
├── docker-compose.yml        # Docker Compose configuration
├── config/
├── data/
├── db_init/
├── etl/
├── logs/
├── warehouse/
├── dashboard.py
├── dashboard_streamlit.py
├── main.py
├── pipeline.py
└── requirements.txt
```

The Docker setup will:
- Run the ETL pipeline in the background
- Start both dashboards automatically
- Persist data in the `data`, `logs`, and `warehouse` directories
- Automatically restart if any container stops

#### Docker Logging

The setup provides comprehensive logging:

1. **Application Logs**:
   - All application logs are stored in the `./logs` directory
   - Includes ETL pipeline logs, dashboard logs, and other application logs
   - Logs persist even after container restart

2. **Docker Container Logs**:
   ```bash
   # View all container logs
   docker-compose logs

   # Follow logs in real-time
   docker-compose logs -f

   # View logs for specific service
   docker-compose logs dashboard
   docker-compose logs dashboard_streamlit
   docker-compose logs scheduler
   ```

3. **Log File Structure**:
   ```
   logs/
   ├── etl_extraction.log
   ├── etl_transformation.log
   ├── etl_loading.log
   ├── pipeline.log
   └── dashboard.log
   ```

## Dashboard Features

### Dash Dashboard
- Interactive filtering by year, month, weekday, appointment status, specialty, insurance company, patient gender, doctor gender, coverage type, and patient age range
- Summary metrics for total appointments, doctors, patients, and revenue
- Patient gender distribution (pie chart)
- Appointment status distribution (pie chart)
- Gender distribution by specialty (stacked bar chart)
- Gender distribution by insurance company (stacked bar chart)
- Monthly appointment trends by year (line chart)
- Top 7 profitable specialties (horizontal bar chart)
- Age distribution by gender (stacked bar chart)
- Appointments by coverage type (bar chart)
- Doctor experience vs. appointment fee (scatter plot)
- Appointments by weekday (bar chart)
- Doctor gender distribution (pie chart)
- Specialty revenue comparison (dual-axis chart)

### Streamlit Dashboard
- Interactive filtering by year, month, weekday, appointment status, specialty, insurance company, patient gender, doctor gender, coverage type, and patient age range
- Summary metrics for total appointments, doctors, patients, and revenue
- Patient gender distribution (pie chart)
- Appointment status distribution (pie chart)
- Gender distribution by specialty (stacked bar chart with totals)
- Gender distribution by insurance company (stacked bar chart with totals)
- Monthly appointment trends by year (line chart with markers)
- Top 7 profitable specialties (horizontal bar chart with revenue labels)
- Age distribution by gender (stacked bar chart with totals)
- Appointments by coverage type (bar chart)
- Doctor experience vs. appointment fee (scatter plot with trend line)
- Appointments by weekday (bar chart)
- Doctor gender distribution (pie chart)
- Specialty revenue comparison (dual-axis chart showing total and average revenue)
- Tabbed interface for additional charts
- Responsive layout that adapts to different screen sizes
- Custom styling for a professional appearance

## OLAP Features

Both dashboards implement OLAP (Online Analytical Processing) features:

1. **Multi-dimensional Analysis**: Analyze data across multiple dimensions (time, patient demographics, doctor attributes, etc.)
2. **Drill-down Capabilities**: Start with high-level data and drill down into more detailed views
3. **Cross-dimensional Analysis**: Analyze relationships between different dimensions (e.g., gender by specialty)
4. **Aggregation of Measures**: Calculate totals, averages, and other metrics across dimensions
5. **Interactive Filtering**: Apply filters to see how different segments of data perform

## Dependencies

The project requires the following Python packages:

- dash>=2.14.2: Web application framework for building analytical dashboards
- dash-bootstrap-components>=1.5.0: Bootstrap components for Dash
- streamlit>=1.32.0: Framework for creating data applications
- pandas>=2.1.4: Data manipulation and analysis library
- plotly>=5.18.0: Interactive plotting library
- schedule>=1.2.1: Task scheduling library
- requests>=2.31.0: HTTP library for API requests
- numpy>=1.26.3: Numerical computing library
- watchdog>=3.0.0: For file system monitoring
- altair>=5.2.0: For additional visualizations
- python-dateutil>=2.8.2: For date handling
- pytz>=2024.1: For timezone handling

## Logging and Monitoring

- Log files are created in the `logs` directory
- Each module has its own log file for better debugging
- Docker containers have health checks to ensure they're running properly
- The ETL pipeline logs its progress and any errors that occur
- Both dashboards log their startup and any errors that occur

## Data Sources

1. **Flat Files** (CSV):
   - `appointments.csv`: Appointment records
   - `patients.csv`: Patient information
   - `slots.csv`: Available appointment slots

2. **SQLite Database**:
   - Contains doctor information
   - Specialty information
   - Coverage type information
   - Doctor appointment mappings

3. **API**:
   - Insurance company information
   - Fallback to local JSON if API is unavailable

## Data Warehouse Schema

### Dimension Tables:
- `dim_patient`: Patient information
- `dim_doctor`: Doctor information
- `dim_doctor_specialty`: Doctor specialties
- `dim_slot`: Appointment slots
- `dim_date`: Date information
- `dim_time`: Time information
- `dim_coverage_type`: Insurance coverage types
- `dim_appointment_status`: Appointment statuses
- `dim_insurance_company`: Insurance company information

### Fact Table:
- `fact_appointment`: Appointment records with foreign key relationships to all dimensions

## Troubleshooting

1. **Database Connection Issues**:
   - Check if the `data` directory exists
   - Verify database file permissions
   - Check log files for specific error messages

2. **API Connection Issues**:
   - Check internet connection
   - Verify API endpoint accessibility
   - Check log files for API-related errors

3. **File Access Issues**:
   - Verify file permissions
   - Check if required CSV files exist in the `data` directory
   - Check log files for file access errors