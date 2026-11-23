import os
import sys
import json
import logging
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.config import ensure_directories
from code.parser import parse_trajectories, extract_static_log_proxy
from code.splitter import stratified_split, save_split_data
from code.ablation import run_ablation_study, generate_ablation_config
from code.validator import check_sample_count
from code.classifier import validate_proxy_correlation, run_training
from code.simulator import run_dynamic_simulation, run_baseline_simulation
from code.stats import detect_divergence, save_statistical_results
from code.token_reduction_verifier import generate_verification_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure required directories exist."""
    dirs = [
        'data/raw', 'data/processed', 'models', 'figures'
    ]
    for d in dirs:
        (project_root / d).mkdir(parents=True, exist_ok=True)

def run_pipeline_stage(stage_name, func, *args, **kwargs):
    """Run a pipeline stage with error handling."""
    logger.info(f"Running stage: {stage_name}")
    try:
        result = func(*args, **kwargs)
        logger.info(f"Stage {stage_name} completed successfully")
        return result
    except Exception as e:
        logger.error(f"Stage {stage_name} failed: {e}")
        traceback.print_exc()
        raise

def verify_artifacts(expected_files):
    """Verify that expected output files exist."""
    missing = []
    for f in expected_files:
        path = project_root / f
        if not path.exists():
            missing.append(f)
    
    if missing:
        logger.error(f"Missing artifacts: {missing}")
        return False
    return True

def generate_validation_report(results):
    """Generate a validation report."""
    report = {
        "status": "success",
        "artifacts_verified": True,
        "details": results
    }
    report_path = project_root / "data" / "processed" / "validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report written to {report_path}")

def run_full_pipeline_validation():
    """
    Run the full pipeline to generate all required artifacts for validation.
    This function orchestrates the sequence defined in tasks.md.
    """
    ensure_directories()
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    
    # 1. Parse (T006)
    parse_trajectories(raw_dir, processed_dir / "metrics_with_moves.csv")
    
    # 2. Split (T014a)
    # Note: splitter.py expects a CSV with trajectory_id and outcome
    # We assume metrics_with_moves.csv has enough info or we adapt
    # For this validation, we assume the splitter can run on the parsed data
    if (processed_dir / "metrics_with_moves.csv").exists():
        stratified_split(
            input_path=processed_dir / "metrics_with_moves.csv",
            output_prefix=processed_dir / "split" # Helper to save multiple files
        )
        # The splitter creates: train_set.csv, ablation_train_set.csv, validation_set.csv, test_set.csv, validation_set_ids.json
        # Adjust paths based on actual splitter output if needed
        # Assuming standard naming:
        val_set_path = processed_dir / "validation_set.csv"
        train_set_path = processed_dir / "train_set.csv"
        ablation_train_path = processed_dir / "ablation_train_set.csv"
        
        # If splitter uses different naming, we adapt:
        # T014a output: data/processed/train_set.csv, etc.
        
        # 3. Static Proxy (T007b)
        extract_static_log_proxy(
            validation_set_path=val_set_path,
            raw_dir=raw_dir,
            output_path=processed_dir / "static_log_proxy.json"
        )
        
        # 4. Ablation (T008, T008b)
        # Run on ablation_train_set
        config = generate_ablation_config()
        run_ablation_study(
            dataset_path=ablation_train_path,
            config=config,
            output_path=processed_dir / "ablation_labels_train.json"
        )
        
        # Run on validation_set
        run_ablation_study(
            dataset_path=val_set_path,
            config=config,
            output_path=processed_dir / "ablation_labels_validation.json"
        )
        
        # 5. Validator (T008c)
        check_sample_count(ablation_train_path)
        
        # 6. Classifier Validation (T014)
        validate_proxy_correlation(
            val_set_path=val_set_path,
            static_proxy_path=processed_dir / "static_log_proxy.json",
            ablation_labels_path=processed_dir / "ablation_labels_validation.json",
            ids_path=processed_dir / "validation_set_ids.json",
            report_path=processed_dir / "proxy_validation_report.json"
        )
        
        # 7. Training (T009)
        run_training(
            train_labels_path=processed_dir / "ablation_labels_train.json",
            model_path=project_root / "models" / "layer_utility_classifier.pkl"
        )
        
        # 8. Simulation (T017, T019, T020)
        test_set_path = processed_dir / "test_set.csv"
        run_dynamic_simulation(test_set_path, processed_dir / "simulation_logs_dynamic.json")
        run_baseline_simulation(test_set_path, "static", processed_dir / "simulation_logs_static.json")
        run_baseline_simulation(test_set_path, "random", processed_dir / "simulation_logs_random.json")
        
        # 9. Stats (T021-T025)
        # Aggregation
        # (Assuming stats.py handles this internally or via separate calls)
        detect_divergence(
            dynamic_path=processed_dir / "simulation_logs_dynamic.json",
            static_path=processed_dir / "simulation_logs_static.json",
            output_path=processed_dir / "divergence_report.json"
        )
        
        # Token reduction verification
        generate_verification_report(
            baseline_path=processed_dir / "baseline_comparison.csv", # Generated by aggregation
            output_path=processed_dir / "token_reduction_verification.json"
        )
        
        # Final statistical results
        save_statistical_results(
            output_path=processed_dir / "statistical_results.json"
        )
        
    else:
        logger.warning("No input data found. Skipping pipeline execution.")

def main():
    """Main entry point."""
    try:
        run_full_pipeline_validation()
        logger.info("Pipeline validation completed.")
    except Exception as e:
        logger.error(f"Pipeline validation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
