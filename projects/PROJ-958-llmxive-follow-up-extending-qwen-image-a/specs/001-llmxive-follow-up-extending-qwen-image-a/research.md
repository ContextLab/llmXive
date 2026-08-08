# Research: llmXive follow-up: extending "Qwen-Image-Agent"

## Objective

To determine if a deterministic "Syntactic Complexity Score" can predict the necessity of agentic reasoning in image generation. Specifically, we aim to identify a "knee point" threshold where the marginal gain in "Context Fidelity" (CLIP similarity + Structural Detail Score) from using the full Qwen-Image-Agent pipeline (or Verified Proxy) becomes statistically indistinguishable from a lightweight rule-based expansion.

## Dataset Strategy

We utilize two primary datasets for prompt ingestion. Both are verified, open-access, and programmatically downloadable via Hugging Face `datasets` library, ensuring CI feasibility.

| Dataset | Role | Source / Load Method | Verification Status |
| :--- | :--- | :--- | :--- |
| **IA-Bench** | Primary prompt source (agentic context) | `datasets.load_dataset("irl-kit/IA-Bench", data_files="data/agibot_world/test/metadata.jsonl")` | Verified (HF URL provided) |
| **LAION-CC** | Secondary prompt source (general image-text pairs) | `datasets.load_dataset("laion/laion-captions", split="train", streaming=True)` (Filtered subset) | Verified (HF URL provided) |
| **MTLD Reference** | Calibration for lexical diversity | N/A (Algorithmic calculation via `nltk`) | N/A (No external dataset needed for calculation) |
| **Gold Standard References** | Reference text for Fidelity | **Generated** by Llama-3-70b (or GPT-4o if accessible) from prompts. | Generated (Not in source dataset) |

**Note on Dataset Fit**:
- **IA-Bench** and **LAION-CC** contain raw text prompts and (for LAION) associated images. They **do not** contain the "Context Fidelity" scores or "human-verified reference descriptions" in the sense of a pre-existing gold standard text.
- **Reference Generation**: The plan explicitly includes a step to generate "gold standard" reference descriptions using a high-capacity LLM (Llama-3-70b) from the prompt text. This ensures a consistent, high-quality reference text exists for every prompt in the paired sample, addressing the data availability gap.
- **MTLD** datasets listed in the verified block are *not* used as input data. The plan calculates MTLD algorithmically using `nltk` on the prompt text itself, as specified in FR-001.
- **WISE-Verified**: Removed. It is a text-reasoning dataset without image pairs, unsuitable for this study.

## Methodology

### Phase 0: Pilot Study (FR-012)
1.  **Sample**: Select a random sample of prompts from IA-Bench/LAION.
2.  **Scoring**: Compute Syntactic Complexity Score for each.
3.  **Ground Truth**: 3 human experts rate each prompt on a 1-5 scale for "Agentic Need" (Rubric: 1=Simple description, 5=Complex reasoning required).
4.  **Validation**: Calculate Pearson correlation between Syntactic Score and Mean Human Rating.
    -   **Success**: Correlation ≥ 0.5.
    -   **Failure**: Adjust weights ($w_1, w_2, w_3$) and re-run pilot.
5.  **Normalization**: Calculate Min/Max normalization parameters **only from this Pilot Study**. These parameters are **frozen** for the Main Study to prevent look-ahead bias.
6.  **Gate**: Store correlation coefficient in `data/results/pilot_correlation.json`. The Main Study (Phase 1) **cannot proceed** without this file.

### Phase 1: Syntactic Complexity Scoring (FR-001)
1.  **Parsing**: Load prompts from IA-Bench and LAION-CC. Parse each using `spacy` (en_core_web_sm) to extract:
    -   Parse tree depth (max depth of the dependency tree).
    -   Clause count (number of `ROOT` nodes in subordinate clauses).
    -   Token count.
2.  **Lexical Diversity**: Calculate Mean Length of T-Units (MTLD) using `nltk` logic:
    -   Segment text into T-units (independent clauses + attached modifiers).
    -   Compute average tokens per T-unit.
3.  **Normalization**: Normalize each metric to [0.0, 1.0] using the **frozen Min/Max parameters** from Phase 0.
4.  **Aggregation**: Compute `Syntactic_Complexity_Score` = $w_1 \cdot \text{Depth}_{norm} + w_2 \cdot \text{Clause}_{norm} + w_3 \cdot \text{MTLD}_{norm}$.
    -   Weights ($w_1, w_2, w_3$) are set to 1/3 unless Phase 0 suggests otherwise.
    -   **Constraint**: No semantic embeddings (e.g., BERT, CLIP text encoder) are used in this phase.

### Phase 2: Stratified Sampling & Reference Generation
1.  **Stratification**: Select a **paired sample of 600 prompts** (200 Photorealistic, 200 Abstract, 200 Illustration).
    -   Use a pre-trained ResNet-50 classifier (`src/domain/classifier.py`) to estimate domain for a large pool, then sample to ensure balance.
2.  **Reference Generation**: For all 600 prompts, generate a "Gold Standard" reference description using a high-capacity LLM (e.g., Llama-3-70b).
    -   Prompt: "Describe the image that should be generated from this prompt in high detail: [Prompt]."
    -   Store as `reference_text` in `data/processed/`. This is the dependent variable anchor.

### Phase 3: Hybrid Routing & Full Paired Execution (FR-002, FR-003, FR-009)
1.  **Routing Logic**:
    -   `Score < 0.2` → **Low**: Route to `lightweight_expander`.
    -   `0.2 <= Score <= 0.6` → **Medium**: Route to `lightweight_expander`.
    -   `Score > 0.6` → **High**: Route to **REAL Agent/Proxy**.
2.  **Execution (Paired)**:
    -   **CRITICAL**: For **EVERY** prompt in the 600-sample, run **BOTH** paths:
        -   **Path A (Hybrid)**: Execute the assigned path (Lightweight for Low/Med, Agent for High).
        -   **Path B (Baseline)**: **Always** execute the **REAL Agent/Proxy** (Qwen or SDXL-Turbo) regardless of complexity.
    -   **Engine Consistency**: The "Baseline" and "High" path use the **exact same engine** (Qwen if available, otherwise SDXL-Turbo proxy). This ensures the delta measures routing efficiency, not model capability differences.
    -   **Logging**: Record `latency_ms` and `token_count` (or `inference_steps` for diffusion models) for both paths.
        -   *Token Count Note*: For SDXL-Turbo (diffusion), `token_count` is N/A; `inference_steps` is logged as the valid efficiency proxy. For Qwen (LLM), actual tokens are logged.

### Phase 4: Fidelity Measurement & Statistical Analysis (FR-004, FR-005, FR-006, FR-010)
1.  **Fidelity Metrics**:
    -   **CLIP Score**: Compute cosine similarity between generated image and `reference_text` using frozen CLIP ViT-B/.
    -   **Structural Detail Score**: Compute a deterministic score based on the presence of key nouns/locations from the prompt in the image caption (generated by a captioning model) to address construct validity.
    -   **Fidelity Delta**: `Delta = Score_Baseline - Score_Hybrid`.
2.  **Regression**: Fit a piecewise linear regression model: $y = \beta_0 + \beta_1 x + \beta_2 (x - \tau)_+$.
    -   $x$: Syntactic Complexity Score.
    -   $y$: Fidelity Delta.
    -   $\tau$: Knee point threshold.
    -   **Hypothesis**: For Low X, Delta ~ 0. For High X, Delta > 0. The "Knee Point" is where Delta starts to rise significantly.
3.  **Model Comparison**:
    -   Perform **F-test** comparing Piecewise vs. Linear model. Require $p < 0.05$.
    -   Perform **Likelihood Ratio Test (LRT)** comparing Piecewise vs. Linear model. Require $p < 0.05$ (FR-005).
4.  **Permutation Test**: Shuffle Fidelity Deltas a sufficient number of times to generate a null distribution of the slope change. Verify observed slope change is in the top 5% (alpha=0.05).
5.  **Stratification**: Repeat regression for each visual domain (Photorealistic, Abstract, Illustration) using the domain-specific subset of the 600-sample. Apply Bonferroni correction for multiple comparisons.

## Compute Feasibility & Strategy

### CPU-First Strategy
-   **Scoring**: `spacy` and `nltk` are CPU-native and fast. 600 prompts will take < 10 minutes.
-   **CLIP**: `CLIP ViT-B/32` is CPU-tractable for inference on a small batch.
    -   *Optimization*: Process images in batches of a fixed size..
    -   *Memory*: Sufficient RAM is required for ViT-B variants (approx. 1GB model + batch buffers).
    -   *Time*: Inference on a batch of images (prompts x paths) takes a moderate amount of time on 2 cores..
-   **Regression**: `scikit-learn` and `numpy` are CPU-native. Permutation test (10k iterations) is fast on CPU for N=600.

### GPU Escape Hatch
-   **Agent/Proxy Execution**: This component **requires** a GPU.
    -   *Plan*: The `runner.py` script will detect if `CUDA` is available.
    -   *If No GPU*: The script will trigger the **Kaggle Auto-Offload** mechanism. The plan assumes this offload is active.
    -   *Fallback Engine*: If Qwen-Image-Agent is inaccessible, the script will automatically switch to **SDXL-Turbo** (via `diffusers`) as the "Verified Proxy" for the **REAL** execution.
    -   *Constraint*: We will limit the generation to a feasible sample size to fit within the approximate -hour Kaggle kernel limit.

## Statistical Rigor & Assumptions

1.  **Multiple Comparisons**: When performing stratified regression (3 domains), we will apply a Bonferroni correction or False Discovery Rate (FDR) control to the p-values of the knee point detection.
2.  **Power Analysis & Limitations**: The sample size (N=600, 200 per domain) is chosen to ensure power > 0.8 for detecting a medium effect size (Cohen's d=0.5) in the piecewise regression. However, if the model fails to converge or R² < 0.85, the result will be reported as "No Threshold Found" to avoid overfitting noise.
3.  **Causal Inference**: This is an **observational** study. We cannot claim the complexity score *causes* the need for an agent. We will frame results as "association" and "predictive threshold".
4.  **Collinearity**: Parse depth and clause count are likely correlated. We will report Variance Inflation Factors (VIF) and, if VIF > 5, combine them into a single "Structural Complexity" factor to avoid claiming independent effects.
5.  **Measurement Validity**: CLIP ViT-B/32 is a standard proxy for image-text fidelity. We acknowledge it may not capture "artistic intent" perfectly, so we supplement with a "Structural Detail Score".
6.  **Normalization**: Normalization parameters are **frozen** from the Pilot Study to prevent look-ahead bias.

## Risks & Mitigations

-   **Risk**: Qwen-Image-Agent API/Code is not accessible.
    -   *Mitigation*: Use **SDXL-Turbo** as the Verified Proxy. The plan explicitly defines this as the fallback "REAL" execution engine. Note: This shifts the construct from "Agentic Reasoning" to "High-Capacity Generation", which is a limitation acknowledged in the final report.
-   **Risk**: CLIP inference exceeds GB RAM on the runner.
    -   *Mitigation*: Implement streaming batch processing. Load a limited batch of images at a time.
-   **Risk**: No clear "knee point" exists (linear relationship).
    -   *Mitigation*: The plan explicitly handles this (Edge Case: "No Threshold Found"). The output will be "No Threshold Found" with the max observed fidelity delta recorded.