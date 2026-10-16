# Quickstart: Structure-Only Surrogate Model for 2D Material Elastic Moduli

## 1. Prerequisites
- Python 3.11+, 7GB+ RAM, 14GB+ disk, internet access to the verified dataset URL.

## 2. Installation
```bash
cd projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate
python -m venv venv && source venv/bin/activate
pip install -r code/requirements.txt
```

## 3. Run the Pipeline
```bash
python code/main_pipeline.py
```
Exit code 0 only if all hard gates pass. Stages, in order:

1. **Constitution title audit** (T060c): checks title for forbidden "First-Principles"/"Schrödinger Equation" terms; writes `data/results/constitution_title_audit.json`; **exits 1 on FAIL**.
2. **Data ingestion** (T013d1): downloads the verified canonical parquet, validates schema, checksums → `data/raw/`.
3. **Graph construction** (T013d2–d4): PBC-aware graphs → `data/processed/graphs_v1.parquet`.
4. **Split generation** (T013f): family-clustered split, atomically written → `data/processed/split_indices.json`.
5. **Split validation** (T017b): leakage check → `data/results/split_validation.json`.
6. **Training** (T018b): CPU-only GNN under `tracemalloc`; saves `data/processed/model_v1.pt`, `data/results/training_logs.json`; exits 1 if peak memory > 7GB.
7. **Evaluation**: `data/results/predictions.json`, `data/results/generalization_metrics.json` (incl. baseline comparison for SC-002).
8. **Inference benchmark** (T022): `data/results/inference_benchmark.json`; exits 1 if > 100ms/material.
9. **Feature importance** (T003): `data/results/feature_importance_report.md`.

## 4. Verification
```bash
python code/utils/verify_constitution_title.py   # expect exit 0 + audit JSON
pytest tests/                                    # unit + contract tests
python code/utils/verify_success_criteria.py --input data/results/generalization_metrics.json
```

## 5. Troubleshooting
- **Memory error**: reduce `batch_size` in `code/model/train.py`.
- **Audit FAIL**: amend the constitution title per the amendment procedure (remove "First-Principles Calculations").
- **Dataset schema mismatch**: loader falls back to the same-schema verified alternates; if none fit, it exits with an explicit mismatch error — do not substitute unverified data.
