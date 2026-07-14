# Implementation Plan: llmXive follow-up: extending "SWE-Explore: Benchmarking How Coding Agents Explore Repositories"

**Branch**: `001-iterative-exploration-benchmark` | **Date**: 2026-07-14 | **Spec**: `specs/001-iterative-exploration-benchmark/spec.md`
**Input**: Feature specification from `specs/001-iterative-exploration-benchmark/spec.md`

## Summary

This project extends the SWE-Explore benchmark by evaluating an iterative, feedback-driven exploration strategy against a **Static Multi-Query Baseline** (3 parallel queries) to isolate the "feedback" mechanism from mere "search volume". The primary requirement is to demonstrate whether dynamic adaptation yields higher line-level coverage and ranking efficiency on "hard" (high complexity) and synthetically ambiguous issues. The technical approach involves downloading the SWE-Explore dataset, curating a "hard" subset based on **code complexity metrics** (not static baseline failure), generating synthetic ambiguous variants, implementing a 3-turn CPU-tractable iterative agent loop, and performing survival analysis or modified non-parametric tests for censored data.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `scikit-learn`, `pandas`, `pylint`, `ast` (stdlib), `networkx`, `transformers` (CPU-only), `torch` (CPU-only), `pytest`, `lifelines` (for survival analysis), `llama-cpp-python` (for CPU-quantized inference)  
**Storage**: Local file system (`data/` for raw/curated datasets, `artifacts/` for logs/results). No external DB.  
**Testing**: `pytest` (unit tests for mutation logic, integration tests for agent loop, **contract tests** for schema validation).  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM, no GPU).  
**Project Type**: Research/Computational Benchmarking Tool.  
**Performance Goals**: Complete full analysis within 6 hours on free-tier runner.  
**Constraints**: No GPU usage; models must run in default precision on CPU or -bit quantization (if CPU-compatible); memory usage < 6GB; no causal claims (associational only).  
**Scale/Scope**: A substantial set of issues will be compiled, comprising "hard," "easy," and synthetic samples. Max a small number of turns per issue.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | All random seeds pinned in `code/`. External datasets fetched from canonical HuggingFace URLs. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **Compliant** | Citations in `research.md` limited to verified dataset URLs provided in the spec. No invented URLs. |
| **III. Data Hygiene** | **Compliant** | Raw data downloaded to `data/raw/` with checksums. Curated subsets (`data/curated/`) derived via scripts, never modified in place. |
| **IV. Single Source of Truth** | **Compliant** | Final metrics in `paper/` will be generated programmatically from `data/results.csv` and `code/analysis.py`. No hand-typed numbers. |
| **V. Versioning Discipline** | **Compliant** | **Automated Hashing**: `code/utils/hash_artifacts.py` will compute SHA256 hashes for all artifacts in `data/` and update `state/` automatically after each phase. |
| **VI. Iterative Feedback Validation** | **Compliant** | Agent loop will log `query_history`, `static_analysis_signals`, and `turn_reasons` for every issue to verify the feedback loop mechanism. |
| **VII. Hard-Tail Dataset Integrity** | **Compliant** | "Hard" subset (high complexity) and A set of synthetic issues will be saved as immutable JSONL/Parquet files in `data/` with version hashes. |

## Project Structure

### Documentation (this feature)

```text
specs/001-iterative-exploration-benchmark/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output (Sibling to code/)
    ├── dataset_schema.yaml
    ├── agent_log_schema.yaml
    └── result_schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-897-llmxive-follow-up-extending-swe-explore/
├── code/
│   ├── __init__.py
│   ├── config.py                 # Configs, seeds, paths
│   ├── data/
│   │   ├── download.py           # Download SWE-Explore
│   │   ├── derive_gt.py          # Derive ground_truth_lines from patches
│   │   ├── curate.py             # Filter "hard" (complexity) + generate synthetic
│   │   ├── validate_hard.py      # Manual validation report generator
│   │   └── utils.py              # Checksums, validation
│   ├── agent/
│   │   ├── base.py               # Static Multi-Query Baseline
│   │   ├── iterative.py          # 3-turn feedback agent
│   │   ├── static_analysis.py    # Pylint/Ast wrapper
│   │   └── prompts.py            # Prompt templates
│   ├── metrics/
│   │   ├── coverage.py           # Line-level coverage calc
│   │   └── ranking.py            # Ranking efficiency calc (with censored handling)
│   ├── analysis/
│   │   ├── stats.py              # Survival analysis, Wilcoxon, Bonferroni
│   │   └── plots.py              # Visualization
│   ├── utils/
│   │   └── hash_artifacts.py     # Automated hashing for Constitution Principle V
│   └── main.py                   # Orchestration script
├── data/
│   ├── raw/                      # Downloaded raw datasets
│   ├── curated/                  # Hard subset + synthetic issues
│   └── results/                  # Agent logs, metrics, stats
├── contracts/                    # Schemas for contract testing
│   ├── dataset_schema.yaml
│   ├── agent_log_schema.yaml
│   └── result_schema.yaml
├── tests/
│   ├── unit/
│   │   ├── test_mutation.py
│   │   └── test_static_analysis.py
│   ├── integration/
│   │   └── test_agent_loop.py
│   └── contract/
│       └── test_schemas.py       # Validates outputs against contracts/
├── docs/
└── requirements.txt
```

**Structure Decision**: Single project structure (`code/`) is selected to minimize overhead and facilitate the 6-hour runtime constraint. The separation into `data/`, `agent/`, `metrics/`, and `analysis/` ensures modularity for testing and reproducibility while keeping the import graph shallow for CPU execution. `contracts/` is a root-level sibling to ensure `test_schemas.py` can import them easily.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Static Multi-Query Baseline** | Required to isolate "feedback" from "search volume" (Methodology Concern). | A simple one-shot static baseline is tautological when testing on "hard" instances defined by its own failure. |
| **Survival Analysis** | Required for censored "Ranking Efficiency" data (Scientific Soundness Concern). | Standard Wilcoxon assumes symmetry and fails when many values are censored (no relevant lines found). |
| **Iterative Agent Loop** | Required by FR-003/US-2 to test the hypothesis. | A static baseline alone cannot answer the research question about feedback-driven adaptation. |
| **Synthetic Ambiguity Generation** | Required by FR-002/US-1 to create controlled "hard" cases where static retrieval fails. | Relying solely on the natural "hard" tail might not provide enough signal or controlled variance for robust statistical testing. |
| **CPU-Only Constraint** | Required by SC-005 (compute feasibility). | GPU-based models or 8-bit quantization are not available on the free-tier runner and would cause job failure. |

## Phases

### Phase 0: Data Curation & Validation (FR-001, FR-002, FR-008, FR-009, FR-010)

1.  **Download**: Fetch `bench.final.public.jsonl` from the verified HuggingFace URL.
2.  **Ground Truth Derivation**: Run `code/data/derive_gt.py` to parse solution patches and generate `ground_truth_lines` (list of integers) for each issue.
3.  **"Hard" Instance Selection**:
    - **Proxy**: Calculate **Cyclomatic Complexity** or **Lines of Code** for each issue's code context.
    - **Selection**: Select the most complex subset as "Hard". **Do NOT use `initial_coverage`** to avoid tautology.
    - **Validation (FR-010)**: Run `code/data/validate_hard.py` to generate a report for a random subset of "hard" issues for **manual human inspection**. The report is saved to `data/curated/validation_report.md`.
4.  **"Easy" Control Group**: Select a random subset of issues with low complexity for control.
5.  **Synthetic Ambiguity Generation**:
    - Select a representative sample of solvable issues from the non-hard set.
    - Apply mutations (variable renaming, comment removal, structural obfuscation).
    - **Oracle Derivation (FR-008)**: Store the `ground_truth_lines` from the original unmutated code.
    - **Validity Check**: Ensure mutated code is syntactically valid (AST parseable). Skip invalid mutations.
6.  **Hashing**: Run `code/utils/hash_artifacts.py` to hash all curated datasets and update `state/`.

### Phase 1: Agent Execution (FR-003, FR-004, SC-006)

1.  **Static Multi-Query Baseline**:
    - Run **multiple parallel** retrieval queries per issue (matching the iterative agent's total search budget).
    - Record retrieved context and coverage metrics.
2.  **Iterative Agent**:
    - **Loop Limit**: Max 3 turns (FR-003).
    - **Turn Logic**:
        - Turn 1: Query -> Retrieve -> Static Analysis (Pylint/Ast).
        - Turn 2: If error detected, reformulate query with error message -> Retrieve -> Static Analysis.
        - Turn 3: Repeat if necessary.
    - **Static Analysis (FR-004)**: Use `pylint` or `ast` to detect "missing import", "undefined variable", or parse errors.
    - **Logging (Constitution VI)**: Log `query_history`, `error_signals`, and `reformulation_reason` for every turn.
    - **Early Termination**: Stop if solution found or if query repeats (loop detection).
3.  **Turn Limit Sweep (SC-006)**:
    - Run a subset of issues (N=20) with **4 turns** to verify result stability.
4.  **Hashing**: Run `code/utils/hash_artifacts.py` to hash all agent logs.

### Phase 2: Metric Calculation & Statistical Testing (FR-005, FR-006, FR-007)

1.  **Metrics**:
    - **Line-Level Coverage**: % of `ground_truth_lines` retrieved.
    - **Ranking Efficiency**: Position of first retrieved relevant line. **Censored Handling**: If no lines found, assign `N+1` (where N is total lines) or a penalty score.
2.  **Statistical Test**:
    - **Coverage**: Wilcoxon signed-rank test (paired) on the full random sample (not just "hard").
    - **Efficiency**: **Survival Analysis** (Cox proportional hazards) or modified Wilcoxon for censored data to handle the "no relevant lines" cases.
    - **Multiplicity Correction (SC-004)**: Apply Bonferroni correction for the family of tests.
    - **Threshold**: p < 0.05 (adjusted).
3.  **Framing (FR-007)**: Results framed as "associational differences in performance".
4.  **Hashing**: Run `code/utils/hash_artifacts.py` to hash final results.

### Contract Testing

- **Scope**: `tests/contract/test_schemas.py` will validate that all JSON outputs in `data/results/` match the schemas in `contracts/`.
- **Execution**: Run `pytest tests/contract/ -v` as part of the CI pipeline.

## Compute Feasibility & Constraints

- **Environment**: GitHub Actions free-tier (2 CPU, 7GB RAM, no GPU).
- **Model Strategy**:
    - Use a **<1B parameter model** (e.g., `Qwen-Instruct

The specific value to remove/generalize: a specific model scale identifier

Rewritten passage:
The study investigates whether instruction-tuned large language models can effectively perform domain-specific reasoning tasks (Research Question). We will employ a controlled experimental design comparing model performance across varying architectural scales (Method).`) in **float32** to ensure the OS, tools, and context window fit within 7GB RAM.
    - **Alternative**: `Qwen-2.5-1.5B` in **4-bit quantization** using `llama-cpp-python` (CPU-optimized) if memory pressure is high.
    - **No GPU/CUDA**: Explicitly avoid `device_map="auto"` or `load_in_8bit` which require CUDA.
- **Time Limit**:
    - Target: < 6 hours.
    - Mitigation: Limit total issues to a manageable scale. If runtime exceeds a practical threshold, reduce sample size to a manageable level.
- **Memory**:
    - Pin `torch` CPU version.
    - Clear GPU cache (N/A) and Python garbage collect after each issue.