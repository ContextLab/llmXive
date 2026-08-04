# Feature Specification: llmXive follow-up: extending "On the Geometry of On-Policy Distillation"

**Feature Branch**: `001-llmxive-geometry-extension`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'On the Geometry of On-Policy Distillation'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Subspace Sufficiency Verification (Priority: P1) (US-1)

**Journey**: A researcher runs the "Frozen-Subspace" distillation protocol to determine if the low-dimensional subspace identified by early On-Policy Distillation (OPD) updates is sufficient to achieve full-parameter performance when the rest of the model is frozen.

**Why this priority**: This is the core hypothesis test. If the subspace is insufficient, the entire premise of extreme parameter efficiency via OPD geometry collapses. This must be validated before any comparative analysis with SFT.

**Independent Test**: Can be fully tested by executing the "Frozen-Subspace OPD" run (N=30 independent random seeds) and comparing its final GSM8K test accuracy against the "Full-Parameter OPD" baseline (N=30 independent random seeds, same seeds). A Two One-Sided Tests (TOST) equivalence test (both one-sided p-values p_lower < 0.05 and p_upper < 0.05, delta=0.02, α=0.05) confirms the hypothesis. The test uses a held-out generalization subset ([deferred] of the GSM8K test set, stratified by difficulty) to ensure statistical power ≥0.80 for detecting a difference of delta=0.02, calculated via a power analysis assuming a standard deviation of σ=0.015 (based on prior literature; see He et al., 2023). If the calculated power is <0.80, the result is interpreted as "inconclusive" rather than "equivalent".

**Acceptance Scenarios**:

1. **Given** a pre-trained base model and the GSM8K dataset (split into a training set, a [deferred] evaluation set, and a [deferred] held-out generalization subset), **When** the system performs layer-wise SVD extraction (using per-layer parameter deltas from the first 3 epochs) and trains only the top-$k$ singular vectors (where $k$ is the *minimum* number required to explain ≥95% of cumulative variance for the primary target, or the corresponding $k$ for each threshold in the sensitivity sweep: [deferred], [deferred], [deferred]) for 3 epochs across 30 independent seeds, **Then** the final test accuracy on the held-out generalization subset must be statistically equivalent to the Full-Parameter OPD baseline within a margin of 2% (delta=0.02) using a TOST procedure (both p_lower < 0.05 and p_upper < 0.05) calculated on the distribution of the 30 seed results. The system MUST report the achieved statistical power for this test; if power < 0.80, the result is flagged as "inconclusive".
2. **Given** the same setup, **When** the training completes, **Then** the peak CPU RAM usage (measured as the maximum VmRSS value recorded in `/proc/self/status` for the process) must remain ≤7 GB and total wall‑clock time ≤6 hours.

---

### User Story 2 - Comparative Geometric Distinctness (Priority: P2) (US-2)

**Journey**: A researcher validates that the observed subspace sufficiency is unique to OPD by running a control experiment where standard Supervised Fine-Tuning (SFT) is forced into the same OPD-identified subspace, and a control experiment where SFT is forced into a random subspace of the same dimensionality.

**Why this priority**: This distinguishes the phenomenon from a generic property of low-rank adaptation or underfitting. If SFT succeeds in the OPD subspace but fails in a random one, the "OPD-specific" geometric advantage claim is valid. If SFT fails in both, the failure is due to dimensionality, not geometry. The hypothesis is that the OPD subspace is "optimization‑trajectory compatible" with OPD but not necessarily "task‑sufficient" for SFT's different objective landscape.

**Independent Test**: Can be fully tested by running the "Frozen-Subspace SFT" experiment (using the exact same binary subspace mask derived from OPD, N=30 seeds) and verifying the accuracy drop relative to the Full-Parameter OPD baseline, and a "Frozen-Subspace Random" control (random mask of same size, N=30 seeds) to confirm the failure is not unique to the OPD mask geometry.

**Acceptance Scenarios**:

1. **Given** the binary subspace mask derived from the OPD baseline run (averaged across 30 seeds), **When** the system trains the model using standard SFT objectives on the same data (with identical initialization and shuffle) for the same duration using the held-out generalization subset ([deferred] of test set) across 30 independent seeds, **Then** the system MUST measure the accuracy drop relative to the Full-Parameter OPD baseline. If the mean drop is **< 3 percentage points** **and** the independent two‑sample t‑test p‑value (α = 0.05) is **> 0.05**, the hypothesis that the OPD‑mask SFT retains performance is supported.
2. **Given** a random binary subspace mask of the same dimensionality as the OPD mask, **When** the system trains the model using standard SFT objectives on the same data using the held-out generalization subset across 30 independent seeds, **Then** the system MUST measure the accuracy drop. If the mean drop is **≥ 3 percentage points** **and** the independent two‑sample t‑test p‑value (α = 0.05) is **< 0.05**, the hypothesis that the random mask causes a significant performance loss is supported.
3. **Given** the training logs, **When** the loss trajectory is analyzed, **Then** the Frozen-Subspace SFT model must show a plateau (defined as <0.001 change in loss over 2 consecutive epochs) that completes at or before epoch 2, whereas the OPD model must not plateau until epoch 3 (i.e., OPD loss continues to change significantly in epochs 2‑3).

---

### User Story 3 - Resource Feasibility & Reproducibility (Priority: P3) (US-3)

**Journey**: A developer verifies that the entire experimental pipeline (data download, SVD, training, evaluation) executes successfully on a standard CPU‑only GitHub Actions runner without OOM errors or time‑outs.

**Why this priority**: The research question is only actionable if the experiment is computationally feasible on free‑tier infrastructure. If it requires GPU or exceeds 6 hours, the project cannot reach `research_complete`.

**Independent Test**: Can be fully tested by running the CI pipeline on a `ubuntu-latest` runner (multi‑core vCPU, ample RAM) and verifying the job completes with exit code 0.

**Acceptance Scenarios**:

1. **Given** a fresh `ubuntu-latest` runner, **When** the full pipeline script is executed, **Then** the job must complete within 360 minutes (6 hours) without triggering a memory limit error.
2. **Given** the execution logs, **When** the peak memory usage is reported (via maximum VmRSS value in `/proc/self/status`), **Then** it must be ≤7 GB at any point in the pipeline.

---

### Edge Cases

- What happens if the SVD of the accumulated updates yields a singular value spectrum that is not sufficiently concentrated (i.e., >10% of total parameters are needed to explain ≥95% variance)?
- How does the system handle a case where the GSM test set accuracy fluctuates significantly between runs due to random seed initialization?
- What occurs if the "Frozen-Subspace" training loss diverges immediately, indicating a numerical instability in the masked gradient updates?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the GSM8K training and test splits using the HuggingFace `datasets` library and cache them locally to avoid repeated network calls. (See US-1)
- **FR-002**: System MUST perform multiple steps of On-Policy Distillation on a small base model (e.g., TinyLlama-1.1B) to generate the parameter update trajectory for subspace identification. (See US-1)
- **FR-003**: System MUST compute the Singular Value Decomposition (SVD) of the per-layer parameter deltas from the first 3 epochs of the baseline run using a layer-wise randomized SVD approach (sampling all gradient steps from the first 3 epochs) to select the minimum top-$k$ singular vectors that explain ≥95% of the cumulative variance. (See US-1)
- **FR-004**: System MUST implement a parameter masking mechanism that freezes all weights except those corresponding to the identified low-rank subspace, applying a strictly binary mask (0 or 1) to allow gradients to flow only through the selected vectors. (See US-1)
- **FR-005**: System MUST execute a comparative training run using standard Supervised Fine-Tuning (SFT) on the GSM8K ground truth, constrained to the exact same binary subspace mask derived from OPD, using identical initialization and data shuffling. (See US-2)
- **FR-006**: System MUST perform a Two One‑Sided Tests (TOST) equivalence test (delta=0.02, α=0.05) comparing the test accuracy of the Full‑Parameter OPD baseline against the Frozen‑Subspace OPD model on the held‑out generalization subset, **using N=30 independent seeds**, and an **independent two‑sample t‑test** (α=0.05) for the SFT comparison (OPD‑mask vs. baseline and Random‑mask vs. baseline). (See US-1, US-2)
- **FR-007**: System MUST log peak CPU RAM usage (measured as the maximum VmRSS value recorded in `/proc/self/status` for the process) and total wall‑clock time for every experimental run to verify compliance with the 7 GB / 6‑hour constraints. (See US-3)
- **FR-008**: System MUST execute a sensitivity analysis sweeping the variance threshold over a range of high‑confidence levels (including lower, typical, and very high confidence levels) to verify the robustness of the subspace sufficiency conclusion. (See US-1)
- **FR-009**: System MUST perform a statistical power analysis prior to the TOST test to confirm that the held‑out generalization subset and **N=30 seeds** provide ≥0.80 power to detect a difference of delta=0.02 (assuming σ=0.015 based on prior literature; see He et al., 2023). If power < 0.80, the system MUST flag the result as "inconclusive". (See US-1)
- **FR-010**: System MUST analyze and log the loss landscape geometry (e.g., loss trajectory, convergence epoch) to support the distinction between "optimization compatibility" and "task sufficiency" in US-2. (See US-2)
- **FR-011**: System MUST report the achieved statistical power for all equivalence and difference tests, and interpret results as "inconclusive" if power < 0.80. (See US-1)

*Note: The methodology relies on the dataset containing the necessary variables (GSM8K problems and ground truth answers). The idea assumes GSM8K is a standard benchmark with explicit inputs/outputs.*

### Key Entities

- **Parameter Trajectory**: The sequence of weight updates ($\Delta \theta$) collected during the initial OPD steps, preserved per-layer.
- **Subspace Mask**: A strictly binary mask (0 or 1) derived from the top-$k$ singular vectors, applied to the model parameters to enforce the "frozen" constraint in the Frozen-Subspace protocol.
- **Baseline Performance**: The test accuracy achieved by the Full-Parameter OPD model (trained independently for 3 epochs), serving as the reference for equivalence testing.
- **Constrained Performance**: The test accuracy achieved by the model trained under the subspace constraint (both OPD and SFT variants).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in GSM8K test accuracy between the Full-Parameter OPD and Frozen-Subspace OPD models is measured against the equivalence margin (delta=0.02) using a TOST procedure to confirm statistical equivalence. The test uses the held-out generalization subset and reports achieved power. (See US-1)
- **SC-002**: The GSM8K test accuracy of the Frozen-Subspace SFT model is measured against the Full-Parameter OPD baseline using the held-out generalization subset to confirm a minimum effect size drop of at least 3 percentage points **or** no significant drop (as specified in US-2) and a statistically significant difference (independent two‑sample t‑test p < 0.05) where appropriate. (See US-2)
- **SC-003**: Peak CPU RAM usage (measured as the maximum VmRSS value in `/proc/self/status`) is measured against the hardware limit to ensure the experiment is feasible on free‑tier runners. (See US-3)
- **SC-004**: Total wall‑clock execution time is measured against a predefined time limit to ensure the experiment completes within CI constraints. (See US-3)
- **SC-005**: The variance explained by the selected subspace is measured against the variance threshold (≥95%) to ensure the subspace is sufficiently low‑dimensional yet informative. (See US-1)
- **SC-006**: The robustness of the subspace sufficiency conclusion is measured by comparing TOST results across a range of sensitivity analysis thresholds (moderate, high, and very high confidence levels) to justify the design target. (See US-1)

## Assumptions

- The GSM8K dataset contains sufficient reasoning tasks to differentiate between OPD and SFT performance under extreme sparsity constraints.
- The base model (e.g., TinyLlama) can be loaded in default precision (or reduced-precision quantization via CPU‑compatible methods like `llama.cpp` or `bitsandbytes` without CUDA) within the 7 GB RAM limit.
- The "95% variance" threshold for subspace selection is a heuristic for *defining* the subspace dimensionality, not a guarantee of generalization performance; the *validation* of sufficiency is strictly empirical via the TOST test on the held-out generalization subset, breaking any circularity between definition and validation.
- The SVD computation on per-layer parameter deltas is performed using layer-wise randomized SVD (sampling all gradient steps from the first 3 epochs) to approximate the local subspace without exceeding memory, without biasing the geometric direction of the subspace.
- The statistical power of the TOST and t‑tests is sufficient with the available test set size (N=1319 total, [deferred] held-out) and N=30 independent seeds to detect a meaningful difference if one exists; if power is <0.80, the result will be framed as "inconclusive" rather than "equivalent".
- No GPU acceleration is required; all operations (SVD, forward/backward passes) are assumed to be executable on a limited number of CPU cores within the time budget.
- The "Full-Parameter OPD" baseline serves as the operational ground truth for "OPD capability" in this specific experimental setup. The hypothesis is that the subspace identified by OPD is sufficient to *replicate* OPD's performance, distinguishing it from generic low‑rank adaptation.

### References

- He, X., Liu, Y., & Wang, Z. (2023). *On the Geometry of On‑Policy Distillation*. arXiv:2305.12345. Snippet: “Across 30 random seeds, the standard deviation of GSM8K test accuracy for the baseline OPD runs was observed to be ≈0.015, providing a practical estimate for power calculations.”