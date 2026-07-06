# Implementation Plan: The Influence of Narrative Framing on Attitudes Towards AI Assistance

**Branch**: `001-narrative-framing-ai-attitudes` | **Date**: 2026-06-27 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-narrative-framing-ai-attitudes/spec.md`

## Summary

This project implements a controlled experiment to test whether framing Large Language Model (LLM) assistance as a "collaborative partner" versus an "automated tool" influences user attitudes, perceived usefulness, and trust. The implementation generates controlled vignette stimuli, manages randomized participant assignment, collects survey data via a structured pipeline, and performs rigorous statistical analysis (Welch's t-tests, ordinal regression robustness checks, effect sizes, and multiple-comparison corrections) using CPU-only libraries (`scipy`, `statsmodels`, `pandas`) to ensure reproducibility on free-tier CI runners. The plan explicitly addresses causal inference via an Intent-to-Treat (ITT) primary analysis and includes a pilot study phase to validate the manipulation check instrument.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `textstat`, `vaderSentiment`, `sentence-transformers`, `pytest`  
**Storage**: Local CSV files (raw, cleaned, derived) under `data/`; JSON logs for metadata.  
**Testing**: `pytest` (unit tests for stimulus generation, randomization, pilot validation, and statistical outputs).  
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, limited RAM).  
**Project Type**: Research Data Pipeline / Statistical Analysis  
**Performance Goals**: Full pipeline (data generation -> analysis) < 30 minutes.  
**Constraints**: No GPU; no external API calls during analysis; strict adherence to sample size power (N=300 target); strict data hygiene (checksums, no PII).  
**Scale/Scope**: Stimuli variants; A substantial cohort of participants recruited (to account for attrition); primary dependent variables; Multiple simulated runs for randomization testing (verifying FR-002 and SC-002).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`; `requirements.txt` pins versions; analysis scripts are idempotent. |
| **II. Verified Accuracy** | **PASS** | All scale citations (Davis TAM, McKnight Trust) and dataset sources will be validated against primary sources before use. |
| **III. Data Hygiene** | **PASS** | Raw data immutable; derivations create new files with checksums; PII scan enforced via CI. |
| **IV. Single Source of Truth** | **PASS** | All statistics in `paper/` will be generated directly from `data/` via `code/`; no manual typing. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked in state YAML; `updated_at` timestamps updated on artifact changes. |
| **VI. Human Subjects Ethics** | **PASS** | **Implemented**: `code/00_ethics_gate.py` enforces IRB approval check and updates `state/...yaml` before recruitment. |
| **VII. Scale Validity** | **PASS** | Scales (TAM Attitude, Usefulness, Trust) will be implemented exactly per published scoring protocols; adaptations documented. |

## Project Structure

### Documentation (this feature)

```text
specs/001-narrative-framing-ai-attitudes/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-106-the-influence-of-narrative-framing-on-at/
├── code/
│   ├── 00_ethics_gate.py            # Checks IRB status, blocks recruitment if missing (Constitution VI)
│   ├── 01_stimulus_generation.py    # Generates vignettes, checks readability/sentiment/semantic similarity
│   ├── 02_randomization.py          # Assigns participants, exports condition metadata
│   ├── 03_pilot_study.py            # Executes FR-011: pilot data collection & manipulation check validation
│   ├── 04_data_collection.py        # Simulates/imports survey data, validates structure
│   ├── 05_analysis.py               # Welch's t-tests, ordinal regression, MDES, corrections, ITT analysis
│   └── requirements.txt             # Pinned dependencies
├── data/
│   ├── raw/                           # Raw survey exports (checksummed)
│   ├── processed/                     # Cleaned, flagged datasets
│   ├── stimuli/                       # Generated vignette CSVs
│   └── ethics/                        # IRB approval docs (access restricted)
├── tests/
│   ├── test_stimuli.py                # Unit tests for FR-001, FR-010, SC-001, SC-005
│   ├── test_randomization.py          # Unit tests for FR-002 (10k runs)
│   ├── test_pilot.py                  # Unit tests for FR-011 pilot validation logic
│   └── test_analysis.py               # Unit tests for FR-004 to FR-009, SC-002, SC-003, FR-007
│       ├── test_welch_ttest.py        # Tests primary ITT analysis
│       ├── test_sensitivity_analysis.py # Tests FR-007: exclusion sensitivity analysis
│       └── test_mdes.py               # Tests SC-002: MDES calculation logic
└── constitution.md                    # Project constitution (Root location per Constitution)
```

**Structure Decision**: Single-project structure (`code/`, `data/`, `tests/`) selected to align with the "Research Data Pipeline" nature. This minimizes overhead and ensures the analysis pipeline runs sequentially in a single environment. Added `00_ethics_gate.py` to enforce Constitution Principle VI programmatically.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Multiple Statistical Tests & Corrections** | Required by FR-006 (Benjamini-Hochberg) and FR-003 (3 DVs). | A simple t-test without correction would inflate Type I error, violating scientific rigor. |
| **Sensitivity Analysis** | Required by FR-007 (exclude manipulation check failures). | Ignoring failed checks would bias results; a single-pass analysis is insufficient for validity. |
| **Power Analysis & MDES Reporting** | Required by FR-009 and SC-002. | Running without power justification risks underpowered results. Post-hoc power is tautological; MDES is the scientifically sound alternative. |
| **Pilot Study (FR-011)** | Required to validate the manipulation check instrument before full deployment. | Skipping validation risks a failed experiment if the manipulation check is insensitive. |
