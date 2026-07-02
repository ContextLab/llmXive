# Research: The Impact of Linguistic Accommodation on Perceived Empathy in AI Assistants

## Research Question
Does linguistic accommodation in dialogue (simulating AI-Human interaction) influence emotional congruence (a proxy for perceived empathy)?

## Theoretical Background
Linguistic Accommodation Theory (Communication Accommodation Theory, CAT) posits that individuals adjust their speech patterns (lexical, syntactic, prosodic) to converge with their interlocutors to increase social approval and rapport (Giles et al., 2003). In Human-Computer Interaction (HCI), this suggests that AI assistants mimicking user linguistic styles may be perceived as more empathetic. **Limitation**: This study uses Human-Human data (DailyDialog) as a proxy.

## Dataset Strategy

| Dataset Name | Source URL (Verified) | Usage | Variables Needed | Fit Check |
|--------------|-----------------------|-------|------------------|-----------|
| **DailyDialog** | https://huggingface.co/datasets/roskoN/dailydialog/resolve/main/test.zip (and related parquet/json) | Primary source for dialogue pairs, user turns, AI responses (proxy), and emotion labels. | `user_turn`, `ai_response` (2nd turn), `emotion_label`, `topic` | **Verified**: The dataset contains dialogue pairs with emotion labels (Joy, Sadness, Anger, Fear, Surprise, Disgust, Neutral) and topic labels. **Limitation**: It is Human-Human, not AI-Human. The "AI response" is simulated by the second turn. |
| **Giles et al. (2003)** | (Cited Literature, not a dataset) | Baseline for effect size comparison (SC-003). | N/A | Used as a theoretical benchmark for correlation strength (r=0.15). |

**Dataset Fit Analysis**:
The DailyDialog dataset is suitable for this study as a **proxy**. It provides the necessary components:
1.  **Dialogue Pairs**: Explicit `user_turn` and `ai_response` (simulated) fields.
2.  **Emotion Labels**: Includes `emotion` tags (e.g., "joy", "sadness") which map directly to the required Likert scale (FR-003).
3.  **Topic/Context**: Includes topic labels (provided in the dataset) which can be used as covariates (FR-007).

*Note: The study explicitly acknowledges that the "AI response" is a proxy (second turn of Human-Human dialogue) and the "empathy score" is a proxy (derived from emotion). The findings are about "Accommodation and Emotional Congruence" in dialogue, not necessarily AI empathy.*

## Methodology

### 1. Data Preprocessing
- **Normalization**: Apply Unicode NFKC normalization to all text (FR-008). Remove empty/non-text records.
- **Repetition Filter**: Exclude records where the Jaccard similarity between user and AI turn is > 0.9 (to distinguish accommodation from simple repetition).
- **Metric Computation**:
  - **Lexical Overlap**: Jaccard similarity of token sets (lowercased, stripped punctuation).
  - **Syntactic Similarity (POS)**: Jaccard similarity of POS tag sets (using NLTK `pos_tag`).
  - **Syntactic Similarity (Dependency)**: Jaccard similarity of dependency relations (using `spacy` dependency parser) for sensitivity analysis.
  - **Sentence Length Variance**: Variance of sentence lengths in the AI response.
- **Empathy Mapping**:
  - If explicit empathy rating exists: Use it.
  - Else: Map `emotion_label` to Likert (Joy=5, Sadness=2, Anger=1, Fear=2, Surprise=4, Disgust=1, Neutral=3).
  - Exclude records with no emotion label (document exclusion rate).
  - **Label**: This derived score is termed "Proxy Empathy Score" (Emotional Congruence).

### 2. Statistical Analysis
- **Correlation**:
  - Pearson correlation ($r$) between accommodation metrics (lexical, syntactic) and Proxy Empathy Score.
  - Spearman rank correlation ($\rho$) for robustness against non-linearity.
- **Multiple Comparison Correction**: Apply Bonferroni correction ($\alpha_{adj} = 0.05 / 4$) for the four primary tests (Pearson/Spearman on Lexical/Syntactic).
- **Regression Control**:
  - Linear model: $Empathy \sim Accommodation + \log(Length) + \text{Topic}_{dummies}$.
  - Controls: Conversation length (word count), **Topic (dataset-provided label, not LDA)**.
- **Bootstrap Resampling**:
  - **Iterative Loop**: Start with 1000 iterations. While `ci_width >= 0.01` and `iterations < max_limit` (e.g., 10000), increment iterations.
  - Purpose: Estimate stability of $r$ (SC-002).
- **Effect Size Interpretation**:
  - Report Cohen's guidelines (e.g., r < 0.1 is negligible, 0.1-0.3 small, 0.3-0.5 medium, >0.5 large).
  - Explicitly state if a significant result is trivial (e.g., p < 0.05 but r < 0.1).

### 3. Sensitivity Analysis (FR-009)
- **Metric**: Compare POS-based metrics against dependency-parse-based metrics.
- **Divergence Threshold**: If $|r_{POS} - r_{Dependency}| > 0.1$, the POS proxy is flagged as insufficient.
- **Execution**: Run `sensitivity_analysis.py`.

### 4. Validation Subset (FR-010)
- **Method**: Sample 30 random pairs. Compare the "Proxy Empathy Score" (inferred from emotion) against the original dataset's emotion label.
- **Expectation**: [deferred] match (since the rule is deterministic).
- **Purpose**: Verify that the mapping rule is applied consistently. (Note: A *new* human annotation task is not feasible; the dataset's existing labels serve as the validation proxy).

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Bonferroni correction applied (Assumption: Standard practice for 4 tests).
- **Power Justification**: DailyDialog test set size (approx. large number of turns) provides high statistical power for correlation detection. No power calculation needed for discovery, but effect sizes will be reported.
- **Causal Inference**: **Observational Study**. No randomization of linguistic style. Claims will be strictly **associational**. "Accommodation correlates with emotional congruence" NOT "Accommodation causes empathy".
- **Measurement Validity**:
  - **Instruments**: Emotion labels are a proxy for empathy. This is a limitation. The mapping rule (Joy=5) is an assumption, not a validated scale. The study tests "Accommodation vs. Emotional Congruence".
  - **Collinearity**: Lexical and Syntactic metrics may be correlated. Variance Inflation Factor (VIF) will be checked in the regression model. If VIF > 5, multicollinearity is acknowledged, and independent effects cannot be claimed.
  - **Topic Confounding**: Topic is controlled using dataset-provided labels to avoid LDA instability.
- **Dataset Fit**: DailyDialog is verified to contain the necessary variables. **Limitation**: It is Human-Human, not AI-Human. The "AI response" is a proxy (second turn).

## Compute Feasibility
- **Method**: CPU-only.
- **Libraries**: `scikit-learn`, `scipy`, `nltk`, `spacy` (CPU optimized).
- **Memory**: Text processing is linear; 13k pairs fit easily in < 1GB RAM.
- **Time**: POS tagging and Jaccard calculation are fast (< 1 min for full set). Bootstrap (iterative loop) may take a moderate duration on a limited number of cores. Dependency parsing (spacy) adds time but is CPU tractable for large-scale pair sets. Total runtime < 4 hours.
- **GPU**: Not required.
