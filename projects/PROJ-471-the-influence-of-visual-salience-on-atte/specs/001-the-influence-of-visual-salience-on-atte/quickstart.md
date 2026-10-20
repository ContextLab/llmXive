# Quickstart: The Influence of Visual Salience on Attentional Bias in Moral Judgements

## Prerequisites
- Python 3.11+; pip.
- **Data (manual)**: download OpenNeuro ds003123 (Moral Foundations Eye-Tracking) yourself and place the extracted directory at `data/raw/ds003123/`. It must contain `stimuli/` and at least one `sub-*` participant directory. There is no verified automated download source; the pipeline will not fetch or substitute data.

## Installation
```bash
git clone <repo-url>
cd projects/PROJ-471-the-influence-of-visual-salience-on-atte
python code/bootstrap.py --root .
pip install -r requirements.txt
```

## Verify data presence
```bash
python -m code.ingestion.verify_data
# OK:    "✅ Dataset structure valid; N files checksummed to data/raw/checksums.json"
# FAIL:  "❌ DATA_MISSING_001 – expected data/raw/ds003123/stimuli/ and sub-* directories"
```
The script exits non-zero on missing structure or on an empty checksum result.

## Run the full pipeline
```bash
python -m code.main --stage full
```
Order: verify data → salience maps (OpenCV spectral residual, CPU) → ROI masks (YOLOv8) → fixation extraction → alignment + covariates → VIF/PCA → mixed models A/B + FDR + power → contract validation.

## Expected outputs
- `data/raw/checksums.json` — SHA-256 of every raw file (non-empty).
- `data/interim/salience_maps/<stimulus_id>.npy` + `salience_metadata.json` (schema-conformant).
- `data/interim/masks/`, `mask_metadata.csv`, `fixations.csv`.
- `data/processed/aligned_data.csv` (validates against `dataset.schema.yaml`).
- `data/processed/results.json` (validates against `output.schema.yaml`; includes FDR-corrected p-values, sensitivity, VIF report, `power_status`, and the `"correlational only"` disclaimer).
- `logs/pipeline.log`, `logs/diagnostics.log`, `logs/resource.log`.

## Run tests
```bash
pytest tests/ -q
```
Unit tests cover bootstrap (with `--root tmp_path`), data verification (synthetic fixture trees), salience generation, ROI segmentation (including graceful degradation when ultralytics is absent), fixation parsing, and contract validation.

## Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| `DATA_MISSING_001` | ds003123 not placed / incomplete structure | Place full extracted dataset (stimuli + sub-* dirs) under `data/raw/ds003123/` |
| Checksum file empty | verification ran against empty dir | ensure raw files exist; re-run `verify_data.py` |
| Masks all `undetected` | YOLOv8 weights unavailable offline | allow network for first run (weights cache), or accept flagged-ROI degradation |
| High VIF | collinear low-level features | PCA orthogonalization applies automatically when VIF > 5; see `logs/diagnostics.log` |
| `power_status: "invalid"` | simulated power < 0.8 | result reported as invalid for inference per SC-003; limitation documented |
