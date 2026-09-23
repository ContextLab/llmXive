# Implementation Plan: llmXive Follow-up: Semantic Divergence Diagnostic for Agentic Reasoning

**Branch**: `001-llmxive-semantic-gap-diagnostic` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-follow-up-extending-agent-explor/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-agent-explor/spec.md`

## Summary

This feature implements a diagnostic tool to quantify the "Semantic Divergence Score" between an agent's internal "thinking" trace and its external "tool-action" distribution. The system loads a static subset of the MathVista dataset, extracts thinking prefixes (using static stubs if traces are missing), retrieves tool descriptions via BM25 (with lexical overlap masking), computes embeddings using DistilBERT (CPU-only), and calculates cosine similarity. It then correlates these scores with simulated RL failure rates (derived from a deterministic Oracle based on ground truth answers) and trains a Logistic Regression classifier to predict failure. The implementation strictly adheres to CPU constraints (≤7 GB RAM, 2 cores) and enforces data hygiene via checksums and versioning.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `sentence-transformers` (CPU wheels), `rank_bm25`, `scikit-learn`, `pandas`, `pyyaml`, `ruff`, `black`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/cache`) with checksums recorded in `state/projects/PROJ-849-llmxive-follow-up-extending-agent-explor.yaml`  
**Testing**: `pytest` (unit tests for embedding logic, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, ~7 GB RAM)  
**Project Type**: Research CLI / Data Analysis Pipeline  
**Performance Goals**: ≤5 hours total execution; peak memory ≤7 GB; no GPU usage for embedding/retrieval.  
**Constraints**: CPU-only for all ML inference; dataset size capped at 500 records (downsampled to a reduced resolution if memory pressure detected); strict timeout enforcement.  
**Scale/Scope**: Processing ≤500 multimodal reasoning problems; generating one correlation report and one classification model.

## Constitution Check

*Gates determined based on constitution file `projects/PROJ-849-llmxive-follow-up-extending-agent-explor/.specify/memory/constitution.md`*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `src/lib/config.py`. `datasets.load_dataset` uses canonical HF source. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` limited to verified dataset URLs. No hallucinated sources. |
| **III. Data Hygiene** | **PASS** | Raw data checksummed upon download. Derived data (embeddings, scores) written to new files with derivation logs. |
| **IV. Single Source of Truth** | **PASS** | All metrics in `results/` trace back to specific rows in `data/processed/scores.parquet` and `code/` scripts. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked in project state file. Artifacts invalidated on code change. |
| **VI. Semantic Divergence Quantification** | **PASS** | Metric explicitly defined as `1 - cosine_similarity` between DistilBERT thinking embedding and BM25-retrieved tool centroid. **Implementation Detail**: The system uses a **non-reasoning** BM25 retrieval (keyword-based) and **does NOT** substitute the agent's own reasoned tool distributions. The retrieval logic is strictly keyword-based to ensure independence. |
| **VII. Diagnostic Validation Rigor** | **PASS** | Logistic Regression predicts ground-truth AXPO outcomes (derived from a deterministic Oracle based on ground truth answers) using only semantic metrics. No data leakage from embedding to outcome generation. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-agent-explor/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (created by /speckit-tasks)
```

### Source Code (repository root)

```text
projects/PROJ-849-llmxive-follow-up-extending-agent-explor/
├── data/
│   ├── raw/
│   │   └── mathvista_subset.jsonl
│   ├── processed/
│   │   ├── tool_mappings.json
│   │   ├── embeddings_cache.parquet
│   │   └── divergence_scores.parquet
│   └── cache/
│       └── axpo_simulated_outcomes.jsonl
├── src/
│   ├── __init__.py
│   ├── lib/
│   │   ├── config.py          # Paths, seeds, thresholds, error definitions
│   │   ├── data_loader.py     # HF dataset loading, BM25 index building
│   │   ├── embedding_service.py # DistilBERT inference, centroid calculation
│   │   ├── metrics.py         # Divergence calculation, correlation, logistic regression
│   │   ├── errors.py          # TimeoutExceededError, MemoryLimitExceededError
│   │   └── oracle.py          # Ground truth failure generation
│   └── cli/
│       └── run_diagnostic.py  # Main entry point
├── tests/
│   ├── unit/
│   │   └── test_metrics.py
│   └── integration/
│       └── test_pipeline.py
├── pyproject.toml             # Ruff/Black config, dependencies
└── requirements.txt           # Pinned dependencies
```

**Structure Decision**: Single project structure (`src/`) chosen to minimize overhead for a research pipeline. `lib/` isolates core logic, `cli/` handles orchestration. `data/` follows the raw/processed split for hygiene.

## Complexity Tracking

*No violations detected in Constitution Check. Standard research pipeline complexity applies.*

## Phased Execution Plan

### Phase 0: Research & Feasibility (Research Agent)
1.  **Data Verification**: Confirm `AI4Math/MathVista` dataset availability and field presence (`question`, `answer`, `metadata`).
2.  **Tool Mapping Strategy**: Define schema for `mathvista_tool_map.json` (problem_id -> list of tool descriptions). Source: `data/tool_mappings/mathvista_tool_map.json` (static asset).
3.  **Embedding Model Selection**: Verify `distilbert-base-uncased` or `sentence-transformers/all-MiniLM-L6-v2` runs within 7GB RAM on CPU.
4.  **Outcome Simulation**: Define logic for `simulated_failure_rate` using a deterministic Oracle (ground truth answer comparison) to ensure reproducibility and independence from the thinking trace.

### Phase 1: Design & Contracts (Design Agent)
1.  **Data Model Definition**: Define schemas for `ProblemInstance`, `ToolDistribution`, `DivergenceMetric`.
2.  **Contract Generation**: Create `contracts/*.schema.yaml` for input data, intermediate embeddings, and final output. **Explicitly map** `ProblemInstance`, `ToolDistribution`, and `DivergenceMetric` entities to `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`.
3.  **API Design**: Define function signatures for `load_data`, `compute_divergence`, `run_correlation`, `train_classifier`.
4.  **Error Handling**: Define `TimeoutExceededError` and `MemoryLimitExceededError` in `src/lib/errors.py` with clear module paths.

### Phase 2: Implementation (Implementer Agent)
1.  **Environment Setup**: Install dependencies, configure `pyproject.toml` (ruff/black), create directory structure. **Task T003**: Install and configure `ruff` and `black`.
2.  **Config Creation**: **Task T004**: Create `src/lib/config.py` with all necessary paths, seeds, and thresholds.
3.  **Data Loader**: **Task T005**: Implement `src/lib/data_loader.py` to fetch MathVista, extract thinking traces (or static stubs), load tool mappings from `data/tool_mappings/mathvista_tool_map.json`, build BM25 index. **Validate** inputs/outputs against `contracts/dataset.schema.yaml`.
4.  **Embedding Service**: Implement `src/lib/embedding_service.py` for CPU-only DistilBERT inference and centroid calculation. **Validate** outputs against `contracts/dataset.schema.yaml`.
5.  **Oracle Implementation**: **Task T008-impl-cache**: Implement `src/lib/oracle.py` to generate `simulated_failure` labels based on ground truth answers (independent of thinking trace). This task is **sequential** (not parallel) to data loading.
6.  **Metric Engine**: **Task T004-ext**: Implement `src/lib/metrics.py` for divergence scoring (with centroid variance check and lexical overlap masking), Pearson/Point-Biserial correlation, and Logistic Regression training. **Include** check for N >= 30 and raise `InsufficientSampleSize` error if N < 30.
7.  **CLI Orchestration**: Implement `src/cli/run_diagnostic.py` with timeout/memory monitoring. **Enforce** `TimeoutExceededError` and `MemoryLimitExceededError` (imported from `src/lib/errors.py`) as per FR-007.
8.  **Testing**: Write unit tests for metric calculations and integration tests for the full pipeline.

### Phase 3: Validation & Reporting (Validator Agent)
1.  **Reproducibility Check**: Re-run pipeline on fresh runner; verify checksums and output consistency.
2.  **Statistical Rigor**: Verify sample size (N ≥ 30), correlation significance (p < 0.05), and AUC-ROC (≥ 0.65). **Task T014**: Run statistical checks. **Task T015**: Generate final report (sequential to T014).
3.  **Constitution Compliance**: Final audit against Principles I-VII.

## Computational Feasibility & Data Strategy

- **CPU-First**: All embedding and retrieval steps use CPU-optimized models (`sentence-transformers` with `device='cpu'`). No GPU required.
- **Memory Management**: The pipeline processes data in batches. If memory usage approaches a high threshold, the system triggers a graceful downsampling to 300 records. (as per FR-007) and logs the action.
- **Data Source**: Uses `AI4Math/MathVista` (verified URL) for problems. Tool mappings are generated from a curated JSON file (`data/tool_mappings/mathvista_tool_map.json`) which is a static asset in the repo.
- **Outcome Data**: Simulated failure rates are derived from a deterministic Oracle (ground truth answer comparison) to ensure reproducibility and independence from the thinking trace.
- **Timeout Enforcement**: A hard 5-hour limit is enforced via a wrapper in `run_diagnostic.py`. If exceeded, `TimeoutExceededError` is raised.
