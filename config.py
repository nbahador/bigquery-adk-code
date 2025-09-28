import os

# BigQuery Configuration
BIGQUERY_CONFIG = {
    "project_id": os.getenv("GOOGLE_CLOUD_PROJECT"),  # Use current project
    "dataset_id": "insurance_claims",
    "table_id": "claims_data"
}

# Fallback project IDs to try
FALLBACK_PROJECTS = [
    os.getenv("GOOGLE_CLOUD_PROJECT"),
    "bigquery-public-data",  # For testing with public data
]

def get_bigquery_config():
    """Get validated BigQuery configuration"""
    config = BIGQUERY_CONFIG.copy()
    
    # Ensure project_id is set
    if not config["project_id"]:
        config["project_id"] = input("Please enter your Google Cloud Project ID: ")
    
    return config