"""
Preprocessing pipeline for molecular data.
Handles data alignment, interpolation, smoothing, and normalization.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Configure paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PREPROCESSED_DIR = DATA_DIR / "preprocessed"
EXTERNAL_DIR = DATA_DIR / "external"
LOGS_DIR = PROJECT_ROOT / "logs"
RESULTS_DIR = PROJECT_ROOT / "results"

def load_qm9_data(qm9_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load QM9 dataset.

    Args:
        qm9_path: Path to QM9 data file. If None, uses default path.

    Returns:
        DataFrame with QM9 data.
    """
    if qm9_path is None:
        qm9_path = RAW_DIR / "qm9" / "qm9.csv"

    if not qm9_path.exists():
        raise FileNotFoundError(f"QM9 data not found at {qm9_path}")

    logger = logging.getLogger(__name__)
    logger.info(f"Loading QM9 data from {qm9_path}")

    df = pd.read_csv(qm9_path)
    logger.info(f"Loaded {len(df)} QM9 samples")

    return df

def load_ir_spectra_data(ir_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load IR spectra dataset.

    Args:
        ir_path: Path to IR spectra data file. If None, uses default path.

    Returns:
        DataFrame with IR spectra data.
    """
    if ir_path is None:
        ir_path = RAW_DIR / "ir_spectra" / "ir_spectra.csv"

    if not ir_path.exists():
        raise FileNotFoundError(f"IR spectra data not found at {ir_path}")

    logger = logging.getLogger(__name__)
    logger.info(f"Loading IR spectra data from {ir_path}")

    df = pd.read_csv(ir_path)
    logger.info(f"Loaded {len(df)} IR spectra samples")

    return df

def perform_inner_join(
    qm9_df: pd.DataFrame,
    ir_df: pd.DataFrame,
    key: str = "InChIKey"
) -> Tuple[pd.DataFrame, int]:
    """
    Perform inner join on QM9 and IR spectra datasets.

    Args:
        qm9_df: QM9 DataFrame.
        ir_df: IR spectra DataFrame.
        key: Column name to join on.

    Returns:
        Tuple of (joined DataFrame, count of discarded samples).
    """
    logger = logging.getLogger(__name__)

    qm9_count = len(qm9_df)
    ir_count = len(ir_df)

    # Perform inner join
    joined_df = pd.merge(qm9_df, ir_df, on=key, how="inner")
    joined_count = len(joined_df)

    discarded_count = qm9_count + ir_count - joined_count
    logger.info(f"Inner join: {qm9_count} + {ir_count} -> {joined_count} (discarded: {discarded_count})")

    return joined_df, discarded_count

def interpolate_spectra(
    spectra_df: pd.DataFrame,
    wavenumber_range: Tuple[int, int] = (400, 4000),
    wavenumber_step: int = 1,
    spectrum_col: str = "spectrum"
) -> pd.DataFrame:
    """
    Interpolate spectra to a fixed wavenumber grid.

    Args:
        spectra_df: DataFrame with spectra data.
        wavenumber_range: (min, max) wavenumber range.
        wavenumber_step: Step size for wavenumber grid.
        spectrum_col: Column name containing spectrum data.

    Returns:
        DataFrame with interpolated spectra.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Interpolating spectra to grid {wavenumber_range[0]}-{wavenumber_range[1]} cm⁻¹ "
               f"with step {wavenumber_step} cm⁻¹")

    target_wavenumbers = np.arange(
        wavenumber_range[0],
        wavenumber_range[1] + wavenumber_step,
        wavenumber_step
    )

    def interpolate_row(row):
        # Parse spectrum data (assumes format: "wavenumber1:intensity1;wavenumber2:intensity2;...")
        spectrum_str = row[spectrum_col]
        if pd.isna(spectrum_str) or spectrum_str == "":
            return np.full(len(target_wavenumbers), np.nan)

        pairs = spectrum_str.split(";")
        wn_vals = []
        int_vals = []
        for pair in pairs:
            if ":" in pair:
                wn, intensity = pair.split(":")
                wn_vals.append(float(wn))
                int_vals.append(float(intensity))

        wn_vals = np.array(wn_vals)
        int_vals = np.array(int_vals)

        # Interpolate
        if len(wn_vals) > 1:
            interp_int = np.interp(target_wavenumbers, wn_vals, int_vals)
        else:
            interp_int = np.full(len(target_wavenumbers), np.nan)

        return interp_int

    spectra_df["interpolated_spectrum"] = spectra_df.apply(interpolate_row, axis=1)
    logger.info(f"Interpolation complete, grid size: {len(target_wavenumbers)}")

    return spectra_df, target_wavenumbers

def apply_smoothing_and_normalization(
    spectra_df: pd.DataFrame,
    sigma: float = 2.0,
    spectrum_col: str = "interpolated_spectrum"
) -> pd.DataFrame:
    """
    Apply Gaussian smoothing and unit area normalization to spectra.

    Args:
        spectra_df: DataFrame with spectra.
        sigma: Standard deviation for Gaussian smoothing.
        spectrum_col: Column name containing spectrum data.

    Returns:
        DataFrame with smoothed and normalized spectra.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Applying Gaussian smoothing (σ={sigma}) and unit area normalization")

    from scipy.ndimage import gaussian_filter1d

    def smooth_and_normalize(spectrum):
        if np.any(np.isnan(spectrum)):
            return spectrum

        # Apply Gaussian smoothing
        smoothed = gaussian_filter1d(spectrum, sigma=sigma)

        # Unit area normalization
        area = np.trapz(smoothed)
        if area > 0:
            normalized = smoothed / area
        else:
            normalized = smoothed

        return normalized

    spectra_df["processed_spectrum"] = spectra_df[spectrum_col].apply(smooth_and_normalize)
    logger.info("Smoothing and normalization complete")

    return spectra_df

def filter_properties_and_save(
    data_df: pd.DataFrame,
    output_path: Optional[Path] = None,
    required_properties: List[str] = None
) -> Tuple[pd.DataFrame, int]:
    """
    Filter molecules missing required properties and save to .npz.

    Args:
        data_df: DataFrame with molecular data.
        output_path: Path to save the .npz file.
        required_properties: List of required property column names.

    Returns:
        Tuple of (filtered DataFrame, count of discarded samples).
    """
    if required_properties is None:
        required_properties = ["dipole", "polarizability", "homo_lumo_gap"]

    if output_path is None:
        output_path = PREPROCESSED_DIR / "aligned_data.npz"

    logger = logging.getLogger(__name__)

    initial_count = len(data_df)

    # Filter out rows with missing required properties
    mask = data_df[required_properties].notna().all(axis=1)
    filtered_df = data_df[mask]
    discarded_count = initial_count - len(filtered_df)

    logger.info(f"Filtered {discarded_count} samples missing required properties, "
               f"kept {len(filtered_df)} samples")

    # Prepare data for saving
    # Extract spectra and properties
    X = np.array(filtered_df["processed_spectrum"].tolist())
    y = np.array(filtered_df[required_properties].values)

    # Create property indices mapping
    property_indices = {prop: i for i, prop in enumerate(required_properties)}

    # Save to .npz
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        output_path,
        X=X,
        y=y,
        property_indices=property_indices,
        InChIKeys=filtered_df["InChIKey"].values
    )

    logger.info(f"Saved aligned data to {output_path}")

    return filtered_df, discarded_count

def check_dft_metadata(data_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check DFT metadata for consistency.

    Args:
        data_df: DataFrame with molecular data.

    Returns:
        Dictionary with metadata check results.
    """
    logger = logging.getLogger(__name__)
    logger.info("Checking DFT metadata consistency")

    # Placeholder for DFT metadata checks
    # In a real implementation, this would verify DFT method, basis set, etc.

    results = {
        "check_passed": True,
        "message": "DFT metadata check passed (placeholder)"
    }

    return results

def perform_coverage_audit(
    full_qm9_df: pd.DataFrame,
    aligned_df: pd.DataFrame,
    property_columns: List[str] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Dict[str, float]]:
    """
    Perform coverage audit using KS-test to detect selection bias.

    Args:
        full_qm9_df: Full QM9 DataFrame.
        aligned_df: Aligned DataFrame (after join).
        property_columns: List of property column names to audit.
        output_path: Path to save audit results.

    Returns:
        Dictionary with KS-test results for each property.
    """
    if property_columns is None:
        property_columns = ["dipole", "polarizability", "homo_lumo_gap"]

    if output_path is None:
        output_path = RESULTS_DIR / "coverage_audit.json"

    logger = logging.getLogger(__name__)
    logger.info("Performing coverage audit (KS-test)")

    results = {}

    for prop in property_columns:
        if prop not in full_qm9_df.columns or prop not in aligned_df.columns:
            logger.warning(f"Property {prop} not found in both datasets, skipping")
            continue

        full_values = full_qm9_df[prop].dropna().values
        aligned_values = aligned_df[prop].dropna().values

        if len(full_values) == 0 or len(aligned_values) == 0:
            logger.warning(f"No data for property {prop}, skipping")
            continue

        # KS-test
        statistic, p_value = stats.ks_2samp(full_values, aligned_values)

        results[prop] = {
            "statistic": float(statistic),
            "p_value": float(p_value),
            "bias_detected": p_value < 0.05
        }

        logger.info(f"{prop}: KS-statistic={statistic:.4f}, p-value={p_value:.4f}, "
                   f"bias={'DETECTED' if p_value < 0.05 else 'not detected'}")

    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Coverage audit results saved to {output_path}")

    return results

def main():
    """
    Main entry point for the preprocessing script.
    """
    # Set up logging
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOGS_DIR / "preprocessing.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting preprocessing pipeline")

    try:
        # Load data
        qm9_df = load_qm9_data()
        ir_df = load_ir_spectra_data()

        # Perform inner join
        joined_df, discarded_count = perform_inner_join(qm9_df, ir_df)

        # Interpolate spectra
        joined_df, wavenumbers = interpolate_spectra(joined_df)

        # Apply smoothing and normalization
        joined_df = apply_smoothing_and_normalization(joined_df)

        # Filter and save
        filtered_df, filter_count = filter_properties_and_save(joined_df)

        logger.info("Preprocessing pipeline completed successfully")

    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
