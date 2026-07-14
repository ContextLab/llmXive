# Quickstart for PROJ-843-llmxive-follow-up-extending-latent-spati

This document lists the commands required to reproduce the end‑to‑end
research pipeline on a CPU‑only environment.

## 1. Prepare directories
```bash
python -c "from config import ensure_directories; ensure_directories()"
```

## 2. Download the RealEstate10K dataset (dense baseline)
```bash
python code/data/download.py
```

## 3. Stratify the dataset
```bash
python code/data/stratify.py
```

## 4. Extract sparse features
```bash
python code/data/extract_features.py
```

## 5. Run the geometry pipeline (solver + warp)
```bash
python code/geometry/run_pipeline.py
```

## 6. Compute evaluation metrics
```bash
python code/eval/metrics.py
```

## 7. Perform ANOVA analysis
```bash
python code/eval/anova.py
```

## 8. Sensitivity sweep
```bash
python code/eval/sensitivity.py
```

## 9. Generate final report
```bash
python code/eval/report.py
```

After step 6 you should find the file `data/results/metrics.json` and after
step 9 the verification markdown `data/results/hypothesis_verification.md`.