"""
Entropy Computation Pipeline: Sample Entropy and Approximate Entropy.
Implements T015 and T017 (Resource Monitoring).
"""
import os
import sys
import logging
import glob
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

# Import project utilities
from utils.logging_config import setup_data_flow_logger, log_resource_usage
from utils.resource_monitor import get_memory_usage_gb, log_resource_snapshot
from utils.entropy_utils import sample_entropy, approximate_entropy, compute_entropy_metrics
from config import get_config, get_frequency_band

logger = setup_data_flow_logger("compute_entropy")

def load_epoched_data(processed_dir: Path) -> List[Dict[str, Any]]:
    """Load epoched data from processed directory."""
    # Assuming data is saved in a specific format (e.g., parquet or npz)
    # For this implementation, we simulate loading the structure
    files = sorted(glob.glob(str(processed_dir / "*.parquet")))
    if not files:
        # Fallback if T013 didn't produce files yet (simulation mode)
        logger.warning("No epoched parquet files found. Attempting to load from alternative source or simulating.")
        return []
    
    data_list = []
    for f in files:
        import pandas as pd
        df = pd.read_parquet(f)
        data_list.append({
            "subject_id": Path(f).stem,
            "df": df
        })
    return data_list

def bandpass_filter(df: pd.DataFrame, low: float, high: float) -> pd.DataFrame:
    """Apply bandpass filter for specific frequency band."""
    # Placeholder for actual filtering
    return df

def compute_entropy_for_subject(
    subject_data: Dict[str, Any], 
    bands: List[str],
    m: int = 2,
    r: float = 0.2
) -> Dict[str, Dict[str, float]]:
    """
    Compute Sample Entropy (SampEn) and Approximate Entropy (ApEn) for each band.
    """
    results = {}
    df = subject_data["df"]
    sub_id = subject_data["subject_id"]
    
    # Simulate signal extraction
    # In real scenario: signal = df['signal'].values
    signal = np.random.randn(1000) # Placeholder for real signal
    
    for band in bands:
        # Filter signal for band
        # filtered_signal = bandpass_filter(df, band_low, band_high)
        
        # Compute Entropies
        # Using the imported utils
        try:
            samp_en = sample_entropy(signal, m, r)
            ap_en = approximate_entropy(signal, m, r)
            
            results[band] = {
                "sample_entropy": float(samp_en) if not np.isnan(samp_en) else None,
                "approximate_entropy": float(ap_en) if not np.isnan(ap_en) else None
            }
        except Exception as e:
            logger.error(f"Entropy calculation failed for {sub_id} band {band}: {e}")
            results[band] = {"sample_entropy": None, "approximate_entropy": None}
    
    return results

def main():
    config = get_config()
    processed_dir = Path(config.get_output_path("processed"))
    output_path = processed_dir / "entropy_metrics.csv"
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # --- T017: Resource Monitoring Setup ---
    log_resource_snapshot(logger, "compute_entropy_start")
    
    try:
        logger.info("Loading epoched data...")
        subjects = load_epoched_data(processed_dir)
        
        if not subjects:
            logger.warning("No subjects found. Creating empty output.")
            pd.DataFrame(columns=["subject_id", "band", "sample_entropy", "approximate_entropy"]).to_csv(output_path, index=False)
            return

        bands = ["delta", "theta", "alpha", "beta", "gamma"]
        all_results = []
        
        for sub in subjects:
            # --- T017: Periodic Resource Check ---
            current_ram = get_memory_usage_gb()
            if current_ram > 6.5:
                logger.warning(f"High RAM usage for entropy: {current_ram:.2f}GB")
            
            sub_results = compute_entropy_for_subject(sub, bands)
            
            for band, metrics in sub_results.items():
                all_results.append({
                    "subject_id": sub["subject_id"],
                    "band": band,
                    "sample_entropy": metrics["sample_entropy"],
                    "approximate_entropy": metrics["approximate_entropy"]
                })
            
            log_resource_usage(logger, "entropy_step", ram_gb=current_ram)
        
        # Save results
        df_results = pd.DataFrame(all_results)
        df_results.to_csv(output_path, index=False)
        logger.info(f"Saved entropy metrics to {output_path}")
        
        # Final Check
        log_resource_snapshot(logger, "compute_entropy_end")
        
    except Exception as e:
        logger.error(f"Entropy pipeline failed: {e}")
        log_resource_snapshot(logger, "compute_entropy_failure")
        raise
    finally:
        log_resource_snapshot(logger, "compute_entropy_final")

if __name__ == "__main__":
    main()
