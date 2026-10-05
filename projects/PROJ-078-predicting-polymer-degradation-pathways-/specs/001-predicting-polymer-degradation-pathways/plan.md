# Implementation Plan: Predicting Polymer Degradation Pathways with Graph Neural Networks

**Branch**: `001-polymer-degradation` | **Date**: 2026-06-28 | **Spec**: `specs/001-predicting-polymer-degradation-pathways/spec.md`
**Input**: Feature specification from `/specs/001-predicting-polymer-degradation-pathways/spec.md`

## Summary

This feature implements a lightweight Graph Neural Network (GNN) pipeline to predict *synthetic* polymer degradation pathways (hydrolysis, oxidation, photolysis) derived from chemical priors, using molecular structures (SMILES) and environmental conditions. The system attempts to download data from NIST Chemistry WebBook and Materials Project APIs (with exponential backoff and fallback logic), but primarily ingests verified SMILES datasets from HuggingFace (ChemDataK, etc.) due to API inaccessibility. It applies synthetic labeling where ground truth is missing, augments the dataset via edge dropout, and trains a CPU-optimized GNN (≤3 layers, hidden dim ≤128). It concludes with Integrated Gradients-based feature attribution and statistical validation (χ² test for attribution stability) to identify structure-synthetic-mechanism correlations. **Note**: Findings are simulation-based associations and cannot be used for real polymer design without experimental validation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: RDKit, PyTorch (CPU-only), PyTorch Geometric, scikit-learn, pandas, numpy, requests, scipy, datasets  
**Storage**: Local file system (CSV/Parquet for data, JSON/YAML for logs)  
**Testing**: pytest (unit, integration, contract tests)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM, no GPU)  
**Project Type**: Computational Chemistry Simulation Pipeline  
**Performance Goals**: <6h total runtime, <7GB RAM peak, <30min augmentation  
**Constraints**: CPU-only execution; no external API credentials; dataset size ~a representative subset (estimated from ChemData filtering for ester bonds)  
**Scale/Scope**: A dataset of polymer records; 3 degradation classes; 1 GNN model; 1 statistical report

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: All random seeds pinned in `code/`; external datasets fetched from canonical HuggingFace sources (verified); `requirements.txt` pins all dependencies.
- **II. Verified Accuracy**: Citations in `research.md` validated against primary sources (e.g., arXiv for confidence threshold 0.6).
- **III. Data Hygiene**: Raw data checksummed in `state/`; derivations written to new files; no PII allowed.
- **IV. Single Source of Truth**: All figures/stats trace to `data/` rows and `code/` blocks; no hand-typed numbers in reports.
- **V. Versioning Discipline**: Content hashes for all artifacts; `state/` timestamps updated on change.
- **VI. Computational Chemistry Validation**: χ² test at α=0.05 (for attribution stability); Integrated Gradients for feature attribution; 5-fold CV (or LOO if n<150).
- **VII. Small Dataset Robustness**: Data augmentation via edge dropout/subgraph sampling; metrics reported with confidence intervals.

## Project Structure

### Documentation (this feature)

```text
specs/001-polymer-degradation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-078-predicting-polymer-degradation-pathways-/
├── data/
│   ├── raw/               # Downloaded raw files (checksummed)
│   ├── processed/         # Cleaned, graph-converted data
│   └── augmented/         # Augmented training sets
├── code/
│   ├── ingest.py          # Data ingestion from NIST/Materials Project (fallback to HF)
│   ├── preprocess.py      # SMILES → Graph, missing value handling
│   ├── augment.py         # Edge dropout, subgraph sampling
│   ├── model.py           # Lightweight GNN (≤3 layers)
│   ├── train.py           # Training loop, 5-fold/LOO CV
│   ├── attribution.py     # Integrated Gradients computation
│   ├── validate.py        # χ² test, motif extraction, report generation
│   ├── utils.py           # Logging, API backoff, memory monitoring
│   ├── data_models.py     # Implements PolymerRecord, MolecularGraph classes
│   └── requirements.txt   # Pinned dependencies
├── tests/
│   ├── unit/              # Unit tests for ingest, preprocess, model
│   ├── integration/       # End-to-end pipeline tests
│   └── contract/          # Schema validation tests
├── state/
│   ├── setup_log.txt      # Directory listing with timestamp (T001b)
│   ├── artifact_hashes.yaml # Checksums for data files
│   └── current_stage.yaml # Stage tracking
└── docs/
    └── usage.md           # User guide, quickstart instructions
```

**Structure Decision**: Single-project structure with modular `code/` scripts for each pipeline stage. Chosen for simplicity, reproducibility, and alignment with CI runner constraints.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Data augmentation (increased magnitude) | Small dataset requires robustness; Constitution VII mandates augmentation. | No augmentation would lead to overfitting and unreliable CV metrics. |
| 5-fold CV (or LOO if n<150) | Small sample size; Constitution VI mandates cross-validation. | Single train/test split would not capture variance; LOO used if n<150. |
| χ² test with iterations | Statistical validation of attribution stability required; Constitution VI mandates significance testing. | No statistical test would render findings unverified. |
| Synthetic Labels | Real degradation pathway labels are unavailable in verified sources; required to train any model. | Without labels, no supervised learning is possible. |

## Implementation Phases

### Phase 0: API Source Verification (T051)
- **T051**: Implement API Source Verification.
  - Logic: Attempt to fetch NIST Chemistry WebBook and Materials Project records for polyesters with documented degradation.
  - Backoff: Implement exponential backoff with maximum 3 retries (FR-009).
  - Fallback: If APIs fail (rate limit, no data, or unreachable), log failure and switch to verified HuggingFace datasets (ChemData700K, etc.).
  - Output: Log of API attempts and final data source selection.

### Phase 1: Data Ingestion & Preprocessing (T013-T020)
- **T013**: Implement `ingest.py` for data download.
  - Logic: Fetch from HuggingFace (primary) or NIST/Materials Project (fallback).
  - Filtering: Retain only polyester records using RDKit to detect ester bonds (`C(=O)O`) (FR-001, SC-006).
 - Labeling: Apply synthetic label distribution (dominant hydrolysis, [deferred] oxidation, [deferred] photolysis) if labels missing (FR-001, FR-008).
  - Flagging: Flag records missing labels for manual curation (FR-001, FR-008).
  - Halt Logic: If N=0 after filtering, halt with fatal error. If N>0 but all flagged, proceed with synthetic labels and log warning.
- **T014**: Identify records missing labels.
  - Logic: Scan ingested data for missing `degradation_pathway`.
  - Action: Apply synthetic labels or flag for curation. Calculate ratio of flagged records (SC-010).
- **T015**: Implement `preprocess.py` for SMILES → Graph.
  - Logic: Convert SMILES to molecular graphs using RDKit.
  - Missing Values: Impute missing environmental conditions (temp, pH, UV) with defaults (standard laboratory temperature, neutral pH, and absence of UV) and flag (FR-002, SC-006).
  - Invalid SMILES: Skip invalid SMILES strings, log them, and continue (FR-009).
- **T016a**: Save raw ingested dataset.
  - Logic: Save filtered/flagged records to `data/raw/` with checksums.
- **T016b**: Save processed graph dataset.
  - Logic: Save graph-converted data to `data/processed/`.
- **T016c**: Save pre-augmentation dataset.
  - Logic: Save dataset before augmentation for baseline comparison.
- **T017a**: Define Power Analysis Logic.
  - Logic: Define method to calculate statistical power for n<150.
- **T017b**: Power Analysis Execution (SC-004).
  - Logic: Execute power analysis. If n<150, trigger warning and switch to LOO validation later.
- **T019**: Data Integrity Check (SC-006).
  - Logic: Verify checksums and calculate ingestion success rate. Ensure ≥95% success rate.
- **T019b**: Metadata Generation.
  - Logic: Generate metadata including power analysis warnings and flag ratios.
- **T020**: Add logging for data ingestion.
  - Logic: Log all ingestion, filtering, and flagging actions.

### Phase 2: Data Augmentation (T025a-T025c)
- **T025a**: Implement exact 2x expansion.
  - Logic: Apply edge dropout and subgraph sampling to expand dataset by **exactly 2x** (FR-004).
- **T025b**: Augmentation Validation.
  - Logic: Verify augmented dataset size and topology preservation.
- **T025c**: Augmentation Runtime Measurement (SC-009).
  - Logic: Measure augmentation time. Ensure <30 minutes.

### Phase 3: Model Training (T024-T033)
- **T024**: Implement `model.py`.
  - Logic: Define lightweight GNN architecture (≤3 layers, hidden dim ≤128) (FR-003).
- **T028**: Training (SC-001, FR-009).
  - Logic: Train model. If n<150 (from T017b), switch to leave-one-out (LOO) validation. Otherwise, use 5-fold CV.
  - Metrics: Calculate macro-F1 and loss convergence (|loss_t - loss_{t-5}| / loss_{t-5} < 0.05).
- **T029**: Compute feature importance (FR-005).
  - Logic: Compute Integrated Gradients scores for all test samples.
- **T030**: Ester Attribution Validation (SC-005).
  - Logic: Verify ester bonds are in top [deferred] attribution scores for ≥90% of hydrolysis cases.
- **T031**: Save model checkpoints.
  - Logic: Save model weights after validation.
- **T032**: Generate test-set predictions (SC-001).
  - Logic: Generate predictions and measure macro-F1 against held-out test set.
- **T033**: Add logging for training.
  - Logic: Log training metrics and validation strategy used.

### Phase 4: Statistical Validation & Reporting (T034-T037)
- **T034**: Unit test for permutation test.
- **T035**: Unit test for motif extraction.
- **T036**: Integration test for full report.
- **T037**: Scientific Validation & Report Generation (FR-006, FR-007, SC-002, SC-007, SC-011, SC-012).
  - Logic: Perform χ² test with ≥1000 iterations of shuffled motif importance to validate attribution stability (not external truth).
  - Report: Generate final report containing:
    - Top 3-5 structural motifs with correlation strength (SC-007, SC-012).
    - Valid p-value from χ² test (SC-011).
    - List of low-confidence predictions (softmax <0.6) and percentage correctly flagged (SC-008).
    - Power analysis warning if n<150.
    - Attribution stability results (not causal claims).

### Phase 5: Final Checks (T043-T056)
- **T043**: Generate README.
- **T044**: Generate docs/usage.md.
- **T045**: Refactor code/utils.py.
- **T046**: Refactor code/data_models.py.
- **T047**: Implement memory monitoring (SC-003).
- **T048**: Integrate subsampling trigger.
- **T049**: Additional unit tests.
- **T050**: Run quickstart.md validation.
- **T053**: Statistical Power Analysis Enhancement.
- **T054**: Motif Significance Validation.
- **T055**: Confidence Interval Estimation.
- **T056**: Data Visualization.
- **T057**: Compute Feasibility Measurement (SC-003).
  - Logic: Measure total runtime and peak RAM usage. Verify ≤6h runtime and ≤7GB RAM.

## Complexity & Constraints

- **CPU-First**: All methods (GNN, Integrated Gradients, χ² test) are tractable on CPU.
- **GPU Escape Hatch**: Not required; lightweight GNN and small dataset fit within 7GB RAM.
- **Streaming**: Use `datasets.load_dataset(..., streaming=True)` for large SMILES files to avoid OOM.
- **Synthetic Data**: Explicitly acknowledged as simulation data; no claims of real-world causal discovery.

## Risk Mitigation

- **API Failure**: Fallback to HuggingFace datasets (T051).
- **Small Dataset**: LOO validation and power analysis warning (T017b, T028).
- **Invalid SMILES**: Skip and log (T015).
- **Memory Limit**: Subsample if >7GB RAM (T048).
- **Synthetic Labels**: Explicitly flagged in report as simulation-based (T037).