"""
Data preprocessing module.
Implements loading of QM9 and IR spectra data, alignment, interpolation onto a uniform
wavenumber grid, Gaussian smoothing, unit‑area normalization, conversion of target
properties to the required units, filtering of molecules with missing targets, and
saving of the final dataset as an NPZ file.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
WAVENUMBER_RANGE = (400, 4000)          # cm⁻¹
WAVENUMBER_STEP = 1                    # cm⁻¹
GRID_POINTS = (WAVENUMBER_RANGE[1] - WAVENUMBER_RANGE[0]) // WAVENUMBER_STEP + 1
GRID = np.arange(WAVENUMBER_RANGE[0],
                 WAVENUMBER_RANGE[1] + WAVENUMBER_STEP,
                 WAVENUMBER_STEP)
GAUSSIAN_SIGMA_CM = 2.0                # cm⁻¹
GAUSSIAN_SIGMA_IDX = GAUSSIAN_SIGMA_CM / WAVENUMBER_STEP

# Conversion factors
BOHR_TO_ANGSTROM = 0.529177210903      # Å / Bohr
BOHR3_TO_ANGSTROM3 = BOHR_TO_ANGSTROM ** 3
HARTREE_TO_EV = 27.211386245988        # eV / Hartree

# Target property column names (as they appear in the QM9 dataset)
# The dataset may use slightly different names; we handle a few common variants.
DIPOLE_COLS = ["Dipole_debye", "dipole", "mu"]
POLARIZABILITY_COLS = ["Polarizability_bohr3", "polarizability", "alpha"]
GAP_COLS = ["HOMO_LUMO_gap_au", "gap", "HOMO_LUMO_gap", "gap_au"]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _select_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """Return the first column name from *candidates* that exists in *df*."""
    for col in candidates:
        if col in df.columns:
            return col
    return None

def load_qm9_data(qm9_path: Optional[Path] = None) -> pd.DataFrame:
    """Load the QM9 dataset (properties)."""
    if qm9_path is None:
        qm9_path = Path("data/raw/qm9.parquet")
    return pd.read_parquet(qm9_path, engine="pyarrow")

def load_ir_spectra_data(ir_path: Optional[Path] = None) -> pd.DataFrame:
    """Load the IR‑spectra dataset."""
    if ir_path is None:
        ir_path = Path("data/raw/ir_spectra.parquet")
    return pd.read_parquet(ir_path, engine="pyarrow")

def _load_aligned_data() -> pd.DataFrame:
    """Load the already‑aligned dataset if it exists; otherwise perform a fresh join."""
    aligned_path = paths.data("processed", "aligned_data.parquet")
    if aligned_path.is_file():
        return pd.read_parquet(aligned_path, engine="pyarrow")
    # Fallback – join the raw tables
    qm9_df = load_qm9_data()
    ir_df = load_ir_spectra_data()
    merged, _ = perform_inner_join(qm9_df, ir_df)
    return merged

def perform_inner_join(qm9_df: pd.DataFrame,
                       ir_df: pd.DataFrame,
                       key: str = "InChIKey") -> Tuple[pd.DataFrame, int]:
    """
    Perform an inner join on QM9 and IR spectra datasets.

    Returns:
        (merged_dataframe, number_of_discarded_qm9_rows)
    """
    merged = pd.merge(qm9_df, ir_df, on=key, how="inner")
    discarded = len(qm9_df) - len(merged)
    return merged, discarded

def interpolate_spectra(spectra_df: pd.DataFrame,
                       wavenumber_range: Tuple[int, int] = WAVENUMBER_RANGE,
                       wavenumber_step: int = WAVENUMBER_STEP,
                       spectrum_col: str = "spectrum") -> pd.DataFrame:
    """
    Interpolate each spectrum onto a uniform wavenumber grid.

    The input *spectra_df* must contain two columns:
    - ``wavenumbers``: iterable of wavenumber values (cm⁻¹)
    - ``intensities``: iterable of the same length with intensity values

    A new column ``interpolated_spectrum`` is added containing a ``np.ndarray`` of
    length ``grid_points``.
    """
    logger = get_logger(__name__)

    if "wavenumbers" not in spectra_df.columns or "intensities" not in spectra_df.columns:
        raise KeyError("IR spectra DataFrame must contain 'wavenumbers' and 'intensities' columns.")

    grid = np.arange(wavenumber_range[0],
                     wavenumber_range[1] + wavenumber_step,
                     wavenumber_step)

    def _interp(row):
        wn = np.asarray(row["wavenumbers"], dtype=float)
        inten = np.asarray(row["intensities"], dtype=float)

        # Restrict to the requested range
        mask = (wn >= wavenumber_range[0]) & (wn <= wavenumber_range[1])
        if not np.any(mask):
            # No points in range – return zeros
            return np.zeros_like(grid)

        wn_in = wn[mask]
        inten_in = inten[mask]
        # Use np.interp with zero padding outside the available range
        return np.interp(grid, wn_in, inten_in, left=0.0, right=0.0)

    logger.info("Interpolating %d spectra onto a uniform grid", len(spectra_df))
    spectra_df["interpolated_spectrum"] = spectra_df.apply(_interp, axis=1)
    return spectra_df

def apply_smoothing_and_normalization(spectra_df: pd.DataFrame,
                                      sigma: float = GAUSSIAN_SIGMA_IDX,
                                      spectrum_col: str = "interpolated_spectrum") -> pd.DataFrame:
    """
    Apply Gaussian smoothing (σ expressed in grid indices) and unit‑area normalization.

    The function updates the ``interpolated_spectrum`` column in place.
    """
    logger = get_logger(__name__)
    logger.info("Applying Gaussian smoothing (σ=%.2f grid points)", sigma)

    def _smooth_and_norm(row):
        spec = np.asarray(row[spectrum_col], dtype=float)
        # Gaussian smoothing
        spec_smoothed = gaussian_filter1d(spec, sigma=sigma, mode="constant")
        # Unit‑area normalization (area = sum * step, step=1)
        total = spec_smoothed.sum()
        if total > 0:
            spec_normalized = spec_smoothed / total
        else:
            spec_normalized = spec_smoothed  # all zeros – leave as‑is
        return spec_normalized

    spectra_df[spectrum_col] = spectra_df.apply(_smooth_and_norm, axis=1)
    return spectra_df

def _convert_properties(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert dipole (Debye), polarizability (Bohr³ → Å³) and HOMO‑LUMO gap (Hartree → eV)
    to the required units and store them under canonical column names
    ``dipole``, ``polarizability`` and ``gap``.
    """
    logger = get_logger(__name__)

    # Dipole (already in Debye for the common column)
    dip_col = _select_column(df, DIPOLE_COLS)
    if dip_col is None:
        raise KeyError(f"None of the expected dipole columns {DIPOLE_COLS} found.")
    df["dipole"] = df[dip_col].astype(float)

    # Polarizability: Bohr³ → Å³
    pol_col = _select_column(df, POLARIZABILITY_COLS)
    if pol_col is None:
        raise KeyError(f"None of the expected polarizability columns {POLARIZABILITY_COLS} found.")
    df["polarizability"] = df[pol_col].astype(float) * BOHR3_TO_ANGSTROM3

    # Gap: Hartree → eV
    gap_col = _select_column(df, GAP_COLS)
    if gap_col is None:
        raise KeyError(f"None of the expected gap columns {GAP_COLS} found.")
    df["gap"] = df[gap_col].astype(float) * HARTREE_TO_EV

    logger.debug("Converted properties to target units")
    return df

def filter_properties_and_save(data_df: pd.DataFrame,
                              output_path: Optional[Path] = None,
                              required_properties: List[str] = None) -> Tuple[pd.DataFrame, int]:
    """
    Drop rows missing any of the *required_properties* and persist the arrays as an ``.npz`` file.

    The NPZ contains:
        - ``spectra``: shape (N, 1, 3601)   (float32)
        - ``dipole``: shape (N,)            (float32)
        - ``polarizability``: shape (N,)    (float32)
        - ``gap``: shape (N,)               (float32)
        - ``InChIKeys``: shape (N,)         (object / string)
        - ``selection_bias_stats``: empty dict (placeholder)
    """
    logger = get_logger(__name__)

    if required_properties is None:
        required_properties = ["dipole", "polarizability", "gap"]

    before = len(data_df)
    filtered = data_df.dropna(subset=required_properties)
    discarded = before - len(filtered)

    logger.info("Filtered molecules: %d kept, %d discarded (missing targets)",
                len(filtered), discarded)

    # Build arrays
    spectra_list = filtered["interpolated_spectrum"].tolist()
    spectra_arr = np.stack(spectra_list, axis=0).astype(np.float32)  # (N, 3601)
    spectra_arr = spectra_arr[:, np.newaxis, :]  # (N, 1, 3601)

    dipole_arr = filtered["dipole"].astype(np.float32).to_numpy()
    polar_arr = filtered["polarizability"].astype(np.float32).to_numpy()
    gap_arr = filtered["gap"].astype(np.float32).to_numpy()
    inchikeys_arr = filtered["InChIKey"].astype(str).to_numpy()

    if output_path is None:
        output_path = paths.data("processed", "aligned_dataset.npz")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(
        output_path,
        spectra=spectra_arr,
        dipole=dipole_arr,
        polarizability=polar_arr,
        gap=gap_arr,
        InChIKeys=inchikeys_arr,
        selection_bias_stats={}
    )

    logger.info("Saved preprocessed dataset to %s (shape %s)",
                output_path, spectra_arr.shape)
    return filtered, discarded

def check_dft_metadata(data_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Placeholder for any DFT‑metadata consistency checks.
    Currently returns an empty dict.
    """
    return {}

def perform_coverage_audit(full_qm9_df: pd.DataFrame,
                           aligned_df: pd.DataFrame,
                           property_columns: List[str] = None,
                           output_path: Optional[Path] = None) -> Dict[str, Dict[str, float]]:
    """
    Placeholder for a KS‑test coverage audit. Returns an empty dict.
    """
    return {}

def main() -> None:
    """
    Entry point for the preprocessing script.
    Orchestrates loading, alignment (if needed), interpolation, smoothing,
    normalization, unit conversion, filtering, and saving.
    """
    logger = get_logger(__name__)
    logger.info("Starting preprocessing pipeline")

    # ------------------------------------------------------------------
    # 1. Load (or re‑load) the aligned dataset
    # ------------------------------------------------------------------
    aligned_df = _load_aligned_data()
    logger.info("Loaded aligned dataset with %d rows", len(aligned_df))

    # ------------------------------------------------------------------
    # 2. Interpolate spectra onto the uniform grid
    # ------------------------------------------------------------------
    aligned_df = interpolate_spectra(aligned_df)

    # ------------------------------------------------------------------
    # 3. Smooth & normalize
    # ------------------------------------------------------------------
    aligned_df = apply_smoothing_and_normalization(aligned_df)

    # ------------------------------------------------------------------
    # 4. Convert target properties to required units
    # ------------------------------------------------------------------
    aligned_df = _convert_properties(aligned_df)

    # ------------------------------------------------------------------
    # 5. Filter out molecules missing any target property and persist
    # ------------------------------------------------------------------
    filtered_df, _ = filter_properties_and_save(aligned_df)

    # ------------------------------------------------------------------
    # 6. (Optional) Run any additional checks / audits – placeholders for now
    # ------------------------------------------------------------------
    _ = check_dft_metadata(filtered_df)
    # No explicit audit output required for the current task

    logger.info("Preprocessing completed successfully")

if __name__ == "__main__":
    main()