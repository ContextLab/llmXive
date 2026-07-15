# Research: llmXive Follow-up: OPD Generalization Gap in Unified Diffusion

## 1. Research Question

Does the on-policy distillation (OPD) stage in unified diffusion frameworks induce a measurable degradation in zero-shot generalization performance when evaluated on prompts strictly outside the training distribution of the reward-guided teachers?

## 2. Dataset Strategy

### 2.1 Model Weights
- **Base Model**: Qwen-Image-2.0 (Pre-trained).
  - **Source**: Hugging Face Model Hub (Canonical source).
  - **Verification**: SHA-256 checksum verification upon download.
- **RL-Unified Model**: Qwen-Image-2.0-RL (Student).
  - **Source**: Hugging Face Model Hub (Canonical source).
  - **Verification**: SHA-256 checksum verification upon download.

### 2.2 Prompt Sets
- **In-Distribution (ID) Set**:
  - **Description**: 500 prompts mirroring the Qwen-Image-Bench training distribution.
  - **Source**: Curated manually to match the style and content of the Qwen-Image-Bench training set.
  - **Verification**: Latent-space embedding similarity check against known training centroids (Target: Cosine Similarity > 0.7).
- **Out-of-Distribution (OOD) Set**:
  - **Description**: 500 prompts covering abstract physics concepts and obscure historical artifacts.
  - **Source**: **Primary**: `stabilityai/stable-diffusion-3-prompts` (Filtered for "abstract", "physics", "history", "artifact", "concept").
  - **Verification**:
    1.  **Latent-Space**: Cosine similarity to ID centroids < 0.3.
    2.  **Semantic**: Keyword filtering to ensure presence of target concepts (abstract physics, historical artifacts).
    3.  **Visual**: Subset of generated images visually inspected to confirm domain shift.
  - **Fallback Source**: `laion/laion-aesthetic-6plus` (Filtered for low-frequency CLIP concepts) if Primary fails to yield sufficient prompts.
  - **Note**: NLP datasets (xsum, hc3, PLANE) are explicitly excluded as they do not represent image generation prompts.

### 2.3 Human Proxy Data (FR-008)
- **Source**: `HuggingFaceH4/image-reward` dataset.
- **Usage**: This dataset contains human-annotated scores for image generation prompts. We will load this dataset and join it with our generated images via `prompt_id` (and `image_hash` if available) to provide an independent ground-truth metric.
- **Validation**: The "Generalization Gap" calculated from VLM scores will be correlated with the "Generalization Gap" calculated from Human Proxy scores to rule out circular dependency.

### 2.4 Dataset-Variable Fit
- **Fit**: The OOD datasets (`stabilityai/stable-diffusion-3-prompts`) contain text prompts suitable for image generation.
- **Gap**: The dataset may not perfectly align with "abstract physics" or "obscure historical artifacts" without filtering.
- **Mitigation**: Keyword filtering and manual curation will be used. If the filter fails, the Fallback Dataset Strategy (see 2.2) will be invoked.

## 3. Methodology

### 3.1 Data Acquisition & Curation
1.  **Download Models**: Fetch Qwen-Image-2.0 and Qwen-Image-2.0-RL from Hugging Face. Verify cryptographic hash checksums.
2.  **Curate Prompts**:
    - Load ID prompts.
    - Load OOD prompts from Primary Source (`stabilityai/stable-diffusion-3-prompts`).
    - **Filter**: Select prompts containing keywords: "abstract", "physics", "history", "artifact", "concept", "theory".
    - Compute latent-space embeddings.
    - Validate OOD set: Ensure cosine similarity to ID centroids < 0.3. Abort if contamination detected.
    - **Fallback**: If Primary Source yields < 20 valid prompts, switch to Fallback Source (`laion/laion-aesthetic-6plus`).
3.  **Load Human Proxy**: Fetch `HuggingFaceH4/image-reward` and index by `prompt_id`.

### 3.2 Inference Execution (CPU-Only)
1.  **Environment Setup**: Configure `diffusers` with `torch_dtype=torch.float16` and CPU offloading.
2.  **Generation**:
    - For each prompt in ID and OOD sets:
      - Generate a set of images using the Base model.
      - Generate a set of images using the RL-Unified model.
    - **Batching**: Process prompts in small batches (e.g., 1-2 at a time) to stay within 7 GB RAM limits.
    - **Garbage Collection**: Explicitly call `gc.collect()` after each batch.
3.  **Storage**: Save images to `data/outputs/base/` and `data/outputs/rl_unified/` with metadata (prompt ID, model version, seed).

### 3.3 Scoring & Evaluation
1.  **Reward Models**: Load quantized (INT8) VLM-based reward models for:
    - Aesthetics
    - Prompt Adherence
    - Identity Preservation
2.  **Scoring**:
    - Score all generated images (Base and RL) on all three metrics.
    - Aggregate scores per prompt (mean of multiple images).
3.  **Variance Handling (SC-005)**:
    - Calculate Coefficient of Variation (CV) per prompt across the 3 images.
    - **Action**: If `CV > 0.2`, set `variance_flag = True`.
    - **Exclusion**: Prompts with `variance_flag = True` are **excluded** from the primary mean degradation calculation.
    - **Robustness Check**: These prompts are included in a separate "Robustness Check" analysis to quantify noise sensitivity.

### 3.4 Human Proxy Validation (FR-008)
1.  **Join**: Match generated images to `HuggingFaceH4/image-reward` entries by `prompt_id`.
2.  **Calculate**: Compute degradation for Human Proxy scores (Base Proxy - RL Proxy) for the matched subset.
3.  **Correlate**: Compare the VLM-derived Generalization Gap with the Human Proxy-derived Generalization Gap.
4.  **Validation**: If the correlation is weak, flag the VLM results as potentially biased.

### 3.5 Statistical Analysis
1.  **Metric Calculation**:
    - Compute mean score degradation: `Degradation = Base_Score - RL_Score`.
    - Calculate separately for ID and OOD sets (excluding high-variance prompts).
2.  **Generalization Gap**:
    - `Gap = Mean(Degradation_OOD) - Mean(Degradation_ID)`.
3.  **Hypothesis Testing**:
    - **Null Hypothesis (H0)**: The Generalization Gap is zero (Mean(ID Degradation) == Mean(OOD Degradation)).
    - **Test**: **Independent Samples T-Test (Welch's t-test)** comparing the distribution of degradation values in the ID set vs. the OOD set.
    - **Bootstrap**: 10,000 bootstrap iterations to estimate confidence intervals for the effect size.
    - **Significance**: p < 0.05.
4.  **Power Analysis**:
    - Calculate achieved power based on the final N and observed effect size.
    - Report if power is < 0.80.

## 4. Computational Feasibility

- **Constraint**: 2 CPU cores, ~7 GB RAM, 6-hour limit, no GPU.
- **Strategy**:
  - **Model Loading**: Use CPU offloading for large diffusion models.
  - **Precision**: Float16 for generation, INT8 for VLM reward models.
  - **Batching**: Small batch sizes (1-2 prompts) to prevent OOM.
  - **Garbage Collection**: Aggressive `gc.collect()` after each step.
  - **Runtime**: Use the **Pilot-to-Target Decision Logic** (Plan Section 7) to dynamically adjust N.
  - **Fallback**: If runtime exceeds 6 hours even for Pilot, report Power Limitation and proceed with N=20.

## 5. Risks & Mitigations

- **Risk**: OOM crash during inference.
  - **Mitigation**: Dynamic batch size reduction, explicit garbage collection, memory monitoring.
- **Risk**: OOD prompt contamination.
  - **Mitigation**: Strict latent-space similarity check (< 0.3) and semantic keyword filtering.
- **Risk**: Runtime exceeds 6 hours.
  - **Mitigation**: Pilot-to-Target logic to scale N down dynamically.
- **Risk**: VLM reward models fail to load in CPU mode.
  - **Mitigation**: Use quantized (INT8) versions; fallback to CPU-only float32 if INT8 fails (with performance trade-off).
- **Risk**: Human Proxy data not available for specific prompts.
  - **Mitigation**: Proceed with VLM-only analysis for unmatched prompts, but report the reduced sample size for the validation step.

## 6. Decision Rationale

- **CPU-Only**: Mandated by the free-tier runner constraints.
- **Independent Samples T-Test (Welch's)**: Chosen to correctly compare two independent groups (ID vs OOD degradation distributions).
- **Human Proxy Validation**: Critical to satisfy FR-008 and avoid circular reasoning.
- **Variance Exclusion**: Ensures the main result is not driven by stochastic noise.
- **Dynamic Batching & Scaling**: Necessary to fit within 7 GB RAM and 6-hour time limit while maximizing throughput.
- **Semantic OOD Verification**: Ensures the OOD set is valid for image generation tasks, addressing construct validity.
