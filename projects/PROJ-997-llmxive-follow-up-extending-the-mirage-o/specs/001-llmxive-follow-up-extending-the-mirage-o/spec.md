# Feature Specification: llmXive follow-up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

**Feature Branch**: `001-llmxive-mipu-gap-bounds`  
**Created**: 2026-08-06  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'The Mirage of Optimizing Training Policies: Monotonic Inference Polici'"

## User Scenarios & Testing

### User Story 1 - Hardware-Validated Gap Dataset Generation (Priority: P1)

As a researcher, I need to generate a dataset pairing full-precision training signals (gradient norms, local curvature) with ground-truth policy divergence measured by a CPU-based quantized inference engine, so that I can train a predictor that reflects real hardware constraints rather than simulated noise.

**Why this priority**: This is the foundational data layer. Without ground-truth divergence measured against actual hardware (e.g., `llama.cpp` or ONNX Runtime), any subsequent model training or bound verification is theoretically unsound and fails the project's core validation requirement.

**Independent Test**: This story is complete when a CSV/Parquet file exists containing rows with: `input_id`, `gradient_norms`, `local_curvature`, `quantized_logits`, and `calculated_kl_divergence`. The `calculated_kl_divergence` column must be non-zero for a statistically significant portion of the dataset, proving quantization effects are captured.

**Acceptance Scenarios**:

1. **Given** a pre-trained LLM (e.g., Llama-3-8B) and a sample of prompts from GSM8K, **When** the system runs inference in full precision and then in INT8, INT4, and FP8 via `llama.cpp` on a CPU, **Then** the system calculates the KL divergence between the full-precision and each quantized output distribution and stores it as the ground truth.
2. **Given** the same prompts, **When** the system extracts gradient norms and local curvature from the training state, **Then** these features are aligned with the ground-truth divergence values in the output dataset.
3. **Given** a dataset subset, **When** the system compares the mean divergence of INT8/INT4/FP8 vs FP16, **Then** the difference is non-zero and statistically significant (p < 0.05), confirming the quantization gap exists and is measurable.

---

### User Story 2 - Training-Signal Predictor Model (Priority: P2)

As a researcher, I need to train a lightweight regression model (e.g., Kernel Ridge Regression or small MLP) to predict the hardware-measured policy gap using only training-side features (gradient norms, curvature), so that I can replace expensive synchronous hardware checks with a fast analytical bound.

**Why this priority**: This implements the core hypothesis: that training signals contain sufficient information to bound the divergence. It is the "solution" component of the research question.

**Independent Test**: This story is complete when a trained model artifact exists that, given new training-side features (gradient norms, curvature), outputs a predicted divergence value. The model must achieve a correlation coefficient (r) of > 0.8 on a held-out validation set against the ground-truth hardware divergence.

**Acceptance Scenarios**:

1. **Given** the generated dataset from US-001, **When** the system trains a Kernel Ridge Regression model on a [deferred] split of the data, **Then** the model achieves a Pearson correlation coefficient of at least 0.8 with the ground-truth divergence on the remaining test set.
2. **Given** a new set of training features not seen during training, **When** the model predicts the gap, **Then** the output is a single scalar value representing the estimated KL divergence.
3. **Given** a comparison between the predicted gap and the actual hardware gap, **When** the error is calculated, **Then** the Mean Absolute Error (MAE) is < 0.1 for normalized divergence.

---

### User Story 3 - Bound Verification & Statistical Validation (Priority: P3)

As a researcher, I need to verify if a consistent theoretical bound holds across different quantization levels (INT4, INT8, FP8) and statistically compare the proxy-based MIPU loop against the full-hardware-sync baseline, so that I can confirm the feasibility of the latency reduction.

**Why this priority**: This delivers the final research conclusion. It validates the "bound" aspect of the research question and provides the empirical evidence required to claim the gap is solvable.

**Independent Test**: This story is complete when a report exists showing the correlation between predicted and actual gaps across quantization levels (INT4, INT8, FP8) and a statistical test (paired t-test) result comparing policy acceptance rates between the proxy and baseline methods.

**Acceptance Scenarios**:

1. **Given** the trained predictor and test data, **When** the system compares predicted vs. actual divergence across multiple quantization levels (INT4, INT8, and FP8), **Then** the correlation coefficient remains > 0.8 for at least one quantization level, demonstrating the bound holds.
2. **Given** a small-scale RL task, **When** the system runs the MIPU loop using the proxy vs. the full hardware sync, **Then** a paired t-test on the final reasoning scores shows no significant degradation (p > 0.05) for the proxy method.
3. **Given** the latency measurements, **When** the system compares the proxy method to the baseline, **Then** the latency reduction is measured against the baseline full-hardware-sync method.

### Edge Cases

- **What happens when** the quantized engine produces logits that are numerically identical to full precision (e.g., for very simple inputs)? The system must handle zero-divergence cases without division-by-zero errors in KL calculation.
- **How does the system handle** inputs where gradient norms are near-zero (flat loss landscape)? The predictor must not hallucinate a high divergence gap when the training signal indicates stability.
- **What happens when** the CPU inference engine (e.g., `llama.cpp`) fails to load a specific quantization format? The system must log the error, skip that sample, and continue processing the rest of the dataset to ensure partial completion.

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract training-side features (gradient norms, local curvature) from the full-precision model state for every input sample. (See US-001)
- **FR-002**: System MUST execute inference using a CPU-based quantized engine (e.g., `llama.cpp` or ONNX Runtime) to generate ground-truth quantized logits for every input sample. (See US-001)
- **FR-003**: System MUST calculate the exact KL divergence between full-precision and quantized logits to serve as the ground-truth policy gap. (See US-001)
- **FR-004**: System MUST train a lightweight regression model (e.g., Kernel Ridge Regression) to predict the hardware-measured gap using only the extracted training features (gradient norms, curvature), trained jointly on data from INT4, INT8, and FP8 quantization levels. (See US-002)
- **FR-005**: System MUST evaluate the trained model on a held-out test set and report the Pearson correlation coefficient between predicted and actual divergence. (See US-002)
- **FR-006**: System MUST perform a statistical comparison (paired t-test) of policy acceptance rates and final scores between the proxy-based MIPU loop and the full-hardware-sync baseline. (See US-003)
- **FR-007**: System MUST verify if the theoretical bound (|predicted - actual| < 0.1) holds consistently across at least three different quantization bit-widths (INT4, INT8, and FP8). (See US-003)

### Key Entities

- **TrainingSample**: Represents a single input instance containing the input prompt, gradient norms, local curvature, and the associated ground-truth divergence.
- **QuantizedInferenceResult**: Represents the output of the hardware engine, including the quantized logits and the calculated KL divergence relative to the full-precision output.
- **GapPredictor**: The trained regression model that maps training features to an estimated policy gap.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation between predicted and actual policy gap is measured against the Pearson correlation coefficient (r) threshold of > 0.8 on the held-out test set. (See US-002, US-003)
- **SC-002**: The latency reduction of the proxy method is measured against the baseline full-hardware-sync method, targeting a reduction of ≥ 90% in the policy evaluation step. (See US-003)
- **SC-003**: The statistical equivalence of training stability is measured against a paired t-test (p > 0.05) comparing final reasoning scores of the proxy vs. baseline MIPU loops. (See US-003)
- **SC-004**: The robustness of the bound is measured against the consistency of the correlation coefficient (r > 0.8) across at least three distinct quantization levels (INT4, INT8, and FP8). (See US-003)
- **SC-005**: The computational feasibility is measured against the constraint that the entire analysis (dataset generation + model training + validation) completes within 6 hours on an ubuntu-latest runner; if this exceeds 6 hours, the dataset size is reduced until the constraint is met while maintaining statistical power (n ≥ 300 samples). (See FR-004, FR-005)

## Assumptions

- **Assumption about data availability**: The GSM8K subset used for evaluation is sufficiently representative of the reasoning tasks required to stress-test the quantization gap, and a pre-trained Llama-3-8B model is accessible via Hugging Face.
- **Assumption about hardware environment**: The GitHub Actions free-tier runner provides a CPU environment capable of running `llama.cpp` or ONNX Runtime with INT8 quantization, even if inference is slower than on GPU, and that the available RAM limit is sufficient for loading the 8B model in quantized form (e.g., using 4-bit or 8-bit quantization which fits within the available memory constraints)..
- **Assumption about methodological validity**: Since the study is observational (no random assignment of quantization levels to models), the findings regarding the correlation between training signals and hardware divergence are framed strictly as associational, not causal, to avoid inference errors.
- **Assumption about threshold justification**: The epsilon tolerance for the theoretical bound (|predicted - actual| < 0.1) is set to 0.1 (normalized) based on community standards for acceptable approximation error in RL policy proxies, and a sensitivity analysis will be performed by sweeping epsilon over a range of small values to ensure the conclusion is robust.
- **Assumption about collinearity**: Gradient norms and local curvature are treated as potentially collinear predictors; the analysis will include a Variance Inflation Factor (VIF) diagnostic to ensure the regression model does not claim independent predictive effects where none exist.
- **Assumption about multiplicity**: Since multiple quantization levels and statistical tests are performed, a Bonferroni correction or similar family-wise error rate control will be applied to the p-values in the final statistical comparison to account for multiple comparisons.