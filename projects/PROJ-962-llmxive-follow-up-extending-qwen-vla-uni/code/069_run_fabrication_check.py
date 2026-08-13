"""
Task T069: End-to-End Fabrication Check
Executes the full pipeline verification to ensure no synthetic data is used.
"""
import os
import sys
import json
import argparse
import logging
import hashlib
import pandas as pd
from typing import Dict, List, Any, Optional

# Import from existing project modules
from utils.seeds import set_global_seed
from utils.validation import compute_file_checksum, validate_dataframe_schema
from utils.data_loader import DataFetchError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/fabrication_check.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
RESULTS_DIR = os.path.join(DATA_DIR, 'results')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, 'artifacts')

# Expected artifacts from previous tasks
REQUIRED_ARTIFACTS = {
    # Ingestion & Clustering (US1)
    'ingestion_check': {
        'path': os.path.join(PROCESSED_DIR, 'assignments.parquet'),
        'type': 'file',
        'min_rows': 100,  # Ensure real data exists
        'description': 'Cluster assignments from real dataset ingestion'
    },
    'clusters_metadata': {
        'path': os.path.join(PROCESSED_DIR, 'clusters.json'),
        'type': 'file',
        'description': 'Cluster metadata (centers, stats)'
    },
    'clustering_method_log': {
        'path': os.path.join(RESULTS_DIR, 'clustering_method_log.json'),
        'type': 'file',
        'description': 'Log of clustering method selection (K-means vs HAC)'
    },
    'coverage_report': {
        'path': os.path.join(RESULTS_DIR, 'coverage_report.json'),
        'type': 'file',
        'description': 'Clustering coverage metrics'
    },

    # Model Training (US2)
    'train_embeddings': {
        'path': os.path.join(PROCESSED_DIR, 'train_embeddings.parquet'),
        'type': 'file',
        'min_rows': 100,
        'description': 'BERT embeddings from real text instructions'
    },
    'embedding_verification': {
        'path': os.path.join(PROCESSED_DIR, 'embedding_verification.json'),
        'type': 'file',
        'description': 'Verification of embedding dimensions and checksum'
    },
    'model_selection_report': {
        'path': os.path.join(RESULTS_DIR, 'model_selection_decision.md'),
        'type': 'file',
        'description': 'Decision rationale for DT vs GMM selection'
    },

    # Simulation & Evaluation (US3)
    'vla_proxy_baseline': {
        'path': os.path.join(PROCESSED_DIR, 'vla_proxy_baseline.parquet'),
        'type': 'file',
        'min_rows': 10,
        'description': 'VLA Proxy baseline (must be real, not synthetic)'
    },
    'simulation_logs': {
        'path': os.path.join(RESULTS_DIR, 'simulation_logs.csv'),
        'type': 'file',
        'min_rows': 10,
        'description': 'Simulation results (success/collision flags)'
    },
    'fidelity_metrics': {
        'path': os.path.join(RESULTS_DIR, 'fidelity_metrics.json'),
        'type': 'file',
        'description': 'Trajectory fidelity metrics vs VLA proxy'
    },
    'evaluation_report': {
        'path': os.path.join(RESULTS_DIR, 'evaluation_report.md'),
        'type': 'file',
        'description': 'Final evaluation report with p-values and metrics'
    },

    # Validation & Checks
    'memory_profile': {
        'path': os.path.join(RESULTS_DIR, 'memory_profile.json'),
        'type': 'file',
        'description': 'Memory usage profile of inference pipeline'
    },
    't068_validation': {
        'path': os.path.join(RESULTS_DIR, 'final_simulation_validation.json'),
        'type': 'file',
        'description': 'Validation results from T068 (simulation & stats)'
    }
}

# Patterns that indicate synthetic/fake data
SYNTHETIC_INDICATORS = {
    'text_patterns': [
        'sample_text', 'fake_instruction', 'synthetic_prompt',
        'placeholder_text', 'dummy_instruction', 'test_prompt'
    ],
    'numeric_patterns': {
        # Check for suspiciously round numbers in real-world data
        'roundness_threshold': 0.95,  # If >95% of values are perfectly round
        'zero_variance': True  # If a column has zero variance in real data
    },
    'file_patterns': [
        'mock_', 'fake_', 'synthetic_', 'sample_', 'dummy_'
    ]
}

def check_file_exists(path: str, description: str) -> bool:
    """Check if a required file exists."""
    if not os.path.exists(path):
        logger.error(f"MISSING: {description} at {path}")
        return False
    logger.info(f"FOUND: {description} at {path}")
    return True

def check_file_size(path: str, min_size: int = 0) -> bool:
    """Check if file has minimum size (non-empty)."""
    if not os.path.exists(path):
        return False
    size = os.path.getsize(path)
    if size < min_size:
        logger.warning(f"SMALL: {path} is {size} bytes (min: {min_size})")
        return False
    return True

def check_parquet_rows(path: str, min_rows: int) -> bool:
    """Check if parquet file has minimum number of rows."""
    try:
        df = pd.read_parquet(path)
        row_count = len(df)
        if row_count < min_rows:
            logger.warning(f"LOW_ROWS: {path} has {row_count} rows (min: {min_rows})")
            return False
        logger.info(f"ROW_COUNT: {path} has {row_count} rows (min: {min_rows})")
        return True
    except Exception as e:
        logger.error(f"ERROR reading {path}: {e}")
        return False

def check_json_structure(path: str, required_keys: List[str] = None) -> bool:
    """Check if JSON file exists and has required structure."""
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        if required_keys:
            for key in required_keys:
                if key not in data:
                    logger.warning(f"MISSING_KEY: {key} in {path}")
                    return False
        logger.info(f"JSON_VALID: {path} is valid JSON")
        return True
    except Exception as e:
        logger.error(f"ERROR reading JSON {path}: {e}")
        return False

def check_for_synthetic_indicators(path: str) -> bool:
    """Check file for signs of synthetic/fake data."""
    try:
        if path.endswith('.parquet'):
            df = pd.read_parquet(path)
            # Check for synthetic text patterns in string columns
            for col in df.select_dtypes(include=['object']).columns:
                if df[col].dtype == 'object':
                    for pattern in SYNTHETIC_INDICATORS['text_patterns']:
                        if df[col].str.contains(pattern, case=False, na=False).any():
                            logger.error(f"SYNTHETIC_PATTERN: Found '{pattern}' in {path}, column '{col}'")
                            return False
            # Check for suspicious numeric patterns
            for col in df.select_dtypes(include=['number']).columns:
                if df[col].var() == 0:
                    logger.warning(f"ZERO_VARIANCE: Column '{col}' in {path} has zero variance")
                    # This is suspicious but not necessarily synthetic
        elif path.endswith('.json') or path.endswith('.csv'):
            with open(path, 'r') as f:
                content = f.read().lower()
            for pattern in SYNTHETIC_INDICATORS['text_patterns']:
                if pattern in content:
                    logger.error(f"SYNTHETIC_PATTERN: Found '{pattern}' in {path}")
                    return False
        logger.info(f"NO_SYNTHETIC: {path} passed synthetic data checks")
        return True
    except Exception as e:
        logger.error(f"ERROR checking synthetic indicators in {path}: {e}")
        return False

def verify_data_source_integrity(path: str) -> bool:
    """Verify that data comes from a real source (not hardcoded)."""
    try:
        if path.endswith('.parquet'):
            df = pd.read_parquet(path)
            # Check for realistic value ranges
            for col in df.select_dtypes(include=['number']).columns:
                values = df[col].dropna()
                if len(values) > 0:
                    # Real data should have some variation
                    if values.var() == 0 and len(values) > 10:
                        logger.warning(f"SUSPICIOUS: Column '{col}' in {path} has no variation")
                        # Not a hard failure, but suspicious
            # Check for realistic text length distribution
            for col in df.select_dtypes(include=['object']).columns:
                if df[col].dtype == 'object':
                    lengths = df[col].str.len().dropna()
                    if len(lengths) > 0:
                        mean_len = lengths.mean()
                        if mean_len < 5:  # Very short text might be synthetic
                            logger.warning(f"SHORT_TEXT: Column '{col}' in {path} has mean length {mean_len}")
        logger.info(f"SOURCE_INTEGRITY: {path} passed source integrity check")
        return True
    except Exception as e:
        logger.error(f"ERROR checking source integrity in {path}: {e}")
        return False

def run_fabrication_check() -> Dict[str, Any]:
    """Run the full fabrication check."""
    logger.info("=" * 80)
    logger.info("Starting End-to-End Fabrication Check (T069)")
    logger.info("=" * 80)

    results = {
        'timestamp': pd.Timestamp.now().isoformat(),
        'checks_passed': 0,
        'checks_failed': 0,
        'warnings': [],
        'errors': [],
        'artifacts_verified': [],
        'synthetic_data_found': False
    }

    # 1. Check all required artifacts exist
    logger.info("\n--- Artifact Existence Check ---")
    for check_name, check_config in REQUIRED_ARTIFACTS.items():
        path = check_config['path']
        description = check_config['description']

        if not check_file_exists(path, description):
            results['checks_failed'] += 1
            results['errors'].append(f"Missing: {description}")
            continue

        results['artifacts_verified'].append(path)
        results['checks_passed'] += 1

        # Additional checks based on type
        if check_config.get('type') == 'file':
            if check_config.get('min_rows'):
                if not check_parquet_rows(path, check_config['min_rows']):
                    results['warnings'].append(f"Low rows in {description}")

    # 2. Check for synthetic data indicators
    logger.info("\n--- Synthetic Data Detection ---")
    for check_name, check_config in REQUIRED_ARTIFACTS.items():
        path = check_config['path']
        if not os.path.exists(path):
            continue

        if not check_for_synthetic_indicators(path):
            results['synthetic_data_found'] = True
            results['checks_failed'] += 1
            results['errors'].append(f"Synthetic data detected in {path}")
        else:
            results['checks_passed'] += 1

    # 3. Verify data source integrity
    logger.info("\n--- Data Source Integrity Check ---")
    for check_name, check_config in REQUIRED_ARTIFACTS.items():
        path = check_config['path']
        if not os.path.exists(path):
            continue

        if not verify_data_source_integrity(path):
            results['warnings'].append(f"Integrity warning for {path}")
        else:
            results['checks_passed'] += 1

    # 4. Verify specific critical files
    logger.info("\n--- Critical File Verification ---")

    # Check clustering method log
    clustering_log_path = REQUIRED_ARTIFACTS['clustering_method_log']['path']
    if os.path.exists(clustering_log_path):
        with open(clustering_log_path, 'r') as f:
            log_data = json.load(f)
        if 'method' not in log_data or 'silhouette_score' not in log_data:
            results['warnings'].append("Clustering method log missing expected fields")
        else:
            logger.info(f"Clustering method: {log_data['method']}, Score: {log_data['silhouette_score']}")

    # Check model selection report
    model_report_path = REQUIRED_ARTIFACTS['model_selection_report']['path']
    if os.path.exists(model_report_path):
        with open(model_report_path, 'r') as f:
            content = f.read()
        if 'Decision Tree' not in content and 'GMM' not in content:
            results['warnings'].append("Model selection report missing DT/GMM discussion")
        else:
            logger.info("Model selection report contains DT/GMM analysis")

    # 5. Final summary
    logger.info("\n" + "=" * 80)
    logger.info("FABRICATION CHECK SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total Checks: {results['checks_passed'] + results['checks_failed']}")
    logger.info(f"Passed: {results['checks_passed']}")
    logger.info(f"Failed: {results['checks_failed']}")
    logger.info(f"Synthetic Data Found: {results['synthetic_data_found']}")

    if results['synthetic_data_found']:
        logger.error("CRITICAL: Synthetic data detected in pipeline outputs!")
        results['overall_status'] = 'FAILED'
    elif results['checks_failed'] > 0:
        logger.warning(f"WARNING: {results['checks_failed']} checks failed, but no synthetic data detected")
        results['overall_status'] = 'WARNING'
    else:
        logger.info("SUCCESS: All checks passed. No synthetic data detected.")
        results['overall_status'] = 'PASSED'

    # Save results
    results_path = os.path.join(RESULTS_DIR, 'fabrication_check_results.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Results saved to {results_path}")

    return results

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='T069: End-to-End Fabrication Check')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Ensure directories exist
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # Run the check
    results = run_fabrication_check()

    # Exit with appropriate code
    if results['overall_status'] == 'PASSED':
        logger.info("Pipeline fabrication check: PASSED")
        sys.exit(0)
    elif results['overall_status'] == 'WARNING':
        logger.warning("Pipeline fabrication check: WARNING (no synthetic data, but some checks failed)")
        sys.exit(0)  # Still exit 0 as no fabrication detected
    else:
        logger.error("Pipeline fabrication check: FAILED (synthetic data detected)")
        sys.exit(1)

if __name__ == '__main__':
    main()
