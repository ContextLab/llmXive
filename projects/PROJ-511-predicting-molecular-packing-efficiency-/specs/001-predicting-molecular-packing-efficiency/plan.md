# Implementation Plan: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

**Branch**: `PROJ-511-predicting-molecular-packing-efficiency`  
**Date**: 2026-10-10  
**Spec**: `spec.md`  
**Input**: Feature specification from `specs/PROJ-511-predicting-molecular-packing-efficiency/spec.md`

## Summary
The goal is to build a **CPU‑only** end‑to‑end pipeline that (1) obtains a reproducible dataset of organic crystal structures with SMILES strings and packing coefficients, (2) trains two lightweight 2‑layer MLP regression models (SMILES‑only primary model and SMILES + 3‑D full model), (3) evaluates predictive performance with rigorous statistical tests, (4) conducts a sensitivity analysis over high‑packing thresholds, and (5) generates a fully validated HTML report. All steps must be reproducible on a GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ≤6 h).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `rdkit`, `torch` (CPU‑only), `transformers`, `scikit-learn`, `pandas`, `numpy`, `joblib`, `datasets`, `jinja2`, `pyyaml`, `scipy`, `statsmodels`  
- **Storage**: Local `data/` folder (raw, processed, artifacts)  
- **Testing**: `pytest` (unit + integration)  
- **Target Platform**: Linux CI runner (GitHub Actions)  
- **Project Type**: Data‑science pipeline / CLI  
- **Performance Goals**: End‑to‑end ≤ 6 h, model training ≤ 30 min, permutation test ≤ 2 h (fallback).  
- **Constraints**: CPU‑first; GPU escape hatch only if transformer inference OOMs (Kaggle free GPU).  
- **Scale/Scope**: Minimum 500 valid records after filtering; ≤ 100 k trainable parameters per model.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| **I. Reproducibility** | All random seeds (`numpy`, `torch`, `random`) are pinned in `code/utils/random.py`. External datasets are fetched deterministically from the same URL on every run. |
| **II. Verified Accuracy** | All citations (Bondi radii, COD source) are cross‑checked against the verified facts list. No unverified URLs are introduced. |
| **III. Data Hygiene** | Raw downloads are stored unchanged under `data/raw/`. Every derived file is checksum‑verified (SHA‑256) and carries a provenance JSON. |
| **IV. Single Source of Truth** | Every figure, table, and statistic in `report.html` is generated programmatically from the validated CSVs; no hand‑typed numbers. |
| **V. Versioning Discipline** | Content hashes for all artifacts are recorded in `state/projects/PROJ-511-predicting-molecular-packing-efficiency-.yaml`. |
| **VI. Open Crystallographic Data Integrity** | The pipeline is required to source crystal records directly from the Crystallography Open Database (COD). **However, no verified COD download URL is present in the verified‑datasets block** (see Data Availability section). This constitutes a current violation that must be resolved before Phase 0 can run. |
| **VII. Model Transparency and Statistical Validation** | Model architecture, hyper‑parameters, and training script are committed. Permutation test uses 10 000 shuffles (or a documented fallback). All statistical diagnostics are included in the validation report. |

*The plan notes a data‑source gap (Principle VI) that must be addressed before execution.*

## Project Structure
```text
projects/PROJ-511-predicting-molecular-packing-efficiency-/
├── code/
│   ├── __init__.py
│   ├── utils/
│   │   ├── random.py               # Seed management
│   │   ├── rdkit_helpers.py        # SMILES extraction/generation, 3‑D descriptors
│   │   └── stats.py                # VIF, permutation test, Shapiro‑Wilk
│   ├── download_cod.py             # FR‑001 (dataset acquisition)
│   ├── generate_smiles.py          # FR‑002
│   ├── compute_descriptors.py      # FR‑012
│   ├── encode_smiles.py            # FR‑004 (streaming transformer)
│   ├── generate_confounders.py     # FR‑021
│   ├── train_model.py              # FR‑005
│   ├── evaluate_model.py           # FR‑006, FR‑009, FR‑014, FR‑015
│   ├── sensitivity_analysis.py    # FR‑007, FR‑008
│   ├── report_generator.py         # FR‑010
│   └── requirements.txt
├── data/
│   ├── raw/                         # Unmodified downloads
│   ├── processed/                   # CSVs, feature matrix
│   └── artifacts/                   # Model checkpoints, reports, logs
├── contracts/
│   ├── dataset.schema.yaml
│   ├── model.schema.yaml
│   └── validation_report.schema.yaml
└── tests/
    ├── unit/
    └── integration/
```

## Phase Execution Order & FR Mapping
| Phase | Description | Script(s) | FR(s) Covered |
|-------|-------------|-----------|----------------|
| **Phase 0 – Data Acquisition & Feature Engineering** | Download COD, filter, generate SMILES, compute 3‑D descriptors, encode SMILES, add confounder counts, merge into full feature matrix. | `download_cod.py`, `generate_smiles.py`, `compute_descriptors.py`, `encode_smiles.py`, `generate_confounders.py` | FR‑001, FR‑002, FR‑003, FR‑004, FR‑012, FR‑021 |
| **Phase 1 – Data Validation & Diagnostics** | Schema validation, checksum logging, VIF diagnostics, target‑distribution checks. | `evaluate_model.py` (validation sub‑routines) | FR‑009, FR‑014, FR‑016 (source verification), FR‑017 (Bondi radii), FR‑019 (power analysis) |
| **Phase 2 – Model Training** | Train Primary (SMILES‑only) and Full (SMILES + 3‑D) MLPs on an 80/20 split. | `train_model.py` | FR‑005 |
| **Phase 3 – Evaluation & Robustness** | Compute MAE, Spearman ρ, Pearson r, Shapiro‑Wilk, permutation test, Bonferroni‑corrected p‑values, residual‑composition correlation. | `evaluate_model.py` | FR‑006, FR‑008, FR‑010, FR‑013, FR‑014, FR‑015 |
| **Phase 4 – Sensitivity Analysis** | Sweep high‑packing thresholds {0.5, 0.6, 0.7}, record metrics, apply Bonferroni correction. | `sensitivity_analysis.py` | FR‑007, FR‑008 |
| **Phase 5 – Reporting** | Assemble HTML report, embed provenance, model hashes, and validation JSON. | `report_generator.py` | FR‑010, FR‑018, FR‑020 (streaming inference sanity check) |

All **Success Criteria (SC‑001 … SC‑006)** are verified in the final validation report and the generated HTML.

## Compute Feasibility & Data Strategy
1. **CPU‑First**  
   - SMILES‑Transformer inference is performed with `device="cpu"` and a batch size of **64**; embeddings are streamed to disk in JSONL chunks to stay < 7 GB RAM.  
   - MLP training uses PyTorch CPU tensors; total training time ≤ 30 min on 2 cores.  
   - Permutation test uses `joblib.Parallel(n_jobs=-1)`; a hard timeout of **2 h** is enforced. If the timeout fires, the actual number of shuffles performed is recorded and the report flags the deviation (FR‑015, SC‑006).  

2. **GPU Escape Hatch**  
   - If the transformer OOMs despite batching, the execution framework will automatically re‑run the same script on a Kaggle free GPU (`device="cuda"`, 8‑bit quantization via `bitsandbytes` if needed). This satisfies the “real GPU” requirement without fabricating a CPU approximation.  

3. **Data Availability**  
   - **Verified COD source**: *No* URL appears in the verified‑datasets block. Consequently, the pipeline **cannot** automatically fetch the COD archive on a CI runner. This is a **blocking data‑availability issue** (Principle VI).  
   - **Proposed resolution**:  
     - **Option A** – Obtain a COD mirror that is hosted on HuggingFace (none currently verified).  
     - **Option B** – Revise the research question to use an open crystallographic dataset that *is* verified (e.g., a subset of the Materials Project).  
   - Until a verified source is supplied, Phases 0‑5 remain **pending**. The plan explicitly documents this gap and requests a scope revision or provision of a verified dataset.

## Risk Mitigation
| Risk | Mitigation |
|------|------------|
| **Missing verified COD data** (Principle VI) | Flag as blocking; request an open, programmatically downloadable substitute or provide a verified COD mirror. |
| **OOM during transformer encoding** | Streaming inference with batch = 64; automatic GPU escape hatch. |
| **Permutation test timeout** | Hard 2 h limit; fallback to the maximum feasible shuffle count (≥ 1 000) and log deviation. |
| **Circularity / tautology** | Target redefined to **PC_raw** (FR‑003) and atom‑count features excluded from the primary predictor set (FR‑021). Residual analysis quantifies any remaining compositional signal (FR‑014). |
| **Non‑normal residuals** | Use Spearman ρ as primary metric; Shapiro‑Wilk test determines whether Pearson r is reported (FR‑014). |
| **Multiple‑comparison inflation** | Bonferroni correction applied to the three sensitivity thresholds (FR‑008). |
| **Insufficient power** | Power analysis via bootstrap (FR‑019); if dataset < 500 after filtering, pipeline aborts with a warning (SC‑001). |

---
