# Research: EvoMem-Conflict Filtering for Robust LLM Agents

## Research Question

Does filtering retrieved memory traces in dynamic environments to include only 'conflict-inducing' patches significantly improve agent accuracy and reduce hallucination rates compared to retrieving all recent traces?

## Hypothesis

**H1**: The `EvoMem-Conflict` agent will demonstrate significantly higher accuracy and lower hallucination rates than `EvoMem-All` on the `Terminal-Bench-Evo` dataset, specifically in tasks requiring state tracking across contradictory updates.

**H2**: The `EvoMem-Conflict` agent will process significantly fewer context tokens (reduced "memory noise") without sacrificing performance.

## Dataset Strategy

### Terminal-Bench-Evo (Synthetic)
The `Terminal-Bench-Evo` dataset is **synthetically generated** by `code/data/generators/terminal_bench_evo_generator.py`. It is not a pre-existing external download.
- **Generation Logic**: The generator creates terminal command sequences with embedded state updates (file creations, deletions, permission changes) and explicitly introduces contradictions (e.g., "File X created" followed by "File X deleted" then "File X created again").
- **Validation**: The generator must produce at least `TARGET_TASKS` (default 200) unique task instances with at least 5 version updates each. A subset of labeled conflict/non-conflict pairs is extracted for validating the detector.
- **Source**: Internal code generation. No external URL cited.

### Conflict Detection Validation Set
- **Source**: Synthetic pairs generated from the same logic as `Terminal-Bench-Evo`.
- **Content**: `TARGET_PAIRS` (default 500) pairs of (Current State, Memory Patch) labeled as `conflict` or `no_conflict`.
- **Purpose**: To establish a precision/recall baseline (≥ 80%) for the heuristic before full agent execution.

## Methodology

### Phase 0: Data Validity Check
1.  **Pilot Study**: Before full-scale generation, run a pilot with `TARGET_TASKS`/10 tasks to ensure the synthetic contradictions are non-trivial and representative of real-world dynamic environments.
2.  **Real-World Validation**: If available, compare the synthetic contradiction patterns against a small set of real-world terminal logs to validate the generator's output.
3.  **Threshold**: If the pilot study shows trivial contradictions (e.g., LLM resolves them without memory), the generator logic must be revised.
4.  **Validation Gate**: If the generator fails to produce sufficient data, the pipeline flags this limitation in the final report.

### Phase 1: Conflict Detector Development
1.  **Model Selection**: Use `distilbert-base-uncased` (CPU-tractable, ~80M params) fine-tuned for binary classification (contradiction detection).
    *   *Rationale*: Fits within 7GB RAM on CPU; faster inference than larger models; sufficient for semantic contradiction detection in short text patches.
    *   *Constraint*: No 8-bit quantization or GPU usage. **Model size is fixed**; sensitivity analysis varies thresholds, not model architecture.
2.  **Training Data**: Synthetic pairs from the generator.
3.  **Hold-out Strategy**: To prevent circular validation, the conflict detector is trained on one set of contradiction rules and evaluated on a hold-out set generated with different rules. This ensures the detector learns semantic contradiction rather than generator syntax.
4.  **Thresholding**: Implement a confidence threshold. Patches with `prob(conflict) > threshold` are flagged.
5.  **Sensitivity Analysis (FR-008)**: Run the detector with varying **confidence thresholds** (0.70, 0.80, 0.90) to observe trade-offs between false positives (discarding useful context) and false negatives (retaining noise).

### Phase 2: Agent Execution
1.  **Baselines**:
    *   `EvoMem-All`: Retrieves the last $N$ patches (e.g., last 10) regardless of content.
    *   `EvoMem-Conflict`: Retrieves the latest state + patches flagged as conflicts. If no conflicts are detected, retrieves **latest state + 2 most recent non-conflict patches** (fallback) to ensure a consistent minimum context window size.
2.  **Environment**: `Terminal-Bench-Evo` tasks (target `TARGET_TASKS` instances).
3.  **Metrics Logged**:
    *   `task_id`, `agent_variant`, `patches_retrieved`, `context_tokens`, `inference_time`, `success_status`, `hallucination_type`.
    *   *Hallucination Definition*: (Incorrect command execution) OR (State description similarity < 90% to **Normalized Ground Truth**). The Normalized Ground Truth is a canonical natural language summary generated from the command log.

### Phase 3: Statistical Analysis
1.  **Primary Test**: Generalized Linear Mixed Models (GLMM) for binary accuracy outcomes, with task as a random effect. This accounts for the dependency structure and handles binary data appropriately.
    *   *Null Hypothesis*: No difference in median accuracy between variants.
    *   *Significance*: $p < 0.05$.
2.  **Secondary Test**: Wilcoxon signed-rank test on accuracy scores per task (descriptive only).
3.  **Noise Reduction**: Calculate mean percentage reduction in context tokens.
4.  **Hallucination Rate**: Compare rates using GLMM.
5.  **Unit of Analysis**: Task (aggregated per task).

## Feasibility & Constraints

- **Compute**: Target multiple CPU cores, 7GB RAM. `distilbert-base-uncased` inference is < 500ms/patch. A moderate number of tasks × multiple steps/task × 2 agents ≈ 4000 inferences. Total runtime estimated < 2 hours.
- **Memory**: Synthetic data is text-based; model is < 1GB. Fits comfortably.
- **Risk Mitigation**:
    *   *Low Conflict Rate*: If the generator produces < 10% conflicts, the study will flag this limitation. The fallback mechanism (latest state + 2 most recent non-conflict patches) ensures the agent still runs.
    *   *Detector Failure*: If confidence < 0.90, patch is treated as non-conflict (conservative).

## References
- **Dataset**: `Terminal-Bench-Evo` (Synthetic, generated by `code/data/generators/terminal_bench_evo_generator.py`). No external URL.
- **Model**: HuggingFace `distilbert-base-uncased` (Standard CPU model).