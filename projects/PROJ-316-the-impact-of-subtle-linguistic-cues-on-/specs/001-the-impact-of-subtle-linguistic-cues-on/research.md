# Research: The Impact of Subtle Linguistic Cues on Perceived Authenticity in AI Chatbots

## Research Question

Do subtle variations in linguistic style—specifically first-person pronoun frequency, hedging language, and emotional valence—predict human ratings of perceived authenticity in AI chatbot conversations?

## Background & Literature Review

The perception of authenticity in AI is a critical factor in user trust and engagement. While extensive research exists on the "Uncanny Valley" and anthropomorphism, the specific role of *subtle* linguistic cues remains under-explored.
* **Hedging**: In human communication, hedging (e.g., "I believe," "perhaps") can signal intellectual honesty and appropriate uncertainty, potentially increasing authenticity. Conversely, over-hedging may signal weakness or lack of confidence.
* **First-Person Pronouns**: The use of "I" can personalize an interaction, but excessive use might be perceived as self-centered or unnatural for an AI.
* **Emotional Valence**: Sentiment alignment with the user's emotional state is often linked to rapport, but the relationship with "authenticity" is complex.

**Key Assumption**: The relationship is assumed to be linear or monotonic for the initial model, with non-linear terms tested as a robustness check (FR-009).

## Dataset Strategy

The project will utilize public datasets containing chatbot conversations for **text extraction only**. The dependent variable (authenticity) will be generated via a **human annotation protocol** to ensure construct validity.

### Verified Datasets (Text Source Only)
The following datasets have been verified for reachability and format (Parquet). They provide the text content for feature extraction but **do not contain human-rated authenticity scores**.

| Dataset Name | Source URL | Relevance & Limitations |
|:--- |:--- |:--- |
| **AIC (RobotDesign1M)** | ` | Contains chatbot conversations. **Limitation**: No authenticity ratings. Used for text extraction. |
| **AIC (AI-CUDA-Engineer)** | ` | Contains technical dialogues. **Limitation**: No authenticity ratings. Used for text extraction. |
| **AICC** | ` | Large-scale corpus. **Limitation**: No authenticity ratings. Used for text extraction. |
| **MixSub-LLaMA** | ` | Text-only. **Limitation**: No authenticity ratings. Used for text extraction. |

**Dataset Fit Analysis**:
The spec requires `authenticity_score` (FR-006). The verified datasets listed above provide rich text for feature extraction (FR-001) but **do not explicitly guarantee** the presence of human-rated authenticity scores.
* **Strategy**: The pipeline will extract linguistic features from these datasets.
* **Contingency (Human Annotation)**: To obtain valid `authenticity_score` data, the project will conduct a small-scale human annotation study on a stratified subset of these conversations. The sample size (N) for this subset will be determined by a **Power Analysis** (FR-011) to ensure sufficient statistical power for the multiple regression model.
* **Synthetic Data Restriction**: Synthetic labels (e.g., random or heuristic-based) are **strictly prohibited** for the main statistical analysis (FR-002/US-2). They may only be used for unit testing the pipeline code (US-1).

**Note**: No other datasets will be used. The plan does not invent a dataset URL.

## Methodology

### 1. Feature Extraction (FR-001, FR-008)
* **Tool**: `nltk` VADER Sentiment Analyzer for valence.
 * *Construct Validity Note*: VADER measures "emotional valence" (positive/negative polarity) based on social media data. It is used here as a **covariate** to control for sentiment, not as a direct proxy for authenticity. The primary hypothesis tests the unique variance of hedging and pronouns.
* **Hedge Lexicon**: Fixed list: `["maybe", "perhaps", "possibly", "probably", "likely", "unlikely", "seem", "seems", "appear", "appears", "believe", "think", "guess", "suppose", "assume"]`.
* **Metrics**:
 * `first_person_count`: Regex match for `\b(I|me|my|myself|we|us|our|ourselves)\b`.
 * `hedge_count`: Count of exact matches from the fixed lexicon.
 * `hedge_ratio`: `hedge_count / total_word_count`.
 * `sentiment_score`: VADER compound score.
 * `conversation_length`: Word count.

### 2. Lexicon Validation (FR-010)
* **Protocol**: A sample of 50 turns will be annotated by human raters to establish a "ground truth" for hedge presence.
* **Precision Calculation**: Precision = (Lexicon Matches ∩ Human Matches) / Lexicon Matches.
* **Threshold**: Target precision ≥ 0.8. If met, proceed. If not, flag for manual review.

### 3. Statistical Analysis (FR-002, FR-003, FR-004, FR-009)
* **Correlation**: Pearson and Spearman coefficients between each linguistic feature and `authenticity_score`.
* **Multiple Linear Regression**:
 * Dependent Variable: `authenticity_score` (Human-rated).
 * Independent Variables: `first_person_count`, `hedge_count`, `sentiment_score`.
 * Controls: `conversation_length`, `turn_count`.
 * **VIF Check**: Calculate Variance Inflation Factors. If VIF > 5, exclude the collinear variable or log a warning (FR-003).
 * **Non-linearity**: Test quadratic terms (e.g., `hedge_count^2`) and interactions (e.g., `hedge_count * sentiment_score`).
* **Multiple Comparison Correction**: Apply Benjamini-Hochberg procedure to all p-values (FR-004).
* **Power Analysis**: Perform a priori power analysis (FR-011) to determine if the sample size (N) is sufficient for the expected effect size. If N < 30, issue a warning (FR-007).

### 4. Sensitivity Analysis (SC-003)
* **Protocol**: Leave-one-out sweep of the 15-word hedge lexicon. Re-run the regression model multiple times, each time removing one word from the lexicon.
* **Metric**: Compare the stability of the regression coefficient for `hedge_count` across multiple iterations.

### 5. Visualization & Reporting (FR-005)
* Scatter plots with regression lines and 95% CI.
* Bar chart of regression coefficients.
* Markdown summary report.

## Statistical Rigor & Assumptions

* **Causal Claims**: None. The data is observational. Results will be framed as "associations."
* **Collinearity**: Explicitly addressed via VIF checks.
* **Multiple Comparisons**: Addressed via Benjamini-Hochberg.
* **Measurement Validity**: The hedge lexicon is fixed and citable. VADER is used as a sentiment control, with acknowledged limitations for non-social-media text.
* **Sample Size**: Determined by power analysis. The annotation protocol ensures N is sufficient for the regression model.

## Feasibility & Compute Constraints

* **Hardware**: CPU-only (2 cores, 7 GB RAM).
* **Method**: Lexicon-based extraction and standard linear regression are computationally lightweight.
* **Data Volume**: Processing a substantial volume of tokens is well within the time and memory constraints.
* **Libraries**: `nltk`, `scikit-learn`, `statsmodels` have CPU wheels and do not require GPU.

## Decision/Rationale

* **Why Lexicon over ML for Hedges?** The spec (FR-001) explicitly defines a 15-word lexicon. This ensures interpretability and reproducibility (Constitution Principle I) and avoids the computational overhead of training a classifier, fitting the CPU constraint.
* **Why Benjamini-Hochberg?** The project tests multiple hypotheses (multiple predictors, multiple correlations). Without correction, the family-wise error rate would be inflated.
* **Why VIF Check?** Linguistic features (e.g., word count and hedge count) are often correlated. VIF prevents singular matrix errors and ensures the stability of regression coefficients.
* **Why Human Annotation?** Synthetic labels create a fatal construct validity gap. Human annotation is the only method to measure "perceived authenticity" with validity.
* **Why Power Analysis First?** To prevent running an underpowered study (N=50) that cannot detect the effect, ensuring statistical rigor (FR-011).
