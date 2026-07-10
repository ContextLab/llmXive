# Feature Specification: The Impact of Narrative Perspective on Empathy and Moral Judgement

**Feature Branch**: `001-narrative-perspective-empathy`  
**Created**: 2026-06-17  
**Status**: Draft  
**Input**: User description: "How does shifting narrative perspective in fictional texts—from first-person to third-person—affect readers' empathic engagement and subsequent moral judgements of character actions?"

## User Scenarios & Testing

### User Story 1 - Perspective Feature Extraction Pipeline (Priority: P1)

As a researcher, I need to automatically extract narrative perspective markers (pronoun density, focalization cues) from a corpus of public short stories so that I can quantify the independent variable for statistical analysis.

**Why this priority**: Without quantifying the predictor variable (narrative perspective), the core research question cannot be addressed. This is the foundational data generation step.

**Independent Test**: The pipeline can be tested by processing a small, manually annotated sample of 10 stories and verifying that the computed "first-person density" scores correlate ≥ 0.8 with human annotations of perspective type.

**Acceptance Scenarios**:

1. **Given** a raw text file of a short story in English, **When** the extraction script processes it, **Then** it outputs a JSON record containing `pronoun_density_1st`, `pronoun_density_3rd`, and `narrator_distance_score`.
2. **Given** a story containing no first-person pronouns (e.g., "The cat sat on the mat"), **When** the script runs, **Then** the `pronoun_density_1st` field is recorded as 0.0 with a confidence flag indicating "neutral/omniscient".
3. **Given** a mixed-perspective story, **When** the script runs, **Then** it calculates a weighted average score rather than a binary classification, preserving the nuance of the text.

---

### User Story 2 - Pilot Validation: Text Similarity Matching Logic (Priority: P2)

As a researcher, I need to validate the text-similarity matching algorithm by aligning a subset of processed stories with a "gold standard" set of story-judgement pairs from external datasets, so that I can ensure the matching logic does not introduce bias before applying it to the primary analysis.

**Why this priority**: This validates the *algorithm* used for data linkage. It ensures that the matching mechanism is robust and precise, but it is explicitly designated as a validation step, NOT the source of the primary dependent variable for the main research question.

**Independent Test**: The matching logic can be tested by running it against a "gold standard" subset of 50 manually annotated story-judgement pairs, selected via stratified random sampling across three difficulty levels (low, medium, high similarity), verifying a precision ≥ 0.9 on the matches.

**Acceptance Scenarios**:

1. **Given** a processed story with a computed TF-IDF vector (excluding pronoun features) and a target moral judgement dataset, **When** the similarity matcher runs, **Then** it returns the top-3 candidate moral judgement entries with their cosine similarity scores.
2. **Given** a story with no sufficiently similar match (similarity < 0.3 threshold), **When** the matcher runs, **Then** the story is excluded from the validation set and logged as "unmatched".
3. **Given** multiple moral judgement entries with similar similarity scores, **When** the matcher runs, **Then** it applies a deterministic tie-breaking rule (e.g., highest raw score) to select the single best match.

---

### User Story 3 - Primary Analysis: Statistical Association & Visualization (Priority: P3)

As a researcher, I need to run a linear regression and t-tests on the dataset containing reader-response data (from US-4) to determine if first-person perspective predicts higher deontological moral judgement scores and empathic engagement, and visualize these results, so that I can answer the research question.

**Why this priority**: This delivers the final scientific output (the answer to the research question) using the primary data source (reader responses), ensuring the results are interpretable as a psychological effect.

**Independent Test**: The analysis can be tested by running it on a synthetic dataset with a known, hardcoded correlation (e.g., slope = 0.5), verifying that the regression recovers the slope within a 5% margin of error.

**Acceptance Scenarios**:

1. **Given** the final aligned CSV dataset (containing reader-response data), **When** the analysis script executes, **Then** it outputs a summary table containing the regression coefficient, p-value, and R-squared for the relationship between `perspective_score` and `moral_judgement_score`.
2. **Given** the dataset contains multiple hypothesis tests (e.g., testing empathy and utilitarianism separately), **When** the script runs, **Then** it applies a Bonferroni correction and reports the adjusted p-values.
3. **Given** the analysis completes successfully, **When** the script finishes, **Then** it generates a scatter plot with a regression line and confidence interval saved as a PNG file in the `artifacts/` directory.

---

### User Story 4 - Primary Data Collection: Reader Empathy & Moral Judgement (Priority: P1)

As a researcher, I need to collect empathic engagement and moral judgement scores for a subset of the story corpus from human participants (or a validated proxy simulation) to serve as the primary dependent variable for the main analysis.

**Why this priority**: The research question explicitly asks about "readers' empathic engagement". External dataset proxies are insufficient for the primary hypothesis. This user story ensures the dependent variable is directly measured (or validly proxied) from a reader perspective.

**Independent Test**: The data collection module can be tested by running a pilot with a small cohort of participants on a limited set of stories, verifying that the collected scores (e.g., IRI scale, moral dilemma rating) show variance and correlate with known narrative archetypes.

**Acceptance Scenarios**:

1. **Given** a story from the corpus, **When** a participant completes the reading and the survey, **Then** the system records `empathy_score` (e.g., Interpersonal Reactivity Index) and `moral_judgement_score` (e.g., 1-7 Likert scale) linked to the story ID.
2. **Given** a participant who fails the attention check (e.g., "Select 'Strongly Agree' for this item"), **When** the survey is submitted, **Then** the response is flagged as invalid and excluded from the dataset.
3. **Given** the full dataset of reader responses, **When** the aggregation script runs, **Then** it outputs a CSV containing `story_id`, `perspective_score`, `empathy_score`, and `moral_judgement_score` for the primary analysis.

### Edge Cases

- **What happens when** the input text is too short (e.g., < 50 words) to reliably calculate pronoun density? The system must exclude the record and log a "data_quality_insufficient" warning rather than producing a spurious zero.
- **How does the system handle** non-English text or mixed-language stories? The system must detect language via `langdetect` and skip processing if the primary language is not English, logging the filename.
- **What happens when** the text similarity matching yields a false positive (e.g., matching a story about "war" to a moral judgement dataset entry about "war" but with different context)? The sensitivity analysis in FR-006 and SC-003 addresses this by sweeping the similarity threshold to observe stability.

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract first-person and third-person pronoun frequencies from input text using a standard NLP library (e.g., spaCy) and normalize them by total token count to produce a `perspective_score` between 0.0 and 1.0. (See US-1)
- **FR-002**: System MUST compute TF-IDF vectors for all processed stories and all candidate moral judgement dataset entries to enable cosine similarity matching. (See US-2)
- **FR-003**: System MUST perform a linear regression analysis where `perspective_score` is the predictor and `moral_judgement_score` (from reader data) is the outcome, reporting the slope, intercept, and p-value. (See US-3, US-4)
- **FR-004**: System MUST implement a Bonferroni correction for multiple comparisons if more than one moral dimension (e.g., care, fairness, loyalty) is tested simultaneously, adjusting the significance threshold to α/k. (See US-3)
- **FR-005**: System MUST generate a scatter plot visualizing the relationship between `perspective_score` and `moral_judgement_score` with a 95% confidence interval ribbon. (See US-3)
- **FR-006**: System MUST execute a sensitivity analysis on the text-similarity matching threshold by sweeping the cutoff value over the set {0.25, 0.30, 0.35, 0.40} and reporting how the sample size and headline correlation coefficient vary across these thresholds. (See US-2, US-3)
- **FR-007**: System MUST calculate the Variance Inflation Factor (VIF) for the predictor variables (e.g., first-person vs. third-person density if used as separate predictors) and report a warning if VIF > 5.0 to ensure model stability. (See US-3)
- **FR-008**: System MUST exclude all pronoun-based features (e.g., "I", "we", "he", "she") from the TF-IDF vector construction used for similarity matching to prevent circularity between the predictor and the matching metric. (See US-2)

### Key Entities

- **StoryDocument**: Represents a single narrative text with attributes `text_id`, `raw_text`, `language`, `perspective_score`, `tfidf_vector`.
- **ReaderResponse**: Represents a human or proxy response to a story with attributes `response_id`, `story_id`, `empathy_score`, `moral_judgement_score`, `participant_id`.
- **AnalysisResult**: Represents the outcome of the statistical test with attributes `regression_coefficient`, `p_value`, `adjusted_p_value`, `r_squared`, `sample_size`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The `perspective_score` extraction pipeline is measured against a manually annotated gold-standard subset of 50 stories to verify a Pearson correlation coefficient ≥ 0.85 between automated and human scores. (See US-1)
- **SC-002**: The text-similarity matching precision is measured against a stratified random sample of 100 potential matches (balanced by genre and similarity quartile) to ensure the false-positive rate is ≤ 5% at the primary threshold. (See US-2)
- **SC-003**: The statistical model stability is measured by the variation in the headline correlation coefficient (slope) when the similarity threshold is swept across a defined set of low, medium, and high values; the coefficient must not vary significantly across the sweep to be considered robust. (See US-3)
- **SC-004**: The multiplicity control is measured by verifying that the count of reported significant findings exactly equals the count of p-values < 0.05/k after Bonferroni adjustment. (See US-3)
- **SC-005**: The compute feasibility is measured by ensuring the total execution time of the analysis script on a standard GitHub Actions free-tier runner (multi-core CPU, standard RAM) does not exceed 45 minutes, with peak memory usage remaining below 6 GB. (See US-3)
- **SC-006**: The primary analysis validity is measured by confirming that the regression coefficient for `perspective_score` is derived from the `ReaderResponse` dataset (US-4) and not solely from external text proxies. (See US-3, US-4)

## Assumptions

- The public narrative corpora (e.g., Project Gutenberg) contain sufficient English-language short stories with clear narrative perspectives (first or third person) to achieve a sample size of at least 100 matched pairs after filtering.
- The external moral judgement datasets (e.g., Moral Foundations Twitter, HuggingFace moral dilemmas) contain textual descriptions of scenarios that are semantically similar enough to the story plots in the narrative corpus to allow for valid TF-IDF matching (for validation purposes only).
- The "empathic engagement" construct is adequately proxied by the "moral judgement scores" (specifically Care/Harm and Fairness/Cheating dimensions) available in the selected external datasets ONLY for the purpose of algorithm validation (US-2); for the primary analysis, reader-response data (US-4) is the source.
- The text-similarity matching process does not introduce circularity that invalidates the association; specifically, the features used for matching (TF-IDF) are distinct from the perspective markers (pronoun density) due to the explicit exclusion mandated in FR-008.
- The GitHub Actions free-tier runner environment (standard CPU allocation and memory capacity) is sufficient to run the required NLP preprocessing (spaCy) and statistical analysis (scikit-learn/statsmodels) without GPU acceleration.
- The dataset contains no hidden confounders (e.g., genre, publication year) that are perfectly correlated with narrative perspective, which would prevent isolating the effect of perspective alone.
- The sensitivity analysis sweep for the similarity threshold (0.25 to 0.40) is sufficient to detect instability in the results; if results are highly sensitive within this range, the study will report the instability rather than a single definitive value.
- The "moral judgement" scores in the external datasets are normalized or comparable across different source studies; if not, the analysis will treat them as relative ranks or apply z-score normalization per dataset before merging.
- **Reader-response data (US-4) is the primary source for the dependent variable in the main regression analysis**, ensuring the study addresses the "reader's" psychological state as required by the research question.