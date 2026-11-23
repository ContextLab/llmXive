# Reproducibility Statement

This project is designed to be fully reproducible using real data and open-source tools.

## Data Integrity

- **Source**: OpenNeuro `ds003645`. [UNRESOLVED-CLAIM: c_725f86a4 — status=not_enough_info]
- **Verification**: All downloads are verified via SHA256 checksums against the OpenNeuro manifest.
- **No Fabrication**: The pipeline contains no synthetic data generation. If the source is unreachable, the pipeline fails explicitly.

## Environment

- **Python**: 3.11
- **Dependencies**: Pinned in `requirements.txt` (e.g., `mne>=1.6.0`).
- **Hardware**: Designed for standard CPU (2 cores) and 7GB RAM.

## Execution Flow

To reproduce the results:
1. Clone the repository.
2. Set `OPENNEURO_API_KEY`.
3. Run `code/download.py`, `code/preprocess.py`, `code/extract.py`, `code/stats.py`, and `code/viz.py` in sequence.
4. Verify `results/` contains `metrics.csv`, `statistics.json`, and plots.

## Version Control

- Code changes are tracked in Git.
- Intermediate data artifacts (`.fif`, `.csv`, `.json`) are generated deterministically from the same input.

## Known Limitations

- **Memory**: ICA on full datasets may exceed 7GB RAM on some machines; the pipeline subsamples to 32 channels [UNRESOLVED-CLAIM: c_0552cf50 — status=not_enough_info] to mitigate this.
- **Time**: Cluster-based permutation tests (1000 permutations [UNRESOLVED-CLAIM: c_ae25c06b — status=not_enough_info]) may take several hours on dual-core CPUs.
