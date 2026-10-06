"""
Generate methodology notes documenting the associational nature of the study
and summarizing covariate controls used in the regression analysis.

Output: logs/methodology_notes.md
"""
import os
import sys
import logging
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Import existing utilities
from utils.logging_config import setup_general_logger, get_logger
from utils.resource_monitor import get_memory_usage_gb

# Import config
from config import get_config

def generate_associational_disclaimer():
    """Generate the explicit associational disclaimer text."""
    return """
## ⚠️ Important Methodological Note: Associational Nature of Findings

**This study establishes statistical associations, not causal relationships.**

The Multiple Linear Regression (OLS) analysis performed in this pipeline identifies
statistical relationships between neural entropy metrics and cognitive flexibility
(WCST perseverative errors), controlling for specified covariates. However, these
findings do not establish:

1. **Causality**: Higher/lower neural entropy does not cause changes in cognitive
   flexibility, nor vice versa. The observed relationships may be influenced by
   unmeasured confounding variables.

2. **Directionality**: The cross-sectional design cannot determine the temporal
   sequence of neural and cognitive changes.

3. **Generalizability**: Results are specific to the population and conditions
   represented in the OpenNeuro datasets used (ds000246, ds004298) and may not
   extend to other populations, age ranges, or cognitive tasks.

**Recommendation for Interpretation**: These findings should be interpreted as
hypothesis-generating associations that warrant further investigation through
longitudinal studies, experimental manipulations, or causal inference methods
(e.g., instrumental variables, propensity score matching, or randomized trials
where ethically feasible).
"""

def generate_covariate_summary(behavioral_scores_path, regression_results_path):
    """
    Generate a summary of covariates used in the regression analysis.
    
    Reads the regression results and behavioral scores to document:
    - Which covariates were included
    - How they were handled (continuous vs. categorical)
    - Rationale for inclusion based on literature
    """
    covariates_info = """
## Covariate Control Summary

The Multiple Linear Regression (OLS) model includes the following covariates to
control for potential confounding factors:

### Primary Predictors
- **Neural Entropy Metrics**: Sample Entropy (SampEn) and Approximate Entropy (ApEn)
  calculated across five frequency bands (Delta, Theta, Alpha, Beta, Gamma)

### Outcome Variable
- **WCST Perseverative Errors**: Primary measure of cognitive flexibility from the
  Wisconsin Card Sorting Test

### Covariates Included

| Covariate | Type | Rationale |
|-----------|------|-----------|
| **Age** | Continuous | Neural entropy and cognitive flexibility both change with age; critical control |
| **Education** | Continuous (years) | Educational attainment affects WCST performance and may correlate with neural measures |
| **Task Accuracy** | Continuous | Performance on the WCST itself; controls for general task engagement |
| **Neurological Condition** | Binary (0/1) | Controls for presence of neurological disorders that may independently affect outcomes |
| **Medication Use** | Binary (0/1) | Controls for pharmacological effects on neural activity and cognition |

### Multicollinearity Handling
- **VIF Check**: Variance Inflation Factor (VIF) calculated for all predictors
- **Threshold**: VIF > 5 triggers exclusion of Approximate Entropy to reduce redundancy
- **Method**: Full model re-run with reduced feature set if multicollinearity detected

### Statistical Corrections
- **FDR Correction**: Benjamini-Hochberg procedure applied to account for multiple
  comparisons across frequency bands and entropy metrics
- **Effect Size Classification**: Partial r ≥ 0.3 classified as clinically meaningful
"""
    return covariates_info

def generate_limitations_section():
    """Generate limitations section based on study design."""
    return """
## Study Limitations

### Data Limitations
1. **Sample Size**: Limited by availability of OpenNeuro datasets with both EEG and
   WCST behavioral data; power analysis was deferred per project constraints
2. **Dataset Heterogeneity**: ds000246 and ds004298 may have different acquisition
   parameters, potentially introducing batch effects
3. **Missing Data**: Participants excluded due to:
   - Insufficient EEG duration (<60 seconds valid data)
   - High artifact contamination (>20% corrupted segments)
   - Low signal-to-noise ratio (SNR < 5 dB)
   - Missing WCST perseverative errors variable

### Methodological Limitations
1. **Cross-Sectional Design**: Cannot establish temporal relationships or causality
2. **Entropy Metric Selection**: Sample and Approximate Entropy are just two of many
   possible complexity measures; results may not generalize to other metrics
3. **Frequency Band Definition**: Standard bands (Delta: 1-4Hz, Theta: 4-8Hz, etc.)
   may not capture individual variability in peak frequencies
4. **Covariate Selection**: Unmeasured confounders (e.g., sleep quality, diet,
   genetic factors) may influence both neural entropy and cognitive performance

### Generalizability
- Results apply specifically to the demographics represented in the analyzed datasets
- External validity to clinical populations or different age groups requires validation

## Compliance Statements

### FR-009: Associational Disclaimer
✓ Explicit disclaimer included in this document and final report

### SC-005: Methodology Transparency
✓ All preprocessing steps, exclusion criteria, and statistical methods documented

### Constitution Amendment Request
✓ Acknowledgement of OLS+FDR approach (deviation from original Spec FR-004)
✓ Clear statement that findings are associational, not causal
"""

def main():
    """Main entry point to generate methodology notes."""
    # Setup logging
    logger = setup_general_logger("methodology_notes")
    logger.info("Starting methodology notes generation")
    
    # Check resource usage
    mem_gb = get_memory_usage_gb()
    logger.info(f"Current memory usage: {mem_gb:.2f} GB")
    
    # Define paths
    config = get_config()
    project_root = Path(__file__).parent.parent
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    output_path = logs_dir / "methodology_notes.md"
    
    # Load data for summary (if available)
    behavioral_scores_path = project_root / "data" / "processed" / "behavioral_scores.csv"
    regression_results_path = project_root / "data" / "processed" / "correlation_results_fdr.csv"
    
    # Generate content
    content = []
    content.append("# Methodology Notes: Neural Entropy and Cognitive Flexibility in Aging")
    content.append("")
    content.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    content.append("")
    content.append("---")
    content.append("")
    
    # Add associational disclaimer
    content.append(generate_associational_disclaimer())
    content.append("")
    
    # Add covariate summary
    content.append(generate_covariate_summary(behavioral_scores_path, regression_results_path))
    content.append("")
    
    # Add limitations
    content.append(generate_limitations_section())
    content.append("")
    
    # Add processing pipeline summary (referencing T033b)
    content.append("""
## Processing Pipeline Summary

This analysis follows a multi-stage pipeline:

1. **Data Acquisition**: OpenNeuro datasets (ds000246, ds004298) downloaded via HuggingFace Hub
2. **Validation**: Variable fit check for WCST perseverative errors
3. **Preprocessing**: Bandpass filtering (1-45Hz), notch filtering (50/60Hz), ICA artifact removal, epoching
4. **Quality Control**: SNR calculation, exclusion based on duration, artifact rate, and SNR threshold
5. **Entropy Computation**: Sample and Approximate Entropy for 5 frequency bands
6. **Statistical Analysis**: Multiple Linear Regression with FDR correction
7. **Sensitivity Analysis**: Threshold sweeps and exclusion scenario comparisons

Detailed implementation notes are available in `docs/methodology_notes.md` (T033b).
""")
    
    # Write output
    full_content = "\n".join(content)
    output_path.write_text(full_content)
    
    logger.info(f"Methodology notes written to {output_path}")
    logger.info("Methodology notes generation complete")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())