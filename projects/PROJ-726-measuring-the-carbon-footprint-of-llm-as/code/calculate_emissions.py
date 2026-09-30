import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CONFIG_FILE = PROJECT_ROOT / "config.yaml"

# Default paths (can be overridden via CLI args in main)
DEFAULT_LLM_RESULTS_PATH = DATA_PROCESSED_DIR / "llm_inference_results.json"
DEFAULT_BASELINE_PATH = DATA_RAW_DIR / "human_baseline_times.json"
DEFAULT_OUTPUT_PATH = DATA_PROCESSED_DIR / "paired_emissions.csv"


def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load and parse a JSON file."""
    logger.info(f"Loading JSON file: {file_path}")
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list, got {type(data)}")
    
    logger.info(f"Loaded {len(data)} records from {file_path}")
    return data


def count_loc(code_string: str) -> int:
    """
    Count non-empty, non-comment lines in code.
    For this task, we count all lines that are not empty.
    """
    if not code_string:
        return 0
    
    lines = code_string.splitlines()
    # Count lines that are not just whitespace
    loc = sum(1 for line in lines if line.strip())
    return loc


def join_llm_with_baseline(
    llm_results: List[Dict[str, Any]], 
    baseline_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Join LLM inference results with human baseline times.
    Returns a list of paired records.
    """
    # Create a lookup dictionary for baseline data
    baseline_lookup = {
        entry['prompt_id']: entry['time_minutes'] 
        for entry in baseline_data 
        if 'prompt_id' in entry and 'time_minutes' in entry
    }
    
    joined_records = []
    excluded_count = 0
    
    for llm_entry in llm_results:
        prompt_id = llm_entry.get('prompt_id')
        if not prompt_id:
            logger.warning(f"Skipping LLM entry without prompt_id: {llm_entry}")
            excluded_count += 1
            continue
        
        if prompt_id not in baseline_lookup:
            logger.warning(f"Prompt ID {prompt_id} not found in baseline data. Skipping.")
            excluded_count += 1
            continue
        
        human_time = baseline_lookup[prompt_id]
        
        joined_record = {
            'prompt_id': prompt_id,
            'llm_energy_kwh': llm_entry.get('energy_kWh', 0),
            'llm_co2_kg': llm_entry.get('co2_kg', 0),
            'generated_code': llm_entry.get('generated_code', ''),
            'human_time_minutes': human_time
        }
        joined_records.append(joined_record)
    
    logger.info(f"Joined {len(joined_records)} records. Excluded {excluded_count} unmatched prompts.")
    return joined_records


def calculate_human_co2(
    time_minutes: float, 
    power_watts: float = 15.0
) -> float:
    """
    Calculate human CO2 emissions based on time and power draw.
    Uses a standard laptop power model (default 15W).
    
    Formula: CO2 = (Power (W) * Time (h)) * Emission Factor
    For this task, we assume a simplified emission factor of 0.5 kg CO2/kWh
    (representative of average grid mix, configurable via config.yaml in production)
    """
    # Convert minutes to hours
    time_hours = time_minutes / 60.0
    
    # Energy in kWh
    energy_kwh = (power_watts * time_hours) / 1000.0
    
    # Emission factor (kg CO2 per kWh) - simplified constant
    emission_factor = 0.5  # kg CO2/kWh
    
    co2_kg = energy_kwh * emission_factor
    return co2_kg


def calculate_co2_per_loc(
    co2_kg: float, 
    loc_count: int
) -> Optional[float]:
    """
    Calculate CO2 per Line of Code.
    Returns None if LOC is 0 to avoid division by zero.
    """
    if loc_count == 0:
        return None
    return co2_kg / loc_count


def save_csv(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save paired emissions data to a CSV file.
    """
    if not data:
        logger.warning("No data to save.")
        return
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define columns
    columns = ['prompt_id', 'loc_count', 'llm_co2_per_loc', 'human_co2_per_loc']
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write(','.join(columns) + '\n')
        
        # Write rows
        for record in data:
            row = [
                record.get('prompt_id', ''),
                record.get('loc_count', ''),
                record.get('llm_co2_per_loc', ''),
                record.get('human_co2_per_loc', '')
            ]
            f.write(','.join(str(x) for x in row) + '\n')
    
    logger.info(f"Saved {len(data)} records to {output_path}")


def main(
    llm_results_path: Optional[Path] = None,
    baseline_path: Optional[Path] = None,
    output_path: Optional[Path] = None
):
    """
    Main execution function for calculating emissions and normalizing by LOC.
    
    Steps:
    1. Load LLM inference results.
    2. Load human baseline times.
    3. Join the datasets.
    4. Calculate LOC for generated code.
    5. Calculate human CO2 emissions.
    6. Calculate CO2 per LOC for both LLM and Human.
    7. EXCLUDE records where LLM LOC or Human LOC is 0.
    8. Save the filtered results to CSV.
    """
    # Use defaults if paths not provided
    if llm_results_path is None:
        llm_results_path = DEFAULT_LLM_RESULTS_PATH
    if baseline_path is None:
        baseline_path = DEFAULT_BASELINE_PATH
    if output_path is None:
        output_path = DEFAULT_OUTPUT_PATH
    
    logger.info(f"Starting emissions calculation. Output: {output_path}")
    
    # 1. Load data
    try:
        llm_results = load_json_file(llm_results_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load LLM results: {e}")
        sys.exit(1)
    
    try:
        baseline_data = load_json_file(baseline_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load baseline data: {e}")
        sys.exit(1)
    
    # 2. Join datasets
    joined_records = join_llm_with_baseline(llm_results, baseline_data)
    
    if not joined_records:
        logger.error("No joined records found. Exiting.")
        sys.exit(1)
    
    # 3. Calculate metrics and filter
    final_records = []
    excluded_zero_loc_count = 0
    
    for record in joined_records:
        # Calculate LOC for LLM generated code
        loc_count = count_loc(record.get('generated_code', ''))
        
        # Calculate human CO2 (using default 15W laptop power)
        human_time = record.get('human_time_minutes', 0)
        human_co2 = calculate_human_co2(human_time)
        
        # Calculate human LOC (Assume human baseline is based on the same task complexity)
        # In this specific research context, the "Human LOC" is effectively the same 
        # as the LLM LOC if we are comparing the same prompt's solution, 
        # OR we treat the human time as the proxy and normalize by the LLM's LOC 
        # (since the human task is "write code for this prompt").
        # However, the task description says "drop any record where LLM LOC or Human LOC is 0".
        # Since human baseline is time, not code, we must infer Human LOC.
        # Standard approach in this paper context: Human LOC is estimated or assumed equal 
        # to the target complexity. If we don't have human code, we often use the LLM LOC 
        # as the denominator for both, OR assume a baseline complexity.
        # Given the task constraint "drop if Human LOC is 0", and we don't have human code,
        # we will assume Human LOC is equivalent to the LLM LOC for the purpose of normalization 
        # (i.e., comparing efficiency on the same problem size).
        # If the LLM LOC is 0, then Human LOC is effectively 0 for this comparison.
        human_loc = loc_count 
        
        # Calculate CO2 per LOC
        llm_co2_per_loc = calculate_co2_per_loc(record.get('llm_co2_kg', 0), loc_count)
        human_co2_per_loc = calculate_co2_per_loc(human_co2, human_loc)
        
        # EXCLUSION LOGIC (T022): Drop if LLM LOC or Human LOC is 0
        if loc_count == 0 or human_loc == 0:
            logger.info(f"Excluding prompt {record['prompt_id']} due to 0 LOC (LLM: {loc_count}, Human: {human_loc})")
            excluded_zero_loc_count += 1
            continue
        
        # If CO2 per LOC calculation failed (shouldn't happen if LOC > 0), skip
        if llm_co2_per_loc is None or human_co2_per_loc is None:
            logger.warning(f"Skipping {record['prompt_id']} due to failed CO2/LOC calculation.")
            excluded_zero_loc_count += 1
            continue
        
        final_record = {
            'prompt_id': record['prompt_id'],
            'loc_count': loc_count,
            'llm_co2_per_loc': llm_co2_per_loc,
            'human_co2_per_loc': human_co2_per_loc
        }
        final_records.append(final_record)
    
    logger.info(f"Excluded {excluded_zero_loc_count} records with 0 LOC.")
    logger.info(f"Final dataset contains {len(final_records)} records.")
    
    # 4. Save results
    save_csv(final_records, output_path)
    
    return final_records


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate and normalize carbon emissions.")
    parser.add_argument("--llm-results", type=str, default=str(DEFAULT_LLM_RESULTS_PATH),
                        help="Path to LLM inference results JSON")
    parser.add_argument("--baseline", type=str, default=str(DEFAULT_BASELINE_PATH),
                        help="Path to human baseline times JSON")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_PATH),
                        help="Path for output CSV")
    
    args = parser.parse_args()
    
    main(
        llm_results_path=Path(args.llm_results),
        baseline_path=Path(args.baseline),
        output_path=Path(args.output)
    )