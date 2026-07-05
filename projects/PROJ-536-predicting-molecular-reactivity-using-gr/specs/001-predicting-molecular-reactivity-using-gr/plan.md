# Implementation Plan: Predicting Molecular Reactivity Using Graph Neural Networks and Reaction Datasets

**Branch**: `001-predict-molecular-reactivity` | **Date**: 2023-10-27 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-predict-molecular-reactivity/spec.md`

## Summary

This project implements a reproducible pipeline to predict chemical reaction yields using Graph Neural Networks (GNNs) on the USPTO reaction dataset. The core approach involves parsing SMILES strings into molecular graphs, training a lightweight Message Passing Neural Network (MPNN) on CPU-only hardware, and comparing its performance against traditional baselines (Random Forest with Morgan fingerprints, Linear Regression with molecular descriptors). The plan strictly adheres to the constraint of running on GitHub Actions free-tier (a limited CPU count, limited RAM) by utilizing sampled data subsets, CPU-optimized libraries, and early stopping.

**Critical Methodology Update**: To prevent data leakage and ensure construct validity, this plan implements a **Scaffold Split** (grouped by molecular scaffold) instead of a simple reaction class stratification. This contradicts the current text of FR-008 in `spec.md` (which mandates reaction class stratification). The plan proceeds with the Scaffold Split as the scientifically correct approach, and the spec is flagged for an immediate update to align FR-008 with this methodology.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `rdkit`, `torch` (CPU wheel), `torch-geometric` (CPU wheel), `scikit-learn`, `pandas`, `numpy`, `gnnexplainer` (or custom implementation), `conformal-prediction`  
**Storage**: Local file system (CSV/Parquet/JSON artifacts); no external DB.  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: Research pipeline / CLI tool  
**Performance Goals**: Full pipeline (parse -> train -> eval) < 6 hours on 2-core CPU.  
**Constraints**: No GPU, no CUDA, no 8-bit quantization. Data subset to fit available RAM.  
**Scale/Scope**: Subset of USPTO dataset (sampled for feasibility); MPNN with < 1M parameters.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Check | Status |
| :--- | :--- | :--- |
| **I. Reproducibility** | Plan mandates pinned seeds, `requirements.txt`, and isolated virtualenv. External data sources are fixed URLs. | ✅ Pass |
| **II. Verified Accuracy** | Plan requires citing only verified dataset URLs. **Conditional**: Pipeline halts if the verified dataset lacks the 'yield' column. | ⚠️ Conditional (Pending Phase 0 Validation) |
| **III. Data Hygiene** | Plan mandates checksums for raw data, immutable raw data, and derived artifacts in new files. | ✅ Pass |
| **IV. Single Source of Truth** | Plan defines strict data flow: Raw Data -> Parsed Graphs -> Models -> Metrics. No hand-typed numbers. | ✅ Pass |
| **V. Versioning Discipline** | Plan includes content hashes for artifacts and updates to state files. | ✅ Pass |
| **VI. Molecular Graph Validity** | Plan explicitly includes a validation step using RDKit to filter invalid SMILES and log skipped entries (FR-001). | ✅ Pass |
| **VII. Uncertainty Quantification** | Plan includes a dedicated phase for Conformal Prediction to generate intervals (FR-007, SC-003). | ✅ Pass |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-molecular-reactivity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created later)
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # Fetches USPTO subset
│   ├── parse.py             # SMILES -> Graphs (RDKit)
│   └── preprocess.py        # Feature extraction & splitting (Scaffold Split)
├── models/
│   ├── mpnn.py              # MPNN architecture
│   ├── baselines.py         # RF and LR implementations
│   └── explainers.py        # GNNExplainer logic
├── analysis/
│   ├── train.py             # Training loop with 5-fold CV
│   ├── evaluate.py          # Metrics (MAE, RMSE, R2) & Comparison (Statistical Tests)
│   ├── uncertainty.py       # Conformal prediction intervals
│   └── viz.py               # Subgraph visualization (with disclaimers)
├── config/
│   └── defaults.yaml        # Hyperparameters, paths, seeds
├── utils/
│   ├── logging.py           # Custom logger for skipped entries
│   └── metrics.py           # Metric calculators
└── main.py                  # Orchestration script

tests/
├── contract/
│   ├── test_data_contracts.py
│   └── test_model_contracts.py
├── integration/
│   └── test_pipeline.py
└── unit/
    ├── test_parsing.py
    └── test_models.py

requirements.txt
```

**Structure Decision**: A modular `src/` layout is selected to separate data ingestion, modeling, and analysis. This supports the "Reproducibility" principle by isolating dependencies and ensuring scripts can be run independently or via `main.py`. The `contracts/` directory in `specs/` holds schema definitions for validation.

## Complexity Tracking

> No violations detected. The complexity is managed by strict resource constraints (CPU-only) and modular design.

## Phase Breakdown & FR/SC Mapping

### Phase 0: Data Acquisition & Validation (Addresses FR-001, FR-002, FR-008, SC-005)
1.  **Download**: Fetch USPTO subset from verified HuggingFace URL.
2.  **Schema Validation (Hard Stop)**: **Blocking Gate**. Verify the presence of the `yield` column (continuous numeric) and `reactants_smiles`/`product_smiles` columns.
    - *If `yield` is missing*: HALT with error "Dataset lacks 'yield' column. Spec assumption A-001 violated. Regression task unachievable."
    - *If raw SMILES missing*: HALT with error "Dataset lacks raw SMILES. RF/LR baselines cannot be implemented."
    - *If `yield` is categorical*: HALT with error "Dataset 'yield' is categorical. Regression task unachievable."
3.  **Parse & Validate**: Convert SMILES to graphs using RDKit. Log invalid entries (FR-001).
4.  **Feature Extraction**: Generate atom/bond features and molecular descriptors.
5.  **Scaffold Split**: Split data by **Molecular Scaffold** (MurckoScaffold) to prevent leakage.
    - *Note*: This contradicts Spec FR-008 ("Stratified by reaction class"). The plan prioritizes scientific validity (leakage prevention) and flags the spec for update.
    - *Consistency*: The `reaction_class` field (defined in `data-model.md`) is available for reference but NOT used as the primary split key to avoid leakage.
6.  **Output**: Validated graph dataset, split indices, logging report.

### Phase 1: Model Training (Addresses FR-003, A-004, SC-004)
1.  **MPNN Implementation**: Define lightweight MPNN for CPU.
2.  **5-Fold Cross-Validation**: Train MPNN, Random Forest, and Linear Regression models using **5-Fold CV**.
    - Each fold uses a distinct Scaffold Split.
    - Early stopping (patience=5), max 200 epochs per fold.
    - Random seeds pinned for reproducibility.
3.  **Output**: Model weights (per fold), training history, baseline metrics.

### Phase 2: Evaluation & Comparison (Addresses FR-004, FR-005, SC-001, SC-002, SC-006)
1.  **Metric Aggregation**: Compute mean and standard deviation of R², MAE, RMSE across the 5 folds for all models.
2.  **Statistical Significance Test**: Perform a **paired t-test** (or Wilcoxon signed-rank test if normality fails) on the fold-level R² scores of GNN vs. Best Baseline.
    - Report p-value and a confidence interval for the R² difference.
3.  **Practical Significance Assessment**:
    - If p < 0.05 AND the lower bound of the 95% CI for the R² delta > 0.10: Flag as "Practically Significant".
    - If p < 0.05 but CI includes 0.10: Report "Statistically Significant, but effect size uncertain".
    - If p >= 0.05: Report "No Statistical Significance".
    - *Note*: This replaces the binary threshold with a statistically sound reporting mechanism.
4.  **Output**: Comparison table, statistical report (p-values, CIs), significance assessment.

### Phase 3: Explainability & Uncertainty (Addresses FR-006, FR-007, SC-003)
1.  **GNNExplainer**: Identify top subgraph patterns.
    - **Output Requirement**: All visualizations and reports MUST include a mandatory disclaimer: "These subgraphs represent associational patterns and may reflect dataset bias; they are not proven causal drivers."
    - **Entity Mapping**: Output `SubgraphPattern` objects as defined in `data-model.md` and validated against `contracts/subgraph_pattern.schema.yaml`.
2.  **Conformal Prediction**: Generate prediction intervals and calculate coverage rate.
    - **Entity Mapping**: Output `PredictionInterval` objects as defined in `data-model.md` and validated against `contracts/prediction_interval.schema.yaml`.
3.  **Output**: Ranked motif list (with disclaimer), interval CSV, coverage report.

### Phase 4: Reporting & Packaging (Addresses SC-004, Constitution Principles)
1.  **Artifact Assembly**: Combine logs, models, and metrics.
2.  **Checksums**: Generate and record hashes.
3.  **Final Validation**: Ensure all FR/SC are addressed.

## Compute Feasibility Strategy
- **Data Sampling**: The plan explicitly limits the dataset size to a subset (e.g., 10k-20k reactions) to ensure < 7GB RAM usage and < 6h runtime.
- **Model Architecture**: MPNN will use shallow layers (e.g., a few message passing steps) and small hidden dimensions.
- **Libraries**: `torch` and `torch-geometric` will be installed from CPU wheels. No CUDA dependencies.
- **Parallelism**: Only limited multi-threading (a small number of cores) allowed; no distributed training.
