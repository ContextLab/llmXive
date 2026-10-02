# Implementation Plan: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

**Branch**: `001-predict-alloy-diffusion` | **Date**: 2026-06-26 | **Spec**: `specs/001-predicting-the-impact-of-alloying-on-the/spec.md`
**Input**: Feature specification from `/specs/001-predicting-the-impact-of-alloying-on-the/spec.md`

## Summary

This project implements a reproducible machine learning pipeline to predict the impact of alloying on the diffusion activation energy in FCC metals. The approach involves ingesting real-world diffusion datasets (specifically the verified DiffusionDB), filtering for FCC self-diffusion, engineering atomic descriptors (specifically size mismatch), and training Random Forest, Gradient Boosting, and Linear Regression models. The pipeline enforces strict data hygiene, statistical validation of the size-mismatch hypothesis (framed as association), and sensitivity analysis of decision thresholds, all constrained to run on GitHub Actions free-tier resources (CPU-first).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `requests`, `joblib`, `mendeleev`  
**Storage**: Local file system (CSV, JSON, Pickle) within the repository `data/` and `models/` directories.  
**Testing**: `pytest` (unit tests for feature calculation, integration tests for pipeline execution).  
**Target Platform**: Linux (GitHub Actions Runner).  
**Project Type**: Data Science / Scientific Computing Pipeline.  
**Performance Goals**: Complete full pipeline (ingestion to validation) in <6 hours; peak memory <7 GB.  
**Constraints**: No synthetic data generation; strict filtering for FCC/self-diffusion; CPU-only execution for models; no external API calls during runtime (datasets must be local or streamable).  
**Scale/Scope**: Processing of public diffusion datasets (target <50k rows after filtering); training of multiple regression models.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Principle I (Reproducibility)**: The plan mandates pinned `requirements.txt`, fixed random seeds in `code/`, and checksumming of all `data/` artifacts. External datasets MUST be fetched from the same canonical source on every run (DiffusionDB). Every result reported MUST be reproducible by re-running the project's `code/` against the project's `data/` on a fresh GitHub Actions runner.
2.  **Principle II (Verified Accuracy)**: Every external citation in `idea/`, `technical-design/`, `implementation-plan/`, or `paper/` MUST be verified by the Reference-Validator Agent against the primary source before contributing review points. Title-token-overlap with the cited source MUST be ≥ `CITATION_TITLE_OVERLAP_THRESHOLD` (default 0.7). Citations in `research.md` are restricted to the "Verified datasets" block.
3.  **Principle III (Data Hygiene)**: Datasets MUST be checksummed and the checksum recorded under `data/`. No data may be modified in place; every transformation MUST produce a new file with a documented derivation. The plan includes a `Data Availability Check` (FR-001) and generates `data/curated/data_provenance.json`. No PII will appear in committed data.
4.  **Principle IV (Single Source of Truth)**: Every figure, statistic, or interpretation in the paper MUST trace back to exactly one row in this project's `data/` and one block in this project's `code/`. Derived numbers MUST NOT be hand-typed into the paper. The `data-model.md` defines strict schemas.
5.  **Principle V (Versioning Discipline)**: Every artifact under this project carries a content hash. The Advancement-Evaluator Agent invalidates stale review records when the hashed artifact changes. Every research-stage artifact change updates this project's `state/projects/PROJ-415-predicting-the-impact-of-alloying-on-the.yaml` `updated_at` timestamp. The plan includes generating content hashes for data and model artifacts.
6.  **Principle VI (Computational Resource Compliance)**: All training pipelines MUST complete within the 6-hour GitHub Actions runner limit specified in the feasibility check; model training MUST remain within a computationally efficient timeframe.; The dataset size must remain within a manageable limit to ensure efficient processing and storage. to ensure reproducibility within CI constraints. The methodology is strictly CPU-first (scikit-learn).
7.  **Principle VII (Descriptor Consistency)**: All atomic descriptors (atomic radius, electronegativity, valence) MUST be computed using fixed, versioned periodic table constants. The Pauling scale for electronegativity MUST be used consistently across all solutes to prevent feature drift. The plan specifies using a fixed, versioned `mendeleev` library.

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-alloy-diffusion/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── model_output.schema.yaml
    └── validation_report.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-415-predicting-the-impact-of-alloying-on-the/
├── data/
│   ├── raw/               # Downloaded raw files (preserved)
│   └── curated/           # Filtered, processed data (filtered.csv, data_provenance.json)
├── code/
│   ├── __init__.py
│   ├── ingestion/
│   │   └── curation.py    # Ingests, filters, validates, writes provenance (FR-001, FR-007)
│   │                      # Logic: Writes data/curated/data_provenance.json with source_url, hash, timestamp, filter_criteria
│   ├── features/
│   │   └── engineering.py # Calculates size_mismatch, electronegativity diff (FR-002)
│   ├── models/
│   │   └── train.py       # Trains RF, GB, Linear; saves artifacts (FR-003, FR-004)
│   └── validation/
│       ├── baseline.py    # Calculates baseline_shift from data/curated/filtered.csv (FR-008, T030)
│       │                  # Logic: Joins curated data with PureMetalBaseline table to compute shift
│       └── sensitivity.py # Threshold sweep, stability index (FR-005, FR-006)
├── models/
│   ├── final_rf.pkl
│   ├── final_gb.pkl
│   └── linear_coef.json
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── README.md
```

**Structure Decision**: A modular Python package structure is selected to separate concerns (ingestion, features, training, validation) and facilitate unit testing. The `code/` directory mirrors the functional requirements directly. The `data/` directory is split into `raw` and `curated` to enforce the "no modification in place" rule.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project scope is strictly bounded by the spec and resource constraints. | A monolithic script was rejected to ensure testability of the `baseline.py` and `curation.py` modules independently. |
