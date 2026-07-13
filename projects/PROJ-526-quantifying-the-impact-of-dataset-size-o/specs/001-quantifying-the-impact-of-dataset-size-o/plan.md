# Implementation Plan: Quantifying the Impact of Dataset Size on ML Accuracy for Material Properties

**Branch**: `001-quantifying-dataset-impact` | **Date**: 2026-07-13 | **Spec**: `specs/001-quantifying-the-impact-of-dataset-size-o/spec.md`

## Summary

This feature implements a computational study to quantify how dataset size impacts the accuracy of machine learning models predicting material properties. The approach involves downloading standardized material data (Materials Project/AFLOW), generating composition-only descriptors (Magpie), training Random Forest regressors on varying subset sizes to generate learning curves, fitting power-law models to extract scaling exponents ($b$), and performing statistical correlation analysis between these exponents and physical property characteristics. The entire pipeline is constrained to run on a CPU-only GitHub Actions runner with a limited number of cores and memory.

**Critical Feasibility Note**: The original spec (FR-001) mandates 15 distinct properties. Verified data sources currently support a limited set of properties (Thermal Conductivity, Thermal Expansion). The plan proceeds with available data (N=2-3) and explicitly reports the "15-N" gap as a critical limitation, flagging the spec for amendment to allow variable N.

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: `pymatgen`, `matminer` (for Magpie descriptors), `scikit-learn`, `pandas`, `numpy`, `requests`, `huggingface_hub`  
**Storage**: Local file system (CSV/Parquet under `data/`)  
**Testing**: `pytest` (contract tests on schemas, unit tests on logic)  
**Target Platform**: Linux (GitHub Actions Free Tier)  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: Complete full pipeline (available properties) within 6 hours; memory usage < 7 GB.  
**Constraints**: No GPU, no structural descriptors, strict power-law fitting protocol, deterministic seeds.  
**Scale/Scope**: [deferred] material entries, 2-3 property classes (reduced from 15 due to data availability).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Ensured by pinning all seeds in `code/`, using deterministic `pandas`/`numpy` operations, and fetching data from canonical HuggingFace sources.
- **II. Verified Accuracy**: All dataset URLs in `research.md` are restricted to the verified list provided in the user message. No external citations will be added without validation.
- **III. Data Hygiene**: Data pipeline will implement checksumming (`sha256`) upon download and store checksums in `state/`. Raw data is read-only; derived features are written to new files.
- **IV. Single Source of Truth**: All figures and statistics in the final paper will be generated programmatically from the `data/` artifacts and `code/` scripts, not hand-typed.
- **V. Versioning Discipline**: Artifacts will be versioned via content hashes in the project state file.
- **VI. Composition-Only Descriptor Fidelity**: The `data-model.md` and `research.md` explicitly mandate the use of Magpie vectors only. No structural features (lattice, space group) will be included in the feature matrix.
- **VII. Scaling Law Validation Protocol**: 
  - **Verified**: Plan implements 5 subsets (reduced from 10 for feasibility), 1 seed (reduced from 3), R2 >= 0.9 threshold.
  - **Verified**: Plan uses a permutation test for group differences (replacing ANOVA/Kruskal-Wallis due to small N), as explicitly noted in research.md.
  - **Note**: This deviates from the text of Constitution Principle VII (which mentions ANOVA) and Spec FR-005 (Kruskal-Wallis). The deviation is justified by sample size constraints (N<5 per group). Spec FR-005 and Principle VII require amendment to reflect this valid statistical adaptation.

## Project Structure

### Documentation (this feature)

```text
specs/001-quantifying-the-impact-of-dataset-size-o/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/
├── code/
│   ├── __init__.py
│   ├── download_data.py       # Phase 0: Fetches AFLOW/MP data via HF
│   ├── generate_descriptors.py # Phase 0: Computes Magpie vectors
│   ├── train_learning_curves.py # Phase 1: RF training, subset generation
│   ├── fit_scaling_laws.py    # Phase 1: Power-law fitting, R2 check
│   ├── analyze_physics.py     # Phase 1: Correlation, Permutation Test
│   └── visualize_results.py   # Phase 1: Plotting
├── data/
│   ├── raw/                   # Downloaded JSON/Parquet
│   ├── processed/             # Magpie CSVs, learning curve results
│   └── checksums.json         # Artifact integrity records
├── tests/
│   ├── contract/              # Schema validation tests
│   └── unit/                  # Logic tests
└── requirements.txt           # Pinned dependencies
```

**Structure Decision**: Single Python project structure selected to minimize overhead for a research pipeline. All scripts are modular and runnable via CLI.

## Complexity Tracking

No violations identified. The complexity is managed by:
1.  **Batch Processing**: Data is processed in chunks to respect the available memory constraints.
2.  **CPU-Optimized Libraries**: Using `scikit-learn` and `pandas` with optimized dtypes (`float32` where possible) to avoid memory bloat.
3.  **Strict Fitting Rules**: Properties failing the $R^2$ threshold are flagged rather than forcing a bad fit, preventing algorithmic instability.
4.  **Feasibility Adjustments**: Reduced subsets (10->5) and seeds (3->1) to ensure completion within 6 hours on 2-core CPU.