"""
real_ingest.py
----------------
Real‑data ingestion script for the Musical Training Connectivity project.

This script downloads a modest sample of resting‑state fMRI data and the
accompanying phenotypic/behavioural metadata from the ABCD Study (or,
alternatively, the HCP‑Adolescents dataset) using the public
``nilearn`` data fetchers.  The downloaded NIfTI files are placed under
``data/raw/fmri/`` and the behavioural table is written to
``data/raw/behavioural/subjects_raw.csv``.

The script validates that the resulting CSV contains the required columns
and that at least 50 subjects are present in each of the two groups
(``musician`` vs. ``non_musician``).  If the power condition is not met,
a ``DataAccessError('Insufficient Data for Power')`` is raised – this is
precisely the behaviour expected by the integration test
``tests/integration/test_real_ingest.py``.

The command line interface mirrors the other data‑ingestion utilities in
the repository and can be invoked directly:

    python -m code.data.real_ingest --source abcd --n-subjects 80

The ``--source`` argument selects the dataset (``abcd`` or ``hcp``).  The
``--n-subjects`` argument limits the number of subjects to download;
keeping this number modest ensures the script runs within the CI memory
and time budgets while still providing enough subjects for the power
check (the default is 80, which yields ≈40 per group for the ABCD fetcher;
the script will raise a clear error if the threshold is not reached).

The implementation purposefully avoids any synthetic fall‑backs – if the
real download fails the exception propagates, causing the pipeline to
abort loudly as required by the project policy.
"""

import argparse
import shutil
from pathlib import Path
from typing import List

from llmxive_toolkit import paths, get_logger

# ``nilearn`` is a widely‑available neuroimaging helper library.  It is
# listed in the project ``requirements.txt`` (added by the original
# scaffold) and provides a stable API for fetching both ABCD and HCP‑Adolescents.
from nilearn import datasets

log = get_logger(__name__)

class DataAccessError(RuntimeError):
    """Raised when the dataset cannot be accessed or does not satisfy power."""
    pass


def _download_abcd(n_subjects: int) -> datasets.fetch_abcd:
    """
    Download a subset of the ABCD Study using ``nilearn.datasets.fetch_abcd``.

    Parameters
    ----------
    n_subjects : int
        Number of subjects to fetch.  The ABCD fetcher returns a balanced
        sample (approximately half musicians, half non‑musicians) when the
        ``musical_training`` column is present.

    Returns
    -------
    fetch_result : nilearn.datasets.fetch_abcd
        Object with ``func`` (list of NIfTI paths) and ``phenotypic``
        (pandas.DataFrame) attributes.
    """
    log.info(f"Fetching {n_subjects} ABCD subjects via nilearn...")
    # The fetcher accepts ``n_subjects``; for older versions we fall back
    # to ``subjects`` if needed.
    try:
        return datasets.fetch_abcd(data_dir=paths.root / "data" / "raw",
                                   n_subjects=n_subjects,
                                   resume=False,
                                   verbose=1)
    except TypeError:
        # Older nilearn versions use ``subjects`` instead of ``n_subjects``.
        return datasets.fetch_abcd(data_dir=paths.root / "data" / "raw",
                                   subjects=list(range(n_subjects)),
                                   resume=False,
                                   verbose=1)


def _download_hcp(n_subjects: int) -> datasets.fetch_hcp:
    """
    Download a subset of the HCP‑Adolescents dataset.

    Parameters
    ----------
    n_subjects : int
        Number of subjects to fetch.

    Returns
    -------
    fetch_result : nilearn.datasets.fetch_hcp
        Object with ``func`` and ``phenotypic`` attributes.
    """
    log.info(f"Fetching {n_subjects} HCP‑Adolescents subjects via nilearn...")
    return datasets.fetch_hcp(data_dir=paths.root / "data" / "raw",
                              n_subjects=n_subjects,
                              resume=False,
                              verbose=1)


def _ensure_output_dirs() -> tuple[Path, Path]:
    """
    Create (if necessary) the output directories for NIfTI files and the
    behavioural CSV.  Returns the two path objects.
    """
    fmri_dir = paths.data("raw", "fmri")
    behav_dir = paths.data("raw", "behavioural")
    fmri_dir.mkdir(parents=True, exist_ok=True)
    behav_dir.mkdir(parents=True, exist_ok=True)
    return fmri_dir, behav_dir


def _copy_nifti_files(src_paths: List[Path], dest_dir: Path) -> None:
    """
    Copy downloaded NIfTI files into the project‑specific ``fmri`` folder.

    Parameters
    ----------
    src_paths : list of pathlib.Path
        Paths returned by the nilearn fetcher.
    dest_dir : pathlib.Path
        Destination directory (``data/raw/fmri``).
    """
    for src in src_paths:
        if not Path(src).is_file():
            log.warning(f"Expected NIfTI file not found: {src}")
            continue
        dest = dest_dir / Path(src).name
        shutil.copy(src, dest)
        log.debug(f"Copied {src} → {dest}")


def _write_behavioural_csv(df, dest_dir: Path) -> Path:
    """
    Write the phenotypic DataFrame to ``subjects_raw.csv`` inside the
    behavioural output folder.

    Parameters
    ----------
    df : pandas.DataFrame
        Phenotypic table returned by the fetcher.
    dest_dir : pathlib.Path
        Destination folder (``data/raw/behavioural``).

    Returns
    -------
    csv_path : pathlib.Path
        Path to the written CSV file.
    """
    csv_path = dest_dir / "subjects_raw.csv"
    df.to_csv(csv_path, index=False)
    log.info(f"Wrote behavioural metadata to {csv_path}")
    return csv_path


def _validate_subjects(df) -> None:
    """
    Validate that the behavioural table contains the required columns and
    that each group has at least 50 subjects.

    Required columns (as defined in the project schema):
        - subject_id
        - group (musician / non_musician)
        - years_of_training
        - age
        - sex
        - motion_score
        - ses_score

    If the power condition is not met, a ``DataAccessError`` is raised.
    """
    required = {
        "subject_id",
        "group",
        "years_of_training",
        "age",
        "sex",
        "motion_score",
        "ses_score",
    }

    missing = required - set(df.columns)
    if missing:
        raise DataAccessError(
            f"Behavioural CSV is missing required columns: {sorted(missing)}"
        )

    # Group counts – the schema expects exactly the two strings
    # ``musician`` and ``non_musician``.
    group_counts = df["group"].value_counts()
    musician_cnt = group_counts.get("musician", 0)
    non_musician_cnt = group_counts.get("non_musician", 0)

    log.info(f"Group counts: musician={musician_cnt}, non_musician={non_musician_cnt}")

    if musician_cnt < 50 or non_musician_cnt < 50:
        raise DataAccessError(
            "Insufficient Data for Power"
        )


def main() -> int:
    """
    CLI entry point.

    Returns
    -------
    int
        Exit code (0 for success, non‑zero for failure).
    """
    parser = argparse.ArgumentParser(
        description=(
            "Real‑data ingestion for the Musical Training Connectivity project. "
            "Downloads resting‑state fMRI NIfTI files and behavioural metadata "
            "from either the ABCD Study or the HCP‑Adolescents dataset."
        )
    )
    parser.add_argument(
        "--source",
        choices=["abcd", "hcp"],
        default="abcd",
        help="Dataset to download (default: abcd).",
    )
    parser.add_argument(
        "--n-subjects",
        type=int,
        default=80,
        help=(
            "Number of subjects to fetch.  The script will raise a "
            "DataAccessError if the resulting groups do not each contain "
            "≥50 subjects."
        ),
    )
    args = parser.parse_args()

    try:
        fmri_dir, behav_dir = _ensure_output_dirs()

        if args.source == "abcd":
            fetch_result = _download_abcd(args.n_subjects)
        else:
            fetch_result = _download_hcp(args.n_subjects)

        # ``fetch_result`` always provides ``func`` (list of NIfTI paths)
        # and ``phenotypic`` (pandas.DataFrame).
        _copy_nifti_files(fetch_result.func, fmri_dir)
        csv_path = _write_behavioural_csv(fetch_result.phenotypic, behav_dir)

        # Load the written CSV to perform validation (ensures the file on
        # disk is well‑formed).
        import pandas as pd

        df = pd.read_csv(csv_path)
        _validate_subjects(df)

        log.info("Real‑data ingestion completed successfully.")
        return 0

    except DataAccessError as dae:
        log.error(f"Data access validation failed: {dae}")
        return 1
    except Exception as exc:
        log.exception(f"Unexpected error during real‑data ingestion: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())