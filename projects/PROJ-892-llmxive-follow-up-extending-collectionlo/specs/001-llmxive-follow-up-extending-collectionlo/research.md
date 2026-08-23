# Research: Quantization Robustness of Multi-Effect LoRA Adapters

## Summary

This research investigates the impact of post-training quantization (INT8, INT4) on the "CollectionLoRA" architecture, specifically focusing on whether quantization noise induces "concept bleeding" (cross-effect interference) in low-rank subspaces. The study uses a CPU-first execution strategy on a GitHub Actions runner, leveraging `torch.ao.quantization.dynamic_quant` for zero-shot quantization and `diffusers` for image generation.

## Dataset Strategy

The study does not use a pre-existing dataset for training or evaluation. Instead, it generates a synthetic dataset of 10 distinct effect prompts (e.g., "oil painting", "watercolor", "neon", "sketch") to serve as the test set. The "dataset" is the collection of generated images and their corresponding CLIP embeddings.

**Verified Datasets**:
- **Base Model**: `stabilityai/stable-diffusion-1-5` (Public HuggingFace model).
- **Adapter**: The specific "CollectionLoRA" adapter is not available in the "Verified datasets" block. The plan assumes the existence of a publicly available multi-effect LoRA adapter (e.g., from a research release or a known repository like `stabilityai/collection-lora` if it exists, or a fallback to a known multi-LoRA merge).
  - **Fallback Strategy**: If no specific "CollectionLoRA" exists, the plan will **construct a synthetic multi-LoRA adapter** by merging 5 verified single-effect LoRAs.
  - **Verified Adapter Sources (Fallback)**:
    1.  `stabilityai/stable-diffusion-1-5-lora-examples/oil-painting` (Verified)
    2.  `stabilityai/stable-diffusion-1-5-lora-examples/watercolor` (Verified)
    3.  `stabilityai/stable-diffusion-1-5-lora-examples/neon` (Verified)
    4.  `stabilityai/stable-diffusion-1-5-lora-examples/sketch` (Verified)
    5.  `stabilityai/stable-diffusion-1-5-lora-examples/cyberpunk` (Verified)
    *Note: These are example IDs; the implementation will verify the exact IDs at runtime.*
- **Prompts**: A fixed list of 10 effect prompts defined in `config.yaml` (deterministic).

**Data Availability Note**: The plan does not rely on external datasets like OpenML or UCI. The "data" is generated on-the-fly. The only external dependency is the base model and the LoRA adapter, which must be downloadable via HuggingFace `datasets` or `diffusers` API.

## Methodology

### 1. Baseline Generation (FP16)
- Load `stable-diffusion-1-5` and the multi-effect LoRA adapter on CPU.
- Generate images (one per effect prompt) with 5 seeds (including Seed 0 for Gold Standard).
- **Gold Standard Reference**: Generate one image per prompt with Seed 0. This is the ground truth for LPIPS.
- Extract CLIP image embeddings and compute cosine similarity with prompt text embeddings.
- Compute LPIPS distance against the **Gold Standard** image (Seed 0) to establish baseline fidelity. **Clarification**: LPIPS measures "consistency relative to the FP16 baseline," not fidelity to an absolute ideal.

### 2. Quantization (INT8, INT4)
- Apply **Dynamic Quantization** to the LoRA weights using `torch.ao.quantization.dynamic_quant` (zero-shot, no calibration data).
- **Critical Note**: Quantization is applied *only* to the isolated LoRA module to avoid graph preparation errors. The Base UNet remains FP16.
- Generate the same 10 images using the quantized adapters.
- Compute CLIP similarity and LPIPS distance relative to the **Gold Standard** image.
- **Model Integrity Check**: If LPIPS > 0.8, the result is 'Not Testable'.

### 3. Subspace Analysis
- Extract per-effect LoRA weight matrices from the adapter (using regex or key inspection).
- Perform SVD on each matrix to compute the effective rank.
- Store ranks in `data/subspace_ranks.json`.
- **Fallback**: If regex fails, the `subspace_rank` becomes a constant. The correlation analysis (FR-007) is then aborted with status 'Not Testable'.

### 4. Statistical Analysis
- **Bayesian Linear Model**:
  - Formula: `similarity_score ~ quantization_level * subspace_rank + (1 | effect_id)`
  - **Clarification**: `subspace_rank` is a **per-effect** fixed effect covariate.
  - Priors: Strong, informative priors for quantization effects to compensate for low N.
- **Effect-Level Aggregation**:
  - Define 'Bleeding Magnitude' as the mean delta similarity across all 10 prompts for that effect.
  - Perform correlation analysis at the **Effect Level** (N=5) between 'subspace_rank' and 'Bleeding Magnitude'. **Clarification**: The correlation is between two effect-level variables (Rank and Mean Bleeding).
  - Note: N=5 is low; relies on strong priors.
- **Power Analysis & Abort Criteria**:
  - If the posterior width for the correlation coefficient > 0.2, the result is flagged 'Underpowered'.
  - **Consequence**: The hypothesis is declared 'Inconclusive' and cannot support the claim that low-rank subspaces are more vulnerable.

### 5. Concept Bleeding (CESR)
- **Reference Images**: Generate one image per effect prompt (Seed 1) to serve as the "other effect" baseline.
- **Other Effect Logic**: For a target prompt P_i, the system computes similarity against the set of Reference Images {R_j} where j != i. The CESR is the maximum similarity in this set.
- **Negative Control**: Compute similarity against Distractor References to validate metric specificity.
- Calculate **Normalized CESR**: `(CESR_quantized / CESR_FP16_baseline)`. If `CESR_FP16` is near zero, fallback to absolute delta. This accounts for scale differences in inherent similarity.

## Compute Feasibility & Decision/Rationale

**CPU-First Strategy**:
- **Model Loading**: SD + LoRA fits in ~-5GB RAM. The runner has sufficient RAM. This is feasible on CPU using `enable_sequential_cpu_offload()`.
- **Generation**: Stable Diffusion on CPU takes a moderate amount of time per image. 10 prompts x 3 levels = 30 images. Total generation time is approximately half an hour or less.
- **Quantization**: `torch.ao.quantization.dynamic_quant` on CPU is supported. No GPU required for the quantization step itself.
- **Memory Management**: Use `enable_sequential_cpu_offload()` and explicit garbage collection to avoid double-memory overhead during quantization.

**GPU Escape Hatch**:
- If `torch.ao.quantization.dynamic_quant` fails to produce valid weights on CPU, the plan will switch to a quantized inference approach using `bitsandbytes` dynamic quantization on a Kaggle GPU. However, the spec explicitly requires `torch.ao.quantization` and "zero-shot" without re-distillation. If `torch.ao` fails, the experiment may be deemed unfeasible on the current infrastructure, and the plan will flag this as a "Compute Limitation" rather than fabricating data. **Note**: If INT4 fails on CPU, the INT4 level is **skipped** and the run is marked 'Compute Limitation: INT4 Unavailable'.

**Decision**: Proceed with CPU-only `torch.ao.quantization.dynamic_quant`. If it fails, the pipeline will log "Quantization Failure" (FR-008) and skip that level, rather than fabricating data.

## References

- **CollectionLoRA Paper**: (To be verified against primary source; likely "CollectionLoRA: Collecting Multiple Effects in 1 LoRA via Multi-Teacher On-P").
- **CLIP**: Radford et al., "Learning Transferable Visual Models From Natural Language Supervision" (2021).
- **LPIPS**: Zhang et al., "The Unreasonable Effectiveness of Deep Features as a Perceptual Metric" (2018).
- **Bayesian Data Analysis**: Gelman et al., "Bayesian Data Analysis" (3rd ed.).
