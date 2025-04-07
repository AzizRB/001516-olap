# Import required libraries for database and file system operations
import sqlite3
from pathlib import Path
import os

def create_data_warehouse():
    # Create warehouse directory if it doesn't exist
    Path('warehouse').mkdir(exist_ok=True)

    # Remove existing warehouse database if it exists
    if os.path.exists("warehouse/warehouse.db"):
        os.remove("warehouse/warehouse.db")

    # Create new SQLite database connection
    conn = sqlite3.connect("warehouse/warehouse.db")
    # Create cursor for executing SQL commands
    cursor = conn.cursor()

    # Create fact table for appointments with foreign key constraints
    cursor.execute("""CREATE TABLE fact_appointment (
            appointment_id INTEGER PRIMARY KEY,
            patient_id INTEGER,
            doctor_id INTEGER,
            slot_id INTEGER,
            appointment_status_id INTEGER,
            appointment_date_id INTEGER,
            appointment_time_id INTEGER,
            scheduling_interval_days INTEGER,
            waiting_duration_min REAL,
            appointment_duration_min REAL,
            patient_age INTEGER,        
            FOREIGN KEY (patient_id) REFERENCES dim_patient(patient_id),
            FOREIGN KEY (doctor_id) REFERENCES dim_doctor(doctor_id),
            FOREIGN KEY (slot_id) REFERENCES dim_slot(slot_id),
            FOREIGN KEY (appointment_status_id) REFERENCES dim_appointment_status(status_id),
            FOREIGN KEY (appointment_date_id) REFERENCES dim_date(date_id),
            FOREIGN KEY (appointment_time_id) REFERENCES dim_time(time_id)        
        );""")

    # Create dimension table for patient information
    cursor.execute("""CREATE TABLE dim_patient (
            patient_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            date_of_birth TEXT,
            gender TEXT,
            insurance_company_id INTEGER,
            coverage_type_id INTEGER,
            FOREIGN KEY (insurance_company_id) REFERENCES dim_insurance_company(insurance_company_id),
            FOREIGN KEY (coverage_type_id) REFERENCES dim_coverage_type(coverage_type_id)
        );""")

    # Create dimension table for doctor information
    cursor.execute("""CREATE TABLE dim_doctor (
            doctor_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            gender TEXT,
            years_of_experience INTEGER,
            appointment_fee REAL,
            specialty_id INTEGER,
            FOREIGN KEY (specialty_id) REFERENCES dim_doctor_specialty(specialty_id)
        );""")

    # Create dimension table for doctor specialties
    cursor.execute("""CREATE TABLE dim_doctor_specialty (
            specialty_id INTEGER PRIMARY KEY,
            specialty_title TEXT
        );""")

    # Create dimension table for appointment slots
    cursor.execute("""CREATE TABLE dim_slot (
            slot_id INTEGER PRIMARY KEY,
            appointment_date TEXT,
            appointment_time TEXT
        );""")

    # Create dimension table for dates
    cursor.execute("""CREATE TABLE dim_date (
            date_id INTEGER PRIMARY KEY,
            full_date TEXT,
            day INTEGER,
            month INTEGER,
            year INTEGER,
            weekday TEXT,
            quarter INTEGER
        );""")

    # Create dimension table for times
    cursor.execute("""CREATE TABLE dim_time (
            time_id INTEGER PRIMARY KEY,
            full_time TEXT,
            hour INTEGER,
            minute INTEGER,
            am_pm TEXT
        );""")

    # Create dimension table for coverage types
    cursor.execute("""CREATE TABLE dim_coverage_type (
            coverage_type_id INTEGER PRIMARY KEY,
            coverage_title TEXT
        );""")

    # Create dimension table for appointment statuses
    cursor.execute("""CREATE TABLE dim_appointment_status (
            status_id INTEGER PRIMARY KEY,
            status_title TEXT
        );""")

    # Create dimension table for insurance companies
    cursor.execute("""CREATE TABLE dim_insurance_company (
            insurance_company_id TEXT PRIMARY KEY,
            insurance_company_name TEXT,
            insurance_company_type TEXT,
            founded_year INTEGER,
            coverage_area TEXT
        );""")

    # Commit all changes to the database
    conn.commit()
    # Close the database connection
    conn.close()
    print("Warehouse SUCCESSFULLY created and saved in 'warehouse/warehouse.db'.")

