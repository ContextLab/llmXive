"""
Task T029b: Validate classifier precision/recall against SC-006 threshold.

Reads existing classifier metrics from data/ground_truth/classifier_metrics.json,
compares against the threshold defined in code/utils/config.py (0.85),
and documents any failure in docs/paper/limitations.md.
"""
import os
import sys
import json
from pathlib import Path

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import CLASSIFIER_THRESHOLD

def setup_output_directories():
    """Ensure the docs/paper directory exists."""
    docs_dir = Path(__file__).parent.parent / "docs" / "paper"
    docs_dir.mkdir(parents=True, exist_ok=True)
    return docs_dir

def load_classifier_metrics(metrics_path: Path) -> dict:
    """
    Load classifier precision/recall metrics from JSON file.
    
    Args:
        metrics_path: Path to classifier_metrics.json
        
    Returns:
        Dictionary containing precision and recall values
        
    Raises:
        FileNotFoundError: If metrics file does not exist
        json.JSONDecodeError: If file is not valid JSON
    """
    if not metrics_path.exists():
        raise FileNotFoundError(f"Classifier metrics file not found: {metrics_path}")
        
    with open(metrics_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_threshold(metrics: dict, threshold: float) -> tuple:
    """
    Compare classifier metrics against threshold.
    
    Args:
        metrics: Dictionary with 'precision' and 'recall' keys
        threshold: Minimum required value (SC-006)
        
    Returns:
        Tuple of (pass_status, results_dict)
        pass_status: True if both precision and recall meet threshold
        results_dict: Detailed comparison results
    """
    precision = metrics.get('precision')
    recall = metrics.get('recall')
    
    if precision is None or recall is None:
        raise ValueError("Metrics must contain 'precision' and 'recall' keys")
        
    precision_pass = precision >= threshold
    recall_pass = recall >= threshold
    overall_pass = precision_pass and recall_pass
    
    results = {
        'threshold': threshold,
        'precision': precision,
        'precision_pass': precision_pass,
        'recall': recall,
        'recall_pass': recall_pass,
        'overall_pass': overall_pass
    }
    
    return overall_pass, results

def write_limitations_documentation(docs_dir: Path, results: dict, overall_pass: bool):
    """
    Document the validation results in docs/paper/limitations.md.
    
    Args:
        docs_dir: Path to docs/paper directory
        results: Validation results dictionary
        overall_pass: Whether validation passed
    """
    limitations_file = docs_dir / "limitations.md"
    
    # Read existing content if file exists
    existing_content = ""
    if limitations_file.exists():
        with open(limitations_file, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    
    # Build new section
    section_header = "\n## Classifier Threshold Validation (SC-006)\n\n"
    section_header += f"**Validation Date**: {__import__('datetime').datetime.now().isoformat()}\n\n"
    
    if overall_pass:
        status_text = "✅ PASSED"
        content = f"""The classifier precision and recall metrics meet the SC-006 threshold requirement.
- Precision: {results['precision']:.4f} (≥ {results['threshold']})
- Recall: {results['recall']:.4f} (≥ {results['threshold']})

No limitations need to be documented regarding classifier accuracy."""
    else:
        status_text = "❌ FAILED"
        limitations = []
        if not results['precision_pass']:
            limitations.append(f"- Precision ({results['precision']:.4f}) is below threshold ({results['threshold']})")
        if not results['recall_pass']:
            limitations.append(f"- Recall ({results['recall']:.4f}) is below threshold ({results['threshold']})")
        
        content = f"""The classifier precision and recall metrics **do not** meet the SC-006 threshold requirement.
This is documented as a limitation in this study:

{chr(10).join(limitations)}

**Impact on Analysis**:
The misclassification rates may affect the validity of the propensity score matching and subsequent statistical tests.
Sensitivity analyses (Task T029) have been adjusted to account for these misclassification rates.
"""
    
    # Combine with existing content
    new_content = existing_content.rstrip() + "\n" + section_header + content + "\n"
    
    # Write back to file
    with open(limitations_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    return limitations_file

def main():
    """Main entry point for classifier threshold validation."""
    project_root = Path(__file__).parent.parent
    
    # Define paths
    metrics_path = project_root / "data" / "ground_truth" / "classifier_metrics.json"
    
    print(f"Loading classifier metrics from: {metrics_path}")
    
    try:
        # Load metrics
        metrics = load_classifier_metrics(metrics_path)
        print(f"Loaded metrics: precision={metrics['precision']:.4f}, recall={metrics['recall']:.4f}")
        
        # Validate against threshold
        print(f"Validating against SC-006 threshold: {CLASSIFIER_THRESHOLD}")
        overall_pass, results = validate_threshold(metrics, CLASSIFIER_THRESHOLD)
        
        # Setup output directories
        docs_dir = setup_output_directories()
        
        # Write documentation
        limitations_file = write_limitations_documentation(docs_dir, results, overall_pass)
        print(f"Documentation written to: {limitations_file}")
        
        # Print summary
        print("\n" + "="*50)
        print("VALIDATION RESULT:", "PASSED" if overall_pass else "FAILED")
        print("="*50)
        print(f"Precision: {results['precision']:.4f} {'✓' if results['precision_pass'] else '✗'}")
        print(f"Recall:    {results['recall']:.4f} {'✓' if results['recall_pass'] else '✗'}")
        print(f"Threshold: {results['threshold']:.4f}")
        print("="*50)
        
        return 0 if overall_pass else 1
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("The classifier_metrics.json file must be generated by T017b before running this task.")
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in metrics file: {e}")
        return 1
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())