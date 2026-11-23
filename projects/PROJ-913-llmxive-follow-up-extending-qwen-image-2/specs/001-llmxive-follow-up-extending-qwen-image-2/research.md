# Research: llmXive Follow-up: OPD Generalization Gap in Unified Diffusion

## Problem Statement

The core research question is whether the On-Policy Distillation (OPD) stage in unified diffusion frameworks induces a measurable degradation in zero-shot generalization performance when evaluated on prompts strictly outside the training distribution of the reward-guided teachers. Specifically, we compare the performance of a pre-trained base model (Qwen-Image-2.0) against an RL-unified student model (Qwen-Image-2.0-RL) on In-Distribution (ID) and Out-of-Distribution (OOD) prompt sets.

## Dataset Strategy

The study requires two distinct prompt sets and two model weight repositories. The following datasets and sources are verified and used exclusively:

| Dataset / Source | Type | Verified URL | Usage |
|------------------|------|--------------|-------|
| **Qwen-Image-Bench (Public Evaluation Set)** | ID Prompt Source | ` | Source for In-Distribution prompts. |
| **LAION-2B (Subset: Physics/History)** | OOD Prompt Source | *No direct single-file URL; sampled via programmatic loader* | Source for Out-of-Distribution prompts. Filtered for 'Physics' and 'History' categories using a validated script.|
| **Qwen-Image-2.0 (Base)** | Model Weights | `Qwen/Qwen-Image-2.0` (Hugging Face Hub) | Pre-trained base model for generation. |
| **Qwen-Image-2.0-RL (Student)** | Model Weights | `Qwen/Qwen-Image-2.0-RL` (Hugging Face Hub) | RL-unified student model for generation. |
| **VLM Reward Models** | Scoring Models | `HuggingFaceH4/image-reward` (Aesthetics, Prompt Adherence); `clip-vit-base-patch16` (Identity Preservation)| Quantized models for Aesthetics, Prompt Adherence, Identity Preservation scoring.|
| **Proxy Reward Model** | Consistency Check | `HuggingFaceH4/image-reward` | External consistency check for Generalization Gap. |

**Note on Dataset Availability**:
- **Prompt Curation**: The spec requires an OOD set derived from LAION-2B. Since LAION-2B is massive, the plan implements a sampling strategy using a programmatic filter to extract prompts for 'Physics' and 'History'.
- **Model Weights**: Both Qwen models are available on the Hugging Face Hub. The implementation will verify SHA-256 checksums against the repository manifest (FR-001).
- **No Access-Gated Data**: No datasets requiring credentials are used. All data is open or programmatic.

**Dataset Variable Fit**:
- **Predictors**: Model Type (Base vs. RL), Prompt Distribution (ID vs. OOD).
- **Outcomes**: VLM Scores (Aesthetics, Adherence, Identity).
- **Covariates**: Prompt complexity (latent embedding magnitude), prompt length, and semantic content.

## Methodology

### 1. Data Acquisition & Curation (FR-001, FR-002, FR-009)
- **Model Download**: Download `Qwen/Qwen-Image-2.0` and `Qwen/Qwen-Image-2.0-RL` with SHA-256 verification.
- **Prompt Curation**:
 - **ID Set**: Sample from the Qwen-Image-Bench public evaluation set via HF Dataset loader.
 - **OOD Set**: Sample from LAION-2B subset (Physics/History) using a programmatic filtering script.
 - **Leakage Check**: Compute CLIP-ViT-L/14 embeddings for all OOD prompts. Calculate cosine similarity to the centroid of the ID set. If `max_similarity >= 0.3`, trigger re-curation (up to 2 iterations). Abort if still failing.

### 2. Inference Execution (FR-003, FR-004)
- **Engine**: `diffusers` pipeline with `torch_dtype=torch.float16` and `device_map="cpu"`.
- **Process**:
 - Load Base and RL models separately.
 - Generate multiple images per prompt for both models.
 - **Batching**: Process in small batches to stay under available RAM capacity.
 - **Timeout**: Monitor runtime; reduce sample size if needed.

### 3. Scoring (FR-005)
- **Models**: Load quantized VLMs for Aesthetics, Prompt Adherence, and Identity Preservation.
- **Process**: Score all generated images. Store scores in a structured JSON/CSV format.
- **Proxy Check**: Generate a subset of scores using `HuggingFaceH4/image-reward` as external reference.

### 4. Statistical Analysis (FR-006, FR-007, FR-008, FR-010)
- **Metrics**:
 - Mean Score Degradation (Base - RL) for ID and OOD sets.
 - Generalization Gap = (OOD Degradation) - (ID Degradation).
- **Hypothesis Test**:
 - **Null Hypothesis**: Generalization Gap = 0.
 - **Test**: Welch’s t-test on the degradation differences, accounting for unequal variances and non-normality. A Levene's test will be performed to assess variance homogeneity prior to selecting a test. If assumptions are not met after Welch's, bootstrap resampling (a sufficient number of iterations) will be used.
 - **Robustness**: Use HC3 robust standard errors.
 - **Covariates**: Include prompt length and semantic complexity as covariates in the LMM model to control for confounding factors.
- **Power Analysis**:
 - Compute achieved power and MDES at N=500.
 - Report "Variance Saturation Check".

## Compute Feasibility & GPU Escape Hatch

- **CPU-First**: The entire pipeline is designed for CPU execution.
- **GPU Escape Hatch**: (Not applicable; CPU-only plan).

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **CPU-Only Inference** | Mandatory for GitHub Actions free-tier feasibility. |
| **CLIP-ViT-L/14 + Reward Divergence for Leakage** | Ensures OOD integrity by checking both semantic and reward signal separation.|
| **Welch's t-test with Bootstrap** | Accounts for potential non-normality in score distributions and unequal variances between groups.|
| **Quantized VLMs** | Essential to fit scoring models into constrained RAM alongside inference buffers. |
