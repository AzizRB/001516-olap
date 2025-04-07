import pandas as pd
import os
import requests
import sqlite3
import json
from db_init.sql_database_create import create_sql_database_source
from config.logging_config import setup_logger

# Set up logger for this module
logger = setup_logger(__name__)

# Extract data from data sources

# extract data from flat files (CSV)
def extract_from_flat_file(folder='data'):    
    logger.info("Starting extraction from flat files")
    
    # Dictionary mapping file types to their corresponding CSV filenames
    flat_files = {
        'appointments': 'appointments.csv',
        'patients': 'patients.csv',
        'slots': 'slots.csv'
    }

    # Initialize empty dictionary to store dataframes
    dataframes = {}
    
    # Iterate through each file type and filename
    for key, filename in flat_files.items():
        # Construct full file path by joining folder and filename
        path = os.path.join(folder, filename)
        logger.debug(f"Attempting to read file: {path}")
        # Check if file exists at the specified path
        if not os.path.exists(path):
            logger.error(f"Missing required file: {path}")
            raise FileNotFoundError(f"Missing required file: {path}")
        # Read CSV file into pandas DataFrame with UTF-8 encoding
        df = pd.read_csv(path, encoding='utf-8')
        logger.debug(f"Successfully read {filename} with {len(df)} rows")
        # Store DataFrame in dictionary with file type as key
        dataframes[key] = df

    logger.info("Flat files successfully extracted")
    print("Flat files successfully extracted.")    
    # Return tuple of three DataFrames in specific order
    return dataframes['appointments'], dataframes['patients'], dataframes['slots']
#############################################################################################

# Extract data from SQLite database
def extract_from_db(folder='data'):
    logger.info("Starting extraction from SQLite database")
    # Define database filename
    file_name ='healthcare.db'
    # Construct full database path
    db_path = os.path.join(folder, file_name)
        
    # Check if database exists, if not create it
    if not os.path.exists(db_path):
        logger.warning(f"Database not found at: {db_path}")
        print(f"Database not found at: {db_path}")
        print("Running database creation script...")
        create_sql_database_source()        
    
    logger.debug(f"Connecting to database at: {db_path}")
    # Establish connection to SQLite database
    conn = sqlite3.connect(db_path)

    # Extract data from each table using SQL queries
    logger.debug("Extracting data from doctor table")
    doctor_df = pd.read_sql_query("SELECT * FROM doctor", conn)
    logger.debug("Extracting data from specialty table")
    specialty_df = pd.read_sql_query("SELECT * FROM specialty", conn)
    logger.debug("Extracting data from coverage_type table")
    coverage_type_df = pd.read_sql_query("SELECT * FROM coverage_type", conn)
    logger.debug("Extracting data from doctor_appointment table")
    doctor_appointment_df = pd.read_sql_query("SELECT * FROM doctor_appointment", conn)

    # Close database connection
    conn.close()

    logger.info("Successfully extracted 4 tables from DB")
    print("Extracted 4 tables from DB")

    # Create dictionary to store all extracted DataFrames
    db_data = {
        'doctor': doctor_df,
        'specialty': specialty_df,
        'coverage_type': coverage_type_df,
        'doctor_appointment': doctor_appointment_df
    }

    return db_data
#############################################################################################

# extract data from API source
def extract_from_api():
    logger.info("Starting extraction from API")
    print("Fetching data from API...")
    
    # Define API endpoint URL with API key
    api_url = "https://my.api.mockaroo.com/insurance_companies.json?key=1c428350"
    # Define path to fallback JSON file
    fallback_path='data/api_sample.json'
    
    try:
        logger.debug(f"Making API request to: {api_url}")
        # Make HTTP GET request to API
        response = requests.get(api_url)
        # Check if request was successful
        if response.status_code != 200:
            logger.error(f"API request failed with status code: {response.status_code}")
            raise Exception(f"Bad response: {response.status_code}")
            
        # Parse JSON response into Python object
        data = response.json()
        # Check if response contains data
        if not data:
            logger.error("API response was empty")
            raise Exception("API response was empty.")
        logger.info(f"Successfully extracted {len(data)} insurance companies from API")
        print(f"Extracted {len(data)} insurance companies from API")        

    except Exception as e:
        logger.error(f"API loading failed: {str(e)}")
        print(f"Error: API loading failed: {e}")
        logger.info(f"Falling back to local file: {fallback_path}")
        print("\nFalling back to local file:", fallback_path)
        print("Extracting data from JSON file...")
        # Check if fallback file exists
        if not os.path.exists(fallback_path):
            logger.error(f"Fallback file not found at: {fallback_path}")
            raise FileNotFoundError(f"Fallback file not found at: {fallback_path}")
        # Read fallback JSON file
        with open(fallback_path, 'r', encoding='utf-8') as json_data:
            data = json.load(json_data)        
        logger.info(f"Successfully loaded {len(data)} fallback records from JSON file")
        print(f"Loaded {len(data)} fallback records from JSON file.")        

    # Convert JSON data to pandas DataFrame
    df = pd.DataFrame(data)
    # Define columns to keep in final DataFrame
    cols_to_load = [
        'rownum',
        'insurance_company_name',
        'insurance_company_type',
        'founded_year',
        'coverage_area'
    ]
        
    # Select only required columns and create a copy
    df = df[cols_to_load].copy()
    # Rename 'rownum' column to 'insurance_company_id'
    df.rename(columns={'rownum': 'insurance_company_id'}, inplace=True)
    
    logger.info("API data extraction completed successfully")
    return df


