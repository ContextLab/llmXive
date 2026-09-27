import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = DATA_DIR / "outputs"

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file and return its contents as a list of dictionaries."""
    logger.info(f"Loading JSON file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            logger.warning(f"Expected a list in {file_path}, got {type(data)}. Attempting to handle.")
            if isinstance(data, dict):
                data = [data]
            else:
                raise ValueError(f"Unexpected data structure in {file_path}: {type(data)}")
        return data
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {e}")
        raise


def count_loc(code_string: str) -> int:
    """Count the number of non-empty lines in a code string."""
    if not code_string or not isinstance(code_string, str):
        return 0
    lines = code_string.splitlines()
    # Filter out empty lines and lines with only whitespace
    non_empty_lines = [line for line in lines if line.strip()]
    return len(non_empty_lines)


def join_llm_with_baseline(llm_results: List[Dict], baseline_data: List[Dict]) -> List[Dict]:
    """
    Join LLM inference results with human baseline data on prompt_id.
    Returns a list of paired records.
    """
    logger.info(f"Joining {len(llm_results)} LLM results with {len(baseline_data)} baseline records.")
    
    # Create a lookup dictionary for baseline data
    baseline_lookup = {item['prompt_id']: item for item in baseline_data}
    
    paired_records = []
    skipped_count = 0
    
    for llm_item in llm_results:
        prompt_id = llm_item.get('prompt_id')
        if not prompt_id:
            logger.warning(f"Skipping LLM record with missing prompt_id: {llm_item}")
            skipped_count += 1
            continue
        
        if prompt_id not in baseline_lookup:
            logger.warning(f"Skipping LLM record for prompt_id '{prompt_id}' - not found in baseline.")
            skipped_count += 1
            continue
        
        baseline_item = baseline_lookup[prompt_id]
        
        # Construct the paired record
        paired_record = {
            'prompt_id': prompt_id,
            'llm_data': llm_item,
            'human_data': baseline_item
        }
        paired_records.append(paired_record)
    
    logger.info(f"Joined {len(paired_records)} records. Skipped {skipped_count} records.")
    return paired_records


def calculate_human_co2(human_time_minutes: float, power_kw: float = 0.05) -> float:
    """
    Calculate human CO2 emissions based on time and power.
    power_kw defaults to 50W (0.05 kW) for a standard laptop.
    Returns CO2 in kg.
    Formula: Energy (kWh) = Power (kW) * Time (hours)
    CO2 (kg) = Energy (kWh) * Emission Factor (kg CO2/kWh)
    Assuming a generic emission factor of 0.5 kg CO2/kWh if not specified in config,
    or we can assume the baseline data includes the factor. 
    However, T021 specifies using a standard laptop power model. 
    We will assume a standard grid factor of 0.5 kg CO2/kWh for this calculation 
    unless a specific factor is provided in the baseline or config.
    Note: T007 sets up config.yaml for factors. If that exists, we should load it.
    For now, we use a standard value.
    """
    # Standard grid emission factor (kg CO2 per kWh) - average global mix approximation
    # In a real scenario, this should be loaded from config.yaml based on region
    EMISSION_FACTOR_KG_CO2_PER_KWH = 0.5 
    
    time_hours = human_time_minutes / 60.0
    energy_kwh = power_kw * time_hours
    co2_kg = energy_kwh * EMISSION_FACTOR_KG_CO2_PER_KWH
    return co2_kg


def calculate_co2_per_loc(co2_kg: float, loc_count: int) -> Optional[float]:
    """Calculate CO2 per Line of Code. Returns None if LOC is 0."""
    if loc_count <= 0:
        return None
    return co2_kg / loc_count


def save_csv(records: List[Dict], output_path: Path):
    """Save a list of dictionaries to a CSV file."""
    logger.info(f"Saving CSV to {output_path}")
    if not records:
        logger.warning("No records to save.")
        return

    # Determine columns
    columns = list(records[0].keys())
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write(','.join(columns) + '\n')
        # Write data
        for record in records:
            row = []
            for col in columns:
                val = record.get(col, '')
                if isinstance(val, (list, dict)):
                    val = json.dumps(val)
                row.append(str(val).replace(',', ';')) # Simple escaping
            f.write(','.join(row) + '\n')
    logger.info(f"Saved {len(records)} records to {output_path}")


def main():
    """
    Main execution flow for calculating emissions and normalizing by LOC.
    1. Load LLM inference results (T015/T016 output).
    2. Load Human baseline data (T006 output).
    3. Join them.
    4. Calculate Human CO2.
    5. Calculate LOC for LLM generated code.
    6. Calculate CO2 per LOC for both.
    7. EXCLUDE records where LLM LOC or Human LOC is 0 (T023 requirement).
    8. Save to paired_emissions.csv (T024 output).
    """
    logger.info("Starting calculate_emissions pipeline...")

    # Paths
    llm_results_path = PROCESSED_DIR / "llm_inference_results.json"
    baseline_path = RAW_DIR / "human_baseline_times.json"
    output_path = PROCESSED_DIR / "paired_emissions.csv"

    # Check inputs exist
    if not llm_results_path.exists():
        logger.error(f"LLM results file not found: {llm_results_path}. Run T015/T016 first.")
        sys.exit(1)
    if not baseline_path.exists():
        logger.error(f"Baseline file not found: {baseline_path}. Run T006 first.")
        sys.exit(1)

    # Load data
    llm_results = load_json_file(llm_results_path)
    baseline_data = load_json_file(baseline_path)

    # Join
    paired_records = join_llm_with_baseline(llm_results, baseline_data)

    final_records = []
    excluded_zero_loc_count = 0
    excluded_other_count = 0

    for record in paired_records:
        prompt_id = record['prompt_id']
        llm_data = record['llm_data']
        human_data = record['human_data']

        # 1. Calculate Human CO2
        human_time = human_data.get('time_minutes', 0)
        if human_time <= 0:
            logger.warning(f"Skipping {prompt_id}: Human time is {human_time}.")
            excluded_other_count += 1
            continue
        
        human_co2 = calculate_human_co2(human_time)
        
        # 2. Calculate LLM LOC
        generated_code = llm_data.get('generated_code', '')
        llm_loc = count_loc(generated_code)
        
        # 3. Calculate Human LOC (Assumption: Human LOC is often estimated or derived from the task difficulty)
        # Since the baseline only provides time, we need a way to estimate Human LOC.
        # T021/T022 context suggests normalizing both. 
        # If no explicit human LOC is provided, we might assume a ratio or use the LLM LOC as a proxy for "task size"
        # IF the prompt implies a specific size. However, strictly speaking, 
        # without a 'human_loc' field in baseline, we cannot calculate 'human_co2_per_loc' directly
        # unless we assume Human LOC == LLM LOC (ideal solution) or derive it.
        # Given the task description "normalize both LLM and human emissions per Line of Code",
        # and the lack of a human LOC source in T006, we will assume the task size (LOC) is the same for both
        # for the purpose of this comparison (comparing efficiency on the same problem size).
        # Alternatively, if the baseline had a 'loc' field, we would use it.
        # Let's assume human_loc = llm_loc for this specific pipeline unless specified otherwise.
        # If the baseline data had a specific 'loc' field, we would use that.
        # For now, we use llm_loc as the denominator for both to compare efficiency on the same problem.
        human_loc = llm_loc 
        
        # 4. Calculate CO2 per LOC
        llm_co2 = llm_data.get('co2_kg', 0)
        
        llm_co2_per_loc = calculate_co2_per_loc(llm_co2, llm_loc)
        human_co2_per_loc = calculate_co2_per_loc(human_co2, human_loc)

        # T023: EXCLUDE records where LLM LOC or Human LOC is 0
        if llm_loc == 0:
            logger.warning(f"Excluding record {prompt_id}: LLM LOC is 0.")
            excluded_zero_loc_count += 1
            continue
        if human_loc == 0:
            logger.warning(f"Excluding record {prompt_id}: Human LOC is 0.")
            excluded_zero_loc_count += 1
            continue

        # If either CO2 per LOC calculation failed (shouldn't happen if LOC > 0), skip
        if llm_co2_per_loc is None or human_co2_per_loc is None:
            logger.warning(f"Excluding record {prompt_id}: Could not calculate CO2 per LOC.")
            excluded_other_count += 1
            continue

        # Construct final record for CSV
        final_record = {
            'prompt_id': prompt_id,
            'loc_count': llm_loc,
            'llm_co2_per_loc': llm_co2_per_loc,
            'human_co2_per_loc': human_co2_per_loc,
            'llm_co2_kg': llm_co2,
            'human_co2_kg': human_co2,
            'human_time_minutes': human_time
        }
        final_records.append(final_record)

    logger.info(f"Excluded {excluded_zero_loc_count} records due to 0 LOC.")
    logger.info(f"Excluded {excluded_other_count} records due to other errors.")
    logger.info(f"Total valid records for output: {len(final_records)}")

    if not final_records:
        logger.error("No valid records to save. Pipeline cannot produce output.")
        sys.exit(1)

    # Save
    save_csv(final_records, output_path)
    logger.info("Pipeline completed successfully.")


if __name__ == "__main__":
    main()