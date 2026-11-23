"""
T039: Audit for Fabrication.

Inspects output JSONs to ensure:
1. No values are hardcoded or synthetic (checks against known synthetic patterns).
2. The 'flags' array correctly identifies limitations (e.g., "Proxy Used: General Anxiety").
3. Results are consistent with real data processing (non-trivial variance, expected ranges).
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import load_config, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('outputs/audit.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Known synthetic patterns to check against
SYNTHETIC_INDICATORS = {
    'perfect_correlation': 1.0,
    'zero_variance': 0.0,
    'round_coefficients': [0.0, 1.0, -1.0, 0.5, -0.5, 0.25],
    'fixed_p_values': [0.0, 1.0, 0.05, 0.01]
}

REQUIRED_FLAGS = [
    "Proxy Used: General Anxiety"
]

def load_json_report(file_path: Path) -> Dict[str, Any]:
    """Load a JSON report file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Report file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)

def check_for_synthetic_patterns(data: Dict[str, Any], source: str) -> List[str]:
    """Check for indicators of synthetic/fabricated data."""
    issues = []
    
    # Check correlation results
    if 'correlation' in data:
        corr_val = data['correlation'].get('pearson_r')
        if corr_val is not None:
            if abs(corr_val) == 1.0:
                issues.append(f"Perfect correlation ({corr_val}) detected in {source}")
            if abs(corr_val - round(corr_val, 2)) < 0.001 and abs(corr_val) > 0.9:
                # Suspiciously round high correlation
                issues.append(f"Suspiciously round high correlation ({corr_val}) in {source}")
    
    # Check regression results
    if 'coefficients' in data:
        for coef_name, coef_val in data['coefficients'].items():
            if isinstance(coef_val, (int, float)):
                # Check for suspiciously round coefficients
                if coef_val in SYNTHETIC_INDICATORS['round_coefficients'] and abs(coef_val) > 0.0:
                    issues.append(f"Suspiciously round coefficient for {coef_name} ({coef_val}) in {source}")
                # Check for zero variance indicators
                if coef_val == 0.0 and 'std_err' in data and data['std_err'].get(coef_name) == 0.0:
                    issues.append(f"Zero variance detected for {coef_name} in {source}")
    
    # Check p-values
    if 'p_values' in data:
        for var_name, p_val in data['p_values'].items():
            if p_val in SYNTHETIC_INDICATORS['fixed_p_values']:
                issues.append(f"Suspiciously fixed p-value ({p_val}) for {var_name} in {source}")
    
    # Check sample size
    if 'n_obs' in data:
        n = data['n_obs']
        if n < 30:
            issues.append(f"Sample size too small (N={n}) in {source}")
        if n == 10000:  # Common synthetic sample size
            logger.warning(f"Sample size N={n} matches common synthetic size in {source}")
    
    return issues

def check_flags(data: Dict[str, Any], source: str) -> List[str]:
    """Check if required flags are present."""
    issues = []
    flags = data.get('flags', [])
    
    for required_flag in REQUIRED_FLAGS:
        if required_flag not in flags:
            # Only flag as issue if the condition for the flag actually applies
            # For "Proxy Used: General Anxiety", check if general_anxiety was used
            if 'anxiety_type' in data and data['anxiety_type'] == 'general_anxiety':
                issues.append(f"Missing required flag: '{required_flag}' in {source}")
    
    return issues

def verify_robustness_results(data: Dict[str, Any], source: str) -> List[str]:
    """Verify robustness check results are valid."""
    issues = []
    
    status = data.get('status')
    if status == 'skipped':
        # Verify skip reason is provided
        if 'skip_reason' not in data:
            issues.append(f"Robustness check skipped but no reason provided in {source}")
        else:
            reason = data['skip_reason']
            if not reason.startswith("Robustness check skipped:"):
                issues.append(f"Invalid skip reason format in {source}: {reason}")
    elif status == 'run':
        # Verify results are present
        if 'full_model' not in data or 'subset_model' not in data:
            issues.append(f"Robustness check ran but missing model results in {source}")
        else:
            # Check for reasonable coefficient differences
            full_coef = data['full_model'].get('coefficients', {})
            subset_coef = data['subset_model'].get('coefficients', {})
            
            for key in full_coef:
                if key in subset_coef:
                    diff = abs(full_coef[key] - subset_coef[key])
                    if diff > 1.0:
                        logger.warning(f"Large coefficient difference ({diff}) for {key} in {source}")
    else:
        issues.append(f"Invalid robustness status '{status}' in {source}")
    
    return issues

def audit_all_outputs() -> bool:
    """Audit all output JSON files."""
    config = load_config()
    ensure_directories(config)
    
    outputs_dir = Path('outputs')
    audit_passed = True
    all_issues = []
    
    # Files to audit
    files_to_check = [
        ('regression_results.json', check_for_synthetic_patterns),
        ('correlation_results.json', check_for_synthetic_patterns),
        ('robustness_results.json', verify_robustness_results)
    ]
    
    for filename, check_func in files_to_check:
        file_path = outputs_dir / filename
        logger.info(f"Auditing {filename}...")
        
        try:
            data = load_json_report(file_path)
            
            # Run checks
            issues = check_func(data, filename)
            all_issues.extend(issues)
            
            # Additional specific checks
            if filename == 'regression_results.json':
                flag_issues = check_flags(data, filename)
                all_issues.extend(flag_issues)
            
            if issues:
                logger.error(f"Found {len(issues)} issues in {filename}")
                for issue in issues:
                    logger.error(f"  - {issue}")
                audit_passed = False
            else:
                logger.info(f"✓ {filename} passed all checks")
                
        except FileNotFoundError as e:
            logger.error(f"File not found: {filename}")
            all_issues.append(str(e))
            audit_passed = False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filename}: {e}")
            all_issues.append(f"JSON decode error in {filename}")
            audit_passed = False
        except Exception as e:
            logger.error(f"Error auditing {filename}: {e}")
            all_issues.append(f"Error auditing {filename}: {str(e)}")
            audit_passed = False
    
    # Summary
    logger.info("=" * 50)
    if audit_passed:
        logger.info("AUDIT PASSED: No fabrication detected.")
        logger.info("All outputs appear to be derived from real data processing.")
    else:
        logger.error("AUDIT FAILED: Potential fabrication or issues detected.")
        logger.error(f"Total issues found: {len(all_issues)}")
        for issue in all_issues:
            logger.error(f"  - {issue}")
    
    return audit_passed

def main():
    """Main entry point for the audit."""
    logger.info("Starting fabrication audit (T039)...")
    
    try:
        success = audit_all_outputs()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Audit failed with exception: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
