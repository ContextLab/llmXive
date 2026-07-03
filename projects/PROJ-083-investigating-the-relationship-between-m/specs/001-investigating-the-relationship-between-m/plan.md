# Implementation Plan: Investigating the Relationship Between Molecular Topology and Reaction Selectivity

**Branch**: `001-molecular-topology-selectivity` | **Date**: 2026-06-25 | **Spec**: `specs/001-molecular-topology-selectivity/spec.md`
**Input**: Feature specification from `specs/001-molecular-topology-selectivity/spec.md`

## Summary

This project investigates the *structural correlation* between molecular topological descriptors (Wiener, Balaban, Zagreb indices) and the *theoretical* regioisomer diversity of Electrophilic Aromatic Substitution (EAS) reactions. 

**Critical Methodological Note**: The target variable ("Theoretical Regioisomer Count") is a deterministic function of the reactant graph topology. Consequently, the predictors (topological indices) are definitionally correlated with the target. 
**Reframed Objective**: The analysis is **not** a predictive model of an independent outcome. Instead, it is a **Structural Correlation & Graph Complexity Study**. The goal is to:
1.  Quantify the *degree* of definitional correlation (how well graph complexity metrics map to substitution site counts).
2.  Identify *non-linearities* or *deviations* from the theoretical 1:1 complexity-to-site relationship (e.g., steric hindrance effects captured by Balaban index that reduce effective diversity).
3.  Validate the robustness of topological indices as proxies for theoretical reactivity patterns.
Standard regression (Poisson/RF) will be used to quantify these relationships and test for significant deviations from linearity, not to predict an unknown outcome.

**Implementation Steps**:
1.  Download USPTO-50k, parse SMILES, filter EAS using specific SMARTS patterns.
2.  Sanitize reactant SMILES (remove salts, disconnects) to ensure valid graph enumeration.
3.  Compute topological descriptors (Wiener, Balaban, Zagreb) using `rdkit`.
4.  Derive target via reaction template enumeration on the *sanitized* reactant graph.
5.  Validate target distribution; switch to Binary/Ordinal modeling if degenerate.
6.  Fit models to quantify correlation strength and non-linearities.
7.  Report metrics (R², RMSE, VIF) and interpret deviations from theoretical expectations.

The pipeline is constrained to CPU-only execution on a GitHub Actions free-tier runner (limited CPU, limited RAM, 6h limit).

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: `rdkit` (molecular graph analysis), `scikit-learn` (modeling), `pandas` (data manipulation), `requests` (download), `pyyaml` (contracts), `statsmodels` (Poisson/ZIP), `networkx` (graph analysis)  
**Storage**: Local CSV/Parquet files in `data/` (checksummed)  
**Testing**: `pytest` (unit tests for descriptor calculation, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier)  
**Project Type**: Computational Chemistry Pipeline / Research Script  
**Performance Goals**: Descriptor calculation ≤ 15 mins; Total pipeline ≤ 6 hours; Memory ≤ 7GB  
**Constraints**: No GPU; No heavy LLM inference; Must handle malformed SMILES gracefully; Must switch to LOO CV if N < 20.  
**Scale/Scope**: ~50k raw reactions, filtered to EAS subset (expected N > 1000).

> Domain-specific empirical specifics (exact counts, dataset sizes) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on constitution file*

1.  **Reproducibility (Principle I - NON-NEGOTIABLE)**:
    *   **Plan**: All random seeds will be pinned in `code/` (e.g., `np.random.seed(<value>)`).
    *   **Plan**: External datasets will be fetched from the canonical HuggingFace URLs provided in the spec.
    *   **Plan**: `requirements.txt` will pin exact versions of `rdkit`, `scikit-learn`, and `pandas`.
    *   **Plan**: Every artifact under `data/` is checksummed in the project's `state/projects/PROJ-083-...` `artifact_hashes` map.
    *   **Status**: Compliant.

2.  **Verified Accuracy (Principle II)**:
    *   **Plan**: Citations for topological indices (Wiener, Balaban, Zagreb) will be verified against primary literature (Balaban et al., Wiener 1947) in `research.md`.
    *   **Plan**: Dataset URLs are restricted to the "Verified datasets" block in the input.
    *   **Status**: Compliant.

3.  **Data Hygiene (Principle III)**:
    *   **Plan**: Raw data download will be checksummed (SHA-256) and stored in `data/raw/`.
    *   **Plan**: Derived datasets (filtered EAS, descriptor table) will be stored in `data/processed/` with new checksums.
    *   **Plan**: No in-place modifications; all transformations produce new files.
    *   **Status**: Compliant.

4.  **Single Source of Truth (Principle IV)**:
    *   **Plan**: All metrics (R², RMSE, p-values) in the final report will be generated programmatically from `data/processed/` and `code/`. No hand-typed numbers.
    *   **Plan**: **Traceability Mechanism**: A dedicated script `code/generate_report.py` will read `data/processed/model_results.json` and write the report, ensuring every figure/statistic traces back to exactly one row in `data/` and one block in `code/`.
    *   **Status**: Compliant.

5.  **Versioning Discipline (Principle V)**:
    *   **Plan**: Artifact hashes will be recorded in the `artifact_hashes` map within the project's `state/projects/PROJ-083-...` YAML state file (not `updated_at`).
    *   **Plan**: A dedicated script `code/update_hashes.py` will compute SHA-256 checksums for all files in `data/` and update the `artifact_hashes` map programmatically after each transformation step.
    *   **Status**: Compliant.

6.  **Computational Resource Compliance (Principle VI)**:
    *   **Plan**: Scripts will include memory monitoring hooks (e.g., `psutil`) to abort if >7GB RAM is exceeded.
    *   **Plan**: Methods are selected for CPU efficiency (no GPU/CUDA, no 8-bit quantization).
    *   **Plan**: Descriptor calculation is capped at a fixed duration to preserve time for modeling.
    *   **Status**: Compliant.

7.  **Topological Descriptor Transparency (Principle VII)**:
    *   **Plan**: `rdkit` version and parameters will be logged in the descriptor generation step.
    *   **Plan**: The descriptor table will be stored under `data/` with a recorded checksum, providing a traceable link from each model input back to the original molecular structure.
    *   **Status**: Compliant.

## Project Structure

### Documentation (this feature)

```text
specs/001-molecular-topology-selectivity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (not created here)
```

### Source Code (repository root)

```text
projects/PROJ-083-investigating-the-relationship-between-m/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── ingest.py          # FR-001, FR-006: Download, parse, filter EAS
│   ├── descriptors.py     # FR-002: Compute Wiener, Balaban, Zagreb
│   ├── target_enumeration.py # FR-003: Theoretical regioisomer count via template enumeration
│   ├── modeling.py        # FR-003, FR-004, FR-005: Poisson, ZIP, RF, CV
│   ├── utils.py           # Logging, error handling, checksums
│   ├── update_hashes.py   # Mechanism for updating artifact_hashes
│   ├── generate_report.py # Traceability script for reports
│   └── run_pipeline.py    # Orchestration script
├── data/
│   ├── raw/               # Downloaded parquet files (checksummed)
│   ├── processed/         # Filtered CSV, descriptor tables
│   └── checksums.json     # Artifact hashes
├── tests/
│   ├── unit/
│   │   ├── test_descriptors.py  # Verify benzene/toluene/nitrobenzene values
│   │   └── test_ingest.py
│   └── integration/
│       └── test_pipeline.py
└── docs/
    └── (generated reports)
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) selected to minimize overhead and align with the research pipeline nature. No frontend/backend split required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project scope is contained within a single pipeline. | N/A |

## Phase Ordering

1.  **Data Ingestion**: Download USPTO-50k, parse SMILES, filter EAS (FR-001, FR-006).
2.  **Sanitization**: Clean reactant SMILES (remove salts, disconnects) for valid graph enumeration.
3.  **Descriptor Calculation**: Compute topological indices for reactants (FR-002).
4.  **Target Extraction**: Derive Theoretical Regioisomer Count via reaction template enumeration on sanitized reactant (FR-003).
5.  **Distribution Check**: Validate target variance; switch to ZIP/Binary/Ordinal if degenerate.
6.  **Modeling**: Fit Poisson, Zero-Inflated Poisson, and Random Forest with CV to quantify structural correlation (FR-003, FR-004, FR-005).
7.  **Validation**: Report metrics, significance, and collinearity diagnostics.

## Compute Feasibility Statement

- **Memory**: Data is processed in chunks or filtered immediately to fit <7GB.
- **Time**: Descriptor calculation is optimized (vectorized where possible) to stay [deferred]. Total runtime <6h.
- **Hardware**: No GPU required. `rdkit`, `scikit-learn`, and `statsmodels` are used in CPU mode.
- **Fallback**: If EAS subset < 20, switch to LOO CV (FR-005). If target variance is near zero, switch to ZIP or binary classification.
