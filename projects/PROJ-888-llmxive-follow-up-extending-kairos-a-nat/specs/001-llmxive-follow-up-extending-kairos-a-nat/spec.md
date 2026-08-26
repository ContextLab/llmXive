# Feature Specification: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

**Feature Branch**: `001-llmxive-kairos-discrete-scaling`  
**Created**: 2026-08-24  
**Status**: Draft  
**Input**: User description: "How does the minimum information density required for stable long-horizon forecasting in embodied agents scale as input modality shifts from continuous visual streams to sparse, discrete sensor streams, and what architectural properties are necessary to preserve error bounds under these constraints?"

## User Scenarios & Testing

### User Story 1 - Data Construction and Quantization Pipeline (Priority: P1)

The research system MUST convert the continuous `lerobot/libero_plus` benchmark dataset (RGB frames and proprioceptive states) into discrete, JSON-serialized state vectors with configurable quantization levels (4-bit, 6-bit, 8-bit, 16-bit) to simulate sparse sensor inputs. **Crucially**, velocities and acceleration vectors MUST be derived via finite differencing of the *continuous* ground-truth position data *before* any quantization occurs to prevent the amplification of quantization noise. A parallel "noise-only" dataset MUST be created by adding Gaussian noise (std dev = 0.1 * quantization_step) to the continuous states *before* quantization to model telemetry instability distinct from quantization error. The ingestion logic MUST explicitly map the `lerobot/libero_plus` parquet schema (verifying presence of `observations.positions` and `observations.ee_pos`, mapping `observations.ee_pos` to `position` and `observations.positions` to `orientation` where applicable) to the derivation pipeline.

**Why this priority**: Without a reproducible, quantized dataset where velocities are derived from continuous physics (not quantized artifacts), the study confounds "model instability" with "data corruption," invalidating the core research question regarding modality shift.

**Independent Test**: The pipeline can be tested by running the conversion script on a 10-episode subset of `lerobot/libero_plus`, verifying that the output JSON files contain discrete integer values within the specified bit-depth ranges, and confirming that the derived velocity fields in the discrete output match the velocity fields derived from the continuous source within a tolerance of < 1e-4 (proving pre-quantization derivation).

**Acceptance Scenarios**:

1. **Given** the raw `lerobot/libero_plus` dataset is downloaded, **When** the quantization script is executed with a target bit-depth of 4-bit, **Then** the output state vectors contain non-negative integer values within the range [0, 15] and the file size is reduced by at least 75% compared to the raw float32 representation (specific to the `lerobot/libero_plus` subset used).
2. **Given** a raw continuous state vector, **When** the script derives velocity from the continuous position data and *then* applies Gaussian noise injection (standard deviation = 0.1 * quantization_step) *before* quantization, **Then** the resulting noisy vector remains within the discrete quantization bins without floating-point leakage, and the velocity magnitude matches the continuous ground truth derivation.
3. **Given** the full dataset, **When** the pipeline runs on a 2-core CPU runner, **Then** the entire conversion process completes in ≤ 30 minutes and peak RAM usage remains < 7GB.

---

### User Story 2 - CPU-Only Model Training and Inference (Priority: P2)

The system MUST load the pre-trained Kairos Hybrid Linear Temporal Attention module, replace the visual embedding layers with a *heuristic-initialized* discrete projection layer (initialized via uniform mapping based on continuous mean/std or a 5-epoch proxy pre-training) to ensure convergence is not hindered by random initialization. The system MUST execute a "Fair Baseline" run where the continuous model uses a *similarly heuristic-initialized* projection layer to isolate the modality shift effect from initialization artifacts. The entire training and inference loop MUST execute on a CPU-only environment (GitHub Actions Free Tier: 2-core/7GB RAM/6h runtime) without GPU acceleration, CUDA, or mixed-precision quantization (no `load_in_8bit`, no `bitsandbytes`).

**Why this priority**: The core research question depends on evaluating the architecture's stability under CPU constraints and modality shift. A fair baseline and proper initialization are required to distinguish "modality shift" from "random initialization" failure, and the CPU constraint is a hard boundary for the study's feasibility.

**Independent Test**: The model can be tested by initiating a training run with a fixed random seed, verifying that the loss trend shows convergence (loss converges to within 10% of the continuous baseline loss or demonstrates a stable gradient norm < 0.01 over 5 epochs), confirming that the total training time is ≤ 4 hours (graceful exit if > 6h), and confirming that inference on a long sequence completes without CUDA errors or out-of-memory exceptions.

**Acceptance Scenarios**:

1. **Given** the pre-trained Kairos weights are available, **When** the visual embedding layers are replaced with a heuristic-initialized discrete projection layer, **Then** the model initialization completes successfully on a CPU-only PyTorch environment without any "CUDA device" or "bitsandbytes" errors.
2. **Given** a training loop configured for a sufficient number of epochs to ensure convergence, **When** it runs on the 2-core CPU runner, **Then** the total training time for the sampled dataset is ≤ 4 hours (graceful exit if > 6h), and the loss curve shows convergence (loss converges to within 10% of the continuous baseline loss or demonstrates a stable gradient norm < 0.01 over 5 epochs).
3. **Given** a trained model, **When** it predicts a 1000-step horizon sequence, **Then** the inference latency per step is recorded, and the cumulative RAM usage remains < 6GB throughout the sequence generation.

---

### User Story 3 - Stability Analysis and Threshold Mapping (Priority: P3)

The system MUST compute the **Total Mean Squared Error (MSE)** between predicted and ground-truth discrete sequences across varying quantization levels and noise levels. The stability threshold is defined as the point where the *Total MSE* of the discrete model exceeds the *Total MSE* of the continuous baseline by a statistically significant margin (determined by the upper bound of the confidence interval of the ratio). The system MUST perform statistical validation using a **Linear Mixed-Effects Model (LMM)** with 'episode_id' as a random effect and 'modality' as a fixed effect (or a block-bootstrap method) to account for temporal autocorrelation and serial correlation in autoregressive errors. The analysis MUST include horizons of **100**, 500, and **1000** time steps. A sensitivity analysis MUST sweep the quantization resolution (varying bit-widths) and report how the error rates vary.

**Why this priority**: This is the direct answer to the research question. It synthesizes the data and model outputs into the "scaling law" and "threshold" findings required for the paper, using scientifically valid statistical methods that respect the non-independence of time-series errors.

**Acceptance Scenarios**:

1. **Given** the prediction results for 4-bit, 6-bit, 8-bit, and 16-bit inputs, **When** the error accumulation rate is calculated, **Then** the system produces a clear non-linear scaling curve and reports the specific quantization threshold where the Total MSE ratio (Discrete/Continuous) exceeds the upper bound of the 95% confidence interval for the null hypothesis (ratio=1).
2. **Given** N runs (determined by power analysis) with different noise seeds, **When** a Linear Mixed-Effects Model is performed on the error rates between discrete and visual modalities (paired by run_id), **Then** the system outputs a p-value and explicitly states whether the difference is statistically significant (p < 0.05) or indistinguishable.
3. **Given** the sensitivity analysis results, **When** the quantization threshold is swept, **Then** the system reports the specific error rate change and identifies the stability boundary with a confidence interval.

### Edge Cases

- **What happens when** the quantization level is so low (e.g., 1-bit) that the state space collapses to a single value? The system MUST detect this degeneracy, raise an exception, and exit with code 1, flagging the output as "Invalid Data" rather than producing a false stability metric.
- **How does system handle** a scenario where the CPU runner hits the 6-hour time limit during training? The system MUST checkpoint the model state every epoch and gracefully exit, logging the progress so the run can be resumed or the sample size reduced. This handling applies to all horizons (100, 500, 1000).
- **What happens when** the noise injection (std dev = 0.1 * quantization_step) causes the discrete state to flip to a completely invalid bin? The system MUST clamp the noise to the nearest valid discrete bin to prevent data corruption in the ground truth. (Note: Noise is added to continuous states *before* quantization; clamping occurs after the quantization step is applied to the noisy continuous value).

## Requirements

### Functional Requirements

- **FR-001**: System MUST convert continuous `lerobot/libero_plus` dataset frames and proprioceptive states into discrete JSON-serialized vectors with user-defined quantization levels (4-bit, 6-bit, 8-bit, 16-bit) to simulate sparse sensor inputs. Velocities MUST be derived via finite differencing of the *continuous* position data *before* quantization. Noise injection MUST use a standard deviation of 0.1 * quantization_step applied to continuous data before quantization. The ingestion logic MUST map the specific schema of the source parquet files (e.g., `observations.ee_pos` -> `position`, `observations.positions` -> `orientation`) and verify the presence of position fields. (See US-1).
- **FR-002**: System MUST process discrete inputs through the *same* unpruned Kairos architecture, replacing the visual encoder with a *heuristic-initialized* discrete projection layer that is *trained* alongside the rest of the model. The system MUST also execute a "Fair Baseline" run where the continuous model uses a *similarly heuristic-initialized* layer to isolate modality shift. (See US-2).
- **FR-003**: System MUST execute the full training and inference pipeline on a CPU-only environment (GitHub Actions Free Tier: 2-core/7GB RAM/6h runtime) without requiring GPU, CUDA, or mixed-precision accelerators. (See US-2).
- **FR-004**: System MUST calculate the **Total Mean Squared Error (MSE)** between predicted and ground-truth discrete sequences and report the *Total MSE* for both discrete and continuous modalities. The system MUST **NOT** subtract a theoretical "Quantization Noise Floor" from the Total MSE to derive "Model Error"; instead, it MUST compare Total MSEs directly or use variance decomposition (ANOVA) if attribution is needed. (See US-3).
- **FR-005**: System MUST perform statistical validation using a **Linear Mixed-Effects Model (LMM)** with 'episode_id' as a random effect and 'modality' as a fixed effect, or a block-bootstrap method, across N runs to determine significance of error accumulation, explicitly accounting for temporal autocorrelation. The system MUST output a `stats_results.json` artifact containing p-values, confidence intervals, and model coefficients. (See US-3).
- **FR-006**: System MUST implement a sensitivity analysis that sweeps the quantization resolution (4-bit, 6-bit, 8-bit, 16-bit) and reports the variation in headline error rates, including analysis over horizons of **100**, 500, and **1000** time steps. (See US-3).
- **FR-007**: System MUST log CPU utilization, peak RAM usage, and latency per time step using `psutil` to verify compliance with the 2-core/7GB RAM/6h GitHub Actions Free Tier constraints and MUST output a `resource_profile.json` artifact containing these metrics with keys `peak_ram_gb`, `total_time_h`, and `cpu_utilization_avg`. (See US-2).
- **FR-008**: System MUST explicitly frame stability claims as "mse_ratio" (Total MSE Discrete / Total MSE Continuous) or "relative_degradation (mse_ratio - 1)" in a specific output field named `stability_claim_framing` within the final results JSON or report. The value MUST be numeric. (See US-3).
- **FR-009**: System MUST perform an a priori power analysis to determine the required number of independent runs (N), targeting a minimum detectable effect size (Cohen's d) of 0.5 with power ≥ 0.8. Pairing for statistical tests MUST be at the 'run' level (comparing mean error of Run A discrete vs mean error of Run A continuous) for the power analysis, while the LMM uses 'episode_id' as a random effect within runs. The system MUST output a `power_analysis_report.json` artifact with effect size, alpha, beta, and calculated N. (See US-3).
- **FR-010**: System MUST detect 1-bit collapse (state space degeneracy) and halt the run by raising an exception and exiting with code 1. (See Edge Cases).

### Key Entities

- **DiscreteStateVector**: Represents the quantized state of the embodied agent at a single time step, containing integer values for object positions, velocities (derived from continuous data), and binary collision flags. Fields: `timestamp`, `position`, `velocity`, `collision_flags`, `is_dropped` (boolean indicating if the state was dropped due to degeneracy), `metadata` (object containing source schema mapping info).
- **PredictionHorizon**: The number of future time steps (100, 500, and 1000) the model attempts to predict from a given input sequence.
- **ErrorMetric**: A composite record containing the total MSE (Discrete), total MSE (Continuous), the ratio of Discrete MSE to Continuous MSE, cumulative error growth rate, and statistical significance (p-value) for a specific quantization level and noise seed. Includes fields: `mse_discrete`, `mse_continuous`, `mse_ratio`, `cumulative_error_rate`, `p_value`, `is_significant`.
- **ErrorAccumulationRate**: The rate of Total MSE growth per time step, calculated as the slope of the Total MSE vs. time step curve over a specific horizon. Used to determine relative degradation.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The minimum information density threshold (quantization level) required to maintain stable long-horizon forecasting is measured against the point where the Total MSE ratio (Discrete/Continuous) exceeds the upper bound of the 95% confidence interval for the null hypothesis (ratio=1). This threshold MUST be reported as a specific numeric value in the final results JSON. (See US-3).
- **SC-002**: The error accumulation rate (Total MSE growth per time step) is measured against the continuous visual-modality baseline to determine the relative degradation caused by the discrete modality. (See US-3).
- **SC-003**: The computational feasibility (training time and peak RAM) is measured against the time and memory constraints of the GitHub Actions Free Tier runner (≤6h, ≤7GB), with an explicit validation step that produces a pass/fail result based on the `resource_profile.json` artifact (comparing `total_time_h` ≤ 6.0 and `peak_ram_gb` ≤ 7.0). (See US-2).
- **SC-004**: The statistical significance of the difference in error rates between discrete and visual modalities is measured against the p < 0.05 threshold using a Linear Mixed-Effects Model or block-bootstrap (paired by run_id). (See US-3).
- **SC-005**: The sensitivity of the stability threshold to quantization resolution is measured by the change in Total MSE ratio when sweeping the bit-depth across a set of representative resolutions (4, 6, 8, 16-bit). (See US-3).
- **SC-006**: The Total MSE of the discrete model is reported as a raw value without subtraction of a theoretical noise floor; any noise floor analysis is reported separately as a reference metric, not used to derive model error. "Model Error" is not a defined metric in this spec; only "Total MSE" is used for comparisons. (See US-3).

## Assumptions

- **Assumption about data**: The `lerobot/libero_plus` dataset is publicly available and contains sufficient variety of object states and collision events to generate a representative "Sparse Physical World" dataset after quantization. The specific schema (e.g., `observations.positions`, `observations.ee_pos`) is verified to expose position fields for velocity derivation. Velocities are derived from the continuous ground truth before quantization.
- **Assumption about scope boundaries**: The study focuses exclusively on the Hybrid Linear Temporal Attention mechanism within the Kairos architecture; other architectural components (e.g., visual encoders, policy heads) are assumed to be irrelevant to the specific stability question of the attention module on sparse data.
- **Assumption about target hardware**: The GitHub Actions Free Tier (2-core/7GB RAM/6h runtime) is representative of the target "resource-constrained" edge environment, and the CPU-only training time will remain within a practical duration for the sampled dataset size.
- **Assumption about quantization**: The discrete state vectors generated by 4-bit, 6-bit, 8-bit, and 16-bit quantization will retain enough semantic information to allow the model to learn a valid predictive distribution, provided the information density is above the identified threshold.
- **Hypothesis about noise injection**: The injected Gaussian noise (std dev = 0.1 * quantization_step) accurately simulates the telemetry instability found in real-world industrial IoT and micro-controller sensors. This hypothesis requires validation against real-world telemetry data if available, or citation of a source for this noise model. This noise is distinct from quantization noise and is accounted for in the Total MSE analysis.
- **Assumption about statistical power**: An a priori power analysis will determine the required sample size (N) to detect a minimum effect size (Cohen's d) of 0.5 with power ≥ 0.8. The use of LMM over t-test is justified by the need to account for temporal autocorrelation in time-series data, which is a scientifically necessary deviation from generic paired test requirements.
- **Assumption about model weights**: The pre-trained Kairos weights are available in a format compatible with the CPU-only PyTorch environment and do not require GPU-specific quantization (e.g., 8-bit/CUDA) to load.
- **Assumption about baseline comparison**: The 'continuous baseline' is derived from a separate run of the *same* unpruned Kairos model (with *heuristic-initialized* projection layer) on the continuous data, ensuring architectural consistency and equal initialization conditions when comparing modality effects.
- **Assumption about independent ground truth**: An independent ground truth for the discrete modality (e.g., high-fidelity sensor logs from a physical robot) is unavailable; therefore, the study is scoped to measure relative degradation against the continuous baseline rather than absolute stability.