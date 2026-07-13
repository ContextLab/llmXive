# Implementation Plan: llmXive follow-up: extending "Intern-Atlas: A Methodological Evolution Graph as Research Infrastruct"

**Branch**: `001-methodological-evolution-fragility` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-follow-up-extending-intern-atlas/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-intern-atlas/spec.md`

## Summary

This feature implements a computational study to determine if the topological structure of methodological evolution graphs (specifically the ratio of 'bottleneck-resolving' edges to 'incremental-variant' edges) predicts the long-term reproducibility or stability of a methodological lineage. The system will ingest the Intern-Atlas graph snapshot and external retraction/replication databases to compute topological features (Bottleneck Resolution Ratio, Branching Entropy) for nodes published within a defined historical period. It will then train a lightweight logistic regression model to predict retraction status (Fragile vs. Robust) and compare it against a citation-count baseline, performing mandatory permutation tests (n=100) and threshold sensitivity analyses (cutoffs {0.3, 0.5, 0.7}) as defined in the specification.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `networkx`, `pandas`, `scikit-learn`, `numpy`, `pyyaml`, `requests`, `statsmodels` (for Firth's regression if needed)  
**Storage**: Local CSV/Parquet files under `data/` (raw and derived). SQLite used ONLY for transient runtime caching (not persisted to `data/`, does not violate Data Hygiene Principle III).  
**Testing**: `pytest` (unit tests for feature extraction logic, integration tests for pipeline flow).  
**Target Platform**: Linux server (GitHub Actions free-tier: 2 CPU, 7GB RAM).  
**Project Type**: Computational research pipeline / CLI tool.  
**Performance Goals**: Complete full pipeline (extraction, modeling, validation) within 6 hours on CPU-only runner.  
**Constraints**: 
- No GPU usage; memory footprint < 7GB.
- **Strict adherence to spec-defined thresholds**: 
  - Permutation test: **n=100** (FR-007).
  - Threshold sweep: **{0.3, 0.5, 0.7}** (FR-008).
  - VIF/MI Flag: **VIF > 5** or **MI > 0.1** (FR-009).
  - Fuzzy match: **Levenshtein >= 0.95** (FR-011, revised for precision).
  - Label mapping: **1=Methodological, 2=Fraud, 0=Robust** (FR-004).
  - Duplicate resolution: **Earliest date, then alphabetical journal** (FR-010).
  - Confounding control: **Mandatory stratified permutation test or covariate adjustment** (FR-012).
- **Exclude LLM-inferred edge types** (FR-002).
- **Filter nodes -2018** (FR-001).
- **CITATION_TITLE_OVERLAP_THRESHOLD = 0.7** (Constitution Principle II).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned random seeds, deterministic data fetching, and isolated virtualenv execution. |
| **II. Verified Accuracy** | **PASS** | External citations (Retraction Watch, Intern-Atlas) will be validated against primary sources via the Reference-Validator Agent with **CITATION_TITLE_OVERLAP_THRESHOLD = 0.7**. |
| **III. Data Hygiene** | **PASS** | Plan mandates checksumming of raw data, immutable derivations, and PII scanning. SQLite usage is strictly transient and does not violate immutability. |
| **IV. Single Source of Truth** | **PASS** | All metrics will be derived from `data/` and `code/`; no hand-typed numbers in reports. |
| **V. Versioning Discipline** | **PASS** | Content hashes will be recorded in `state/`; artifact updates will trigger **state/...yaml `updated_at` timestamp** updates. |
| **VI. Graph-Topology Non-Circularity** | **PASS** | Plan explicitly separates feature extraction (topology) from label assignment (external retraction DB) to prevent circular evaluation. **Specific blinding mechanism**: The `run_extraction.py` script explicitly strips any retraction metadata from the graph before feature calculation and strictly separates the label assignment logic (external DB) from the feature extraction logic. |
| **VII. Interpretability** | **PASS** | Logistic regression (interpretable coefficients) is the mandated model; black-box embeddings are excluded. |

## Project Structure

### Documentation (this feature)

```text
specs/001-methodological-evolution-fragility/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── model.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-815-llmxive-follow-up-extending-intern-atlas/
├── data/
│   ├── raw/                 # Downloaded raw graph snapshots and DB dumps
│   ├── derived/             # Computed features, labeled datasets
│   └── cache/               # Temporary processing artifacts
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── run_extraction.py          # Implements FR-001, FR-002, FR-003, FR-004, FR-010, FR-011. Includes abort logic for missing ground truth.
│   ├── run_training.py            # Implements FR-005, FR-006, FR-007, FR-008, FR-009, FR-012
│   ├── utils/
│   │   ├── graph_utils.py         # Feature calculation logic (blinded to retraction status)
│   │   ├── match_utils.py         # DOI/Title matching logic (Levenshtein >= 0.95)
│   │   └── stats_utils.py         # Permutation (n=100), VIF, MI, Threshold Sweep {0.3, 0.5, 0.7} logic
│   └── tests/
│       ├── test_extraction.py
│       └── test_training.py
├── data/
│   ├── raw/                       # Downloaded Intern-Atlas snapshot, Retraction DB
│   └── processed/                 # Derived CSVs with features and labels
├── paper/
│   └── results/                   # Generated plots and final reports
└── state/
    └── projects/PROJ-815-llmxive-follow-up-extending-intern-atlas.yaml
```

**Traceability Matrix**:
- `run_extraction.py`: FR-001 (Filter 2010-2018), FR-002 (Edge types), FR-003 (Entropy), FR-004 (Labels), FR-010 (Duplicates), FR-011 (Fuzzy match), **Abort logic for missing ground truth**.
- `run_training.py`: FR-005 (Topo Model), FR-006 (Baseline), FR-007 (Perm n=100), FR-008 (Sweep {0.3, 0.5, 0.7}), FR-009 (VIF/MI), FR-012 (Confounding).

**Structure Decision**: A single `code/` directory with modular scripts (`run_extraction.py`, `run_training.py`) is selected to align with the linear pipeline nature of the research (Extraction -> Training -> Validation). This avoids the complexity of a web service or multi-language setup, ensuring maximum compatibility with the CPU-only CI runner. Directory creation is consolidated into Phase 1 setup tasks.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed. | N/A |