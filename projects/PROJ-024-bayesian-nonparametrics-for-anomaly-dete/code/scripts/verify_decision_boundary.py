"""
Verify decision boundary configuration in config.yaml.

This script validates that:
1. Decision boundary parameters exist in config.yaml
2. Parameters are documented with clear descriptions
3. Threshold values are within reasonable bounds
4. Metadata includes audit trail information

Per US3 acceptance scenario 2 and FR-009.
"""
import os
import sys
from pathlib import Path
import yaml
from typing import Dict, Any, List, Tuple
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path: Path) -> Dict[str, Any]:
    """Load YAML configuration file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def verify_decision_boundary_section(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Verify decision_boundary section exists and is properly configured."""
    violations = []
    
    if 'decision_boundary' not in config:
        violations.append("decision_boundary section is missing from config.yaml")
        return False, violations
    
    decision_boundary = config['decision_boundary']
    
    # Check required fields
    required_fields = ['calibration_method', 'metadata']
    for field in required_fields:
        if field not in decision_boundary:
            violations.append(f"decision_boundary.{field} is missing")
    
    # Verify calibration_method is valid
    valid_methods = ['percentile', 'statistical', 'adaptive']
    if 'calibration_method' in decision_boundary:
        if decision_boundary['calibration_method'] not in valid_methods:
            violations.append(
                f"Invalid calibration_method: {decision_boundary['calibration_method']}. "
                f"Must be one of {valid_methods}"
            )
    
    # Verify percentile configuration if method is percentile
    if decision_boundary.get('calibration_method') == 'percentile':
        if 'percentile' not in decision_boundary:
            violations.append("percentile section missing when calibration_method=percentile")
        elif 'value' not in decision_boundary['percentile']:
            violations.append("percentile.value is missing")
        else:
            percentile_value = decision_boundary['percentile']['value']
            if not (0 < percentile_value < 100):
                violations.append(
                    f"percentile.value must be between 0 and 100, got {percentile_value}"
                )
    
    # Verify anomaly rate bounds
    if 'anomaly_rate_bounds' in decision_boundary:
        bounds = decision_boundary['anomaly_rate_bounds']
        if 'min_expected' in bounds and 'max_expected' in bounds:
            if bounds['min_expected'] >= bounds['max_expected']:
                violations.append(
                    "anomaly_rate_bounds.min_expected must be < max_expected"
                )
        else:
            violations.append("anomaly_rate_bounds missing min_expected or max_expected")
    
    # Verify metadata for audit trail
    if 'metadata' in decision_boundary:
        metadata = decision_boundary['metadata']
        required_metadata = ['version', 'created', 'purpose']
        for field in required_metadata:
            if field not in metadata:
                violations.append(f"decision_boundary.metadata.{field} is missing")
    
    return len(violations) == 0, violations

def verify_config_size(config_path: Path, max_size_bytes: int = 2048) -> Tuple[bool, int]:
    """Verify config.yaml is under 2KB per FR-009."""
    size_bytes = os.path.getsize(config_path)
    return size_bytes <= max_size_bytes, size_bytes

def verify_threshold_reasonableness(decision_boundary: Dict[str, Any]) -> List[str]:
    """Verify threshold values are reasonable for anomaly detection."""
    violations = []
    
    # Check percentile value
    if 'percentile' in decision_boundary:
        pct_value = decision_boundary['percentile'].get('value', 95)
        if pct_value < 50 or pct_value > 99:
            violations.append(
                f"Percentile threshold {pct_value} is unusual. "
                "Typical range: 90-99 for anomaly detection"
            )
    
    # Check z-score threshold
    if 'statistical' in decision_boundary:
        z_threshold = decision_boundary['statistical'].get('z_score_threshold', 3.0)
        if z_threshold < 2.0 or z_threshold > 5.0:
            violations.append(
                f"Z-score threshold {z_threshold} is unusual. "
                "Typical range: 2.5-4.0 for anomaly detection"
            )
    
    return violations

def main():
    """Main verification function."""
    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_path = project_root / 'config.yaml'
    
    if not config_path.exists():
        logger.error(f"config.yaml not found at {config_path}")
        sys.exit(1)
    
    logger.info(f"Loading config from {config_path}")
    config = load_config(config_path)
    
    all_violations = []
    all_passed = True
    
    # Check 1: Decision boundary section exists and is valid
    logger.info("Checking decision_boundary section...")
    valid, violations = verify_decision_boundary_section(config)
    if valid:
        logger.info("✓ decision_boundary section is valid")
    else:
        all_passed = False
        all_violations.extend(violations)
        for v in violations:
            logger.error(f"✗ {v}")
    
    # Check 2: Config file size under 2KB
    logger.info("Checking config.yaml size (must be < 2KB)...")
    size_ok, size_bytes = verify_config_size(config_path)
    if size_ok:
        logger.info(f"✓ config.yaml is {size_bytes} bytes (< 2048 bytes)")
    else:
        all_passed = False
        all_violations.append(
            f"config.yaml is {size_bytes} bytes, exceeds 2048 byte limit"
        )
        logger.error(f"✗ config.yaml is {size_bytes} bytes (exceeds 2048 byte limit)")
    
    # Check 3: Threshold values are reasonable
    if 'decision_boundary' in config:
        logger.info("Checking threshold reasonableness...")
        threshold_violations = verify_threshold_reasonableness(
            config['decision_boundary']
        )
        if threshold_violations:
            all_passed = False
            all_violations.extend(threshold_violations)
            for v in threshold_violations:
                logger.warning(f"⚠ {v}")
        else:
            logger.info("✓ Threshold values are within reasonable bounds")
    
    # Summary
    logger.info("=" * 60)
    if all_passed:
        logger.info("✓ All decision boundary verifications PASSED")
        logger.info(f"  - Decision boundary section: VALID")
        logger.info(f"  - Config file size: {size_bytes} bytes")
        logger.info(f"  - Threshold values: REASONABLE")
        sys.exit(0)
    else:
        logger.error(f"✗ Decision boundary verification FAILED with {len(all_violations)} issues")
        for v in all_violations:
            logger.error(f"  - {v}")
        sys.exit(1)

if __name__ == '__main__':
    main()
