import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
logs_dir = Path('logs')
logs_dir.mkdir(exist_ok=True)

# Configure logging format
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def setup_logger(name):
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Create formatters
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Create handlers
    # File handler - logs everything to file
    file_handler = RotatingFileHandler(
        logs_dir / f'{name}.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Console handler - logs ERROR and above to console
    console_handler = logging.StreamHandler()
    
    #we are using Print instead of logging to console, so only errors are shown
    #console_handler.setLevel(logging.INFO)
    
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger 