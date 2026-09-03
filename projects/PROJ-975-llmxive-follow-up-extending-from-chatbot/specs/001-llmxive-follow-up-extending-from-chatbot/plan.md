# Implementation Plan: llmXive follow-up: extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

**Branch**: `001-gene-regulation` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-follow-up-extending-from-chatbot/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-from-chatbot/spec.md`

## Summary

This project implements a deterministic synthetic simulation to test the "Digital Colleague" hypothesis: specifically, identifying the "tipping point" where library size and semantic redundancy degrade agent task success, and evaluating a "Skill Pruning" heuristic to mitigate this. The approach involves generating a synthetic dataset of multi-step tasks and a configurable library of Python skills, executing an agent across **multiple library sizes** spanning a defined range to provide sufficient data points for breakpoint estimation, and performing statistical analysis (Piecewise Linear Regression) to locate the performance inflection point.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `sentence-transformers` (CPU-only), `pandas`, `numpy`, `pytest`, `pyyaml`, `jsonschema`  
**Storage**: Local JSON/CSV files (`data/raw`, `data/results`)  
**Testing**: `pytest` (unit, integration, contract), `jsonschema` for contract validation  
**Target Platform**: GitHub Actions Free Tier (Linux, CPU, 7GB RAM)  
**Project Type**: Research Simulation / CLI Tool  
**Performance Goals**: Complete full experiment (500 tasks x 10 configurations) within 6 hours; Memory < 7GB during embedding calculation.  
**Constraints**: No GPU access for training; must use CPU-tractable embeddings (e.g., `all-MiniLM-L6-v2`); synthetic data must be deterministic (fixed seeds).  
**Scale/Scope**: A substantial set of tasks, A maximum number of skills will be established., library configurations.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/generate_data.py` and `code/agent.py`. `requirements.txt` pins exact versions. CI runs full suite on fresh runner. |
| **II. Verified Accuracy** | **PASS** | Citations for Piecewise Regression and `sentence-transformers` in `research.md` will be validated against primary sources. Code logic is self-contained but relies on validated external methods. |
| **III. Data Hygiene** | **PASS** | `data/raw` contains immutable generated JSON. `data/results` contains derived CSV/JSON. Checksums recorded in state file. No PII (synthetic code). |
| **IV. Single Source of Truth** | **PASS** | `data/results/experiment_log.csv` is the sole source for all metrics. `code/analyze.py` reads only from this file. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked for `data/` and `code/`. State file updated on artifact change. |
| **VI. Synthetic Environment Validity** | **PASS** | Data generation logic explicitly separates "ground truth" paths from "retrieval" logic. Overlap metrics calculated programmatically. |
| **VII. Pruning Intervention Fidelity** | **PASS** | Pruning logic (periodically)

The research question, method, and references remain unchanged as no specific empirical values were asserted in this context beyond the interval frequency. is isolated in `code/pruning.py`. Baseline runs (pruning disabled) are executed in parallel for comparison. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/
    ├── task.schema.yaml
    ├── skill.schema.yaml
    ├── experiment_log.schema.yaml
    ├── execution_log.schema.yaml
    └── metrics.schema.yaml
```

### Source Code (repository root)

```text
data/
├── raw/
│   ├── tasks.json
│   └── skills.json
└── results/
    ├── experiment_log.csv
    ├── experiment_log_baseline.csv
    ├── tipping_point.json
    └── pruning_analysis.json

code/
├── generate_data.py      # FR-001, FR-002 (includes overlap detection & tie-breaking)
├── agent.py              # FR-003, Edge Cases (includes missing skill logging)
├── pruning.py            # FR-004
├── analyze.py            # FR-005, FR-006, FR-007 (writes tipping_point.json)
├── run_baseline.py       # US-2 execution loop (generates experiment_log_baseline.csv)
└── utils.py              # Embedding helpers, seed pinning

tests/
├── unit/
│   ├── test_generate_data.py
│   ├── test_agent.py
│   └── test_pruning.py
├── integration/
│   └── test_full_pipeline.py
└── contract/
    └── test_schemas.py   # Uses jsonschema for validation

requirements.txt
pre-commit-config.yaml
```

**Structure Decision**: Single-project structure selected. `data/` is split into `raw` (immutable generation) and `results` (derived metrics). `code/` contains modular scripts for generation, execution, and analysis to ensure separation of concerns and reproducibility.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Piecewise Linear Regression** | Required by FR-005 to identify the non-linear "tipping point" where performance degrades. | Simple linear regression fails to capture the threshold effect; logistic regression is for binary outcomes, but we need to model the continuous decline in success rate against library size. |
| **Synthetic Data Generation** | Required to control semantic overlap (FR-002) and ground truth (FR-001) precisely, which is impossible with public datasets. | Public datasets (e.g., HumanEval) lack the specific "semantic overlap" variable and controlled ground-truth paths needed for this specific hypothesis. |

## Methodological Rigor & Feasibility

- **FR/SC Coverage**:
  - **FR-001/002**: Addressed in `generate_data.py` (synthetic generation with overlap control, mean pairwise similarity calculation, `maximal_overlap_detected` flag, and deterministic tie-breaking).
  - **FR-003**: Addressed in `run_baseline.py` (execution loop for **10 library sizes**: 10, 20, 30, ..., 100).
  - **FR-004**: Addressed in `pruning.py` (heuristic logic triggered periodically at regular task intervals).
  - **FR-005**: Addressed in `analyze.py` (Piecewise Linear Regression implementation, writes `x0` to `tipping_point.json`).
  - **FR-006**: Addressed in `analyze.py` (Jaccard and Inverse Variance metrics).
  - **FR-007**: Addressed in `analyze.py` (VIF calculation for 'Library Size' vs 'Mean Pairwise Similarity').
  - **SC-001 to SC-006**: All mapped to specific output files and statistical checks in `analyze.py`.

- **Statistical Rigor**:
  - **Multiple Comparisons**: Not applicable as this is a single experiment with pre-registered conditions (library sizes).
  - **Power**: Sample size is fixed by spec. With multiple groups (tasks/group), the study is powered to detect large effect sizes (Cohen's h > 0.4). Subtle tipping points may be missed; this limitation is explicitly recorded in the final report.
  - **Causal Framing**: Claims limited to "associational within the simulation" due to synthetic nature, as per Assumptions.
  - **Collinearity**: VIF (FR-007) explicitly calculated for 'Library Size' and 'Mean Pairwise Similarity'. **Success Criterion**: If VIF >= 5.0, the model is invalid for causal interpretation of independent effects, and the hypothesis is rejected for that configuration.

- **Compute Feasibility**:
  - **CPU-First**: `sentence-transformers` (all-MiniLM-L6-v2) runs efficiently on CPU. Embeddings for 100 skills x 500 tasks are < 1GB RAM.
  - **No GPU**: No training required; only inference.
  - **Time**: 500 tasks x 10 configs = 5000 runs. Each run is a simple retrieval + execution. Estimated < 3 hours on 2-core CPU.

- **Data Availability**:
  - **Synthetic**: No external download needed. Data generated locally, ensuring CI feasibility.
  - **Streaming**: Not required due to small dataset size.

## Edge Case Handling

- **Maximal Overlap**: If mean pairwise similarity >= 0.95, the system logs `maximal_overlap_detected`, handles retrieval ties deterministically (by skill_id), and reports Retrieval Precision as 0 if no ground-truth skills are retrieved.
- **Missing Skills**: If a task requires a skill not in the library, the agent logs the specific missing skill ID, records the failure, and does not attempt to hallucinate a solution.
- **Memory Pressure**: The system detects memory pressure and samples the dataset or fails with a clear "Memory Limit Exceeded" error.