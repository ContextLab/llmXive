"""
Synthetic data generation entry‑point.

This script is used by the verification pipeline to create:
  * ``data/raw/mock_nifti/`` – a directory of mock NIfTI files (one per subject)
  * ``data/processed/subjects.parquet`` – a Parquet table with behavioural metadata

The implementation relies on :pyfunc:`synthetic_generator.generate_synthetic_dataset`,
which now guarantees a balanced cohort (≈75 musicians, ≈75 non‑musicians),
respects the schema defined in ``contracts/subject.schema.yaml``, and injects
a small seeded rate of missing training‑history values and corrupted NIfTI files
(logged) so that downstream preprocessing can demonstrate exclusion handling.

Running this script will **always** write the two artefacts to the exact
locations expected by downstream modules and unit tests.
"""

import sys
from pathlib import Path

# Import the generator from the sibling module using a direct import
# (the ``code/data`` directory is on ``sys.path`` when the script is executed)
import synthetic_generator

def main() -> int:
    """
    Execute the synthetic data generation.

    The function uses a deterministic seed (42) so that repeated runs
    produce identical data – this is required for reproducible unit tests.
    """
    # Target ~150 subjects → 75 per group (the default MIN_SUBJECTS_PER_GROUP is 50,
    # so 150 satisfies the “≈75 per group” description while keeping the dataset
    # small enough for quick verification runs.
    n_subjects = 150

    # The generator writes the required files automatically.
    # We keep the seed fixed for reproducibility.
    synthetic_generator.generate_synthetic_dataset(n_subjects=n_subjects, seed=42)

    # Verify that the expected artefacts now exist; raise if not.
    subjects_path = Path("data/processed/subjects.parquet")
    nifti_dir = Path("data/raw/mock_nifti")

    missing = []
    if not subjects_path.is_file():
        missing.append(str(subjects_path))
    if not nifti_dir.is_dir() or not any(nifti_dir.iterdir()):
        missing.append(str(nifti_dir))

    if missing:
        print(f"ERROR: Expected synthetic artefacts not found: {', '.join(missing)}", file=sys.stderr)
        return 1

    print("Synthetic dataset generated successfully.")
    print(f"  - Behavioural table: {subjects_path}")
    print(f"  - Mock NIfTI directory: {nifti_dir} (contains {len(list(nifti_dir.iterdir()))} files)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
