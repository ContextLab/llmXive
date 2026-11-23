"""
Heterogeneity analysis module for meta-analysis.
Calculates I-squared (I²) statistic to quantify heterogeneity across studies.
"""

import json
import math
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from utils.config import get_project_root

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_json(file_path: Path) -> Dict[str, Any]:
    """Load JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for {file_path}: {e}")
        raise


def save_json(data: Dict[str, Any], file_path: Path) -> None:
    """Save data to JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Results saved to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save results to {file_path}: {e}")
        raise


def load_effect_sizes_and_se(meta_results_path: Path) -> Tuple[List[float], List[float]]:
    """
    Load effect sizes (r) and standard errors from meta-analysis results.
    
    Args:
        meta_results_path: Path to meta_results.json
        
    Returns:
        Tuple of (effect_sizes, standard_errors)
    """
    data = load_json(meta_results_path)
    
    # Extract effect sizes and SEs from the studies list
    if 'studies' not in data:
        logger.error("Meta results file does not contain 'studies' key")
        raise ValueError("Meta results file missing 'studies' key")
    
    effect_sizes = []
    standard_errors = []
    
    for study in data['studies']:
        if 'r' in study and 'se' in study:
            effect_sizes.append(float(study['r']))
            standard_errors.append(float(study['se']))
        else:
            logger.warning(f"Skipping study without r or se: {study}")
    
    if len(effect_sizes) == 0:
        logger.error("No valid effect sizes found in meta results")
        raise ValueError("No valid effect sizes found")
        
    return effect_sizes, standard_errors


def load_study_count_from_json(count_path: Path) -> int:
    """Load study count from study_count.json."""
    data = load_json(count_path)
    return int(data.get('N', 0))


def calculate_i_squared(effect_sizes: List[float], standard_errors: List[float]) -> float:
    """
    Calculate I-squared (I²) heterogeneity statistic.
    
    I² = 100% * (Q - df) / Q
    where Q is Cochran's Q statistic and df = k - 1
    
    Args:
        effect_sizes: List of effect sizes (r values)
        standard_errors: List of standard errors
        
    Returns:
        I-squared value as a percentage (0-100)
    """
    k = len(effect_sizes)
    
    if k < 2:
        logger.warning("Less than 2 studies. Cannot calculate I². Returning 0.")
        return 0.0
    
    # Calculate weighted mean effect size
    weights = [1.0 / (se ** 2) for se in standard_errors]
    weighted_sum = sum(w * r for w, r in zip(weights, effect_sizes))
    weight_sum = sum(weights)
    
    if weight_sum == 0:
        logger.error("Sum of weights is zero. Cannot calculate I².")
        raise ValueError("Sum of weights is zero")
    
    mean_effect = weighted_sum / weight_sum
    
    # Calculate Cochran's Q
    q_statistic = sum(w * ((r - mean_effect) ** 2) for w, r in zip(weights, effect_sizes))
    
    # Degrees of freedom
    df = k - 1
    
    # Calculate I²
    if q_statistic <= df:
        # No heterogeneity detected
        i_squared = 0.0
    else:
        i_squared = 100.0 * (q_statistic - df) / q_statistic
    
    # Ensure I² is within [0, 100]
    i_squared = max(0.0, min(100.0, i_squared))
    
    return i_squared


def get_heterogeneity_interpretation(i_squared: float) -> str:
    """
    Interpret I-squared value according to standard guidelines.
    
    Guidelines (Higgins et al., 2003):
    - 0-25%: Low heterogeneity
    - 25-50%: Moderate heterogeneity
    - 50-75%: Substantial heterogeneity
    - 75-100%: Considerable heterogeneity
    
    Args:
        i_squared: I-squared value (0-100)
        
    Returns:
        Interpretation string
    """
    if i_squared <= 25.0:
        return "Low heterogeneity"
    elif i_squared <= 50.0:
        return "Moderate heterogeneity"
    elif i_squared <= 75.0:
        return "Substantial heterogeneity"
    else:
        return "Considerable heterogeneity"


def update_output_json(output_path: Path, data: Dict[str, Any]) -> None:
    """Update output JSON file with new data."""
    try:
        if output_path.exists():
          existing = load_json(output_path)
          existing.update(data)
          data = existing
    except FileNotFoundError:
        pass  # File doesn't exist yet, use new data
        
    save_json(data, output_path)


def run_heterogeneity_analysis(
    gate_result_path: Path,
    meta_results_path: Path,
    output_path: Path,
    study_count_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run heterogeneity analysis.
    
    Args:
        gate_result_path: Path to gate_result.json
        meta_results_path: Path to meta_results.json
        output_path: Path to write heterogeneity_results.json
        study_count_path: Optional path to study_count.json for N value
        
    Returns:
        Dictionary containing heterogeneity results
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check gate result
    try:
        gate_result = load_json(gate_result_path)
        status = gate_result.get('status', '')
        
        if status == 'narrative_required':
            logger.info("Skipping heterogeneity analysis: Narrative mode active")
            result = {
                "skipped": True,
                "reason": "Narrative mode active",
                "status": "skipped"
            }
            save_json(result, output_path)
            return result
            
    except FileNotFoundError:
        logger.warning(f"Gate result file not found: {gate_result_path}. "
                     "Proceeding with heterogeneity analysis.")
    except Exception as e:
        logger.warning(f"Error reading gate result: {e}. Proceeding with analysis.")
    
    # Check meta results
    if not meta_results_path.exists():
        logger.error(f"Meta results file not found: {meta_results_path}")
        result = {
            "skipped": True,
            "reason": "Meta results file not found",
            "status": "skipped"
        }
        save_json(result, output_path)
        return result
    
    try:
        # Load effect sizes and standard errors
        effect_sizes, standard_errors = load_effect_sizes_and_se(meta_results_path)
        
        # Get study count if available
        n_studies = len(effect_sizes)
        if study_count_path and study_count_path.exists():
            try:
                n_studies = load_study_count_from_json(study_count_path)
            except Exception as e:
                logger.warning(f"Could not load study count: {e}")
        
        # Calculate I²
        i_squared = calculate_i_squared(effect_sizes, standard_errors)
        interpretation = get_heterogeneity_interpretation(i_squared)
        
        # Calculate Q statistic and p-value (approximate)
        weights = [1.0 / (se ** 2) for se in standard_errors]
        weighted_sum = sum(w * r for w, r in zip(weights, effect_sizes))
        weight_sum = sum(weights)
        mean_effect = weighted_sum / weight_sum
        q_statistic = sum(w * ((r - mean_effect) ** 2) for w, r in zip(weights, effect_sizes))
        df = len(effect_sizes) - 1
        
        # Approximate p-value for Q statistic using chi-square distribution
        # Using scipy if available, otherwise just report Q
        try:
            from scipy.stats import chi2
            p_value = 1 - chi2.cdf(q_statistic, df)
        except ImportError:
            logger.warning("scipy not available. Skipping p-value calculation.")
            p_value = None
        
        result = {
            "skipped": False,
            "status": "completed",
            "n_studies": n_studies,
            "i_squared": round(i_squared, 2),
            "i_squared_interpretation": interpretation,
            "q_statistic": round(q_statistic, 4) if q_statistic else None,
            "degrees_of_freedom": df,
            "p_value": round(p_value, 4) if p_value is not None else None,
            "heterogeneity_level": "low" if i_squared <= 25 else 
                                  "moderate" if i_squared <= 50 else 
                                  "substantial" if i_squared <= 75 else "considerable"
        }
        
        logger.info(f"I² = {i_squared:.2f}% ({interpretation})")
        logger.info(f"Q = {q_statistic:.4f}, df = {df}")
        if p_value:
            logger.info(f"p-value = {p_value:.4f}")
            
        save_json(result, output_path)
        return result
        
    except Exception as e:
        logger.error(f"Error during heterogeneity analysis: {e}")
        result = {
            "skipped": True,
            "reason": f"Analysis error: {str(e)}",
            "status": "error"
        }
        save_json(result, output_path)
        return result


def main():
    """Main entry point for heterogeneity analysis."""
    project_root = get_project_root()
    
    gate_result_path = project_root / "data" / "derived" / "gate_result.json"
    meta_results_path = project_root / "data" / "derived" / "meta_results.json"
    study_count_path = project_root / "data" / "processed" / "study_count.json"
    output_path = project_root / "data" / "derived" / "heterogeneity_results.json"
    
    logger.info("Starting heterogeneity analysis...")
    logger.info(f"Gate result: {gate_result_path}")
    logger.info(f"Meta results: {meta_results_path}")
    logger.info(f"Output: {output_path}")
    
    result = run_heterogeneity_analysis(
        gate_result_path=gate_result_path,
        meta_results_path=meta_results_path,
        output_path=output_path,
        study_count_path=study_count_path
    )
    
    logger.info("Heterogeneity analysis completed.")
    return result


if __name__ == "__main__":
    main()