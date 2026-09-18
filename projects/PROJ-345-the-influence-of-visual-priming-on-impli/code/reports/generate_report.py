import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
import numpy as np

from code.config import Config
from code.viz.plots import generate_interaction_plot, generate_coefficient_table
from code.models.metrics import calculate_effect_sizes_with_bootstrap

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_limitations_section() -> str:
    """
    Generates the Limitations section of the report.
    Explicitly cites the observational nature of the study and the derived prime valence.
    """
    limitations = []
    limitations.append("## Limitations")
    limitations.append("")
    limitations.append("This study presents an **observational analysis** of the influence of visual priming on implicit attitudes.")
    limitations.append("While linear mixed-effects models control for participant and stimulus variability, the findings should be interpreted as **associational** rather than causal.")
    limitations.append("Correlations between prime valence and response times do not establish a causal mechanism without further experimental manipulation.")
    limitations.append("")
    limitations.append("Furthermore, the **prime valence** scores used in this analysis were **derived** computationally using a Valence-Arousal-Dominance (VAD) regression model.")
    limitations.append("These derived scores are estimates based on the model's training data and may not perfectly capture the subjective emotional response of all participants.")
    limitations.append("Consequently, any conclusions regarding the specific impact of 'valence' are contingent upon the validity and generalizability of the VAD model used.")
    limitations.append("")
    limitations.append("Finally, the ambiguity scores, while human-rated, represent a snapshot of perception that may vary across different cultural or temporal contexts.")
    
    return "\n".join(limitations)

def generate_report_pdf(
    results: Dict[str, Any],
    output_path: Optional[str] = None
) -> str:
    """
    Compiles the final report including plots, tables, and the limitations section.
    
    Args:
        results: Dictionary containing model coefficients, effect sizes, and metadata.
        output_path: Path to save the generated report (text/markdown for now, PDF logic placeholder).
    
    Returns:
        Path to the generated report file.
    """
    if output_path is None:
        output_path = str(Config.DATA_PROCESSED / "final_report.txt")
    
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating report at {output_path}")
    
    # 1. Generate Limitations Section
    limitations_text = generate_limitations_section()
    
    # 2. Prepare Content
    report_content = []
    report_content.append("# Report: Influence of Visual Priming on Implicit Attitudes")
    report_content.append("")
    report_content.append("## Executive Summary")
    report_content.append("This report details the statistical analysis of response times in relation to visual prime valence and stimulus ambiguity.")
    report_content.append("")
    
    # 3. Add Model Results
    if results:
        report_content.append("## Statistical Results")
        report_content.append("")
        report_content.append("### Fixed Effects Coefficients")
        report_content.append("")
        if 'fixed_effects' in results:
            fe_df = results['fixed_effects']
            report_content.append(fe_df.to_markdown(index=False))
        report_content.append("")
        
        if 'caution_note' in results:
            report_content.append(f"> **Note**: {results['caution_note']}")
            report_content.append("")
        
        # Add Effect Sizes
        if 'effect_sizes' in results:
            report_content.append("### Effect Sizes")
            report_content.append("")
            es_df = results['effect_sizes']
            report_content.append(es_df.to_markdown(index=False))
        report_content.append("")
    
    # 4. Add Limitations (Critical for T037)
    report_content.append(limitations_text)
    report_content.append("")
    
    # 5. Write to file
    full_text = "\n".join(report_content)
    with open(output_path_obj, 'w', encoding='utf-8') as f:
        f.write(full_text)
    
    logger.info(f"Report successfully written to {output_path}")
    
    # Generate plots as side artifacts if data is available
    if results and 'data' in results:
        try:
            plot_path = str(Config.DATA_PROCESSED / "interaction_plot.png")
            generate_interaction_plot(results['data'], output_path=plot_path)
            logger.info(f"Interaction plot saved to {plot_path}")
        except Exception as e:
            logger.warning(f"Could not generate interaction plot: {e}")
    
    return str(output_path_obj)

def main():
    """
    Entry point for report generation.
    Simulates loading results or expects them to be passed via config/args in a full pipeline.
    For this task, we ensure the limitations logic is present and runnable.
    """
    # Mock results for demonstration of the logic flow
    mock_results = {
        'fixed_effects': pd.DataFrame({
            'term': ['Intercept', 'prime_valence', 'stimulus_ambiguity', 'prime_valence:stimulus_ambiguity'],
            'coef': [1.2, -0.05, 0.02, -0.01],
            'pval': [0.001, 0.04, 0.12, 0.08],
            'ci_low': [1.1, -0.10, -0.01, -0.03],
            'ci_high': [1.3, 0.00, 0.05, 0.01]
        }),
        'effect_sizes': pd.DataFrame({
            'metric': ['Cohen d', 'Eta Squared'],
            'value': [0.45, 0.08],
            'ci': ['[0.2, 0.7]', '[0.02, 0.15]']
        }),
        'caution_note': "Associational analysis only; not causal",
        'data': pd.DataFrame({
            'prime_condition': ['A', 'A', 'B', 'B'],
            'response_time': [500, 520, 480, 490]
        })
    }
    
    try:
        report_path = generate_report_pdf(mock_results)
        print(f"Report generation complete: {report_path}")
        
        # Verify limitations content
        with open(report_path, 'r') as f:
            content = f.read()
            if "observational nature" in content and "derived prime valence" in content:
                print("SUCCESS: Limitations section verified.")
            else:
                print("ERROR: Limitations section missing required phrases.")
                return 1
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())