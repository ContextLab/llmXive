# Research: llmXive follow-up: extending "ArcANE"

## 1. Problem Statement

The "ArcANE" hypothesis posits that role-playing LLMs maintain character consistency better when provided with fine-grained, phase-specific psychological axes (Fine) compared to broad trait summaries (Coarse). However, it is unknown if a "Hybrid" approach (combining both) offers superior transferability to novel, "Out-of-World" scenarios. This research aims to empirically validate this by generating novel probes, executing the target model under three conditions, and statistically comparing consistency scores. The unit of analysis is the (Character, Probe) pair (N ≥ 150), ensuring statistical power for repeated-measures tests.

## 2. Dataset Strategy

### Verified Datasets
The following sources have been verified for programmatic access and format compatibility:

| Dataset Name | Description | Verified URL / Loader | Status |
| :--- | :--- | :--- | :--- |
| **Project Gutenberg (via HF)** | Source text for character definitions (e.g., Elizabeth Bennet, Sherlock Holmes). | `huggingface/datasets/gutenberg` | **Verified** |
| **Gold Standard Annotations** | Manually created (n=20) for Judge Calibration (Static responses). | `data/gold_standard/human_annotations.json` (Local) | **Verified** |

**Note on Data Availability**: The experiment is restricted to characters available in the `gutenberg` dataset (public domain) to ensure the 'Out-of-World' semantic distance check can be automated against the actual source text. Characters like Harry Potter (copyrighted, not in `gutenberg`) are excluded from the automated pipeline to prevent the 'source text missing' failure. The axes for included characters are derived from the text in `gutenberg`.

### Data Processing Strategy
1. **Ingestion**: Stream `gutenberg` dataset to extract text for selected characters (e.g., Austen, Doyle).
2. **Manual Axis Definition**: Researcher inputs Coarse/Fine axes for each character into `data/derived/axes.jsonl`.
3. **Axis Validation**: Two independent researchers define axes; Kappa is calculated. If Kappa < 0.6, axes are revised.
4. **Probe Generation**: Use the `probe_generator` service to create multiple probes per character, filtering via cosine similarity against the source text (must be < 0.3).
5. **Gold Standard**: Load local `human_annotations.json` (static responses) for calibration.

## 3. Methodology

### 3.1. Experimental Design
- **Unit of Analysis**: (Character, Probe) pair.
- **Independent Variable**: Prompting Condition (Coarse, Fine, Hybrid).
- **Dependent Variable**: Consistency Score (1-5 Likert).
- **Subjects**: 3 Characters (e.g., Elizabeth Bennet, Sherlock Holmes, Atticus Finch - *only if available in gutenberg*).
- **Trials**: 50 probes per character × 3 conditions = 150 observations per condition (Total N=450).

### 3.2. Model Selection
- **Target Model**: `Phi-3-mini-4k-instruct` (4-bit quantized via `llama.cpp` or `bitsandbytes`).
  - *Rationale*: Fits within 7GB RAM on CPU.
- **Judge Model**: `TinyLlama-1.1B-Chat-v1.0` (8-bit quantized).
  - *Rationale*: Smaller than target, sufficient for scoring, fits in RAM.

### 3.3. Execution Flow
1. **Axis Validation**: Two researchers define axes; compute Kappa. Abort if Kappa < 0.6.
2. **Calibration**: Run Judge on a set of static, pre-written character responses (manually annotated). Compute Cohen's Kappa. If Kappa < 0.6, abort.
3. **Probe Generation**: Generate probes, filter for semantic distance (< 0.3 cosine similarity).
4. **Experiment Loop**:
   - For each probe and condition:
     - Construct prompt (Coarse/Fine/Hybrid).
     - Generate response (Target Model).
     - **Timeout Handling**: If generation > 60s, mark trial as `missing` (exclude from analysis or impute). Do NOT assign score 0.
     - Score response (Judge + Rule-based).
     - Log result.
5. **Statistical Analysis**:
   - Check normality (Shapiro-Wilk) on residuals.
   - If normal: Repeated-measures ANOVA.
   - If non-normal: Friedman test.

### 3.4. Rule-Based Metric (Non-Tautological)
The rule-based score is based on **sentiment alignment** and **narrative coherence** against the character's known profile (derived from source text), NOT on the presence of injected keywords. This prevents the 'Hybrid' condition from being guaranteed a higher score by construction.

### 3.5. Compute Feasibility
- **CPU-Only**: All models run in 4-bit/8-bit quantization on CPU. No GPU offload.
- **Streaming**: Probes and responses are streamed to disk immediately to avoid memory bloat.
- **Timeouts**: 60s per generation. Failures logged as `missing`.
- **Performance**: If the full experiment exceeds a substantial duration, the probe count per character will be reduced. to ensure completion within the CI limit.

## 4. Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Use Gutenberg only** | Ensures source text is available for automated semantic distance checks. Excludes copyrighted characters to prevent pipeline failure. |
| **Quantized Models (4-bit/8-bit)** | Required to fit ~7GB RAM on GitHub Actions free tier. Full precision would OOM. |
| **Dual Scoring (Judge + Rule)** | Prevents circularity (FR-006). Rule-based metric is based on sentiment/coherence, not keywords, to avoid tautology. |
| **Friedman vs ANOVA** | Ensures statistical validity (FR-005) regardless of data distribution. |
| **Missing Data Handling** | Excluding/Imputing timeouts prevents artificial bias against longer prompts (Hybrid condition). |
| **Static Calibration Set** | Ensures Judge Kappa compares evaluations of the *same* text, avoiding 'apples to oranges' comparison. |

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Model Timeout** | Incomplete experiment. | 60s timeout; mark as `missing`; exclude from analysis. |
| **Judge Calibration Failure** | Invalid results. | Abort if Kappa < 0.6; manual review of calibration set. |
| **Semantic Similarity Fail** | Probes too similar to source. | A maximum number of attempts per probe will be established.; discard character if < 50 valid probes found. |
| **CPU Performance** | Exceeds 6h limit. | Reduce probe count per character if necessary; stream results. |
| **Axis Definition Variance** | Subjective noise. | Two researchers define axes; require Kappa > 0.6. |