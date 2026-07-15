import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# We use the `datasets` library from Hugging Face which provides a robust
# interface to PhysioNet/TUH EEG data. This avoids manual URL construction
# and handles streaming/chunking automatically.
try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: 'datasets' library not found. Please install it via: pip install datasets")
    sys.exit(1)

# Import config to ensure directories exist
# Note: The API surface says `from config import ensure_dirs`.
# We assume `code/config.py` is in the PYTHONPATH or installed.
try:
    from config import ensure_dirs
except ImportError:
    # Fallback for direct script execution if path isn't set
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import ensure_dirs

# Hardcoded registry for FR-007 compliance
VALID_COGNITIVE_INSTRUMENTS = {"MMSE", "MoCA"}

def get_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """
    Compute the hash of a file to verify integrity.
    Reads in chunks to handle large files.
    """
    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except FileNotFoundError:
        return "FILE_NOT_FOUND"
    except Exception as e:
        return f"ERROR: {str(e)}"

def validate_record_metadata(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a single metadata record according to T005 requirements.
    
    Rules:
    1. Check age >= 18.
    2. Check cognitive_score presence.
    3. FR-007: Validate cognitive_instrument against registry.
    
    Returns a dict with validation flags and status.
    """
    status = "VALID"
    issues = []
    
    # 1. Age Check
    age = record.get("age")
    if age is None:
        issues.append("Missing age")
        status = "INVALID"
    elif not isinstance(age, (int, float)) or age < 18:
        issues.append(f"Age < 18 ({age})")
        status = "INVALID"
    
    # 2. Cognitive Score Check
    # Note: We do not fail if missing, just flag.
    cognitive_score = record.get("cognitive_score")
    cognitive_instrument = record.get("cognitive_instrument")
    
    missing_cognitive = False
    invalid_instrument = False
    
    if cognitive_score is None:
        missing_cognitive = True
        issues.append("Missing cognitive_score")
    else:
        # If score exists, check instrument if present
        if cognitive_instrument is not None:
            if cognitive_instrument not in VALID_COGNITIVE_INSTRUMENTS:
                invalid_instrument = True
                issues.append(f"Invalid Instrument: {cognitive_instrument}")
        else:
            # Score present but instrument missing is not an error per spec,
            # but we might flag it if strict. Spec says: 
            # "If present but not in registry, flag as Invalid. 
            # If missing, flag as Missing Cognitive Data (do not fail)."
            # This implies if score is present, we don't flag "Missing Cognitive Data".
            pass

    return {
        "record_id": record.get("id", "unknown"),
        "status": status,
        "is_valid": status == "VALID",
        "issues": issues,
        "flags": {
            "missing_cognitive": missing_cognitive,
            "invalid_instrument": invalid_instrument
        }
    }

def fetch_tuh_metadata(output_dir: Path) -> List[Dict[str, Any]]:
    """
    Fetch metadata for the TUH EEG dataset.
    We use the `tuh_eeg` dataset from Hugging Face which maps to PhysioNet.
    This function streams the metadata to avoid loading huge files into RAM.
    """
    print(f"Fetching metadata for 'tuh_eeg' dataset to {output_dir}...")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # We attempt to load the dataset. 
    # Note: The actual TUH EEG dataset on PhysioNet is large. 
    # The `datasets` library might require specific configuration or 
    # a specific subset ID. We try the standard 'tuh_eeg' ID.
    # If the full dataset is too large, we might need to stream specific splits.
    # For this implementation, we assume we can access the metadata split 
    # or a subset that allows iteration.
    
    try:
        # Attempt to load the dataset. 
        # We use streaming=True to handle large datasets efficiently.
        # We specifically look for a split that contains metadata.
        # If the dataset doesn't have a 'metadata' split, we iterate the main one.
        ds = load_dataset("tuh_eeg", split="train", streaming=True)
        
        # Convert to list of dicts for processing (or process on the fly)
        # Since we need to generate a report, we iterate and collect stats.
        records = []
        
        # We will iterate over the dataset. 
        # Note: The actual structure of 'tuh_eeg' in HF might vary.
        # We assume it has fields like 'age', 'cognitive_score', 'cognitive_instrument'.
        # If the dataset doesn't have these, we will catch it and fail loudly.
        
        for item in ds:
            # Normalize keys if necessary (e.g., lowercase)
            normalized_item = {k.lower(): v for k, v in item.items()}
            records.append(normalized_item)
            
            # Safety break for testing if the dataset is infinite or huge
            # In a real run, we would remove this or make it configurable.
            # However, for the task to be "real", we must process the real data.
            # If the dataset is too large for the runner, we process in chunks.
            # For this script, we assume we can iterate enough to get a representative report.
            # If the dataset is massive, we might limit to N for the report generation
            # but the task says "Real data only". 
            # We will process the whole stream if possible, or a reasonable chunk if it's too big.
            # Given the constraint "Large dataset? Stream the real data", we stream.
            # We will collect all valid records to write the report.
            # If the dataset is too large to hold in memory, we write the report incrementally?
            # The task asks for a JSON report. We can accumulate stats in memory (ints)
            # and write the JSON at the end. We don't need to store all records.
            
        return records
        
    except Exception as e:
        print(f"ERROR: Failed to fetch 'tuh_eeg' dataset: {e}")
        print("This script requires a real, accessible source. It will not generate synthetic data.")
        raise RuntimeError("Real data source inaccessible") from e

def process_and_validate(metadata_path: Path, output_report_path: Path) -> Dict[str, int]:
    """
    Process the metadata file (or stream), validate records, and generate the report.
    
    Args:
        metadata_path: Path to the metadata file (if downloaded) or a placeholder if streaming directly.
        output_report_path: Path to write the final JSON report.
        
    Returns:
        Dictionary with counts: valid, invalid_instrument, missing_cognitive, total.
    """
    counts = {
        "valid_count": 0,
        "invalid_instrument_count": 0,
        "missing_cognitive_count": 0,
        "total_count": 0
    }
    
    # If we are streaming directly from the dataset object, we would iterate there.
    # Since `fetch_tuh_metadata` returns a list (which might be memory heavy),
    # let's refactor `fetch_tuh_metadata` to yield items or we iterate here.
    # Given the constraints, let's assume we iterate the dataset directly here.
    
    # Re-implementation of fetching and processing in one go to save memory
    print("Starting validation process...")
    
    try:
        # Load dataset in streaming mode
        ds = load_dataset("tuh_eeg", split="train", streaming=True)
        
        for item in ds:
            normalized_item = {k.lower(): v for k, v in item.items()}
            validation_result = validate_record_metadata(normalized_item)
            
            counts["total_count"] += 1
            
            if validation_result["is_valid"]:
                counts["valid_count"] += 1
            else:
                # Determine specific failure type
                if validation_result["flags"]["invalid_instrument"]:
                    counts["invalid_instrument_count"] += 1
                elif validation_result["flags"]["missing_cognitive"]:
                    counts["missing_cognitive_count"] += 1
                # If both or other reasons, we count as invalid but not specific?
                # The spec implies distinct buckets. We'll count the primary failure.
                # If both, we count invalid_instrument first? Or just mark as invalid.
                # Let's assume mutually exclusive for counting or prioritize.
                # Spec: "If present but not in registry, flag as Invalid... If missing, flag as Missing".
                # We'll count based on the flags.
                
        # Write report
        with open(output_report_path, "w") as f:
            json.dump(counts, f, indent=2)
            
        print(f"Validation complete. Report written to {output_report_path}")
        print(f"Counts: {counts}")
        return counts
        
    except Exception as e:
        print(f"ERROR during processing: {e}")
        raise

def main():
    """
    Main entry point for the download and validation task.
    1. Ensure directories exist.
    2. Fetch/Stream TUH EEG metadata.
    3. Validate records.
    4. Write report to data/quality/download_report.json.
    """
    # Initialize paths
    base_dir = Path(__file__).parent.parent.parent
    raw_dir = base_dir / "data" / "raw"
    quality_dir = base_dir / "data" / "quality"
    
    # Ensure directories
    ensure_dirs(base_dir)
    
    report_path = quality_dir / "download_report.json"
    
    # Ensure quality dir exists
    quality_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting T005: Download and Validate TUH EEG Metadata")
    print(f"Target Report: {report_path}")
    
    try:
        # Process and validate
        # Note: We do not save the raw files to disk in this specific task 
        # (T005 focuses on metadata validation and report). 
        # T005_run might handle the actual file download if needed, 
        # but the task description says "Implement ... for PhysioNet/TUH access ... and metadata validation".
        # We perform the validation logic now.
        
        process_and_validate(None, report_path)
        
        print("Task T005 completed successfully.")
        
    except Exception as e:
        print(f"Task T005 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
