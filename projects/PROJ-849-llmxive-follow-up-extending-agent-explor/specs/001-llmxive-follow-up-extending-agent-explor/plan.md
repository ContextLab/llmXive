# Implementation Plan: Semantic Divergence Diagnostic for Agentic Reasoning

**Branch**: `001-llmxive-semantic-gap-diagnostic` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-follow-up-extending-agent-explor/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-agent-explor/spec.md`

## Summary

This feature implements a diagnostic tool to quantify the "Semantic Divergence Score" between an agent's internal "thinking" process and the external tool actions it selects. The system extracts thinking prefixes from a MathVista subset, generates a tool-action distribution via BM25 retrieval against a curated mapping, and computes cosine similarity to derive a divergence metric. It then correlates this metric with simulated RL failure rates and trains a logistic regression classifier to predict failure, validating the hypothesis that a "thinking-acting gap" predicts agent failure.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (DistilBERT), `rank_bm25`, `scikit-learn`, `pandas`, `datasets`, `pyyaml`  
**Storage**: Local JSON/Parquet files (`data/`), HuggingFace cache  
**Testing**: `pytest` with contract validation  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Research CLI / Data Analysis Pipeline  
**Performance Goals**: < 7 GB RAM peak, < 5 hours runtime, CPU-only execution  
**Constraints**: Must handle missing tool mappings gracefully; must enforce sample size N ≥ 30; must downsample if N > 500 or memory exceeds limits.  

### Verified Accuracy & Failure Modes

To comply with **Constitution Principle II (Verified Accuracy)**:
- **Unreachable Verified URLs**: If a verified dataset URL (e.g., MathVista) fails to resolve or returns a non-200 status during the download phase, the system MUST **immediately halt** with error code `ERR_DATASET_UNREACHABLE` and a message citing the specific URL. It MUST **NOT** attempt to fallback to a cached version, an alternative dataset, or a synthetic placeholder. This prevents silent data corruption or hallucination.
- **Missing Local Artifacts**: If the local tool mapping file (`data/tool_mappings/mathvista_tool_map.json`) is missing, the system halts with `ERR_TOOL_MAPPING_MISSING`.
- **Verification Gate**: The `run_diagnostic.py` entry point includes a pre-flight check that attempts a `HEAD` request on all verified dataset URLs before proceeding. If any fail, the job aborts before consuming compute resources.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds, `requirements.txt`, and re-runnable scripts. |
| **II. Verified Accuracy** | **PASS** | Citations restricted to verified dataset URLs; **Explicit halt** defined for unreachable URLs to prevent silent fallback. |
| **III. Data Hygiene** | **PASS** | Plan specifies checksumming raw data and immutable derivations. Raw data is checksummed and the hashes are recorded in `state/projects/PROJ-849-llmxive-follow-up-extending-agent-explor.yaml`. |
| **IV. Single Source of Truth** | **PASS** | Metrics trace directly to `data/` rows and `code/` logic. |
| **V. Versioning Discipline** | **PASS** | Content hashes will be generated for artifacts using a script integrated into the CI pipeline, updating the project's state file (`state/projects/PROJ-849-llmxive-follow-up-extending-agent-explor.yaml`) with artifact checksums. |
| **VI. Semantic Divergence Quantification** | **PASS** | Metric defined strictly as cosine similarity between thinking and BM25-retrieved tool centroid, generated dynamically by the Thought-to-Action Simulator. |
| **VII. Diagnostic Validation Rigor** | **PASS** | Logistic regression validates predictive power against independent failure outcomes with problem difficulty as a covariate. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-agent-explor/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-849-llmxive-follow-up-extending-agent-explor/code/
├── src/
│   ├── models/
│   │   └── divergence_model.py      # Embedding & scoring logic
│   ├── services/
│   │   ├── retrieval_service.py     # BM25 index & retrieval
│   │   └── analysis_service.py      # Correlation & Logistic Regression
│   ├── cli/
│   │   └── run_diagnostic.py        # Entry point
│   └── lib/
│       └── config.py                # Constants, seeds, paths
├── tests/
│   ├── contract/
│   │   └── test_schemas.py          # Validates output against YAML schemas
│   ├── integration/
│   │   └── test_pipeline.py         # End-to-end flow
│   └── unit/
│       └── test_retrieval.py        # BM25 edge cases
├── data/
│   ├── raw/                         # Downloaded datasets
│   └── tool_mappings/
│       └── mathvista_tool_map.json  # Curated mapping
└── requirements.txt
```

**Structure Decision**: Single project structure selected for a research CLI. The `src/` hierarchy separates concerns (models, services, CLI) to ensure the analysis pipeline is modular and testable. `data/` is strictly for inputs and derivations, adhering to Data Hygiene.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |