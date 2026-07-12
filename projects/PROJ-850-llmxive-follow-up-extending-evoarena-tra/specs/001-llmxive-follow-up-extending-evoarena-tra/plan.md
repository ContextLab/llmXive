# Implementation Plan: EvoMem-Conflict Filtering for Robust LLM Agents

**Branch**: `001-evoconflict-filtering` | **Date**: 2026-07-12 | **Spec**: `specs/001-evoconflict-filtering/spec.md`
**Input**: Feature specification from `specs/001-evoconflict-filtering/spec.md`

## Summary

This feature implements a comparative study of two LLM agent variants: `EvoMem-All` (baseline retrieving all recent memory traces) and `EvoMem-Conflict` (experimental retrieving only the latest state and traces flagged as semantic contradictions). The core innovation is a CPU-tractable conflict-detection heuristic that filters "noise" from "signal" in dynamic terminal environments. The implementation focuses on a **synthetic data generator** for the `Terminal-Bench-Evo` dataset, a lightweight conflict classifier (using a CPU-optimized model like `distilbert-base-uncased`), and a dual-agent execution pipeline that logs context usage and execution success for statistical comparison via **Generalized Linear Mixed Models (GLMM)**.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `scikit-learn`, `pandas`, `pytest`, `datasets` (if applicable, otherwise synthetic generator)  
**Storage**: Local filesystem (`data/` for synthetic logs, `data/` for generated dataset)  
**Testing**: `pytest` (unit tests for conflict detector, integration tests for agent pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM)  
**Project Type**: Research CLI / Experimental Pipeline  
**Performance Goals**: Full experiment (200 tasks, 2 agents) must complete within 6 hours on CPU; conflict detector inference < 500ms per patch.  
**Constraints**: No GPU/CUDA; no 8-bit quantization; memory usage < 7 GB; dataset generation must be reproducible via random seeds.  
**Scale/Scope**: Synthetic dataset of a representative scale of tasks; a substantial set of labeled conflict pairs for detector validation (see **FR-001**: ≥ 500 labeled synthetic pairs).

> Empirical specifics (exact counts, performance metrics) are deferred to `research.md` and the implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Plan mandates pinned seeds in `code/` and synthetic data generation via deterministic scripts. Specifically, `random.seed()` in `terminal_bench_evo_generator.py` ensures reproducibility. Dynamic variables (`TARGET_PAIRS`, `TARGET_TASKS`) allow adjustment if generator output is insufficient. |
| **II. Verified Accuracy** | **Pass** | Citations in `research.md` will be restricted to verified URLs. For internal synthetic data, the **generator code** is verified against the spec and checksummed to satisfy the 'Verified Accuracy' gate. |
| **III. Data Hygiene** | **Pass** | Raw synthetic data will be checksummed; derivations (filtered logs) will be new files. No PII. |
| **IV. Single Source of Truth** | **Pass** | All metrics trace back to `data/` CSVs and `code/` analysis scripts. |
| **V. Versioning Discipline** | **Pass** | Artifacts will carry content hashes; `state/` updated on change. |
| **VI. Conflict-Based Retrieval Fidelity** | **Pass** | `EvoMem-Conflict` logic strictly adheres to heuristic flags. Fallback to **'latest state + 2 most recent non-conflict patches'** ensures the 'latest state' is always included, complying with the principle while maintaining context size and avoiding empty contexts. |
| **VII. Ground-Truth Execution Independence** | **Pass** | Success metrics rely on terminal command execution ground truth, not memory content. Specifically: **'incorrect command execution OR state misinterpretation (<90% similarity to Normalized Ground Truth)'**. |

**Resolved Concerns from Kickback**:
- **Dataset Clarification**: `Terminal-Bench-Evo` is explicitly defined as a **synthetic generator** in this plan. No external URL is cited. The name refers to the *type* of benchmark generated, not an external fetch.
- **Sensitivity Analysis (FR-008)**: The plan clarifies that the "sensitivity analysis" will vary the **confidence threshold** of the fixed `distilbert-base-uncased` model (0.70, 0.80, 0.90) rather than model size, as model size is fixed for CPU feasibility.
- **Statistical Test Consistency**: Plan mandates **Generalized Linear Mixed Models (GLMM)** for binary accuracy outcomes (primary) and Wilcoxon signed-rank test (secondary/descriptive) to address statistical soundness concerns. McNemar's test is not used.
- **Hallucination Metric**: `research.md` and implementation will define hallucination as **(Incorrect Command Execution) OR (State Misinterpretation < 90% similarity to Normalized Ground Truth)**, addressing `T026` gaps.
- **Dataset Sizes**: `research.md` and implementation will validate the synthetic generator's output size before proceeding; tasks will use variables (`TARGET_PAIRS`, `TARGET_TASKS`) rather than hardcoded literals to allow dynamic adjustment if the generator underperforms.
- **Context Size Confound**: Fallback logic updated to 'latest state + 2 most recent non-conflict patches' to ensure consistent context window size.
- **Circular Validation**: The detector training and validation sets will use **distinct contradiction rule sets** (Set A vs. Set B) to prevent the detector from learning generator syntax.
- **Ground Truth Generation**: 'Normalized Ground Truth' is generated by a **rule-based script** (`state_normalizer.py`) to ensure canonical, non-linguistic variance.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-evoarena-tra/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── generators/
│   │   ├── terminal_bench_evo_generator.py  # Synthetic dataset generator
│   │   └── state_normalizer.py              # Rule-based ground truth generator
│   └── conflict_pairs/
│       └── synthetic_conflict_dataset.json  # Labeled pairs for validation
├── models/
│   └── conflict_detector.py                 # CPU-tractable classifier wrapper
├── agents/
│   ├── base_agent.py                        # Abstract agent class
│   ├── evomem_all.py                        # Baseline variant
│   └── evomem_conflict.py                   # Experimental variant
├── analysis/
│   ├── metrics.py                           # Accuracy, hallucination, noise reduction
│   └── stats.py                             # GLMM, Wilcoxon, plots
├── main.py                                  # Orchestration script
└── requirements.txt                         # Pinned dependencies

tests/
├── unit/
│   └── test_conflict_detector.py
├── integration/
│   └── test_agent_pipeline.py
└── contract/
    └── test_schemas.py
```

**Structure Decision**: Single project structure. Separation of `data/generators`, `models`, `agents`, and `analysis` ensures modularity and aligns with the "Reproducibility" principle by isolating data generation from analysis.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Dual-Agent Pipeline | Required to isolate the variable (retrieval strategy) for the comparative study. | Single-agent run cannot establish the causal link between filtering and accuracy. |
| Synthetic Dataset Generator | `Terminal-Bench-Evo` is not externally available; must be generated to ensure specific conflict patterns exist. | Using a generic terminal dataset would likely lack the specific "evolving state" contradictions required for the hypothesis. |
| Threshold Sensitivity Analysis | Required by FR-008 to validate robustness. | Fixed threshold would not demonstrate the system's resilience to heuristic errors. |
| GLMM Statistical Test | Required to handle binary outcomes and dependency structure correctly. | Wilcoxon on binary data is underpowered and inappropriate for this design. |

## Methodology & Phases

### Phase 0: Data Validity Check (Pilot & Proxy)
1.  **Pilot Study**: Generate `TARGET_TASKS` (default 20) tasks using `terminal_bench_evo_generator.py`.
    *   **Validation**: Run against a "Human-in-the-Loop" or "Rule-Based Oracle" to verify that contradictions are non-trivial (i.e., an LLM without memory fails, but one with memory succeeds).
    *   **Real-World Proxy**: Compare the distribution of synthetic contradictions (e.g., file existence toggles) against a small, public sample of terminal logs (e.g., from a standard Linux test suite) to ensure the generator mimics real-world dynamics.
    *   **Threshold**: If contradictions are trivial or distribution mismatches, the generator logic must be revised before full-scale generation.
2.  **Dataset Generation**: Upon pilot success, generate the full dataset (target `TARGET_TASKS` ≥ 200 tasks, `TARGET_PAIRS` ≥ 500 conflict pairs).
    *   **Validation Gate**: If the generator produces fewer than `TARGET_TASKS` or `TARGET_PAIRS`, the pipeline logs a warning and proceeds with available data, but flags this limitation in the final report to prevent invalid statistical conclusions.

### Phase 1: Conflict Detector Development
1.  **Model Selection**: Use `distilbert-base-uncased` (CPU-tractable, ~80M params) fine-tuned for binary classification (contradiction detection).
    *   *Rationale*: Fits within 7GB RAM on CPU; faster inference than larger models; sufficient for semantic contradiction detection in short text patches.
    *   *Constraint*: No 8-bit quantization or GPU usage. **Model size is fixed**; sensitivity analysis varies thresholds, not model architecture.
2.  **Training Data**: Synthetic pairs generated using **Set A** contradiction rules (e.g., file existence toggles).
3.  **Hold-out Strategy**: To prevent circular validation, the conflict detector is evaluated on a hold-out set generated using **Set B** contradiction rules (e.g., permission/ownership conflicts, temporal logic contradictions). This ensures the detector learns semantic contradiction rather than generator syntax.
4.  **Thresholding**: Implement a confidence threshold. Patches with `prob(conflict) > threshold` are flagged.
5.  **Sensitivity Analysis (FR-008)**: Run the detector with varying **confidence thresholds** (0.70, 0.80, 0.90) to observe trade-offs between false positives and false negatives.

### Phase 2: Agent Execution
1.  **Baselines**:
    *   `EvoMem-All`: Retrieves the last $N$ patches (e.g., last 10) regardless of content.
    *   `EvoMem-Conflict`: Retrieves the latest state + patches flagged as conflicts. If no conflicts are detected, retrieves **latest state + 2 most recent non-conflict patches** (fallback) to ensure a consistent minimum context window size.
2.  **Environment**: `Terminal-Bench-Evo` tasks (target a sufficient number of instances).
3.  **Metrics Logged**:
    *   `task_id`, `agent_variant`, `patches_retrieved`, `context_tokens`, `inference_time`, `success_status`, `hallucination_type`.
    *   *Hallucination Definition*: **(Incorrect Command Execution) OR (State description similarity < 90% to Normalized Ground Truth)**. The **Normalized Ground Truth** is a canonical natural language summary generated by `code/data/generators/state_normalizer.py` (rule-based extraction from command logs).

### Phase 3: Statistical Analysis
1.  **Primary Test**: **Generalized Linear Mixed Models (GLMM)** for binary accuracy outcomes, with task as a random effect. This accounts for the dependency structure and handles binary data appropriately.
    *   *Null Hypothesis*: No difference in median accuracy between variants.
    *   *Significance*: $p < 0.05$.
2.  **Secondary Test**: Wilcoxon signed-rank test on accuracy scores per task (descriptive only).
3.  **Noise Reduction**: Calculate mean percentage reduction in context tokens.
4.  **Hallucination Rate**: Compare rates using GLMM.
5.  **Unit of Analysis**: **Task** (aggregated per task). Step-level data is used only for descriptive token counts.

## Feasibility & Constraints

- **Compute**: Target multiple CPU cores, 7GB RAM. `distilbert-base-uncased` inference is < 500ms/patch. A moderate number of tasks × ~ steps/task × 2 agents A substantial number of inferences. Total runtime estimated < 2 hours.
- **Memory**: Synthetic data is text-based; model is < 1GB. Fits comfortably.
- **Risk Mitigation**:
    *   *Low Conflict Rate*: If the generator produces < 10% conflicts, the study will flag this limitation. The fallback mechanism (latest state + 2 most recent non-conflict patches) ensures the agent still runs.
    *   *Detector Failure*: If confidence < 0.90, patch is treated as non-conflict (conservative).

## References
- **Dataset**: `Terminal-Bench-Evo` (Synthetic, generated by `code/data/generators/terminal_bench_evo_generator.py`). No external URL.
- **Model**: HuggingFace `distilbert-base-uncased` (Standard CPU model).