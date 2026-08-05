import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Ensure directories exist
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file and return its contents as a list of dictionaries."""
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list in {file_path}, got {type(data)}")
    
    return data

def count_loc(code_string: str) -> int:
    """
    Count the number of lines of code (LOC) in a generated code string.
    Excludes empty lines and lines containing only whitespace.
    """
    if not code_string or not isinstance(code_string, str):
        return 0
    
    lines = code_string.splitlines()
    # Count non-empty lines
    loc = sum(1 for line in lines if line.strip())
    return loc

def join_llm_with_baseline(llm_results: List[Dict], baseline_data: Dict[str, float]) -> List[Dict]:
    """
    Join LLM inference results with human baseline data.
    Only includes records where a matching baseline exists.
    """
    joined = []
    skipped_count = 0
    
    for record in llm_results:
        prompt_id = record.get("prompt_id")
        if not prompt_id:
            logger.warning(f"Skipping record missing 'prompt_id': {record}")
            continue
        
        if prompt_id not in baseline_data:
            skipped_count += 1
            continue
        
        joined_record = record.copy()
        joined_record["human_time_minutes"] = baseline_data[prompt_id]
        joined.append(joined_record)
    
    logger.info(f"Joined {len(joined)} records; skipped {skipped_count} without baseline.")
    return joined

def calculate_human_co2(time_minutes: float, power_kw: float = 0.0001) -> float:
    """
    Calculate CO2 emissions for human effort.
    
    Args:
        time_minutes: Time spent in minutes.
        power_kw: Average power consumption of a laptop in kW (default 100W = 0.1kW).
    
    Returns:
        CO2 emissions in kg.
    """
    # Convert minutes to hours
    time_hours = time_minutes / 60.0
    energy_kwh = time_hours * power_kw
    
    # Use a generic grid factor (kg CO2 / kWh) - typically ~0.4-0.5 depending on region
    # This should ideally be configurable via config.yaml, but using a standard default here
    grid_factor_kg_co2_per_kwh = 0.475 
    
    co2_kg = energy_kwh * grid_factor_kg_co2_per_kwh
    return co2_kg

def calculate_co2_per_loc(co2_kg: float, loc_count: int) -> Optional[float]:
    """
    Calculate CO2 per Line of Code.
    
    Args:
        co2_kg: Total CO2 emissions in kg.
        loc_count: Number of lines of code.
    
    Returns:
        CO2 per LOC, or None if LOC is 0 to avoid division by zero.
    """
    if loc_count <= 0:
        return None
    return co2_kg / loc_count

def save_csv(data: List[Dict], output_path: Path):
    """Save a list of dictionaries to a CSV file."""
    import csv
    
    if not data:
        logger.warning("No data to save to CSV.")
        return
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Determine fieldnames
    fieldnames = list(data[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Saved CSV to {output_path}")

def main():
    """
    Main execution flow for T022: Normalization logic.
    1. Load LLM inference results.
    2. Load human baseline times.
    3. Join data.
    4. Calculate human CO2.
    5. Calculate LOC for LLM results.
    6. Calculate CO2 per LOC for both LLM and Human.
    7. Filter out records with 0 LOC.
    8. Save to paired_emissions.csv.
    """
    logger.info("Starting T022: Normalization logic implementation.")
    
    # Paths
    llm_results_path = DATA_PROCESSED_DIR / "llm_inference_results.json"
    baseline_path = DATA_RAW_DIR / "human_baseline_times.json"
    output_path = DATA_PROCESSED_DIR / "paired_emissions.csv"
    
    # 1. Load LLM results
    if not llm_results_path.exists():
        logger.error(f"LLM results file not found: {llm_results_path}")
        sys.exit(1)
    
    llm_results = load_json_file(llm_results_path)
    logger.info(f"Loaded {len(llm_results)} LLM inference results.")
    
    # 2. Load baseline data
    if not baseline_path.exists():
        logger.error(f"Baseline file not found: {baseline_path}")
        sys.exit(1)
    
    baseline_list = load_json_file(baseline_path)
    baseline_dict = {item["prompt_id"]: item["time_minutes"] for item in baseline_list}
    logger.info(f"Loaded baseline data for {len(baseline_dict)} prompts.")
    
    # 3. Join data
    joined_data = join_llm_with_baseline(llm_results, baseline_dict)
    
    # 4 & 5 & 6: Process each record
    processed_records = []
    excluded_count = 0
    
    for record in joined_data:
        # Calculate LOC for LLM generated code
        generated_code = record.get("generated_code", "")
        loc_count = count_loc(generated_code)
        
        # Calculate Human CO2
        human_time = record.get("human_time_minutes", 0)
        human_co2 = calculate_human_co2(human_time)
        
        # Calculate CO2 per LOC for LLM
        llm_co2 = record.get("co2_kg", 0)
        llm_co2_per_loc = calculate_co2_per_loc(llm_co2, loc_count)
        
        # Calculate CO2 per LOC for Human
        human_co2_per_loc = calculate_co2_per_loc(human_co2, loc_count)
        
        # T023 Exclusion logic: Drop if LLM LOC or Human LOC is 0
        # Since Human LOC is effectively the same as LLM LOC for the same prompt task
        # (we are comparing the effort to produce the same solution), 
        # we check if loc_count is 0.
        if loc_count == 0:
            excluded_count += 1
            continue
        
        processed_records.append({
            "prompt_id": record["prompt_id"],
            "loc_count": loc_count,
            "llm_co2_per_loc": llm_co2_per_loc,
            "human_co2_per_loc": human_co2_per_loc,
            "llm_total_co2_kg": llm_co2,
            "human_total_co2_kg": human_co2,
            "human_time_minutes": human_time
        })
    
    logger.info(f"Processed {len(processed_records)} records; excluded {excluded_count} with 0 LOC.")
    
    # 8. Save to CSV
    save_csv(processed_records, output_path)
    logger.info("T022 completed successfully.")

if __name__ == "__main__":
    main()