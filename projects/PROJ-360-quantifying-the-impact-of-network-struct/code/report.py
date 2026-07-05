import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Import from existing project modules as per API surface
# We do not import analyze's internals, but we might need to ensure paths exist.
# The task specifically requires reading model_performance.json.

def setup_report_logger() -> logging.Logger:
    """Setup logging for the report generation task."""
    logger = logging.getLogger("report")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_model_performance(file_path: Path) -> Dict[str, Any]:
    """Load the model performance JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Model performance file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_final_report(
    model_performance_path: Path,
    output_path: Path,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Generate the final report markdown file.
    
    Mandatory: Insert the exact "Limitations" text defined in FR-008.
    Action: Read `r2_interpretation` from model_performance.json (if present);
    if present, append it as a separate paragraph immediately following the
    mandatory Limitations text.
    """
    if logger is None:
        logger = setup_report_logger()

    logger.info(f"Loading model performance from {model_performance_path}")
    performance_data = load_model_performance(model_performance_path)
    
    r2_interpretation = performance_data.get("r2_interpretation")
    
    # Mandatory Limitations text from FR-008
    limitations_text = (
        "This study is observational. Correlations do not imply causality. "
        "The thermal conductivity tensor was reduced to a scalar by averaging "
        "principal components, which may obscure anisotropic effects."
    )

    # Build the report content
    report_content = []
    
    # Header
    report_content.append("# Final Report: Network Structure and Heat Diffusion")
    report_content.append("")
    
    # Summary Section (Basic summary based on available data)
    report_content.append("## Summary")
    report_content.append("")
    if "mean_r2" in performance_data:
        report_content.append(f"The linear regression model achieved a mean R² of {performance_data['mean_r2']:.4f}.")
    if "mean_rmse" in performance_data:
        report_content.append(f"The mean Root Mean Squared Error (RMSE) was {performance_data['mean_rmse']:.4f}.")
    report_content.append("")
    
    # Limitations Section
    report_content.append("## Limitations")
    report_content.append("")
    report_content.append(limitations_text)
    report_content.append("")
    
    # Append R2 interpretation if present (T026 requirement)
    if r2_interpretation:
        report_content.append(r2_interpretation)
        report_content.append("")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to file
    logger.info(f"Writing final report to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_content))

    logger.info("Final report generation complete.")

def main():
    """Entry point for the report generation script."""
    logger = setup_report_logger()
    
    # Define paths relative to project root
    # Assuming standard project structure: code/, results/
    project_root = Path(__file__).resolve().parent.parent
    model_performance_path = project_root / "results" / "model_performance.json"
    output_path = project_root / "results" / "final_report.md"

    try:
        generate_final_report(model_performance_path, output_path, logger)
    except FileNotFoundError as e:
        logger.error(f"Required input file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise

if __name__ == "__main__":
    main()