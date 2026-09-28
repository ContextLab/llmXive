"""
Secondary Literature Synthesis Fallback (T017d).

This script executes a meta-analysis of real published literature to estimate
the correlation between gut microbiome composition and cognitive flexibility
when individual-level data linkage fails.

Input: data/raw/literature_metadata.json (produced by T040a)
Output: data/processed/meta_analysis_report.json
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import numpy as np
from scipy import stats

# Add project root to path to allow relative imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils import get_data_raw_path, get_data_processed_path, setup_logger

# Configure logging
logger = setup_logger("meta_analysis")

def load_literature_metadata():
    """
    Load the literature metadata extracted by T040a.
    
    Returns:
        list: List of dictionaries containing study metadata.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or malformed.
    """
    input_path = get_data_raw_path("literature_metadata.json")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T040a (code/09_literature_extraction.py) has been executed successfully."
        )
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list) or len(data) == 0:
        raise ValueError(
            f"Input file {input_path} is empty or malformed. "
            "Expected a non-empty list of study dictionaries."
        )
    
    logger.info(f"Loaded {len(data)} studies from {input_path}")
    return data

def calculate_pooled_correlation(studies):
    """
    Calculate pooled correlation coefficient and heterogeneity (I²).
    
    Uses Fisher's Z-transformation for meta-analysis:
    1. Convert r to Fisher's Z
    2. Weight by sample size (approximate variance)
    3. Calculate weighted mean Z
    4. Convert back to r
    5. Calculate I² for heterogeneity
    
    Args:
        studies (list): List of study dictionaries with 'correlation_r', 'n_samples'.
        
    Returns:
        dict: Pooled statistics including pooled_r, pooled_p, I_squared, k_studies, n_total.
    """
    valid_studies = []
    for study in studies:
        r = study.get('correlation_r')
        n = study.get('n_samples')
        if r is not None and n is not None and n > 3:
            valid_studies.append({'r': r, 'n': n})
    
    if not valid_studies:
        raise ValueError("No valid studies with correlation_r and n_samples found.")
    
    k = len(valid_studies)
    n_total = sum(s['n'] for s in valid_studies)
    
    # Fisher's Z transformation
    # Z = 0.5 * ln((1+r)/(1-r))
    # Variance of Z = 1 / (n - 3)
    zs = []
    variances = []
    weights = []
    
    for s in valid_studies:
        r = s['r']
        n = s['n']
        # Clamp r to [-0.999, 0.999] to avoid log(0)
        r_clamped = np.clip(r, -0.999, 0.999)
        z = 0.5 * np.log((1 + r_clamped) / (1 - r_clamped))
        var_z = 1.0 / (n - 3)
        w = 1.0 / var_z
        
        zs.append(z)
        variances.append(var_z)
        weights.append(w)
    
    zs = np.array(zs)
    weights = np.array(weights)
    
    # Weighted mean Z
    pooled_z = np.sum(weights * zs) / np.sum(weights)
    
    # Standard error of pooled Z
    se_pooled_z = np.sqrt(1.0 / np.sum(weights))
    
    # Convert back to r
    pooled_r = (np.exp(2 * pooled_z) - 1) / (np.exp(2 * pooled_z) + 1)
    
    # P-value for pooled r (test against 0)
    # t = z / se, df = sum(n) - 2k approx, or use normal approx for large k
    z_stat = pooled_z / se_pooled_z
    pooled_p = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    
    # Heterogeneity Q
    Q = np.sum(weights * (zs - pooled_z)**2)
    
    # Degrees of freedom
    df = k - 1
    
    # I² statistic: (Q - df) / Q * 100
    if Q > df:
        i_squared = (Q - df) / Q * 100.0
    else:
        i_squared = 0.0
    
    # Clamp I² to [0, 100]
    i_squared = np.clip(i_squared, 0.0, 100.0)
    
    logger.info(f"Pooled r: {pooled_r:.4f}, p-value: {pooled_p:.4f}, I²: {i_squared:.2f}%")
    
    return {
        'pooled_r': float(pooled_r),
        'pooled_p': float(pooled_p),
        'I_squared': float(i_squared),
        'k_studies': k,
        'n_total': n_total,
        'Q_statistic': float(Q),
        'df': df
    }

def generate_meta_analysis_report(studies, stats_result):
    """
    Generate the final meta-analysis report JSON.
    
    Args:
        studies (list): Original list of studies.
        stats_result (dict): Calculated statistics.
        
    Returns:
        dict: Complete report structure.
    """
    # Extract source citations
    citations = []
    for i, study in enumerate(studies):
        citation = {
            'study_id': study.get('study_id', f'study_{i}'),
            'pmid': study.get('pmid', 'N/A'),
            'n_samples': study.get('n_samples', 'N/A'),
            'correlation_r': study.get('correlation_r', 'N/A'),
            'p_value': study.get('p_value', 'N/A'),
            'taxon_name': study.get('taxon_name', 'N/A'),
            'effect_direction': study.get('effect_direction', 'N/A')
        }
        citations.append(citation)
    
    report = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'analysis_type': 'Secondary Literature Synthesis Fallback',
        'description': 'Meta-analysis of real published literature due to data linkage failure.',
        'pooled_r': stats_result['pooled_r'],
        'pooled_p': stats_result['pooled_p'],
        'I_squared': stats_result['I_squared'],
        'k_studies': stats_result['k_studies'],
        'n_total': stats_result['n_total'],
        'Q_statistic': stats_result['Q_statistic'],
        'df': stats_result['df'],
        'source_citations': citations,
        'interpretation': {
            'pooled_r_interpretation': f"Small effect size (r={stats_result['pooled_r']:.3f})" if abs(stats_result['pooled_r']) < 0.3 else 
                                     f"Medium effect size (r={stats_result['pooled_r']:.3f})" if abs(stats_result['pooled_r']) < 0.5 else 
                                     f"Large effect size (r={stats_result['pooled_r']:.3f})",
            'heterogeneity_interpretation': f"Low heterogeneity (I²={stats_result['I_squared']:.1f}%)" if stats_result['I_squared'] < 25 else 
                                          f"Moderate heterogeneity (I²={stats_result['I_squared']:.1f}%)" if stats_result['I_squared'] < 50 else 
                                          f"High heterogeneity (I²={stats_result['I_squared']:.1f}%)"
        },
        'limitations': [
            'Derived from literature extraction, not individual-level data',
            'Potential publication bias not assessed',
            'Heterogeneity in study designs and taxa definitions'
        ]
    }
    
    return report

def main():
    """Main entry point for the meta-analysis script."""
    logger.info("Starting Secondary Literature Synthesis Fallback (T017d)...")
    
    try:
        # 1. Load literature metadata
        studies = load_literature_metadata()
        
        # 2. Calculate pooled statistics
        stats_result = calculate_pooled_correlation(studies)
        
        # 3. Generate report
        report = generate_meta_analysis_report(studies, stats_result)
        
        # 4. Write output
        output_dir = get_data_processed_path()
        output_path = output_dir / "meta_analysis_report.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Meta-analysis report written to: {output_path}")
        logger.info(f"Summary: k={stats_result['k_studies']}, N={stats_result['n_total']}, r={stats_result['pooled_r']:.4f}, p={stats_result['pooled_p']:.4f}, I²={stats_result['I_squared']:.2f}%")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during meta-analysis: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
