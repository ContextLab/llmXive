# Quickstart for the Latent Spatial Memory Project

This document describes the minimal commands required to run the full
research pipeline on a CPU‑only environment. All commands are expected
to succeed and produce the artefacts listed in the specification.

## 1. Prepare directories

```bash
python -c "import code.config as cfg; cfg.ensure_directories()"
```

## 2. Download datasets

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

## 5. Run geometry pipeline (solver + warp)

```bash
python code/geometry/run_pipeline.py
```

## 6. Aggregate warped frames (produces the missing artefact)

```bash
python code/geometry/aggregate_warps.py
```

## 7. Compute evaluation metrics

```bash
python code/eval/metrics.py
```

## 8. Perform ANOVA analysis

```bash
python code/eval/anova.py
```

## 9. Sensitivity sweep

```bash
python code/eval/sensitivity.py
```

## 10. Final report

```bash
python code/eval/report.py
```

After the above steps complete, you should find the following files:

- `data/results/sparse_warped_frames.npy` (produced by step 6)
- `data/results/metrics.json` (produced by step 7)
- `data/results/metrics_anova.json` (produced by step 8)
- `data/results/sensitivity.json` (produced by step 9)
- `data/results/hypothesis_verification.md` (produced by step 10)