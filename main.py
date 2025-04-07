import schedule
import time
from config.logging_config import setup_logger

# Set up logger for this module
logger = setup_logger(__name__)

# Import pipeline script
from pipeline import etl_pipeline

def run_pipeline_with_message():
    etl_pipeline()
    print("Scheduler is running. ETL will run daily at 00:00. Press Ctrl+C to stop.")
    logger.info("Scheduler is running. ETL will run daily at 00:00.")


def run_scheduled_pipeline():   
    logger.info("Starting scheduled pipeline")
    #Run the pipeline for the first time without waiting schedule. Next run will be as scheduled.
    run_pipeline_with_message()     
    
    #Schedule the pipeline run for at the end of the day
    schedule.every().day.at("00:00").do(run_pipeline_with_message)
    #schedule.every(5).minutes.do(run_pipeline_with_message) #this is for testing the scheduler
    
    while True:        
        schedule.run_pending()
        time.sleep(60)
                
        
# Make sure the pipeline only runs when this script is executed directly not imported from other file
if __name__ == "__main__":    
    run_scheduled_pipeline()