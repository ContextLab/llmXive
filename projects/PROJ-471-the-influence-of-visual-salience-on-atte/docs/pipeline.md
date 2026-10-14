# Pipeline Overview

This document describes each stage of the **Visual Salience → Attentional Bias**
pipeline. It is referenced by the quick‑start guide and serves as a living
specification for developers.

## 1. Project bootstrap

*Script*: `code/bootstrap.py`
Creates the folder hierarchy:

```
code/
data/
 raw/
 interim/
 processed/
 results/
docs/
```

Also writes a pinned `requirements.txt` and prints a directory tree.

## 2. Data ingestion

*Script*: `code/ingestion/download_data.py` (implemented in later tasks)
Verifies that `data/raw/ds003123/` exists, computes checksums, and aborts
with `DATA_MISSING_001` if the dataset is absent.

## 3. Salience map generation

*Script*: `code/ingestion/salience_map.py` (later task)
Uses DeepGaze II on CPU, batches images, writes `.npy` maps to
`data/interim/salience_maps/`.

## 4. ROI segmentation

*Script*: `code/eye_tracking/segment_roi.py` (later task)
Generates face masks (YOLOv8) and weapon masks (Detectron2) in
`data/interim/masks/`.

## 5. Fixation metric extraction

*Script*: `code/eye_tracking/parse_fixations.py` (later task)
Produces `data/interim/fixations.csv`.

## 6. Alignment & feature generation

*Scripts*: `code/analysis/align_data.py`,
`code/analysis/feature_gen.py` (low‑level features for VIF diagnostics).

Resulting aligned CSV is stored at `data/processed/aligned_data.csv`.

## 7. Statistical modelling

*Scripts*: `code/analysis/lmm_fit.py`,
`code/analysis/robustness.py`,
`code/analysis/plot_sensitivity.py`,
`code/analysis/write_final_results.py`.

Final JSON results are written to `data/processed/results.json`.

## 8. Validation

*Script*: `code/utils/final_validator.py` (later task) validates the
output schema and ensures the “correlational only” disclaimer is added
where required.

## 9. Documentation & reproducibility

*README.md* (this file) and the `docs/` folder provide installation,
execution, and methodological details for users and reviewers.
