# Research: DreamX-Lite: Geometric Priors for 3D Consistency

## 1. Problem Statement & Hypothesis

**Problem**: Learned positional encodings (E-PRoPE) in DiT backbones may introduce instability or ambiguity in 3D-consistent video generation. It is unknown if deterministic geometric constraints (fixed 4x4 camera matrices) are sufficient to replace these learned representations.

**Hypothesis**: Replacing the learned E-PRoPE module with a fixed, non-trainable linear projection of 4x4 camera pose matrices will yield comparable or superior **robustness** (measured by SfM convergence rate) and **scale consistency** (measured by Scale Drift) while reducing parameter count and inference complexity. The primary claim is not about 'superior 3D consistency' in a trivial sense (which is guaranteed by the rendering engine), but about the **stability** of the generation process under the deterministic prior.

**Null Hypotheses**:
- H0 (Convergence): There is no significant difference in SfM convergence rates between the Baseline and DreamX-Lite models (McNemar's test).
- H0 (Error): There is no significant difference in the median MAE of recovered trajectories (after Procrustes alignment) between the Baseline and DreamX-Lite models (Wilcoxon signed-rank test), conditional on convergence.

**Non-Triviality Clarification**: The 'Ground Truth' for MAE is the rendering engine's metadata (independent of the model's internal state) and the 'Input' is the camera prompt. The metric measures the deviation of the *generated video's* implied geometry (recovered via SfM) from this independent ground truth, not the identity of the input. A 'Non-Triviality Check' will be performed to verify that the generated video differs from a direct render of the input geometry, ensuring the metric measures *generative deviation* rather than *input identity*.

## 2. Dataset Strategy

The study relies on two primary data sources. The **DreamX-World subset** (Unreal Engine renders) provides ground-truth camera extrinsics and video frames. The **ScanNet** dataset is used for additional geometric priors or validation if required by the specific implementation of the SfM module.

| Dataset | Description | Source URL (Verified) | Usage in Plan |
|:--- |:--- |:--- |:--- |
| **DreamX-World Subset** | Unreal Engine renders with ground-truth 4x4 camera extrinsics. | *NO verified source found* (See note below) | Primary evaluation data. Used for generating rollouts and providing ground-truth trajectories. |
| **ScanNet** | 3D scene scans with camera poses. | `<br>`<br>` | Secondary validation or SfM initialization if DreamX-World subset lacks sufficient diversity. |

**Note on Data Availability**: The spec assumes the DreamX-World subset is available. The verified datasets block indicates **NO verified source found** for "DreamX-World subset" or "CPU-tractable".
*Action Plan (Data Fallback Protocol)*: The implementation will first attempt to locate the DreamX-World subset via a standard HuggingFace loader (e.g., `datasets.load_dataset("dreamx-world/subset")`). If this fails or requires credentials, the plan will **abort** the primary claim generation phase and report a "Data Unavailability" status, as per the "Data availability" rules. No synthetic data will be generated to substitute for the missing real dataset. If a substitute is absolutely necessary for the statistical framework to be demonstrated, a small, open, verified subset of ScanNet (using the URLs above) will be used for the *metric calculation logic* verification only, but the primary claim will be marked as "Pending Data Access".

**Model Availability**: The plan assumes the existence of a 'DreamX-World 1.0 DiT' pre-trained model. **No source URL, repository link, or accession ID is provided for this model.** If the model weights are not publicly available or require proprietary access, the entire architectural ablation (FR-001) and comparative study are infeasible. The plan must cite a specific, accessible source for the baseline model weights or acknowledge that the study cannot proceed without them.

**Feasibility Check**:
- **Size**: The full DreamX-World dataset is expected to be substantial in size. The plan will stream data or sample a fixed number of trajectories (N=50) to fit the CI runner constraints.
- **Access**: If the dataset requires a token, the pipeline will fail at the download stage. The plan assumes an open access variant exists or the user provides the token via CI secrets.

## 3. Methodology & Statistical Rigor

### 3.1. Architectural Ablation (FR-001)
- **Baseline**: Load pre-trained DreamX-World 1.0 DiT.
- **DreamX-Lite**: Replace `E-PRoPE` layer with `nn.Linear(16, embedding_dim)` (flattened 4x4 matrix). Set `requires_grad=False`.
- **Validation**: Verify parameter count reduction and deterministic output for identical inputs.
- **Identical Constraints**: To isolate the geometric effect from resolution/quantization artifacts, *both* Baseline and Lite variants will use the **exact same** resolution (256x256) and quantization (8-bit if needed). Any performance gap is attributable to the geometric prior, not the resolution artifact.

### 3.2. Video Generation & SfM Recovery (FR-002, FR-003, FR-004)
- **Rollouts**: Generate short-duration videos for 50 distinct camera prompts (identical for both models).
- **SfM**: Use a frozen `COLMAP` instance to recover camera poses from video frames.
- **Metric Independence**: The metric script (`code/pipeline/evaluate.py`) accepts **only** video frames (numpy) and ground-truth extrinsics. It contains **no** imports of `dreamx` internal states (FR-007).
- **Procrustes Alignment**: Before computing MAE, the recovered trajectory is aligned to the ground-truth trajectory via **Generalized Procrustes Analysis (GPA)** to remove scale and rotation ambiguities. This ensures the MAE measures pose error, not coordinate system mismatch. **Explicit Normalization**: MAE is computed on *aligned* trajectories to remove scale/rotation ambiguity.
- **Scale Drift**: Defined as the ratio of the mean depth of the *aligned* recovered trajectory to the mean depth of the ground-truth trajectory, or the residual scale factor from GPA.
- **Failure Handling**:
 - If SfM fails to converge, record `convergence=false` and `sfm_failure_reason` (e.g., "insufficient features").
 - Set `mae_position` and `mae_rotation` to `null` (not -1.0) to avoid contaminating the continuous error distribution.
 - If SfM fails but a depth-consistency metric is available, mark `sfm_status` as 'censored'.

### 3.3. Statistical Analysis (FR-005, FR-006) - Hurdle Model
To address survivorship bias and the non-Gaussian nature of errors, a **Hurdle Model** is employed:
1. **Convergence (Binary)**: McNemar's test on the binary `convergence` flags (Baseline vs. Lite).
2. **Censoring (Binary)**: Analysis of the 'censored' rate (SfM failed but depth available) to quantify the proportion of 'hard' cases.
3. **Error (Continuous)**: Wilcoxon signed-rank test on MAE scores (position and rotation) **only** for trajectories where `convergence=true`. **No Sentinels**: Sentinel values are excluded from the Wilcoxon test.
4. **Sensitivity**: Sweep thresholds {0.01, 0.05, 0.1} MAE. Report success rates for both models at each level.
5. **Sufficiency Ratio**: Calculate the 'Information-Theoretic Sufficiency Ratio' = (DreamX-Lite Success Rate) / (Baseline Success Rate) across the thresholds.

### 3.4. Compute Feasibility (CPU-First)
- **Model**: DiT inference on CPU. If the full model is too large (>7GB RAM), the plan will use a quantized (8-bit) version or a smaller subset of layers, provided the *geometric ablation* remains valid.
- **SfM**: COLMAP on CPU is computationally expensive. The plan will limit the number of frames per video (e.g., 30 frames) and use a downscaled resolution (e.g., 256x256) to ensure the 6-hour CI limit is met.
- **GPU Escape Hatch**: If the DiT backbone *strictly* requires CUDA (e.g., specific attention kernels not available on CPU), the plan will trigger the "GPU escape hatch" to run the generation phase on a Kaggle free GPU (16GB VRAM), while keeping the SfM and analysis on CPU. However, the primary design is CPU-first.
- **Limitation Note**: Results are valid for the 'low-resolution/quantized' regime defined in the compute constraints. The comparison is strictly relative (Lite vs. Baseline under identical constraints).