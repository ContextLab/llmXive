# Research: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

## Research Question

How does the minimum information density required for stable long-horizon forecasting in embodied agents scale as input modality shifts from continuous visual streams to sparse, discrete sensor streams, and what architectural properties are necessary to preserve error bounds under these constraints?

## Dataset Strategy

The study relies on the **LIBERO** benchmark, a standard dataset for embodied AI that provides high-fidelity continuous state representations (proprioceptive states).

| Dataset Component | Source / URL | Rationale | Access Method |
| :--- | :--- | :--- | :--- |
| **LIBERO LeRobot v3** | `https://huggingface.co/datasets/nvidia/LIBERO_LeRobot_v3` | Contains the necessary continuous proprioceptive states (positions, orientations) and task metadata required to derive discrete state vectors. | `datasets.load_dataset("nvidia/LIBERO_LeRobot_v3", split="train", streaming=True)` |
| **LIBERO Plus / LeRobot** | `https://huggingface.co/datasets/lerobot/libero_plus` | Alternative verified source for the same data structure if the primary source is rate-limited. | `datasets.load_dataset("lerolibero_plus", split="train", streaming=True)` |

**Why not other datasets?**
- **RGB-only datasets** (e.g., SULAND_v2, rice-rgb-demo) lack the proprioceptive state vectors (joint angles, end-effector positions) required to derive velocities and construct the full state vector for the Kairos model.
- **JSON-serialized datasets**: No verified source exists for pre-quantized discrete physical world data. The study *must* generate this via the quantization pipeline.
- **Access-gated datasets**: Clinical or industrial IoT datasets often require credentials (ADNI, HCP). These are incompatible with the CI runner and are excluded.

**Data Availability & Feasibility**:
The LIBERO datasets are open and directly downloadable via Hugging Face. The `streaming=True` option allows processing of the dataset without loading the full ~100GB+ archive into RAM, satisfying the 7GB RAM constraint. We will sample a representative subset for the training and inference runs to ensure the runtime constraints are met while maintaining statistical power.

## Methodology

### Phase 1: Data Construction & Quantization (FR-001)
1.  **Ingestion & Schema Verification**: Load continuous state vectors from the verified LIBERO parquet sources.
    - **Schema Mapping**: Explicitly map `observations.state` array indices: `state[0:3]` -> position (x, y, z), `state[3:7]` -> orientation (quaternion). **Verify these fields exist** in the loaded shard before proceeding. If not, raise a configuration error.
2.  **Velocity Derivation**: Compute velocities via finite differencing on the **continuous ground truth data** (before quantization): $v_t = (pos_{t} - pos_{t-1}) / \Delta t$. **This ensures the velocity signal is not dominated by quantization artifacts.**
3.  **Quantization**: Map continuous values (positions AND derived velocities) to discrete bins based on bit-depth ($B \in \{4, 8, 16\}$).
    - Range normalization: $x_{norm} = (x - min) / (max - min)$
    - Discretization: $x_{disc} = \lfloor x_{norm} \times (2^B - 1) \rfloor$
4.  **Noise Injection**: Apply Gaussian noise $\mathcal{N}(0, \sigma)$ where $\sigma = 0.1 \times \text{quantization\_step}$.
    - **Clamping**: Ensure noisy values remain within valid bin bounds $[0, 2^B - 1]$.
    - **Noise Floor Calculation**: Calculate the theoretical noise floor based on the **combined** noise distribution (quantization step variance + injected Gaussian variance: $\sigma^2_{total} = \sigma^2_{quant} + \sigma^2_{injected}$) for diagnostic purposes ONLY.
5.  **Degeneracy Check (FR-010)**: Detect 1-bit collapse (if $B=1$ and state space collapses to a single value).
    - **Action**: **Raise RuntimeError**, log "Invalid Data", and **exit with code 1**. Exclude this run from the N=10 aggregate statistics.
6.  **Output**: JSON-serialized state vectors.

### Phase 2: Model Adaptation & Training (FR-002, FR-003)
1.  **Architecture**: Load pre-trained Kairos Hybrid Linear Temporal Attention weights.
2.  **Modification**: Replace visual embedding layers with a **randomly initialized discrete projection layer**. This layer is trained alongside the rest of the model to learn the discrete-to-latent mapping.
3.  **Fair Baseline Protocol (Critical)**: To isolate the modality shift from the initialization confound:
    - **Arm A (Discrete)**: Train on quantized data with a randomly initialized discrete projection layer.
    - **Arm B (Continuous Baseline - Random Init)**: Train on **noisy continuous data** (same noise seed, applied to continuous values) with a **randomly initialized visual encoder** (same architecture). This ensures both arms suffer from the same "random initialization" penalty, isolating the modality shift.
    - **Arm C (Continuous Baseline - Pre-trained)**: Train on noisy continuous data with the **pre-trained visual encoder** (frozen or fine-tuned). This serves as the performance ceiling.
    - **Primary Stability Threshold**: Calculated against **Arm B** (Continuous Random Init) to isolate modality shift.
4.  **Environment**: CPU-only execution (PyTorch CPU build).
5.  **Training**:
    - Loss: Mean Squared Error (MSE) between predicted and ground-truth discrete sequences.
    - Checkpointing: Save model state every epoch to handle 6h timeout (graceful exit).
    - Duration: Target ≤ 4 hours for the sampled dataset.
6.  **Resource Profiling (FR-007)**:
    - **Mechanism**: Use `psutil` to sample CPU utilization and RAM usage every 100ms during training and inference.
    - **Aggregation**: Log **maximum** values per run into `resource_profile.json`.
    - **Latency**: Log latency per time step.

### Phase 3: Stability Analysis & Threshold Mapping (FR-004, FR-005, FR-006)
1.  **Error Decomposition**:
    - **Total MSE**: The raw Mean Squared Error between predicted and ground-truth sequences. **This is the primary metric.**
    - **Quantization Noise Floor**: The theoretical noise floor calculated from the combined noise distribution. **Reported as a separate diagnostic field `quantization_noise_floor`. NOT subtracted from Total MSE.**
    - **Model Error**: Defined as **Total MSE**. (The invalid subtraction method is removed to ensure scientific validity).
2.  **Baseline Comparison**: Compare **Total MSE** of the discrete model (Arm A) against the **Total MSE** of the continuous baseline model (Arm B, trained on same noisy data, same seed).
3.  **Stability Threshold**: Identify the bit-depth where `Total MSE (Discrete) / Total MSE (Continuous) > 1.20`.
4.  **Statistical Validation**:
    - Perform N=10 independent runs with different noise seeds.
    - **Run-Level Pairing**: For each run, pair the discrete model's mean error with the continuous baseline's mean error (trained on the same noisy data/seed).
    - **Method**: Use **Mixed-Effects Models** or **Block-Bootstrap** to account for temporal autocorrelation (errors are serially correlated). Do NOT use a simple paired t-test on timesteps.
    - Significance threshold: $p < 0.05$.
5.  **Sensitivity Analysis**: Sweep bit-depths (low, medium, high) and report error rate changes.
6.  **Resource Validation (SC-003)**:
    - Explicitly compare `resource_profile.json` metrics against constraints (RAM < 7GB, Time < 6h).
    - **Logic**: If any run exceeds limits, flag as "Fail" and write a `resource_validation.json` artifact with the specific violation. **This produces the required pass/fail result.**

## Compute Feasibility & Decision Rationale

**Decision**: **CPU-First** execution for all phases.

**Rationale**:
- **Method Suitability**: The research question focuses on *stability under resource constraints*. Using a GPU would invalidate the "edge deployment" hypothesis.
- **Tractability**:
    - **Data Processing**: Quantization and noise injection are lightweight vector operations (NumPy/Pandas) that run efficiently on CPU.
    - **Model Training**: The Kairos architecture, while complex, can be scaled down (smaller batch size, sampled dataset) to fit within 7GB RAM and 6 hours on 2 cores. The "discrete projection layer" is a simple linear transformation, adding negligible overhead.
    - **Inference**: 500-step prediction on a sampled model is feasible on CPU within the 2s/step target.
- **GPU Escape Hatch**: Not required. The study explicitly avoids GPU-dependent operations (e.g., large-scale transformer fine-tuning, diffusion models). If the CPU run fails due to time limits, the plan is to reduce the sample size (fewer episodes) or horizons, not to offload to a GPU (which would violate the constraint).

**Resource Budget**:
- **RAM**: < 7GB (streaming data, small batch size, CPU model).
- **Time**: ≤ 4 hours for training (graceful exit at 6h).
- **Disk**: < 14GB (raw parquet shards + JSON artifacts).

## Statistical Rigor & Limitations

- **Multiple Comparisons**: When comparing 3 bit-depths against the baseline, a Bonferroni correction will be applied to the significance threshold ($\alpha / 3$) to control family-wise error rate.
- **Power Analysis**: N=10 runs is targeted to achieve power ≥ 0.8 for detecting a medium effect size (Cohen's d ≈ 0.5) in error accumulation rates.
- **Causal Inference**: This is an observational study on simulated data. Claims will be framed as "associational" or "relative degradation" rather than causal effects of quantization on physical stability.
- **Collinearity**: Position and velocity are definitionally related (velocity is the derivative of position). The plan acknowledges this collinearity and reports it descriptively; the model is not claimed to learn "independent" effects of velocity.
- **Measurement Validity**: The "quantization noise" is a simulated proxy for sensor noise. The study acknowledges this limitation and frames results as a lower-bound estimate of stability in real-world systems.
- **Temporal Autocorrelation**: The use of Mixed-Effects Models or Block-Bootstrap accounts for the serial correlation of errors in autoregressive predictions, avoiding the inflated Type I error rate of a standard paired t-test.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **1-bit Collapse** | Invalid data generation. | Explicit check in `data/validator.py` (FR-010) to halt, log "Invalid Data", and exclude from aggregate. |
| **Training Timeout** | Incomplete results. | Checkpointing every epoch; graceful exit with partial results; reduce sample size if needed. |
| **RAM Overflow** | Job failure. | Streaming data loading; batch size reduction; monitoring via `resource_profile.json`. |
| **Statistical Insignificance** | No clear threshold found. | Report the "non-significant" finding as a valid result (stability holds at all tested resolutions); increase N if feasible. |
| **Invalid Baseline** | Flawed comparison. | Re-train continuous baseline per-run with the same seed and noisy data to ensure valid pairing. |
| **Schema Mismatch** | Data ingestion failure. | Explicit schema verification step in Phase 1 Step 1. |