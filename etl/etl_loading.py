# Import required libraries for database operations
import sqlite3
import pandas as pd
import os
from db_init.warehouse_create import create_data_warehouse
from config.logging_config import setup_logger

# Set up logger for this module
logger = setup_logger(__name__)

# LOAD TO WAREHOUSE
def load_data_into_table(df, table_name, connection):
    try:
        logger.debug(f"Starting to load {len(df)} rows into table '{table_name}'")
        # Load DataFrame into SQLite table, replacing if exists
        df.to_sql(table_name, connection, if_exists='replace', index=False)
        logger.info(f"Successfully loaded {len(df)} rows into table '{table_name}'")
        print(f"Loaded '{table_name}' successfully.")
    except Exception as e:
        logger.error(f"Error loading table '{table_name}': {str(e)}")
        print(f"Error loading '{table_name}': {e}")

def load_data(
        specialty_df,
        insurance_company_df,
        coverage_type_df,
        date_df,
        time_df,
        patients_df,
        doctors_df,    
        slots_df,
        appointment_status_df,
        appointment_df
    ):
    logger.info("Starting data loading process")
    
    # Define path to warehouse database
    db_path = 'warehouse/warehouse.db'
    # Check if warehouse exists, if not create it
    if not os.path.exists(db_path):
        logger.warning(f"Warehouse not found at '{db_path}'. Creating...")
        print(f"Warehouse not found at '{db_path}'. Creating...")
        create_data_warehouse()
    
    # Establish connection to warehouse database
    logger.debug(f"Connecting to warehouse at {db_path}")
    conn = sqlite3.connect(db_path)
    logger.info(f"Connected to the warehouse {db_path}")
    print(f"Connected to the warehouse { db_path }")

    # Load dimension tables in specific order
    logger.info("Starting to load dimension tables")
    print("\nInserting specialty into warehouse...")
    load_data_into_table(specialty_df, 'dim_doctor_specialty', conn)

    print("\nInserting insurance companies into warehouse...")
    load_data_into_table(insurance_company_df, 'dim_insurance_company', conn)

    print("\nInserting coverage types into warehouse...")
    load_data_into_table(coverage_type_df, 'dim_coverage_type', conn)

    print("\nInserting dates into warehouse...")
    load_data_into_table(date_df, 'dim_date', conn)

    print("\nInserting times into warehouse...")
    load_data_into_table(time_df, 'dim_time', conn)

    print("\nInserting patients into warehouse...")
    load_data_into_table(patients_df, 'dim_patient', conn)

    print("\nInserting doctors into warehouse...")
    load_data_into_table(doctors_df, 'dim_doctor', conn)

    print("\nInserting slots into warehouse...")
    load_data_into_table(slots_df, 'dim_slot', conn)

    print("\nInserting appointment statuses into warehouse...")
    load_data_into_table(appointment_status_df, 'dim_appointment_status', conn)

    # Load fact table last
    logger.info("Starting to load fact table")
    print("\nInserting appointments FACT data into warehouse...")
    load_data_into_table(appointment_df, 'fact_appointment', conn)

    # Close database connection
    logger.debug("Closing database connection")
    conn.close()
    logger.info("Data loading process completed successfully")
