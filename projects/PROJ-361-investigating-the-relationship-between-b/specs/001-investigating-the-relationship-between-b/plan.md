# Implementation Plan: Investigating the Relationship Between Brain Network Topology and Susceptibility to Visual Illusions

**Branch**: `PROJ-361-brain-illusion-topology` | **Date**: 2026-06-26 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/PROJ-361-investigating-the-relationship-between-b/spec.md`

## Summary

This project implements a computational pipeline to investigate the associational relationship between brain network topology and behavioral susceptibility. **CRITICAL DATA CONSTRAINT**: The primary target dataset, OpenNeuro ds004285, contains *movie-watching* fMRI data and *does not* contain resting-state data or visual illusion susceptibility scores (Müller-Lyer, Ponzo). Consequently, the original hypothesis (Resting-State Topology vs. Illusion Scores) is **infeasible** with this dataset.

The plan is revised to:
1.  Analyze the topology of the *available* movie-watching fMRI data (Naturalistic Viewing).
2.  Explicitly check for behavioral illusion scores; if missing (as expected), the analysis will be limited to describing the topology of the movie-watching network, with a clear statement that the behavioral correlation target is unavailable.
3.  If a different open dataset with both resting-state fMRI and illusion scores is identified in future research, the plan will be updated; otherwise, the project will document the topology of the available data as a descriptive study.

The technical approach relies on `nilearn`, `networkx`, `scikit-learn`, and `pandas`, running on a CPU-first basis. All analysis is framed as associational, with strict adherence to FDR correction and motion exclusion criteria (FD > 0.5mm).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nilearn>=0.10.0`, `networkx>=3.2`, `scikit-learn>=1.4.0`, `pandas>=2.1.0`, `numpy>=1.26.0`, `scipy>=1.12.0`, `fmriprep` (docker/singularity via `nipype`), `pyyaml`, `black`, `flake8`, `mypy`  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/interim`), SQLite for metadata registry (`data/metadata/registry.db`), JSON for topology metrics  
**Testing**: `pytest` with `pytest-cov`  
**Target Platform**: Linux (GitHub Actions runner: 2 CPU, ~7GB RAM).  
**Project Type**: Computational Neuroscience Pipeline / Data Analysis Library  
**Performance Goals**: Process ~5-10 subjects within 6 hours on CPU (fMRIPrep is CPU-bound and time-intensive; A large subject cohort is infeasible on this hardware.). Memory usage < 6GB peak; disk usage < 12GB.  
**Constraints**: No local GPU; strict motion exclusion (FD > 0.5mm); FDR correction mandatory; reproducibility via fixed seeds; no synthetic data; only open, programmatically downloadable datasets.  
**Scale/Scope**: Single dataset (ds004285); ~5-10 subjects (feasible limit); Several network metrics (Modularity, Path Length, Clustering, Efficiency); Behavioral data: *Expected to be missing*.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | All code pinned in `requirements.txt`; random seeds set in `code/utils/seeds.py`; fMRIPrep version fixed; data checksums recorded in `data/metadata/checksums.json`. |
| **II. Verified Accuracy** | DEFERRED | URL verification is performed in `research.md`. The plan defers this check to the research artifact, which contains the verified dataset sources. |
| **III. Data Hygiene** | PASS | Raw data preserved in `data/raw/` with checksums; derivations in `data/processed/`; exclusion lists (`excluded_subjects.csv`) materialized as artifacts; PII scan enforced via pre-commit hook. |
| **IV. Single Source of Truth** | PASS | Every statistic traces to a specific row in `data/processed/merged_dataset.csv` (or the exclusion list if missing); figures generated from code, not hand-typed. |
| **V. Versioning Discipline** | PASS | Content hashes recorded in `state/projects/...yaml`; artifact changes trigger `updated_at` updates via `code/utils/update_state.py`. |
| **VI. Neuroimaging Preprocessing Rigor** | PASS | fMRIPrep container used; motion parameters (FD) calculated and logged; nuisance regression documented in `code/preprocessing/pipeline.py`. |
| **VII. Statistical Correction Discipline** | PASS | Benjamini-Hochberg FDR applied in `code/statistics/correlation.py`; uncorrected p-values flagged as non-significant. |

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-361-investigating-the-relationship-between-b/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-361-investigating-the-relationship-between-b/
├── code/
│   ├── __init__.py
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   ├── fmriprep_wrapper.py   # Wrapper for fMRIPrep container
│   │   ├── motion_qc.py          # FD calculation and exclusion logic
│   │   └── pipeline.py           # Main preprocessing orchestration
│   ├── topology/
│   │   ├── __init__.py
│   │   ├── connectivity.py       # Correlation matrix generation
│   │   └── metrics.py            # Graph theory metric computation
│   ├── statistics/
│   │   ├── __init__.py
│   │   └── correlation.py        # Correlation + FDR correction (PCA-based)
│   ├── io/
│   │   ├── __init__.py
│   │   ├── data_loader.py        # OpenNeuro/HF download logic
│   │   └── schema_registry.py    # SQLite interaction
│   ├── db/
│   │   └── schema.sql            # SQLite DDL for metadata registry
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── seeds.py              # Seed management
│   │   ├── checksums.py          # Data integrity checks
│   │   └── update_state.py       # State update logic
│   ├── hooks/
│   │   └── pre-commit            # Shell script for state updates on commit
│   └── main.py                   # Entry point
├── data/
│   ├── raw/                      # Downloaded raw data (symlinks or copies)
│   ├── interim/                  # Preprocessed fMRI (nii.gz)
│   ├── processed/                # Metrics, merged datasets, exclusion lists
│   │   └── excluded_subjects.csv # Materialized exclusion list
│   └── metadata/
│       ├── registry.db           # SQLite metadata store
│       └── checksums.json        # File integrity records
├── tests/
│   ├── unit/
│   │   ├── test_connectivity.py
│   │   └── test_metrics.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── contract/
│       └── test_schemas.py       # Validates against contracts/
├── contracts/                    # Schema definitions (Root level)
│   ├── topology_metrics.schema.yaml
│   ├── merged_dataset.schema.yaml
│   ├── exclusion_list.schema.yaml
│   └── analysis_result_schema.schema.yaml
├── requirements.txt
├── pyproject.toml                # Black, flake8, mypy config
├── .flake8                       # Flake8 configuration
└── .git_hooks/
    └── pre-commit                # PII scan, linting trigger
```

**Structure Decision**: The project follows a modular pipeline structure (`preprocessing`, `topology`, `statistics`) to ensure separation of concerns and testability. The `io` module handles all data ingestion and metadata registry interactions, centralizing the "Single Source of Truth" logic. The `data/` directory is strictly hierarchical (raw/interim/processed) to enforce Data Hygiene. The `contracts/` directory is at the root to match the actual file paths. The `code/db/schema.sql` file provides the concrete DDL for the metadata registry.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | Constitution Check passed all gates. | N/A |

## Phase Breakdown

### Phase 0: Foundation & Configuration
- **Task**: Create `requirements.txt`, `pyproject.toml`, `.flake8`.
- **Task**: Create `code/db/schema.sql` with DDL for `subjects`, `files`, `artifacts` tables (including Foreign Keys).
- **Task**: Create `code/hooks/pre-commit` script to trigger state updates.
- **Constraint**: Ensure all configuration files are valid and lintable.

### Phase 1: Data Acquisition & Verification
- **Task**: Download OpenNeuro ds004285 via HuggingFace mirror.
- **Artifact**: `data/raw/`, `data/metadata/checksums.json`.
- **Constraint**: Verify dataset content. If `illusion_scores` are missing, log a "MISSING" status and proceed with topology analysis only.

### Phase 2: Preprocessing & Motion QC
- **Task**: Run fMRIPrep (CPU-only) on available subjects.
- **Task**: Calculate Mean Framewise Displacement (FD).
- **Artifact**: `data/processed/excluded_subjects.csv` (Materialized exclusion list).
- **Constraint**: Exclude subjects with FD > 0.5mm. This artifact must exist before Phase 3.

### Phase 3: Topology Computation
- **Task**: Compute connectivity matrices (Pearson correlation).
- **Task**: Compute multiple metrics: Modularity, Path Length, Clustering, Efficiency. (Small-worldness excluded due to redundancy).
- **Artifact**: `data/processed/topology_metrics_raw.json`.

### Phase 4: Statistical Analysis
- **Task**: Merge topology metrics with available behavioral data (if any) using `excluded_subjects.csv` to filter.
- **Task**: Perform PCA on the 4 topology metrics to derive orthogonal components.
- **Task**: Correlate PCA components with available behavioral data (if any).
- **Task**: Apply Benjamini-Hochberg FDR correction.
- **Artifact**: `data/processed/analysis_results.json`.
- **Note**: If behavioral data is missing, this phase will output a "No Behavioral Data" report.

## Risk Assessment

| Risk | Probability | Mitigation |
| :--- | :--- | :--- |
| **Dataset Mismatch** | HIGH | ds004285 lacks illusion scores. Mitigation: Explicitly document this gap and analyze topology of available data only. |
| **Motion Exclusion** | Medium | Strict FD > 0.5mm may exclude many subjects; report power limitation honestly. |
| **Compute Time** | High | fMRIPrep may exceed 6h for >10 subjects. Mitigation: Limit sample size to a small cohort of subjects for the CI run.. |
| **Collinearity** | High | Metrics are related. Mitigation: Use PCA to derive orthogonal components before correlation. |