"""
Interpretation logic for the analysis pipeline.
Determines whether results should be framed as 'Empirical Association' or 'Simulated Causal Effect'
based on the data source type.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from data.config import get_config

logger = logging.getLogger(__name__)


def determine_interpretation_label(data_source_type: str) -> str:
    """
    Determines the appropriate interpretation label based on the data source.

    Args:
        data_source_type: The type of data source used. Expected values:
                          'real' for real-world data,
                          'synthetic' for simulated data.

    Returns:
        str: 'Empirical Association' if data_source_type is 'real',
             'Simulated Causal Effect' if data_source_type is 'synthetic'.
             Raises ValueError for unknown types.

    Raises:
        ValueError: If data_source_type is not recognized.
    """
    if not isinstance(data_source_type, str):
        raise TypeError(f"data_source_type must be a string, got {type(data_source_type)}")

    data_source_type = data_source_type.strip().lower()

    if data_source_type == 'real':
        return "Empirical Association"
    elif data_source_type == 'synthetic':
        return "Simulated Causal Effect"
    else:
        raise ValueError(
            f"Unknown data_source_type: '{data_source_type}'. "
            "Expected 'real' or 'synthetic'. "
            "This flag is set by the data loader (T011) based on data availability."
        )


def generate_interpretation_summary(
    results: Dict[str, Any],
    data_source_type: str,
    model_diagnostics: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generates a summary dictionary containing the interpretation label and context.

    Args:
        results: Dictionary containing regression coefficients and model results.
        data_source_type: 'real' or 'synthetic'.
        model_diagnostics: Optional dictionary containing VIF, p-values, etc.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - 'interpretation_label': The determined label.
            - 'data_source_type': The input data source type.
            - 'context_note': A human-readable explanation of the framing.
            - 'results_summary': A subset of key results (e.g., main effect, interaction).
    """
    label = determine_interpretation_label(data_source_type)

    if label == "Empirical Association":
        context = (
            "Results are framed as an empirical association because the analysis "
            "used real-world observational data. Causal claims are not supported "
            "without randomization, though covariates (pre_self_esteem) were controlled."
        )
    else:
        context = (
            "Results are framed as a simulated causal effect because the analysis "
            "used synthetic data generated with known ground-truth parameters. "
            "The 'effect' represents the recovery of the programmed interaction term."
        )

    summary = {
        "interpretation_label": label,
        "data_source_type": data_source_type,
        "context_note": context,
        "results_summary": {
            "interaction_coefficient": results.get("interaction_coefficient"),
            "interaction_p_value": results.get("interaction_p_value"),
            "main_effect_coefficient": results.get("main_effect_coefficient"),
            "main_effect_p_value": results.get("main_effect_p_value")
        }
    }

    if model_diagnostics:
        summary["model_diagnostics_summary"] = {
            "vif_max": model_diagnostics.get("max_vif"),
            "normality_p_value": model_diagnostics.get("shapiro_p_value"),
            "homoscedasticity_p_value": model_diagnostics.get("breusch_pagan_p_value")
        }

    logger.info(f"Generated interpretation summary: {label}")
    return summary


def run_interpretation(
    results_path: Path,
    diagnostics_path: Path,
    output_path: Path,
    data_source_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main entry point to load results, determine interpretation, and save the summary.

    Args:
        results_path: Path to the CSV file containing regression coefficients.
        diagnostics_path: Path to the JSON file containing model diagnostics.
        output_path: Path where the interpretation summary JSON will be saved.
        data_source_type: Optional override for data source type. If None, it attempts
                          to infer from the config or defaults to 'synthetic' if
                          a specific flag isn't found (requires explicit config check).

    Returns:
        Dict[str, Any]: The generated interpretation summary.

    Raises:
        FileNotFoundError: If results or diagnostics files are missing.
        ValueError: If data_source_type cannot be determined.
    """
    logger.info(f"Running interpretation logic for: {results_path}")

    # Determine data source type
    if data_source_type is None:
        try:
            config = get_config()
            # The config should have been set by the loader (T011)
            data_source_type = getattr(config, 'data_source_type', None)
            if data_source_type is None:
                # Fallback: check if files exist in 'data/raw' with specific naming
                # or rely on the fact that if we are here, the loader ran.
                # If config is missing, we must fail loudly per Constitution Principle.
                raise ValueError(
                    "data_source_type is not set in config and not provided as argument. "
                    "The loader (T011) must set this flag."
                )
        except Exception as e:
            raise ValueError(f"Failed to determine data_source_type from config: {e}")

    # Load results (simplified loading for this function, assuming CSV structure)
    import pandas as pd
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")
    
    results_df = pd.read_csv(results_path)
    
    # Extract key values (assuming standard column names from T018/T021)
    # We expect a single row or specific columns.
    interaction_coef = results_df[results_df['term'] == 'interaction'][['coef']].iloc[0, 0] if 'term' in results_df.columns else results_df.get('interaction_coefficient', 0)
    interaction_p = results_df[results_df['term'] == 'interaction'][['pvalue']].iloc[0, 0] if 'term' in results_df.columns else results_df.get('interaction_p_value', 1.0)
    
    # If the CSV structure is flat (one row), adjust accordingly
    if results_df.shape[0] == 1:
        row = results_df.iloc[0]
        interaction_coef = row.get('interaction_coefficient', interaction_coef)
        interaction_p = row.get('interaction_p_value', interaction_p)
        
    # Load diagnostics
    import json
    diagnostics = {}
    if diagnostics_path.exists():
        with open(diagnostics_path, 'r') as f:
            diagnostics = json.load(f)
    else:
        logger.warning(f"Diagnostics file not found: {diagnostics_path}. Proceeding without diagnostics.")

    # Prepare results dict for the summary generator
    results_dict = {
        "interaction_coefficient": interaction_coef,
        "interaction_p_value": interaction_p,
        "main_effect_coefficient": results_df.get('main_effect_coefficient', 0) if hasattr(results_df, 'get') else 0,
        "main_effect_p_value": results_df.get('main_effect_p_value', 0) if hasattr(results_df, 'get') else 0
    }
    
    # Try to get main effect from CSV if available
    if 'term' in results_df.columns:
        main_effect_row = results_df[results_df['term'] == 'avatar_condition']
        if not main_effect_row.empty:
            results_dict["main_effect_coefficient"] = main_effect_row['coef'].iloc[0]
            results_dict["main_effect_p_value"] = main_effect_row['pvalue'].iloc[0]

    # Generate summary
    summary = generate_interpretation_summary(results_dict, data_source_type, diagnostics)

    # Save to output path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Interpretation summary saved to {output_path}")
    return summary