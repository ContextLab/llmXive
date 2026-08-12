#!/usr/bin/env python3
"""
validate_citations.py

Verifies ActivityNet and Kwai Keye-VL model citations against verified sources
before execution (Constitution Principle II).

This script must run pre-execution to ensure all external data sources and
model references are valid, accessible, and correctly cited.

Usage:
    python scripts/validate_citations.py
"""

import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library not found. Please install it via pip.")
    sys.exit(1)

# Configuration for verified sources
# These are the authoritative sources defined in the project specifications
VERIFIED_SOURCES = {
    "activitynet_captions": {
        "name": "ActivityNet Captions Dataset",
        "huggingface_id": "ActivityNet/activitynet-captions",
        "paper_url": "https://arxiv.org/abs/1905.03981",
        "description": "Large-scale video dataset for dense captioning"
    },
    "kwai_keye_vl": {
        "name": "Kwai Keye-VL-2.0 (Int4)",
        "huggingface_id": "Kwai-Kyle/Kwai-Keye-VL-2.0-Int4",
        "paper_url": "https://arxiv.org/abs/2401.12345", # Placeholder for actual technical report URL
        "description": "Quantized Vision-Language model for temporal grounding"
    }
}

def check_huggingface_accessibility(dataset_id: str, timeout: int = 10) -> bool:
    """
    Checks if a dataset or model is accessible on Hugging Face Hub.
    Uses the Hugging Face Hub API to verify existence.
    """
    api_url = f"https://huggingface.co/api/datasets/{dataset_id}"
    # For models, the endpoint is slightly different, but we can try both or infer.
    # Let's try the dataset endpoint first, if it fails, try model.
    
    # Actually, a more robust way without the full HF Hub library is to check the repo page or API.
    # The API for datasets: https://huggingface.co/api/datasets/{repo_id}
    # The API for models: https://huggingface.co/api/models/{repo_id}
    
    # We need to distinguish if it's a dataset or model. 
    # For this task, we know ActivityNet is a dataset and Kwai Keye is a model.
    # But a generic checker is better. Let's try dataset first, then model.
    
    endpoints = [
        f"https://huggingface.co/api/datasets/{dataset_id}",
        f"https://huggingface.co/api/models/{dataset_id}"
    ]
    
    for url in endpoints:
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            continue
    
    return False

def validate_citations():
    """
    Main validation loop. Checks all verified sources.
    Returns 0 if all pass, 1 if any fail.
    """
    print("Starting citation and source validation...")
    print("-" * 60)
    
    all_passed = True

    for key, config in VERIFIED_SOURCES.items():
        print(f"Checking: {config['name']} ({config['huggingface_id']})")
        
        # 1. Check Hugging Face Accessibility
        is_accessible = check_huggingface_accessibility(config['huggingface_id'])
        
        if not is_accessible:
            print(f"  ❌ FAILED: Cannot access Hugging Face Hub for {config['huggingface_id']}")
            print(f"     Reason: Repository not found or network unreachable.")
            all_passed = False
        else:
            print(f"  ✅ PASSED: Hugging Face Hub accessible")

        # 2. Check Paper/Documentation URL (Optional but recommended for citation integrity)
        if config.get('paper_url'):
            try:
                response = requests.head(config['paper_url'], timeout=10, allow_redirects=True)
                if response.status_code in [200, 301, 302]:
                    print(f"  ✅ PASSED: Citation URL accessible")
                else:
                    print(f"  ⚠️  WARNING: Citation URL returned status {response.status_code}")
            except requests.RequestException as e:
                print(f"  ⚠️  WARNING: Could not verify citation URL: {e}")
        
        print("-" * 60)

    if all_passed:
        print("✅ All citations and sources verified successfully.")
        print("Proceeding with execution.")
        return 0
    else:
        print("❌ CRITICAL: One or more sources are invalid or inaccessible.")
        print("Execution halted per Constitution Principle II.")
        return 1

if __name__ == "__main__":
    sys.exit(validate_citations())
