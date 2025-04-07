# Import required libraries for data manipulation
import pandas as pd
import numpy as np
from config.logging_config import setup_logger

# Set up logger for this module
logger = setup_logger(__name__)

# DATA TRANSFORMATIONS
def create_dim_date(appointments_df):
    logger.info("Starting date dimension creation")
    # Convert appointment_date column to datetime format
    appointments_df['appointment_date'] = pd.to_datetime(appointments_df['appointment_date'], errors='coerce')
    # Get minimum date from appointments
    min_date = appointments_df['appointment_date'].min()
    # Get maximum date from appointments
    max_date = appointments_df['appointment_date'].max()

    logger.debug(f"Date range: {min_date} to {max_date}")
    # Create date range between min and max dates
    date_range = pd.date_range(start=min_date, end=max_date)
    # Create date dimension DataFrame with various date attributes
    dim_date = pd.DataFrame({
        'full_date': date_range,
        'date_id': date_range.strftime('%Y%m%d').astype(int),
        'day': date_range.day,
        'month': date_range.month,
        'year': date_range.year,
        'weekday': date_range.day_name(),
        'quarter': date_range.quarter
    })

    # Add date_id to appointments DataFrame
    appointments_df['appointment_date_id'] = appointments_df['appointment_date'].dt.strftime('%Y%m%d').astype(int)
    logger.info("Date dimension generated successfully")
    print("  DATE dimension generated successfully.")
    return appointments_df, dim_date


def create_dim_time(appointments_df):
    logger.info("Starting time dimension creation")
    # Create time range from 8 AM to 6 PM with 15-minute intervals
    time_range = pd.date_range('08:00', '18:00', freq='15min').time
    # Create time dimension DataFrame with various time attributes
    dim_time = pd.DataFrame({
        'full_time': [t.strftime('%H:%M:%S') for t in time_range],
        'time_id': [int(t.strftime('%H%M')) for t in time_range],
        'hour': [t.hour for t in time_range],
        'minute': [t.minute for t in time_range],
        'am_pm': ['AM' if t.hour < 12 else 'PM' for t in time_range]
    })

    # Add time_id to appointments DataFrame
    appointments_df['appointment_time_id'] = appointments_df['appointment_time'].str.replace(':', '').str[:4].astype(int)
    logger.info("Time dimension generated successfully")
    print("  TIME dimension generated successfully.")
    return appointments_df, dim_time

def create_dim_appointment_status(appointments_df):
    logger.info("Starting appointment status dimension creation")
    # Get unique status values from appointments
    unique_statuses = appointments_df['status'].dropna().unique()
    logger.debug(f"Found {len(unique_statuses)} unique appointment statuses")
    # Create status dimension DataFrame
    dim_status = pd.DataFrame({
        'status_id': range(1, len(unique_statuses) + 1),
        'status_title': unique_statuses
    })

    # Create lookup dictionary for status mapping
    status_lookup = dict(zip(dim_status['status_title'], dim_status['status_id']))
    # Add status_id to appointments DataFrame
    appointments_df['appointment_status_id'] = appointments_df['status'].map(status_lookup)

    logger.info("Appointment status dimension generated successfully")
    print("  APPOINTMENT STATUS dimension generated successfully.")
    return appointments_df, dim_status

def map_doctor_to_appointments(appointments_df, doctor_appointment_df):
    logger.info("Starting doctor to appointments mapping")
    # Check for duplicate appointment_ids in doctor_appointment
    if doctor_appointment_df['appointment_id'].duplicated().any():
        logger.error("Duplicate appointment_id entries found in doctor_appointment")
        raise ValueError("Duplicate appointment_id entries found in doctor_appointment. Must be one doctor per appointment.")

    # Merge appointments with doctor assignments
    merged_df = appointments_df.merge(
        doctor_appointment_df[['appointment_id', 'doctor_id']],
        how='left',
        on='appointment_id'
    )

    # Check for appointments without assigned doctors
    if merged_df['doctor_id'].isnull().any():
        missing = merged_df[merged_df['doctor_id'].isnull()]
        logger.error(f"Found {len(missing)} appointments without assigned doctors")
        raise ValueError(f"Some appointments have no matching doctor_id:\n{missing[['appointment_id']].head()}")

    logger.info("Appointment records and doctors merged successfully")
    print("  Appoinment records and doctors merged successfully.")
    return merged_df

def map_insurance_to_patients(patients_df, insurance_company_df):
    logger.info("Starting insurance to patients mapping")
    # Merge patients with insurance companies based on name
    merged_df = patients_df.merge(
        insurance_company_df[['insurance_company_id', 'insurance_company_name']],
        how='left',
        left_on='insurance',
        right_on='insurance_company_name'
    )
    
    # Remove redundant columns
    merged_df.drop(columns=['insurance', 'insurance_company_name'], inplace=True)
    logger.info("Insurance companies re-assigned to patients successfully")
    print("  Insurance companies re-assigned to patients successfully.")
    return merged_df


def transform_patient(patients_df, coverage_type_df):
    logger.info("Starting patient transformation")
    # 1. Extract IDs and assign probabilities in correct order
    coverage_type_ids = coverage_type_df['coverage_type_id'].tolist()
    # Define probability weights for coverage types
    weights = [0.3, 0.6, 0.07, 0.02, 0.01]

    logger.debug(f"Assigning coverage types to {len(patients_df)} patients")
    # Randomly assign coverage types based on weights
    patients_df['coverage_type_id'] = np.random.choice(
        coverage_type_ids,
        size=len(patients_df),
        p=weights
    )

    # 2. Split name into first and last names
    name_split = patients_df['name'].str.strip().str.split(' ', n=1, expand=True)
    patients_df['first_name'] = name_split[0]
    patients_df['last_name'] = name_split[1].fillna('')

    # 3. Rename and drop unnecessary columns
    patients_df.rename(columns={'dob': 'date_of_birth'}, inplace=True)
    patients_df.rename(columns={'sex': 'gender'}, inplace=True)    
    # Remove original name column
    patients_df.drop(columns=['name'], inplace=True)

    logger.info("Patient columns transformed successfully")
    print("  Patient columns transformed successfully.")
    return patients_df

def format_appointment(appointments_df):    
    logger.info("Starting appointment formatting")
    # Select and rename columns for fact table
    clean_appointment_df = appointments_df[[
        'appointment_id',
        'patient_id',
        'slot_id',
        'appointment_date_id',
        'appointment_time_id',
        'doctor_id',
        'appointment_status_id',
        'scheduling_interval',
        'waiting_time',
        'appointment_duration',
        'age'
    ]].rename(columns={
        'scheduling_interval': 'scheduling_interval_days',
        'waiting_time': 'waiting_duration_min',
        'appointment_duration': 'appointment_duration_min',
        'age': 'patient_age'
    })

    logger.info("Appointment formatting completed successfully")
    return clean_appointment_df

def format_specialty(specialty_df):    
    logger.info("Starting specialty formatting")
    # Rename title column for consistency
    specialty_df.rename(columns={'title': 'specialty_title'}, inplace=True)
    logger.info("Specialty formatting completed successfully")
    return specialty_df

def format_coverage_type(coverage_type_df):    
    logger.info("Starting coverage type formatting")
    # Rename title column for consistency
    coverage_type_df.rename(columns={'title': 'coverage_title'}, inplace=True)
    logger.info("Coverage type formatting completed successfully")
    return coverage_type_df

def format_slots(slots_df):    
    logger.info("Starting slots formatting")
    # Remove is_available column if it exists
    result_df = slots_df.drop(columns=['is_available'], errors='ignore')
    logger.info("Slots formatting completed successfully")
    return result_df

def format_doctors(doctors_df):    
    logger.info("Starting doctors formatting")
    # Remove contact information columns
    result_df = doctors_df.drop(columns=['email', 'phone'], errors='ignore')
    logger.info("Doctors formatting completed successfully")
    return result_df
