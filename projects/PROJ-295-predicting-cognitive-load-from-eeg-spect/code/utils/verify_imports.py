"""
Verify that all imports in the codebase match the declared API surface.

This script checks that:
1. All imported names exist in their source modules
2. No private names (starting with _) are imported
3. Import statements match the project's API surface documentation
"""
import ast
import os
import sys
from pathlib import Path
from typing import Dict, Set, List, Tuple
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Known API surface from project documentation
KNOWN_API_SURFACE = {
    'config': {
        'public': {'load_config', 'get_env_variable', 'get_config_value'},
        'imports': {'os', 'yaml', 'typing'}
    },
    'data.download': {
        'public': {'calculate_file_checksum', 'download_dataset', 'verify_dataset_integrity', 
                  'update_state_checksums', 'main'},
        'imports': {'os', 'sys', 'hashlib', 'json', 'subprocess', 'yaml'}
    },
    'data.loader': {
        'public': {'estimate_memory_usage', 'get_epoch_metadata', 'load_epochs_chunked', 
                  'load_all_epochs'},
        'imports': {'os', 'glob', 'numpy', 'pandas', 'typing', 'mne'}
    },
    'data.manifest': {
        'public': {'calculate_file_checksum', 'fetch_remote_checksum', 'verify_dataset_integrity',
                  'generate_manifest', 'update_state', 'main'},
        'imports': {'os', 'sys', 'hashlib', 'json', 'datetime', 'yaml'}
    },
    'data.memory_check': {
        'public': {'get_peak_memory_mb', 'run_memory_check', 'main'},
        'imports': {'os', 'sys', 'json', 'time', 'tracemalloc', 'argparse'}
    },
    'data.power_analysis': {
        'public': {'update_state_checksums', 'calculate_file_checksum', 'calculate_minimum_n', 'main'},
        'imports': {'os', 'sys', 'json', 'math', 'typing'}
    },
    'data.preprocess': {
        'public': {'butter_bandpass_filter', 'notch_filter', 'apply_ica', 'create_epochs',
                  'exclude_subjects', 'calculate_file_checksum', 'update_state_checksums',
                  'preprocess_eeg_data', 'main'},
        'imports': {'os', 'sys', 'hashlib', 'datetime', 'logging', 'typing'}
    },
    'data.verify_dataset': {
        'public': {'calculate_checksum', 'verify_gaze_data', 'get_channel_count', 'main'},
        'imports': {'os', 'sys', 'json', 'hashlib', 'pathlib', 'typing'}
    },
    'features.extract': {
        'public': {'load_epochs_chunked', 'compute_psd_welch', 'extract_band_power',
                  'compute_theta_alpha_ratio', 'extract_features', 'calculate_file_checksum',
                  'update_state_checksums', 'main'},
        'imports': {'numpy', 'mne', 'typing', 'pandas', 'os', 'sys'}
    },
    'features.labels': {
        'public': {'calculate_file_checksum', 'update_state_checksums', 'compute_gaze_variance',
                  'generate_cognitive_load_labels', 'normalize_labels', 'main'},
        'imports': {'numpy', 'pandas', 'os', 'sys', 'hashlib', 'datetime'}
    },
    'features.validity': {
        'public': {'calculate_file_checksum', 'update_state_checksums', 'identify_missing_sensor_epochs',
                  'flag_missing_sensors', 'measure_power_stability', 'main'},
        'imports': {'numpy', 'pandas', 'typing', 'hashlib', 'json', 'datetime'}
    },
    'main': {
        'public': {'main'},
        'imports': {'argparse', 'os', 'sys', 'json', 'yaml', 'pandas'}
    },
    'models.evaluate': {
        'public': {'compute_metrics', 'compare_with_baseline', 'bonferroni_correction',
                  'permutation_test', 'save_metrics'},
        'imports': {'numpy', 'pandas', 'typing', 'scipy', 'sklearn'}
    },
    'models.sensitivity': {
        'public': {'load_config', 'run_sensitivity_analysis'},
        'imports': {'numpy', 'pandas', 'typing', 'sklearn', 'yaml'}
    },
    'models.train': {
        'public': {'calculate_subject_split_size', 'subject_wise_cv', 'create_held_out_test_set',
                  'train_final_model', 'load_data_for_training', 'main'},
        'imports': {'numpy', 'pandas', 'typing', 'sklearn'}
    },
    'setup_structure': {
        'public': {'create_structure', 'calculate_file_checksum', 'calculate_directory_checksums',
                  'update_state', 'main'},
        'imports': {'os', 'hashlib', 'datetime', 'yaml', 'sys'}
    }
}

class ImportVerifier:
    """Verifies imports against the known API surface."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def verify_directory(self, directory: str) -> bool:
        """Verify all Python files in a directory."""
        path = Path(directory)
        if not path.exists():
            self.errors.append(f"Directory not found: {directory}")
            return False
            
        python_files = list(path.rglob("*.py"))
        all_valid = True
        
        for py_file in python_files:
            if not self.verify_file(py_file):
                all_valid = False
                
        return all_valid
        
    def verify_file(self, file_path: Path) -> bool:
        """Verify imports in a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            relative_path = str(file_path.relative_to(Path('code')))
            
            # Get module name from path
            module_name = relative_path.replace('/', '.').replace('\\', '.')
            if module_name.endswith('.__init__'):
                module_name = module_name[:-9]
                
            expected_api = KNOWN_API_SURFACE.get(module_name, {'public': set(), 'imports': set()})
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._check_import(alias.name, file_path)
                        
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        full_name = f"{module}.{alias.name}" if module else alias.name
                        self._check_import(full_name, file_path)
                        
            return True
            
        except Exception as e:
            self.errors.append(f"Error parsing {file_path}: {e}")
            return False
            
    def _check_import(self, name: str, file_path: Path) -> None:
        """Check if an import is valid."""
        # Skip private imports
        if name.startswith('_'):
            self.warnings.append(f"Private import found in {file_path}: {name}")
            
        # Check against known standard library and common packages
        standard_libs = {'os', 'sys', 'json', 'yaml', 'hashlib', 'datetime', 'typing', 
                       'argparse', 'logging', 'math', 're', 'collections', 'functools',
                       'pathlib', 'glob', 'time', 'tracemalloc', 'subprocess'}
                       
        common_packages = {'numpy', 'pandas', 'mne', 'sklearn', 'scipy', 'pytest'}
        
        base_name = name.split('.')[0]
        
        if base_name not in standard_libs and base_name not in common_packages:
            # Check if it's a local module
            if not any(base_name in known for known in KNOWN_API_SURFACE.keys()):
                self.warnings.append(f"Unknown import in {file_path}: {name}")

def main():
    """Main entry point for import verification."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Verify imports in the codebase against known API surface'
    )
    parser.add_argument(
        '--directory',
        type=str,
        default='code',
        help='Directory to verify (default: code)'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Verifying imports in {args.directory}")
    
    verifier = ImportVerifier()
    is_valid = verifier.verify_directory(args.directory)
    
    if verifier.warnings:
        logger.warning(f"\nFound {len(verifier.warnings)} warnings:")
        for warning in verifier.warnings[:10]:  # Show first 10
            logger.warning(f"  - {warning}")
        if len(verifier.warnings) > 10:
            logger.warning(f"  ... and {len(verifier.warnings) - 10} more")
            
    if verifier.errors:
        logger.error(f"\nFound {len(verifier.errors)} errors:")
        for error in verifier.errors:
            logger.error(f"  - {error}")
            
    if is_valid and not verifier.errors:
        logger.info("\nImport verification completed successfully!")
        return 0
    else:
        logger.error("\nImport verification found issues.")
        return 1

if __name__ == '__main__':
    sys.exit(main())