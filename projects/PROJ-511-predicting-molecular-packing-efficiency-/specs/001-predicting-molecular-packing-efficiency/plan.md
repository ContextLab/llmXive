# Implementation Plan: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

**Branch**: `PROJ-511-predicting-molecular-packing-efficiency` | **Date**: 2026-07-02 | **Spec**: `specs/001-predicting-molecular-packing-efficiency/spec.md`
**Input**: Feature specification from `/specs/001-predicting-molecular-packing-efficiency/spec.md`

## Summary

This project implements a CPU-only pipeline to predict the **Raw Packing Coefficient (PC_raw)** of organic crystals, isolating the contribution of molecular topology (SMILES) beyond the deterministic effects of 3D geometry. The pipeline ingests the official Crystallography Open Database (COD), filters for organic molecules with ≤50 non-hydrogen atoms, and generates canonical SMILES via RDKit **strictly from 2D connectivity graphs** (derived from CIF bond data or inferred from 3D bonds *before* conformational optimization). This ensures the SMILES predictor is independent of the experimental 3D coordinates used to calculate the target (PC_raw) and 3D descriptors, breaking the circular dependency. The pipeline computes 3D descriptors (radius of gyration, asphericity, inertia) **strictly from the experimental CIF coordinates** (FR-012) to preserve environmental context (FR-013). A frozen pre-trained SMILES Transformer (ChemBERTa-Zinc) encodes molecular topology. The core scientific analysis employs a two-stage modeling approach: (1) a baseline model using only 3D geometric descriptors to predict PC_raw, and (2) a full model adding SMILES embeddings. The **incremental variance explained** by the SMILES features quantifies the predictive power of topology. The evaluation includes rigorous statistical validation: Pearson/Spearman correlation, Shapiro-Wilk normality tests, VIF diagnostics for collinearity (FR-009), and a -shuffle permutation test with Bonferroni correction for threshold sensitivity (FR-007, FR-008, FR-016). The "Composition-Adjusted Packing Efficiency" (CAPE) is computed as a diagnostic covariate (mean atomic volume) but **not** as the regression target, avoiding tautological target definitions (FR-003, FR-011). A partial correlation analysis controls for **elemental atom counts** (not just size) to ensure the SMILES signal is not a proxy for composition. All steps adhere to the project constitution's reproducibility and data hygiene principles.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `rdkit`, `torch` (CPU-only), `scikit-learn`, `pandas`, `datasets`, `pyyaml`, `jinja2`, `matplotlib`, `seaborn`, `transformers`  
**Storage**: Local filesystem (`data/`, `code/`, `results/`); no external database.  
**Testing**: `pytest` (unit tests for parsing, feature extraction, and model constraints).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM).  
**Project Type**: Computational research pipeline / CLI tool.  
**Performance Goals**: End-to-end execution ≤6 hours (SC-005); dataset generation ≥500 records (SC-001); model training <30 minutes.  
**Constraints**: CPU-only inference for the transformer; no GPU usage; strict memory footprint (<7 GB); no external API calls during runtime.  
**Scale/Scope**: A representative set of crystal structures; ~k parameter model; permutation shuffles (FR-016).

> The dataset source is the official COD bulk download (`ftp://ftp.ccdc.cam.ac.uk/pub/structures/cod/`), verified via checksum. The Bondi radii are hard-coded from the 1964 reference (DOI: 10.1021/j100785a001) as required by FR-018. The SMILES Transformer weights are sourced from `seyonec/ChemBERTa-zinc-base-v`.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Verification Strategy |
|-----------|--------|-----------------------|
| **I. Reproducibility** | PASS | All random seeds pinned in `code/utils.py`; `requirements.txt` pins versions; dataset checksums recorded in `state/`. |
| **II. Verified Accuracy** | PASS | Bondi radii cited from DOI 10.1021/j100785a001 (FR-018); COD source URL verified in `research.md`; model weights from verified Hugging Face repo (`seyonec/ChemBERTa-zinc-base-v1`). |
| **III. Data Hygiene** | PASS | Raw data immutable; derived `dataset.csv` checksummed; no PII (crystal structures are public). |
| **IV. Single Source of Truth** | PASS | Every metric in the report traces to a specific row in `dataset.csv` and a function in `code/`. |
| **V. Versioning Discipline** | PASS | Artifacts hashed; `state/` updated on change. |
| **VI. Open Crystallographic Data Integrity** | PASS | Data sourced from official COD; provenance tags (COD ID) retained in CSV. |
| **VII. Model Transparency** | PASS | MLP architecture <100k params (FR-005); permutation test a sufficient number of shuffles (FR-016, which supersedes Principle VII's general iteration guideline as the specific operational requirement); full code committed. |

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-511-predicting-molecular-packing-efficiency/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── model.schema.yaml
│   └── validation_report.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-511-predicting-molecular-packing-efficiency-/
├── data/
│   ├── raw/             # Downloaded CIFs (immutable)
│   └── processed/       # dataset.csv, feature_matrix.csv
├── code/
│   ├── __init__.py
│   ├── config.py        # Hyperparameters, paths, seeds
│   ├── bondi_constants.py # Bondi radii (FR-018)
│   ├── data_ingestion.py # COD download/parse, SMILES gen (FR-001, FR-002)
│   ├── features.py      # 3D descriptors, VIF calc (FR-004, FR-009, FR-012)
│   ├── model.py         # Frozen transformer, MLP (FR-004, FR-005)
│   ├── train.py         # Training loop, checkpointing
│   ├── evaluate.py      # Metrics, permutation test, sensitivity (FR-006, FR-007, FR-008)
│   └── report.py        # HTML report generation (FR-010)
├── tests/
│   ├── test_data_ingestion.py
│   ├── test_features.py
│   └── test_model_constraints.py
├── results/
│   ├── model.pt
│   ├── validation_report.md
│   └── report.html
└── requirements.txt
```

**Structure Decision**: Single-project structure selected to minimize overhead for a linear research pipeline. All logic is encapsulated in `code/` with clear separation of concerns (ingestion, features, model, evaluation).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The pipeline is strictly linear: Download → Parse → Feature → Train → Evaluate. No complex branching or microservices are required. | A monolithic script was rejected in favor of modular functions to ensure testability and adherence to Constitution Principle I (Reproducibility). |

## Scientific Rigor & Methodological Notes

- **Leakage Mitigation**: SMILES are generated **exclusively from 2D connectivity graphs** (derived from CIF bond data or inferred from 3D bonds *before* any conformational optimization). The experimental 3D coordinates are **never** used to generate the SMILES string. This breaks the circular dependency where the predictor would be a proxy for the target. The 3D descriptors are calculated from the experimental coordinates, ensuring the model learns the relationship between *topology* (2D) and *packing* (3D).
- **Metric Validity**: PC_raw is the target (standard metric). CAPE is computed as a covariate (mean atomic volume) to control for size, avoiding the tautology of defining the target as a function of the predictors. Partial correlation controls for **elemental composition** (atom counts) to ensure the SMILES signal is not merely a proxy for elemental identity.
- **Model Capacity**: The multi-layer perceptron with 32 units is justified by a **power analysis** (Cohen's f2) indicating >90% power to detect r=0.4 with N≥500. The frozen transformer weights prevent overfitting the high-dimensional input. L2 regularization and dropout are applied.
- **Data Source**: The pipeline uses the official COD bulk download with streaming and checksum verification to ensure data completeness and reproducibility, avoiding reliance on third-party mirrors.
- **Statistical Rigor**: The plan includes explicit Bonferroni correction for the three threshold tests (FR-008) and a -shuffle permutation test (FR-016). VIF diagnostics (FR-009) and partial correlation (FR-014) are explicitly included to address collinearity and compositional effects. An ECFP4 baseline is included to validate the frozen transformer's signal capture.