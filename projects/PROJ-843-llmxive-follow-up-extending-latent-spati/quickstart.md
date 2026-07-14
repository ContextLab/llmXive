# Quickstart for llmXive Follow‑up Project

This document describes the commands needed to run the full research pipeline on a
CPU‑only environment. Run each command from the repository root.

## 1️⃣ Prepare data & download resources
```bash
python code/data/download.py # RealEstate10K download
python code/eval/download_dense_baseline.py # Dense baseline frames
```

## 2️⃣ Stratify & extract features
```bash
python code/data/stratify.py
python code/data/extract_features.py
```

## 3️⃣ Geometry pipeline (solver + warp)
```bash
python code/geometry/run_pipeline.py
```

## 4️⃣ Evaluation
```bash
python code/eval/metrics.py # Compute WorldScore, Sparse‑Consistency, FID, etc.
python code/eval/anova.py # Two‑Way ANOVA
python code/eval/report.py # Final verification report
```

## 5️⃣ End‑to‑end orchestration (optional)
```bash
python code/main.py --phase evaluate # Runs the full evaluation phase
```

After the pipeline finishes, you will find:
- `data/results/metrics.json` – all computed metrics.
- `data/results/metrics.json` will be consumed by `code/eval/report.py` to
 generate `data/results/hypothesis_verification.md`.