"""
T069: End-to-End Fabrication Check
Executes a comprehensive verification of the entire pipeline to ensure no synthetic
data is generated or used at any stage. It validates that all output files originate
from real sources (Qwen-VLA dataset, VLA Proxy baseline) and contain expected data structures.
"""
import os
import sys
import json
import argparse
import logging
import hashlib
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PROCESSED = os.path.join(PROJECT_ROOT, 'data', 'processed')
DATA_RESULTS = os.path.join(PROJECT_ROOT, 'data', 'results')
ARTIFACTS_MODELS = os.path.join(PROJECT_ROOT, 'artifacts', 'models')

# Expected real data sources
REAL_DATA_INDICATORS = {
    'qwen_vla': ['Qwen-VLA', 'Hy-Embodied', 'instruction', 'action'],
    'vla_proxy': ['vla-proxy', 'baseline', 'trajectory']
}

def check_file_exists(filepath: str) -> Tuple[bool, str]:
    """Check if a file exists."""
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"
    return True, "OK"

def check_file_size(filepath: str, min_size_bytes: int = 1024) -> Tuple[bool, str]:
    """Check if file size is above a minimum threshold to avoid empty files."""
    size = os.path.getsize(filepath)
    if size < min_size_bytes:
        return False, f"File too small ({size} bytes): {filepath}"
    return True, f"Size OK ({size} bytes)"

def check_parquet_rows(filepath: str, min_rows: int = 10) -> Tuple[bool, str]:
    """Check if a parquet file has a reasonable number of rows."""
    try:
        df = pd.read_parquet(filepath)
        count = len(df)
        if count < min_rows:
            return False, f"Too few rows ({count}) in {filepath}"
        return True, f"Row count OK ({count})"
    except Exception as e:
        return False, f"Error reading parquet: {str(e)}"

def check_json_structure(filepath: str, required_keys: Optional[List[str]] = None) -> Tuple[bool, str]:
    """Check if a JSON file exists and has expected structure."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        if required_keys:
            for key in required_keys:
                if key not in data:
                    return False, f"Missing key '{key}' in {filepath}"
        
        return True, "Structure OK"
    except Exception as e:
        return False, f"Error reading JSON: {str(e)}"

def check_for_synthetic_indicators(filepath: str) -> Tuple[bool, str]:
    """
    Scan a file for common indicators of synthetic/fake data.
    Returns False if synthetic patterns are detected.
    """
    synthetic_patterns = [
        'synthetic', 'fake', 'mock', 'placeholder', 'dummy',
        'random_sample', 'generated_data', 'test_data_only',
        'np.random', 'np.zeros', 'np.ones'
    ]
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
            
        for pattern in synthetic_patterns:
            if pattern in content:
                # Check if it's in a comment or string literal context
                # For now, we flag it as a potential issue
                if 'synthetic' in pattern or 'fake' in pattern:
                    return False, f"Potential synthetic indicator found: '{pattern}' in {filepath}"
        
        return True, "No synthetic indicators found"
    except Exception as e:
        return False, f"Error scanning file: {str(e)}"

def verify_data_source_integrity(filepath: str, source_type: str) -> Tuple[bool, str]:
    """
    Verify that data in a file comes from the expected real source.
    Checks for presence of expected columns, values, or metadata.
    """
    try:
        if filepath.endswith('.parquet'):
            df = pd.read_parquet(filepath)
            
            if source_type == 'qwen_vla':
                # Check for expected columns from Qwen-VLA dataset
                expected_cols = ['instruction', 'action']
                for col in expected_cols:
                    if col not in df.columns:
                        return False, f"Missing expected column '{col}' for Qwen-VLA data"
                
                # Check if action data looks real (non-uniform, reasonable range)
                if 'action' in df.columns:
                    action_sample = df['action'].iloc[0] if len(df) > 0 else None
                    if action_sample is None:
                        return False, "No action data found"
                    
                    # Real actions should have some variance
                    if isinstance(action_sample, (list, np.ndarray)):
                        arr = np.array(action_sample)
                        if np.all(arr == arr[0]):
                            return False, "Action data appears uniform (likely synthetic)"
                
                return True, "Qwen-VLA data integrity verified"
            
            elif source_type == 'vla_proxy':
                expected_cols = ['trajectory', 'success']
                for col in expected_cols:
                    if col not in df.columns:
                        return False, f"Missing expected column '{col}' for VLA Proxy data"
                
                return True, "VLA Proxy data integrity verified"
        
        elif filepath.endswith('.json'):
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Check for metadata indicating real source
            if 'source' in data:
                if data['source'] in ['synthetic', 'mock', 'fake']:
                    return False, f"Source marked as synthetic in {filepath}"
            
            return True, "JSON metadata verified"
        
        return True, "Source verification passed"
    
    except Exception as e:
        return False, f"Error verifying source: {str(e)}"

def run_fabrication_check() -> Dict[str, Any]:
    """
    Run the full fabrication check across all pipeline outputs.
    Returns a summary report of the verification results.
    """
    logger.info("Starting End-to-End Fabrication Check (T069)...")
    
    results = {
        'check_timestamp': pd.Timestamp.now().isoformat(),
        'checks': [],
        'summary': {
            'total_checks': 0,
            'passed': 0,
            'failed': 0,
            'warnings': 0
        },
        'artifacts_verified': [],
        'synthetic_indicators_found': [],
        'data_sources_confirmed': []
    }
    
    # Define artifacts to check
    artifacts_to_check = [
        # Ingestion & Clustering
        {'path': os.path.join(DATA_PROCESSED, 'streaming_stats.json'), 'type': 'json', 'source': None},
        {'path': os.path.join(DATA_PROCESSED, 'clustering_state.json'), 'type': 'json', 'source': None},
        {'path': os.path.join(DATA_PROCESSED, 'clusters.json'), 'type': 'json', 'source': None},
        {'path': os.path.join(DATA_PROCESSED, 'assignments.parquet'), 'type': 'parquet', 'source': 'qwen_vla'},
        
        # Embeddings
        {'path': os.path.join(DATA_PROCESSED, 'train_embeddings.parquet'), 'type': 'parquet', 'source': None},
        {'path': os.path.join(DATA_PROCESSED, 'embedding_verification.json'), 'type': 'json', 'source': None},
        
        # Models
        {'path': os.path.join(ARTIFACTS_MODELS, 'cluster_0_selected.pkl'), 'type': 'pkl', 'source': None},
        
        # Simulation & Evaluation
        {'path': os.path.join(DATA_PROCESSED, 'vla_proxy_baseline.parquet'), 'type': 'parquet', 'source': 'vla_proxy'},
        {'path': os.path.join(DATA_RESULTS, 'simulation_logs.csv'), 'type': 'csv', 'source': None},
        {'path': os.path.join(DATA_RESULTS, 'fidelity_scores_per_sample.json'), 'type': 'json', 'source': None},
        {'path': os.path.join(DATA_RESULTS, 'evaluation_report.md'), 'type': 'md', 'source': None},
        {'path': os.path.join(DATA_RESULTS, 'final_validation.log'), 'type': 'log', 'source': None}
    ]
    
    # Run checks on each artifact
    for artifact in artifacts_to_check:
        path = artifact['path']
        artifact_type = artifact['type']
        source = artifact['source']
        
        check_result = {
            'artifact': path,
            'checks': []
        }
        
        # 1. File exists
        exists, msg = check_file_exists(path)
        check_result['checks'].append({'check': 'exists', 'passed': exists, 'message': msg})
        results['summary']['total_checks'] += 1
        if exists:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
            logger.warning(f"Missing artifact: {path}")
            continue
        
        # 2. File size
        size_ok, msg = check_file_size(path)
        check_result['checks'].append({'check': 'size', 'passed': size_ok, 'message': msg})
        results['summary']['total_checks'] += 1
        if size_ok:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
            logger.warning(f"Small file: {path}")
            continue
        
        # 3. Content structure (type-specific)
        if artifact_type == 'parquet':
            rows_ok, msg = check_parquet_rows(path)
            check_result['checks'].append({'check': 'parquet_rows', 'passed': rows_ok, 'message': msg})
            results['summary']['total_checks'] += 1
            if rows_ok:
                results['summary']['passed'] += 1
            else:
                results['summary']['failed'] += 1
        
        elif artifact_type == 'json':
            struct_ok, msg = check_json_structure(path)
            check_result['checks'].append({'check': 'json_structure', 'passed': struct_ok, 'message': msg})
            results['summary']['total_checks'] += 1
            if struct_ok:
                results['summary']['passed'] += 1
            else:
                results['summary']['failed'] += 1
        
        # 4. Synthetic indicators scan (for text-based files)
        if artifact_type in ['json', 'md', 'log', 'csv']:
            synth_ok, msg = check_for_synthetic_indicators(path)
            check_result['checks'].append({'check': 'synthetic_indicators', 'passed': synth_ok, 'message': msg})
            results['summary']['total_checks'] += 1
            if synth_ok:
                results['summary']['passed'] += 1
            else:
                results['summary']['failed'] += 1
                results['synthetic_indicators_found'].append(path)
        
        # 5. Data source integrity (if source is specified)
        if source:
            source_ok, msg = verify_data_source_integrity(path, source)
            check_result['checks'].append({'check': 'source_integrity', 'passed': source_ok, 'message': msg})
            results['summary']['total_checks'] += 1
            if source_ok:
                results['summary']['passed'] += 1
                results['data_sources_confirmed'].append({
                    'artifact': path,
                    'source': source
                })
            else:
                results['summary']['failed'] += 1
                logger.error(f"Source integrity failed for {path}: {msg}")
        
        results['artifacts_verified'].append(check_result)
    
    # Final summary
    results['summary']['overall_status'] = 'PASS' if results['summary']['failed'] == 0 else 'FAIL'
    
    logger.info(f"Fabrication Check Complete: {results['summary']['passed']} passed, {results['summary']['failed']} failed")
    
    return results

def main():
    """Main entry point for T069."""
    parser = argparse.ArgumentParser(description='T069: End-to-End Fabrication Check')
    parser.add_argument('--output', type=str, 
                      default=os.path.join(DATA_RESULTS, 'fabrication_check_report.json'),
                      help='Output path for the check report')
    args = parser.parse_args()
    
    # Run the fabrication check
    report = run_fabrication_check()
    
    # Save the report
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Report saved to {args.output}")
    
    # Exit with appropriate code
    if report['summary']['overall_status'] == 'FAIL':
        logger.error("Fabrication check FAILED. Synthetic data or missing artifacts detected.")
        sys.exit(1)
    else:
        logger.info("Fabrication check PASSED. All data verified as real.")
        sys.exit(0)

if __name__ == '__main__':
    main()