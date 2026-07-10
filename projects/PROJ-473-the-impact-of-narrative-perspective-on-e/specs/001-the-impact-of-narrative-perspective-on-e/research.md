# Research: The Impact of Narrative Perspective on Empathy and Moral Judgement

## Research Question
How does shifting narrative perspective in fictional texts—from first-person to third-person—affect readers' empathic engagement and subsequent moral judgements of character actions?

## Dataset Strategy

The project relies on two distinct data sources: a **Story Corpus** (for the independent variable) and a **Reader Response** dataset (for the dependent variable). A secondary **External Moral Judgment** dataset is used *only* for validating the text-similarity matching logic (US-2).

### 1. Story Corpus (Independent Variable)
* **Source**: Project Gutenberg (Public Domain Short Stories).
* **Acquisition**: Downloaded locally via script using specific accession IDs (e.g., `pg12345`).
* **Variables**: `raw_text`, `story_id`, `genre`, `publication_year`.
* **Processing**:
 * Language detection (`langdetect`). Non-English texts are excluded.
 * Tokenization via `spaCy`.
 * **Feature Extraction**: Calculation of `pronoun_density_1st`, `pronoun_density_3rd`, and `perspective_score` (FR-001).
 * **TF-IDF Vectorization**: Computed excluding pronouns to prevent circularity (FR-008).
 * **Confounding Control**: Metadata (genre, year) is extracted and stored for use as covariates.

### 2. Reader Response Dataset (Dependent Variable - Primary)
* **Source**: **Verified External Datasets**:
 * **Primary**: Open Science Framework (OSF) repository for "Narrative Empathy and Moral Judgment" ( - *placeholder for actual verified DOI*).
 * **Secondary/Proxy**: Moral Foundations Twitter Dataset (for moral judgement proxies if specific empathy scores are unavailable).
* **Acquisition**: Fetched via verified URLs or programmatic loaders (e.g., `osfclient` or direct CSV download).
* **Variables**: `story_id` (linked to corpus), `empathy_score` (e.g., IRI), `moral_judgement_score` (e.g., Care/Harm, Fairness/Cheating), `participant_id`.
* **Strategy**:
 * **Real Data Only**: The primary analysis uses **only** real human response data from the verified sources above.
 * **Synthetic Data**: Used **strictly** for the "Independent Test" of the statistical engine (US-3) to verify that the regression code can recover known parameters. It is **not** used for the scientific conclusion.
* **Power Analysis**: Target sample size N=300 based on a conservative effect size (f²=0.05) for power=0.80 at α=0.05. If the external dataset is smaller, the plan explicitly states the power limitation.

### 3. External Moral Judgment Dataset (Validation Only)
* **Source**: **Verified External Dataset**: A subset of the "StoryCorpus" with human ratings (e.g., from a published study with open data).
* **Strategy**:
 * The "Verified datasets" block confirms the availability of specific datasets.
 * The matching logic will be tested against this **manually annotated gold standard** (not simulated) to ensure precision ≥ 0.9, as required by the spec.
* **Constraint**: Do NOT fabricate a URL. The plan uses only the verified sources listed.

## Methodology & Statistical Rigor

### 1. Feature Extraction (FR-001, FR-008)
* **Method**: `spaCy` tokenization.
* **Calculation**:
 * `perspective_score` = (Count of 1st Person Pronouns) / (Total Tokens).
 * **Collinearity Check**: If using both 1st and 3rd density as predictors, VIF will be calculated (FR-007). If VIF > 5.0, a warning is issued, and the model may be adjusted to use only the composite `perspective_score`.
 * **Confounder Extraction**: `genre` and `publication_year` are extracted to control for potential confounds.

### 2. Text Similarity Matching (US-2)
* **Method**: TF-IDF vectorization (excluding pronouns) followed by Cosine Similarity.
* **Threshold**: Primary threshold set at a moderate level.
* **Validation**: Precision measured against the **manually annotated gold standard** (real human data).
* **Sensitivity Analysis (FR-006)**: The threshold will be swept over {0.25, 0.30, 0.35, 0.40} to check stability of the correlation coefficient (SC-003).

### 3. Statistical Analysis (FR-003, FR-004)
* **Model**: Linear Regression: `moral_judgement_score ~ perspective_score + empathy_score + genre + year`.
* **Multiple Comparisons**: Bonferroni correction applied if testing multiple moral dimensions (e.g., Care, Fairness) simultaneously (FR-004).
* **Power/Sample Size**: The study targets N=300. If the external dataset is smaller, the plan reports the achieved power and limitations.
* **Causal Claims**: As this is an observational study, claims will be framed as "associational" unless the study design (e.g., randomized reading) supports causal inference. The plan avoids claiming causal inference from observational data.
* **Software Verification**: Synthetic data is used *only* to verify that the regression code recovers a hardcoded slope within 5% (US-3 Independent Test). This is distinct from the scientific analysis.

## Compute Feasibility
* **Environment**: GitHub Actions Free Tier (multiple CPUs, 7GB RAM).
* **Library Choice**: `scikit-learn` and `statsmodels` are CPU-optimized and memory-efficient.
* **Data Size**: The story corpus will be capped at ~300 stories to ensure memory usage remains < 6GB.
* **Runtime**: The pipeline (Extraction -> Matching -> Regression -> Plotting) is estimated to run in < 15 minutes.

## Risks & Mitigations
* **Risk**: Lack of verified external datasets for moral judgments.
 * **Mitigation**: Use specific verified datasets (OSF, Moral Foundations Twitter) as identified in the "Verified datasets" block. If no suitable dataset exists, the study explicitly reframes as a "Methodological Validation" only (though the plan prioritizes finding a real dataset).
* **Risk**: Circular reasoning in matching.
 * **Mitigation**: Strict enforcement of FR-008 (excluding pronouns from TF-IDF).
* **Risk**: Small sample size reducing statistical power.
 * **Mitigation**: The plan includes a power analysis and explicitly reports power limitations if N < 300.