# Implementation Plan: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

**Branch**: `PROJ-511-predicting-molecular-packing-efficiency`  
**Date**: 2026-10-11  
**Spec**: `specs/PROJ-511-predicting-molecular-packing-efficiency/spec.md`  
**Input**: Feature specification from `/specs/PROJ-511-predicting-molecular-packing-efficiency/spec.md`

## Summary
Build a **CPU‑only** end‑to‑end pipeline that (1) downloads organic crystal entries from the Crystallography Open Database (COD), (2) extracts or generates canonical SMILES strings, (3) computes the packing coefficient (PC) from Bondi van der Waals volumes, (4) encodes SMILES with a frozen pre‑trained SMILES‑Transformer, (5) trains a lightweight 2‑layer MLP (≤ 100 k parameters, dropout = 0.1), (6) evaluates the model with MAE, Spearman ρ, Pearson r, Shapiro‑Wilk on residuals, and a **full** 10 000‑shuffle permutation test, (7) performs diagnostic VIF analyses on a PCA‑reduced fingerprint, (8) runs a Bonferroni‑corrected sensitivity sweep over high‑packing thresholds {0.5, 0.6, 0.7}, and (9) generates a reproducible HTML report validated against `contracts/validation_report.schema.yaml`. All steps must complete on a GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ≤ 6 h). No GPU escape hatch is used; if memory pressure occurs during SMILES encoding, the batch size is automatically reduced (64 → 32 → 16) to stay within the 6 GB RAM limit.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `rdkit`, `torch` (CPU‑only), `transformers`, `scikit-learn`, `pandas`, `numpy`, `joblib`, `datasets`, `jinja2`, `pyyaml`, `scipy`, `statsmodels`  
- **Storage**: File‑based hierarchy under `data/` (`raw/`, `processed/`, `artifacts/`)  
- **Testing**: `pytest` (unit + integration)  
- **Target Platform**: Linux CI runner (GitHub Actions)  
- **Performance Goals**: End‑to‑end ≤ 6 h; model training ≤ 30 min; permutation test ≤ 2 h (hard timeout removed – full extensive shuffles guaranteed).  
- **Constraints**: CPU‑first; no GPU fallback to preserve deterministic embeddings; streaming inference to keep RAM ≤ 6 GB.  
- **Scale/Scope**: Minimum 500 valid records after filtering; ≤ 100 k trainable parameters per model  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| **I. Reproducibility** | All random seeds (`numpy`, `torch`, `random`) are pinned in `code/utils/random.py`. External datasets are fetched deterministically from the same URL on every run. |
| **II. Verified Accuracy** | Bondi radii are cited from DOI 10.1021/j100785a001 (verified fact). The COD source URL is **missing** from the verified‑datasets block, which violates Principle VI. The pipeline is therefore **blocked** until a verified COD mirror URL is supplied; all downstream phases are marked as pending. |
| **III. Data Hygiene** | Raw downloads are stored unchanged under `data/raw/`. Every derived file is checksum‑verified (SHA‑256) and accompanied by a provenance JSON (`source_verification.json`). |
| **IV. Single Source of Truth** | Every figure, table, and statistic in `report.html` is generated programmatically from validated CSVs; no hand‑typed numbers appear. |
| **V. Versioning Discipline** | Content hashes for all artifacts are recorded in `state/projects/PROJ-511-predicting-molecular-packing-efficiency-.yaml`. |
| **VI. Open Crystallographic Data Integrity** | **Blocking issue** – No verified COD download URL is currently available. The pipeline will not commence until such a URL is provided, satisfying Principle VI. |
| **VII. Model Transparency and Statistical Validation** | Model architecture, hyper‑parameters, and training script are committed. Permutation test now always runs the full 10 000 shuffles; VIF diagnostics are performed on a PCA‑reduced fingerprint (≤ 20 components) to avoid multicollinearity instability. |

## Project Structure
```text
projects/PROJ-511-predicting-molecular-packing-efficiency/
├── code/
│   ├── __init__.py
│   ├── utils/
│   │   ├── random.py               # Seed management
│   │   ├── rdkit_helpers.py        # SMILES extraction/generation, 3‑D descriptors
│   │   └── stats.py                # VIF, permutation test, Shapiro‑Wilk
│   ├── download_cod.py             # FR‑001, FR‑011
│   ├── generate_smiles.py          # FR‑002
│   ├── compute_descriptors.py      # FR‑003, FR‑009
│   ├── encode_smiles.py            # FR‑004 (streaming, CPU‑only, batch‑size fallback)
│   ├── train_model.py              # FR‑005
│   ├── evaluate_model.py           # FR‑006, FR‑007, FR‑013, FR‑014, FR‑015, SC‑003
│   ├── sensitivity_analysis.py    # FR‑008
│   ├── report_generator.py         # FR‑010, FR‑018
│   └── requirements.txt
├── data/
│   ├── raw/                         # Unmodified COD files (or substitute once URL provided)
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
| **Phase 0 – Data Acquisition & Feature Engineering** | Download COD, filter organic ≤ 50 non‑H atoms, extract/generate SMILES, compute PC, compute 3‑D geometry descriptors, encode SMILES, add confounder metadata, merge into full feature matrix. | `download_cod.py`, `generate_smiles.py`, `compute_descriptors.py`, `encode_smiles.py` | FR‑001, FR‑002, FR‑003, FR‑004, FR‑011, FR‑009 |
| **Phase 1 – Data Validation & Hygiene** | Verify schema compliance (`contracts/dataset.schema.yaml`), compute SHA‑256 checksums, log download statistics, abort on missing mandatory fields. | `validate_dataset.py` (to be implemented) | FR‑011, FR‑012, Principle III |
| **Phase 2 – Model Training** | Train Primary SMILES‑only MLP on an 80/20 split; optionally train Full model with geometry descriptors. | `train_model.py` | FR‑005 |
| **Phase 3 – Evaluation & Robustness** | Compute MAE, Spearman ρ, Pearson r, Shapiro‑Wilk test on residuals, **full** 10 000‑shuffle permutation test, VIF diagnostics on PCA‑reduced fingerprint, residual‑composition correlation, enforce SC‑003 via automated check. | `evaluate_model.py` | FR‑006, FR‑007, FR‑013, FR‑014, FR‑015, SC‑003 |
| **Phase 4 – Sensitivity Analysis** | Sweep high‑packing thresholds {0.5, 0.6, 0.7}, compute metrics, apply Bonferroni correction (α_adj ≈ 0.0167). | `sensitivity_analysis.py` | FR‑008 |
| **Phase 5 – Reporting** | Assemble reproducible HTML report, embed provenance JSON, model hashes, full‑source‑code git commit, and validate against `contracts/validation_report.schema.yaml`. | `report_generator.py` | FR‑010, FR‑018, SC‑005, SC‑002, SC‑003 |

All **Success Criteria** (SC‑001 – SC‑005) are verified in the final `validation_report.json` and `report.html`.

## Compute Feasibility & Data Strategy
1. **CPU‑First**  
   - SMILES‑Transformer inference runs on `device="cpu"` with batch size 64; if memory usage exceeds 6 GB, the script automatically halves the batch size (64 → 32 → 16) and retries. This guarantees successful encoding without GPU fallback, preserving deterministic embeddings.  
   - MLP training uses PyTorch CPU tensors; total training time ≤ 30 min on 2 cores.  
   - Permutation test parallelized via `joblib.Parallel(n_jobs=-1)` and guaranteed to complete the full 10 000 shuffles within the 2‑hour window (no timeout).  

2. **Data Availability**  
   - **Verified COD source**: *None* appears in the “Verified datasets” block. This is a **blocking issue**.  
   - **Proposed resolution**:  
     - **Option A** – Provide a verified COD mirror URL (e.g., a HuggingFace dataset that contains the raw CIF files).  
     - **Option B** – Adopt an open substitute that supplies equivalent crystallographic metadata (e.g., a curated subset of the Materials Project that is openly downloadable).  
   - Until a verified source is supplied, Phases 0‑5 remain **pending**. The plan explicitly documents this gap to avoid hidden assumptions.  

## Risk Mitigation
| Risk | Mitigation |
|------|------------|
| Missing verified COD data (Principle VI) | Flag as blocking; pipeline will not start until a verified COD mirror URL is provided. |
| OOM during `encode_smiles.py` | Batch size too large for available RAM; script automatically reduces the batch size (64 → 32 → 16) and retries. |
| Permutation test exceeds timeout | Full 10 000 shuffles are guaranteed; algorithmic optimizations and parallelization ensure completion within 2 h. |
| Fewer than 500 valid records | Abort with clear warning if `< 500`; power analysis (FR‑019) will have already flagged low power. |
| Collinearity among fingerprint dimensions | Apply PCA to reduce the SMILES‑Transformer fingerprint to ≤ 20 orthogonal components before VIF calculation; flag any remaining high‑VIF features. |
| Non‑normal residuals | Use Spearman ρ as primary metric; Pearson r is reported regardless of normality to quantify linear association. |
| Multiple‑comparison inflation | Apply Bonferroni correction to the three threshold tests (α_adj ≈ 0.0167). |
| Data‑hygiene violations | Schema validation aborts on any missing required column; checksums recorded for all files. |