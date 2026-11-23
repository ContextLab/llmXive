# Research: llmXive follow-up: extending "Qwen-Image-Agent: Bridging the Context Gap in Real-World Image Generation"

## Problem Statement
The core research question is whether a syntactic complexity metric (independent of semantic content) can predict the need for agentic reasoning in image generation, and if so, where the "knee point" lies where the marginal fidelity gain from using the full Qwen-Image-Agent pipeline becomes statistically negligible. This study extends the Qwen-Image-Agent paper by introducing a hybrid routing strategy that bypasses expensive agentic processing for low-complexity prompts, aiming to reduce computational cost without sacrificing context fidelity.

## Dataset Strategy

| Dataset | Purpose | Source (Verified URL) | Access Method | Notes |
|---------|---------|----------------------|---------------|-------|
| IA-Bench | Raw text prompts for complexity scoring and generation | https://huggingface.co/datasets/irl-kit/IA-Bench/resolve/main/data/agibot_world/test/metadata.jsonl | `datasets.load_dataset(..., streaming=True)` | Contains diverse prompts; will be filtered for image-generation tasks. |
| WISE-Verified | Raw text prompts with cultural common sense verification | https://huggingface.co/datasets/Yuwei-Niu/WISE_Verified/resolve/main/cultural_common_sense_verified.json | `datasets.load_dataset(..., streaming=True)` | Provides high-quality, human-verified prompts; used for fidelity validation. |
| MTLD | Lexical diversity reference (optional, if not computed on-the-fly) | https://huggingface.co/datasets/Abeyankar/mtl_ds_full_fin/resolve/main/metadata.json | `datasets.load_dataset(...)` | Used to calibrate MTLD calculation; MTLD will be computed via `textstat` library. |
| CLIP (mfaq) | Reference descriptions for fidelity scoring | https://huggingface.co/datasets/clips/mfaq/resolve/main/data/cs/train.jsonl | `datasets.load_dataset(...)` | Contains image-caption pairs; used to verify CLIP model behavior on domain data. |

**Dataset Selection Rationale**: All datasets are open, programmatically accessible via Hugging Face `datasets` library, and verified for reachability. No access-gated data is used. Streaming is enabled for large datasets to fit within 7GB RAM.

**Data Hygiene Plan**:
- Each dataset fetch is followed by checksum computation (SHA-256) and storage in `data/raw/`.
- Reference-Validator Agent will verify all dataset citations before use (Constitution Principle II).
- **Reference Independence Check**: `02_validate_data.py` will verify that the `reference_description` field in WISE-Verified is distinct from the input `prompt` (string distance > 10% or semantic similarity < 0.8). Prompts failing this check are flagged and excluded from the Fidelity Metric calculation to prevent circular validation.
- Derived files (complexity scores, fidelity deltas) are stored in `data/derived/` with provenance logs.

## Methodology

### Phase 1: Syntactic Complexity Scoring (FR-001, FR-012)
- **Input**: Raw prompts from IA-Bench and WISE-Verified.
- **Features**: Parse tree depth (via `spacy`), clause count (via dependency parsing), MTLD (via `textstat`).
- **Exclusion**: No semantic embeddings (e.g., BERT, CLIP text encoder) used in scoring.
- **Output**: Normalized score (0.0–1.0) per prompt.
- **Validation**: Pilot study on 200 prompts (FR-012) to correlate score with human-rated "need for agentic reasoning".

### Phase 2: Hybrid Routing & Counterfactual Sampling (FR-002, FR-003, FR-007, FR-008, FR-009)
- **Routing Logic**: 
  - Low (< 0.2): Rule-based context expansion (template-based).
  - Medium (0.2–0.6): Rule-based context expansion.
  - High (> 0.6): Full Qwen-Image-Agent pipeline.
- **Counterfactual Sampling Strategy**: To enable Fidelity Delta calculation for Low/Medium prompts without executing the expensive Baseline for all prompts, a **random subset** of Low/Medium prompts is selected for **full Baseline (Qwen-Agent) execution**.
  - **High Complexity**: All prompts execute both Baseline (for verification) and Hybrid (Agent).
  - **Low/Medium Complexity**: 
    - **Counterfactual Sample**: A statistically valid random sample (seeded) executes **both** Baseline (Qwen-Agent) and Hybrid (Rule-based) to calculate Delta.
    - **Non-Sampled**: Executes **only** Hybrid (Rule-based). Delta is **undefined** for these points and they are excluded from the primary "Delta vs. Complexity" regression.
- **Execution**: Real image generation for High and Counterfactual Sample prompts; lightweight for non-sampled Low/Medium.
- **Logging**: Token counts, latency, routing decision, and sampling flag per prompt.

### Phase 3: Fidelity Measurement & Threshold Detection (FR-004, FR-005, FR-006, FR-010, FR-011)
- **Fidelity Metric**: CLIP ViT-B/32 similarity score between generated image and human-verified reference description.
- **Delta Calculation**: `Fidelity_Hybrid - Fidelity_Baseline`.
  - **Defined**: For High complexity prompts AND the Counterfactual Sample of Low/Medium prompts.
  - **Undefined**: For the Non-Sampled Low/Medium prompts. These are **excluded** from the "Delta vs. Complexity" regression.
- **Regression Strategy**:
  1. **Global Fidelity Curve**: "Hybrid Fidelity" vs. "Complexity Score" for **all** prompts (to show overall performance).
  2. **Delta vs. Complexity Curve**: "Fidelity Delta" vs. "Complexity Score" for **High + Counterfactual Sample only**. This is the primary curve for knee point detection.
- **Piecewise Linear Regression**:
  - Fitted on the **Delta vs. Complexity** dataset.
  - Identifies the "knee point" where the slope of the Delta curve stabilizes (approaches zero or changes sign).
- **Statistical Validation**:
  - F-test: Compare piecewise vs. linear model (p < 0.05 required).
  - **Likelihood Ratio Test (LRT)**: Explicitly validate non-linear relationship (FR-005). The LRT compares the log-likelihood of the piecewise model against the linear model. A significant LRT (p < 0.05) confirms the necessity of the non-linear term.
  - Permutation Test: 10,000 iterations to test if fidelity difference below threshold is distinguishable from zero (FR-006).
- **Stratification**: Domain classification via ResNet-50; separate regression per domain (FR-010, FR-011).

## Statistical Rigor & Feasibility

### Multiple Comparisons & Family-Wise Error
- For stratified analysis (3 domains), apply Bonferroni correction to alpha (0.05/3 = 0.0167) for domain-specific threshold tests.

### Sample Size & Power
- Target N ≥ 2,000 prompts.
- **Counterfactual Power**: With a random sampling of Low/Medium (e.g., 20-30%), we expect ~400-600 points in the "Delta" regression (assuming ~2000 total, ~1500 Low/Med). Power analysis deferred to pilot study; if N < 200 in the Delta set, acknowledge power limitation.

### Causal Inference
- **Observational Study**: Claims are associational for the full set.
- **Randomized Sub-Experiment**: The Counterfactual Sample provides a randomized assignment within the Low/Medium range, allowing causal inference about "agent value" for that subset.

### Measurement Validity
- CLIP ViT-B/32: Widely validated for image-text similarity; use frozen weights.
- Syntactic metrics: Standard NLP measures (parse depth, MTLD); validated in prior literature.
- **Reference Independence**: Validated via string/semantic distance check (Phase 1).

### Predictor Collinearity
- Parse depth and clause count may be correlated; report correlation matrix; if high (>0.8), use PCA or report descriptive relationship only.

## Compute Feasibility
- **CPU-First**: All steps (syntactic scoring, CLIP inference in batches, regression) are CPU-tractable.
- **GPU Escape Hatch**: Qwen-Image-Agent execution may require GPU; offload to Kaggle free-tier if CUDA error occurs. Scaled down to a manageable subset of high-complexity prompts if the full set exceeds time limit.
- **Streaming**: Datasets streamed to avoid RAM overflow; results accumulated in chunks.

## Decision/Rationale
- **Why Syntactic Only?** To avoid circular validation (Constitution Principle VI); semantic embeddings would confound the independence of the complexity metric.
- **Why CLIP?** Standard, frozen, CPU-tractable metric for image-text fidelity.
- **Why Piecewise Regression?** To identify a non-linear "knee point"; linear model insufficient for threshold detection.
- **Why Permutation Test?** To validate statistical significance without distributional assumptions.
- **Why Stratification?** Visual domains may have different ambiguity thresholds (Constitution Principle VII).
- **Why Counterfactual Sampling?** To resolve the "undefined Delta" problem for Low/Medium prompts without executing the expensive Baseline for all [deferred]+ prompts. This balances feasibility with statistical rigor.

## References
- IA-Bench: https://huggingface.co/datasets/irl-kit/IA-Bench
- WISE-Verified: https://huggingface.co/datasets/Yuwei-Niu/WISE_Verified
- CLIP ViT-B/32: https://huggingface.co/openai/clip-vit-base-patch32
- Qwen-Image-Agent: [Primary paper, to be cited via Reference-Validator]
- MTLD: https://huggingface.co/datasets/Abeyankar/mtl_ds_full_fin