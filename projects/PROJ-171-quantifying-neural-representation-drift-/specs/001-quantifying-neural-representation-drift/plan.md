# Implementation Plan: Quantifying Neural Representation Drift During Skill Learning

**Branch**: `001-quantify-neural-drift` | **Date**: 2026-08-23 | **Spec**: `specs/001-quantify-neural-drift/spec.md`
**Input**: Feature specification from `/specs/001-quantify-neural-drift/spec.md`

## Summary

This project implements a CPU-tractable pipeline to quantify neural representation drift in electrophysiology data across training days. The core approach ingests raw or pre-sorted spike data, filters for unit stability (≥80% session presence), constructs daily population activity matrices, and computes a Representational Dissimilarity Matrix (RDM) using Pearson correlation distances. A linear model (`drift(t) = a + b·t`) is fitted to the RDM off-diagonals to extract the drift rate `b`. This rate is then correlated with behavioral learning speeds using permutation testing and Linear Mixed-Effects Models (LMM). The pipeline includes robustness checks (metric sweeping, threshold sensitivity) and strict data hygiene protocols.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `scikit-learn`, `statsmodels`, `nibabel` (for neuro formats), `openneuro` (via `datasets` or direct URL), `pytest`  
**Storage**: Local filesystem (`data/` for raw/derived, `artifacts/` for outputs); No persistent database.  
**Testing**: `pytest` with contract tests against YAML schemas; synthetic data generators for ground-truth validation.  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, ~7 GB RAM, ~14 GB Disk).  
**Project Type**: Computational Research Pipeline / CLI Tool  
**Performance Goals**: Complete full pipeline on available dataset subset within 6 hours; Memory usage < 7 GB via streaming/chunking.  
**Constraints**: CPU-only execution; No GPU acceleration; Strict adherence to unit stability criteria; No modification of raw data in place.  
**Scale/Scope**: Processing of multi-day electrophysiology sessions (N subjects, D days); Analysis of population vectors (Units × Conditions).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Status | Action Required |
|-----------|--------|-----------------|
| **I. Reproducibility** | PASS | Ensure `requirements.txt` pins versions; Random seeds set in `code/`; CI runs on fresh runner. |
| **II. Verified Accuracy** | PASS | All dataset URLs in `research.md` must be from the verified list; Citations validated by agent. |
| **III. Data Hygiene** | PASS | Raw data checksums recorded in `state/`; Derivations written to new files; No PII in `data/`. |
| **IV. Single Source of Truth** | PASS | All figures/stats trace to `data/` rows and `code/` blocks; No hand-typed numbers in paper. |
| **V. Versioning Discipline** | PASS | Content hashes for artifacts; `updated_at` timestamps updated on changes. |
| **VI. Neural Data Integrity** | PASS | Strict enforcement of ≥80% unit stability; Spike-sorting artifacts validated before inclusion. |
| **VII. Computational Robustness** | PASS | Drift metric implemented as linear model (per spec) with validation against alternatives; Permutation test (10k shuffles) included. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantify-neural-drift/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── neural-population.schema.yaml
│   ├── rdm-output.schema.yaml
│   └── drift-results.schema.yaml
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-171-quantifying-neural-representation-drift-/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── config.py              # Paths, seeds, thresholds
│   ├── data_ingestion.py      # Downloaders, validators
│   ├── preprocessing.py       # Unit filtering, alignment
│   ├── drift_analysis.py      # RDM, linear fit, drift rate
│   ├── correlation_analysis.py# LMM, permutation tests
│   ├── robustness.py          # Metric sweep, threshold sensitivity
│   └── main.py                # Orchestration
├── data/
│   ├── raw/                   # Downloaded datasets (checksummed)
│   ├── derived/               # Population matrices, RDMs
│   └── artifacts/             # Final results, plots
├── tests/
│   ├── contract/              # Schema validation tests
│   ├── unit/                  # Logic tests (synthetic data)
│   └── integration/           # End-to-end pipeline tests
└── state/
    └── projects/PROJ-171-quantifying-neural-representation-drift-.yaml
```

**Structure Decision**: Single project structure selected. The pipeline is a linear research workflow (Ingest -> Process -> Analyze -> Validate) best served by a modular CLI within a single package. This minimizes overhead for the 2-core CPU constraint and simplifies dependency management.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project scope is contained within a single analysis pipeline. | N/A |
