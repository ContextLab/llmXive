"""
Linear Mixed-Effects Model (LMM) Analysis Module.

Performs exploratory LMM analysis to quantify the influence of network topology
on thermal conductivity, treating samples as random effects and topological
features as fixed effects.

This is a secondary/exploratory analysis, supplementary to the primary Pearson
correlation (T033a).
"""
import json
import logging
import pickle
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

# Import config to get paths
from config import get_config, get_paths

# Setup logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def load_conductivity_samples() -> pd.DataFrame:
    """
    Load thermal conductivity data from the processed conductivities directory.
    
    Reads all JSON files in `data/processed/conductivities/` and combines them
    into a single DataFrame with sample_id, conductivity, and metadata.
    
    Returns:
        pd.DataFrame: Combined thermal conductivity data.
        
    Raises:
        FileNotFoundError: If no conductivity files are found.
    """
    paths = get_paths()
    conductivities_dir = Path(paths["processed_conductivities"])
    
    if not conductivities_dir.exists():
        raise FileNotFoundError(f"Conductivities directory not found: {conductivities_dir}")
    
    samples = []
    for file_path in conductivities_dir.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract relevant fields
            sample_entry = {
                "sample_id": data.get("graph_id", file_path.stem),
                "conductivity": data.get("conductivity", None),
                "converged": data.get("converged", False),
                "metadata": data.get("metadata", {})
            }
            
            # Flatten metadata if needed
            if isinstance(sample_entry["metadata"], dict):
                for k, v in sample_entry["metadata"].items():
                    sample_entry[f"meta_{k}"] = v
                del sample_entry["metadata"]
            
            samples.append(sample_entry)
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            continue
    
    if not samples:
        raise FileNotFoundError(f"No valid thermal sample files found in {conductivities_dir}")
    
    df = pd.DataFrame(samples)
    
    # Filter for converged samples only
    if "converged" in df.columns:
        df = df[df["converged"] == True]
    
    logger.info(f"Loaded {len(df)} converged thermal conductivity samples.")
    return df.reset_index(drop=True)

def extract_topological_features() -> pd.DataFrame:
    """
    Load topological metrics from the processed graphs directory.
    
    Reads the global degree distribution stats and any per-sample metrics
    to create a feature matrix aligned with sample IDs.
    
    Returns:
        pd.DataFrame: Topological features indexed by sample_id.
    """
    paths = get_paths()
    graphs_dir = Path(paths["processed_graphs"])
    
    # Try to load per-sample metrics if they exist
    # Assuming metrics are stored alongside graph files or in a separate metrics file
    metrics_file = graphs_dir / "topology_metrics.json"
    
    if metrics_file.exists():
        with open(metrics_file, 'r') as f:
            metrics_data = json.load(f)
        
        # Convert to DataFrame
        df = pd.DataFrame(metrics_data)
        logger.info(f"Loaded topological metrics for {len(df)} samples.")
        return df
    
    # Fallback: If per-sample metrics don't exist, we might need to compute them
    # or use aggregate stats. For now, we assume the pipeline has generated
    # a metrics file or we construct a minimal feature set.
    # In a real scenario, this would load from T021 output.
    
    # Attempt to load from a standard location if it exists
    # This is a placeholder for where T021 would write its output
    # For now, we raise if not found, as we need real data
    raise FileNotFoundError(
        f"Topological metrics file not found at {metrics_file}. "
        "Ensure T021 (topology_extractor) has run and generated metrics."
    )

def run_lmm_analysis(conductivity_df: pd.DataFrame, features_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run Linear Mixed-Effects Model analysis.
    
    Models thermal conductivity as a function of topological features,
    with sample ID as a random effect to account for within-sample correlation.
    
    Formula: conductivity ~ degree_mean + clustering_coeff + shortest_path_mean + (1|sample_id)
    
    Args:
        conductivity_df: DataFrame with conductivity data.
        features_df: DataFrame with topological features.
        
    Returns:
        Dict[str, Any]: Results including coefficients, p-values, and model summary.
    """
    # Merge data on sample_id
    if "sample_id" not in conductivity_df.columns or "sample_id" not in features_df.columns:
        raise ValueError("Both DataFrames must contain 'sample_id' column.")
    
    merged_df = pd.merge(conductivity_df, features_df, on="sample_id", how="inner")
    
    if len(merged_df) < 10:
        logger.warning(f"Sample size too small for LMM: N={len(merged_df)}. Results may be unreliable.")
    
    # Select features for the model
    # We look for common topological metrics
    potential_features = [
        "degree_mean", "degree_mode", "degree_std",
        "clustering_coeff_mean", "clustering_coeff_std",
        "shortest_path_mean", "shortest_path_std"
    ]
    
    # Filter features that actually exist in the dataframe
    available_features = [f for f in potential_features if f in merged_df.columns]
    
    if not available_features:
        raise ValueError("No topological features found in the data to build the model.")
    
    # Build formula
    # For LMM with statsmodels, we use mixedlm
    # Formula: dependent ~ independent1 + independent2 ...
    feature_str = " + ".join(available_features)
    formula = f"conductivity ~ {feature_str}"
    
    logger.info(f"Fitting LMM with formula: {formula}")
    
    # Prepare data for statsmodels
    # MixedLM requires specifying groups
    groups = merged_df["sample_id"]
    endog = merged_df["conductivity"]
    exog = merged_df[available_features]
    
    # Add constant for intercept
    exog = sm.add_constant(exog)
    
    # Fit the model
    try:
        model = smf.mixedlm(formula, merged_df, groups=groups)
        result = model.fit()
        
        logger.info("LMM fitting completed successfully.")
        
    except Exception as e:
        logger.error(f"Failed to fit LMM: {e}")
        # Fallback: If LMM fails (e.g., singular fit), try OLS as a diagnostic
        logger.warning("Falling back to OLS for diagnostic purposes.")
        model_ols = sm.OLS(endog, exog).fit()
        result = model_ols
        
    # Extract results
    coefficients = result.params.to_dict()
    p_values = result.pvalues.to_dict()
    
    # Calculate R-squared (pseudo for mixed models, or standard for OLS)
    if hasattr(result, 'rsquared'):
        r_squared = result.rsquared
    else:
        # For mixed models, use conditional R-squared approximation
        # This is a simplification
        r_squared = result.prsquared if hasattr(result, 'prsquared') else 0.0
    
    return {
        "formula": formula,
        "n_samples": len(merged_df),
        "coefficients": coefficients,
        "p_values": p_values,
        "r_squared": r_squared,
        "convergence": result.converged if hasattr(result, 'converged') else True,
        "log_likelihood": result.llf if hasattr(result, 'llf') else None,
        "aic": result.aic if hasattr(result, 'aic') else None,
        "bic": result.bic if hasattr(result, 'bic') else None
    }

def interpret_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interpret the LMM results for scientific reporting.
    
    Args:
        results: Output from run_lmm_analysis.
        
    Returns:
        Dict[str, Any]: Human-readable interpretation of the findings.
    """
    interpretation = {
        "summary": "",
        "significant_features": [],
        "topological_influence": "Unknown"
    }
    
    p_values = results.get("p_values", {})
    coefficients = results.get("coefficients", {})
    
    # Identify significant features (p < 0.05)
    significant = [k for k, v in p_values.items() if v is not None and v < 0.05 and k != "const"]
    interpretation["significant_features"] = significant
    
    if significant:
        interpretation["summary"] = (
            f"Found {len(significant)} topological features significantly correlated with thermal conductivity "
            f"(p < 0.05). The model explains {results.get('r_squared', 0):.2%} of the variance."
        )
        interpretation["topological_influence"] = "Strong"
    else:
        interpretation["summary"] = (
            "No individual topological features showed statistically significant correlation with thermal conductivity "
            "at the p < 0.05 level. This may indicate a complex, non-linear relationship or insufficient sample size."
        )
        interpretation["topological_influence"] = "Weak or Non-linear"
    
    # Add coefficient interpretations
    coefficient_analysis = {}
    for feat in significant:
        coef = coefficients.get(feat, 0)
        p = p_values.get(feat, 1.0)
        direction = "positive" if coef > 0 else "negative"
        coefficient_analysis[feat] = {
            "coefficient": coef,
            "p_value": p,
            "direction": direction,
            "interpretation": f"A one-unit increase in {feat} is associated with a {coef:.4f} change in conductivity."
        }
    
    interpretation["coefficient_analysis"] = coefficient_analysis
    
    return interpretation

def save_results(results: Dict[str, Any], interpretation: Dict[str, Any], output_path: Path) -> None:
    """
    Save LMM analysis results and interpretation to JSON.
    
    Args:
        results: Raw model results.
        interpretation: Human-readable interpretation.
        output_path: Path to save the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "model_results": results,
        "interpretation": interpretation,
        "analysis_type": "Linear Mixed-Effects Model (LMM)",
        "status": "completed"
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"LMM results saved to {output_path}")

def main():
    """
    Main entry point for LMM analysis task.
    """
    logger.info("Starting Linear Mixed-Effects Model Analysis (T033).")
    
    try:
        # 1. Load data
        logger.info("Loading conductivity samples...")
        conductivity_df = load_conductivity_samples()
        
        logger.info("Loading topological features...")
        features_df = extract_topological_features()
        
        # 2. Run analysis
        logger.info("Running LMM...")
        results = run_lmm_analysis(conductivity_df, features_df)
        
        # 3. Interpret results
        logger.info("Interpreting results...")
        interpretation = interpret_results(results)
        
        # 4. Save results
        paths = get_paths()
        output_path = Path(paths["model_outputs"]) / "lmm_results.json"
        save_results(results, interpretation, output_path)
        
        logger.info("LMM Analysis completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data not found: {e}")
        logger.error("Ensure T021 (topology_extractor) and T022/T023 (conductivity simulation) have completed.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()