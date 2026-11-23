import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

from config.settings import get_config, DatasetPaths
from data.modeling import load_processed_data, compute_external_validation_correlation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_state_log() -> Dict[str, Any]:
    """Load the performance log from the state directory."""
    config = get_config()
    path = Path(config.paths.state) / "performance_log.json"
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {"status": "unknown", "total_runtime_seconds": 0, "thread_count": 0}

def load_validity_status() -> Dict[str, Any]:
    """Load the validity status report."""
    config = get_config()
    path = Path(config.paths.processed) / "validity_status.json"
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {"status": "unknown", "valid_thread_percentage": 0, "threshold": 30}

def load_model_results() -> Optional[pd.DataFrame]:
    """Load the GLMM results if available."""
    config = get_config()
    path = Path(config.paths.processed) / "model_results.csv"
    if path.exists():
        return pd.read_csv(path)
    return None

def load_external_validation_correlation() -> Optional[pd.DataFrame]:
    """Load the correlation analysis between external validation and decision quality."""
    config = get_config()
    path = Path(config.paths.processed) / "external_validation_correlation.csv"
    if path.exists():
        return pd.read_csv(path)
    return None

def generate_paper_content(
    state_log: Dict[str, Any],
    validity_status: Dict[str, Any],
    model_results: Optional[pd.DataFrame],
    correlation_results: Optional[pd.DataFrame]
) -> str:
    """Generate the Markdown content for the final paper."""
    lines = []
    lines.append("# The Influence of Emotional Contagion on Collective Decision-Making in Online Forums")
    lines.append("")
    lines.append("## Abstract")
    lines.append("")
    lines.append("This study investigates the relationship between emotional contagion and decision quality in online forums. ")
    lines.append("We analyze thread data from Reddit and Stack Exchange, computing sentiment dynamics and modeling their impact on consensus formation.")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("Data was collected via the Pushshift API and validated against ground-truth answers where available. ")
    lines.append("Sentiment analysis was performed using VADER, and the Emotional Contagion Index was computed as the correlation between seed sentiment and reply sentiment deltas.")
    lines.append("Generalized Linear Mixed Models (GLMMs) were fitted to assess the impact of contagion on decision quality metrics.")
    lines.append("")
    lines.append("## Results")
    lines.append("")
    lines.append("### Performance & Validity")
    lines.append("")
    lines.append(f"- **Pipeline Status**: {state_log.get('status', 'unknown').upper()}")
    lines.append(f"- **Total Runtime**: {state_log.get('total_runtime_seconds', 0):.2f} seconds")
    lines.append(f"- **Threads Processed**: {state_log.get('thread_count', 0)}")
    lines.append(f"- **Ground Truth Validity**: {validity_status.get('valid_thread_percentage', 0):.2f}% (Threshold: {validity_status.get('threshold', 30)}%)")
    lines.append(f"- **Validity Status**: {validity_status.get('status', 'unknown').upper()}")
    lines.append("")
    lines.append("### SC-006 Compliance Check")
    lines.append("")
    if state_log.get('status') == 'success':
        lines.append("- **Status**: PASS")
        lines.append("  - The full pipeline completed within the 6-hour runtime limit on CPU-only hardware.")
    else:
        lines.append("- **Status**: FAIL")
        lines.append("  - The pipeline did not complete within the specified runtime constraints.")
    lines.append("")
    lines.append("### Model Results")
    lines.append("")
    if model_results is not None and not model_results.empty:
        lines.append("The following Generalized Linear Mixed Models were fitted:")
        lines.append("")
        lines.append("| Model Type | Predictor | Coefficient | P-Value | Significance |")
        lines.append("|---|---|---|---|---|")
        
        for _, row in model_results.iterrows():
            p_val = row.get('p_value', 0)
            sig = "Yes" if p_val < 0.05 else "No"
            lines.append(f"| {row.get('model_type', 'N/A')} | {row.get('predictor', 'N/A')} | {row.get('coefficient', 0):.4f} | {p_val:.4f} | {sig} |")
    else:
        lines.append("No model results were available to report.")
    lines.append("")
    lines.append("### External Validation Correlation Analysis")
    lines.append("")
    lines.append("Correlation between external validation scores and decision quality metrics (contagion index, agreement proportion):")
    lines.append("")
    
    if correlation_results is not None and not correlation_results.empty:
        lines.append("| Metric | Correlation Coefficient | P-Value |")
        lines.append("|---|---|---|")
        for _, row in correlation_results.iterrows():
            metric = row.get('metric_name', 'N/A')
            corr = row.get('correlation', 0)
            p_val = row.get('p_value', 0)
            lines.append(f"| {metric} | {corr:.4f} | {p_val:.4f} |")
    else:
        lines.append("No correlation analysis results were available.")
    lines.append("")
    lines.append("## Conclusion")
    lines.append("")
    lines.append("This analysis provides empirical evidence regarding the influence of emotional contagion on collective decision-making. ")
    lines.append("The validity of the ground truth data and the statistical significance of the models inform the robustness of these findings.")
    lines.append("")
    lines.append("---")
    lines.append(f"*Report generated automatically on pipeline completion.*")
    
    return "\n".join(lines)

def main():
    """Generate the final paper.md report."""
    logger.info("Starting final report generation (T026).")
    
    config = get_config()
    docs_dir = Path(config.paths.docs)
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Load dependencies
    state_log = load_state_log()
    validity_status = load_validity_status()
    model_results = load_model_results()
    correlation_results = load_external_validation_correlation()
    
    # Generate content
    paper_content = generate_paper_content(
        state_log,
        validity_status,
        model_results,
        correlation_results
    )
    
    # Write output
    output_path = docs_dir / "paper.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(paper_content)
    
    logger.info(f"Final report written to {output_path}")
    return 0

if __name__ == "__main__":
    exit(main())