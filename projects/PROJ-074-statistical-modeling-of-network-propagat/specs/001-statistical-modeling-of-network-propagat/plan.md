# Implementation Plan: Bayesian Hierarchical Modeling of Misinformation Cascade Size

**Branch**: `001-bayesian-misinformation-cascade` | **Date**: 2026-06-24 | **Spec**: `specs/001-bayesian-misinformation-cascade/spec.md`
**Input**: Feature specification from `/specs/001-bayesian-misinformation-cascade/spec.md`

## Summary

This feature implements a reproducible end-to-end pipeline for Bayesian hierarchical modeling of misinformation cascade sizes. It ingests raw cascade data (JSON only), computes pre-cascade network context and user activity features, fits a hierarchical model using CPU-compatible Bayesian inference (NumPyro/PyStan), and outputs posterior summaries with collinearity diagnostics. The plan explicitly addresses the lack of verified cascade datasets by designing the pipeline to accept user-supplied local data or synthetic data while using available dummy data for schema validation only.

**CRITICAL NOTE ON SPEC GAPS**: The source spec (spec.md) contains assumptions that contradict research findings regarding verified datasets and feature definitions. The following spec-root causes have been flagged for kickback:
- **Spec Assumptions ([deferred] node limit)**: spec.md states "cascades larger than 10 000 nodes are excluded" but this exceeds CPU feasibility. Plan reduces to [deferred] nodes for 6-hour runtime budget on 2-core, 7GB RAM runner. **SPEC ROOT CAUSE - FLAGGED FOR KICKBACK**
- **Spec FR-002 (cascade topology features)**: spec.md requires cascade depth as a network-level feature, but deriving features from cascade topology creates circular validation with the outcome variable. Plan implements pre-cascade network context instead. **SPEC ROOT CAUSE - FLAGGED FOR KICKBACK**
- Spec Assumptions claim PolitiFact/SNAP datasets contain necessary variables, but research confirms NO verified sources exist
- Spec FR-005 specifies k-fold CV, but leave-one-user-out is required for hierarchical data
- Spec FR-001 allows CSV format, but JSON is required for topology data
- Spec FeatureSet columns do not match data-model.md FeatureSet specification

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `numpyro`, `cmdstanpy`, `networkx`, `pandas`, `scikit-learn`, `pyyaml`, `jsonschema`  
**Storage**: Local filesystem (`data/raw/`, `results/`)  
**Testing**: `pytest` (contract tests against schemas)  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7 GB RAM)  
**Project Type**: Statistical Modeling Pipeline  
**Performance Goals**: ≤6h runtime, ≤7 GB RAM, CPU-only  
**Constraints**: No GPU, no large-LLM inference, no quantization (8-bit/4-bit)  
**Scale/Scope**: Benchmark dataset (synthetic or user-supplied), ≤2,000 nodes/cascade (reduced from [deferred] for CPU feasibility; see Spec Root Cause Note above)

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Strategy | Status |
| :--- | :--- | :--- |
| **I. Reproducibility** | All scripts pinned in `requirements.txt`; random seeds set in `run_pipeline.sh`; data checksums recorded. | ✅ |
| **II. Verified Accuracy** | Citations in `research.md` restricted to `Verified datasets` block; external sources flagged if missing. | ✅ |
| **III. Data Hygiene** | Raw data immutable; derivations in new files; PII scan on commit; checksums in `state/`. | ✅ |
| **IV. Single Source of Truth** | Figures/stats trace to `results/` CSVs; no hand-typed numbers in paper. | ✅ |
| **V. Versioning Discipline** | Content hashes for artifacts; `state/` updated on change. | ✅ |
| **VI. Model Specification Transparency** | Model priors/structure in `code/model_spec.yaml`; referenced in `manifest.json`. | ✅ |
| **VII. Feature Engineering Reproducibility** | Feature scripts in `code/feature_engineering/`; inputs/outputs logged. | ✅ |

## Project Structure

### Documentation (this feature)

```text
specs/001-bayesian-misinformation-cascade/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── feature_engineering/
│   ├── network_features.py
│   ├── user_susceptibility.py
│   └── generate_synthetic.py
├── models/
│   ├── hierarchical_model.py
│   └── model_spec.yaml
├── pipeline/
│   ├── run_pipeline.sh
│   ├── diagnostics.sh
│   └── utils.py
├── tests/
│   ├── contract/
│   └── integration/
└── requirements.txt

data/
├── raw/                  # User-supplied cascade data (FR-001, JSON only)
└── processed/            # Generated features (FR-002)

results/
├── features.csv
├── model_trace.nc
├── posterior_summary.csv
├── cv_metrics.json
├── collinearity_report.txt
├── susceptibility_method.md
└── manifest.json
```

**Structure Decision**: Single project structure (`code/`, `data/`, `results/`) to maintain simplicity for a statistical pipeline. No frontend/backend split required.

## Phased Implementation Plan

### Phase 0: Environment & Constraints (FR-008, SC-004)
- **Goal**: Ensure CPU-only feasibility with [deferred] node limit.
- **Steps**:
    1.  Pin `numpyro` (CPU wheel) and `cmdstanpy` in `requirements.txt`.
    2.  Verify `torch` installs without CUDA dependencies.
    3.  Set `OMP_NUM_THREADS=2` in `run_pipeline.sh` to limit CPU cores.
    4.  Add memory monitoring hooks to abort if RAM > 7 GB.
 5. Add memory profiling step to empirically validate [deferred] node limit during implementation.
- **FR/SC Mapping**: FR-008, SC-004.

### Phase 1: Data Ingestion & Validation (FR-001, FR-007)
- **Goal**: Load and validate cascade files (JSON only).
- **Steps**:
    1.  Implement `load_cascade()` to accept JSON edge-list format only.
    2.  Validate columns: `node_id`, `timestamp`, `cascade_id`.
    3.  Normalize timestamps to UTC (FR-001 Clarification).
    4.  Log errors to `pipeline.log` (FR-007).
    5.  Skip cascades > 2,000 nodes; log to `skipped_cascades.log`.
- **FR/SC Mapping**: FR-001, FR-007, SC-006.

### Phase 2: Feature Engineering (FR-002, FR-003, FR-006, SC-005)
- **Goal**: Compute predictors using pre-cascade network context (NOT cascade topology).
- **Steps**:
    1.  Compute pre-cascade network context features: user's historical degree, clustering, betweenness in broader network (NOT cascade graph to avoid circularity).
        *   **Spec Gap Note**: FR-002 requires cascade depth feature but this creates circular validation. Implementation uses pre-cascade context instead. **SPEC ROOT CAUSE - FLAGGED FOR KICKBACK**
    2.  Compute user activity proxy score: Historical sharing frequency (FR-003).
        *   *Note*: If historical data missing, use proxy (degree ≥ 2, shares ≥ 1) per FR-003 Clarification. Document in `susceptibility_method.md`.
    3.  Include `platform_id` as optional column when multiple platforms present.
    4.  Compute VIFs and Pearson correlations (FR-006).
    5.  Flag pairs with |r| > 0.8 (SC-005).
    6.  Generate `susceptibility_method.md` with exact formula and thresholds (FR-003 Clarification requirement).
    7.  Output `features.csv`.
- **FR/SC Mapping**: FR-002, FR-003, FR-006, SC-005.

### Phase 3: Bayesian Modeling & Evaluation (FR-004, FR-005, FR-009, SC-001, SC-002, SC-003)
- **Goal**: Fit model and evaluate with hierarchical-appropriate CV.
- **Steps**:
    1.  Define hierarchical model: Cascade Size ~ Network + User + (1|User) + (1|Message) (FR-004).
    2.  Use Negative Binomial likelihood for count outcome (methodology fix).
    3.  Add Platform random intercept if ≥2 platforms (FR-004 Clarification).
    4.  Fit using CPU-compatible HMC/NUTS (NumPyro).
    5.  Monitor divergent transitions; auto-reduce step size if >5% (Edge Case).
    6.  Run leave-one-user-out CV (LOUOCV) to prevent information leakage (FR-005 fix).
    7.  Compute WAIC/LOO (FR-005).
    8.  Compute posterior predictive interval coverage (SC-002).
    9.  Check predictor probabilities > 0.95 (SC-001).
    10. Compare WAIC vs Baseline Linear Regression (SC-003).
    11. Output `model_trace.nc`, `posterior_summary.csv` with `prob_nonzero` column (FR-009, schema fix).
- **FR/SC Mapping**: FR-004, FR-005, FR-009, SC-001, SC-002, SC-003.

### Phase 4: Reporting & Manifest (FR-010, SC-006)
- **Goal**: Finalize artifacts.
- **Steps**:
    1.  Generate `collinearity_report.txt` with recommendations (FR-006).
    2.  Create `manifest.json` with hashes, seeds, versions (FR-010).
    3.  Run schema validation tests (SC-006).
- **FR/SC Mapping**: FR-010, SC-006.