import json
import math
import pandas as pd
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def main():
    # 1. Load power analysis results
    power_analysis_path = paths.data("results", "power_analysis.json")
    if not power_analysis_path.exists():
        log.error(f"Power analysis file not found at {power_analysis_path}")
        raise FileNotFoundError(f"Missing {power_analysis_path}")

    with open(power_analysis_path, 'r') as f:
        power_data = json.load(f)
    
    n_required = power_data.get("N_required")
    if n_required is None:
        log.error("N_required not found in power_analysis.json")
        raise KeyError("N_required missing from power analysis results")

    # 2. Calculate N_final based on runtime budget
    # Budget: 6 hours * 3600 seconds/hour = 21600 seconds
    # Per-image budget: 60 seconds
    runtime_limit_samples = math.floor((6 * 3600) / 60)
    n_final = min(n_required, runtime_limit_samples)
    log.info(f"N_required: {n_required}, Runtime limit: {runtime_limit_samples}, N_final: {n_final}")

    # 3. Load the raw dataset
    raw_data_path = paths.data("raw", "omnidoc_tokenbench.parquet")
    if not raw_data_path.exists():
        log.error(f"Raw dataset not found at {raw_data_path}")
        raise FileNotFoundError(f"Missing {raw_data_path}")

    df = pd.read_parquet(raw_data_path)
    total_available = len(df)
    log.info(f"Total rows available in raw dataset: {total_available}")

    # 4. Deterministic sampling
    # If the dataset is smaller than N_final, we take all available rows.
    actual_sample_size = min(total_available, n_final)
    seed = 42
    
    if actual_sample_size < n_final:
        log.warning(f"Dataset size ({total_available}) is smaller than N_final ({n_final}). Sampling all available rows.")

    sampled_df = df.sample(n=actual_sample_size, random_state=seed)
    
    # 5. Write outputs
    sample_output_path = paths.data("interim", "sample.parquet")
    sampled_df.to_parquet(sample_output_path, index=False)
    log.info(f"Sampled dataset written to {sample_output_path} (size: {actual_sample_size})")

    report_path = paths.data("results", "sampling_report.json")
    report = {
        "seed": seed,
        "N_required": n_required,
        "N_final_target": n_final,
        "N_final_actual": actual_sample_size,
        "total_raw_rows": total_available,
        "status": "success" if actual_sample_size >= n_final else "undersampled"
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    log.info(f"Sampling report written to {report_path}")

if __name__ == "__main__":
    main()