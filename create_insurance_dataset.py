import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import random

def generate_synthetic_insurance_data():
    np.random.seed(42)
    random.seed(42)
    
    # Define base data
    procedures = {
        'Virtual Consultation': {'avg_cost': 150, 'duration': 30},
        'Mental Health Session': {'avg_cost': 200, 'duration': 50},
        'Prescription Refill': {'avg_cost': 50, 'duration': 10},
        'Follow-up Visit': {'avg_cost': 120, 'duration': 20},
        'Emergency Consult': {'avg_cost': 300, 'duration': 45}
    }
    
    diagnoses = [
        'Hypertension', 'Diabetes', 'Anxiety', 'Depression', 'Common Cold',
        'Back Pain', 'Migraine', 'Insomnia', 'Allergies', 'Stomach Flu'
    ]
    
    states = ['CA', 'NY', 'TX', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI']
    providers = ['TeleHealth Inc', 'VirtualCare Co', 'RemoteMed Group', 'DigitalDoc Services']
    
    # Generate claims data
    claims = []
    
    for i in range(1000):  # 1000 claims
        claim_id = f"CLM_{10000 + i}"
        patient_id = f"PAT_{random.randint(1000, 9999)}"
        provider = random.choice(providers)
        procedure = random.choice(list(procedures.keys()))
        diagnosis = random.choice(diagnoses)
        state = random.choice(states)
        
        # Base cost with some variation
        base_cost = procedures[procedure]['avg_cost']
        cost_variation = np.random.normal(0, base_cost * 0.3)
        claim_amount = max(50, base_cost + cost_variation)
        
        # Date in 2024
        claim_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 364))
        
        # Create some outlier patterns
        is_outlier = False
        outlier_reason = None
        
        # Rule 1: Unusual diagnosis + procedure combinations
        unusual_combos = [
            ('Mental Health Session', 'Common Cold'),
            ('Emergency Consult', 'Allergies'),
            ('Virtual Consultation', 'Surgery'),  # Shouldn't happen in telehealth
            ('Mental Health Session', 'Surgery')  # Invalid combo
        ]
        
        if (procedure, diagnosis) in [(p, d) for p, d in unusual_combos if d in diagnoses]:
            is_outlier = True
            outlier_reason = 'Unusual diagnosis-procedure combination'
        
        # Rule 2: Abnormally high claim amount
        elif claim_amount > procedures[procedure]['avg_cost'] * 3:
            is_outlier = True
            outlier_reason = 'Abnormally high claim amount'
        
        # Rule 3: Geographic mismatch (telehealth not covered in certain states/scenarios)
        elif state in ['WY', 'AK', 'MT'] and procedure == 'Virtual Consultation':
            is_outlier = True
            outlier_reason = 'Geographic coverage restriction'
        
        # Rule 4: Multiple high-cost claims from same patient
        elif random.random() < 0.02:  # 2% chance for testing
            is_outlier = True
            outlier_reason = 'Suspicious claim pattern'
        
        claims.append({
            'claim_id': claim_id,
            'patient_id': patient_id,
            'provider_name': provider,
            'procedure_type': procedure,
            'diagnosis': diagnosis,
            'claim_amount': round(claim_amount, 2),
            'claim_date': claim_date.strftime('%Y-%m-%d'),
            'patient_state': state,
            'is_outlier': is_outlier,
            'outlier_reason': outlier_reason,
            'review_required': is_outlier,
            'claim_status': 'Pending' if is_outlier else 'Approved'
        })
    
    return pd.DataFrame(claims)

def upload_to_bigquery(df, project_id, dataset_id):
    from google.cloud import bigquery
    
    client = bigquery.Client(project=project_id)
    
    # Create dataset if not exists
    dataset_ref = client.dataset(dataset_id)
    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset {dataset_id} already exists")
    except Exception:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        client.create_dataset(dataset)
        print(f"Created dataset {dataset_id}")
    
    # Upload data
    table_ref = dataset_ref.table("insurance_claims")
    job_config = bigquery.LoadJobConfig()
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
    job_config.autodetect = True
    
    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result()
    
    print(f"Uploaded {len(df)} rows to {dataset_id}.insurance_claims")

if __name__ == "__main__":
    # Generate data
    df = generate_synthetic_insurance_data()
    
    # Save to JSON for evaluation
    df.to_json("insurance_claims_dataset.json", orient="records", indent=2)
    print("Saved dataset to insurance_claims_dataset.json")
    
    # Upload to BigQuery (uncomment and set your project ID)
    # upload_to_bigquery(df, "your-project-id", "healthcare_claims")