"""
T039: Generate Final Analysis Report
Synthesizes results from model fitting and robustness checks into a single Markdown report.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

from config import ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DOCS_DIR = PROJECT_ROOT / "docs"

def load_json_safe(path: Path) -> dict:
    """Load JSON file safely, returning empty dict if not found."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON {path}: {e}")
        return {}

def load_csv_safe(path: Path) -> pd.DataFrame:
    """Load CSV file safely, returning empty DataFrame if not found."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception as e:
        logger.error(f"Failed to load CSV {path}: {e}")
        return pd.DataFrame()

def format_coefficient(val, stars=True):
    """Format a coefficient with significance stars."""
    if val is None:
        return "N/A"
    try:
        f_val = float(val)
        if not (f_val == f_val):  # NaN check
            return "N/A"
    except (TypeError, ValueError):
        return "N/A"
    
    s_val = f"{f_val:.4f}"
    if not stars:
        return s_val
    
    # Simple significance approximation based on value magnitude if p-value not available here
    # In a real report, we'd pass p-value to determine stars
    return s_val

def generate_executive_summary(main_results: dict, robustness: dict) -> str:
    """Generate the executive summary section."""
    lines = []
    lines.append("## 1. Executive Summary")
    lines.append("")
    
    author_coef = main_results.get('author_count_coefficient')
    p_val = main_results.get('p_value')
    
    if author_coef is not None:
        try:
            coef_val = float(author_coef)
            direction = "positive" if coef_val > 0 else "negative"
            significance = "statistically significant" if p_val and float(p_val) < 0.05 else "not statistically significant"
            lines.append(f"The primary analysis indicates a **{direction}** association between authorship diversity (unique authors) and vulnerability counts.")
            lines.append(f"The coefficient for author count is **{coef_val:.4f}** (p-value: {p_val:.4f if p_val else 'N/A'}), which is {significance}.")
        except (TypeError, ValueError):
            lines.append("The primary model results were inconclusive or failed to converge.")
    else:
        lines.append("The primary model could not be fitted or results were unavailable.")
    
    lines.append("")
    lines.append("This analysis is observational. The results describe associations in the data and do not imply causation.")
    return "\n".join(lines)

def generate_main_table(main_results: dict) -> str:
    """Generate the main model coefficients table."""
    lines = []
    lines.append("## 2. Primary Model Results")
    lines.append("")
    lines.append("| Predictor | Coefficient | Std Error | P-Value (Raw) | 95% CI Lower | 95% CI Upper |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    
    # Extract main model fields
    coef = main_results.get('author_count_coefficient')
    std_err = main_results.get('std_err')
    p_val = main_results.get('p_value')
    ci_lower = main_results.get('ci_95_lower')
    ci_upper = main_results.get('ci_95_upper')
    
    # Helper to format
    def fmt(v):
        if v is None: return "N/A"
        try:
            return f"{float(v):.4f}"
        except: return "N/A"

    lines.append(f"| Author Count | {fmt(coef)} | {fmt(std_err)} | {fmt(p_val)} | {fmt(ci_lower)} | {fmt(ci_upper)} |")
    
    # Add control variables if available in a nested structure or flat
    # Assuming flat structure for controls if they were logged separately, 
    # but typically main_results focuses on the target variable.
    # We will add a note about controls used.
    lines.append("")
    lines.append("**Controls**: Project Age, Primary Language (Categorical), Release Count, log(KLOC) (Free Predictor).")
    
    if main_results.get('high_collinearity_warning'):
        lines.append("")
        lines.append("> **Warning**: High collinearity detected (VIF > 5.0) for one or more predictors. Interpret coefficients with caution.")
    
    if not main_results.get('convergence_status', True):
        lines.append("")
        lines.append("> **Warning**: The model failed to converge. Results may be unreliable.")
        
    return "\n".join(lines)

def generate_robustness_section(robustness_data: dict) -> str:
    """Generate the robustness checks section."""
    lines = []
    lines.append("## 3. Robustness Checks")
    lines.append("")
    
    # Subsamples
    lines.append("### 3.1 Subsample Analysis by Language")
    lines.append("")
    subsamples = robustness_data.get('subsample_results', [])
    if not isinstance(subsamples, list):
        # Try to find it in a different key if structure varies
        subsamples = robustness_data.get('robustness_subsample_pvalues', [])
    
    if subsamples:
        lines.append("| Language | Coefficient | Std Error | P-Value (Raw) | N Rows |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for row in subsamples:
            lang = row.get('language', 'N/A')
            coef = row.get('coefficient')
            std = row.get('std_err')
            p = row.get('p_value_raw')
            n = row.get('n_rows')
            lines.append(f"| {lang} | {fmt(coef)} | {fmt(std)} | {fmt(p)} | {n} |")
    else:
        lines.append("No subsample results available.")
    lines.append("")

    # Entropy
    lines.append("### 3.2 Shannon Entropy Model")
    lines.append("")
    entropy_results = robustness_data.get('entropy_results', robustness_data.get('robustness_entropy_pvalues', []))
    if entropy_results and isinstance(entropy_results, list) and len(entropy_results) > 0:
        row = entropy_results[0]
        lines.append(f"- **Coefficient (Entropy)**: {fmt(row.get('coefficient'))}")
        lines.append(f"- **Coefficient Difference (vs Author Count)**: {fmt(row.get('coefficient_diff'))}")
    else:
        lines.append("Entropy model results not available.")
    lines.append("")

    # Lagged
    lines.append("### 3.3 Lagged Variable Analysis")
    lines.append("")
    lagged_results = robustness_data.get('lagged_results', robustness_data.get('robustness_lagged_results', {}))
    if lagged_results and isinstance(lagged_results, dict):
        lines.append(f"- **Lag Period**: 12 months")
        lines.append(f"- **Author Count Lag Coefficient**: {fmt(lagged_results.get('author_count_lag_coefficient'))}")
        lines.append(f"- **CVE Count Lag Coefficient**: {fmt(lagged_results.get('cve_count_lag_coefficient'))}")
        if lagged_results.get('excluded_repos_count'):
            lines.append(f"- **Repos Excluded due to Data Window**: {lagged_results.get('excluded_repos_count')}")
    else:
        lines.append("Lagged analysis results not available.")
    lines.append("")
    
    return "\n".join(lines)

def generate_limitations(main_results: dict, robustness_data: dict) -> str:
    """Generate the limitations section."""
    lines = []
    lines.append("## 4. Limitations")
    lines.append("")
    lines.append("1. **Observational Nature**: This study uses observational data. The identified associations should not be interpreted as causal relationships without further experimental or quasi-experimental validation.")
    lines.append("2. **Reverse Causality**: While lagged variable analysis was attempted (Section 3.3), the possibility of reverse causality (e.g., security issues influencing contributor churn) cannot be fully ruled out.")
    lines.append("3. **Data Constraints")
    
    # Check for exclusions
    if main_results.get('high_collinearity_warning'):
        lines.append("   - High collinearity between predictors was detected, which may inflate standard errors.")
    
    if robustness_data.get('excluded_subsamples'):
        lines.append(f"   - Some language subsamples were excluded due to insufficient sample size (n < 30).")
    
    if robustness_data.get('lagged_excluded_count', 0) > 0:
        lines.append(f"   - {robustness_data.get('lagged_excluded_count')} repositories were excluded from the lagged analysis because their history fell outside the shallow clone window.")
    
    lines.append("")
    lines.append("4. **Shallow Clone Window**: The git history was limited to `--shallow-since=2015-01-01`. Repositories created before this date or with activity primarily before this date may have incomplete authorship data.")
    
    return "\n".join(lines)

def generate_appendix() -> str:
    """Generate the reproducibility appendix."""
    lines = []
    lines.append("## Appendix: Reproducibility")
    lines.append("")
    lines.append("To reproduce these results, execute the following commands in the project root directory:")
    lines.append("")
    lines.append("```bash")
    lines.append("# 1. Generate Target List")
    lines.append("python code/data/generate_target_list.py")
    lines.append("")
    lines.append("# 2. Download NVD Data")
    lines.append("python code/data/download_nvd.py")
    lines.append("")
    lines.append("# 3. Extract GitHub Metrics")
    lines.append("python code/data/extract_github.py")
    lines.append("")
    lines.append("# 4. Merge Datasets")
    lines.append("python code/data/merge_datasets.py")
    lines.append("")
    lines.append("# 5. Fit Models")
    lines.append("python code/analysis/fit_models.py")
    lines.append("")
    lines.append("# 6. Run Robustness Checks")
    lines.append("python code/analysis/robustness.py")
    lines.append("")
    lines.append("# 7. Generate Final Report (This Task)")
    lines.append("python code/analysis/generate_final_report.py")
    lines.append("```")
    lines.append("")
    lines.append(f"**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return "\n".join(lines)

def main():
    logger.info("Starting Final Report Generation (T039)")
    
    # Ensure output directory exists
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load input files
    main_results_path = DATA_PROCESSED / "model_results_raw.json"
    robustness_path = DATA_PROCESSED / "robustness_results.json"
    metrics_clean_path = DATA_PROCESSED / "repo_metrics_clean.csv"
    
    main_results = load_json_safe(main_results_path)
    robustness_data = load_json_safe(robustness_path)
    metrics_df = load_csv_safe(metrics_clean_path)
    
    if not main_results and not robustness_data:
        logger.error("Critical input files missing. Cannot generate report.")
        return 1
    
    # Build Report Content
    report_parts = []
    
    # Title
    report_parts.append("# Final Analysis Report: Code Authorship Diversity and Software Security")
    report_parts.append("")
    report_parts.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_parts.append("")
    
    # Sections
    report_parts.append(generate_executive_summary(main_results, robustness_data))
    report_parts.append("")
    report_parts.append(generate_main_table(main_results))
    report_parts.append("")
    report_parts.append(generate_robustness_section(robustness_data))
    report_parts.append("")
    report_parts.append(generate_limitations(main_results, robustness_data))
    report_parts.append("")
    report_parts.append(generate_appendix())
    
    # Write Report
    report_content = "\n".join(report_parts)
    output_path = DOCS_DIR / "final_analysis_report.md"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"Report successfully generated at: {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
