"""
Import refactoring utilities for llmXive project.

This module provides functions to analyze and fix import statements
across the project to ensure consistency and correctness.
"""
import ast
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Define the expected import structure for the project
PROJECT_IMPORTS = {
    'config': ['load_config', 'get_model_list_path', 'get_dataset_paths', 
              'get_sample_limits', 'get_exclusion_keywords', 'get_audio_config',
              'save_config', 'get_default_model_list'],
    'utils': ['AudioSample', 'ModelInstance'],
    'load_audio': ['load_json_dataset', 'load_librispeech_samples', 
                  'load_fma_samples', 'load_esc50_samples', 
                  'load_all_datasets', 'main'],
    'preprocess_audio': ['resample_audio', 'process_sample', 
                        'preprocess_dataset', 'main'],
    'exclude_models': ['normalize_string', 'check_model_exclusion', 
                      'filter_models', 'main'],
    'detect_hallucination': ['normalize_string', 'get_synonyms', 
                            'is_fuzzy_match', 'expand_ground_truth_entities',
                            'check_caption_entity_against_gt', 
                            'load_ground_truth_datasets', 'load_captions',
                            'detect_hallucinations', 'save_results', 'main'],
    'run_inference': ['GenerationResult', 'calculate_wilson_score_interval',
                     'calculate_confidence_intervals', 'save_ci_results',
                     'write_hallucination_rates_csv', 'run_inference_pipeline',
                     'main'],
    'analyze_correlation': ['load_hallucination_rates', 'load_human_judgments',
                           'calculate_cohens_kappa', 'generate_kappa_report',
                           'main'],
    'estimate_training_data': ['TrainingEstimate', 'extract_text_from_pdf',
                              'parse_markdown_card', 'find_hours_in_text',
                              'derive_proxy_estimate', 'process_model_card',
                              'main'],
    'handle_missing_data': ['flag_missing_as_unknown', 'validate_training_estimate',
                           'process_training_data_estimates', 
                           'handle_missing_hallucination_rates', 'main'],
    'stratified_sampling': ['load_captions', 'load_hallucination_rates',
                           'stratified_sample', 'save_sampling_pool', 'main'],
    'retrieve_crowd_judgments': ['load_job_ids', 'fetch_submissions_from_prolific',
                                'generate_mock_submissions', 'format_judgments',
                                'save_judgments_csv', 'main'],
    'checksum_data': ['calculate_sha256', 'load_manifest', 'save_manifest',
                     'register_file', 'verify_file', 'verify_all',
                     'generate_checksums_for_directory', 'main'],
    'setup_logging': ['ReproducibleFormatter', 'get_logger', 'init_logging',
                     'log_pipeline_start', 'log_pipeline_end', 'log_error'],
    'runtime_guard': ['get_runtime_config', 'time_limit_guard', 
                     'memory_limit_guard', 'with_runtime_guards',
                     'check_aborted', 'get_abort_reason', 'main'],
    'save_captions': ['load_captions_from_inference', 'save_captions_to_jsonl',
                     'main']
}

def analyze_imports(file_path: Path) -> Dict[str, Any]:
    """
    Analyze import statements in a Python file.
    
    Args:
        file_path: Path to the Python file
    
    Returns:
        Dictionary with import analysis results
    """
    result = {
        'path': str(file_path),
        'imports': [],
        'issues': [],
        'correct_imports': []
    }
    
    try:
        content = file_path.read_text(encoding='utf-8')
        tree = ast.parse(content)
    except Exception as e:
        result['issues'].append(f"Could not parse file: {e}")
        return result
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                result['imports'].append({
                    'type': 'import',
                    'module': alias.name,
                    'alias': alias.asname
                })
        
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                result['imports'].append({
                    'type': 'from',
                    'module': module,
                    'name': alias.name,
                    'alias': alias.asname
                })
    
    # Check for incorrect imports
    for imp in result['imports']:
        if imp['type'] == 'from':
            module = imp['module']
            name = imp['name']
            
            # Check if module is in our project imports
            if module in PROJECT_IMPORTS:
                if name not in PROJECT_IMPORTS[module]:
                    result['issues'].append(
                        f"Import '{name}' from '{module}' not in expected exports"
                    )
            elif not module.startswith('.') and module not in ['os', 'sys', 'json', 
                                                               'logging', 'pathlib',
                                                               'typing', 're', 'ast',
                                                               'yaml', 'csv', 'time',
                                                               'signal', 'resource',
                                                               'hashlib', 'datetime',
                                                               'nltk', 'fuzzywuzzy',
                                                               'librosa', 'pdfplumber',
                                                               'PyPDF2']:
                # Not a standard library module and not a project module
                result['issues'].append(
                    f"Unknown module '{module}' imported"
                )
            else:
                result['correct_imports'].append(imp)
        elif imp['type'] == 'import':
            module = imp['module']
            if module not in ['os', 'sys', 'json', 'logging', 'pathlib', 'typing',
                             're', 'ast', 'yaml', 'csv', 'time', 'signal', 
                             'resource', 'hashlib', 'datetime', 'nltk', 
                             'fuzzywuzzy', 'librosa', 'pdfplumber', 'PyPDF2']:
                result['issues'].append(
                    f"Unknown module '{module}' imported"
                )
            else:
                result['correct_imports'].append(imp)
    
    return result

def fix_imports(file_path: Path, dry_run: bool = True) -> Dict[str, Any]:
    """
    Fix import statements in a Python file.
    
    Args:
        file_path: Path to the Python file
        dry_run: If True, only analyze without modifying
    
    Returns:
        Dictionary with fix results
    """
    result = {
        'path': str(file_path),
        'original_issues': [],
        'fixed_issues': [],
        'success': True
    }
    
    analysis = analyze_imports(file_path)
    result['original_issues'] = analysis['issues']
    
    if not analysis['issues']:
        result['fixed_issues'].append("No issues found")
        return result
    
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        result['success'] = False
        result['original_issues'].append(f"Could not read file: {e}")
        return result
    
    # For now, we just log the issues
    # In a full implementation, we would rewrite the imports
    result['fixed_issues'].append(f"Found {len(analysis['issues'])} import issues")
    
    if not dry_run:
        # Placeholder for actual import fixing logic
        # This would require more sophisticated AST manipulation
        pass
    
    return result

def validate_all_imports(code_dir: Path) -> List[Dict[str, Any]]:
    """
    Validate imports in all Python files in a directory.
    
    Args:
        code_dir: Path to the code directory
    
    Returns:
        List of validation results for each file
    """
    results = []
    
    if not code_dir.exists():
        logger.error(f"Code directory does not exist: {code_dir}")
        return results
    
    python_files = list(code_dir.glob('**/*.py'))
    
    for py_file in python_files:
        logger.info(f"Validating {py_file}")
        result = analyze_imports(py_file)
        results.append(result)
        
        if result['issues']:
            logger.warning(f"  Issues found: {len(result['issues'])}")
            for issue in result['issues']:
                logger.warning(f"    - {issue}")
        else:
            logger.info("  No issues found")
    
    return results

def main():
    """Main entry point for the import refactoring script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Refactor import statements')
    parser.add_argument('--code-dir', type=Path, default=Path('code'),
                      help='Directory containing Python files to validate')
    parser.add_argument('--fix', action='store_true',
                      help='Fix import issues (not fully implemented)')
    parser.add_argument('--dry-run', action='store_true',
                      help='Only analyze without making changes')
    parser.add_argument('--verbose', action='store_true',
                      help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
    
    logger.info(f"Starting import validation for {args.code_dir}")
    logger.info(f"Fix mode: {args.fix}")
    
    results = validate_all_imports(args.code_dir)
    
    total_files = len(results)
    files_with_issues = sum(1 for r in results if r['issues'])
    
    logger.info(f"Validation complete:")
    logger.info(f"  Total files processed: {total_files}")
    logger.info(f"  Files with issues: {files_with_issues}")
    
    if files_with_issues > 0 and not args.fix:
        logger.info("Run with --fix to attempt automatic fixes (limited support)")
    
    return 0 if files_with_issues == 0 else 1

if __name__ == '__main__':
    exit(main())
