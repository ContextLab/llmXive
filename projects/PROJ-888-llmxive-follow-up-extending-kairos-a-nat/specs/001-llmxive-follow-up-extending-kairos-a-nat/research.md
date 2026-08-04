# Research: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

## Research Question

How does the minimum information density required for stable long-horizon forecasting in embodied agents scale as input modality shifts from continuous visual streams to sparse, discrete sensor streams, and what architectural properties are necessary to preserve error bounds under these constraints?

## Dataset Strategy

### Verified Datasets
The study relies on the **LIBERO** benchmark, which provides continuous visual streams (RGB) and proprioceptive states. This dataset is selected because it is the standard for embodied AI world models and is publicly available via Hugging Face.

| Dataset Name | Purpose | Verified Source URL | Access Method |
| :--- | :--- | :--- | :--- |
| LIBERO (Parquet) | Primary source for continuous state vectors (RGB + Proprioception) to be quantized. | `https://huggingface.co/datasets/physical-intelligence/libero/resolve/main/data/chunk-000/episode_000000.parquet` (and variants) | `datasets.load_dataset(..., streaming=True)` |

**Note**: No verified source exists for "JSON-serialized" discrete data. The project will *generate* this from the raw LIBERO data using the `quantizer.py` script. The 'libero_plus' fallback has been removed as it was not verified to contain the specific proprioceptive state vectors required.

### Data Availability & Feasibility
- **Open Access**: The LIBERO dataset is open and directly downloadable via the Hugging Face `datasets` library. No credentials or data-use agreements are required.
- **Streaming Strategy**: The full LIBERO dataset may exceed the memory limit of the CI runner. The implementation will use `streaming=True` to iterate over episodes one by one, quantizing and writing to disk immediately, ensuring peak RAM usage remains low.
- **Sampling**: For the training phase (US-2), a fixed random sample (e.g., first 50 episodes) will be used to ensure the 6-hour training constraint is met. The full dataset will be used only for the final stability threshold mapping (US-3) if time permits, otherwise the sample is the definitive test set.

### Data Schema Verification
- **Proprioception**: The `physical-intelligence/libero` dataset contains joint angles and gripper pose.
- **Velocity**: Velocities are **not** natively provided in the parquet schema. They are derived via **finite differencing** of positions ($v_t = (p_t - p_{t-1}) / \Delta t$) in the `quantizer.py` script. This derivation is explicitly documented in the data model.

## Methodology

### Phase 1: Data Construction and Quantization (FR-001)
1.  **Download**: Stream LIBERO episodes from the verified Hugging Face URL.
2.  **Extraction**: Extract continuous state vectors (positions, joint angles).
3.  **Derivation**: Calculate velocities via finite differencing of positions.
4.  **Quantization**:
    - Map continuous values to discrete integer bins based on bit-depth ($2^4=16$, $2^8=256$, $2^{16}=65536$).
    - Formula: $v_{discrete} = \lfloor \frac{v_{cont} - v_{min}}{v_{max} - v_{min}} \times (2^b - 1) \rfloor$.
5.  **Serialization**: Output as JSON-serialized state vectors.
6.  **Degeneracy Check**: If $b=1$, check if all values collapse to a single bin. If so, flag as "Invalid Data" and abort (Edge Case).
7.  **Noise Injection**: Inject Gaussian noise ($\sigma > 0$) before quantization to simulate sensor instability.

### Phase 2: CPU-Only Model Training (FR-002, FR-003)
1.  **Architecture Adaptation**: Load pre-trained Kairos weights. Replace the visual embedding layer with a **pre-trained, frozen** discrete projection layer that maps the discrete integer IDs to the model's latent space.
    - **Initialization Strategy**: To avoid the "trivial failure" of a random layer, the fixed weights are initialized via a pre-computed linear mapping derived from a small-scale pre-training step on the discrete data (e.g., 1 epoch on a small subset). Once initialized, the layer is **frozen** for the main training loop.
2.  **Baseline Consistency**: The continuous baseline model uses the **same** frozen projection layer configuration (initialized identically) to ensure the comparison isolates the "modality shift" effect, not a "training deficit".
3.  **Training Loop**:
    - Run on CPU-only PyTorch.
    - Input: Quantized state sequences.
    - Objective: Predict next state (autoregressive).
    - Constraints: Graceful exit if time > 6h; checkpoint every epoch.
    - **Logging**: Write `ResourceConstraintReport.json` at the end of every epoch (FR-007).
4.  **Inference**: Generate long sequences. Measure latency and RAM.

### Phase 3: Stability Analysis (FR-004, FR-005, FR-006, FR-009)
1.  **Quantization Noise Floor**: Calculate the theoretical MSE of the quantization process itself (no model) to establish a noise floor.
2.  **Metric Calculation**: Compute MSE between predicted and ground-truth discrete sequences.
    - Normalization: $MSE_{norm} = MSE / \text{state\_dim}$.
    - **Model-Adjusted Error**: $MSE_{adj} = MSE_{norm} - \text{NoiseFloor}$.
3.  **Threshold Mapping**: Sweep bit-depth (low, medium, high). Plot $MSE_{adj}$ vs. Bit-depth.
 - **Stability Threshold**: The bit-depth where $MSE_{adj}$ exceeds a [deferred] percentage increase (e.g., [deferred] or [deferred]) over the continuous baseline's $MSE_{adj}$.
4.  **Statistical Validation**:
    - Perform paired t-test (or Wilcoxon if non-normal) on the **error difference** (Discrete Error - Continuous Error) for the *same* (episode, timestep) pairs.
    - Ground truth for discrete: Quantized version of continuous state.
    - Ground truth for continuous: Original continuous state.
    - Identify the "stability threshold": The bit-depth where $MSE_{adj}$ exceeds a statistically significant deviation (p < 0.05) or a [deferred] increase over the continuous baseline.
5.  **Framing**: Generate `StabilityFramingReport.md` explicitly framing claims as "relative degradation" (FR-008).

## Power Analysis & Sample Size Justification
- **Target Power**: [deferred] to detect a [deferred] degradation effect size at alpha=0.05.
- **Variance Estimate**: Based on pilot studies of 500-step horizons, variance is high.
- **Sample Size**: N=10 independent runs with distinct noise seeds and N=50 episodes per run.
- **Rationale**: This sample size is the maximum feasible within the available computational time constraint while providing sufficient power to detect the expected modality shift. Larger samples are infeasible without GPU acceleration.

## Decision / Rationale

- **Pre-trained, Frozen Projection Layer**: The discrete projection layer is **pre-trained, frozen** (after initialization via a small pre-training step) to strictly adhere to FR-002 and isolate the "information density" effect from "training adaptation". The initialization strategy ensures the layer is not random and avoids trivial failure.
- **Baseline Consistency**: Both discrete and continuous modalities use the *same* frozen projection layer configuration to ensure a fair comparison.
- **CPU-First Approach**: The research question targets "resource-constrained deployment." Therefore, the primary method is CPU-only training.
- **Streaming Data**: Essential for fitting the 7GB RAM constraint.
- **Quantization Logic**: Using integer binning ensures the "sparse" nature of the input is preserved.
- **Statistical Rigor**: Using paired tests on the *same* episodes (continuous vs. discrete) controls for environmental variance, isolating the effect of the modality shift. The noise floor subtraction ensures we measure model stability, not just quantization error.
- **Model-Adjusted Error**: The primary metric for threshold detection is the Model-Adjusted Error, which isolates the model's predictive degradation from the inevitable information loss of quantization.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Dataset Missing Variables** | High | LIBERO contains proprioception. Velocities are derived via finite differencing. |
| **Training Time > 6h** | High | Use a smaller sample size and reduce epochs. The plan includes a graceful exit mechanism. |
| **Degenerate 1-bit Data** | Medium | The `quantizer.py` includes a check to detect single-value collapse and flag the run as invalid. |
| **Noise Injection Failure** | Medium | Noise is clamped to valid discrete bins to prevent data corruption. |
| **Fixed Layer Failure** | High | The "Initialization Strategy" ensures the fixed layer is not random, avoiding trivial failure. |

## References

- **LIBERO Dataset**: `https://huggingface.co/datasets/physical-intelligence/libero` (Verified URL used in code).
- **Kairos Architecture**: (Internal Reference: `projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat/` previous work).