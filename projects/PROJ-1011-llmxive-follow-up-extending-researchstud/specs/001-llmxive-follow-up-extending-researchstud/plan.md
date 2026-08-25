# Implementation Plan: llmXive follow-up: extending "ResearchStudio-Idea"

**Branch**: `001-llmxive-extension` | **Date**: 2026-07-23 | **Spec**: `specs/001-llmxive-extension/spec.md`
**Input**: Feature specification from `specs/001-llmxive-extension/spec.md`

## Summary

This feature extends the "ResearchStudio-Idea" system to test the universality of multiple ML-derived ideation patterns. The system will ingest abstracts from ML and non-ML domains (Public Health, Climate Adaptation), map non-ML problem statements to ML patterns using a CPU-quantized embedding model, generate paired research proposals (pattern-guided vs. random-pattern vs. baseline), and subject them to expert evaluation. The core technical approach relies on a CPU-first pipeline using `sentence-transformers` (quantized), a small LLM (via Hugging Face Inference API with Ollama fallback), and rigorous statistical analysis (Linear Mixed-Effects Model with covariates) to determine if the patterns generalize.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `sentence-transformers`, `transformers`, `scikit-learn`, `pandas`, `numpy`, `requests`, `pyyaml`, `statsmodels`, `prolific-api` (for recruitment logic)
**Storage**: Local file system (`data/` for raw/processed JSON/CSV), GitHub Actions ephemeral storage
**Testing**: `pytest` (unit tests for data parsing, statistical logic; integration tests for pipeline flow)
**Target Platform**: Linux (GitHub Actions Free Runner: 2 vCPU, 7 GB RAM, 14 GB Disk)
**Project Type**: Computational Research Pipeline / CLI
**Performance Goals**: Complete end-to-end pipeline (download -> generate -> analyze) within ≤6 hours; Memory usage < 7 GB at peak.
**Constraints**: Must run on CPU; no local GPU; data must be openly downloadable (no paywalls); statistical rigor (FWER correction, power acknowledgement, IRR gate).
**Scale/Scope**: A sample of abstracts (comprising ML, Non-ML accepted, and Non-ML rejected categories) will be collected to address the research question using the specified method (Citation: DOI/Author-Year).; problem statements; A set of generated proposals (Pattern, Random, Baseline); Multiple expert ratings per proposal.

## Constitution Check

*Gates determined based on `projects/PROJ-1011-llmxive-follow-up-extending-researchstud/.specify/memory/constitution.md`*

1.  **I. Reproducibility**:
    *   **Action**: All random seeds (numpy, torch, python) pinned in `code/`.
    *   **Action**: External datasets fetched via deterministic URLs or `datasets` library.
    *   **Action**: `requirements.txt` pins exact versions.
2.  **II. Verified Accuracy**:
    *   **Action**: `code/utils/validate_citations.py` runs before analysis.
    *   **Action**: CI Step: `.github/workflows/ci.yml` includes a `validate_citations` stage that blocks merge if any citation is unreachable or mismatch.
    *   **Action**: Title-token-overlap threshold ≥ 0.7 enforced by validator.
3.  **III. Data Hygiene**:
    *   **Action**: Raw data checksums recorded in `state/` manifest.
    *   **Action**: No in-place modification; derivations written to new files (e.g., `data/raw/...` -> `data/processed/...`).
    *   **Action**: PII scan integrated into CI.
4.  **IV. Single Source of Truth**:
    *   **Action**: All statistics in the final report generated directly from `code/` output, not hand-typed.
    *   **Action**: Figures trace to `data/` rows.
5.  **V. Versioning Discipline**:
    *   **Action**: Content hashes for all artifacts in `state/`.
    *   **Action**: `code/utils/update_state.py` updates `state/...yaml` `updated_at` timestamps on every artifact change as required by Principle V.
6.  **VI. Cross-Domain Pattern Validity**:
    *   **Action**: Pattern mapping uses `all-MiniLM-L6-v2` (quantized) as specified.
    *   **Action**: Claims of generalization strictly tied to statistical comparison of expert ratings (FR-005).
7.  **VII. Human-in-the-Loop Evaluation Integrity**:
    *   **Action**: Analysis uses only human scores (no model metrics as proxies).
    *   **Action**: Blind evaluation protocol enforced in data preparation (metadata stripped).
    *   **Action**: IRR gate (Krippendorff's alpha ≥ 0.6) enforced before aggregation.

## Test Traceability Matrix

| User Story | Acceptance Scenario | Test Function | Status |
| :--- | :--- | :--- | :--- |
| **US-1** | Download a representative set of abstracts distributed across the three target domains. | `test_download_and_parse_open_datasets` | Planned |
| **US-1** | Pre-processing: non-empty abstract | `test_preprocessing_validation` | Planned |
| **US-1** | Memory usage < 7 GB | `test_memory_usage_constraint` | Planned |
| **US-2** | Top-3 pattern retrieval (similarity) | `test_pattern_mapping_similarity` | Planned |
| **US-2** | Pattern Mapping Validation (Hold-out) | `test_pattern_mapping_validation` | Planned |
| **US-2** | Generation: multiple pairs + random control | `test_proposal_generation_logic` | Planned |
| **US-3** | Statistical test (Normality check) | `test_statistical_normality_check` | Planned |
| **US-3** | FWER Correction (Bonferroni/BH) | `test_multiple_comparison_correction` | Planned |
| **US-3** | IRR Gate (Alpha ≥ 0.6) | `test_inter_rater_reliability_gate` | Planned |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-extension/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/
├── 01_data_acquisition.py       # Downloads and parses abstracts (FR-001)
├── 02_pattern_mapping.py        # Embedding and top-3 retrieval (FR-002)
├── 02_pattern_validation.py     # Hold-out validation for pattern mapping
├── 03_proposal_generation.py    # LLM generation (pattern vs random vs baseline) (FR-003)
├── 04_evaluation_loader.py      # Loads expert ratings (FR-004)
├── 05_statistical_analysis.py   # Tests, corrections, reporting (FR-005, FR-006)
├── utils/
│   ├── config.py                # Seed pinning, path constants
│   ├── validators.py            # Data hygiene checks
│   ├── validate_citations.py    # Citation validation (Principle II)
│   └── update_state.py          # State update script (Principle V)
├── requirements.txt             # Pinned dependencies
└── run_pipeline.sh              # Orchestration script

tests/
├── unit/
│   ├── test_data_parsing.py
│   ├── test_pattern_mapping.py
│   └── test_statistical_logic.py
└── integration/
    └── test_full_pipeline.py
```

**Structure Decision**: Single project structure within `code/` directory. Chosen for simplicity and to minimize I/O overhead on the constrained GitHub Actions runner. All scripts are sequential but batched where possible to manage memory.

## Complexity Tracking

*No violations detected. The pipeline is linear and fits within the defined constraints.*