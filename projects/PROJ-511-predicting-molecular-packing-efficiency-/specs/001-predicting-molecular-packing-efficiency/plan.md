# Implementation Plan: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

**Branch**: `PROJ-511-predicting-molecular-packing-efficiency` | **Date**: 2026-07-03 | **Spec**: `spec.md`

## Summary

This plan implements a CPU-only pipeline to predict the **Raw Packing Coefficient (PC_raw)** of organic crystals from SMILES strings. The approach involves downloading crystallographic data from the Crystallography Open Database (COD), generating or extracting SMILES, computing 3D geometric descriptors, and training a lightweight 2-layer MLP. 

**Critical Revisions to Address Tautology and Circularity**:
1.  **Target Redefinition**: The primary regression target is now **PC_raw** (Unit-cell volume / Sum of vdW volumes). The Composition-Adjusted Packing Efficiency (CAPE) is retained only as a diagnostic metric. This prevents the mathematical tautology where the target (CAPE) is a direct function of the predictors (atom counts).
2.  **Predictor Pruning**: `atom_count` and `atom_type_counts` are **removed** from the primary feature matrix used for regression. They are used only in a separate residual analysis to quantify compositional effects.
3.  **Geometry Baseline**: A "Geometry-Only" baseline model is introduced to establish the theoretical upper bound of prediction using 3D descriptors. The SMILES model's performance is compared against this baseline to isolate the topological signal.
4.  **Phase Reordering**: SMILES encoding (FR-004) is now explicitly completed in Phase 0, ensuring the `fingerprint_vector` is present before VIF diagnostics (FR-009) run in Phase 1.
5.  **Memory Management**: Embedding generation uses a batched, streaming approach (batch size 64) to ensure <7GB RAM usage.
6. **Statistical Rigor**: The permutation test baseline is set to [deferred] shuffles (per FR-016), with a fallback to a predefined default threshold (per Constitution VII) if a hard timeout occurs.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `rdkit`, `torch` (CPU build), `scikit-learn`, `pandas`, `pyyaml`, `datasets` (HuggingFace), `jinja2` (for HTML report), `joblib` (for parallel permutation tests).
**Storage**: Local `data/` directory for CSV artifacts; `code/` for scripts.
**Testing**: `pytest` for unit tests; integration tests via end-to-end pipeline execution.
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM).
**Project Type**: Data science pipeline / CLI.
**Performance Goals**: End-to-end execution ≤ 6 hours; model training ≤ 30 minutes on CPU; Permutation test ≤ 2 hours (with timeout fallback).
**Constraints**: No GPU usage (unless auto-offloaded to Kaggle for specific transformer inference if CPU fails, but spec mandates CPU-first); strict memory limits (<7GB RAM); no synthetic data.
**Scale/Scope**: Dataset target ≥ 500 records; Model parameters < 100k.

## Constitution Check

*Gates determined based on `constitution.md`*

1.  **Principle I (Reproducibility)**: All random seeds (numpy, torch, python) will be pinned in `code/utils/random.py`. External datasets are fetched via deterministic URLs from the verified list (`cod/cod`).
2.  **Principle II (Verified Accuracy)**: All citations (Bondi radii, COD source) are cross-referenced with the verified facts and dataset block. No fabricated URLs. The specific dataset loader `cod/cod` is verified.
3.  **Principle III (Data Hygiene)**: `data/` files will be checksummed (SHA-256) upon creation. Raw downloads are preserved; derived CSVs are new files.
4.  **Principle IV (Single Source of Truth)**: All statistics in the final report are generated programmatically from the validation CSV; no hand-typed numbers.
5.  **Principle V (Versioning)**: Content hashes for `data/` and `code/` will be recorded in the project state file.
6.  **Principle VI (Open Crystallographic Data Integrity)**: Data sourced exclusively from the verified COD HuggingFace dataset (`cod/cod`). Provenance tags (COD ID) retained in every row. A `source_log.json` records the exact version and loader.
7. **Principle VII (Model Transparency)**: Model architecture (2-layer MLP < 100k params) and training script will be committed. Permutation test execution follows FR-016 ([deferred] shuffles) with a fallback to [deferred] if runtime constraints prevent the full count, as mandated by Constitution Principle VII, with the actual count logged.

## Project Structure

```text
projects/PROJ-511-predicting-molecular-packing-efficiency-/
├── code/
│   ├── __init__.py
│   ├── utils/
│   │   ├── random.py          # Seed management
│   │   ├── rdkit_helpers.py   # SMILES gen, 3D descriptor calc
│   │   └── stats.py           # VIF, permutation test, Shapiro-Wilk
│   ├── download_cod.py        # FR-001: Fetch and filter COD
│   ├── generate_smiles.py     # FR-002: Extract/Generate SMILES
│   ├── compute_descriptors.py # FR-012: 3D geometry metrics
│   ├── encode_smiles.py       # FR-004: SMILES transformer encoding
│   ├── generate_confounders.py# FR-011/FR-014: Atom-type counts (for residual analysis)
│   ├── train_model.py         # FR-005: MLP training (PC_raw target)
│   ├── evaluate_model.py      # FR-006, FR-008, FR-009, FR-014, FR-015
│   ├── sensitivity_analysis.py# FR-007, FR-008: Threshold sweep
│   ├── report_generator.py    # FR-010: HTML report
│   └── requirements.txt
├── data/
│   ├── raw/                   # Unmodified downloads
│   ├── processed/             # Filtered CSVs, features
│   └── artifacts/             # Model weights, final report
├── specs/
│   └── plan.md                # This file
├── contracts/
│   ├── dataset.schema.yaml    # Input/Intermediate CSV schema
│   ├── model.schema.yaml      # Model checkpoint schema
│   └── validation_report.schema.yaml # Output metrics schema
└── tests/
    ├── unit/
    └── integration/
```

**Structure Decision**: Single-project structure (`code/`, `data/`, `contracts/`) is selected to match the CLI/pipeline nature of the work. This minimizes overhead and aligns with the "reproducible pipeline" requirement.

## Phase Execution Order (Addressing Unresolved Concerns)

To resolve the producer-consumer conflicts, memory constraints, and circularity risks:

### Phase 0: Data Acquisition, Feature Engineering & Source Verification
*   **Download COD Data (FR-001)**: Fetch from `datasets.load_dataset("cod/cod", ...)`.
*   **Record Source Metadata (FR-017)**: Log the exact dataset version and loader string to `source_log.json`. **Validation**: Check for `_cell_volume`, `_symmetry_space_group`, and `_chemical_solvent` (or fallback) in the first 100 rows. Abort if missing.
*   **Filter & Validate (T016, T019)**: Apply `atom_count <= 50` filter. Validate schema fields (`_cell_volume`, etc.) exist. Output `data/processed/filtered_cod.csv`.
*   **Generate SMILES (FR-002)**: Extract or generate canonical SMILES using RDKit. Output `data/processed/with_smiles.csv`.
*   **Compute 3D Descriptors (FR-012)**: Radius of gyration, asphericity, moments of inertia. Output `data/processed/with_descriptors.csv`.
*   **Encode SMILES (FR-004)**: Run frozen SMILES transformer in **batches of 64**. Embeddings are written to disk incrementally (JSONL chunks) to avoid OOM, then merged. **Output**: `data/processed/with_embeddings.csv`. **Validation**: Ensure `fingerprint_vector` column is populated and non-null.
*   **Generate Atom-Type Count Features (FR-011/FR-014)**: Create confounder features for composition (used for residual analysis, not primary regression). Output `data/processed/with_confounders.csv`.
*   **Finalize Feature Matrix**: Merge all intermediate outputs into `data/processed/full_feature_matrix.csv`. **Crucial**: This matrix includes SMILES, fingerprints, 3D descriptors, and target (PC_raw), but **excludes** atom counts from the predictor set for the primary model.
*   *Output*: `data/processed/full_feature_matrix.csv` (Contains SMILES, fingerprints, 3D descriptors, target PC_raw).

### Phase 1: Feature Validation & Target Distribution Check
*   **Execute VIF Diagnostics (FR-009)**: Run on the *complete* feature matrix (fingerprints + 3D descriptors). Flag features with VIF > 5.
*   **Target Distribution Check**: Perform Shapiro-Wilk test on PC_raw. If non-normal, log the deviation and prepare non-parametric power estimates.
*   *Output*: `data/processed/vif_report.json`, `data/processed/target_stats.json`.

### Phase 2: Model Training
*   **Train 2-layer MLP (FR-005)**: Use the validated feature matrix to predict **PC_raw**.
*   **Geometry Baseline**: Train a secondary model using only 3D descriptors to establish the geometric upper bound.
*   *Output*: `model.pt`, `geometry_baseline.pt`.

### Phase 3: Evaluation & Robustness
*   **Compute Metrics (FR-006)**: MAE, r, ρ, Shapiro-Wilk on residuals.
* **Permutation Test (FR-016)**: Run **[deferred] shuffles** using `joblib` with `n_jobs=-1`.
    *   **Timeout Strategy**: Hard timeout set to 2 hours. If exceeded, reduce shuffles to the maximum feasible count (minimum 1,000 per Constitution Principle VII), log the actual count, and flag the deviation in the report.
*   **Sensitivity Analysis (FR-007)**: Sweep thresholds {0.5, 0.6, 0.7} on PC_raw.
*   **Bonferroni Correction (FR-008)**: Apply to p-values.
*   **Residual Analysis (FR-014)**: Correlate model residuals with atom-type composition to quantify the unexplained compositional signal (non-circular).
*   **Generate HTML Report (FR-010)**.

## Compute Feasibility & Data Strategy

*   **CPU-First**:
    *   **SMILES Transformer**: `transformers` library with `device="cpu"`. **Batch Size = 64**. Embeddings are written to disk in chunks to ensure total memory usage < 7GB. A memory check is performed before starting.
    *   **MLP**: `torch.nn.Sequential` (Input -> 64 -> 32 -> 1). < 100k params.
 * **Permutation Test**: 10,000 shuffles. **Strategy**: Use `joblib` with `n_jobs=-1` to parallelize across multiple cores. Hard timeout set to 2 hours; if exceeded, reduce shuffles to the maximum feasible count (min [deferred]), log the actual count, and flag the deviation.
*   **GPU Escape Hatch**: If transformer inference OOMs despite batching, the execution agent will detect the error and re-run on a Kaggle GPU (8-bit quantization if necessary).
*   **Dataset Strategy**:
    *   **Source**: `datasets.load_dataset("cod/cod", ...)` (Official COD HuggingFace mirror).
    *   **Variable Fit Verification**: The pipeline includes a **Schema Validation Step** in Phase 0. It inspects the schema of the verified COD JSONL. If `temperature_K` is missing, the pipeline proceeds with a `None` value for that feature, flagging it in the VIF diagnostics and model training (covariate missingness handling). If critical fields like `_cell_volume` are missing, the pipeline aborts.
    *   **Streaming**: The JSONL is streamed. A filter mask is applied in a single pass. Embeddings are generated in batches to respect memory limits.

## Data Availability & Integrity

*   **Source Verification**: The COD dataset loader `cod/cod` is verified to contain the necessary fields. A `source_log.json` file is generated in Phase 0 recording the dataset version hash.
*   **Memory Safety**: The embedding generation step uses a streaming approach (batch size 64) to ensure the 7GB RAM limit is not exceeded.
*   **Feasibility**: The target of ≥ 500 records is easily met by the COD dataset after filtering for organic molecules < 50 atoms.

## Risk Mitigation

*   **Circularity (Tautology)**: The target is redefined to **PC_raw**, removing the compositional denominator from the prediction target. Atom counts are removed from the primary predictor set. Residual analysis is used to study compositional effects, breaking the mathematical identity loop.
*   **Non-Normality**: If PC_raw is non-normal, the plan uses bootstrapping for confidence intervals and Spearman's rho as the primary metric.
* **Time Limits**: The permutation test has a strict timeout and fallback logic (min [deferred] shuffles) to ensure the pipeline completes within 6 hours.
