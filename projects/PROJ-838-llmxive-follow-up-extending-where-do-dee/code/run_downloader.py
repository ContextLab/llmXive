"""
Script to fetch and validate the TELBench dataset.
"""
import sys
from pathlib import Path

from config import ensure_directories, dataset_url
from downloader import fetch_and_validate, ValidationError


def main():
    """
    Entry point for the downloader script.
    Fetches the dataset, validates it, and prints results.
    """
    ensure_directories()
    
    # Define paths
    data_dir = Path("data")
    output_file = data_dir / "train.json"
    
    # Dataset configuration
    # Using the ID specified in the task: HuggingFaceH4/tebench
    dataset_id = "HuggingFaceH4/tebench"
    
    # Note: expected_hash is optional. If a specific hash is known, it can be passed here.
    # For now, we rely on HuggingFace's integrity checks and our JSON validation.
    expected_hash = None

    print(f"Fetching dataset '{dataset_id}'...")
    try:
        result = fetch_and_validate(
            dataset_id=dataset_id,
            output_path=output_file,
            expected_hash=expected_hash
        )
        
        print(f"Downloaded to: {result['file_path']}")
        print(f"Total records: {result['total_records']}")
        print(f"Valid records: {result['valid_records']}")
        print(f"Invalid records: {result['invalid_records']}")
        
        if result['is_valid']:
            print("Validation: PASSED")
            return 0
        else:
            print("Validation: FAILED")
            if result['validation_errors']:
                print("Errors found:")
                for err in result['validation_errors'][:10]: # Print first 10 errors
                    print(f"  - {err}")
            return 1
            
    except ValidationError as e:
        print(f"Validation Error: {e}")
        return 1
    except RuntimeError as e:
        print(f"Runtime Error: {e}")
        return 1
    except ImportError as e:
        print(f"Import Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
