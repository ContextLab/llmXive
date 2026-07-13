"""
Script to verify a real, reachable URL for the CiteVQA dataset.

This script attempts to load the CiteVQA dataset from Hugging Face.
If successful, it writes the verified source details to data/verified_sources.json.
If the dataset is not found or accessible, it writes a failure report.
"""
import json
import os
import sys
from pathlib import Path

# Ensure we can import from the project root if run as a script
# but rely on the installed package structure if in a venv
try:
    from config import get_config_dict
except ImportError:
    # Fallback for direct execution without proper PYTHONPATH setup
    # In a real environment, this should be handled by the venv
    pass

def verify_huggingface_dataset():
    """
    Attempts to verify the CiteVQA dataset on Hugging Face.
    Returns a dict with status, url, and details, or None if it fails.
    """
    dataset_name = "citevqa"
    verified_source = {
        "status": "unknown",
        "source_type": "huggingface",
        "dataset_id": dataset_name,
        "url": f"https://huggingface.co/datasets/{dataset_name}",
        "details": "",
        "timestamp": None
    }

    try:
        # Try to import datasets. If not installed, we catch the error.
        # The task requires adding dependencies to requirements.txt if needed.
        # Assuming datasets is in requirements.txt as per T002a (transformers/sentence-transformers often bring it, 
        # but explicit 'datasets' is safer).
        # However, T002a lists: torch-cpu, transformers, sentence-transformers, pdfplumber, scikit-learn, pandas, pytest, memory-profiler, numpy, matplotlib.
        # 'datasets' is not explicitly in T002a. We should try to import it. 
        # If it fails, we might need to update requirements.txt or handle the error.
        # Let's try to import it first.
        import datasets
        
        # Attempt to load the dataset info (without loading full data to save time/memory)
        # We use load_dataset_builder or just try to access the config
        # A simple way to verify existence is to try loading the dataset builder or checking the repo info.
        # However, the most robust "verification" for a script is to try loading a small sample.
        # But T005a is just verification. Let's try to get the dataset info.
        
        # We will attempt to load the dataset with streaming=True to avoid downloading everything immediately,
        # just to verify it exists and is accessible.
        # Note: The task says "Identify and verify a real, reachable URL".
        # Loading with streaming=True is a good way to verify reachability.
        
        # We need to be careful not to hang. 
        # Let's try to get the dataset builder first.
        builder = datasets.load_dataset_builder(dataset_name)
        
        verified_source["status"] = "success"
        verified_source["details"] = f"Dataset '{dataset_name}' found on Hugging Face Hub. Builder config: {builder.config_name if hasattr(builder, 'config_name') else 'default'}"
        verified_source["timestamp"] = str(datasets.__version__)
        
        return verified_source

    except ImportError as e:
        verified_source["status"] = "failed_dependency"
        verified_source["details"] = f"Failed to import 'datasets' library. Please add 'datasets' to requirements.txt. Error: {str(e)}"
        return verified_source
    except Exception as e:
        verified_source["status"] = "failed_access"
        verified_source["details"] = f"Failed to access dataset '{dataset_name}' on Hugging Face. Error: {str(e)}"
        return verified_source

def main():
    # Determine output path relative to project root
    # Assuming this script runs from project root or we resolve relative to script location
    script_dir = Path(__file__).parent
    project_root = script_dir.parent if script_dir.name == "code" else script_dir
    data_dir = project_root / "data"
    output_path = data_dir / "verified_sources.json"

    # Ensure data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)

    print(f"Verifying CiteVQA dataset source...")
    result = verify_huggingface_dataset()

    # Write result to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Verification result written to: {output_path}")
    print(f"Status: {result['status']}")
    print(f"Details: {result['details']}")

    # Exit with code 1 if verification failed to signal the pipeline
    if result["status"] != "success":
        print("ERROR: Dataset verification failed. Halting.")
        sys.exit(1)
    
    print("Dataset verification successful.")

if __name__ == "__main__":
    main()
