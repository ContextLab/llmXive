# Implementation Plan: Exploring the Correlation Between Solar Flare Characteristics and Geomagnetic Storm Intensities

**Branch**: `001-solar-flare-storm-correlation` | **Date**: 2026-06-25 | **Spec**: `specs/001-solar-flare-storm-correlation/spec.md`

## Summary

This feature implements a CPU-tractable pipeline to analyze the **association** between solar flare X-ray peak flux, CME speeds, and geomagnetic storm intensities (Dst index). The pipeline ingests data from NOAA SWPC (flares, Dst) and CDAWeb (CMEs) over an extended multi-year window, aligns events within a short temporal window, and performs statistical analysis (Spearman correlation, separate univariate regression with VIF checks, and threshold **consistency** analysis) on a time-series split (historical train, recent test). The implementation strictly adheres to the project constitution's reproducibility and data hygiene principles, ensuring all findings are framed as **associational** and explicitly acknowledging limitations regarding circular validation and selection bias.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `requests`, `pyyaml`, `pytest`  
**Storage**: Local CSV/JSON/Parquet files in `data/` and `results/`  
**Testing**: `pytest` with contract validation against `contracts/*.schema.yaml`.
  - `align.py` validates output against `contracts/aligned_event.schema.yaml`.
  - `analysis.py` validates output against `contracts/metrics.schema.yaml`.
**Target Platform**: Linux (GitHub Actions free-tier: CPU, ~7 GB RAM, no GPU)  
**Project Type**: Data analysis pipeline / CLI  
**Performance Goals**: Execution ≤ 6 hours, Peak RAM ≤ 7 GB  
**Constraints**: No GPU/CUDA; missing data flagged but not dropped (analysis defaults to univariate to avoid bias); time-series split for temporal stability check; VIF > 5 triggers univariate fallback.  
**Scale/Scope**: A multi-decade span of solar/geomagnetic events (estimated N < 500 storms).

> **Dataset Variable Fit Warning**: The "Verified datasets" block provided contains NO verified source for the specific NOAA GOES flare lists or CDAWeb LASCO CME catalog required by the spec. The spec explicitly mandates direct ingestion from `ftp://ftp.swpc.noaa.gov` and CDAWeb. The plan below implements this direct ingestion strategy (using `requests`/`urllib` for HTTP/FTP) rather than relying on the provided HF links, which are for unrelated NLP/Finance tasks. If direct ingestion fails due to network restrictions on the runner, the plan includes a fallback to generate a synthetic dataset for testing logic, but the primary research path assumes direct access.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

1.  **I. Reproducibility**: **COMPLIANT**. Plan mandates `requirements.txt` pinning, random seed setting, and checksumming of raw data in `data/source_manifest.yaml`.
2.  **II. Verified Accuracy**: **COMPLIANT**. Plan requires invoking the Reference-Validator Agent to perform a **title-token-overlap check (≥0.7)** on all citations (e.g., Zhang et al., 2020) before finalizing results. No HF URLs will be cited for solar physics data.
3.  **III. Data Hygiene**: **COMPLIANT**. Raw data preserved; transformations create new files; checksums recorded.
4.  **IV. Single Source of Truth**: **COMPLIANT**. All metrics derived from `data/aligned_events.csv` via `code/analysis.py`.
5.  **V. Versioning Discipline**: **COMPLIANT**. Plan includes a specific **Versioning Mechanism** (see below) to generate content hashes and update the project state file.
6.  **VI. Solar Event Data Provenance**: **COMPLIANT**. Plan explicitly defines `data/source_manifest.yaml` to record FTP/HTTP URLs and retrieval timestamps.
7.  **VII. Statistical Analysis Transparency**: **COMPLIANT**. Plan mandates `scipy`/`statsmodels` for correlations/regressions and output to `results/metrics.json`.

### Versioning Mechanism (Principle V Implementation)

To satisfy Constitution Principle V, the following mechanism is implemented:
1.  **Script**: A dedicated `code/versioning.py` script is executed after each major pipeline stage (Ingest, Align, Analyze).
2.  **Hashing**: The script computes the SHA-256 hash of all output artifacts (e.g., `aligned_events.csv`, `metrics.json`).
3.  **State Update**: The script acquires a file lock on `state/projects/PROJ-031-exploring-the-correlation-between-solar-.yaml`, updates the `artifact_hashes` map with the new hashes, and updates the `updated_at` timestamp.
4.  **Validation**: The `Advancement-Evaluator` agent reads this state file to invalidate stale review records if hashes change.

## Project Structure

### Documentation (this feature)

```text
specs/001-solar-flare-storm-correlation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── aligned_event.schema.yaml
│   └── metrics.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-031-exploring-the-correlation-between-solar-/
├── data/
│   ├── raw/                 # Downloaded CSV/JSON from NOAA/CDAWeb
│   ├── processed/           # Aligned events, cleaned datasets
│   └── source_manifest.yaml # Provenance tracking
├── code/
│   ├── __init__.py
│   ├── ingest.py            # Data download and parsing
│   ├── align.py             # Event matching logic
│   ├── analysis.py          # Correlation, regression, power analysis
│   ├── validate.py          # Contract validation
│   ├── versioning.py        # Hash generation and state update
│   └── main.py              # Entry point
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/            # Schema validation tests
├── results/
│   ├── metrics.json
│   ├── figures/
│   └── logs/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure chosen for a data pipeline. Separation of `ingest`, `align`, and `analysis` ensures modularity and testability. `data/raw` is distinct from `data/processed` to satisfy Constitution Principle III.

## Complexity Tracking

No violations detected. The complexity is managed by strict adherence to CPU constraints and the use of established statistical libraries.