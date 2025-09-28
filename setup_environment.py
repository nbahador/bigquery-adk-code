#!/usr/bin/env python3
"""
Script to set up and verify the environment
"""

import os
import subprocess
import sys

def setup_environment():
    """Set up the required environment variables"""
    
    # Get the current project
    try:
        result = subprocess.run([
            "gcloud", "config", "get-value", "project"
        ], capture_output=True, text=True, check=True)
        project_id = result.stdout.strip()
    except:
        project_id = "woven-invention-469721-s1"  # Your project ID
    
    # Set environment variables
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
    
    print("✅ Environment setup complete:")
    print(f"   Project: {project_id}")
    print(f"   Location: us-central1")
    
    return project_id

def verify_environment():
    """Verify that the environment is properly configured"""
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION")
    
    if not project_id:
        print("❌ GOOGLE_CLOUD_PROJECT is not set")
        return False
    
    print("✅ Environment verified:")
    print(f"   Project: {project_id}")
    print(f"   Location: {location}")
    
    return True

if __name__ == "__main__":
    setup_environment()
    verify_environment()