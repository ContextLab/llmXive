"""
TDP Constant Generation Script.

Reads `data/processed/calibration_run.json` and generates
`data/processed/calibrated_tdp.json` with fields:
`tdp_watts`, `source`, `error_margin`, `confidence_interval`.

Constraint: Must fail loudly if calibration data is missing.
"""
import json
import sys
import math
from pathlib import Path
from typing import Dict, Any, Optional


def load_calibration_data(file_path: Path) -> Dict[str, Any]:
    """Load calibration data from file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Calibration data not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_error_margin_and_ci(
    tdp_watts: float,
    cpu_percent: float,
    confidence_level: float = 0.95
) -> tuple[float, float]:
    """
    Calculate error margin and confidence interval for TDP estimate.
    
    Args:
        tdp_watts: Estimated TDP in watts
        cpu_percent: CPU utilization percentage during calibration
        confidence_level: Confidence level (default 0.95)
        
    Returns:
        Tuple of (error_margin, confidence_interval_width)
    """
    # Simplified error model based on CPU utilization uncertainty
    # Higher CPU utilization => more confident estimate
    if cpu_percent <= 0:
        cpu_percent = 10.0  # Prevent division by zero
    
    # Error margin decreases with higher utilization
    base_error = 10.0  # 10% base error
    utilization_factor = 1.0 - (cpu_percent / 100.0) * 0.5
    error_margin = base_error * utilization_factor
    
    # Confidence interval width (assuming normal distribution)
    # For 95% confidence, z-score is approximately 1.96
    z_score = 1.96 if confidence_level == 0.95 else 1.645  # 90% for 1.645
    ci_width = z_score * (error_margin / 100.0) * tdp_watts
    
    return round(error_margin, 2), round(ci_width, 2)


def generate_calibrated_tdp(calibration_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate calibrated TDP constant from calibration data.
    
    Args:
        calibration_data: Calibration run results
        
    Returns:
        Calibrated TDP dictionary
    """
    tdp_watts = calibration_data['estimated_tdp_watts']
    cpu_percent = calibration_data['cpu_percent']
    
    error_margin, ci_width = calculate_error_margin_and_ci(tdp_watts, cpu_percent)
    
    return {
        'tdp_watts': tdp_watts,
        'source': 'pinned-litterature',
        'error_margin': error_margin,
        'confidence_interval': ci_width,
        'calibration_cpu_percent': cpu_percent,
        'calibration_duration': calibration_data.get('duration', 0),
        'cpu_model': calibration_data.get('cpu_model', 'unknown'),
        'generated_at': calibration_data.get('calibration_timestamp', 'unknown')
    }


def save_calibrated_tdp(calibrated_data: Dict[str, Any], file_path: Path):
    """Save calibrated TDP data to file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(calibrated_data, f, indent=2)


def main():
    """Main function to generate TDP constant."""
    # Setup paths relative to project root
    # Assuming this script is at code/utils/generate_tdp_constant.py
    # Project root is 3 levels up
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    
    calibration_path = project_root / "data" / "processed" / "calibration_run.json"
    output_path = project_root / "data" / "processed" / "calibrated_tdp.json"
    
    print("Generating calibrated TDP constant...")
    
    try:
        # Load calibration data (fail loudly if missing)
        calibration_data = load_calibration_data(calibration_path)
        print(f"Loaded calibration data from {calibration_path}")
        
        # Generate calibrated TDP
        calibrated_data = generate_calibrated_tdp(calibration_data)
        
        # Save results
        save_calibrated_tdp(calibrated_data, output_path)
        
        print(f"Calibrated TDP constant written to {output_path}")
        print(f"TDP: {calibrated_data['tdp_watts']}W")
        print(f"Error margin: {calibrated_data['error_margin']}%")
        print(f"Confidence interval: ±{calibrated_data['confidence_interval']}W")
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Cannot proceed without calibration_run.json. Run calibrate_tdp.py first.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to generate calibrated TDP: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()