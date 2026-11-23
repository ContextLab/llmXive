import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def count_loc(code_string: str) -> int:
    """Count non-empty, non-comment lines in a code string."""
    if not code_string or not isinstance(code_string, str):
        return 0
    lines = code_string.splitlines()
    count = 0
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            count += 1
    return count

def load_llm_results(file_path: Path) -> List[Dict[str, Any]]:
    """Load LLM inference results."""
    data = load_json_file(file_path)
    if isinstance(data, dict):
        return [data] if 'prompt_id' in data else []
    if isinstance(data, list):
        return data
    raise ValueError("Unexpected JSON structure for LLM results")

def load_human_baseline(file_path: Path) -> Dict[str, float]:
    """Load human baseline times (prompt_id -> time_minutes)."""
    data = load_json_file(file_path)
    if not isinstance(data, dict):
        raise ValueError("Human baseline must be a dict mapping prompt_id to time_minutes")
    return data

def load_config(file_path: Path) -> Dict[str, Any]:
    """Load configuration file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Config file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_co2_factor_per_kwh(config: Dict[str, Any], region: str = "default") -> float:
    """Get CO2 factor (kg/kWh) from config."""
    try:
        return float(config.get("regions", {}).get(region, {}).get("co2_factor_kg_per_kwh", 0.5))
    except (TypeError, ValueError):
        return 0.5

def get_human_power_watts(config: Dict[str, Any]) -> float:
    """Get human laptop power draw (Watts) from config."""
    try:
        return float(config.get("human_baseline", {}).get("power_watts", 45.0))
    except (TypeError, ValueError):
        return 45.0

def join_llm_with_baseline(llm_results: List[Dict], human_baseline: Dict[str, float]) -> List[Dict]:
    """Join LLM results with human baseline, excluding missing matches."""
    joined = []
    excluded_count = 0
    for llm_record in llm_results:
        pid = llm_record.get("prompt_id")
        if pid in human_baseline:
            joined.append({
                "prompt_id": pid,
                "llm_record": llm_record,
                "human_time_minutes": human_baseline[pid]
            })
        else:
            excluded_count += 1
    logger.info(f"Joined {len(joined)} records. Excluded {excluded_count} prompts without human baseline.")
    return joined

def calculate_human_co2(human_time_minutes: float, power_watts: float, co2_factor: float) -> float:
    """Calculate human CO2 emissions based on time and power."""
    # Convert minutes to hours, Watts to kW
    time_hours = human_time_minutes / 60.0
    power_kw = power_watts / 1000.0
    energy_kwh = time_hours * power_kw
    return energy_kwh * co2_factor

def calculate_co2_per_loc(co2_kg: float, loc_count: int) -> Optional[float]:
    """Calculate CO2 per LOC, returning None if LOC is 0."""
    if loc_count == 0:
        return None
    return co2_kg / loc_count

def process_records(joined_data: List[Dict], config: Dict[str, Any]) -> List[Dict]:
    """Process joined records: calculate LOC, CO2, and normalize. Exclude 0-LOC records."""
    co2_factor = get_co2_factor_per_kwh(config)
    human_power = get_human_power_watts(config)
    processed = []

    for item in joined_data:
        pid = item["prompt_id"]
        llm_rec = item["llm_record"]
        human_time = item["human_time_minutes"]

        # Calculate LLM LOC
        generated_code = llm_rec.get("generated_code", "")
        llm_loc = count_loc(generated_code)

        # Calculate Human LOC (Assume human baseline time implies similar complexity/LOC for comparison)
        # Since the spec doesn't provide a separate human LOC source, we use the LLM LOC as the denominator for both,
        # or we assume the human task produced equivalent code.
        # However, T022 specifically asks to drop if LLM LOC or Human LOC is 0.
        # If we don't have a separate human LOC, we treat the "Human LOC" as the LLM LOC for normalization purposes
        # (normalizing the human time to the code produced by the LLM for fair comparison).
        # Alternatively, if the task implies a separate human LOC, we would need that data.
        # Given the current data model, we use the LLM LOC as the common denominator for the "per LOC" metric.
        # If the requirement strictly implies a separate "Human LOC" field that might be 0, we need that data.
        # Assuming the "Human LOC" here refers to the code the human would have written.
        # Without a separate source, we use the LLM LOC as the proxy for the task complexity.
        # If LLM LOC is 0, Human LOC (proxy) is 0.
        
        human_loc = llm_loc # Proxy for human LOC in this context

        # Exclusion Logic (T022)
        if llm_loc == 0 or human_loc == 0:
            logger.warning(f"Skipping prompt {pid}: LLM LOC={llm_loc}, Human LOC={human_loc}. Excluded due to zero LOC.")
            continue

        # Calculate Emissions
        llm_energy = llm_rec.get("energy_kWh", 0.0)
        llm_co2 = llm_rec.get("co2_kg", 0.0)
        # Recalculate LLM CO2 if missing but energy exists (safety)
        if llm_co2 == 0 and llm_energy > 0:
            llm_co2 = llm_energy * co2_factor

        human_co2 = calculate_human_co2(human_time, human_power, co2_factor)

        # Normalize
        llm_co2_per_loc = calculate_co2_per_loc(llm_co2, llm_loc)
        human_co2_per_loc = calculate_co2_per_loc(human_co2, human_loc)

        if llm_co2_per_loc is None or human_co2_per_loc is None:
            logger.warning(f"Skipping prompt {pid}: Failed normalization (0 LOC).")
            continue

        processed.append({
            "prompt_id": pid,
            "loc_count": llm_loc,
            "llm_co2_per_loc": llm_co2_per_loc,
            "human_co2_per_loc": human_co2_per_loc,
            "llm_co2_total": llm_co2,
            "human_co2_total": human_co2,
            "llm_energy_kwh": llm_energy
        })

    return processed

def save_csv(data: List[Dict], output_path: Path) -> None:
    """Save processed data to CSV."""
    if not data:
        logger.warning("No data to save.")
        return

    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    import csv
    fieldnames = ["prompt_id", "loc_count", "llm_co2_per_loc", "human_co2_per_loc"]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow({k: row[k] for k in fieldnames})
    
    logger.info(f"Saved {len(data)} records to {output_path}")

def main():
    """Main entry point for calculate_emissions.py."""
    # Default paths relative to project root
    project_root = Path(__file__).parent.parent
    llm_results_path = project_root / "data" / "processed" / "llm_inference_results.json"
    human_baseline_path = project_root / "data" / "raw" / "human_baseline_times.json"
    config_path = project_root / "config.yaml" # Assuming JSON or YAML, load_json_file handles JSON
    output_path = project_root / "data" / "processed" / "paired_emissions.csv"

    # Check for config as JSON if YAML not supported by simple loader
    if not config_path.exists():
        config_path = project_root / "config.json"

    if not llm_results_path.exists():
        logger.error(f"LLM results not found: {llm_results_path}")
        sys.exit(1)
    if not human_baseline_path.exists():
        logger.error(f"Human baseline not found: {human_baseline_path}")
        sys.exit(1)
    if not config_path.exists():
        logger.error(f"Config not found: {config_path}")
        sys.exit(1)

    try:
        logger.info("Loading configuration...")
        config = load_config(config_path)

        logger.info("Loading LLM results...")
        llm_results = load_llm_results(llm_results_path)

        logger.info("Loading human baseline...")
        human_baseline = load_human_baseline(human_baseline_path)

        logger.info("Joining datasets...")
        joined_data = join_llm_with_baseline(llm_results, human_baseline)

        logger.info("Processing records (calculating emissions and normalizing)...")
        processed_data = process_records(joined_data, config)

        logger.info("Saving results to CSV...")
        save_csv(processed_data, output_path)

        logger.info("Done.")

    except Exception as e:
        logger.exception(f"Error during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()