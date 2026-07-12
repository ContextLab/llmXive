# Research: LLMXive Follow-up: Latent Anomaly Detection for Audio Jailbreaks

## Research Question
Do statistical anomalies in the latent embedding space of pre-trained audio encoders correlate with cross-modal jailbreak attempts, enabling lightweight, rule-based detection without requiring model retraining or GPU resources?

## Background & Motivation
Cross-modal jailbreaking (e.g., adversarial audio prompts) is an emerging threat to Large Audio Language Models (LALMs). Traditional defenses often require fine-tuning or heavy model overhead, which is incompatible with edge deployment. This research hypothesizes that jailbreak samples, due to their adversarial nature, will occupy distinct regions in the latent space of frozen, benign-trained encoders (like Whisper), manifesting as statistical outliers.

## Dataset Strategy

### Verified Datasets
The following datasets are the **only** sources used for this research, as verified by the spec's "Verified datasets" block. **Note**: Text-only datasets are excluded from audio embedding extraction.

| Dataset Name | Source URL | Content | Relevance |
| :--- | :--- | :--- | :--- |
| **LALM: Adversarial Audio Subset** (If available) | *Deferred to verified URL in spec* | Audio samples with explicit "jailbreak" labels (e.g., "ignore instructions"). | **Primary Source** for audio-jailbreak pairs. |
| **LALM: Benign TTS** (e.g., CosyVoice Instruct) | https://huggingface.co/datasets/LALM-emotional-damage/cosyvoice-instruct/resolve/main/data/train-00000-of-00005.parquet | Instruction-following audio samples. | **Primary Source** for benign/instructive audio baseline. |
| **Random Noise** (Synthetic) | N/A | Synthetic Gaussian noise vectors matching embedding dimension. | **Control Baseline** to test if jailbreaks are outliers relative to a general audio manifold. |

### Dataset-Variable Fit Analysis
- **Required Variables**: `audio_path` (or raw audio bytes), `label` (jailbreak vs. benign), `prompt_text`.
- **Fit Verification**:
  - **Critical Check**: We must verify that the `label` field in these datasets was **not** derived using the same latent space statistics we intend to test (e.g., if the original paper labeled "jailbreak" based on a specific encoder's outlier score).
  - **Label Mapping**: If a dataset contains ambiguous tags (e.g., "emotional damage"), we will map them to "jailbreak" **only** if the definition aligns with adversarial intent (e.g., presence of "ignore previous instructions"). If the label is purely emotional and not adversarial, that dataset will be **excluded** from the jailbreak class and used only for benign baseline construction.
  - **Fallback**: If no verified dataset contains explicit "audio jailbreak" labels, the study will proceed with a "Benign vs. Random Noise" experiment to test the sensitivity of the anomaly detector, while explicitly acknowledging the limitation in the final report.
- **Text-Only Exclusion**: The "MixSub (Text-Only)" dataset is excluded from the audio embedding pipeline as it lacks the required audio modality.

## Methodology

### 1. Embedding Extraction
- **Encoder**: Distil-Whisper Base (Output dimension: 768).
- **Reasoning**: Lightweight, frozen, proven on CPU, and widely used as a feature extractor.
- **Process**:
  1.  Load audio, resample to 16kHz.
  2.  Pass through `model.get_encoder()` with `return_dict=True`, `output_hidden_states=False`.
  3.  Extract the last hidden state mean-pool.
  4.  **Constraint**: Run entirely on CPU (`device="cpu"`). No `torch.cuda`.

### 2. Anomaly Scoring (Mahalanobis Distance)
- **Hypothesis**: Benign samples cluster tightly; jailbreaks are outliers.
- **Method**:
 1. **Strict Data Separation**: Split data into Train ([deferred]) and Test ([deferred]) **before** calculating statistics.
  2.  **Centroid Calculation**: Compute mean $\mu_{benign}$ and covariance $\Sigma$ **only** from the **Training Set's** benign samples.
  3.  **Regularization**: Use `LedoitWolf` shrinkage estimator for $\Sigma$ to ensure invertibility when embedding dimension (768) > sample count.
  4.  Calculate $D_M(x) = \sqrt{(x - \mu_{benign})^T \Sigma^{-1} (x - \mu_{benign})}$ for all samples.
  5.  **Random Noise Baseline**: Generate synthetic Gaussian noise vectors of the same dimension and calculate their distance to $\mu_{benign}$. This tests if jailbreaks are outliers relative to a general "audio-like" distribution, avoiding tautological validation against the specific benign subset.

### 3. Classification (Logistic Regression)
- **Model**: `sklearn.linear_model.LogisticRegression`.
- **Rationale**: Interpretable, fast, CPU-friendly, and sufficient for linear separability testing in latent space.
- **Validation**: 80/20 stratified split. **Crucially**, the classifier is trained on the Train set, and the `AnomalyScore` for the Test set is computed using the Train set's statistics only.

### 4. Statistical Rigor & Assumptions
- **Multiple Comparisons**: We are running a single primary test (correlation of Mahalanobis distance with labels) and one classification task. No family-wise error correction is strictly required for a single hypothesis, but we will report p-values.
- **Sample Size/Power**:
  - The LALM datasets are large, but we will sample to fit the 6-hour limit.
  - **Acknowledgement**: If the resulting sample size is small (<1000), we will explicitly state the power limitation in the results.
- **Causal Framing**:
  - **Observational**: The data is observational (no random assignment of attacks).
  - **Claim**: Findings will be framed as **associational correlations** between latent anomalies and jailbreak labels. We will **not** claim the anomalies *cause* the jailbreaks or that the model *prevents* them, only that they are detectable.
- **Measurement Validity**:
  - **Labels**: Validated against the original dataset paper (LALM survey) to ensure they represent true adversarial attempts.
  - **Embeddings**: Validated by checking reconstruction loss on a held-out benign set (optional sanity check).
- **Collinearity**:
  - If we include text embeddings alongside audio, we must check for collinearity. However, the scope is **audio-only** embeddings.
  - If we use multiple audio encoders, we must acknowledge they may share latent features. The plan focuses on **one** encoder (Whisper) to avoid this.

## Computational Constraints & Feasibility
- **Hardware**: 2 CPU cores, 7 GB RAM.
- **Strategy**:
  - **Batching**: Process audio in small batches (32).
  - **Precision**: Use `float32` (default). Avoid `float16` if it causes instability on CPU without GPU.
 - **Sampling**: If the full dataset is too large, we will perform stratified sampling *before* embedding extraction to ensure the total number of embeddings fits in memory (e.g., [deferred] samples * 768 dims * 4 bytes ≈ 15 MB, which is trivial; the bottleneck is audio decoding and model inference time).
  - **Time**: 6 hours is generous for 5k-10k samples on a distilled model. If inference is slow, we will reduce the sample size further.

## Decision Rationale
- **Why Logistic Regression?** It is the simplest linear classifier. If it fails, the hypothesis (linear separability in latent space) is likely false. More complex models (SVM, Random Forest) add computational overhead without necessarily proving the core "anomaly" hypothesis better.
- **Why Mahalanobis?** It accounts for the covariance structure of the benign data, unlike Euclidean distance, making it more robust to anisotropic clusters.
- **Why CPU-only?** To satisfy the edge-deployment constraint and the specific project constitution (Principle VI).
- **Why Random Noise Baseline?** To avoid the tautological trap where "jailbreaks are far from benign" simply because they are "not benign". This tests if they are far from a general audio distribution.