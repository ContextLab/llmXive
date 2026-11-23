"""
Generate the final research report (results/report.md).

This script aggregates results from previous analysis steps (T029a, T029b, T025, T032, etc.)
and generates a comprehensive markdown report including:
- Data description
- Methods (Continuous & Cluster)
- Results tables (Continuous & Cluster)
- Sensitivity analysis
- Limitations
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import config for paths
from config import get_config, Config

# Import logging utility
from utils.logging import get_logger, setup_logging

def load_csv_safe(path: Path, logger: logging.Logger) -> Optional[pd.DataFrame]:
    """Safely load a CSV file, returning None if missing or invalid."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return None
    try:
        df = pd.read_csv(path)
        return df
    except Exception as e:
        logger.error(f"Failed to load {path}: {e}")
        return None

def load_json_safe(path: Path, logger: logging.Logger) -> Optional[Dict]:
    """Safely load a JSON file, returning None if missing or invalid."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {path}: {e}")
        return None

def load_yaml_safe(path: Path, logger: logging.Logger) -> Optional[Dict]:
    """Safely load a YAML file (using json for simplicity if pyyaml not strictly needed for structure, but using yaml lib if available)."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return None
    try:
        import yaml
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback if yaml not installed, though requirements.txt should have it
        logger.warning("PyYAML not installed, cannot load YAML report.")
        return None
    except Exception as e:
        logger.error(f"Failed to load {path}: {e}")
        return None

def format_df_as_markdown_table(df: pd.DataFrame, caption: str = "") -> str:
    """Convert a DataFrame to a Markdown table string."""
    if df is None or df.empty:
        return f"\n*Table '{caption}' not available (data missing or empty).*\n"
    
    # Ensure all columns are string for table rendering
    df_display = df.astype(str)
    table_str = df_display.to_markdown(index=False)
    
    md_output = f"\n### {caption}\n\n"
    md_output += table_str
    md_output += "\n"
    return md_output

def generate_data_section(config: Config, logger: logging.Logger) -> str:
    """Generate the Data section of the report."""
    section = "\n## 1. Data\n\n"
    
    # Check for validation report
    val_report_path = config.DATA_DIR / "validation_report.json"
    val_report = load_json_safe(val_report_path, logger)
    
    if val_report:
        section += f"**Dataset Status:** {val_report.get('status', 'Unknown')}\n"
        section += f"**Dataset Name:** {val_report.get('dataset_name', 'Unknown')}\n"
        section += f"**Total Participants:** {val_report.get('total_participants', 'N/A')}\n"
        section += f"**Excluded Participants:** {val_report.get('excluded_count', 0)}\n"
        
        missing_vars = val_report.get('missing_variables', [])
        if missing_vars:
            section += f"**Missing Critical Variables:** {', '.join(missing_vars)}\n"
        else:
            section += "**Critical Variables:** All present.\n"
    else:
        section += "*Validation report not found.*\n"
        
    section += "\n"
    return section

def generate_methods_section(config: Config, logger: logging.Logger) -> str:
    """Generate the Methods section."""
    section = "\n## 2. Methods\n\n"
    
    section += "### 2.1 Primary Analysis (Continuous Predictor)\n"
    section += "The primary analysis utilizes a Linear Mixed-Effects Model (LMM) with detection time as the outcome and the **continuous fixation ratio** (eye-to-mouth fixation time) as the fixed effect. Random intercepts for participants were included.\n\n"
    
    section += "### 2.2 Exploratory Analysis (Cluster Labels)\n"
    section += "An exploratory analysis was conducted using cluster labels derived from k-means clustering (k=2) on fixation metrics. This model is **descriptive only** and not used for primary inference to avoid circularity risks.\n\n"
    
    section += "### 2.3 Sensitivity Analysis\n"
    section += "Sensitivity was assessed by varying the number of clusters (k=2, k=3) and observing the variance in the descriptive model coefficients.\n\n"
    
    section += "### 2.4 Power Analysis\n"
    section += "A priori power analysis was conducted targeting a power of 0.80 at alpha=0.05 for an effect size of d=0.5.\n\n"
    
    return section

def generate_results_section(config: Config, logger: logging.Logger) -> str:
    """Generate the Results section with tables."""
    section = "\n## 3. Results\n\n"
    
    # Primary Analysis Table (T029a)
    # Expected file: results/lmm_continuous.csv
    lmm_cont_path = config.RESULTS_DIR / "lmm_continuous.csv"
    df_cont = load_csv_safe(lmm_cont_path, logger)
    section += format_df_as_markdown_table(df_cont, "Primary Analysis: Continuous Fixation Ratio")
    
    # Exploratory Analysis Table (T029b)
    # Expected file: results/lmm_cluster.csv
    lmm_cluster_path = config.RESULTS_DIR / "lmm_cluster.csv"
    df_cluster = load_csv_safe(lmm_cluster_path, logger)
    section += format_df_as_markdown_table(df_cluster, "Exploratory Analysis: Cluster Labels")
    
    # Permutation Test (T030)
    perm_path = config.RESULTS_DIR / "permutation_test.json"
    perm_data = load_json_safe(perm_path, logger)
    if perm_data:
        section += "\n### Permutation Test Results\n\n"
        section += f"- **Observed Statistic:** {perm_data.get('observed_statistic', 'N/A')}\n"
        section += f"- **Null Distribution Mean:** {perm_data.get('null_mean', 'N/A')}\n"
        section += f"- **P-value:** {perm_data.get('p_value', 'N/A')}\n"
        section += f"- **Iterations:** {perm_data.get('iterations', 'N/A')}\n"
    
    return section

def generate_sensitivity_section(config: Config, logger: logging.Logger) -> str:
    """Generate the Sensitivity Analysis section."""
    section = "\n## 4. Sensitivity Analysis\n\n"
    
    # Sensitivity Report (T026)
    sens_path = config.RESULTS_DIR / "sensitivity_report.yaml"
    sens_data = load_yaml_safe(sens_path, logger)
    
    if sens_data:
        section += "Stability of cluster-based models across k=2 and k=3:\n\n"
        if 'summary' in sens_data:
            section += f"**Summary:** {sens_data['summary']}\n"
        if 'coefficients' in sens_data:
            section += "| k | Coefficient | Standard Error |\n|---|---|---|\n"
            for k, stats in sens_data['coefficients'].items():
                coef = stats.get('coef', 'N/A')
                se = stats.get('se', 'N/A')
                section += f"| {k} | {coef} | {se} |\n"
        if 'variance' in sens_data:
            section += f"\n**Coefficient Variance:** {sens_data['variance']}\n"
    else:
        section += "*Sensitivity report not found.*\n"
        
    return section

def generate_limitations_section(config: Config, logger: logging.Logger) -> str:
    """Generate the Limitations section."""
    section = "\n## 5. Limitations\n\n"
    
    section += "1. **Cluster Stability:** The exploratory cluster-based analysis relies on k-means clustering which may be sensitive to initial conditions and the choice of k. The sensitivity analysis (Section 4) addresses this to some extent.\n"
    section += "2. **Power:** If the sample size is insufficient (power < 0.80 as determined in T032/T033), the ability to detect small effect sizes is limited.\n"
    section += "3. **Data Quality:** The analysis depends on the accuracy of the eye-tracking data and the validity of the ROI fallback (3x3 grid) if specific annotations are missing.\n"
    section += "4. **Generalizability:** Results are specific to the dataset downloaded from HuggingFace and may not generalize to all populations or experimental setups.\n"
    
    return section

def generate_power_summary(config: Config, logger: logging.Logger) -> str:
    """Add a summary of power analysis if available."""
    # We can try to load the power analysis results if they were saved as a specific file
    # Assuming T032 output might be in results/power_analysis.json or similar
    # Since T032 is a script, let's assume it might have printed or saved. 
    # For this report, we will just state the target parameters as per T032.
    
    return "\n### Power Analysis Target\nTarget power: 0.80, Alpha: 0.05, Effect Size (d): 0.5.\n"

def main():
    """Main entry point for generating the final report."""
    # Setup logging
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    setup_logging(log_level=logging.INFO, log_file=log_dir / "generate_report.log")
    logger = get_logger("generate_report")
    
    logger.info("Starting final report generation (T038)...")
    
    config = get_config()
    output_path = config.RESULTS_DIR / "report.md"
    output_path.parent.mkdir(exist_ok=True)
    
    report_content = []
    
    # Header
    report_content.append("# Visual Search Strategies and Emotional Faces: Final Report\n")
    report_content.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Sections
    report_content.append(generate_data_section(config, logger))
    report_content.append(generate_methods_section(config, logger))
    report_content.append(generate_results_section(config, logger))
    report_content.append(generate_sensitivity_section(config, logger))
    report_content.append(generate_power_summary(config, logger))
    report_content.append(generate_limitations_section(config, logger))
    
    # Join and write
    full_report = "\n".join(report_content)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_report)
        logger.info(f"Successfully generated report: {output_path}")
    except Exception as e:
        logger.error(f"Failed to write report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()