from google.cloud import bigquery
import create_insurance_dataset

def setup_insurance_dataset(project_id):
    """Complete setup for the insurance claims dataset"""
    
    # Generate synthetic data
    df = create_insurance_dataset.generate_synthetic_insurance_data()
    
    # Upload to BigQuery
    create_insurance_dataset.upload_to_bigquery(df, project_id, "healthcare_claims")
    
    # Create outlier analysis view
    client = bigquery.Client(project=project_id)
    
    view_query = """
    CREATE OR REPLACE VIEW healthcare_claims.outlier_analysis AS
    SELECT 
        claim_id,
        patient_id,
        provider_name,
        procedure_type,
        diagnosis,
        claim_amount,
        patient_state,
        is_outlier,
        outlier_reason,
        review_required,
        claim_status,
        -- Business rule calculations
        CASE 
            WHEN procedure_type = 'Virtual Consultation' AND claim_amount > 450 THEN 'High Amount'
            WHEN procedure_type = 'Mental Health Session' AND diagnosis IN ('Common Cold', 'Back Pain') THEN 'Unusual Combo'
            ELSE 'Other'
        END as triggered_rule
    FROM healthcare_claims.insurance_claims
    """
    
    job = client.query(view_query)
    job.result()
    print("Created outlier_analysis view")

if __name__ == "__main__":
    import os
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if project_id:
        setup_insurance_dataset(project_id)
    else:
        print("Please set GOOGLE_CLOUD_PROJECT environment variable")