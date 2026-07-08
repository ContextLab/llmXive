# Implementation Plan: Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

**Branch**: `001-comparative-analysis-of-molecular-fingerprints` | **Date**: 2026-07-08 | **Spec**: [link]
**Input**: Feature specification from `specs/001-comparative-analysis-of-molecular-fingerprints/spec.md`

## Summary

This project implements a comparative analysis of Morgan fingerprints (radius=2, 2048 bits) versus MACCS keys (bits) for predicting toxicity endpoints in organophosphate compounds. The workflow involves downloading the Tox21 dataset, filtering for organophosphates using a specific SMARTS pattern, generating features via RDKit, training Random Forest classifiers under strict CPU-only constraints, and performing rigorous statistical comparison.

**Key Methodological Update**: To satisfy Constitution Principle VII and ensure statistical validity, the analysis now employs **K-Fold Cross-Validation

The specific value to remove/generalize: 'K'

Rewritten passage:
K-Fold Cross-Validation

K-fold cross-validation will be employed to assess model generalization performance by partitioning the dataset into K subsets, iteratively training on K-1 folds and validating on the remaining fold, thereby ensuring robust evaluation across varying data splits.** where each fold utilizes a **Greedy Maximal Dissimilarity Split** (Tanimoto < 0.85). This generates multiple distinct train/test pairs, enabling the valid application of the **Corrected Resampled t-test (Nadeau & Bengio)**. The plan also includes a specific mechanism to map Morgan fingerprint bits to phosphorus-centered substructures to address the feature importance success criterion (SC-003).

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: `rdkit` (2024.3.x), `scikit-learn` (1.4.x), `pandas` (2.2.x), `numpy` (1.26.x), `requests` (2.31.x)  
**Storage**: Local CSV/Parquet files under `data/` (raw and derived); no external database.  
**Testing**: `pytest` (8.x) with unit tests for SMARTS filtering, fingerprint generation, and statistical test logic.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 vCPU, 7GB RAM, no GPU).  
**Project Type**: Computational chemistry research pipeline.  
**Performance Goals**: Complete full pipeline (filtering -> 5-fold CV training -> evaluation) within 60 minutes on the filtered subset; memory usage < 7 GB.  
**Constraints**: CPU-only execution; strict Tanimoto similarity threshold (<0.85) for each fold split; no GPU/CUDA operations.  
**Scale/Scope**: Filtered dataset expected to be < 5,000 compounds; toxicity endpoints.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Plan mandates pinned `requirements.txt` and random seed initialization in all scripts. External datasets are fetched from canonical HuggingFace URLs.
- **II. Verified Accuracy**: All dataset citations in `research.md` are restricted to the verified list provided in the user prompt. No external URLs will be generated.
- **III. Data Hygiene**: Plan includes checksumming of raw downloads and derivation logging for filtered datasets. No in-place modifications.
- **IV. Single Source of Truth**: All performance metrics in the final report will be generated programmatically from the `data/` artifacts and `code/` scripts.
- **V. Versioning Discipline**: Content hashes for data and code will be recorded in the project state file upon generation.
- **VI. Cheminformatics Structural Integrity**: The SMARTS pattern `[P](=O)([O,SC])[O,SC]` is explicitly defined in the code plan. RDKit canonicalization settings will be fixed. Morgan (radius=2, 2048 bits) and MACCS (fingerprint)

The research question is to evaluate the efficacy of molecular fingerprints in similarity searching. The method involves generating molecular fingerprints and computing pairwise similarity metrics. References: [Cite as needed] parameters are locked.
- **VII. Toxicological Statistical Rigor**: The plan explicitly implements **K-Fold Cross-Validation

The specific value to remove/generalize: 'K'

Rewritten passage:
K-Fold Cross-Validation** with **Greedy Maximal Dissimilarity Splitting** per fold. This satisfies the requirement for repeated samples, enabling the **Corrected Resampled t-test (Nadeau & Bengio)**. The plan explicitly includes reporting **ROC-AUC**, **Precision-Recall AUC**, and **Balanced Accuracy**. Structural leakage is prevented by the Tanimoto < 0.85 constraint per fold.

## Project Structure

### Documentation (this feature)

```text
specs/001-comparative-analysis-of-molecular-fingerprints/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later; contains derived constraints like endpoints, 60 min limit)
```

### Source Code (repository root)

```text
projects/PROJ-678-comparative-analysis-of-molecular-finger/
├── data/
│   ├── raw/             # Downloaded Tox21 files
│   └── processed/       # Filtered organophosphate CSVs, fingerprints, split indices
├── code/
│   ├── __init__.py
│   ├── download.py      # Data acquisition and checksumming
│   ├── filter.py        # SMARTS filtering logic
│   ├── fingerprints.py  # Morgan and MACCS generation + Bit-to-Atom mapping
│   ├── split.py         # Greedy maximal dissimilarity split (per fold)
│   ├── train.py         # Random Forest training (CPU only, 5-fold loop)
│   ├── evaluate.py      # Metrics, Nadeau & Bengio t-test, bootstrapping, SC-003 analysis
│   └── utils.py         # Shared helpers (logging, config)
├── tests/
│   ├── test_filter.py
│   ├── test_fingerprints.py
│   └── test_split.py
├── requirements.txt
└── README.md
```

**Structure Decision**: A linear pipeline structure (`download` -> `filter` -> `fingerprints` -> `split` -> `train` -> `evaluate`) is selected to match the sequential dependency of the research workflow. This ensures data flows strictly from raw to processed, supporting the "Data Hygiene" and "Reproducibility" principles. The `tasks.md` file generated in Phase 2 will contain the specific derived constraints (e.g., exact runtime limits) referenced here.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project scope is contained within a single pipeline. | N/A |