#!/bin/sh

# Function for logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if a directory exists and is writable
check_directory() {
    if [ ! -d "$1" ]; then
        log "Creating directory: $1"
        mkdir -p "$1"
    fi
    
    if [ ! -w "$1" ]; then
        log "Error: Directory $1 is not writable"
        exit 1
    fi
}

# Initialize directories
log "Checking and initializing directories..."
check_directory "/app/data"
check_directory "/app/logs"
check_directory "/app/config"

# Check if required files exist
log "Checking required files..."
for file in main.py dashboard.py pipeline.py; do
    if [ ! -f "/app/$file" ]; then
        log "Error: Required file $file not found in /app"
        log "Current directory contents:"
        ls -la /app
        exit 1
    fi
done

# Start the appropriate service based on the command
case "$1" in
    "dashboard")
        log "Starting Dash dashboard..."
        log "==============================================="
        log "Dashboard is starting..."
        log "To access the dashboard, open in your browser:"
        log "http://localhost:8050"
        log "==============================================="
        log "Current working directory: $(pwd)"
        log "Python version: $(python --version)"
        cd /app
        log "Changed to /app directory"
        log "Current directory contents:"
        ls -la
        log "Python path: $PYTHONPATH"
        # Wait for the warehouse database to be created
        log "Waiting for warehouse.db to be created by scheduler..."
        
        while ! sqlite3 /app/warehouse/warehouse.db "SELECT COUNT(*) FROM fact_appointment;" | grep -v '^0$' >/dev/null 2>&1; do
            log "fact_appointment not ready or empty. Retrying in 3 seconds..."
            sleep 3
        done
        log "Database found. Launching dashboard..."
        exec python -c "import dashboard; print('Dashboard module imported successfully'); print('To access the dashboard, open in your browser: http://localhost:8050'); dashboard.app.run(host='0.0.0.0', port=8050, debug=True)"
        ;;
    "scheduler")
        log "Starting ETL scheduler..."
        log "Current working directory: $(pwd)"
        log "Python version: $(python --version)"
        cd /app
        log "Changed to /app directory"
        exec python main.py
        ;;
    "streamlit")
        log "Starting Streamlit dashboard..."
        log "==============================================="
        log "Streamlit dashboard is starting..."
        log "To access the dashboard, open in your browser:"
        log "http://localhost:8501"
        log "==============================================="
        log "Current working directory: $(pwd)"
        log "Python version: $(python --version)"
        cd /app
        log "Changed to /app directory"
        log "Current directory contents:"
        ls -la
        log "Python path: $PYTHONPATH"
        exec streamlit run dashboard_streamlit.py
        ;;
    *)
        echo "Usage: docker run your-image-name [dashboard|scheduler|streamlit]"
        exit 1
        ;;
esac 