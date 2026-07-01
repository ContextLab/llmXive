# Implementation Plan: Predicting Molecular Crystal Packing from Structural Descriptors

**Branch**: `001-predicting-crystal-packing` | **Date**: 2024-05-21 | **Spec**: `specs/001-predicting-crystal-packing/spec.md`
**Input**: Feature specification from `/specs/001-predicting-crystal-packing/spec.md`

## Summary

This project implements a machine learning pipeline to predict the packing coefficient of molecular crystals and classify dominant intermolecular interaction types using only single-molecule descriptors (volume, surface area, dipole, H-bond counts, PSA) as input. The approach involves ingesting crystallographic data (COD), computing descriptors via RDKit, training Random Forest and Gradient Boosting regressors on CPU, and validating performance against a mean baseline with statistical rigor (paired t-tests, multiple-comparison correction). The pipeline is constrained to run within GitHub Actions free-tier limits (limited CPU, restricted RAM, 6h).

**Critical Scientific Control**: To address the tautology risk (predicting `V_mol / V_cell` using `V_mol`), the plan includes a **Control Analysis** phase that excludes geometric descriptors (Volume, Surface Area) to test if interaction-specific descriptors (Dipole, H-bonds) drive packing efficiency.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `rdkit`, `scikit-learn`, `pandas`, `numpy`, `requests`, `pyyaml`, `matplotlib`, `seaborn`
**Storage**: Local file system (`data/`, `results/`); no external database.
**Testing**: `pytest` (unit tests for descriptor computation, integration tests for pipeline flow).
**Target Platform**: Linux (GitHub Actions Runner).
**Project Type**: Data Science / Computational Chemistry Pipeline.
**Performance Goals**: Complete full pipeline (ingest 1k samples, train 2 models, evaluate) within 6 hours on 2 vCPU.
**Constraints**: No GPU; no heavy LLM inference; memory usage < 7GB; strict adherence to reproducibility (random seeds).
**Scale/Scope**: [deferred] organic small molecules (target); 6 molecular descriptors; 2 regression models.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Mapping to Plan Phase/Script | Verification Method |
|-----------|------------------------------|---------------------|
| **I. Reproducibility** | Phase 0: `requirements.txt` pins; `random_state=42` in all scripts. | Re-run on fresh runner yields identical `results/metrics.json`. |
| **II. Verified Accuracy** | Phase 0: COD bulk download URL is the canonical source. | Script fetches from official COD mirror; no fabricated URLs. |
| **III. Data Hygiene** | Phase 1: `01_ingest_and_descriptors.py` generates SHA-256 checksums. | Checksums recorded in `state/projects/PROJ-238.../artifact_hashes`. |
| **IV. Single Source of Truth** | Phase 2: `02_train_models.py` outputs JSON metrics. | No hand-typed numbers in `paper/`; all stats from JSON. |
| **V. Versioning Discipline** | Phase 0: `requirements.txt` and `state/` updates. | Content hashes updated on artifact change. |
| **VI. Descriptor Consistency** | Phase 1: `utils/descriptors.py` uses RDKit v2023.9.1+. | Script version-controlled; deterministic CSV output. |
| **VII. Eval Transparency** | Phase 3: `03_evaluate_and_report.py` logs hyperparams, seeds, Bonferroni correction. | JSON summary includes all config and statistical test details. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-crystal-packing/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
└── contracts/ # Phase 1 output (Generated from data-model.md)
 ├── dataset.schema.yaml
 └── results.schema.yaml
```

### Source Code (repository root)

```text
code/
├── 01_ingest_and_descriptors.py # Phase 1: Ingestion, Descriptor Calc, Missing Data Handling
├── 02_train_models.py # Phase 2: Split, Train RF/GB, Baseline
├── 03_evaluate_and_report.py # Phase 3: Metrics, T-Test, Bonferroni, Control Analysis, Interaction Classification
├── utils/
│ ├── descriptors.py # RDKit wrapper
│ ├── data_loaders.py # COD fetcher
│ └── metrics.py # Statistical tests
└── requirements.txt

data/
├── raw/ # Downloaded CIFs (checksummed)
├── descriptors/ # Derived CSVs (checksummed)
└── processed/ # Train/Val/Test splits

results/
├── metrics.json # R², MAE, p-values, Bonferroni correction
├── feature_importance.png # Permutation importance plot
├── sensitivity_report.md # LOFO analysis
└── interaction_classification.md # Heuristic proxy report

state/
└── projects/PROJ-238-predicting-molecular-crystal-packing-fro.yaml
 └── artifact_hashes # SHA-256 of data files
```

**Structure Decision**: Single project structure selected to minimize overhead for a data pipeline. All scripts are sequential and dependency-free regarding external services, fitting the "CLI/Data Science" pattern.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is contained within a single script pipeline. | N/A |

## Implementation Phases

### Phase 0: Environment & Data Verification
- **Goal**: Setup environment and verify COD fetch mechanism.
- **Tasks**:
 1. Create `requirements.txt` with pinned versions (`rdkit==2023.9.1`, `scikit-learn==1.3.0`).
 2. Implement `utils/data_loaders.py` to fetch a sample of COD CIFs from the official COD bulk download URL (e.g., ` or verified mirror).
 3. Verify that the fetched CIFs contain unit cell parameters and valid organic molecules.
 4. **Constitution Check**: Ensure no fabricated URLs; use only the canonical COD source.

### Phase 1: Data Ingestion & Descriptor Computation (FR-001, FR-002, FR-007)
- **Goal**: Create the foundational dataset with computed descriptors and derived targets.
- **Tasks**:
 1. **Ingest**: Download CIFs for a random sample of organic small molecules.
 2. **Parse**: Extract unit cell parameters ($a, b, c, \alpha, \beta, \gamma$) to calculate Unit Cell Volume ($V_{cell}$).
 3. **Descriptor Computation**: Use RDKit to compute Volume, Surface Area, Dipole, HBA, HBD, PSA.
 - *Missing Data Handling*: If auxiliary descriptors (e.g., Dipole) are missing, impute with the **training set median** and flag the row. If `packing_coefficient` (target) is missing, **exclude** the row and log the count.
 4. **Derive Target**: Calculate `packing_coefficient` = $V_{mol} / V_{cell}$.
 5. **Filter**: Exclude entries where `packing_coefficient` $\notin [0.5, 1.0]$ or MW > 1000 Da.
 6. **Data Hygiene**: Generate SHA-256 checksums for raw CIFs and derived CSVs; record in `state/`.

### Phase 2: Model Training & Baseline Comparison (FR-003, FR-004, FR-005)
- **Goal**: Train models and establish statistical significance.
- **Tasks**:
 1. **Split**: Stratified split by **packing_coefficient** (target variable) into 70/15/15 Train/Val/Test.
 - *Validation*: Run Kolmogorov-Smirnov test on the target distribution across splits ($p > 0.05$).
 2. **Train**: Train Random Forest and Gradient Boosting regressors (default hyperparams, `random_state=42`).
 3. **Baseline**: Train Mean Predictor.
 4. **Control Analysis**: Train a secondary model **excluding** Volume and Surface Area to test if interaction descriptors (Dipole, H-bonds) drive packing efficiency.
 5. **Evaluate**: Compute R², MAE, RMSE.
 6. **Statistical Test**: Perform paired t-test (Model vs Baseline) on test set predictions.
 - *Correction*: Apply **Bonferroni correction** ($\alpha_{corrected} = 0.05 / 2$) for multiple comparisons.

### Phase 3: Feature Importance, Sensitivity & Interaction Classification (FR-006, FR-008, SC-003, SC-005)
- **Goal**: Interpret model and classify interactions.
- **Tasks**:
 1. **Feature Importance**: Generate **Permutation Importance** (not Gini) to account for collinearity (Volume vs Surface Area).
 2. **Sensitivity Analysis**: Perform **Leave-One-Feature-Out (LOFO)** analysis. Measure R² drop when each feature is removed.
 - *Target*: Document R² variation; acknowledge that removing Volume may cause a large drop due to geometric definition.
 3. **Interaction Classification**:
 - Extract geometric criteria from CIF (H-bond: distance < 3.5Å, angle > 150°).
 - Classify dominant interaction type.
 - **Framing**: Report as a "heuristic proxy" with acknowledged uncertainty; do not claim physical ground truth.
 - *Validation*: Report bootstrapped confidence intervals for the consistency of the geometric classification.
 4. **Report**: Generate `results/feature_importance.png` and `results/sensitivity_report.md`.

### Phase 4: Final Review & Artifacts
- **Goal**: Ensure all artifacts are checksummed and documented.
- **Tasks**:
 1. Update `state/projects/PROJ-238.../artifact_hashes` with final data and result checksums.
 2. Verify `results/metrics.json` contains all required fields (R², MAE, p-values, Bonferroni flag).
 3. Generate `quickstart.md` and `contracts/` schemas from the data model.

## Compute Feasibility

- **Hardware**: 2 CPU, 7 GB RAM.
- **Strategy**:
 - Limit dataset to a manageable subset for preliminary analysis.
 - Use `scikit-learn` (CPU optimized).
 - Avoid deep learning.
 - Process data in chunks if necessary.
- **Runtime**: Est. a few hours for full pipeline.
