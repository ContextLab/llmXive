# Research: Audio Interaction Model Extension (Robustness to Compression)

## 1. Research Question
How does the robustness of acoustic feature detection (specifically high-frequency transients and low-amplitude events) degrade under varying levels of model compression (quantization and pruning) when deployed on resource-constrained edge devices?

## 2. Background & Motivation
Edge deployment of audio-language models requires balancing model size with inference speed and memory usage. However, aggressive compression (e.g., INT4 quantization) may disproportionately degrade the detection of subtle cues (e.g., glass breaking, whispers) which are critical for safety-critical applications. This study systematically evaluates this trade-off to identify the "breaking point" where detection sensitivity collapses.

## 3. Dataset Strategy

### 3.1 Primary Dataset: ESC-50 & UrbanSound8K
**Source**: ESC-50 (Environmental Sound Classification) & UrbanSound8K  
**Verified URLs**: 
- ESC-50: `https://huggingface.co/datasets/ashraq/esc50`
- UrbanSound8K: `https://huggingface.co/datasets/sanchit-gandhi/urban-sound-8k` (Verified via HuggingFace Hub)

**Rationale**: 
- **ESC-50**: Contains [deferred] labeled environmental sound clips (50 classes) with 5-second duration.
- **UrbanSound8K**: Contains [deferred] labeled urban sound clips (10 classes) with higher fidelity and specific high-frequency classes (e.g., "siren", "drilling") that complement ESC-50's "glass breaking".
- **Combined Strategy**: Using both datasets ensures sufficient sample size for the "SubtleCue" testbed and provides a robust "Control Set" of non-subtle classes.

**Filtering Strategy (FR-002) - Composite Feature Score**:
- **Target Classes (Subtle)**: "glass breaking", "alarm", "whisper" (ESC-50); "siren", "drilling" (UrbanSound8K).
- **Control Classes (Non-Subtle)**: "engine", "machinery" (ESC-50/UrbanSound8K). *Note: 'air_conditioner' and 'car_horn' are excluded from Control as they may contain high-frequency transients.*
- **Criteria**: A sample is "Subtle" if `Score = (Centroid > 8k) OR (Flux > thresh) OR (SNR < -40)`.
- **Control Set Verification**: The Control Set is explicitly selected to have `Score < 0.1` (low frequency, low flux, high SNR) to ensure no overlap with the Subtle distribution. We verify this by computing the metric on a sample of the Control classes before inclusion. This prevents circular validation and ensures the AUC measures detection against natural background noise.
- **Implementation**: The `data/subtle_cue_builder.py` script streams both datasets, computes spectral features, assigns labels (Subtle/Control), and splits the data.

### 3.2 Data Availability & Feasibility
- **Access**: Both datasets are open and directly downloadable via `datasets.load_dataset`.
- **Feasibility**: Streaming ensures the full dataset is never fully loaded into RAM, adhering to the 7GB limit.
- **No Gated Data**: No access-gated datasets (e.g., ADNI, HCP) are used.

### 3.3 Data Partitioning & Calibration (Critical)
To prevent data leakage:
1. **Split First**: Raw data is split into [deferred] (Train/Calibration) and [deferred] (Test) *before* any filtering.
2. **Calibrate**: Quantization parameters (activation scales) are derived *only* from a [deferred] random subset of the **Train** split (Calibration Set), NOT the Test split.
3. **Filter Test**: The [deferred] Test split is then filtered into "Subtle" and "Control" subsets.
4. **Evaluate**: Inference is performed *only* on the filtered Test subsets.
This ensures the calibration data is independent of the evaluation testbed.

## 4. Model Strategy

### 4.1 Teacher Model: Wav2Vec2-Base (Substitute)
**Source**: `facebook/wav2vec2-base-960h` (Hugging Face)  
**Rationale**: The spec requires "DeSTA2.5-Audio", which does not exist in public repositories. **facebook/wav2vec2-base-960h** is a verified, CPU-loadable pre-trained audio-language model suitable for feature extraction.
**Constraint**: Must be loadable on CPU. No CUDA-specific kernels are used.

### 4.2 Compression Strategy (FR-001)
- **Quantization**: 
  - **FP32**: Baseline.
  - **INT8**: Post-training static quantization (requires calibration).
  - **INT4**: **Dynamic Quantization** (`torch.nn.quantized.dynamic`) is used for INT4 on CPU. Static INT4 requires external backends (XNNPACK) or Quantization-Aware Training (QAT) which are outside the scope of this CPU-first pipeline. Dynamic quantization is natively supported and CPU-feasible.
- **Pruning**: Structured pruning of feed-forward layers and attention heads using `torch.nn.utils.prune`.
- **Knowledge Distillation**: Student models trained to mimic teacher logits (soft targets) to recover accuracy lost during compression.
- **CPU Compatibility**: All quantization and inference steps are performed on CPU. No 8-bit CUDA libraries (e.g., `bitsandbytes`) are used.

### 4.3 Compute Feasibility
- **CPU-First**: Quantization and inference are computationally intensive but feasible on 2-core CPU for small datasets and models.
- **GPU Escape Hatch**: If the teacher model is too large for CPU loading, the plan will scale down to a smaller architecture (e.g., Wav2Vec2-small) rather than fabricating a CPU approximation. No GPU offload is planned for this specific feature as the spec emphasizes CPU edge constraints.

## 5. Statistical Rigor

### 5.1 Metric Calculation (FR-003)
- **AUC-ROC**: Calculated using `sklearn.metrics.roc_auc_score` on final logits vs. external labels (Subtle vs. Control).
- **Binary Discrimination**: The testbed is a binary classification task: **Subtle** (High Score) vs. **Control** (Low Score). The AUC measures the model's ability to distinguish these two groups, avoiding tautology.

### 5.2 Sensitivity Analysis (FR-006)
- **Threshold Sweep**: Decision thresholds swept over {0.01, 0.05, 0.1}.
- **Metrics**: False Positive Rate (FPR) and False Negative Rate (FNR) reported for each threshold.
- **Rationale**: Validates the stability of the "breaking point" detection.

### 5.3 Ablation Study (FR-007) - Factorial Design
- **Design**: A **2x2 Factorial Design** is used:
  - Factor A: Compression Level (FP32, INT8, INT4)
  - Factor B: Component Modification (None, Freeze Attention, Prune FFN)
- **Control**: Each architectural modification is tested at **FIXED** quantization levels (e.g., INT8-Freeze, INT8-Prune) to isolate the effect of the component from the compression intensity.
- **Normalization**: Performance drops are reported relative to the percentage of parameters/FLOPs removed (e.g., "AUC drop per [deferred] parameter reduction") to ensure fair comparison between attention freezing and FFN pruning.
- **Constraint**: No causal claims. Results reported as associational correlations between component modification and AUC drop.
- **Collinearity**: If components are correlated, joint effects are reported descriptively.

### 5.4 Power Analysis & Sample Size
- **Requirement**: To detect a [deferred] relative AUC drop with 80% power (alpha=0.05), a minimum of [deferred] samples per class is required (calculated via `statsmodels.stats.power`).
- **Strategy**: If the initial ESC-50 subset is underpowered, samples are aggregated from UrbanSound8K to meet the minimum threshold. If the combined dataset is still underpowered, the power limitation is explicitly reported, and confidence intervals are widened.
- **No Fabrication**: No synthetic data is generated to inflate sample size.

## 6. Decision/Rationale

| Decision | Rationale |
|----------|-----------|
| **Wav2Vec2-Base over DeSTA2.5** | DeSTA2.5 does not exist; Wav2Vec2-base is verified, CPU-loadable, and suitable for audio features. |
| **ESC-50 + UrbanSound8K** | Combined datasets provide sufficient samples for both "Subtle" and "Control" classes. |
| **Composite Scoring** | More robust than binary thresholds; captures transient and low-amplitude features better. |
| **Split -> Calibrate -> Filter** | Prevents data leakage between calibration and evaluation sets. |
| **Dynamic Quantization for INT4** | Native CPU support in PyTorch; avoids need for external backends or QAT. |
| **Factorial Ablation** | Isolates architectural effects from compression intensity; normalization ensures fair comparison. |
| **Associational Claims** | Spec prohibits causal claims for architectural ablations; ensures methodological rigor. |

## 7. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Model too large for CPU** | High (OOM/Crash) | Use Wav2Vec2-base; if still too large, use Wav2Vec2-small. |
| **Insufficient subtle cues** | Medium (Low power) | Aggregate samples from UrbanSound8K; report power limitation if still insufficient. |
| **Quantization instability** | Medium (NaN/Inf) | Use dynamic quantization; add gradient clipping; catch errors gracefully. |
| **CI Time Limit Exceeded** | High (Job failure) | Limit dataset size to a manageable subset if the full set is too slow; log time per sample. |
