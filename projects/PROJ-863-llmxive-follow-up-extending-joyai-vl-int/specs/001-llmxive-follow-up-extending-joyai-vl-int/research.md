# Research: llmXive Follow-up: Extending "JoyAI-VL-Interaction"

## Research Question
Do the internal hidden states and attention maps of the JoyAI-VL-Interaction model contain a unique predictive signal ("latent intuition") for high-load intervention events (critical vs. silence) that is distinct from, and potentially superior to, simple visual heuristics, while remaining computationally feasible for CPU-only edge deployment?

## Methodology Overview

The research follows a four-stage pipeline designed to eliminate circularity, respect hardware constraints, and ensure statistical validity:
1.  **Synthetic Data Generation**: Create a dataset of 50+ hours of simulated video with ground truth labels derived **exclusively** from visual events (e.g., object detection of falls, alarms). **Crucially, temporal jitter and noise are injected** to prevent the model from simply memorizing deterministic rules.
2.  **Feature Extraction**: Extract internal states (hidden embeddings, attention maps) from the JoyAI-VL-Interaction model for each frame, explicitly excluding final logits.
3.  **Visual Baseline Implementation**: Implement a **Noisy Rule-Based Visual Detector** that uses the same visual features (with identical noise constraints) as the ground truth labeling. This serves as the baseline for SC-005.
4.  **Scheduler Training & Evaluation**: Train a Transformer classifier with a moderate parameter count on CPU. Evaluate using AUC-ROC, Cohen's Kappa, and Nested Model Comparison (Likelihood Ratio Test) to verify unique predictive signal.

## Dataset Strategy

### Primary Dataset: Synthetic Video Stream
- **Source**: Generated internally via `data_synthesis/generator.py`.
- **Rationale**: No public dataset exists that pairs "latent intuition" labels with specific VLM internal states for security/elder care scenarios. Public datasets (e.g., MMVP, Nemotron) are for general VQA/captioning and do not contain the specific "intervention" ground truth or the required internal state alignment.
- **Ground Truth Logic**: Labels ("critical" vs. "silence") are assigned based on deterministic visual rules (e.g., bounding box velocity > threshold for "fall").
- **Noise Injection**: To address the risk of deterministic memorization, the generator introduces **temporal jitter** (randomizing event onset by ±2 frames) and **label noise** (flipping [deferred] of labels randomly). This ensures the VLM must learn a robust signal, not just a rule.
- **Verification**: An execution log (`data/execution_log.jsonl`) will be generated to prove zero VLM API calls during labeling (FR-001.1).

### Verified Datasets (Reference Only)
While the primary dataset is synthetic, the following verified datasets are available for potential baseline comparisons or pre-training if needed (though not used for the core hypothesis test):
- **MMVP**: https://huggingface.co/datasets/MMVP/MMVP_VLM/resolve/main/Questions.csv
- **Nemotron VLM**: https://huggingface.co/datasets/nvidia/Llama-Nemotron-VLM-Dataset-v1/resolve/main/captioning_1.jsonl
- **Nemotron Activity**: https://huggingface.co/datasets/nvidia/Nemotron-VLM-Dataset-v2/resolve/main/activity_net_1/activity_net_1.jsonl

*Note: The "VL-Interaction" dataset mentioned in the spec has NO verified source. It is not used.*

## Statistical Rigor & Methodological Considerations

### 1. Dataset-Variable Fit
- **Requirement**: The dataset must contain frames labeled "critical" (falls, alarms) and "silence" (calm).
- **Verification**: The synthetic generator will explicitly inject these events with known timestamps. The labeler will verify presence via object detection confidence scores.
- **Risk Mitigation**: If the synthetic generator fails to produce diverse "critical" events, the study will be paused, and the generator logic audited.

### 2. Statistical Significance & Metrics
- **Metric**: **AUC-ROC** (Area Under the Receiver Operating Characteristic Curve) and **Cohen's Kappa** are used for binary classification. Spearman correlation is **rejected** as it is invalid for binary data.
- **Baseline**: Random baseline (AUC=0.5).
- **Threshold**: p-value < 0.05 (SC-001) established via **Permutation Testing** (shuffling labels a sufficient number of times to generate a null distribution).
- **Correction**: Since multiple metrics (Interruption Reduction, Safety Recall, AUC, Kappa) are reported, a Bonferroni correction will be applied to the p-values if multiple hypothesis tests are run on the same dataset split.

### 3. Unique Predictive Signal (Nested Model Comparison)
- **Issue**: How to prove internal states add value beyond visual features?
- **Method**: **Nested Model Comparison** (Likelihood Ratio Test).
  - **Model A (Visual Only)**: Trained on visual features (e.g., object detection confidence, velocity).
  - **Model B (Visual + Internal)**: Trained on visual features + internal state embeddings.
  - **Test**: Compare the log-likelihoods. If Model B is significantly better (p < 0.05), the internal states provide unique signal.
- **Correction**: The previous plan's suggestion of "partial correlation conditioned on ground truth" is methodologically invalid (collider bias). The correct approach is comparing predictive performance of nested models.

### 4. Measurement Validity
- **Proxy Validity**: "Critical" is defined as visual events (falls). We acknowledge this is a proxy for "cognitive load" or "need for intervention." This limitation is explicitly stated in the paper.
- **Instrument Validity**: The "15M Transformer" is a standard architecture. Its validity is established by its ability to converge on the task.

### 5. Baseline Comparison (SC-005)
- **Requirement**: Compare scheduler F1 to a "deterministic rule-based visual detector".
- **Clarification**: The baseline is a **Noisy Rule-Based Detector**. It uses the *same* noisy visual rules (with jitter and label noise) as the ground truth generation.
- **Hypothesis**: If the VLM's internal states capture signal *despite* the noise that degrades the rule-based detector, the scheduler's F1 will be significantly higher than the baseline's F1. This tests "latent intuition" (signal in noise) rather than simple visual recognition.

### 6. Power Analysis & Sample Size
- **Requirement**: Ensure sufficient statistical power to detect the effect size.
- **Analysis**: For a binary classification task (AUC-ROC), a medium effect size (Cohen's h = 0.5) requires approximately **384 samples** per class for 80% power at α=0.05.
- **Plan**: The synthetic generator will produce a minimum of **[deferred] frames** (balanced 50/50) to ensure robust power, even with noise injection. This is well within the 50-hour video target and CPU constraints.

## Compute Feasibility Plan

### Hardware Constraints
- **Runner**: GitHub Actions c6i.large (2 vCPU, 7GB RAM, No GPU).
- **Time Limit**: 6 hours.

### Mitigation Strategies
1.  **Streaming Feature Extraction**: The `feature_extraction/streaming.py` module will process videos in chunks of frames. This ensures RAM usage stays < 6GB even for long videos.
2.  **CPU-Only Model**: The 15M Transformer will be trained using `torch` in CPU mode. No CUDA operations.
3.  **Data Subsetting**: If the 50-hour target exceeds the 6-hour runtime limit, the dataset size will be dynamically scaled down to a "feasible subset" (e.g., 10 hours) while maintaining class balance. The report will explicitly state the actual duration processed.
4.  **Library Pins**: `torch` will be pinned to a version with stable CPU wheels. `transformers` will be used with `device="cpu"`.

## Decision Log

| Decision | Rationale | Alternative Rejected |
| :--- | :--- | :--- |
| **Synthetic Data with Noise** | Prevents memorization of deterministic rules; tests robustness of internal states. | Deterministic synthetic data would allow a simple rule-based detector to achieve perfect F1, invalidating the hypothesis test. |
| **Visual-Only Labeling** | Ensures ground truth is independent of the model's output (Constitution VI). | Using VLM outputs for labels would create circular reasoning. |
| **15M Parameter Model** | Fits within 7GB RAM and 6h runtime on CPU. | Larger models (e.g., 100M+) would likely OOM or exceed time limits. |
| **Streaming Batching** | Prevents OOM on long video segments. | Loading full video into memory is impossible for >1 hour of footage. |
| **AUC-ROC & Kappa** | Standard, valid metrics for binary classification. | Spearman correlation is invalid for binary data. |
| **Nested Model Comparison** | Statistically rigorous method to prove unique signal. | Partial correlation conditioned on Y is invalid (collider bias). |
| **Noisy Baseline** | Tests if internal states capture signal *in the presence of noise*. | Perfect baseline comparison is trivial and uninformative. |