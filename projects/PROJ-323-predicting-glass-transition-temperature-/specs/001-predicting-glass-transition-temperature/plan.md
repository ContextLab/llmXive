# Implementation Plan: Predicting Glass Transition Temperature from Compositional Descriptors with Explainable Boosting Machines

**Branch**: `001-predict-tg-from-composition` | **Date**: 2026-10-11 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-predict-tg-from-composition/spec.md`

## Summary
The project builds a reproducible pipeline that (1) ingests open polymer structural data, (2) engineers chemically-informed descriptors, (3) (conditionally) trains an Explainable Boosting Machine (EBM) to predict glass-transition temperature ($T_g$) when a real $T_g$ dataset is available, (4) generates interpretable visualizations, and (5) validates model explanations against **Fractional Free Volume (FFV) and Chain Stiffness** computed via Van Krevelen group contributions, per spec.md FR-005 / SC-002 / Principle VI. The pipeline respects compute limits (≤ 6 h, ≤ 7 GB RAM) and runs CPU-only on GitHub Actions.

### Critical Data Availability Issue (spec-root kickback)
- No open, programmatically downloadable polymer $T_g$ dataset exists in the verified-datasets list. The spec's mandated sources (Polymer Genome Project, NIST WebBook) are not verifiably fetchable by the CI runner.
- **FR-001 is BLOCKED — spec-root kickback.** The pipeline is demonstrated using the verified open SMILES dataset for structural descriptor engineering; all $T_g$-dependent analyses (model training, performance evaluation, sensitivity) are **deferred** and gracefully skipped (with a clear log message) until a real, open $T_g$ source is added to the spec's verified dataset list. No synthetic or placeholder $T_g$ values are fabricated.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I (Data Integrity) | All raw files are downloaded via HTTPS, SHA-256 checksummed, and stored under `data/`. |
| II (Verified Accuracy) | No hard-coded literature values; any external numbers are read from files in `data/`. |
| III (Local Data) | Validation dataset (`data/physical_properties.csv`) resides in `data/`. |
| IV (Independent Validation) | Physical metrics (FFV, Chain Stiffness) are derived solely from molecular structure via Van Krevelen group contributions, not from $T_g$. |
| V (Reproducibility) | Random seeds are pinned; every transformation writes a new file with documented provenance and checksum. |
| VI (Physical Consistency Validation) | Feature importance will be correlated with FFV and Chain Stiffness from `data/physical_properties.csv` (deferred until Tg data available). Note: the ratified project constitution names WLF constants (C₁, C₂) as the Principle VI metric, which diverges from spec.md FR-005/SC-002 (FFV/Chain Stiffness); this divergence is flagged for spec-root kickback. The plan follows spec.md (FFV/Chain Stiffness) as primary, since no open WLF dataset exists. |
| VII (Numerical Stability) | Median imputation + `StandardScaler` applied; sensitivity analysis (deferred) will perturb top descriptors ±10 %. |
| SSoT (Single Source of Truth, constitution "IV" — cited without a Roman numeral to avoid collision with Principle IV above) | Each figure, statistic, and model artifact logs the exact input data checksum and the code file that produced it (SSoT log step in every phase). |

*All satisfiable principles are satisfied; FR-001 is BLOCKED pending an open $T_g$ data source (spec-root kickback).*

## Phase Mapping (FR / SC coverage)

| Phase | Tasks | Covered FR | Covered SC | Notes |
|-------|-------|------------|------------|-------|
| **0️⃣ Data Ingestion & Integrity** | • Download open SMILES parquet and open physical-properties parquet (verified URLs)  <br>• Verify SHA-256 checksums  <br>• Log retries (max 3, 30 s back-off) | **FR-001 (BLOCKED — spec-root kickback: no open Tg dataset exists; only the verified SMILES/FFV sources are ingested)** | – | Implements Principles I & II. |
| **1️⃣ Descriptor Engineering** | • Parse SMILES with RDKit (CPU-only)  <br>• Compute elemental mass fractions, functional-group counts, estimated MW  <br>• Median imputation & `StandardScaler`  <br>• Save `feature_matrix.csv` (no $T_g$ column) | FR-002, FR-006 | – | Aligns with Principle VII. |
| **2️⃣ Physical Property Calculation** | • Apply Van Krevelen formulas to compute **Fractional Free Volume** and **Chain Stiffness**  <br>• Store in `data/physical_properties.csv` with checksum | FR-008 | – | Primary validation metrics per spec.md FR-005/SC-002. |
| **3️⃣ Model Training** *(conditional)* | • If a real $T_g$ column exists, train EBM (interpret≥0.4) with main effects + 2-way interactions  <br>• 5-fold CV; grid-search λ ∈ {0.01,0.1,1.0}, interaction depth ∈ {1,2}  <br>• Save best model (`model.pkl`) and metadata  <br>• If $T_g$ missing, **skip gracefully** with a clear log message | FR-003 (deferred — blocked by FR-001 data gap) | **SC-001** (deferred), **SC-004** (deferred), **SC-005** (deferred) | Graceful skip-with-log, consistent with quickstart.md and research.md. |
| **4️⃣ Interpretability & Plots** *(conditional)* | • Extract main effects & interactions via `interpret.globals.ebm`  <br>• Generate Partial Dependence Plots for all main effects  <br>• Generate shape-function plots for top 3 interactions  <br>• Log SSoT provenance for each figure | FR-004 (deferred — blocked by FR-001 data gap) | SC-005 (deferred) | |
| **5️⃣ Validation & Sensitivity** *(conditional)* | • **Primary validation (per spec.md FR-005/SC-002)**: correlate top-3 feature importances with **FFV and Chain Stiffness** from `data/physical_properties.csv` (Pearson $r$). Apply Bonferroni correction (α = 0.05/3).  <br>• **Sensitivity analysis** (deferred): perturb top-3 descriptors ±10 % (Gaussian noise, σ = 0.1 × mean) and record std-dev of $T_g$ shifts.  <br>• Summarize in `validation_report.md`.  <br>• Note: the ratified constitution's Principle VI names WLF constants (C₁, C₂) as the validation metric; no open WLF dataset exists, so this path is **flagged as a spec/constitution divergence for kickback**, not silently substituted. | FR-005 (deferred — blocked by FR-001 data gap) | **SC-002** (deferred), **SC-003** (deferred) | |
| **6️⃣ Resource Guardrails** | • Pre-run size check: if raw data > 7 GB → stream or sample (seed = 42).  <br>• Enforce 6 h timeout via GitHub Actions `timeout-minutes`.  <br>• Log RAM usage; fallback to sampled subset if limit exceeded. | FR-007 | SC-004 (deferred) | |
| **7️⃣ Contract Generation** | • Emit `contracts/feature_matrix.schema.yaml` (validates engineered descriptors).  <br>• Emit `contracts/model_output.schema.yaml` (validates model artifact when produced).  <br>• These contracts support automated data-contract compliance checks; they do **not** by themselves satisfy any FR. | – (supporting task only) | – | |

All functional requirements FR-001–FR-008 are addressed in the mapping. **FR-001 is BLOCKED — spec-root kickback** (no open $T_g$ dataset exists in the verified-datasets list; the spec's mandated sources are not programmatically downloadable by the CI runner). FR-003, FR-004, and FR-005 are deferred because they depend on a real $T_g$ target. Success criteria SC-001–SC-005 are mapped to phases but marked **[deferred]** where they depend on real $T_g$ data.

## Project Structure
```text
specs/001-predict-tg-from-composition/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── feature_matrix.schema.yaml
    └── model_output.schema.yaml

code/
├── ingest.py                # data download & checksum
├── descriptors.py           # RDKit feature extraction
├── physical_properties.py   # Van Krevelen FFV & stiffness
├── train_ebm.py             # conditional EBM training
├── interpret.py             # plots & importance
├── validate.py              # FFV/Chain Stiffness validation & sensitivity
└── utils.py                 # logging, retry, sampling, SSoT provenance

data/
├── raw/                     # downloaded source files (read-only)
├── processed/               # intermediate CSV/Parquet files
└── physical_properties.csv  # generated FFV & stiffness (Van Krevelen)

outputs/
├── models/
│   └── ebm_model.pkl        # created only when Tg data available
├── figures/
│   ├── pdp_<feature>.png
│   └── interaction_<pair>.png
└── reports/
    └── validation_report.md
```

## Complexity Tracking
The plan respects every satisfiable constitutional principle, avoids circular validation, follows spec.md's FFV/Chain-Stiffness validation path (flagging the constitution's WLF divergence for kickback), and clearly defers any step that cannot be executed without an open $T_g$ dataset. No unnecessary scaffolding tasks are added.