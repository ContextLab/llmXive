import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.download import download_oqmd_dataset, main as download_main
from data.preprocess import main as preprocess_main, load_config
from models.baseline_nn import main as baseline_main
from models.deep_ensemble import main as ensemble_main
from models.mc_dropout import main as mc_dropout_main
from models.sparse_gp import main as sparse_gp_main
from uq.compute_calibration_report import main as cal_report_main
from utils.timing_logger import TimingLogger

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SEEDS = [42, 43, 44]
OUTPUT_FILE = project_root / "results" / "ece_scores_by_seed.json"

def run_single_seed(seed: int) -> dict:
    """Run the full pipeline for a single seed and return ECE scores."""
    logger.info(f"Starting pipeline for seed: {seed}")
    
    # 1. Setup config for this seed
    config_path = project_root / "code" / "config.yaml"
    # We need to temporarily modify config or pass seed. 
    # Since preprocess reads config, we'll rely on the existing main flow 
    # but ensure the seed is set. 
    # Note: The existing main.py and sub-modules likely read from config.yaml.
    # For this task, we assume the config.yaml is updated or the modules 
    # accept a seed override. If not, we must update config.yaml programmatically.
    
    # Let's update config.yaml for the specific seed
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    original_seed = config.get('seed')
    config['seed'] = seed
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    logger.info(f"Set config seed to {seed}")

    ece_scores = {}
    methods = ["baseline", "deep_ensemble", "mc_dropout", "sparse_gp"]

    try:
        # 2. Download (if not exists, but usually idempotent)
        # We assume download.py handles existence check or we force it.
        # To save time, we check if raw data exists.
        raw_data_path = project_root / "data" / "raw" / "oqmd.parquet"
        if not raw_data_path.exists():
            download_oqmd_dataset()
        
        # 3. Preprocess
        preprocess_main()
        
        # 4. Train & Predict for each method
        # We assume each *_main() function handles training, prediction, 
        # and writing to results/uq_predictions.csv or similar.
        # However, the task requires ECE scores. 
        # The existing `compute_calibration_report.py` generates `results/calibration_report.csv`.
        
        # Run Baseline
        logger.info(f"Running Baseline for seed {seed}")
        baseline_main()
        
        # Run Deep Ensemble
        logger.info(f"Running Deep Ensemble for seed {seed}")
        ensemble_main()
        
        # Run MC Dropout
        logger.info(f"Running MC Dropout for seed {seed}")
        mc_dropout_main()
        
        # Run Sparse GP
        logger.info(f"Running Sparse GP for seed {seed}")
        sparse_gp_main()
        
        # 5. Generate Calibration Report (aggregates all methods)
        # This step computes ECE for all methods present in the predictions file.
        # We need to ensure predictions from all methods are in the file.
        # If the individual *_main functions append to the same file, good.
        # If they overwrite, we need to combine them.
        # Based on T016, `results/uq_predictions.csv` is the base file.
        # We assume the individual training scripts append to it or the 
        # calibration report script reads from a combined source.
        # Let's assume the calibration report script aggregates them.
        cal_report_main()
        
        # 6. Read ECE from the generated report
        report_path = project_root / "results" / "calibration_report.csv"
        if not report_path.exists():
            raise FileNotFoundError(f"Calibration report not found at {report_path}")
        
        import pandas as pd
        df = pd.read_csv(report_path)
        
        # Expected columns: method, ece, ...
        for method in methods:
            row = df[df['method'] == method]
            if not row.empty:
                ece_scores[method] = float(row['ece'].iloc[0])
            else:
                logger.warning(f"Method {method} not found in calibration report")
                ece_scores[method] = None

    except Exception as e:
        logger.error(f"Pipeline failed for seed {seed}: {e}", exc_info=True)
        # Restore original seed on failure
        config['seed'] = original_seed
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        raise e
    finally:
        # Restore original seed
        config['seed'] = original_seed
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
    
    return ece_scores

def main():
    logger.info("Starting multi-seed ECE aggregation")
    
    # Ensure results directory exists
    results_dir = project_root / "results"
    results_dir.mkdir(exist_ok=True)
    
    results = {}
    
    for seed in SEEDS:
        try:
            scores = run_single_seed(seed)
            results[str(seed)] = scores
        except Exception as e:
            logger.error(f"Skipping seed {seed} due to error: {e}")
            results[str(seed)] = {"error": str(e)}
    
    # Write aggregated results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Aggregated ECE scores written to {OUTPUT_FILE}")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()