# Research: Phenomenological AI: First-Person Experience Modeling

## 1. Methodological Rationale

### 1.1 Operationalizing "First-Person Experience"
The core challenge is operationalizing a philosophical concept ("first-person experience") into computable metrics without committing category errors. We adopt a **structural coherence** approach: we do not claim the LLM *has* experience, but that its outputs *exhibit structural properties* (consistency, stability, phenomenological markers) analogous to human phenomenological reports. 

**Category Error Mitigation**: We explicitly frame the 'Marker Presence' metric as a **'Linguistic Proxy for Phenomenological Style'** rather than a direct measure of experience. The validation against human raters is for 'Stylistic Fidelity' (does the text *look* phenomenological?) rather than 'Ontological Validity' (does it *have* experience?).

### 1.2 Prompting Strategies
The four strategies (Direct, Hypothetical, Comparative, Role-play) are selected to manipulate the "frame" of the generation, testing if specific framing elicits higher structural coherence. This is the independent variable for the ANOVA.

### 1.3 Model Selection & Compute Constraints
The spec originally identified `meta-llama/Llamab-chat-hf` and `mistralai/Mistral-7B-Instruct-v0.2`.
**Constraint Analysis**:
- **Hardware**: GitHub Actions free tier (standard CPU allocation, ~7GB RAM).
- **Memory**: A large-scale model in FP16 requires substantial RAM. Even with 4-bit quantization, the overhead of `llama-cpp-python` on a 7GB RAM limit is risky and prone to OOM/Timeout.
- **Resolution**:
  1. **Primary Execution**: Use `TinyLlama-1.1B` (1.1B parameters) via `llama-cpp-python` with 4-bit GGUF quantization. This model fits comfortably within 4GB RAM, leaving headroom for the NLI and Embedding analysis models.
  2. **Exclusion of 7B Models**: The 7B models are **excluded** from the automated CI pipeline. They are too large for the specified compute environment. A separate script (`runner_local.py`) is provided for users with local hardware (≥16GB RAM) to attempt 7B inference, but these results are not part of the primary reproducible CI artifact.
  3. **Sequential Execution**: The NLI model (`bart-large-mnli`) and Embedding model (`all-MiniLM-L6-v2`) are loaded **sequentially** (one unloaded before the other) to prevent cumulative memory footprint from exceeding 7GB RAM.

**Decision**: The implementation uses `TinyLlama` as the primary model. The research question is reframed as: "How do prompting strategies affect the structural coherence of phenomenological-style text in a small-scale, CPU-tractable model?"

## 2. Dataset Strategy

### 2.1 Generated Corpus (Primary Data)
The "dataset" for this project is **synthetically generated**.
- **Source**: LLM inference on specific prompts using `TinyLlama-1.1B`.
- **Target Volume**: [deferred] samples (80 per condition × 4 strategies × 20 prompts).
- **Minimum Analysis Volume**: [deferred] samples (128 per condition) to ensure statistical power.
- **Variables**:
  - `prompt_strategy`: Categorical (Direct, Hypothetical, Comparative, Role-play).
  - `model_id`: Categorical (TinyLlama-1.1B).
  - `prompt_id`: Categorical (20 unique prompts).
  - `generation_seed`: Integer (for reproducibility).
  - `text_output`: String (the report).
- **Verified Sources**: No external dataset is used for generation. The "dataset" is created by the `code/generation/runner.py`.

### 2.2 Control Corpus (Discriminant Validity)
To address **methodology-87fdb544**, the pipeline generates a **Control Corpus** of 200 non-phenomenological technical reports (e.g., "Summarize this code snippet") using the same strategies.
- **Purpose**: To demonstrate that the metrics (NLI, Stability, Markers) are higher for phenomenological text than for generic technical text, establishing **discriminant validity**.
- **Variables**: Same as primary data, with `corpus_type` = "control".

### 2.3 External Validation Data (Human Ratings)
Human ratings are collected via a separate process (qualitative validation phase).
- **Source**: Two philosophy graduate students.
- **Rubric**: **'Phenomenological Depth'** (focusing on subjective richness, embodiment, temporal flow) - distinct from automated 'Structural Consistency'.
- **Blinding**: Raters are blind to prompt strategy and automated scores.
- **Format**: CSV with `report_id`, `rater_id`, `coherence_score`, `comments`.
- **Constraint**: Anonymized to prevent PII (Constitution Principle III).

### 2.4 Metric Calculation Dependencies
- **NLI Model**: `facebook/bart-large-mnli` (CPU-compatible).
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (CPU-optimized).
- **Keyword Dictionary**: Defined in `code/analysis/markers.py` based on phenomenological literature (e.g., Husserl, Merleau-Ponty).

## 3. Statistical Analysis Plan

### 3.1 Power Analysis
- **Goal**: Ensure the study is not underpowered (methodology-bafd86ec).
- **Parameters**: α=0.05, Power=0.80, MDES (f)=0.25 (medium effect).
- **Required Sample Size**: n=128 per group (Total N=512 for 4 strategies).
- **Strategy**: The pipeline targets [deferred] samples to ensure the ANOVA is valid.

### 3.2 Primary Analysis: ANOVA
- **Goal**: Determine if `prompt_strategy` significantly affects `validity_score`.
- **Hypothesis**: "Strategy X elicits a different phenomenological style (as measured by metrics) than Strategy Y."
- **Null Model**: Comparison against the Control Corpus to ensure metrics are sensitive to style differences.
- **Assumptions**:
  - Normality: Shapiro-Wilk test.
  - Homogeneity: Levene's test.
- **Correction**: If assumptions violated, use Kruskal-Wallis.
- **Post-hoc**: Tukey HSD for pairwise comparisons (FR-005).
- **Multiple Comparisons**: Benjamini-Hochberg FDR correction (α=0.05) applied to all p-values (FR-005).

### 3.3 Secondary Analysis: Correlation
- **Goal**: Correlate automated `validity_score` with human `coherence_score`.
- **Method**: Pearson or Spearman correlation.
- **Validation Logic**: We test for **pattern consistency** (e.g., if Role-play scores higher than Direct in both automated and human ratings) rather than direct correlation of the same concept. The human rubric ('Depth') is distinct from the automated metrics ('Consistency'), avoiding tautology (scientific_soundness-8a9f9a5b).

### 3.4 Sensitivity Analysis
- **Weights**: Test composite score weights {0.25, 0.5, 0.75} for each metric component (FR-006).
- **κ Threshold**: Test Cohen's κ thresholds {0.5, 0.6, 0.7} for re-evaluation triggers (FR-011).

## 4. Phenomenological Marker Definitions

To satisfy **FR-009** (Construct Validity), the keyword dictionary is derived from standard phenomenological texts:
- **Sensory**: "see", "hear", "feel", "touch", "smell", "warm", "cold", "light", "dark".
- **Temporal**: "now", "then", "before", "after", "moment", "duration", "flow".
- **Intentional**: "toward", "about", "for", "meaning", "aim", "directed", "conscious of".

*Note*: These definitions are approximate and will be subjected to sensitivity analysis (FR-006) to ensure robustness.

## 5. Risk Mitigation

| Risk | Mitigation Strategy |
| :--- | :--- |
| **OOM on 7B models** | **Excluded**. 7B models are not used in the CI pipeline. Only `TinyLlama-1.1B` is used. |
| **NLI model timeout** | Skip pair, log warning, continue (Edge Case handling). |
| **Generation timeout** | Retry 3 times, then mark as missing (FR-001). |
| **Low Cohen's κ** | Flag condition, trigger re-evaluation (Edge Case handling). |
| **CPU Runtime > 6h** | Reduce sample size per prompt to meet N=512 power target; prioritize statistical power over volume. |
| **Concurrent Memory OOM** | Sequential loading: Unload NLI before loading Embedding model. |
| **Circular Validation** | Human rubric ('Depth') is distinct from automated metrics ('Consistency'). Validation is based on pattern consistency, not direct correlation. |
