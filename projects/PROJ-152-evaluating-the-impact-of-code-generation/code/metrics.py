"""
metrics.py - Compute vulnerability density and statistical metrics for code generation analysis.

Implements:
- V/100LOC calculation
- Mean severity calculation
- FPR-corrected metrics (T023b)
"""
import os
import yaml
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List

import config
from calibration import load_csv, load_findings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_severity_map(severity_map_path: str) -> Dict[str, int]:
    """Load NIST-based severity mapping from YAML file."""
    try:
        with open(severity_map_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Severity map file not found: {severity_map_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing severity map: {e}")
        raise

def map_severity_to_ordinal(severity: str, severity_map: Dict[str, int]) -> int:
    """Map severity string to ordinal rank based on provided map."""
    return severity_map.get(severity, 0)

def calculate_vuln_density(vuln_count: int, line_count: int) -> float:
    """Calculate vulnerability density per 100 lines of code."""
    if line_count == 0:
        return 0.0
    return (vuln_count / line_count) * 100

def calculate_mean_severity(severities: List[int]) -> float:
    """Calculate mean severity from a list of ordinal severities."""
    if not severities:
        return 0.0
    return sum(severities) / len(severities)

def apply_fpr_correction(vuln_count: int, fpr: float) -> int:
    """
    Apply False Positive Rate correction to vulnerability count.
    
    Formula: corrected_count = vuln_count * (1 - fpr)
    Result is rounded to nearest integer.
    """
    if fpr < 0 or fpr > 1:
        logger.warning(f"Invalid FPR value {fpr}, clamping to [0, 1]")
        fpr = max(0, min(1, fpr))
    
    corrected = vuln_count * (1 - fpr)
    return round(corrected)

def compute_fpr_corrected_metrics(
    raw_findings_path: str,
    fpr_stats_path: str,
    output_path: str
) -> None:
    """
    Compute FPR-corrected metrics from raw findings and FPR statistics.
    
    Reads:
    - raw_findings.csv: Contains vulnerability findings with model, prompt_id, severity
    - fpr_stats.csv: Contains FPR per model (from T022c)
    
    Writes:
    - corrected_metrics.csv: Contains corrected vulnerability counts and densities
    
    This file is for sensitivity analysis and reporting only, NOT for primary
    statistical tests (T024/T025).
    """
    logger.info(f"Loading raw findings from {raw_findings_path}")
    raw_findings = load_findings(raw_findings_path)
    
    if raw_findings.empty:
        logger.error("Raw findings file is empty")
        raise ValueError("Raw findings file is empty")
    
    logger.info(f"Loading FPR statistics from {fpr_stats_path}")
    fpr_stats = load_csv(fpr_stats_path)
    
    if fpr_stats.empty:
        logger.error("FPR stats file is empty")
        raise ValueError("FPR stats file is empty")
    
    # Create a dictionary for quick FPR lookup by model
    fpr_dict = {}
    for _, row in fpr_stats.iterrows():
        model = row['model']
        fpr = row['fpr']
        fpr_dict[model] = fpr
    
    logger.info(f"FPR lookup table: {fpr_dict}")
    
    # Process each model's findings
    results = []
    
    for model in raw_findings['model'].unique():
        model_findings = raw_findings[raw_findings['model'] == model]
        
        # Get FPR for this model (default to 0 if not found)
        fpr = fpr_dict.get(model, 0.0)
        logger.info(f"Model: {model}, FPR: {fpr}")
        
        # Count vulnerabilities per prompt
        for prompt_id in model_findings['prompt_id'].unique():
            prompt_findings = model_findings[model_findings['prompt_id'] == prompt_id]
            
            vuln_count = len(prompt_findings)
            severities = [map_severity_to_ordinal(sev, severity_map) 
                         for sev in prompt_findings['severity']]
            mean_severity = calculate_mean_severity(severities)
            
            # Get line count from generated snippets (if available)
            # We'll need to join with snippets data for LOC
            line_count = prompt_findings['line_count'].iloc[0] if 'line_count' in prompt_findings.columns else 0
            
            # Calculate raw metrics
            vuln_density = calculate_vuln_density(vuln_count, line_count)
            
            # Apply FPR correction
            corrected_vuln_count = apply_fpr_correction(vuln_count, fpr)
            corrected_vuln_density = calculate_vuln_density(corrected_vuln_count, line_count)
            
            results.append({
                'model': model,
                'prompt_id': prompt_id,
                'raw_vuln_count': vuln_count,
                'corrected_vuln_count': corrected_vuln_count,
                'fpr': fpr,
                'mean_severity': mean_severity,
                'raw_vuln_density': vuln_density,
                'corrected_vuln_density': corrected_vuln_density,
                'line_count': line_count
            })
    
    # Create DataFrame and save
    results_df = pd.DataFrame(results)
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results_df.to_csv(output_path, index=False)
    logger.info(f"Saved corrected metrics to {output_path}")
    
    # Log summary statistics
    logger.info(f"Total rows processed: {len(results_df)}")
    logger.info(f"Models processed: {results_df['model'].unique().tolist()}")
    
    return results_df

def main():
    """Main entry point for computing FPR-corrected metrics."""
    # Paths
    raw_findings_path = config.DATA_DIR / 'findings' / 'raw_findings.csv'
    fpr_stats_path = config.DATA_DIR / 'calibration' / 'fpr_stats.csv'
    output_path = config.DATA_DIR / 'results' / 'corrected_metrics.csv'
    severity_map_path = config.DATA_DIR / 'mappings' / 'nist_severity_map.yaml'
    
    # Validate inputs exist
    if not raw_findings_path.exists():
        logger.error(f"Raw findings file not found: {raw_findings_path}")
        raise FileNotFoundError(f"Raw findings file not found: {raw_findings_path}")
    
    if not fpr_stats_path.exists():
        logger.error(f"FPR stats file not found: {fpr_stats_path}")
        raise FileNotFoundError(f"FPR stats file not found: {fpr_stats_path}")
    
    # Load severity map
    severity_map = load_severity_map(str(severity_map_path))
    logger.info(f"Loaded severity map: {severity_map}")
    
    # Compute FPR-corrected metrics
    try:
        compute_fpr_corrected_metrics(
            str(raw_findings_path),
            str(fpr_stats_path),
            str(output_path)
        )
        logger.info("FPR-corrected metrics computation completed successfully")
    except Exception as e:
        logger.error(f"Error computing FPR-corrected metrics: {e}")
        raise

if __name__ == '__main__':
    main()