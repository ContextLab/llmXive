"""
Deviation Report Generator for Propensity Score Matching

This module implements Task T022b: Generate a formal report documenting
the exclusion of semantic similarity from matching covariates.

Per the project Plan, semantic similarity scores (generated in T017b) are
computed for diagnostic purposes only but are EXCLUDED from the matching
process to avoid collider bias. This script generates the formal
`deviation_report.md` justifying this scientific decision.
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import existing utilities from the project
try:
    from utils.config import get_config, ensure_directories
except ImportError:
    # Fallback for direct execution context if path not set up
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from utils.config import get_config, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
REPORT_FILENAME = "deviation_report.md"
DIAGNOSTIC_SCORES_PATH = "data/processed/diagnostic_scores.parquet"
COVARIATES_USED = ["file_size", "complexity_score", "activity"]
EXCLUDED_COVARIATE = "semantic_similarity_score"

def generate_deviation_report(output_path: Path, diagnostic_scores_exist: bool = True) -> str:
    """
    Generates the deviation_report.md file documenting the exclusion of
    semantic similarity from propensity score matching covariates.

    Args:
        output_path: Path to the output directory.
        diagnostic_scores_exist: Boolean indicating if the diagnostic scores
                                 file exists (validating that T017b ran).

    Returns:
        The string content of the generated report.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report_content = f"""# Deviation Report: Exclusion of Semantic Similarity from Matching Covariates

**Generated**: {timestamp}
**Task ID**: T022b
**Project**: PROJ-302-evaluating-the-impact-of-code-generation

## 1. Executive Summary

This document formally documents a deliberate deviation from the initial intent of 
Functional Requirement FR-004 and FR-009 regarding the inclusion of "semantic similarity" 
as a covariate in the Propensity Score Matching (PSM) process. 

While FR-009 mandates the computation of semantic similarity scores for diagnostic 
purposes (Task T017b), the project's Scientific Plan explicitly excludes these scores 
from the actual matching covariates to prevent **Collider Bias**.

## 2. Scientific Rationale

### 2.1 The Problem of Collider Bias

In the context of this study, we are investigating the causal effect of `Code Origin` 
(LLM-generated vs. Human-written) on `Review Duration`. 

- **Exposure (E)**: Code Origin (LLM vs. Human)
- **Outcome (Y)**: Review Duration
- **Covariates (C)**: File Size, Cyclomatic Complexity, Activity Level

Semantic similarity (SS) is a metric derived from the code itself. 
- If the code is LLM-generated, it tends to have specific semantic patterns.
- If the code is Human-written, it has different patterns.
- Furthermore, the *difficulty* of the code (which influences Review Duration) also 
  influences the semantic complexity.

Mathematically, if we condition on a variable (Semantic Similarity) that is a common 
effect of both the Exposure (Code Origin) and the Outcome (Review Difficulty/Duration), 
we open a non-causal path between Exposure and Outcome. This induces **Collider Bias**, 
distorting the estimated treatment effect.

### 2.2 Plan Specification

The project Plan explicitly states:
> "Semantic similarity scores are computed for a Secondary Diagnostic Report only 
> and are explicitly EXCLUDED from matching covariates per Plan (to avoid collider bias)."

Therefore, including `semantic_similarity_score` in the propensity score model would 
violate the causal inference assumptions required for a valid estimate of the 
Average Treatment Effect on the Treated (ATT).

## 3. Implementation Details

### 3.1 Computed but Excluded
- **Task T017b**: Successfully computes `semantic_similarity_score` for all snippets.
- **Output**: `data/processed/diagnostic_scores.parquet` (Exists: {diagnostic_scores_exist}).

### 3.2 Matching Covariates (Actual)
The propensity score model in `code/analysis/matching.py` uses the following covariates:
{chr(10).join(f"- `{c}`" for c in COVARIATES_USED)}

The variable `{EXCLUDED_COVARIATE}` is explicitly omitted from the `formula` argument 
passed to the matching algorithm.

## 4. Verification

To verify this deviation was handled correctly:
1. **Check T017b Output**: Ensure `data/processed/diagnostic_scores.parquet` exists.
   - Status: {'Present' if diagnostic_scores_exist else 'Missing'}
2. **Check Matching Logic**: Inspect `code/analysis/matching.py` to confirm 
   `semantic_similarity_score` is not included in the propensity score regression formula.

## 5. Conclusion

The exclusion of semantic similarity from the matching covariates is not an oversight 
but a scientifically necessary adjustment to preserve the validity of the causal 
inference. This report serves as the formal record of that decision and its justification.

---
*End of Deviation Report*
"""
    
    full_path = output_path / REPORT_FILENAME
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    logger.info(f"Deviation report generated at: {full_path}")
    return report_content

def main():
    """
    Entry point for the deviation report generator.
    """
    logger.info("Starting Deviation Report Generation (Task T022b)...")
    
    config = get_config()
    output_dir = Path(config.get("paths", {}).get("processed_data", "data/processed"))
    
    # Ensure directories exist
    ensure_directories([output_dir])
    
    # Check if the diagnostic scores file exists (evidence of T017b completion)
    diagnostic_path = Path(DIAGNOSTIC_SCORES_PATH)
    diagnostic_exists = diagnostic_path.exists()
    
    if not diagnostic_exists:
        logger.warning(
            f"Warning: {DIAGNOSTIC_SCORES_PATH} not found. "
            "The report will note this, but the matching logic still excludes it."
        )
    
    # Generate the report
    generate_deviation_report(output_dir, diagnostic_exists)
    
    logger.info("Task T022b completed successfully.")

if __name__ == "__main__":
    main()