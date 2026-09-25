# Implementation Plan: Context Fidelity vs. Model Scaling Trade-offs

**Branch**: `001-context-fidelity-scaling-tradeoff` | **Date**: 2026-08-06 | **Spec**: `specs/001-context-fidelity-scaling-tradeoff/spec.md`
**Input**: Feature specification from `/specs/001-context-fidelity-scaling-tradeoff/spec.md`

## Summary

This feature implements a comparative experiment to isolate the impact of context compression fidelity against model parameter scaling on software engineering task resolution. The system filters the **Claw-SWE-Bench** dataset (primary) for high-complexity instances (>500 lines of relevant file history, determined via **Hybrid IR-Seeding** using a frozen generic code embedding model), executes them using quantized Q4_K_M models of varying parameter scales under four context strategies (Baseline Truncation, TF-IDF/BM25, Heuristic Keyword-Proxy, Rule-Based Summarization), and analyzes the results via a Generalized Linear Model (GLM) with Firth penalization (or fallback) to detect interaction effects. 

**Critical Design Note**: The study targets a **minimum sample size of 800 instances** (N=100 per cell) to achieve >0.80 power for the confirmatory test of the interaction effect (H3). If the filtered dataset yields N < 800, the study is explicitly **Exploratory** regarding interaction effects. The primary metric is the **Effect Size** (Odds Ratio with 95% CI) of the interaction term, not just statistical significance. A null result (p > 0.05) in an underpowered study will be interpreted as "insufficient evidence to detect an effect" rather than "no effect".

The implementation strictly adheres to CPU-only constraints (limited RAM) via quantization and streaming., and enforces a 60-minute runtime budget per instance and a **≤72 hours total** wall-clock duration.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (Hugging Face), `transformers` (CPU-only, quantized), `sentence-transformers` (CodeBERT-base, frozen), `scikit-learn`, `statsmodels>=0.14.0` (for GLM, with `firth-logistic` or `rpy2` fallback), `pandas`, `pyyaml`, `pytest`  
**Storage**: Local filesystem (`data/`, `data/intermediate/`, `state/`); Parquet for datasets, JSONL for execution logs, CSV for aggregated results.  
**Testing**: `pytest` with contract tests against YAML schemas and integration tests for execution pipelines.  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM, ~14GB Disk).  
**Project Type**: Computational Research / Benchmarking Pipeline.  
**Performance Goals**: Process 800+ instances in ≤72 hours total wall-clock; ≤60 minutes per instance; Pass@1 measurement accuracy.  
**Constraints**: 
- No local GPU; models must run via CPU-quantized GGUF or `load_in_8bit` fallback.
- The model must fit in available RAM (requires low-precision quantization).
- Strict adherence to "Verified datasets" URLs; no gated data access.
- Runtime budget: 60 min/instance, **≤72 hours total**.
- **Quantization Calibration**: Mandatory Phase 0 step to verify Q4_K_M performance vs. FP16.

### Static Analysis Filtering Algorithm (FR-001)
To determine "relevant file history" (>500 lines) without ground-truth patches:
1. **Keyword Extraction**: Parse `issue_description` (or `problem_statement`) via regex to extract file paths (e.g., `.*\.[py|js|ts]`).
2. **Hybrid IR-Seeding**: If no paths are found, use a **frozen generic CodeBERT-base** model to embed the issue description and retrieve the **top-5 files** from the repo based on code similarity. This model is independent of the experimental strategies (TF-IDF, BM25).
3. **Graph Traversal**: For each identified file, load the file and count lines. Traverse the import graph (if available) to include direct dependencies, summing their line counts.
4. **Threshold**: Retain only instances where the sum of relevant file lines > 500.
5. **Fallback**: If no instances meet the threshold, log an error and halt.
6. **Independence Check**: Verify that the correlation between the generic retriever's scores and the experimental strategies is low (<0.3) to ensure the complexity metric is not a function of the strategy.

### Context Strategy Definitions (FR-003)
- **Baseline**: First-N-lines truncation. **N is defined as the first a substantial number of tokens or a substantial number of lines of the relevant files, whichever is reached first..** This ensures a consistent, large context window for the baseline.
- **TF-IDF/BM25**: Relevance-ranked snippets.
- **Heuristic Keyword-Proxy** (formerly Diff-Aware): Identify lines in "relevant files" containing keywords ('fix', 'bug', 'error', 'TODO') and include a contextual window around them. **Note**: This is a construct validity limitation; the plan acknowledges this is a lower-bound proxy for "diff-aware" retrieval.
- **Rule-Based Summarization**: Extract the **first sentence of every paragraph** and the **last sentence of every function block** (defined by indentation or `def`/`function` keywords), concatenate with `...` separator, and truncate to context window.

### GLM Implementation (FR-006)
- **Model Formula**: `Pass ~ Model_Size + Context_Strategy + Model_Size:Context_Strategy + Task_Difficulty + Quantization_Penalty`
- **Interaction Term**: `Model_Size:Context_Strategy` is the primary test for FR-006.
- **Firth Penalization**: Use `statsmodels` if available. If not, fallback to `firth-logistic` (Python) or `logistf` via `rpy2`. If neither is available, proceed with standard GLM and report "Separation Risk".
- **Total Duration**: The system enforces a **≤72 hours total** wall-clock limit. If exceeded, remaining instances are marked as "Timeout".
- **Quantization Penalty**: If the calibration run shows a >5% performance drop, `Quantization_Penalty` (0/1) is added as a covariate.

### Power Analysis & Sample Size Justification (FR-006, SC-003)
- **Target Sample Size**: 800 instances (N=100 per cell for 2x4 design).
- **Power Calculation**: For N=800, power to detect a medium interaction effect (Cohen's h=0.3) is ~0.80. For N=400, power is ~0.35.
- **Decision Gate**: If the filtered dataset yields N < 800, the study is **Exploratory**. The primary claim shifts to the magnitude of the Odds Ratio (OR) with 95% CI. If N >= 800, a confirmatory test is attempted.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Logic |
|-----------|--------|--------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/config.py`. Dataset fetched via `datasets.load_dataset` with `trust_remote_code=True` from verified HF URLs. |
| **II. Verified Accuracy** | PASS | All citations in `research.md` mapped to verified dataset URLs. **Reference-Validator Agent** is invoked via GitHub Actions workflow `ci/validate-citations.yml` on every PR. The workflow executes `scripts/validate_citations.py` which checks `title-token-overlap >= 0.7` against the primary source URLs. |
| **III. Data Hygiene** | PASS | `loader.py` implements SHA256 checksumming of **Raw Parquet, Filtered Parquet, Intermediate JSONL logs, and Final Aggregated CSV**. **No data may be modified in place; every transformation MUST produce a new file with a documented derivation.** State recorded in `state/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben.yaml`. |
| **IV. Single Source of Truth** | PASS | `data/results.csv` is the sole aggregation point. All figures in paper trace to this file. |
| **V. Versioning Discipline** | PASS | **After any data transformation or result generation, the `state/...yaml` file is updated with the new artifact hash and timestamp** by the `utils/checksum.py` module. Content hashes generated for all artifacts in `data/` and recorded in state YAML. |
| **VI. Context-Fidelity vs. Scaling** | PASS | Experimental design explicitly isolates `context_strategy` (4 levels) vs `model_size` (2 levels) in GLM interaction term. |
| **VII. Resource-Constrained Execution** | PASS | Plan mandates `Q_K_M` quantization for 7B model and streaming data loading to fit 7GB RAM. **Total experiment duration ≤72 hours**. |

## Project Structure

### Documentation (this feature)

```text
specs/001-context-fidelity-scaling-tradeoff/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── execution_result.schema.yaml
│   └── aggregated_result.schema.yaml
└── tasks.md             # Phase 2 output (generated by /speckit-tasks)
```

### Source Code (repository root)

```text
projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/
├── __init__.py
├── config.py                 # Global constants, seeds, budgets (60m/72h)
├── loader.py                 # Data fetching, static analysis filtering (>500 lines), checksumming
├── strategies/
│   ├── __init__.py
│   ├── base.py               # Abstract ContextStrategy
│   ├── baseline.py           # First-N-lines truncation
│   ├── tfidf.py              # TF-IDF/BM25 retrieval
│   ├── diff_aware.py         # Heuristic Keyword-Proxy (formerly Diff-Aware)
│   └── summarization.py      # Rule-based semantic summarization (1st/last sentence)
├── models/
│   ├── __init__.py
│   ├── runner.py             # Model loading (1B/7B), quantization (Q4_K_M), inference loop
│   └── quantization.py       # Logic for loading GGUF/quantized weights within 7GB RAM
├── experiments/
│   ├── __init__.py
│   ├── run_baseline.py       # Executes US-1
│   ├── run_strategies.py     # Executes US-2 (TF-IDF, Diff, Summ)
│   └── run_scaling.py        # Executes US-3 (7B model runs)
├── analysis/
│   ├── __init__.py
│   ├── failure_classifier.py # Rule-based failure mode (FR-008)
│   ├── glm_analyzer.py       # GLM with Firth correction (FR-006)
│   └── metrics.py            # Pass@1, Token Count aggregation
├── utils/
│   ├── __init__.py
│   ├── checksum.py           # SHA256 generation and state update
│   └── logging.py            # Structured logging for audit trails
└── tests/
    ├── __init__.py
    ├── contract/             # Schema validation tests
    ├── integration/          # End-to-end execution tests (mocked models)
    └── unit/                 # Strategy logic tests

data/
├── raw/                      # Downloaded Parquet (checksummed)
├── filtered/                 # Filtered Parquet (>500 lines)
├── intermediate/             # JSONL logs per run (checksummed)
└── results.csv               # Final aggregated results (checksummed)

state/
└── projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben.yaml
```

**Structure Decision**: Single-project structure selected to minimize I/O overhead and ensure tight coupling between data loading, execution, and analysis. `strategies/` are decoupled modules to allow independent testing of context fidelity logic. `models/` encapsulates quantization logic to handle the 7B RAM constraint explicitly.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Firth Penalized GLM** | Required by FR-006 and Constitution Principle VI to handle sparse binary data (Pass/Fail) in small cells (n<50) where standard GLM fails to converge. | Standard `statsmodels` GLM often fails to converge with separation in binary outcomes; Firth correction is the only robust method for this sample size. |
| **Q4_K_M Quantization** | Required by FR-007 and Constitution Principle VII to fit 7B model in 7GB RAM. | Full multi-bit models exceed available RAM capacity.; High-bit quantization still risks OOM on 7GB limit; Q4_K_M is the minimal viable precision for reasoning tasks. |
| **Hybrid IR-Seeding** | Required by FR-001 to ensure "context-bound complexity" (>500 lines) without using ground-truth patches and to avoid circularity with test strategies. | Keyword-only extraction fails on natural language issues; pure random filtering does not guarantee "relevant file history" complexity. |
| **Streaming Data Loading** | Required by Constitution Principle III and compute constraints to avoid loading full dataset into RAM. | Loading full SWE-bench into RAM would crash the runner; streaming allows processing on-disk. |
| **Exploratory Design** | Required by Methodology Panel due to low power (N=400) for interaction detection. | A confirmatory design with N=400 would yield high Type II error rates; the study must report effect sizes (OR) with 95% CI as the primary metric. |
| **Total Duration Constraint** | Required by FR-007 (≤72 hours total). | Without a global timeout, the experiment could run indefinitely on slow instances. |
| **Static Analysis Filtering** | Required by FR-001. Implemented in `loader.py` via Hybrid IR-Seeding (top-5 files via generic embeddings) and graph traversal. | |
| **Rule-Based Summarization** | Required by FR-003. Explicitly defined as "first sentence of paragraph, last sentence of function" in `strategies/summarization.py`. | |
| **GLM Interaction Term** | Required by FR-006. Formula explicitly includes `Model_Size:Context_Strategy`. | |
| **Quantization Calibration** | Required by Methodology Panel. Mandatory Phase 0 step to verify Q4_K_M performance. | |
| **Representativeness Validation** | Required by Methodology Panel. KS-test comparison of filtered vs. full dataset. | |
| **Construct Validity Audit** | Required by Methodology Panel. Acknowledges Heuristic Keyword-Proxy limitations. | |