# Implementation Plan: llmXive follow-up: extending "COLLEAGUE.SKILL"

**Branch**: `001-llmxive-skill-separation` | **Date**: 2026-07-16 | **Spec**: `spec.md`
**Input**: Feature specification from `spec.md`

## Summary

This project investigates whether decoupling capability heuristics from behavioral style in LLM prompts reduces hallucination and style drift. The technical approach involves:
1.  **Data Generation**: Creating expert profiles and rule-based task scenarios (with a feasible subset of profiles × tasks for LMM convergence).
2.  **Inference**: Running three prompt conditions (Monolithic, Separated, Generic) on a quantized 8B LLM (e.g., Llama-3-8B-Q4) using a **strict CPU-only backend** (`llama.cpp` or `transformers` with `torch_dtype=float32`). **No GPU offload is permitted** to preserve causal validity.
3.  **Evaluation**: Deterministic, rule-based scoring for Heuristic Adherence, Hallucination Rate (logic chain verification), and Style Consistency (emergent markers).
4.  **Analysis**: Linear Mixed-Effects Models (LMM) with multiple-comparison correction to test statistical significance, plus sensitivity analysis and non-inferiority tests.

The plan strictly adheres to CPU-only constraints (≤7GB RAM, ≤6h runtime). If the model fails to load or run on CPU, the specific run is logged as 'oom' or 'error' and excluded from analysis.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `torch` (CPU build), `llama-cpp-python` (optional fallback), `pandas`, `statsmodels`, `scikit-learn`, `pyyaml`, `jsonlines`, `pytest`, `loguru`.  
**Storage**: Local filesystem (`data/raw`, `data/interim`, `data/processed`).  
**Testing**: `pytest` (unit tests for evaluation logic, integration tests for inference pipeline).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Research CLI / Data Pipeline.  
**Performance Goals**: Inference < 300s per task; Total runtime < 6h; RAM < 7GB.  
**Constraints**: CPU-only inference; No GPU dependencies in default path; Deterministic evaluation (no LLM judges).  
**Scale/Scope**: Target a large-scale set of runs (50 profiles × 200 tasks × 3 conditions), but feasible execution is a balanced subset (10 profiles × 50 tasks × 3 conditions) to ensure LMM convergence.

> Note: The full 30k matrix is the theoretical target, but the **feasible run** is defined as a statistically powered balanced subset (10 profiles, 50 tasks) to ensure sufficient data per random-effect level for LMM convergence.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Evidence/Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | All random seeds pinned in `code/`. Data fetched via deterministic scripts. |
| **II. Verified Accuracy** | **Pass** | Citations in `research.md` will be validated against primary sources. |
| **III. Data Hygiene** | **Pass** | `data/raw` checksummed; `data/interim` derived; no in-place modification. |
| **IV. Single Source of Truth** | **Pass** | All metrics in `data/processed` trace to specific code blocks in `code/`. |
| **V. Versioning Discipline** | **Pass** | Artifacts hashed; `updated_at` timestamps managed by agent workflow. |
| **VI. Deterministic Evaluation** | **Pass** | Evaluation uses regex/logic rules (FR-004, FR-005), not LLM judges. Ambiguous contexts handled via `exclusion_flag`. |
| **VII. Resource-Constrained** | **Pass** | Plan mandates quantized 8B model on CPU; **No GPU offload** (exclusion of failed runs instead). |

## Project Structure

```text
projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/
├── code/
│   ├── __init__.py
│   ├── config.py            # Paths, seeds, model params
│   ├── data/
│   │   ├── generators/
│   │   │   ├── profile_generator.py  # Creates 50 expert profiles
│   │   │   └── task_generator.py     # Creates 200 rule-based tasks
│   │   └── loaders/
│   │       └── dataset_loader.py     # Loads profiles/tasks from data/raw
│   ├── inference/
│   │   ├── engine.py        # CPU inference wrapper (transformers/llama-cpp)
│   │   ├── prompts.py       # Monolithic, Separated, Generic prompt builders
│   │   └── run_inference.py # Main script: loops profiles/tasks/conditions
│   ├── evaluation/
│   │   ├── rules.py         # Regex/logic rules for Adherence, Hallucination, Style
│   │   └── score.py         # Deterministic scoring engine
│   ├── analysis/
│   │   ├── stats.py         # LMM, Bonferroni correction, sensitivity analysis
│   │   └── plot.py          # Visualization scripts
│   ├── tests/
│   │   ├── unit/            # Test rules.py, prompt builders
│   │   └── integration/     # Test end-to-end small run
│   └── requirements.txt
├── data/
│   ├── raw/                 # Downloaded/Generated raw data (profiles, tasks)
│   ├── interim/             # Inference outputs (JSONL)
│   └── processed/           # Aggregated metrics, statistical results
├── state/
│   └── projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/
│       └── artifact_hashes.yaml
└── specs/
    └── 001-llmxive-follow-up-extending-colleague-sk/
        ├── plan.md          # This file
        ├── research.md      # Phase 0 output
        ├── data-model.md    # Phase 1 output
        ├── quickstart.md    # Phase 1 output
        └── contracts/
            ├── profile.schema.yaml
            ├── task.schema.yaml
            ├── inference_output.schema.yaml
            └── evaluation_result.schema.yaml
```

**Structure Decision**: Selected a modular CLI structure (`code/`) to separate data generation, inference, evaluation, and analysis. This ensures the "Deterministic Evaluation" principle is enforced by isolating `evaluation/rules.py` from the inference engine.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Balanced Subset ([deferred] runs)** | Full 30k is infeasible for LMM convergence; a substantial number of runs (10 profiles × 50 tasks) ensures sufficient data per random-effect level. | A smaller sample (e.g., 500) would be too sparse for LMM; a full 30k run exceeds 6h. |
| **CPU-Only Constraint** | Spec requires CPU-only for "deployable on standard hardware". | GPU offload introduces a confound (capacity vs. prompt architecture) and invalidates the hypothesis. |

## Implementation Phases

### Phase 0: Research & Data Strategy
*   **Goal**: Verify dataset availability and model feasibility.
*   **Actions**:
    *   Confirm availability of "expert profiles" (simulated if gallery unavailable).
    *   Verify `Llama-3-8B-Q4` or `Phi-3-mini` loads on 7GB RAM CPU.
    *   Define ground-truth logic for Hallucination/Adherence (rule-bound logic chains).
*   **Deliverable**: `research.md`

### Phase 1: Data Model & Contracts
*   **Goal**: Define schemas for profiles, tasks, and outputs.
*   **Actions**:
    *   Create YAML schemas for `ExpertProfile`, `TaskScenario`, `InferenceOutput`.
    *   Define evaluation metric contracts.
*   **Deliverable**: `data-model.md`, `contracts/*.schema.yaml`

### Phase 2: Implementation & Execution
*   **Goal**: Run the pipeline.
*   **Actions**:
    *   **T006 (Generate Profiles)**: Create 50 valid profiles. *Handle malformed data by logging and skipping.*
    *   **T007 (Generate Tasks)**: Create 200 tasks. *Enforce stratified sampling across multiple domains (coding, math, logic, creative, factual) with proportional distribution. Handle ambiguous contexts by setting `exclusion_flag=True` in `TaskScenario`.*
    *   **T014a (Inference)**: Run 3 conditions on the balanced subset (10 profiles × 50 tasks). *Enforce a fixed timeout per task. If timeout occurs, log `status: 'timeout'` in `InferenceOutput`. If OOM, log `status: 'oom'`. Use Python `logging` module to record start, progress, completion, and failures.*
    *   **T019 (Evaluation)**: Apply deterministic rules. *Calculate Heuristic Adherence by evaluating output against held-out validation rules derived from capability_track. Calculate Hallucination Rate using multi-hop logic checks (boolean chain verification) and rule-based entity extraction.*
    *   **T025 (Analysis)**: Run LMM with Bonferroni or Holm-Bonferroni correction.
    *   **T026 (Sensitivity Analysis)**: Sweep Style Consistency thresholds (low, medium, high) and record variance.
    *   **T027 (Non-Inferiority Test)**: Calculate absolute difference in Style Consistency between conditions and check against predefined margin.
*   **Deliverable**: `data/processed/results.csv`, `paper/` draft, `data/interim/inference_outputs.jsonl`.

## Unresolved Panel Concerns (Addressed)

1.  **T007 Data Robustness**: The plan explicitly includes logic in `data/generators/task_generator.py` to validate context clarity. If a task scenario is ambiguous, it is flagged (`exclusion_flag=True`) and excluded from the Hallucination calculation, satisfying the edge case requirement.
2.  **T014a Timeout Enforcement**: The `inference/engine.py` will implement a hard 300-second timeout per task (using `signal` or `threading` with timeout). Tasks exceeding this are logged as `status: 'timeout'` in `InferenceOutput`, ensuring the consumer (evaluation) receives valid metadata.
3. **LMM Convergence**: The plan now targets a balanced subset of [deferred] runs (10 profiles × 50 tasks) to ensure sufficient data per random-effect level for LMM convergence, rather than a sparse 500-run subset.

## Compute Feasibility Strategy

*   **CPU First**: The primary path uses `transformers` with `torch_dtype=torch.float32` (or `float16` if available on CPU) for a quantized 8B model. If OOM occurs, the specific run is logged as `status: 'oom'` and excluded from analysis. **No GPU offload is permitted** to preserve causal validity.
* **Data Streaming**: If the full 30k matrix exceeds RAM, the pipeline will process tasks in batches (e.g., 10 tasks at a time), writing results immediately to `data/interim` and deleting input batches to free memory. However, the feasible run is a balanced subset of [deferred] runs.

## References

*   Spec: `spec.md`
*   Constitution: `projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/.specify/memory/constitution.md`