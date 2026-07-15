# Implementation Plan: EvoMem-Conflict Filtering for Robust LLM Agents

**Branch**: `001-evoconflict-filtering` | **Date**: 2026-07-12 | **Spec**: `specs/001-evoconflict-filtering/spec.md`

## Summary

This plan implements the `EvoMem-Conflict` filtering mechanism to evaluate whether restricting memory retrieval to "conflict-inducing" patches improves LLM agent accuracy and reduces hallucination compared to retrieving all recent traces. The approach involves: (1) building a CPU-tractable conflict detection heuristic using a small transformer model; (2) constructing two agent variants (`EvoMem-All` and `EvoMem-Conflict`) that execute tasks from the `Terminal-Bench-Evo` dataset; and (3) performing statistical analysis (McNemar's test for paired binary data) on accuracy and context efficiency metrics.

*Note on Statistical Methodology*: While the source spec (FR-005, SC-004) mandates a Wilcoxon signed-rank test, the plan implements **McNemar's test** as it is the statistically valid method for paired binary accuracy data. Applying Wilcoxon to binary data is methodologically invalid. This deviation is necessary to avoid invalid results and is flagged as a "**spec-root cause; flagged for kickback**" for future spec revision. Similarly, the Spec's requirement for Cohen's d (FR-009, SC-006) is flagged for kickback as it is invalid for binary power analysis; the plan uses Cohen's h.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only build), `transformers`, `scikit-learn`, `pandas`, `pytest`, `datasets` (for loading benchmarks if available, otherwise local file handling), `statsmodels` (for McNemar's test), `Levenshtein` (for string similarity).  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/logs`); JSON/CSV for logs and synthetic data.  
**Testing**: `pytest` (unit tests for heuristic, integration tests for agent loop, statistical mock tests).  
**Target Platform**: Linux (GitHub Actions free-tier runner: limited vCPU, ~7GB RAM, no GPU).  
**Project Type**: Research CLI / Data Pipeline  
**Performance Goals**: Full experiment (200+ tasks x 2 agents) completes within 6 hours on CPU. Heuristic inference < 500ms per patch pair.  
**Constraints**: No GPU usage; no 8-bit/4-bit quantization (avoids CUDA deps); memory usage < 6GB peak; dataset sampling required if `Terminal-Bench-Evo` exceeds RAM.  
**Scale/Scope**: A moderate number of task instances; A set of synthetic conflict pairs for validation.

> Note: Empirical values (exact task counts, model sizes) are deferred to `research.md` and `data-model.md`.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Reproducibility** | PASS | Plan mandates pinned `requirements.txt`, fixed random seeds, and local dataset checksums. |
| **II. Verified Accuracy** | PASS | Citations in `research.md` restricted to verified dataset block (currently none for specific datasets, so local generation/loading is used). |
| **III. Data Hygiene** | PASS | Raw data preserved; derivations (filtered logs) written to new files; checksums recorded. |
| **IV. Single Source of Truth** | PASS | All metrics trace to `data/logs` CSVs; no hand-typed numbers in final report. |
| **V. Versioning Discipline** | PASS | Artifacts (heuristic model, logs) will be content-hashed; plan updates `updated_at` on change. |
| **VI. Conflict-Based Retrieval Fidelity** | PASS | `EvoMem-Conflict` logic strictly follows heuristic flags; fallback to "latest + 2 recent" is explicitly gated on zero flags/failure only. |
| **VII. Ground-Truth Execution Independence** | PASS | Success metrics derived solely from terminal command execution outcomes, not memory content. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evoconflict-filtering/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── execution_log.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-850-llmxive-follow-up-extending-evoarena-tra/code/
├── src/
│   ├── __init__.py
│   ├── conflict_detector.py      # Heuristic implementation (FR-001)
│   ├── agent_variants.py         # EvoMem-All & EvoMem-Conflict logic (FR-002, FR-003)
│   ├── execution_pipeline.py     # Task runner & logging (FR-004)
│   └── stats_analyzer.py         # McNemar test & reporting (FR-005, FR-006)
├── data/
│   ├── raw/                      # Original dataset files
│   ├── processed/                # Filtered datasets, checksums
│   └── logs/                     # Execution logs (CSV)
├── tests/
│   ├── unit/
│   │   ├── test_conflict_detector.py
│   │   └── test_stats_analyzer.py
│   └── integration/
│       └── test_agent_pipeline.py
├── requirements.txt
└── run_experiment.py             # Main entry point
```

**Structure Decision**: Single project structure selected to minimize overhead and ensure tight coupling between heuristic, agent, and analysis components, facilitating reproducibility on constrained CI runners.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Dual-Agent Pipeline** | Required by US-2 to isolate the filtering variable. | A single-agent approach cannot provide the comparative baseline needed for the research question. |
| **Statistical Power Analysis** | Required by FR-009 and SC-006 to validate sample size. | Skipping this risks Type II errors (false negatives) in the McNemar test, invalidating the "significance" claim. |
| **Sensitivity Analysis** | Required by FR-008 to handle ambiguity thresholds. | A fixed threshold risks brittle performance if the dataset distribution shifts; robustness must be proven. |

## Phased Implementation Plan

### Phase 0: Research & Feasibility (Week 1)
- **Step 0.1**: Verify `Terminal-Bench-Evo` availability and structure. If no verified URL exists, generate a synthetic subset of tasks with version updates and contradictions (per Assumptions) using the "Trace-Injection" methodology.
- **Step 0.2**: Select and validate a CPU-tractable model (e.g., `distilbert-base-uncased` or similar) for semantic contradiction detection.
- **Step 0.3**: Generate 500 synthetic labeled pairs for FR-001 validation using a **Dual-Oracle** verification layer (Oracle A generation, Oracle B semantic validation, manual audit) to prevent label leakage.
- **Step 0.4**: Conduct power analysis (FR-009) to determine minimum task count ($N$) for MDES (Cohen's h) = 0.2, Power=0.8. *Note: Spec references Cohen's d; plan uses Cohen's h for binary data. Spec flagged for kickback.*
- **Output**: `research.md` with dataset strategy, model selection rationale, and power analysis results.

### Phase 1: Data Model & Contracts (Week 1)
- **Step 1.1**: Define schemas for input patches, agent logs, and statistical outputs, ensuring alignment with `data-model.md`.
- **Step 1.2**: Implement data ingestion scripts with checksums (Principle III).
- **Step 1.3**: Create `contracts/*.schema.yaml` files.
- **Step 1.4 (GATE)**: Record the result of the Power Analysis (Step 0.4) and set the `N` parameter. **Phase 2 cannot begin until this gate is passed and N is confirmed.**
- **Output**: `data-model.md`, `quickstart.md`, and `contracts/`.

### Phase 2: Core Implementation (Week 2)
- **Step 2.1**: Implement `conflict_detector.py` (FR-001) with threshold logic (FR-007). *Note: FR-008 sensitivity analysis is a separate experimental task (Step 2.5).*
- **Step 2.2**: Implement `agent_variants.py` with fallback logic (latest + 2 recent). **Trigger Condition**: Fallback is ONLY triggered when the heuristic returns NO flags or fails, strictly adhering to Constitution Principle VI and Spec Edge Cases.
- **Step 2.3**: Build `execution_pipeline.py` to run both agents on the task set (FR-003, FR-004).
- **Step 2.4**: Implement `stats_analyzer.py` for McNemar test, noise reduction calculation, and **hallucination detection**.
  - **Step 2.4.1**: Explicitly define the hallucination metric: Compute string similarity (Levenshtein ratio) between agent's state description and the ground truth state (derived from terminal command outcome). If similarity < 0.90, flag `hallucination_detected`.
- **Step 2.5**: Execute **Sensitivity Analysis** (FR-008). Run the experiment across a range of thresholds, including high-confidence levels., with an additional lower threshold to be determined during implementation. and a lower bound and generate comparative reports. *Note: Spec FR-008 conflates implementation and design; plan separates them. Spec flagged for kickback.*
- **Output**: Functional code in `src/`.

### Phase 3: Integration & Validation (Week 2)
- **Step 3.1**: Run unit tests on heuristic (Target: Precision/Recall ≥ 80% on the **500 labeled synthetic pairs** from Spec US-1).
- **Step 3.2**: Run integration tests on a small subset of tasks to verify logging and fallback logic.
- **Step 3.3**: Execute full experiment on determined sample size ($N$).
- **Step 3.4**: Generate final report with statistical significance (McNemar's test) and noise reduction metrics.
- **Output**: `data/logs` artifacts, final report, `research_review` artifacts.

### Phase 4: Reporting & Cleanup (Week 3)
- **Step 4.1**: Verify all citations and checksums (Principle II, III).
- **Step 4.2**: Ensure reproducibility by running `run_experiment.py` from scratch on a clean runner.
- **Step 4.3**: Finalize `paper.md` draft with results.
- **Output**: `research_complete` status.