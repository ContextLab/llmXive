# Research: Linguistic Accommodation and Speaker Emotional Intensity

## Overview

This research document defines the data strategy, methodological approach, and statistical rigor for analyzing the relationship between linguistic accommodation and emotional intensity in the DailyDialog dataset. It addresses the pivot from AI empathy (unavailable data) to human-human dialogue dynamics (available data). The study now investigates the association between **turn-level accommodation** and **dialogue-level emotional intensity**.

## Dataset Strategy

### Primary Dataset: DailyDialog (Canonical)
- **Source**: DailyDialog (Human-Human Dialogue)
- **Verified URLs**:
 - `
- **Selection Rationale**: DailyDialog is the only verified dataset in the source list containing human-human dialogue with explicit emotion labels. While labels are per-dialogue (not per-turn), this can be aggregated.
- **Access Method**: Programmatic loading via `datasets.load_dataset("dailydialog", split="test")` (using the HuggingFace `datasets` library) or direct download of the zip file.
- **Variable Fit Verification**:
 - **Required Variables**: `text` (utterances), `emotion` (label per dialogue).
 - **Dataset Availability**: DailyDialog provides `text` (utterances) and `emotion` (labels: 0-7 mapped to Joy, Sadness, Anger, Fear, Surprise, Disgust, Neutral).
 - **Fit**: **Confirmed** with Aggregation Strategy. The dataset contains all necessary variables. The study unit of analysis is the **dialogue** for emotion, and **turn-pairs** for accommodation. We compute accommodation metrics between adjacent turns and associate them with the single emotion label of the containing dialogue.

### Data Exclusion Criteria
- Turns with empty strings after Unicode NFKC normalization.
- Dialogue pairs where either the turn or partner turn is missing.
- Records with missing emotion labels (excluded from analysis).

## Methodological Approach

### 1. Data Preprocessing & Metric Computation
- **Normalization**: All text inputs will undergo Unicode NFKC normalization to handle non-ASCII characters and emojis consistently (FR-008).
- **Lexical Overlap (FR-001)**: Computed as Jaccard similarity of token sets (lowercased, stripped of punctuation) between `turn_i` and `turn_{i+1}`.
 - $J(A, B) = \frac{|A \cap B|}{|A \cup B|}$
- **Syntactic Similarity (FR-002)**: Computed as Jaccard similarity of Part-of-Speech (POS) tag sets (using NLTK's `pos_tag`) between the two turns.
- **Bigram Overlap (Sensitivity)**: Jaccard similarity of bigram sets to capture word order.
- **Positional Overlap (Sensitivity)**: Proportion of tokens in the same relative position (for short turns).
- **Sentence Length Variance**: Standard deviation of sentence lengths (in words) within the turn.

### 2. Emotional Intensity Mapping & Validation (FR-003, FR-010)
- **Mapping Rule**:
 - Joy: 5
 - Sadness: 2
 - Anger: 1
 - Fear: 2
 - Surprise: 4
 - Disgust: 1
 - Neutral: 3
- **Validation Protocol (Phase 1)**:
 1. **Literature Grounding**: Perform a **Chi-Square Goodness-of-Fit test** comparing the observed emotion distribution in DailyDialog against the known distribution in the ISEAR corpus. A p-value > 0.05 indicates statistical similarity.
 2. **Human Annotation**: Select a stratified random sample of dialogues. Annotate with multiple independent raters for 'Emotional Intensity' (1-5 scale).
 3. **Reliability Check**: Compute **Krippendorff's Alpha**. If Alpha < 0.6, the subset is rejected and re-sampled.
 4. **Mapping Validation**: Correlate the mapped scores (Joy=5, etc.) against the mean human ratings. If r < 0.3, the mapping is flagged as invalid, and the study proceeds using only the human-rated subset for the main analysis.

### 3. Statistical Analysis (FR-004, FR-005, FR-006, FR-009, SC-001, SC-002, SC-005)
- **Correlation Tests**:
 - **Spearman Rank Correlation** is the primary test (non-parametric, suitable for ordinal intensity).
 - **Pearson correlation** is **excluded** from primary tests due to the ordinal nature of the dependent variable.
 - **Multiple Comparison Correction**: Bonferroni correction applied to the primary tests (Spearman on Lexical, Syntactic, Bigram, Positional). $\alpha_{adj} = 0.05 / 4 = 0.0125$.
- **Regression Model (FR-007)**:
 - Model: **Ordinal Logistic Regression** (Proportional Odds Model).
 - Outcome: `emotional_intensity` (1-5 ordinal).
 - Predictors: `lexical_overlap`, `syntactic_similarity`.
 - **Covariates**: Conversation length (word count), Topic (LDA cluster ID, k=10). **One-Hot Encoding** is applied to Topic to avoid false ordinal assumptions.
 - **Output**: Odds Ratios and **McFadden's Pseudo-R2** (replacing R-squared).
- **Bootstrap Resampling (FR-006)**:
 - Procedure: Resample the dataset with replacement a sufficient number of times to ensure robust statistical inference.
 - Stopping Condition: Continue until the confidence interval width reaches a pre-specified threshold OR a maximum number of iterations is reached.
 - Output: Bootstrap distribution of Spearman correlation coefficients, 95% CI.
- **Sensitivity Analysis (FR-009)**:
 - Compare POS-based metrics against dependency-parse-based metrics (using `spaCy` on CPU) to validate construct validity.

### 4. Visualization (FR-005)
- Scatter plots of Accommodation Score vs. Emotional Intensity (jittered for ordinal values).
- Regression line with 95% confidence interval shading (derived from bootstrap).
- Effect size distribution histograms.

## Statistical Rigor & Assumptions

- **Observational Nature**: The study is observational. Findings will be framed as **associational**, not causal. No random assignment of linguistic styles occurred.
- **Power & Sample Size**: DailyDialog (~13k dialogues) provides ample power for correlation detection ($r > 0.05$) at $\alpha = 0.05$. Power limitations are acknowledged only if the effective sample size (after filtering) drops significantly.
- **Collinearity**: Lexical and syntactic overlap are definitionally related. The plan will report their individual correlations but will acknowledge potential collinearity in the regression model (VIF check). Independent effects will not be claimed if collinearity is high ($VIF > 5$).
- **Measurement Validity**: POS-tag overlap is a standard proxy for syntactic accommodation. Sensitivity analysis (FR-009) validates this proxy.
- **Multiple Comparisons**: Bonferroni correction is explicitly planned to control Family-Wise Error Rate (FWER) across the 4 primary hypothesis tests.
- **Unit of Analysis**: The unit of analysis for emotion is the **dialogue**, while accommodation is computed at the **turn-pair** level. This aggregation is explicitly documented.

## Decision Rationale: CPU-First Feasibility

- **Method**: All planned methods (Jaccard similarity, POS tagging, Spearman correlation, Ordinal Logistic Regression, bootstrap resampling) are computationally lightweight.
- **Feasibility**: These methods run efficiently on the target GitHub Actions CPU runner (a small-scale instance with limited cores and memory).
- **No GPU Required**: No deep learning models (transformers, embeddings) are needed for the core metrics. Dependency parsing (for sensitivity analysis) is CPU-tractable for this dataset size.
- **Conclusion**: The **CPU-first** strategy is selected. No GPU escape hatch is needed.