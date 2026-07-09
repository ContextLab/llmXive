# Implementation Plan: Mindfulness Components and Delivery Formats in ASD Social Skills

**Branch**: `001-mindfulness-asd-social-skills` | **Date**: 2026-06-26 | **Spec**: `specs/001-mindfulness-asd-social-skills/spec.md`

## Summary

This feature implements a reproducible meta-analysis pipeline to evaluate the efficacy of mindfulness components (breath awareness, body scan, loving-kindness) and delivery formats (caregiver-mediated vs. child-led) on social skills in children (aged 6-12) with Autism Spectrum Disorder (ASD). The system ingests data from ClinicalTrials.gov, OSF, and verified open-access repositories, calculates Hedges' *g* effect sizes, performs random-effects meta-analysis, and generates publication-quality visualizations. The implementation strictly adheres to CPU-only constraints for GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `statsmodels`, `matplotlib`, `requests`, `pyyaml`, `pytest`, `bayesmeta` (for Bayesian fallback)  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/interim`, `state`)  
**Testing**: `pytest` with contract validation against YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, 7 GB RAM)  
**Project Type**: Data Science Pipeline / CLI  
**Performance Goals**: Complete pipeline execution within 6 hours on CPU-only hardware; memory usage < 7 GB.  
**Constraints**: No GPU; no heavy LLM inference; strict adherence to FR-001 retry logic for API calls; dataset variable fit must be verified before analysis.  
**Scale/Scope**: Processing of studies retrieved from ClinicalTrials.gov/OSF, with subgroup analysis contingent on N >= 20 per updated methodology.

> Domain-specific empirical specifics (exact counts, dataset sizes) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action / Justification |
|-----------|--------|------------------------|
| I. Reproducibility | **PASS** | All random seeds pinned in `code/`. External datasets fetched from canonical sources (ClinicalTrials.gov API, OSF API, PMC) with checksums recorded. |
| II. Verified Accuracy | **PASS** | All citations in `research.md` will be validated against the "Verified datasets" block. No invented URLs. |
| III. Data Hygiene | **PASS** | Raw data preserved; derivations written to new files. PII scan integrated into CI. |
| IV. Single Source of Truth | **PASS** | Figures/statistics in paper trace to `data/processed` CSV and `code/` scripts. |
| V. Versioning Discipline | **PASS** | Content hashes for artifacts will be managed in `state/` via `scripts/hash_artifacts.py`. |
| VI. Clinical Trial Registry Integrity | **PASS** | Analysis restricted to ClinicalTrials.gov/OSF over the past decade. Search queries logged. |
| VII. Caregiver-Mediated Delivery Verification | **PASS** | `delivery_format` field explicitly tagged; ambiguous entries flagged/excluded from subgroup analysis; manual double-coding protocol included. |

## Project Structure

### Documentation (this feature)

```text
specs/001-mindfulness-asd-social-skills/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── cleaned_study.schema.yaml
│   └── effect_size.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-008-psychology-research/
├── code/
│   ├── __init__.py
│   ├── main.py                 # Orchestration entry point
│   ├── data/
│   │   ├── collector.py        # API ingestion (FR-001, FR-002)
│   │   ├── extractor.py        # Data extraction (FR-003, FR-009)
│   │   └── cleaner.py          # Validation & cleaning (FR-007)
│   ├── analysis/
│   │   ├── effect_sizes.py     # Hedges' g calculation (FR-004, FR-013)
│   │   ├── meta_analysis.py    # Random-effects model (FR-005, FR-011, FR-012)
│   │   └── bias.py             # Publication bias tests (FR-006, FR-014)
│   ├── viz/
│   │   └── plots.py            # Forest & Funnel plots (FR-006)
│   └── utils/
│       ├── config.py           # Constants & seeds
│       └── logging.py          # Structured logging (FR-007)
├── data/
│   ├── raw/                    # API dumps (immutable)
│   ├── interim/                # Intermediate JSON/CSV
│   └── processed/              # Final clean CSV for analysis
├── contracts/                  # Schema definitions
│   ├── cleaned_study.schema.yaml
│   └── effect_size.schema.yaml
├── state/                      # Versioning & Hashing
│   └── projects/PROJ-008-psychology-research.yaml
├── scripts/                    # Utility scripts
│   └── hash_artifacts.py       # Generates/updates state hashes
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── docs/
    ├── protocol.md
    └── results.md
```

**Structure Decision**: Single project structure selected to maintain tight coupling between data ingestion, analysis, and visualization, ensuring reproducibility as per Constitution Principle I.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations identified. | The plan strictly follows the spec and CPU constraints. |