"""
T025c: Generate final stability proportion report.

Reads intermediate aggregation from T025b-3 (data/processed/sensitivity_sweep.json)
and produces the definitive stability proportion report at
data/processed/sensitivity_report.json with schema:
{0.01: <float>, 0.05: <float>, 0.1: <float>}
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

from utils.config import get_config

def load_sensitivity_sweep(input_path: Path) -> Dict[str, Any]:
    """Load the intermediate aggregation file from T025b-3."""
    if not input_path.exists():
        raise FileNotFoundError(
            f"Intermediate sensitivity sweep file not found at {input_path}. "
            "Ensure T025b-3 has been completed successfully."
        )
    
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_stability_report(sweep_data: Dict[str, Any]) -> Dict[float, float]:
    """
    Generate the final stability proportion report.
    
    Extracts the stability proportion for the required thresholds: 0.01, 0.05, 0.1.
    The input sweep_data is expected to have a structure like:
    {
      "thresholds": {
        "0.01": {"proportion": 0.XX, ...},
        "0.05": {"proportion": 0.XX, ...},
        ...
      }
    }
    or similar, where we extract the 'proportion' for each key.
    """
    thresholds_to_report = [0.01, 0.05, 0.1]
    report = {}
    
    thresholds_data = sweep_data.get("thresholds", {})
    
    for t in thresholds_to_report:
        t_str = str(t)
        if t_str in thresholds_data:
            entry = thresholds_data[t_str]
            # Handle potential variations in key naming
            proportion = entry.get("proportion")
            if proportion is None:
                # Try alternative keys if 'proportion' is missing
                proportion = entry.get("stability_proportion")
                if proportion is None:
                    raise ValueError(
                        f"Could not find 'proportion' or 'stability_proportion' "
                        f"in entry for threshold {t_str}: {entry}"
                    )
            report[t] = float(proportion)
        else:
            # If a threshold is missing, it implies 0 stability or an error in previous steps
            # Based on strict requirements, we should fail if expected data is missing
            raise ValueError(
                f"Threshold {t_str} missing from sensitivity sweep data. "
                f"Available keys: {list(thresholds_data.keys())}"
            )
    
    return report

def save_report(report: Dict[float, float], output_path: Path) -> None:
    """Save the final report to the specified path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure keys are strings for JSON serialization, though float keys are valid in JSON spec,
    # some parsers prefer strings. The spec asks for {0.01: ...} which implies numeric keys in Python dict.
    # JSON standard requires string keys. We will write numeric keys as strings to be safe,
    # but the prompt schema implies a Python dict representation.
    # Standard JSON dumps converts float keys to strings.
    # To strictly match a Python dict representation if loaded later, we keep them as floats in the dict.
    # When writing to JSON, they become strings. This is standard behavior.
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logging.info(f"Stability report saved to {output_path}")

def main() -> int:
    """Main entry point for T025c."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    config = get_config()
    project_root = Path(__file__).resolve().parents[2]
    
    input_path = project_root / "data" / "processed" / "sensitivity_sweep.json"
    output_path = project_root / "data" / "processed" / "sensitivity_report.json"
    
    try:
        logging.info(f"Loading sensitivity sweep from {input_path}")
        sweep_data = load_sensitivity_sweep(input_path)
        
        logging.info("Generating stability proportion report")
        report = generate_stability_report(sweep_data)
        
        logging.info(f"Report contents: {report}")
        
        save_report(report, output_path)
        
        logging.info("T025c completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logging.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
