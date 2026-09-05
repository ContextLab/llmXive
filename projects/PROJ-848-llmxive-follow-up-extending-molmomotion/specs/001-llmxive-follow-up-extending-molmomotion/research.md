# Research: llmXive follow-up: extending "MolmoMotion: Forecasting Point Trajectories in 3D with Language Instru"

## Research Question

Does providing structured kinematic parameters (velocity, duration) as input instructions significantly reduce the Average Trajectory Error (ATE) of a lightweight, CPU-constrained 3D trajectory forecasting model compared to coarse natural language instructions, when controlling for the same ground-truth trajectory?

## Dataset Strategy

The study utilizes the **MolmoMotion-1M** dataset, specifically the **processed trajectory files** which contain pre-extracted 3D point clouds and kinematic metadata.

| Dataset Component | Source / URL | Verification Status | Usage in Plan |
| :--- | :--- | :--- | :--- |
| **MolmoMotion-1M (Processed Trajectories)** | `https://huggingface.co/datasets/junhalee/molmo-motion-1m/resolve/main/processed_trajectories.parquet` | Verified (Hugging Face) | Source of 3D points, velocity vectors, and duration. |
| **MolmoMotion-1M (Metadata Index)** | `https://huggingface.co/datasets/junhalee/molmo-motion-1m/resolve/main/metadata.jsonl` | Verified (Hugging Face) | Index for subsampling and linking. |

**Dataset Fit & Variable Verification**:
- **Required Variables**: Ground-truth 3D point sequences, velocity vectors, duration.
- **Verification**: The verified `processed_trajectories.parquet` file in the MolmoMotion-1M dataset explicitly contains columns for `points` (3D coordinates), `velocity_vector` (list of 3 floats), and `duration` (scalar). This eliminates the need for any 3D reconstruction or optical flow estimation from raw video.
- **Gap Analysis**: No gaps identified. The dataset provides the raw material for both instruction modalities and the ground truth for evaluation.

**Data Acquisition Strategy**:
1.  **Download**: Use `datasets.load_dataset(..., streaming=True)` to fetch the `processed_trajectories.parquet` and `metadata.jsonl` from the verified Hugging Face URL.
2.  **Streaming**: Since the full dataset exceeds the 7GB RAM limit, the pipeline will stream the parquet file.
3.  **Subsampling (FR-001)**: A deterministic random sample of [deferred] instances will be selected using a fixed seed (e.g., `seed=42`). This ensures reproducibility (Constitution I) and fits the memory budget.
4.  **Storage**: Subsampled data will be stored in a memory-efficient format (e.g., `parquet` or `jsonl`) in `data/processed/`.

**Feasibility Note**: The dataset is publicly available via Hugging Face, satisfying the "open, directly-downloadable" requirement. No access gates or credentials are required. The use of processed files ensures that the required 3D kinematic data is immediately available without computationally expensive video processing.

## Model & Methodology

### Architecture: Dual-Head Linear Baseline
- **Type**: Two parallel, non-autoregressive linear projection heads.
- **Rationale**: To isolate the effect of instruction precision without requiring a heavy text encoder (which would violate CPU constraints), the model uses two distinct heads:
    1.  **Structured Head**: Accepts a 4D input vector `[vx, vy, vz, duration]`.
    2.  **NL Head**: Accepts a fixed-length, deterministic **Bag-of-Words (BoW)** vector (32-dimensional) derived from the NL instruction.
- **Input Construction**: For both heads, the input is concatenated with **time-step indices** (e.g., `t=0, 1, ..., T`) to allow the linear model to learn the temporal evolution of the trajectory. This addresses the temporal limitation of linear models by explicitly providing time as a feature.
- **Output**: A sequence of 3D points `[x, y, z]` for the entire trajectory horizon.
- **Implementation**: `torch.nn.Linear` layers.
- **CPU Feasibility**: Linear projections are highly optimized on CPU. With a subsampled dataset and small hidden dimensions, this will easily run within the 7GB RAM and 6h limits.

### Instruction Synthesis (FR-002)
1.  **Coarse Natural Language (NL)**: Generated via a rule-based parser on metadata that **discards precise values**.
    - *Example*: Maps `velocity_magnitude=2.4` to `"fast"`, `direction=0.5` to `"right"`. The output is a string like `"move fast right"`.
    - *Lossiness*: The exact numerical values are lost, forcing the NL Head to approximate the trajectory based on semantic hints.
    - *Embedding*: The string is converted to a 32-dim BoW vector using a fixed vocabulary hash.
2.  **Structured Kinematic**: Direct serialization of the exact metadata.
    - *Example*: `"vel=[2.4, 0.1, -0.5], dur=2.0"`.
    - *Precision*: The input contains the exact parameters defining the ground-truth dynamics.

### Evaluation Metrics
- **Average Trajectory Error (ATE)** (FR-004): Mean Euclidean distance between predicted 3D points and ground truth across the sequence.
- **Instruction Adherence Score**: (Constitution VII) Cosine similarity between the predicted trajectory's primary direction vector and the instruction's intended direction vector.
    - *Structured*: Direction derived from the velocity vector.
    - *NL*: Direction derived from the semantic mapping of the NL string.
- **Statistical Test**: Paired t-test (FR-005).
  - **Null Hypothesis ($H_0$)**: Mean ATE(NL) == Mean ATE(Structured).
  - **Alternative Hypothesis ($H_1$)**: Mean ATE(NL) > Mean ATE(Structured).
  - **Significance Level**: $\alpha = 0.05$.
  - **Power Analysis**: Sample size [deferred] is chosen to balance computational cost with sufficient power to detect a [deferred] effect size. The plan acknowledges the limitation if the sample is too small.

### Statistical Rigor & Assumptions
- **Multiple Comparisons**: Only one primary comparison (NL vs. Structured) is performed per trajectory instance. No family-wise error correction is needed as there is a single hypothesis test.
- **Causal Inference**: This is a **Controlled Experiment** on the model's sensitivity to input precision. Since the ground truth and model weights are held constant and only the input instruction modality varies, the paired t-test validly tests the **causal effect** of 'Instruction Type' on 'Prediction Error' within the scope of this specific model architecture. Claims are framed as causal regarding the model's behavior.
- **Collinearity**: The NL and Structured instructions are derived from the *same* ground truth but represent different *levels of information*. The NL input is a lossy summary, while the Structured input is precise. The paired t-test handles the dependency correctly.
- **Validity**: The linear model is a valid approximation for the "reduced capacity" scenario. It lacks the full attention mechanism, making it a strict lower-bound on capacity. The inclusion of time-step indices allows the linear model to learn a static mapping over time, serving as a baseline for temporal dynamics.
- **Experimental Design Note**: To prevent the model from trivially ignoring the NL head, the **NL Head** is trained *only* on NL inputs (BoW vectors), and the **Structured Head** *only* on structured inputs (kinematic vectors). The comparison is between two separate model runs (or two separate heads trained on disjoint data), ensuring the NL head must actually learn to map semantic tokens to motion without access to the kinematic vector. This isolates the capability of the NL modality.

### Scientific Soundness & Information Bottleneck
- **Circular Validation Mitigation**: The 'Structured' input is treated as a 'Ground Truth Proxy' (ideal condition), while the 'NL' input is the 'Ambiguous Condition'. The comparison measures the *information loss* incurred by the NL parser. The plan explicitly states that the Structured Head's low error is expected (due to direct parameter access) and serves as the baseline for quantifying the degradation in the NL Head.
- **Information Loss**: The experiment is explicitly framed as a test of 'Information Bottleneck' performance: how much predictive power is lost when compressing precise kinematic data into coarse semantic tokens. The parser's information loss is the variable being tested.

## Compute Feasibility & Escape Hatch

- **Primary Strategy (CPU)**: The entire pipeline (data loading, linear model inference, metric calculation) is designed to run on the GitHub Actions free tier (a standard CPU allocation with 7GB RAM).
  - **Data**: Streaming and subsampling ensure RAM usage < 7GB.
  - **Model**: Linear projection is computationally cheap on CPU.
  - **Time**: Subsampling to [deferred] instances ensures the job completes within 6 hours.
- **GPU Escape Hatch**: Not required. The linear model and subsampled dataset are explicitly chosen to be CPU-tractable. No transformer fine-tuning or large model inference is planned. If the subsample size is increased significantly in the future, the plan would require re-evaluation, but for the current spec, CPU is sufficient.

## Risk Mitigation

1.  **Dataset Corruption**: Retry logic (3 attempts) with clear error codes. Checksum verification upon download.
2.  **Ambiguous Metadata**: Log warnings and skip instances where kinematic parameters cannot be derived (excluded from paired test).
3.  **NaN/Inf in Prediction**: Runtime check in inference loop. Flagged instances are excluded from the final statistical analysis to prevent skewing the t-test.
4.  **OOM Errors**: Streaming implementation and strict subsampling limits.

## References

1.  MolmoMotion Dataset (Processed): `https://huggingface.co/datasets/junhalee/molmo-motion-1m` (Verified)
2.  MolmoMotion Data Archive: `https://huggingface.co/datasets/junhalee/molmo-motion-1m-xperience-videos` (Verified)