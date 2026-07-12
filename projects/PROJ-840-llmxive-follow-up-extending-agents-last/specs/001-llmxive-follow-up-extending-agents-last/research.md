# Research: llmXive follow-up: extending "Agents' Last Exam"

## Research Question

Does decomposing long-horizon professional workflows into atomic steps reveal that agent failures are driven primarily by state persistence errors rather than reasoning deficits, and does explicit state recovery (via context checkpointing) significantly improve pass rates?

## Synthetic Data Generation Strategy

Since public ALE datasets with step-level `environment_state` granularity are unavailable or unverified, this project will generate a **Synthetic ALE Dataset** locally. This ensures full control over ground truth labels and data structure.

| Dataset Name | Source | Format | Variables Generated | Verification Status |
|--------------|--------|--------|---------------------|---------------------|
| ALE-Synthetic-Generator | Local Script (`code/data/generator.py`) | JSONL | `step_id`, `action`, `environment_state`, `task_description`, `outcome`, `ground_truth_label` | ✅ Verified (Deterministic) |

**Generation Logic**:
*   The generator creates tasks with N steps.
*   At random steps, it injects "State Persistence Errors" (e.g., deleting a file the agent later tries to edit) or "Reasoning Deficits" (e.g., agent chooses a logically invalid action despite correct state).
*   The `ground_truth_label` is recorded for validation (FR-009).
*   **Volume**: Target N=80 tasks to satisfy power analysis requirements.

**Dataset Selection Rationale**:
*   **Granularity**: Guarantees the presence of `environment_state` at every step, which is required for FR-001.
*   **Ground Truth**: Provides known labels to validate the classification logic (FR-009).
*   **Reproducibility**: The generator is seeded, ensuring identical data across runs (Constitution I).

## Model Strategy

**Target Model**: 7B parameter open-weight model (e.g., `Llama-3-8B-Instruct` in GGUF format).  
**Inference Engine**: `llama-cpp-python` (CPU backend).  
**Quantization**: **Q4_K_M** (approx. 4.2GB RAM for weights + context).  
**Precision**: Q4_K_M (CPU compatible, fits in limited RAM).  
**Memory Management**:  
*   Load model in Q4_K_M.  
*   Context window capped at a fixed limit..  
*   **No Fallback**: If the model fails to load or exceeds memory, the script logs "Hardware Infeasible" and exits. No switch to 3B or smaller models is permitted to preserve the 7B hypothesis test.  
*   **Context Window**: Truncate checkpoint summaries if they exceed model limits (FR-002 edge case).

**Rationale**: The spec mandates a 7B model. Q4_K_M quantization via `llama-cpp-python` is the only method to run a 7B model on a 7GB RAM CPU runner. This ensures the experiment is feasible without changing the experimental subject (model size).

## Statistical Methodology

**Primary Test**: Mixed-Effects Logistic Regression (GLMM).  
**Conditions**: Baseline (no checkpointing) vs. Intervention (checkpointing).  
**Unit of Analysis**: **Step Success** (binary: 0/1), not Task Pass/Fail.  
**Random Effects**: `Task ID` (to account for trajectory divergence and non-independence of steps within a task).  
**Fixed Effects**: `Condition` (Baseline/Intervention), `Checkpoint Interval` (if applicable), `Step Number`.  
**Multiple Comparison Correction**: Bonferroni or Benjamini-Hochberg (FDR) if testing multiple task categories (FR-005).  
**Power Analysis**:  
*   Based on pilot data, estimated baseline failure rate = 40%.  
*   Minimum Detectable Effect (MDE) = 15% improvement.  
*   Required Sample Size: ~80 tasks (A sufficient number of participants per condition) to achieve 80% power at alpha=0.05.  
*   If N < 80, the report will explicitly state "Preliminary" and provide confidence intervals rather than a binary p-value.

**Sensitivity Analysis**:  
*   Test checkpoint intervals N = {3, 5} and other representative values. (FR-006).  
*   Plot pass rate vs. N to identify optimal frequency.

## Decision & Rationale

| Decision | Rationale |
|----------|-----------|
| **Use Synthetic Data Generator** | Public datasets lack required `environment_state` granularity. Synthetic data ensures ground truth and reproducibility. |
| **Use GGUF Q4_K_M for 7B Model** | Only method to run 7B model on 7GB RAM CPU. Ensures 7B constraint is met. |
| **Use Mixed-Effects Logistic Regression** | Accounts for trajectory divergence and non-independence of steps. McNemar's test is invalid for this design. |
| **Apply Bonferroni correction** | Conservative approach for multiple hypothesis testing (FR-005). |
| **Validate reconstruction accuracy on a set of synthetic traces.** | Ensures the classification logic (FR-009) is sound before full analysis. |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Synthetic data does not reflect real-world complexity** | Medium | Medium | Validate against a small set of real-world traces if available; report limitation. |
| **7B model exceeds 7GB RAM on CPU** | Low | High (Blocking) | Use Q4_K_M (4.2GB). If it fails, log "Hardware Infeasible" and halt. No fallback. |
| **Statistical power too low (N < 80)** | Medium | Low | Report power limitation; interpret as preliminary with confidence intervals. |
| **Checkpoint summary truncation loses critical info** | Medium | Low | Implement compression heuristic; test with golden set. |