#!/usr/bin/env python3
"""
Script to verify BigQuery data setup and permissions
"""

from google.cloud import bigquery
import os

def verify_bigquery_setup():
    """Verify that BigQuery dataset and table are properly set up"""
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    print(f"Checking BigQuery setup for project: {project_id}")
    
    client = bigquery.Client(project=project_id)
    
    # Check if dataset exists
    dataset_id = "insurance_claims"
    dataset_ref = client.dataset(dataset_id)
    
    try:
        dataset = client.get_dataset(dataset_ref)
        print(f"✅ Dataset '{dataset_id}' exists")
    except Exception as e:
        print(f"❌ Dataset '{dataset_id}' not found: {e}")
        return False
    
    # Check if table exists
    table_id = "claims_data"
    table_ref = dataset_ref.table(table_id)
    
    try:
        table = client.get_table(table_ref)
        print(f"✅ Table '{table_id}' exists")
        print(f"   Table schema: {len(table.schema)} columns")
        print(f"   Table size: {table.num_rows} rows")
    except Exception as e:
        print(f"❌ Table '{table_id}' not found: {e}")
        return False
    
    # Test query permissions
    try:
        query_job = client.query(f"SELECT COUNT(*) as count FROM `{project_id}.{dataset_id}.{table_id}` LIMIT 1")
        results = query_job.result()
        for row in results:
            print(f"✅ Query permissions: OK (found {row.count} rows)")
    except Exception as e:
        print(f"❌ Query permissions failed: {e}")
        return False
    
    return True

def check_required_permissions():
    """Check if required BigQuery permissions are available"""
    required_roles = [
        "roles/bigquery.jobUser",
        "roles/bigquery.dataViewer",
        "roles/bigquery.dataEditor"
    ]
    
    print("\nRequired BigQuery roles:")
    for role in required_roles:
        print(f" - {role}")
    
    print("\nTo grant permissions, run:")
    print(f"gcloud projects add-iam-policy-binding {os.getenv('GOOGLE_CLOUD_PROJECT')} \\")
    print(f"    --member=user:$(gcloud config get-value account) \\")
    print(f"    --role={required_roles[0]}")

if __name__ == "__main__":
    print("=== BigQuery Data Setup Verification ===\n")
    
    if verify_bigquery_setup():
        print("\n✅ BigQuery setup is correct!")
    else:
        print("\n❌ BigQuery setup issues detected!")
        check_required_permissions()