# Feature Specification: llmXive follow-up: extending "On the Geometry of On-Policy Distillation"

**Feature Branch**: `001-llmxive-geometry-extension`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'On the Geometry of On-Policy Distillation'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Subspace Sufficiency Verification (Priority: P1)

**Journey**: A researcher runs the "Frozen-Subspace" distillation protocol to determine if the low-dimensional subspace identified by early On-Policy Distillation (OPD) updates is sufficient to achieve full-parameter performance when the rest of the model is frozen.

**Why this priority**: This is the core hypothesis test. If the subspace is insufficient, the entire premise of extreme parameter efficiency via OPD geometry collapses. This must be validated before any comparative analysis with SFT.

**Independent Test**: Can be fully tested by executing the "Frozen-Subspace OPD" run and comparing its final GSM8K test accuracy against the "Full-Parameter OPD" baseline (trained independently with the same seed). A Two One-Sided Tests (TOST) equivalence test (both one-sided p-values p_lower < 0.05 and p_upper < 0.05, delta=0.02) confirms the hypothesis.

**Acceptance Scenarios**:

1. **Given** a pre-trained base model and the GSM8K dataset, **When** the system performs layer-wise SVD extraction (using per-layer parameter deltas from the first 3 epochs) and trains only the top-$k$ singular vectors (where $k$ is the *minimum* number required to explain ≥95% of cumulative variance) for 3 epochs, **Then** the final test accuracy must be statistically equivalent to the Full-Parameter OPD baseline within a margin of 2% (delta=0.02) using a TOST procedure (both p_lower < 0.05 and p_upper < 0.05).
2. **Given** the same setup, **When** the training completes, **Then** the peak CPU RAM usage (measured via `/proc/self/status` VmRSS, excluding OS overhead) must remain ≤7 GB and total wall-clock time ≤6 hours.

---

### User Story 2 - Comparative Geometric Distinctness (Priority: P2)

**Journey**: A researcher validates that the observed subspace sufficiency is unique to OPD by running a control experiment where standard Supervised Fine-Tuning (SFT) is forced into the same OPD-identified subspace, and a control experiment where SFT is forced into a random subspace of the same dimensionality.

**Why this priority**: This distinguishes the phenomenon from a generic property of low-rank adaptation or underfitting. If SFT succeeds in the OPD subspace but fails in a random one, the "OPD-specific" geometric advantage claim is valid. If SFT fails in both, the failure is due to dimensionality, not geometry.

**Independent Test**: Can be fully tested by running the "Frozen-Subspace SFT" experiment (using the exact same binary subspace mask derived from OPD) and verifying that it fails to converge to the performance of the Full-Parameter OPD baseline, while a "Frozen-Subspace Random" control (random mask of same size) also fails.

**Acceptance Scenarios**:

1. **Given** the binary subspace mask derived from the OPD baseline run, **When** the system trains the model using standard SFT objectives on the same data (with identical initialization and shuffle) for the same duration, **Then** the final test accuracy must be at least 3 percentage points lower than the Full-Parameter OPD baseline AND the two-sided t-test p-value must be < 0.05.
2. **Given** a random binary subspace mask of the same dimensionality as the OPD mask, **When** the system trains the model using standard SFT objectives on the same data, **Then** the final test accuracy must be at least 3 percentage points lower than the Full-Parameter OPD baseline AND the two-sided t-test p-value must be < 0.05, confirming that the failure is not unique to the OPD mask geometry but also occurs with random low-rank constraints.
3. **Given** the training logs, **When** the loss trajectory is analyzed, **Then** the Frozen-Subspace SFT model must show a plateau or divergence significantly earlier than the Frozen-Subspace OPD model.

---

### User Story 3 - Resource Feasibility & Reproducibility (Priority: P3)

**Journey**: A developer verifies that the entire experimental pipeline (data download, SVD, training, evaluation) executes successfully on a standard CPU-only GitHub Actions runner without OOM errors or time-outs.

**Why this priority**: The research question is only actionable if the experiment is computationally feasible on free-tier infrastructure. If it requires GPU or exceeds 6 hours, the project cannot reach `research_complete`.

**Independent Test**: Can be fully tested by running the CI pipeline on a `ubuntu-latest` runner (multi-core vCPU, ample RAM) and verifying the job completes with exit code 0.

**Acceptance Scenarios**:

1. **Given** a fresh `ubuntu-latest` runner, **When** the full pipeline script is executed, **Then** the job must complete within 360 minutes (6 hours) without triggering a memory limit error.
2. **Given** the execution logs, **When** the peak memory usage is reported (via `/proc/self/status` VmRSS), **Then** it must be ≤7 GB at any point in the pipeline.

---

### Edge Cases

- What happens if the SVD of the accumulated updates yields a singular value spectrum that is not sufficiently concentrated (i.e., >10% of total parameters are needed to explain ≥95% variance)?
- How does the system handle a case where the GSM8K test set accuracy fluctuates significantly between runs due to random seed initialization?
- What occurs if the "Frozen-Subspace" training loss diverges immediately, indicating a numerical instability in the masked gradient updates?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the GSM8K training and test splits using the HuggingFace `datasets` library and cache them locally to avoid repeated network calls. (See US-1)
- **FR-002**: System MUST perform multiple steps of On-Policy Distillation on a small base model (e.g., TinyLlama-1.1B) to generate the parameter update trajectory for subspace identification. (See US-1)
- **FR-003**: System MUST compute the Singular Value Decomposition (SVD) of the per-layer parameter deltas from the first 3 epochs of the baseline run using a layer-wise randomized SVD approach (sampling all gradient steps from the first 3 epochs) to select the minimum top-$k$ singular vectors that explain ≥95% of the cumulative variance. (See US-1)
- **FR-004**: System MUST implement a parameter masking mechanism that freezes all weights except those corresponding to the identified low-rank subspace, applying a strictly binary mask (0 or 1) to allow gradients to flow only through the selected vectors. (See US-1)
- **FR-005**: System MUST execute a comparative training run using standard Supervised Fine-Tuning (SFT) on the GSM8K ground truth, constrained to the exact same binary subspace mask derived from OPD, using identical initialization and data shuffling. (See US-2)
- **FR-006**: System MUST perform a Two One-Sided Tests (TOST) equivalence test (delta=0.02, α=0.05) comparing the test accuracy of the Full-Parameter OPD baseline against the Frozen-Subspace OPD model, and a two-sided paired t-test (α=0.05) for the SFT comparison. (See US-1, US-2)
- **FR-007**: System MUST log peak CPU RAM usage (measured via `/proc/self/status` VmRSS) and total wall-clock time for every experimental run to verify compliance with the 7 GB / 6-hour constraints. (See US-3)
- **FR-008**: System MUST execute a sensitivity analysis sweeping the variance threshold over a range of high-confidence levels to verify the robustness of the subspace sufficiency conclusion. (See US-1)

*Note: The methodology relies on the dataset containing the necessary variables (GSM8K problems and ground truth answers). The idea assumes GSM8K is sufficient for testing reasoning capabilities. No `[NEEDS CLARIFICATION]` is needed regarding dataset variables as GSM8K is a standard benchmark with explicit inputs/outputs.*

### Key Entities

- **Parameter Trajectory**: The sequence of weight updates ($\Delta \theta$) collected during the initial OPD steps, preserved per-layer.
- **Subspace Mask**: A strictly binary mask (0 or 1) derived from the top-$k$ singular vectors, applied to the model parameters to enforce the "frozen" constraint in the Frozen-Subspace protocol.
- **Baseline Performance**: The test accuracy achieved by the Full-Parameter OPD model (trained independently for 3 epochs), serving as the reference for equivalence testing.
- **Constrained Performance**: The test accuracy achieved by the model trained under the subspace constraint (both OPD and SFT variants).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in GSM8K test accuracy between the Full-Parameter OPD and Frozen-Subspace OPD models is measured against the equivalence margin (delta=0.02) using a TOST procedure to confirm statistical equivalence. (See US-1)
- **SC-002**: The GSM8K test accuracy of the Frozen-Subspace SFT model is measured against the Full-Parameter OPD baseline to confirm a statistically significant performance drop of at least 3 percentage points (p < 0.05). (See US-2)
- **SC-003**: Peak CPU RAM usage (measured via `/proc/self/status` VmRSS) is measured against the hardware limit to ensure the experiment is feasible on free-tier runners. (See US-3)
- **SC-004**: Total wall-clock execution time is measured against a predefined time limit to ensure the experiment completes within CI constraints. (See US-3)
- **SC-005**: The variance explained by the selected subspace is measured against the variance threshold (≥95%) to ensure the subspace is sufficiently low-dimensional yet informative. (See US-1)
- **SC-006**: The robustness of the subspace sufficiency conclusion is measured by comparing TOST results across a range of sensitivity analysis thresholds. (See US-1)

## Assumptions

- The GSM8K dataset contains sufficient reasoning tasks to differentiate between OPD and SFT performance under extreme sparsity constraints.
- The base model (e.g., TinyLlama) can be loaded in default precision (or reduced-precision quantization via CPU-compatible methods like `llama.cpp` or `bitsandbytes` without CUDA) within the 7 GB RAM limit.
- The "95% variance" threshold for subspace selection is a fixed design target (community standard for LoRA/PEFT) for capturing the "signal" in low-rank adaptation experiments; a sensitivity analysis will sweep this threshold (e.g., 90%, 95%, 99%) to verify robustness.
- The SVD computation on per-layer parameter deltas is performed using layer-wise randomized SVD (sampling all gradient steps from the first 3 epochs) to approximate the local subspace without exceeding memory, without biasing the geometric direction of the subspace.
- The statistical power of the TOST and t-tests is sufficient with the available test set size (approx. a representative subset of GSM8K test examples) to detect a meaningful difference if one exists; if power is low, the result will be framed as "inconclusive" rather than "equivalent."
- No GPU acceleration is required; all operations (SVD, forward/backward passes) are assumed to be executable on 2 CPU cores within the time budget.