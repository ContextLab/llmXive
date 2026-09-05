import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import setup_logging, get_logger
from theory.theory_comparison import load_regression_results, load_theoretical_distributions
from theory.scaling_laws import load_theoretical_laws

# Configure logging
logger = setup_logging("generate_results", level=logging.INFO)

# Paths
DATA_DIR = project_root / "data"
PROCESSED_DIR = DATA_DIR / "processed"
PAPER_DIR = project_root / "paper"

GAP_LOCATIONS_PATH = PROCESSED_DIR / "gap_locations.csv"
REGRESSION_RESULTS_PATH = PROCESSED_DIR / "regression_results.json"
KDE_VALIDATION_PATH = PROCESSED_DIR / "kde_validation.json"
THEORY_RESULTS_PATH = PROCESSED_DIR / "theory_comparison_results.json"
RESULTS_MD_PATH = PAPER_DIR / "results.md"

def load_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON file safely, returning None if file doesn't exist."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {path}: {e}")
        return None

def load_regression_results_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Load regression results from JSON file."""
    return load_json_safe(path)

def load_kde_validation(path: Path) -> Optional[Dict[str, Any]]:
    """Load KDE validation results."""
    return load_json_safe(path)

def determine_favored_theory(
    slope: float,
    slope_std: float,
    photoevaporation_mean: float,
    photoevaporation_std: float,
    core_powered_mean: float,
    core_powered_std: float,
    p_value_photo: float,
    p_value_core: float,
    alpha: float = 0.025
) -> Tuple[str, str]:
    """
    Determine which theory is favored based on statistical consistency.
    
    Returns:
        Tuple of (favored_theory, reasoning)
    """
    # Check statistical consistency (p-value > alpha means consistent)
    photo_consistent = p_value_photo > alpha
    core_consistent = p_value_core > alpha

    reasoning_parts = []
    
    # Calculate z-scores for observed slope vs theoretical distributions
    z_photo = abs(slope - photoevaporation_mean) / photoevaporation_std
    z_core = abs(slope - core_powered_mean) / core_powered_std

    reasoning_parts.append(f"Observed slope: {slope:.4f} ± {slope_std:.4f}")
    reasoning_parts.append(f"Photoevaporation (Owen & Wu): {photoevaporation_mean:.2f} ± {photoevaporation_std:.2f}, z-score: {z_photo:.2f}, p-value: {p_value_photo:.4f}")
    reasoning_parts.append(f"Core-powered mass loss (Ginzburg et al.): {core_powered_mean:.2f} ± {core_powered_std:.2f}, z-score: {z_core:.2f}, p-value: {p_value_core:.4f}")
    reasoning_parts.append(f"Significance level (Bonferroni corrected): α = {alpha}")

    if photo_consistent and core_consistent:
        # Both consistent - choose the one with higher p-value (less rejected)
        if p_value_photo > p_value_core:
            favored = "Photoevaporation (Owen & Wu)"
            reasoning_parts.append("Both theories are statistically consistent with the data.")
            reasoning_parts.append("Photoevaporation is slightly favored due to a higher p-value (better fit).")
        else:
            favored = "Core-powered mass loss (Ginzburg et al.)"
            reasoning_parts.append("Both theories are statistically consistent with the data.")
            reasoning_parts.append("Core-powered mass loss is slightly favored due to a higher p-value (better fit).")
    elif photo_consistent:
        favored = "Photoevaporation (Owen & Wu)"
        reasoning_parts.append("Only the Photoevaporation theory is statistically consistent with the data.")
        reasoning_parts.append("The Core-powered mass loss hypothesis is rejected (p-value < α).")
    elif core_consistent:
        favored = "Core-powered mass loss (Ginzburg et al.)"
        reasoning_parts.append("Only the Core-powered mass loss theory is statistically consistent with the data.")
        reasoning_parts.append("The Photoevaporation hypothesis is rejected (p-value < α).")
    else:
        favored = "Neither"
        reasoning_parts.append("Neither theory is statistically consistent with the observed slope.")
        reasoning_parts.append("Both hypotheses are rejected at the α = 0.025 significance level.")
        reasoning_parts.append("This may indicate the need for revised theoretical models or additional systematic corrections.")

    return favored, "\n".join(reasoning_parts)

def generate_results_markdown(
    regression_results: Dict[str, Any],
    kde_validation: Dict[str, Any],
    theory_results: Dict[str, Any],
    output_path: Path
) -> None:
    """Generate the results.md file with aggregated findings."""
    
    # Extract slope and uncertainty
    slope = regression_results.get('slope', 0.0)
    slope_std = regression_results.get('slope_std', 0.0)
    
    # Extract p-values
    p_value_photo = theory_results.get('p_value_photoevaporation', 1.0)
    p_value_core = theory_results.get('p_value_core_powered', 1.0)
    
    # Load theoretical distributions for reference
    theoretical_laws = load_theoretical_laws()
    photoevaporation_mean = theoretical_laws.get('photoevaporation', {}).get('mean', -0.11)
    photoevaporation_std = theoretical_laws.get('photoevaporation', {}).get('std', 0.02)
    core_powered_mean = theoretical_laws.get('core_powered', {}).get('mean', -0.15)
    core_powered_std = theoretical_laws.get('core_powered', {}).get('std', 0.03)
    
    # Determine favored theory
    favored_theory, reasoning = determine_favored_theory(
        slope, slope_std,
        photoevaporation_mean, photoevaporation_std,
        core_powered_mean, core_powered_std,
        p_value_photo, p_value_core
    )
    
    # Extract KDE validation result
    kde_passed = kde_validation.get('validation_passed', False) if kde_validation else False
    kde_gap = kde_validation.get('kde_gap_location', None) if kde_validation else None
    gmm_gap = kde_validation.get('gmm_gap_location', None) if kde_validation else None
    
    # Build markdown content
    md_content = f"""# Results: Orbital Period Dependence of the Exoplanet Radius Gap

## Summary

This analysis investigates the orbital period dependence of the radius gap in exoplanet populations, comparing observed scaling relationships against two leading theoretical models: Photoevaporation (Owen & Wu) and Core-powered mass loss (Ginzburg et al., 2018).

## Key Findings

### Measured Scaling Slope

The Errors-in-Variables (EIV) regression of gap radius versus log(period) yields:

- **Slope**: {slope:.4f} ± {slope_std:.4f}

This slope quantifies how the location of the radius gap shifts with orbital period.

### Theoretical Comparison

We compare the measured slope against two theoretical predictions:

| Theory | Predicted Slope | Observed Consistency (p-value) |
|--------|----------------|-------------------------------|
| Photoevaporation (Owen & Wu) | {photoevaporation_mean:.2f} ± {photoevaporation_std:.2f} | p = {p_value_photo:.4f} |
| Core-powered Mass Loss (Ginzburg et al.) | {core_powered_mean:.2f} ± {core_powered_std:.2f} | p = {p_value_core:.4f} |

**Significance Level**: α = 0.025 (Bonferroni corrected for two tests)

### Statistical Conclusion

{reasoning}

**Favored Theory**: **{favored_theory}**

### KDE vs GMM Validation

The non-parametric KDE validation was used to cross-check the parametric GMM gap location estimates:

- **KDE Gap Location**: {kde_gap:.4f} (if available, else "N/A")
- **GMM Gap Location**: {gmm_gap:.4f} (if available, else "N/A")
- **Validation Passed**: {kde_passed}

{"The KDE-derived gap location falls within the GMM confidence interval, supporting the robustness of the GMM estimates." if kde_passed else "The KDE-derived gap location does not fall within the GMM confidence interval. This discrepancy may indicate model misspecification or the presence of non-Gaussian features in the radius distribution."}

## Methodology

1. **Data Ingestion**: Kepler DR25 and KIC catalogs were merged and filtered for high-precision measurements (radius uncertainty < 20%, period uncertainty < 1%).
2. **Binning**: Planets were binned by orbital period using log-spaced bins, with small bins merged to ensure ≥30 planets per bin.
3. **Gap Estimation**: A two-component Gaussian Mixture Model (GMM) was fit to each bin's radius distribution, with bootstrap resampling for uncertainty quantification.
4. **Regression**: An Errors-in-Variables (EIV) regression was performed on the gap locations versus log(period), incorporating completeness corrections.
5. **Theory Comparison**: Monte Carlo simulation propagated full uncertainty distributions to compute overlap areas and p-values for each theoretical model.

## Limitations

- The analysis is limited to Kepler DR25 data and may not generalize to other surveys.
- Systematic uncertainties in stellar parameters could affect gap location estimates.
- The GMM assumes a bimodal distribution; bins with unimodal distributions were flagged as "unresolved".

## Conclusion

{favored_theory} is favored based on statistical consistency with the observed scaling slope. {"However, the discrepancy between KDE and GMM estimates warrants further investigation." if not kde_passed else "The agreement between KDE and GMM estimates strengthens confidence in the results."}

Future work should explore:
- Incorporating additional survey data (e.g., TESS, PLATO)
- Refining stellar parameter estimates to reduce systematic errors
- Testing alternative parametric models for the radius distribution

---
*Generated by the llmXive automated science pipeline*
"""

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write markdown file
    with open(output_path, 'w') as f:
        f.write(md_content)
    
    logger.info(f"Results written to {output_path}")

def main():
    """Main entry point for generating results.md."""
    logger.info("Starting results aggregation...")
    
    # Load required data files
    regression_results = load_regression_results_safe(REGRESSION_RESULTS_PATH)
    kde_validation = load_kde_validation(KDE_VALIDATION_PATH)
    theory_results = load_json_safe(THEORY_RESULTS_PATH)
    
    # Check for missing dependencies
    missing_files = []
    if regression_results is None:
        missing_files.append(str(REGRESSION_RESULTS_PATH))
    if kde_validation is None:
        missing_files.append(str(KDE_VALIDATION_PATH))
    if theory_results is None:
        missing_files.append(str(THEORY_RESULTS_PATH))
    
    if missing_files:
        error_msg = f"Missing required input files: {', '.join(missing_files)}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    # Generate results markdown
    generate_results_markdown(
        regression_results,
        kde_validation,
        theory_results,
        RESULTS_MD_PATH
    )
    
    logger.info("Results aggregation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())