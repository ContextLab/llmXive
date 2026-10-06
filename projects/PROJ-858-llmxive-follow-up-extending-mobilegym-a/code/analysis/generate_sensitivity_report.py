import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Import from sibling modules based on provided API surface
# Note: The API surface lists 'analysis.sensitivity' but the import path in the surface
# suggests the file is at code/analysis/sensitivity.py. We assume standard Python package structure.
# However, the provided surface says "import as: from analysis.sensitivity import ..."
# We will use the relative import structure compatible with the project root being the package root.

# We need to add code to the path to allow imports if run as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger, log_with_context
from analysis.sensitivity import load_config, load_coverage_vectors, load_validation_results, calculate_vector_scalar, align_data, compute_pearson_correlation, analyze_sensitivity, save_results

logger = get_logger(__name__)

def load_sensitivity_results(results_path: str) -> Dict[str, Any]:
    """Load sensitivity analysis results from JSON file."""
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Sensitivity results file not found: {results_path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def format_correlation_section(results: Dict[str, Any]) -> str:
    """Format the correlation section of the report."""
    r_value = results.get('pearson_r', 0.0)
    p_value = results.get('p_value', 0.0)
    sample_size = results.get('sample_size', 0)
    status = results.get('status', 'Unknown')
    
    lines = [
        "## Correlation Analysis",
        f"- **Pearson Correlation (r)**: {r_value:.4f}",
        f"- **P-value**: {p_value:.6f}",
        f"- **Sample Size**: {sample_size}",
        f"- **Status**: {status}",
        ""
    ]
    
    if status == "Proxy Validated":
        lines.append("The State Coverage Vector is a statistically significant proxy for task difficulty.")
    elif status == "Invalid Proxy":
        lines.append("The State Coverage Vector is NOT a statistically significant proxy for task difficulty.")
    else:
        lines.append("The validity of the proxy is inconclusive.")
        
    return "\n".join(lines)

def format_statistics_section(results: Dict[str, Any]) -> str:
    """Format the statistics section of the report."""
    lines = [
        "## Statistical Summary",
        f"- **Mean Scalar Value**: {results.get('mean_scalar', 0.0):.4f}",
        f"- **Std Dev Scalar**: {results.get('std_scalar', 0.0):.4f}",
        f"- **Mean Success Rate**: {results.get('mean_success_rate', 0.0):.4f}",
        f"- **Std Dev Success Rate**: {results.get('std_success_rate', 0.0):.4f}",
        ""
    ]
    return "\n".join(lines)

def format_sample_data_section(results: Dict[str, Any]) -> str:
    """Format the sample data section of the report."""
    lines = [
        "## Sample Data",
        "```json",
        json.dumps(results.get('sample_data', {}), indent=2),
        "```",
        ""
    ]
    return "\n".join(lines)

def format_metadata_section(results: Dict[str, Any]) -> str:
    """Format the metadata section of the report."""
    lines = [
        "## Metadata",
        f"- **Generated**: {datetime.now(timezone.utc).isoformat()}",
        f"- **Config Used**: {results.get('config_file', 'N/A')}",
        f"- **Coverage Vector File**: {results.get('coverage_file', 'N/A')}",
        f"- **Validation File**: {results.get('validation_file', 'N/A')}",
        ""
    ]
    return "\n".join(lines)

def generate_markdown_report(results: Dict[str, Any], output_path: str) -> None:
    """Generate the full markdown sensitivity analysis report."""
    lines = [
        "# Sensitivity Analysis Report",
        "",
        "## Summary",
        f"- **Pearson Correlation (r)**: {results.get('pearson_r', 0.0):.4f}",
        f"- **Sample Size**: {results.get('sample_size', 0)}",
        f"- **Status**: {results.get('status', 'Unknown')}",
        "",
        "## Thresholds",
        f"- **Invalid Threshold**: {results.get('invalid_threshold', 0.3)}",
        f"- **Validated Threshold**: {results.get('validated_threshold', 0.5)}",
        "",
        "## Recommendation",
    ]
    
    r_value = results.get('pearson_r', 0.0)
    validated_threshold = results.get('validated_threshold', 0.5)
    invalid_threshold = results.get('invalid_threshold', 0.3)
    
    if r_value >= validated_threshold:
        lines.append(f"Correlation r={r_value:.4f} meets validation threshold {validated_threshold}. The State Coverage Vector is a statistically significant proxy for task difficulty.")
    elif r_value < invalid_threshold:
        lines.append(f"Correlation r={r_value:.4f} is below invalid threshold {invalid_threshold}. The State Coverage Vector is NOT a statistically significant proxy for task difficulty. Consider expanding the variable set.")
    else:
        lines.append(f"Correlation r={r_value:.4f} falls between thresholds. The validity is inconclusive.")
        
    lines.extend([
        "",
        "## Conclusion",
    ])
    
    status = results.get('status', 'Unknown')
    if status == "Proxy Validated":
        lines.append("The State Coverage Vector variables ARE a statistically significant proxy for task difficulty. The methodology is validated.")
    elif status == "Invalid Proxy":
        lines.append("The State Coverage Vector variables are NOT a statistically significant proxy for task difficulty. The methodology requires revision.")
    else:
        lines.append("The validity of the State Coverage Vector as a proxy for task difficulty is inconclusive.")
        
    lines.extend([
        "",
        format_correlation_section(results),
        format_statistics_section(results),
        format_sample_data_section(results),
        format_metadata_section(results)
    ])
    
    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write("\n".join(lines))
    
    logger.info(f"Sensitivity report generated: {output_path}")

def main():
    """Main entry point for generating the sensitivity report."""
    # Default paths
    config_path = "code/analysis/config/sensitivity_config.json"
    results_path = "data/processed/sensitivity_results.json"
    output_path = "data/processed/sensitivity_report.md"
    
    # Allow command line overrides
    if len(sys.argv) > 1:
        results_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
        
    logger.info(f"Generating sensitivity report from {results_path} to {output_path}")
    
    try:
        # Load results
        results = load_sensitivity_results(results_path)
        
        # Generate report
        generate_markdown_report(results, output_path)
        
        logger.info("Sensitivity report generation completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
