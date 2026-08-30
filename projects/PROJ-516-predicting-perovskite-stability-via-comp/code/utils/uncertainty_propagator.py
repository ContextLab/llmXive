"""
Uncertainty Propagation Module for Perovskite Stability Analysis.

This module implements the calculation of combined standard uncertainty for
thermal decomposition temperature (T_d) measurements based on instrument
precision and reported experimental errors.

Per the Marie Curie review action items, this ensures the analysis represents
a rigorous measurement study rather than simple correlation by explicitly
propagating instrument-specific uncertainties.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any
import math

from .uncertainty_parser import parse_temperature_precision

logger = logging.getLogger(__name__)


def calculate_combined_uncertainty(
    instrument_precision: Optional[float],
    experimental_error: Optional[float] = None
) -> Tuple[float, str]:
    """
    Calculate the combined standard uncertainty for T_d measurements.

    This function combines the instrument precision (systematic uncertainty)
    with any reported experimental error (random uncertainty) using the
    root-sum-square (RSS) method.

    Args:
        instrument_precision: The precision of the thermogrimetric analyzer
            (e.g., ±1°C). If None, defaults to 10°C per T042.
        experimental_error: Any additional reported experimental error
            (e.g., sample-to-sample variation). If None, only instrument
            precision is used.

    Returns:
        Tuple of (combined_uncertainty, source_description) where:
            - combined_uncertainty: The calculated combined standard uncertainty
            - source_description: A string describing the sources used

    Raises:
        ValueError: If instrument_precision is negative
    """
    # Handle default precision (T042 logic: default ±10°C if missing)
    if instrument_precision is None:
        instrument_precision = 10.0
        logger.warning(
            "Instrument precision not specified, using default ±10°C. "
            "Consider updating source metadata with specific TGA model precision."
        )

    if instrument_precision < 0:
        raise ValueError(
            f"Instrument precision cannot be negative: {instrument_precision}"
        )

    # If no experimental error is reported, combined uncertainty equals
    # the instrument precision (Type B evaluation)
    if experimental_error is None:
        combined = instrument_precision
        source_desc = f"Instrument precision only (±{instrument_precision}°C)"
    else:
        if experimental_error < 0:
            raise ValueError(
                f"Experimental error cannot be negative: {experimental_error}"
            )

        # Root-sum-square combination (assuming uncorrelated uncertainties)
        # u_c = sqrt(u_instrument^2 + u_experimental^2)
        combined = math.sqrt(instrument_precision**2 + experimental_error**2)
        source_desc = (
            f"Combined: instrument (±{instrument_precision}°C) + "
            f"experimental (±{experimental_error}°C)"
        )

    return combined, source_desc


def propagate_uncertainty_to_weight(
    combined_uncertainty: float
) -> float:
    """
    Convert combined uncertainty to sample weight for weighted regression.

    In weighted least squares, weights are inversely proportional to the
    variance (σ²). This ensures high-precision measurements contribute
    more to the model fit.

    Args:
        combined_uncertainty: The combined standard uncertainty (σ)

    Returns:
        Sample weight (1/σ²)

    Raises:
        ValueError: If uncertainty is non-positive
    """
    if combined_uncertainty <= 0:
        raise ValueError(
            f"Uncertainty must be positive for weight calculation, got: "
            f"{combined_uncertainty}"
        )

    return 1.0 / (combined_uncertainty ** 2)


def process_uncertainty_batch(
    df_uncertainty_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Process a batch of uncertainty data entries.

    Args:
        df_uncertainty_data: List of dictionaries containing:
            - 'instrument_precision': float or None
            - 'experimental_error': float or None
            - 'source_id': str (optional, for logging)

    Returns:
        List of dictionaries with added:
            - 'combined_uncertainty': float
            - 'uncertainty_source': str
            - 'sample_weight': float
            - 'error': str (if calculation failed)
    """
    results = []

    for idx, entry in enumerate(df_uncertainty_data):
        source_id = entry.get('source_id', f'entry_{idx}')
        result = {'source_id': source_id}

        try:
            inst_prec = entry.get('instrument_precision')
            exp_err = entry.get('experimental_error')

            combined, source_desc = calculate_combined_uncertainty(
                inst_prec, exp_err
            )
            weight = propagate_uncertainty_to_weight(combined)

            result['combined_uncertainty'] = combined
            result['uncertainty_source'] = source_desc
            result['sample_weight'] = weight

        except (ValueError, TypeError) as e:
            result['error'] = str(e)
            result['combined_uncertainty'] = None
            result['sample_weight'] = None

        results.append(result)

    return results


def main():
    """
    Command-line interface for uncertainty propagation testing.

    This function demonstrates the uncertainty propagation logic with
    sample data and outputs the results to the console.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Example data simulating different measurement scenarios
    test_cases = [
        {
            'source_id': 'TGA_001',
            'instrument_precision': 1.0,
            'experimental_error': 2.0
        },
        {
            'source_id': 'TGA_002',
            'instrument_precision': 5.0,
            'experimental_error': None
        },
        {
            'source_id': 'TGA_003',
            'instrument_precision': None,  # Will use default 10°C
            'experimental_error': 3.0
        },
        {
            'source_id': 'TGA_004',
            'instrument_precision': 2.0,
            'experimental_error': 2.0
        }
    ]

    logger.info("Running uncertainty propagation demonstration...")
    logger.info("-" * 60)

    results = process_uncertainty_batch(test_cases)

    for res in results:
        if 'error' in res and res['error']:
            logger.error(f"{res['source_id']}: FAILED - {res['error']}")
        else:
            logger.info(
                f"{res['source_id']}: "
                f"u_c = {res['combined_uncertainty']:.3f}°C, "
                f"weight = {res['sample_weight']:.4f}"
            )
            logger.info(f"  Source: {res['uncertainty_source']}")

    logger.info("-" * 60)
    logger.info("Uncertainty propagation completed.")


if __name__ == '__main__':
    main()