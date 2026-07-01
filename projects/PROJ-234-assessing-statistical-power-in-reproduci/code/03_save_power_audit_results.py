"""
Task T033: Save power audit results to JSON.

Loads extracted parameters and computed sensitivity metrics,
calculates threshold met status, and saves the final audit results.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Import from existing sibling module as per API surface
from code.utils.logging_config import setup_logging

# Configure logging
logger = setup_logging()

INPUT_FILE = Path("data/processed/power_audit_results_temp.json")
OUTPUT_FILE = Path("data/processed/power_audit_results.json")
THRESHOLD = 0.8

def load_power_results(input_path: Path) -> List[Dict[str, Any]]:
    """Load the temporary power results computed by T031/T032."""
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)

def process_and_save_results(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Process results to add threshold_met status and save to final JSON.
    
    Schema: {dataset_id, observed_power, mdes, threshold_met, status}
    """
    final_results = []
    
    for record in data:
        dataset_id = record.get("dataset_id")
        observed_power = record.get("observed_power")
        mdes = record.get("mdes")
        status = record.get("status", "unknown")
        
        # Determine if threshold is met
        threshold_met = observed_power >= THRESHOLD if observed_power is not None else False
        
        final_record = {
            "dataset_id": dataset_id,
            "observed_power": observed_power,
            "mdes": mdes,
            "threshold_met": threshold_met,
            "status": status
        }
        final_results.append(final_record)
        
        logger.debug(f"Processed dataset {dataset_id}: power={observed_power}, mdes={mdes}, met={threshold_met}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=2)
    
    logger.info(f"Saved {len(final_results)} power audit results to {output_path}")

def main():
    """Main entry point for T033."""
    try:
        # The previous step (T031/T032) should have written to a temp file or we load from the computed results
        # Based on the pipeline flow, T031/T032 likely output to a temp location or we need to read from extracted_params and recompute?
        # However, T031/T032 description says "store results". Let's assume they output to a temp file or we need to read the computed state.
        # Looking at T031: "Process all entries... and store results."
        # Looking at T032: "Convert F to d... store results."
        # We assume the output of T032 is the input for T033.
        # Since T031/T032 are marked completed, they likely wrote to a file. 
        # If they didn't specify a file, we might need to re-run the logic or assume a standard location.
        # Let's assume the computed results are in 'data/processed/power_audit_results_temp.json' 
        # or we need to read 'extracted_params.json' and re-run the logic if the temp file doesn't exist.
        
        # Actually, looking at the task chain:
        # T031 computes power/MDES and stores them.
        # T032 converts F to d and updates.
        # T033 saves the final schema.
        # It is most likely that T032 wrote to a temporary file or the main output file.
        # To be safe, let's check if the input file exists. If not, we might need to re-derive from extracted_params.json
        # but the task T031/T032 implies the calculation is done.
        
        # If the previous tasks wrote to a specific file, we should use that. 
        # Since T031/T032 are marked done, let's assume they wrote to 'data/processed/power_audit_results_temp.json'
        # as a staging area, or perhaps they wrote directly to the final file but without the 'threshold_met' field.
        
        # Let's try to load from the expected temp file first.
        if not INPUT_FILE.exists():
            # Fallback: If the temp file doesn't exist, we assume the previous step wrote to the final file 
            # but maybe we need to re-process? Or perhaps the previous step wrote to 'extracted_params.json' with extra fields?
            # The task T031 says "store results". T033 says "Save results to ... with schema".
            # This implies T031/T032 might have stored in a different format or location.
            # Let's assume the previous step (T032) output is in 'data/processed/power_audit_results_temp.json'.
            # If it doesn't exist, we might need to re-run the calculation logic from extracted_params.json.
            # However, to strictly follow "Implement T033", we assume the data is available.
            # If the file is missing, we raise an error.
            raise FileNotFoundError(f"Intermediate results file not found: {INPUT_FILE}. Ensure T031/T032 completed successfully.")
        
        data = load_power_results(INPUT_FILE)
        process_and_save_results(data, OUTPUT_FILE)
        logger.info("T033 completed successfully.")
        
    except Exception as e:
        logger.error(f"T033 failed: {e}")
        raise

if __name__ == "__main__":
    main()