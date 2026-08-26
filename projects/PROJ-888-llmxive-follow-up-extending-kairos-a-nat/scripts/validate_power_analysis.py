#!/usr/bin/env python3
"""
Validation script for power analysis task T004a.
Verifies that power_analysis.py runs correctly and produces expected outputs.
"""
import sys
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add code root to path
_code_root = Path(__file__).resolve().parent.parent / "code"
if str(_code_root) not in sys.path:
    sys.path.insert(0, str(_code_root))

from analysis.power_analysis import main as power_analysis_main
from utils.logging import get_logger

def validate_output():
    """Validate that power analysis produces correct output."""
    logger.info("Running power analysis validation...")
    
    try:
        # Run the analysis
        results = power_analysis_main()
        
        # Check required fields
        required_fields = ["effect_size", "power", "alpha", "beta", "calculated_N", "method"]
        for field in required_fields:
            if field not in results:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate types
        if not isinstance(results["calculated_N"], int):
            logger.error(f"calculated_N must be int, got {type(results['calculated_N'])}")
            return False
        
        if results["calculated_N"] <= 0:
            logger.error(f"calculated_N must be positive, got {results['calculated_N']}")
            return False
        
        # Check output file exists
        output_file = Path("results/power_analysis_report.json")
        if not output_file.exists():
            logger.error(f"Output file not found: {output_file}")
            return False
        
        # Verify JSON content
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
        
        if saved_data["calculated_N"] != results["calculated_N"]:
            logger.error("Mismatch between returned and saved calculated_N")
            return False
        
        logger.info(f"Validation successful! Calculated N = {results['calculated_N']}")
        return True
        
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main validation entry point."""
    logger.info("Starting power analysis validation...")
    
    success = validate_output()
    
    if success:
        logger.info("Power analysis validation PASSED")
        return 0
    else:
        logger.error("Power analysis validation FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())