# Implementation Plan: Exploring the Relationship Between Brain Network Dynamics and Individual Differences in Dream Recall Frequency

**Branch**: `001-exploring-the-relationship-between-brain` | **Date**: 2026-06-27 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-exploring-the-relationship-between-brain/spec.md`

## Summary

This project investigates whether individual differences in resting-state dynamic functional connectivity (specifically network flexibility and stability) predict self-reported dream recall frequency. The technical approach involves downloading OpenNeuro dataset `ds000228` (with a mandatory validation step for dream recall metadata), preprocessing it with ICA-AROMA and normalization under strict memory constraints (≤7GB RAM), extracting dynamic connectivity metrics (flexibility/stability) for DMN, Salience, and Hippocampal networks using a sliding window and Louvain clustering (using **Schaefer-100** atlas to ensure statistical validity), and performing Spearman correlation analysis with FDR correction and permutation testing.

> **Critical Spec-Plan Conflict Note**: The source spec (FR-004) mandates the Schaefer-400 atlas. However, statistical validity analysis (see Research.md) indicates that A large number of regions with a short-duration window results in rank-deficient correlation matrices. The plan **deviates** to **Schaefer-100** to ensure mathematical stability and valid clustering. This deviation is a necessary methodological correction for scientific soundness.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nilearn`, `networkx`, `scikit-learn`, `scipy`, `pandas`, `numpy`, `joblib`, `requests`, `nibabel`  
**Storage**: Local filesystem (intermediate files managed to stay <7GB), JSON/CSV outputs  
**Testing**: `pytest` (contract tests validate against schemas in `contracts/`, unit tests for logic)  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM, no GPU)  
**Project Type**: Computational Neuroscience Analysis Pipeline  
**Performance Goals**: Full pipeline execution ≤6 hours; peak RAM ≤7GB; N=50 subjects processed.  
**Constraints**: CPU-only execution; strict memory monitoring; no GPU/CUDA; dataset must contain "dream recall frequency" metadata.  
**Scale/Scope**: subjects (target), A sufficient number of timepoints per subject, brain regions (Schaefer-100).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Verification |
|-----------|--------|--------------|
| I. Reproducibility | **PASS** | Plan mandates pinned seeds, canonical dataset sources, and `requirements.txt` in `code/`. |
| II. Verified Accuracy | **PASS** | Plan mandates the **Reference-Validator Agent** to run on every artifact write. Citations must pass a **Title-token-overlap ≥ 0.7** check against primary sources before contributing review points. |
| III. Data Hygiene | **PASS** | Plan includes checksumming raw data, immutable transformations, and PII exclusion. |
| IV. Single Source of Truth | **PASS** | All statistics will derive from `data/` artifacts; no hand-typed numbers in reports. |
| V. Versioning Discipline | **PASS** | Plan mandates **content hash generation** for every artifact and automatic update of the `state/projects/...yaml` `updated_at` timestamp upon any artifact change. |
| VI. Dynamic Connectivity Protocol | **PASS** | Plan explicitly enforces a fixed-duration window with a shorter step interval and ICA-AROMA as per spec. |
| VII. Self-Reported Behavioral Metadata | **PASS** | Plan includes logic to skip subjects missing "dream recall frequency" and log exclusions. |

## Project Structure

### Documentation (this feature)

```text
specs/001-exploring-the-relationship-between-brain/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-067-exploring-the-relationship-between-brain/
├── code/
│   ├── requirements.txt
│   ├── __init__.py
│   ├── data/
│   │   ├── download.py          # OpenNeuro fetcher
│   │   └── preprocess.py        # ICA-AROMA, normalization, memory monitor, FD calc
│   ├── analysis/
│   │   ├── metrics.py           # Sliding window, Louvain, flexibility/stability
│   │   └── stats.py             # Spearman, FDR, Permutation, Power Analysis
│   ├── utils/
│   │   ├── config.py            # Seeds, paths, constants
│   │   └── memory_monitor.py    # RSS tracking
│   └── main.py                  # Orchestration script
├── data/
│   ├── raw/                     # Downloaded NIfTI/Parquet (checksummed)
│   ├── processed/               # Preprocessed NIfTI
│   └── metrics/                 # Extracted CSVs (flexibility/stability)
├── results/
│   ├── stats.json               # Final correlation results
│   └── plots/                   # Null distribution, correlation scatter
└── tests/
    ├── contract/
    │   ├── test_metrics.py      # Validates against contracts/subject_metrics.schema.yaml
    │   └── test_stats.py        # Validates against contracts/results_schema.yaml
    └── unit/
        └── test_memory_monitor.py
```

**Structure Decision**: Single-project structure (`code/`, `data/`, `results/`, `tests/`) selected to minimize overhead and ensure easy reproducibility on CI. All data flows from `raw` → `processed` → `metrics` → `results`. Contract tests explicitly validate output files against the schemas defined in `contracts/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Sliding Window + Louvain Clustering | Required by Spec (FR-003, FR-004) to define dynamic states. | Static connectivity (single correlation matrix) fails to capture "dynamics" and "flexibility" as defined in the research question. |
| Memory Monitoring Script | Required by Spec (FR-002, SC-004) to stay within 7GB CI limits. | Relying on default Python GC is insufficient for large NIfTI processing; explicit RSS checks prevent silent CI failures. |
| Permutation Testing | Required by Spec (FR-007, SC-003) for robustness. | Parametric p-values alone are insufficient for non-normal behavioral data; permutation provides empirical null distribution. |
| Schaefer-100 Atlas (vs Spec's 400) | Required for statistical validity (Rank-deficiency avoidance). | Schaefer with 30s windows yields unstable correlations for higher-resolution parcellations; Schaefer-100 is the minimum valid parcellation for this TR/Window combo. |

## Implementation Phases

### Phase 0: Dataset Validation (New Critical Step)
- **Action**: Download `ds000228` metadata.
- **Check**: Verify existence of "dream recall frequency" field.
- **Decision**: If missing, **HALT** with "Fatal Dataset Mismatch" error. Do not proceed to preprocessing.
- **Pivot**: If missing, log error and suggest switching to a verified sleep-dream dataset (if available in verified list).

### Phase 1: Preprocessing & Quality Control
- **Action**: Download NIfTI data.
- **Action**: Run ICA-AROMA denoising.
- **Action**: Calculate Framewise Displacement (FD).
- **Action**: Exclude subjects with FD > 0.5mm.
- **Action**: Spatial normalization to MNI space.
- **Constraint**: Monitor RSS; fail if >7GB.

### Phase 2: Metric Extraction
- **Action**: Apply Schaefer-100 parcellation.
- **Action**: Sliding window correlation (fixed-duration window, fixed-step interval).
- **Action**: Louvain clustering to generate discrete states.
- **Action**: Calculate Flexibility (transitions) and Stability (Mean Dwell Time).

### Phase 3: Statistical Analysis
- **Action**: Spearman correlation.
- **Action**: FDR Correction.
- **Action**: Permutation Test (sufficient iterations).
- **Action**: Post-hoc Power Analysis (report MDE).

### Phase 4: Reporting
- **Action**: Generate `stats.json` (validated against `contracts/results_schema.yaml`).
- **Action**: Generate plots.