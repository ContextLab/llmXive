# Research: llmXive follow-up: extending "Qwen-Image-Agent: Bridging the Context Gap in Real-World Image Generation"

## Research Question
Can syntactic and lexical complexity metrics serve as a reliable, *testable proxy* for "ambiguity" in image generation prompts, enabling a hybrid routing system that preserves context fidelity while reducing computational cost? Specifically, is there a measurable "knee point" threshold where the fidelity advantage of a *rule-based text expansion* (vs. original prompt) vanishes?

## Hypothesis
**H1**: There exists a specific ambiguity score threshold (the "knee point") below which a rule-based context expansion yields context fidelity (CLIP score) statistically indistinguishable from the original prompt, and potentially superior to the original prompt.
**H2**: This threshold varies by visual domain (e.g., abstract vs. photorealistic), *if* domain metadata is available.
**H3**: Syntactic/lexical metrics (parse depth, MTLD) are *predictive* of the need for expansion, but this is a testable proxy, not an assumed sufficiency.

## Dataset Strategy

The study relies on the IA-Bench dataset, which provides both text prompts and their corresponding ground-truth images.

| Dataset | Purpose | Source/URL (Verified) | Access Method | Notes |
|:--- |:--- |:--- |:---:--- |
| **IA-Bench** | Primary prompt and *image* source. | ` (and associated image files) | `datasets.load_dataset` (streaming) or direct download. | Contains prompts and *image URLs*. Used as ground truth for CLIP scoring. |
| **WISE-Verified** | Secondary prompt source (if needed). | ` | `datasets.load_dataset` or direct download. | Used only if IA-Bench is insufficient; may lack images. |
| **MTLD** | **NOT USED** as a dataset. | N/A | N/A | MTLD is a *metric* computed via `textstat` on the prompt text itself. No external dataset is needed for calibration. |

**Data Feasibility Note**:
- **IA-Bench** is directly downloadable via HuggingFace URLs. It provides the necessary *images* for CLIP scoring.
- **No Access-Gated Data**: The plan does not require ADNI, HCP, or other gated datasets.
- **Data Volume**: The spec assumes ≥ 2,000 prompts. If the IA-Bench dataset is smaller, the plan will use all available data and note the power limitation. If larger, the plan will stream or sample (first-N or fixed seed) to fit the ~7GB RAM limit.
- **Domain Metadata**: The plan will explicitly check the IA-Bench schema for "visual domain" metadata. If missing, the stratified analysis (FR-010) will be **skipped** and reported as a limitation. **No keyword heuristics will be used** to infer domains, to prevent invalid aggregation.

## Methodological Rigor

### Ambiguity Scoring (FR-001, US-1)
- **Metric**: Weighted average of **Syntactic Complexity** (Parse Tree Depth, Clause Count via `nltk`/`spacy`) and **Lexical Diversity** (MTLD via `textstat`).
- **Exclusion**: Explicitly **NO** semantic embeddings (e.g., BERT, CLIP text vectors) will be used for scoring. This ensures independence from the fidelity metric (Constitution Principle VI).
- **Handling**: Malformed prompts receive a default score with a warning log.

### Routing Logic (FR-002, FR-003, US-2)
- **Deterministic**:
 - **Low**: Score < 0.2 → Rule-based text expansion.
 - **Medium**: 0.2 ≤ Score ≤ 0.6 → Rule-based text expansion.
 - **High**: Score > 0.6 → Simulated Agentic Pipeline (Latency only).
- **Simulation**: The "full agentic execution" is simulated (FR-009) using: `time = 15ms * token_count + 500ms`. **No real image generation is performed** for the "High" path. The study focuses on the efficacy of the *rule-based expansion* for Low/Medium prompts.

### Fidelity Measurement (FR-004, US-3)
- **Ground Truth**: The *original image* provided in the IA-Bench dataset for each prompt.
- **Model**: Frozen CLIP ViT-B/32 (CPU-tractable).
- **Calculation**:
 - **Baseline Fidelity**: CLIP_Score(Original_Prompt, Original_Image).
 - **Hybrid Fidelity**: CLIP_Score(Expanded_Prompt, Original_Image) (for Low/Medium paths).
 - **Fidelity Delta**: `Hybrid_Fidelity - Baseline_Fidelity`.
 - **High Path**: For "High" ambiguity prompts, no expansion is performed. The "Fidelity Delta" is recorded as `0.0` (no change) or excluded from the "expansion efficacy" regression, as the hypothesis tests the *gain* from expansion.
- **Validity**: By using the *real* ground-truth image, the CLIP score measures the semantic alignment of the *text* (original vs. expanded) with the *visual content*, restoring construct validity.

### Regression Analysis (FR-005, FR-010, US-3)
- **Model**: Piecewise Linear Regression (2 segments) on the "Fidelity Delta" vs. "Ambiguity Score" for the *Low/Medium* prompts.
- **Knee Point**: Identified where the slope change is maximized or where the improvement curve drops below a threshold.
- **Validation**:
 - **F-test**: Compare Piecewise vs. Linear model (p < 0.05 required).
 - **Permutation Test**: 10,000 permutations to validate the significance of the fidelity difference.
 - **Stratification**: Separate regression for domains *only if* explicit metadata exists. If not, global regression is performed and domain-specific claims are omitted.
- **Limitation Check**: If the correlation between Ambiguity Score and Fidelity Delta is weak (r < 0.1), the study will report "No Threshold Found" and reject the hypothesis that syntactic metrics are sufficient proxies.

### Statistical Rigor & Limitations
- **Multiple Comparisons**: If multiple thresholds (per domain) are tested, Bonferroni correction will be applied to the alpha level.
- **Power**: Acknowledgment of sample size limitations if < 2,000 prompts.
- **Causal Claims**: The study is observational/correlational regarding the "knee point". No causal inference is claimed beyond the simulation logic.
- **Collinearity**: Syntactic and lexical metrics may be correlated. Variance Inflation Factor (VIF) will be checked. If high, a composite score will be used, and independent effects will not be claimed.

## Compute Feasibility (CPU-First)

- **Ambiguity Scoring**: Pure Python (`nltk`, `spacy`, `textstat`). Runs in < 1s per 100 prompts. **CPU**.
- **Routing**: Simple threshold logic. **CPU**.
- **Expansion**: Text transformation. **CPU**.
- **CLIP Inference**: `transformers` CLIP ViT-B/32 on CPU.
 - **Strategy**: Batch processing (e.g., batch size 8-16) to fit ~7GB RAM.
 - **Time Estimate**: ~0.5s per image on 2 CPU cores. [deferred] images [deferred]s ([deferred]). Well within 6h limit.
- **Regression**: `statsmodels` or `scipy`. **CPU**.
- **GPU Escape Hatch**: Not required for this specific plan as CLIP ViT-B/32 is CPU-tractable for the expected dataset size.

## Decision/Rationale

- **Why CPU-First?**: The core logic (scoring, routing, regression) is lightweight. CLIP ViT-B/32 is small enough for CPU inference with batching. This avoids the complexity and cost of GPU offloading for a research study that fits within the free tier constraints.
- **Why Real Images?**: Using the ground-truth images from IA-Bench ensures the CLIP score measures semantic alignment, not noise consistency. This is critical for the validity of the "Context Fidelity" metric.
- **Why No Agent Image Generation?**: The "High" path simulation is for latency/cost analysis only. The fidelity analysis focuses on the *rule-based expansion* efficacy. Generating real images for the "High" path would require a GPU, violating the CPU-first constraint. The study tests if *expansion* is sufficient for low-ambiguity prompts, not if the agent is necessary for high-ambiguity ones (which is assumed).
