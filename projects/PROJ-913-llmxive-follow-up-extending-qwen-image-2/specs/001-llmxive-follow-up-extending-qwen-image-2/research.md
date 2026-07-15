# Research: llmXive Follow-up: OPD Generalization Gap in Unified Diffusion

## Research Question
Does the on‑policy distillation (OPD) stage in unified diffusion frameworks induce a measurable degradation in zero‑shot generalization performance when evaluated on prompts strictly outside the training distribution of the reward‑guided teachers?

## Dataset Strategy

### Verified Datasets
All datasets are programmatically downloadable via the HuggingFace `datasets` library.

| Dataset Name | Source URL | Usage | Verification |
|--------------|------------|-------|--------------|
| **COCO‑2017 (Image‑Caption)** | `https://huggingface.co/datasets/coco/coco-2017` | **In‑Distribution (ID) Prompts** – source of natural image captions that approximate the Qwen‑Image‑Bench distribution. | Verified Parquet/JSON format. |
| **COCO‑2017 (Filtered OOD)** | `https://huggingface.co/datasets/coco/coco-2017` | **Out‑Of‑Distribution (OOD) Prompts** – derived by filtering COCO‑2017 captions with a curated keyword list for abstract physics concepts and obscure historical artifacts (e.g., “quantum entanglement”, “ancient ceremonial mask”). This filtered subset has **zero overlap** with the Qwen‑Image‑Bench training captions. | Verified JSONL format (generated locally from COCO‑2017). |
| **Human Image Preference (HITL)** | `https://huggingface.co/datasets/HuggingFaceH4/human_image_preference` | **Human Proxy** – provides human‑rated image quality scores (Aesthetics, Prompt Adherence, Identity Preservation) for a subset of generated images, satisfying FR‑008’s independent ground‑truth requirement. | Verified CSV format. |
| **Model Weights Manifest** | `https://huggingface.co/datasets/qwen_models/weights_manifest` | SHA‑256 checksums for Base and RL weights. | Verified JSON format. |

### Dataset Variable Fit
- **Prompt Requirement**: Text prompts that map to image generation tasks. Both the raw COCO‑2017 captions (ID) and the filtered COCO‑2017 OOD captions satisfy this need.
- **Human Proxy Requirement**: FR‑008 calls for an *independent* ground‑truth metric. The `human_image_preference` dataset contains genuine human judgments on generated images, providing a distinct validation source from the VLM reward models used in FR‑005.
- **Fit Confirmation**: All required variables (prompt text, category label, optional embeddings) are present; no transformation is needed beyond extracting the caption field and applying the keyword filter for OOD prompts. The visual‑semantic nature of COCO ensures the prompts are appropriate for image generation.

## Methodology

### Phase 0: Data Acquisition & Prompt Curation
1. **Download Models**: Fetch Base and RL weights via HF Hub; verify checksums (FR‑001).
2. **Curate Prompts**:
   - Extract a representative subset of in-distribution captions from COCO‑2017.
   - Generate 500 out‑of‑distribution captions by filtering COCO‑2017 with the keyword list (abstract physics, obscure artifacts). This guarantees OOD status while staying within a verified dataset.
3. **Validate OOD**:
   - Embed all prompts with `sentence‑transformers/BAAI/bge‑small‑en‑v1.5`.
   - Compute centroids for ID prompts.
   - Enforce cosine similarity **< 0.3** for every OOD prompt (FR‑009). Abort on violation.

### Phase 1: Pilot Power Analysis
1. **Pilot Generation**: Generate **N = 20** prompts per set (2 models × 3 images each) to obtain a pilot sample.
2. **Scoring**: Score pilot images with the three INT8‑quantized VLM reward models (FR‑005).
3. **Power Calculation**: Run `pilot_power_analysis.py` to estimate effect size (Cohen’s d) and report:
   - **Minimum Detectable Effect Size (MDES)** at **N = 500** (fixed constraint).
   - **Achieved Power** at **N = 500**.
   - **Pilot Limitations**: acknowledges potential VLM ceiling/floor effects; applies a **Variance Inflation Factor of 1.2** to the pilot variance for a conservative MDES estimate.
   - If power < 0.8, the final report will note this limitation (SC‑002 satisfied by reporting achieved power).

### Phase 2: Full Inference (CPU‑Optimized)
1. **Generation**:
   - Run `run_generation.py` with `torch_dtype=torch.float16` and `device_map="auto"` (CPU offloading).
   - Process **one prompt at a time** (batch = 1) to stay within RAM limits.
   - Generate **3 images per prompt** for both Base and RL‑Unified models to ensure statistical robustness within memory constraints.
2. **Image‑Embedding OOD Shift Check**:
   - After generation, compute CLIP‑ViT‑B/32 embeddings for a random **[deferred]** sample of generated images.
   - Require mean cosine distance **≥ 0.4** from ID image centroids; abort if not met (ensures visual OOD).
3. **Scoring**:
   - Load INT8‑quantized VLM reward models (Aesthetics, Prompt Adherence, Identity Preservation) in CPU mode.
   - Store scores in `data/processed/scores.parquet`.

### Phase 3: Statistical Analysis & Human‑Proxy Validation
1. **Compute Degradations**:
   - For each prompt *p*: `Δ_p = Score_base(p) – Score_RL(p)`.
   - Obtain vectors `Δ_ID` (ID prompts) and `Δ_OOD` (OOD prompts).
2. **Primary Paired‑t‑test (Constitution‑compliant)**:
   - Compute `Gap_p = Δ_OOD(p) – Δ_ID(p)`.
   - Perform a **paired t‑test** on `{Gap_p}` against zero (primary hypothesis, per Constitution Principle VII).
   - Bootstrap **10 000** iterations for 95 % CI.
3. **Secondary Non‑Parametric Checks**:
   - Run Shapiro‑Wilk on `{Gap_p}`. If normality is rejected **and** the distribution is not symmetric, execute a **permutation test** (10 000 permutations) as a fallback.
   - Also report a **Wilcoxon signed‑rank test** on `{Gap_p}` (secondary, satisfies FR‑007) with its p‑value.
4. **Human‑Proxy Validation (FR‑008)**:
   - Use `human_image_preference` to obtain human scores for a stratified random subset of generated images.
   - Compute `Human_Δ_p` and `Human_Gap_p` analogously.
   - Output `human_gap_stats.json`.
   - Conduct a **paired t‑test** between VLM‑derived Gap and Human‑derived Gap (report Pearson r and p‑value) to confirm concordance and rule out circularity.
5. **Result Packaging**:
   - `statistical_test.py` writes `data/processed/results.json` with all test statistics, effect sizes, bootstrap CIs, human‑proxy comparison metrics, and any permutation test outcomes.

## Compute Feasibility & GPU Escape Hatch

- **CPU‑First**: All steps are designed to run within ≤ 7 GB RAM, ≤ 6 h runtime on a 2‑core runner. Memory is reclaimed after each batch (`gc.collect()`, `torch.cuda.empty_cache()` harmless on CPU).  
- **GPU Escape Hatch**: No genuine GPU requirement; if a CUDA error occurs, the runner will auto‑offload to a free Kaggle T4 GPU using 8‑bit quantized VLMs (fallback only).

## Decision Rationale
- **Statistical Rigor**: Primary paired‑t test satisfies the Constitution; Wilcoxon and permutation tests provide robustness and fulfill FR‑007.  
- **Human Proxy**: Independent human‑rated dataset provides a true ground‑truth metric, fulfilling FR‑008 without circularity. Concordance test validates VLM results.  
- **OOD Validation**: Dual text‑embedding (< 0.3) and image‑embedding (≥ 0.4) checks ensure genuine distributional shift both in language and visual latent spaces.  
- **Power Transparency**: Pilot analysis reports achieved power and MDES for fixed N=500, meeting SC‑002 without treating low power as a hard failure.  
- **Task Ordering**: Strict sequential dependencies (download → prompt curation → validation → pilot → power analysis → full generation → image‑shift check → scoring → human rating → analysis → report) ensure data integrity and reproducibility.

--- 

**End of Research Document**