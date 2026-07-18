"""
Quickstart Validation Script for llmXive Pipeline (T036)

This script validates the reproducibility of the pipeline by:
1. Verifying environment constraints (CPU-only, dependencies).
2. Executing the core data loading pipeline (BEIR datasets).
3. Running the redundancy injection and verification.
4. Executing the baseline and clustering-aided ranking experiments.
5. Generating statistical reports and threshold sweep analysis.
6. Verifying that all expected output artifacts are created.

Usage:
    python code/quickstart_validator.py
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path if running from code/
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_config, check_system_limits
from env_validator import run_validation
from data_loader import run_injection_pipeline, load_injected_dataset
from verify_redundancy_clusters import validate_cluster_counts
from run_pipeline import run_baseline_experiment, run_clustering_aided_experiment, run_threshold_sweep
from unique_subset_generator import generate_unique_subset
from run_baseline_unique import calculate_drop_percentage
from generate_statistical_report import run_statistical_tests, generate_markdown_report
from analyze_threshold_sweep import run_analysis
from checksums import calculate_sha256, ensure_state_file, load_state, save_state
from metrics import load_beir_ground_truth

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'data' / 'logs' / 'quickstart_validation.log')
    ]
)
logger = logging.getLogger(__name__)

class QuickstartValidator:
    def __init__(self):
        self.project_root = project_root
        self.data_dir = project_root / 'data'
        self.results_dir = self.data_dir / 'results'
        self.state_file = project_root / 'state' / 'projects' / 'PROJ-873-llmxive-follow-up-extending-active-learn.yaml'
        self.expected_artifacts = []
        self.validation_results = {}

    def ensure_directories(self):
        """Ensure all required directories exist."""
        logger.info("Ensuring directory structure...")
        dirs = [
            self.data_dir,
            self.data_dir / 'logs',
            self.data_dir / 'injected',
            self.results_dir,
            self.data_dir / 'figures',
            self.project_root / 'state' / 'projects'
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        logger.info("Directories ready.")

    def validate_environment(self) -> bool:
        """Step 1: Validate environment constraints."""
        logger.info("Step 1: Validating environment constraints...")
        try:
            # Run the env validator
            success = run_validation()
            if not success:
                logger.error("Environment validation failed.")
                return False
            
            # Check system limits explicitly
            config = get_config()
            if not check_system_limits():
                logger.error("System limits exceeded.")
                return False
            
            logger.info("Environment validation passed.")
            return True
        except Exception as e:
            logger.error(f"Environment validation error: {e}")
            return False

    def run_data_pipeline(self) -> bool:
        """Step 2: Run data loading and redundancy injection."""
        logger.info("Step 2: Running data pipeline...")
        try:
            # Run injection pipeline
            run_injection_pipeline()
            
            # Verify clusters
            success = validate_cluster_counts()
            if not success:
                logger.error("Cluster count validation failed.")
                return False
            
            # Record checksums
            beir_files = [
                self.data_dir / 'beir' / 'nfcorpus' / 'corpus.jsonl',
                self.data_dir / 'beir' / 'scifact' / 'corpus.jsonl'
            ]
            for f in beir_files:
                if f.exists():
                    checksum = calculate_sha256(str(f))
                    logger.info(f"Checksum for {f.name}: {checksum}")
            
            ensure_state_file()
            logger.info("Data pipeline completed successfully.")
            return True
        except Exception as e:
            logger.error(f"Data pipeline error: {e}")
            return False

    def run_unique_subset_generation(self) -> bool:
        """Step 3: Generate unique subset for baseline comparison."""
        logger.info("Step 3: Generating unique subset...")
        try:
            generate_unique_subset()
            
            # Verify file exists
            unique_file = self.data_dir / 'injected' / 'unique_subset.json'
            if not unique_file.exists():
                logger.error("Unique subset file not generated.")
                return False
            
            logger.info("Unique subset generation completed.")
            return True
        except Exception as e:
            logger.error(f"Unique subset generation error: {e}")
            return False

    def run_ranking_experiments(self) -> bool:
        """Step 4: Run baseline and clustering-aided experiments."""
        logger.info("Step 4: Running ranking experiments...")
        try:
            # Run baseline
            logger.info("Running baseline experiment...")
            baseline_result = run_baseline_experiment(seed=42)
            
            # Run clustering-aided
            logger.info("Running clustering-aided experiment...")
            clustering_result = run_clustering_aided_experiment(seed=42)
            
            # Run threshold sweep
            logger.info("Running threshold sweep...")
            sweep_result = run_threshold_sweep()
            
            if not baseline_result or not clustering_result:
                logger.error("Ranking experiments failed to produce results.")
                return False
            
            logger.info("Ranking experiments completed.")
            return True
        except Exception as e:
            logger.error(f"Ranking experiments error: {e}")
            return False

    def calculate_metrics(self) -> bool:
        """Step 5: Calculate NDCG drop and other metrics."""
        logger.info("Step 5: Calculating metrics...")
        try:
            # Calculate drop percentage
            drop_result = calculate_drop_percentage()
            if not drop_result:
                logger.error("Failed to calculate drop percentage.")
                return False
            
            logger.info(f"NDCG Drop calculated: {drop_result}")
            return True
        except Exception as e:
            logger.error(f"Metrics calculation error: {e}")
            return False

    def run_statistical_analysis(self) -> bool:
        """Step 6: Run statistical tests and generate reports."""
        logger.info("Step 6: Running statistical analysis...")
        try:
            # Run statistical tests
            stats_result = run_statistical_tests()
            if not stats_result:
                logger.error("Statistical tests failed.")
                return False
            
            # Generate markdown report
            report_path = generate_markdown_report()
            if not report_path or not report_path.exists():
                logger.error("Failed to generate statistical report.")
                return False
            
            # Analyze threshold sweep
            analysis_result = run_analysis()
            if not analysis_result:
                logger.error("Threshold sweep analysis failed.")
                return False
            
            logger.info("Statistical analysis completed.")
            return True
        except Exception as e:
            logger.error(f"Statistical analysis error: {e}")
            return False

    def verify_artifacts(self) -> bool:
        """Step 7: Verify all expected output artifacts exist."""
        logger.info("Step 7: Verifying output artifacts...")
        
        expected_files = [
            self.data_dir / 'injected' / 'nfcorpus_injected.json',
            self.data_dir / 'injected' / 'scifact_injected.json',
            self.data_dir / 'injected' / 'unique_subset.json',
            self.results_dir / 'baseline_results.json',
            self.results_dir / 'clustering_aided_results.json',
            self.results_dir / 'threshold_sweep.json',
            self.results_dir / 'statistical_report.md',
            self.results_dir / 'threshold_sweep_analysis.json',
            self.data_dir / 'logs' / 'comparisons.jsonl',
            self.data_dir / 'logs' / 'resources.jsonl',
            self.data_dir / 'logs' / 'quickstart_validation.log'
        ]
        
        missing = []
        for f in expected_files:
            if not f.exists():
                missing.append(str(f))
            else:
                logger.info(f"Found: {f}")
        
        if missing:
            logger.error(f"Missing artifacts: {missing}")
            return False
        
        logger.info("All artifacts verified.")
        return True

    def run_validation(self) -> bool:
        """Run the full validation pipeline."""
        logger.info("="*60)
        logger.info("Starting Quickstart Validation (T036)")
        logger.info("="*60)
        
        start_time = time.time()
        
        steps = [
            ("Environment Validation", self.validate_environment),
            ("Data Pipeline", self.run_data_pipeline),
            ("Unique Subset Generation", self.run_unique_subset_generation),
            ("Ranking Experiments", self.run_ranking_experiments),
            ("Metrics Calculation", self.calculate_metrics),
            ("Statistical Analysis", self.run_statistical_analysis),
            ("Artifact Verification", self.verify_artifacts),
        ]
        
        all_passed = True
        for step_name, step_func in steps:
            logger.info(f"\n--- {step_name} ---")
            try:
                if not step_func():
                    all_passed = False
                    logger.error(f"Step '{step_name}' failed.")
                    break
            except Exception as e:
                all_passed = False
                logger.error(f"Step '{step_name}' crashed: {e}")
                break
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info("\n" + "="*60)
        logger.info(f"Validation completed in {duration:.2f} seconds")
        if all_passed:
            logger.info("STATUS: SUCCESS - All checks passed.")
        else:
            logger.info("STATUS: FAILED - Some checks failed.")
        logger.info("="*60)
        
        return all_passed

def main():
    validator = QuickstartValidator()
    validator.ensure_directories()
    success = validator.run_validation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()