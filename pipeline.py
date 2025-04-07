from datetime import datetime
import pytz
#Import ETL scripts
from etl.etl_extraction import extract_from_flat_file, extract_from_db, extract_from_api
from etl.etl_transformation import *
from etl.etl_loading import load_data
from config.logging_config import setup_logger

# Set up logger for this module
logger = setup_logger(__name__)

#ETL Pipeline Function
def etl_pipeline():
    logger.info("Starting ETL pipeline")
    
    try:
        print("\n STARTING FULL ETL PIPELINE FOR PATIENT APPOINMENT MANAGEMENT DATA WAREHOUSE")
        

        # --- EXTRACT PHASE ---
        print("\n-- START ETRACTION --")
        print("\nExtracting from flat files...")
        appointments_df, patients_df, slots_df = extract_from_flat_file()
        logger.debug("Extracted flat files")

        print("\nExtracting from database...")
        db_data = extract_from_db()
        logger.debug("Extracted database data")
        doctors_df = db_data['doctor']
        doctor_appointment_df = db_data['doctor_appointment']
        specialty_df = db_data['specialty']
        coverage_type_df = db_data['coverage_type']

        print("\nExtracting from API...")
        insurance_company_df = extract_from_api()
        logger.debug("Extracted API data")
        print("-- ETRACTION COMPLETE --")
        print("---------------------------------------------------------------")
        
        # --- TRANSFORM PHASE ---
        print("\n-- START TRANSFORM --")
        print("Transforming appointments...")
        appointments_df, date_df = create_dim_date(appointments_df)
        appointments_df, time_df = create_dim_time(appointments_df)
        appointments_df, appointment_status_df = create_dim_appointment_status(appointments_df)
        appointments_df = map_doctor_to_appointments(appointments_df, doctor_appointment_df)

        print("Transforming patients...")
        patients_df = map_insurance_to_patients(patients_df, insurance_company_df)    
        patients_df = transform_patient(patients_df, db_data['coverage_type'])

        print("Formatting some tables")
        fact_appointments_df = format_appointment(appointments_df)
        specialty_df = format_specialty(specialty_df)
        coverage_type_df = format_coverage_type(coverage_type_df)
        slots_df = format_slots(slots_df)   
        doctors_df = format_doctors(doctors_df)
        print("  Formatting completed successfully")
        print("-- TRANSFORM COMPLETE --")
        print("---------------------------------------------------------------")
        
        # --- LOAD PHASE --- 
        print("\n-- START LOAD --")   
        load_data(
            specialty_df,
            insurance_company_df,
            coverage_type_df,
            date_df,
            time_df,
            patients_df,
            doctors_df,
            slots_df,
            appointment_status_df,
            fact_appointments_df
        )
        logger.debug("Completed data loading")
        print("-- LOAD COMPLETE --")
        
        print("-------------------------------------------------")
        tz = pytz.timezone("Asia/Tashkent")
        now = datetime.now(tz)
        currentTime = now.strftime("%d %B %Y - %H:%M")
        print(f"ETL PIPELINE COMPLETED AT {currentTime}")
        logger.info(f"ETL pipeline completed successfully at {currentTime}")
        
    except Exception as e:
        error_msg = f"ETL pipeline failed: {str(e)}"
        logger.error(error_msg)
        raise

if __name__ == "__main__":
    etl_pipeline()
