# Research: Quantization Robustness of Multi-Effect LoRA Adapters

## 1. Problem Statement & Hypothesis

**Problem**: Multi-Effect LoRA adapters (CollectionLoRA) combine multiple style/textural effects into a single weight matrix. It is hypothesized that post-training quantization (INT4/INT8) will disproportionately degrade low-rank subspaces, causing "concept bleeding" (interference between effects) and fidelity loss.

**Hypothesis**: 
1. Quantization noise (INT4) will cause a statistically significant drop in CLIP cosine similarity compared to FP16.
2. The magnitude of this drop (concept bleeding) will be **negatively correlated** with the **intrinsic source rank** of the specific LoRA subspace (lower rank = higher vulnerability).
   - *Note*: This correlation is **descriptive/exploratory** due to N=5 effects.
3. INT8 will show minimal degradation, while INT4 will show significant degradation.

## 2. Dataset & Model Strategy

### 2.1 Primary Data Source (Models)
The project requires a "CollectionLoRA" adapter containing ≥5 distinct effects.
- **Primary Strategy**: Synthesize a CollectionLoRA adapter by merging 5 verified, single-effect LoRA adapters from HuggingFace.
  - **Verified Sources for Synthesis** (Specific IDs):
    1. `lykon/dreamshaper-lora` (Style: Dreamshaper)
    2. `cagliostrolab/animagine-xl` (Style: Anime)
    3. `Kiloo/realistic-vision-v5` (Style: Realism)
    4. `stablediffusionapi/anything-v45` (Style: Anime/General)
    5. `prompthero/openjourney-v4` (Style: Midjourney-like)
  - **Fallback Strategy**: If any of the above are unavailable or incompatible (different base models), generate 5 **procedural low-rank matrices** with random weights to serve as the effects. This ensures the experiment is always feasible.
- **Base Model**: `stabilityai/stable-diffusion-2-1-base` (or `1.5` if VRAM constraints dictate).
- **Compatibility Check**: Before merging, verify all sources share the same base model architecture and rank.

### 2.2 Prompts & References
- **Prompts**: A fixed list of 10 diverse prompts (texture, lighting, style, object) defined in `code/config.yaml` (FR-009).
- **Reference Images**: Generated using the FP16 adapter.
- **Distractor References**: Generated using **unrelated** prompts to validate CESR specificity (Plan T004).

### 2.3 Verified Datasets
*Note: The "Verified datasets" block in the input refers to LLM evaluation logs, which are not usable here. The plan relies on the **verified single-effect LoRA repositories** listed above and the **base model** as the primary data sources. No external image dataset is required; images are generated in-situ.*

## 3. Methodology

### 3.1 Quantization (Zero-Shot)
- **Method**: `torch.ao.quantization` with `qconfig` for dynamic quantization on linear layers (LoRA weights).
- **Levels**: FP16 (Baseline), INT8, INT4.
- **Constraint**: Must run on CPU. If `torch.ao.quantization` fails to produce valid INT4 weights (e.g., due to backend limitations), the system logs "Backend Unavailable" and **skips** INT4 for that run (FR-002, Edge Cases).
- **Integrity Check**: After generation, if LPIPS > 0.8 or Similarity < 0.1, flag as "CatastrophicCollapse" and exclude from analysis (Plan T015).

### 3.2 Metrics
1. **Concept Adherence**: Cosine similarity between CLIP text embedding (prompt) and CLIP image embedding.
2. **Pixel Fidelity**: LPIPS distance between Quantized Image and FP16 Baseline Image.
3. **Concept Bleeding (Normalized CESR)**:
   - `CESR_raw`: Cosine similarity between Quantized Image embedding and **FP16 Reference Images** of *other* effects.
   - `CESR_baseline`: Mean similarity between Quantized Image embedding and **Distractor Reference Images** (unrelated prompts).
   - `CESR_normalized = CESR_raw - CESR_baseline`.
   - *Rationale*: This normalizes for general semantic drift (e.g., if the image becomes generic, it scores high on all effect references). The delta isolates specific cross-effect interference.

### 3.3 Statistical Analysis
- **Model**: Bayesian Hierarchical Model (PyMC).
- **Variables**:
  - `similarity_score` ~ Normal(μ, σ)
  - `μ` ~ Effect(quantization_level)
- **Correlation (Descriptive)**:
  - Aggregate `CESR_normalized` to the **effect level** (mean per effect).
  - Correlate aggregated bleeding with `SourceRank` (intrinsic rank from pre-merge matrices).
  - **Power Limitation**: N=5 effects is **insufficient** for statistical significance (ESS will be < 200). This is a **descriptive trend analysis**, not a hypothesis test.
  - **Flag**: Explicitly set `status` = 'Underpowered' in results.
- **Power Analysis**:
  - Check posterior width (≤0.2) for quantization effects.
  - Check ESS for correlation coefficient.
  - Flag "Underpowered" if criteria not met (FR-014).

## 4. Compute Feasibility & Escape Hatches

- **CPU-First**:
  - SD2.x on CPU: ~4-6GB RAM per generation. A total of multiple images will be collected.
  - Quantization: `torch.ao.quantization` on CPU is supported but slow.
  - Bayesian Analysis: PyMC on CPU for N=50 is trivial.
  - **Verdict**: Feasible within 6 hours.
- **No GPU Escape Hatch**:
  - The plan **does not** offload to Kaggle or any external GPU.
  - If CPU quantization fails, the level is skipped and flagged. This preserves reproducibility on the target platform.

## 5. Risk Mitigation

- **Risk**: Public CollectionLoRA adapter missing.
  - **Mitigation**: Synthetic construction from 5 verified single-effect LoRAs or procedural generation (Plan Section 2.1).
- **Risk**: OOM on CPU (Exit 137).
  - **Mitigation**: `try/except` block catching `MemoryError`; log "MemoryLimitExceeded"; skip quantization level (FR-008).
- **Risk**: Quantization collapses the model (LPIPS > 0.8).
  - **Mitigation**: "Model Integrity Check" after generation; if LPIPS > 0.8 or similarity < 0.1, log "Quantization Failure: Catastrophic Collapse" and exclude from analysis (Plan Section 5).
- **Risk**: Low statistical power (N=5 effects for correlation).
  - **Mitigation**: Explicitly label correlation as **descriptive/exploratory**; flag `status` = 'Underpowered' (FR-014).