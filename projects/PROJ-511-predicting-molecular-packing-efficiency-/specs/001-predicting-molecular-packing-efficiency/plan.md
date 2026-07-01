# Implementation Plan: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

**Branch**: `PROJ-511-predicting-molecular-packing-efficiency` | **Date**: 2026-06-29 | **Spec**: `spec.md`

## Summary

This project implements a CPU-only pipeline to predict the **Composition-Adjusted Packing Efficiency (CAPE)** of organic crystals from SMILES representations. The approach involves downloading a pre-filtered subset of the Crystallography Open Database (COD), generating canonical SMILES via RDKit, and training three distinct models to isolate the predictive signal of topology versus 3D geometry:

1.  **Baseline Model (Primary)**: Trains a 2-layer MLP using **only** frozen SMILES-transformer embeddings to predict **CAPE**. This directly answers the research question: "Can SMILES topology predict CAPE?"
2.  **3D-Only Control Model**: Trains a 2-layer MLP using **only** 3D geometric descriptors (derived from CIF) to predict **CAPE**. This isolates the signal available purely from 3D geometry, serving as a control to quantify the specific contribution of SMILES.
3.  **Upper Bound Model (Diagnostic)**: Trains a 2-layer MLP using **both** SMILES embeddings and 3D geometric descriptors to predict **CAPE**. This establishes the theoretical maximum predictability when all available geometric information is used.

The pipeline rigorously validates statistical significance via a conditional two-stage permutation test (A substantial number of shuffles initially; if significant, proceeds to [deferred] shuffles for high resolution) and assesses robustness across packing thresholds.

The research question and method will be addressed using a permutation test with a sufficiently large number of resamples to ensure robust statistical inference, following established protocols (per Constitution Principle VII) and assessing robustness across packing thresholds.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `rdkit`, `torch` (CPU-only), `scikit-learn`, `pandas`, `pyyaml`, `jinja2`, `matplotlib`, `seaborn`, `numpy`
**Storage**: Local filesystem (`data/raw`, `data/processed`, `models`, `results`)
**Testing**: `pytest` with contract validation against YAML schemas
**Target Platform**: GitHub Actions Free Tier (Linux, CPU, 7GB RAM, no GPU)
**Project Type**: Computational Research Pipeline
**Performance Goals**: End-to-end runtime ≤ 6 hours; Dataset generation ≥ 500 records.
**Constraints**: No GPU/CUDA; No large-LLM training; Memory usage < 6GB; Strict adherence to Bondi radii.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: All random seeds pinned in `code/`. COD data fetched via verified URLs. `requirements.txt` pins versions.
- **Principle II (Verified Accuracy)**: COD source URL and Bondi (year) citation verified. `data_provenance.json` records source version.
- **Principle III (Data Hygiene)**: Raw CIFs preserved; derived CSVs checksummed. No in-place modification.
- **Principle IV (Single Source of Truth)**: All metrics in `report.html` generated directly from `results/validation_report.json` (validated against schema).
- **Principle V (Versioning)**: Artifacts hashed; `state` updated on change.
- **Principle VI (Open Crystallographic Data Integrity)**: Data sourced strictly from COD Organic Subset; provenance tags (COD ID) retained in CSV.
- **Principle VII (Model Transparency)**: 2-layer MLP (<100k params) architecture committed; permutation test (sufficient iterations) logged.

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-511-predicting-molecular-packing-efficiency/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── model.schema.yaml
    └── validation_report.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-511-predicting-molecular-packing-efficiency-/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── download_cod.py       # FR-001, FR-017
│   │   ├── generate_smiles.py    # FR-002, FR-003
│   │   └── compute_features.py   # FR-004, FR-011, FR-012, FR-013
│   ├── models/
│   │   ├── __init__.py
│   │   ├── trainer.py            # FR-005, FR-006
│   │   └── architecture.py       # FR-005, FR-019
│   ├── analysis/
│   │   ├── robustness.py         # FR-007, FR-008
│   │   └── diagnostics.py        # FR-009, FR-014, FR-015
│   └── report/
│       └── generate_report.py    # FR-010
├── data/
│   ├── raw/                      # Downloaded CIFs
│   ├── processed/                # dataset.csv, features.parquet
│   └── checksums.json            # PR-003
├── models/
│   ├── baseline_checkpoint.pt    # SMILES -> CAPE
│   ├── control_3d_checkpoint.pt  # 3D -> CAPE
│   └── upper_bound_checkpoint.pt # SMILES+3D -> CAPE
├── results/
│   └── validation_report.json    # FR-006, FR-010
└── tests/
    ├── contract/
    │   └── test_schemas.py       # Validates against contracts/
    └── integration/
        └── test_pipeline.py      # End-to-end sanity check
```

**Structure Decision**: Single-project structure with distinct `data`, `code`, `models`, and `results` directories to enforce separation of concerns and data hygiene (Constitution Principle III).

## Phase Plan

### Phase 0: Data Acquisition & Validation
1.  **Download COD Organic Subset**: Fetch the "COD Organic Subset" (pre-filtered for organic molecules) via the official COD FTP/HTTP endpoint. Filter locally for entries with ≤50 non-H atoms. Log statistics and generate `data_provenance.json` (URL, version, checksum) to satisfy FR-017.
2.  **SMILES Generation**: Parse CIFs. Extract `_chemical_structure_SMILES` if present; else generate canonical SMILES from 3D coordinates using RDKit (FR-002). Flag source.
3.  **Target Calculation**: Compute Unit-Cell Volume and Sum of VdW Volumes (Bondi radii, FR-018). Calculate **Raw PC** (diagnostic only, NOT a regression target per FR-003) and **CAPE** (FR-011).
4.  **Feature Engineering**: Extract 3D descriptors (Radius of Gyration, Asphericity, Moments) (FR-012). Extract confounders (Lattice, Temp, Solvent) (FR-013). **Crucial**: For the CAPE model, explicitly EXCLUDE `sum_vdw_volume` and `n_atoms` from the feature set to prevent circularity.
5.  **Validation**: Verify dataset size ≥500 (SC-001). Check for missing values. Generate `dataset.csv`.

### Phase 1: Model Training & Evaluation
1.  **Encoding**: Load frozen pre-trained SMILES Transformer. Encode SMILES to fixed-length vectors (FR-004). Use `torch.inference_mode` and batched processing to stay within 7GB RAM.
2.  **Dataset Split**: A standard train/validation split ratio will be employed. with fixed seed (FR-005).
3.  **Model Training**:
    -   **Baseline Model (Primary)**: Train a 2-layer MLP (≤100k params) on **SMILES embeddings ONLY** to predict **CAPE**. This isolates the SMILES topology signal for the primary research question.
    -   **3D-Only Control Model**: Train a 2-layer MLP on **3D descriptors ONLY** (excluding SMILES) to predict **CAPE**. This quantifies the baseline predictability of 3D geometry alone.
    -   **Upper Bound Model (Diagnostic)**: Train a 2-layer MLP on **SMILES embeddings + 3D descriptors** (excluding denominator terms) to predict **CAPE**. This quantifies the combined signal.
4.  **Evaluation**: Compute MAE, Pearson r, Spearman ρ for all three models (FR-006).
5.  **Significance**: Run a **conditional permutation test** on the Baseline Model's Pearson r (FR-006, FR-016):
    -   Stage 1: Run a sufficient number of shuffles.
    -   If p-value ≥ 0.05: Report p-value and stop (not significant).
    -   If p-value < 0.05: Immediately run the full set of shuffles to achieve high resolution for the significant claim.
6.  **Diagnostics**:
    -   Shapiro-Wilk test on CAPE residuals (FR-015).
    -   **Spearman's rho on CAPE residuals** (FR-015).
    -   VIF analysis on all features (FR-009).
    -   Partial correlation analysis controlling for atom-type composition (FR-014).
7.  **Comparative Analysis**: Compare Baseline vs. Control vs. Upper Bound performance to determine the specific contribution of SMILES vs. 3D geometry to CAPE prediction.

### Phase 2: Robustness & Reporting
0. **Runtime Validation**: Benchmark the pipeline on a [deferred] subset. If estimated runtime > 4 hours, abort with a clear error message to ensure SC-005 compliance.
1.  **Threshold Sweep**: Evaluate the Baseline, Control, and Upper Bound models at PC thresholds {, 0.6, 0.7} (FR-007).
2.  **Correction**: Apply Bonferroni correction to the three threshold-specific p-values (FR-008).
3.  **Report Generation**: Compile HTML report with all metrics, figures, and provenance. Ensure `validation_report.json` includes `residual_spearman_rho` and `partial_corr` (FR-010, FR-014, FR-015).
4.  **Contract Validation**: Ensure `validation_report.json` matches `contracts/validation_report.schema.yaml` (FR-019).

## Compute Feasibility Strategy

-   **Memory**: Dataset subset to ~ rows. RDKit and PyTorch CPU used in default precision. **Batched Inference**: SMILES transformer inference is performed in batches. to prevent OOM. `torch.inference_mode()` used to reduce memory overhead.
- **Runtime**: Permutation test optimized via conditional logic: [deferred] shuffles for non-significant results; [deferred] shuffles only for significant results. This ensures high resolution for claims while minimizing runtime for null results. Estimated runtime < 4 hours.
-   **Dependencies**: `torch` installed from CPU wheel only. `rdkit` via conda/pip binary.
-   **Data Download**: Use the "COD Organic Subset" (approx. moderate size) instead of the full COD archive to avoid I/O bottlenecks.

## Constitution Principle VII Alignment

Constitution Principle VII mandates a permutation test with **1,000 iterations**. The Spec (FR-016) mentions [deferred] but implies a high-resolution test. Per Constitution Principle IV (Single Source of Truth), the plan implements a **conditional two-stage test**. If the initial [deferred]-shuffle test yields a p-value < 0.05, a full [deferred]-shuffle test is executed to ensure the resolution (0.0001) required for robust significance claims. This balances computational feasibility with statistical rigor.
