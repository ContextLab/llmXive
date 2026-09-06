# Implementation Plan: llmXive follow-up: extending "AI for Auto-Research: Roadmap & User Guide"

**Branch**: `001-llmxive-followup` | **Date**: 2026-07-10 | **Spec**: [link to spec.md]
**Input**: Feature specification from `specs/001-llmxive-followup/spec.md`

## Summary

This project implements a predictive analysis pipeline to determine if topological anomalies in AI-generated literature review graphs correlate with experimental failure. The approach involves: (1) parsing "Creation" phase logs to construct directed entity-relation graphs; (2) extracting topological metrics (cycle density, isolation ratio, semantic distance); (3) training an interpretable Logistic Regression classifier (with Random Forest fallback) against ground-truth failure labels; and (4) validating significance via permutation testing. The entire pipeline is designed to run within 6 hours on a CPU-only GitHub Actions runner with ≤7 GB RAM.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `networkx`, `scikit-learn`, `spacy`, `sentence-transformers` (CPU-optimized `all-MiniLM-L6-v2`), `pandas`, `numpy`, `scipy`, `pytest`  
**Storage**: Local filesystem (CSV/Parquet) under `data/` and `code/`  
**Testing**: `pytest` (unit tests for graph construction, integration tests for full pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data analysis pipeline / CLI tool  
**Performance Goals**: Complete pipeline execution ≤ 6 hours; Memory usage ≤ 7 GB; Dataset streaming for large inputs.  
**Constraints**: CPU-only execution for core logic; no GPU acceleration for training; strict data hygiene (no in-place modification); reproducible random seeds.  
**Scale/Scope**: Dependent on the "AI for Auto-Research" benchmark size (deferred to data exploration, but assumed ≤ 10k samples for CPU feasibility).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Strategy |
|-----------|--------|-----------------------|
| **I. Reproducibility** | PASS | All scripts in `code/` will pin random seeds (`np.random.seed`, `torch.manual_seed` if applicable, `random.seed`). Dependencies pinned in `requirements.txt`. Dataset sources will be canonical URLs or HF dataset IDs. |
| **II. Verified Accuracy** | PASS | Citations in `research.md` and `plan.md` will be validated against primary sources. **Automated Enforcement**: The `data_ingestion.py` and `graph_construction.py` scripts will invoke the **Reference-Validator Agent** to verify citations, enforcing the `CITATION_TITLE_OVERLAP_THRESHOLD` at an empirically determined level before proceeding. |
| **III. Data Hygiene** | PASS | Raw data will be checksummed upon download. All transformations (graph construction, feature extraction) will write to new files in `data/processed/`. **Automated Enforcement**: The `data_ingestion.py` script will execute a **PII scan** via the **Repository-Hygiene Agent** to ensure no PII is present before data is committed. |
| **IV. Single Source of Truth** | PASS | All figures and statistics in the final report will be generated programmatically from `data/` and `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | PASS | Artifacts will carry content hashes. **Automated Enforcement**: A `versioning_manager.py` script will be executed after each pipeline phase to compute content hashes and update the project's `state/` YAML file with the new `artifact_hashes` map, ensuring the `updated_at` timestamp is refreshed. |
| **VI. Topological Metric Integrity** | PASS | The graph construction logic will include **triplet validation steps** where extracted triplets are cross-referenced against the source text (using fuzzy matching) to confirm that "isolation ratio" reflects genuine lack of grounding, not parsing errors. Default values will be logged for empty graphs. |
| **VII. CPU-Bound Execution** | PASS | `sentence-transformers` will be loaded in CPU mode. `scikit-learn` models are CPU-native. Permutation tests will be capped to ensure ≤ 6h runtime. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-followup/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-836-llmxive-follow-up-extending-ai-for-auto/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data_ingestion.py       # Download, checksum, PII scan, Reference-Validator
│   ├── graph_construction.py   # NLP parsing, triplet extraction, validation, graph building
│   ├── metric_engine.py        # Compute cycle density, isolation ratio, semantic distance
│   ├── model_training.py       # LR/RF training, CV, permutation test, bootstrap
│   ├── versioning_manager.py   # Update state/ YAML with artifact hashes
│   └── main.py                 # Orchestration script
├── data/
│   ├── raw/                    # Downloaded benchmark data (checksummed)
│   ├── processed/              # Graphs, feature matrices, labels
│   └── checksums.json          # Artifact hashes
├── tests/
│   ├── unit/                   # Unit tests for graph/metric logic
│   └── integration/            # End-to-end pipeline tests
└── output/                     # Generated reports, plots
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) selected for simplicity and alignment with data science workflows. This minimizes overhead and ensures all data artifacts are centrally managed under `data/` with strict hygiene.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **None** | The scope is contained within a single pipeline. No additional microservices or complex architectures are required. | N/A |

## FR/SC Coverage Map

| Requirement/Scenario | Plan Element | Status |
|----------------------|--------------|--------|
| **FR-001** (Parse text, extract triplets) | `graph_construction.py` (NLP parsing) | Covered |
| **FR-002** (Compute metrics: cycle density, isolation ratio, semantic distance) | `metric_engine.py` (Metric calculation) | Covered |
| **FR-003** (Map graphs to labels) | `data_model.py` (Label mapping) | Covered |
| **FR-004** (Train LR/RF, report coefficients/SHAP) | `model_training.py` (Model training) | Covered |
| **FR-005** (5-fold CV, report AUC) | `model_training.py` (Cross-validation) | Covered |
| **FR-006** (Permutation test, min 1000 iterations) | `model_training.py` (Permutation test) | Covered |
| **FR-007** (Handle missing labels) | `data_ingestion.py` (Filtering) | Covered |
| **FR-008** (Log default metric assignments) | `metric_engine.py` (Logging) | Covered |
| **FR-009** (Verify external labels) | `data_ingestion.py` (Metadata check) | Covered |
| **FR-010** (Report isolation as proxy, state limitation) | `model_training.py` (Report generation) | Covered |
| **SC-001** (AUC vs 0.5 baseline) | `model_training.py` (Performance report) | Covered |
| **SC-002** (P-value vs null hypothesis) | `model_training.py` (Significance test) | Covered |
| **SC-003** (CPU feasibility ≤ 6h) | `model_training.py` (Runtime guard) | Covered |
| **SC-004** (Null result validity) | `model_training.py` (Result reporting) | Covered |
| **SC-005** (Data completeness) | `metric_engine.py` (Validation) | Covered |
| **US-1** (Graph construction) | `graph_construction.py` | Covered |
| **US-2** (Model training) | `model_training.py` | Covered |
| **US-3** (Statistical verification) | `model_training.py` | Covered |
| **Edge Case: Empty text** | `metric_engine.py` (Default values) | Covered |
| **Edge Case: Duplicate entities** | `graph_construction.py` (Node merging) | Covered |
| **Edge Case: Missing labels** | `data_ingestion.py` (Filtering) | Covered |