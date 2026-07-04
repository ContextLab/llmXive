from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Union
import json
from pathlib import Path
import logging
import statsmodels.api as sm
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class StatisticalModel:
    """Container for a single statistical model result."""
    subfield: str
    formula: str
    beta_ace: float
    se_ace: float
    ci_lower: float
    ci_upper: float
    p_value: float
    corrected_p_value: float
    n_obs: int
    is_associational: bool = True  # FR-010: Explicitly frame as associational

@dataclass
class AnalysisResult:
    """Container for the full analysis results."""
    models: List[StatisticalModel] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    disclaimer: str = "NOTE: All findings reported herein are ASSOCIATIONAL only. No causal inference is made regarding the impact of early-life stress on hippocampal subfield volumes."  # FR-010

def extract_model_results(model: Any, subfield_name: str, p_value_uncorrected: float, corrected_p_value: float) -> StatisticalModel:
    """
    Extracts beta, SE, CI, and p-values from a fitted statsmodels LMM summary.
    FR-010: Sets is_associational=True by default.
    """
    # Extract coefficients table
    # Note: For LMM (MixedLM), the summary object structure varies slightly.
    # We assume 'model' is a fitted MixedLMResults object.
    try:
        params = model.params
        bse = model.bse
        conf_int = model.conf_int()

        # ACE is usually the first fixed effect in our formula
        # Formula: subfield_vol ~ ACE_score + age + sex + scanner_site + (1|family_id)
        # We look for 'ACE_score' specifically to be robust
        ace_key = 'ACE_score'
        if ace_key not in params.index:
            # Fallback if naming varies, though spec says ACE_score
            ace_key = [k for k in params.index if 'ACE' in str(k)][0]

        beta = params[ace_key]
        se = bse[ace_key]
        ci_low = conf_int.loc[ace_key, 0]
        ci_high = conf_int.loc[ace_key, 1]

        return StatisticalModel(
            subfield=subfield_name,
            formula=model.model.formula if hasattr(model.model, 'formula') else "N/A",
            beta_ace=float(beta),
            se_ace=float(se),
            ci_lower=float(ci_low),
            ci_upper=float(ci_high),
            p_value=float(p_value_uncorrected),
            corrected_p_value=float(corrected_p_value),
            n_obs=model.model.nobs,
            is_associational=True  # FR-010
        )
    except Exception as e:
        logger.error(f"Failed to extract results for {subfield_name}: {e}")
        # Return a placeholder with is_associational=True to maintain structure
        return StatisticalModel(
            subfield=subfield_name,
            formula="",
            beta_ace=0.0,
            se_ace=0.0,
            ci_lower=0.0,
            ci_upper=0.0,
            p_value=1.0,
            corrected_p_value=1.0,
            n_obs=0,
            is_associational=True
        )

def apply_bonferroni_correction(p_values: List[float], num_tests: int) -> List[float]:
    """
    Applies Bonferroni correction to a list of p-values.
    Threshold = 0.05 / num_tests.
    """
    if num_tests == 0:
        return p_values
    corrected = [min(p * num_tests, 1.0) for p in p_values]
    return corrected

def extract_results_from_models(models_dict: Dict[str, Any], p_values_uncorrected: Dict[str, float], alpha: float = 0.05) -> AnalysisResult:
    """
    Aggregates results from multiple subfield models.
    FR-010: Ensures the final result object carries the associational disclaimer.
    """
    results = AnalysisResult()
    num_tests = len(models_dict)
    
    # Calculate corrected p-values
    raw_p_vals = list(p_values_uncorrected.values())
    corrected_p_vals = apply_bonferroni_correction(raw_p_vals, num_tests)
    
    # Map corrected p-values back to subfields
    subfield_order = list(models_dict.keys())
    corrected_map = dict(zip(subfield_order, corrected_p_vals))

    for subfield, model in models_dict.items():
        p_uncorr = p_values_uncorrected.get(subfield, 1.0)
        p_corr = corrected_map.get(subfield, 1.0)
        
        stat_model = extract_model_results(model, subfield, p_uncorr, p_corr)
        results.models.append(stat_model)

    # FR-010: Add the explicit associational disclaimer to the metadata
    results.metadata['interpretation_warning'] = (
        "Findings are ASSOCIATIONAL only. Causality cannot be inferred from this observational study."
    )
    
    return results

def save_analysis_results(results: AnalysisResult, output_path: Union[str, Path]) -> None:
    """
    Saves analysis results to JSON and CSV.
    FR-010: The saved JSON will include the 'is_associational' flag and the global disclaimer.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare data for JSON
    data_dict = {
        "metadata": results.metadata,
        "disclaimer": results.disclaimer,  # FR-010
        "models": [asdict(m) for m in results.models]
    }

    # Write JSON
    with open(output_path, 'w') as f:
        json.dump(data_dict, f, indent=2)
    
    # Write CSV Summary
    csv_path = output_path.with_suffix('.csv')
    rows = []
    for m in results.models:
        rows.append({
            "subfield": m.subfield,
            "beta_ace": m.beta_ace,
            "ci_lower": m.ci_lower,
            "ci_upper": m.ci_upper,
            "p_value_uncorrected": m.p_value,
            "p_value_corrected": m.corrected_p_value,
            "n_obs": m.n_obs,
            "is_associational": m.is_associational,  # FR-010
            "disclaimer": results.disclaimer
        })
    
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)
    
    logger.info(f"Results saved to {output_path} and {csv_path}")

def main():
    """
    Entry point for saving results if called directly.
    This task (T029) ensures the structures above enforce FR-010.
    """
    logger.info("Running T029: Ensuring associational framing in results.")
    # The logic is embedded in the classes and functions above.
    # No external data is needed to verify the code structure itself.
    pass

if __name__ == "__main__":
    main()
