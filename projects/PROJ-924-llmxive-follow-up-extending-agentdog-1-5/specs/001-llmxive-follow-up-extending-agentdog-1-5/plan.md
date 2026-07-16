# Implementation Plan: llmXive Follow-up: Extending AgentDoG 1.5 with Zero-Shot Drift Detection

**Branch**: `001-llmxive-drift-detection` | **Date**: 2026-07-16 | **Spec**: `specs/001-llmxive-drift-detection/spec.md`
**Input**: Feature specification from `specs/001-llmxive-drift-detection/spec.md`

## Summary

This project implements a lightweight, zero-shot drift detection system to identify novel, emergent agent attack vectors by measuring semantic divergence from the fixed AgentDoG 1.5 safety taxonomy. The core methodology involves generating centroid embeddings for taxonomy categories using `all-MiniLM-L6-v2`, computing minimum cosine distances for input logs, and validating the "Drift Score" against human-annotated ground truth derived from an independent taxonomy (OWASP Top 10 for LLM) and adversarial dataset (AdvBench). The system is designed to run entirely on a GitHub Actions free-tier runner (CPU-only, standard RAM) without requiring GPU acceleration or retraining.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `sentence-transformers`, `scikit-learn`, `pandas`, `numpy`, `datasets`, `jsonschema`, `statsmodels`  
**Storage**: Local file system (CSV/JSON for logs and results)  
**Testing**: `pytest` (unit, integration, and contract validation), statistical tests (Mann-Whitney U, Logistic Regression, Kappa)  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: Research Tool / CLI  
**Performance Goals**: Process 500 logs in ≤ 30 minutes; Peak RAM ≤ 4GB  
**Constraints**: No local GPU; No external API calls for inference (except data fetch); Deterministic reproducibility  
**Scale/Scope**: A substantial volume of agent logs per run; Taxonomy size fixed (~few to several categories)  

> Domain-specific empirical specifics are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates `random_seed` pinning in `code/`; `requirements.txt` for isolated env; data fetched from canonical sources (HuggingFaceH4, AdvBench). |
| **II. Verified Accuracy** | **PASS** | All citations (taxonomy source, model) will be verified via Reference-Validator before code execution. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of raw data; no in-place modification; PII scan enforced. |
| **IV. Single Source of Truth** | **PASS** | All metrics (AUC, p-values) derived from `code/` output, not hand-typed. |
| **V. Versioning Discipline** | **PASS** | Content hashes recorded in state YAML; artifacts versioned. |
| **VI. Zero-Shot Drift Detection Validity** | **PASS** | Plan explicitly includes US-02 (Human-in-the-Loop) with a dedicated `annotator_interface.py` script to enforce -annotator workflow and `test_kappa.py` to verify Kappa > 0.6. |
| **VII. Resource-Constrained Integrity** | **PASS** | Method uses `all-MiniLM-L6-v2` (CPU-friendly); batch processing logic defined to stay < 7GB RAM. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-drift-detection/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── taxonomy_centroid.schema.yaml
│   ├── agent_log.schema.yaml
│   └── drift_result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/
├── __init__.py
├── config.py            # Configs, seeds, paths
├── data_loader.py       # Fetch and validate data (HuggingFaceH4, AdvBench)
├── taxonomy_builder.py  # Generate centroids
├── drift_scoring.py     # Compute distances
├── validation.py        # Human-in-the-loop stats (US-02)
├── comparison.py        # Baseline LLM comparison (US-03)
├── annotator_interface.py # Generates blinded CSVs for multiple annotators
├── main.py              # Orchestration script
└── utils.py             # Contract validation helpers

projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/
├── raw/                 # Original logs, taxonomy source
├── processed/           # Centroids, stratified CSVs, blinded exports
└── checksums.json       # Integrity records

projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/
├── unit/
│   ├── test_taxonomy_builder.py
│   ├── test_drift_scoring.py
│   ├── test_kappa.py       # Verifies Kappa calculation logic
│   ├── test_blind.py       # Verifies drift_score removal before export
│   └── test_contracts.py   # Validates CSVs against schema files
└── integration/
    └── test_end_to_end.py
```

**Structure Decision**: Single project structure within `code/` directory. This minimizes overhead for a research tool and keeps the data flow (raw -> processed -> results) linear and easy to trace for reproducibility.

## Complexity Tracking

> No violations found. The complexity is managed by the strict CPU-first constraint and the modular separation of scoring, validation, and comparison logic.