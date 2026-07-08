# Feature Specification: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

**Feature Branch**: `001-statistical-cognitive-decline`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing (Priority: P1)

The system must successfully acquire, clean, and structure the DementiaBank Pitt Corpus and ADReSS Challenge dataset, transforming raw interview transcripts into a standardized, analysis-ready format with verified cognitive status labels.

**Why this priority**: Without a clean, labeled dataset, no statistical analysis can occur. This is the foundational step that enables all subsequent feature extraction and modeling.

**Independent Test**: Can be fully tested by running the ingestion pipeline on a sample subset (e.g., 50 transcripts) and verifying that the output contains exactly 50 records with non-null cognitive status labels and cleaned text fields.

**Acceptance Scenarios**:

1. **Given** raw transcript files from DementiaBank and ADReSS, **When** the ingestion script processes them, **Then** the output dataset contains only cleaned text (no non-verbal annotations like `<laughter>` or `<pause>`) and valid cognitive status labels (Control, MCI, or AD).
2. **Given** a transcript with missing cognitive status metadata, **When** the ingestion script processes it, **Then** the record is excluded from the final dataset and logged as an exclusion with a specific reason code.
3. **Given** mixed encoding in source files, **When** the ingestion script processes them, **Then** all text is normalized to UTF-8 without data loss or character corruption.

---

### User Story 2 - Linguistic Feature Extraction and Statistical Testing (Priority: P2)

The system must compute lexical, syntactic, and semantic features for each participant and perform statistical hypothesis testing to identify significant differences between cognitive groups (Control vs. AD and Control vs. MCI).

**Why this priority**: This is the core research activity. It transforms raw text into quantifiable metrics and determines if the hypothesized relationship exists in the data, distinguishing early (MCI) from late (AD) decline.

**Independent Test**: Can be fully tested by running the feature extraction on a small, fixed dataset of 10 participants (5 control, 5 AD) and verifying that the output includes multiple feature categories (lexical, syntactic, semantic) with calculated p-values and effect sizes for each.

**Acceptance Scenarios**:

1. **Given** a cleaned transcript, **When** the feature extractor runs, **Then** it outputs at least 3 lexical diversity metrics (Type-Token Ratio, MTLD, Noun/Verb ratio), 2 syntactic complexity metrics (Mean Clause Length, T-unit Count), and 1 semantic coherence metric (Sentence Embedding Cosine Similarity).
2. **Given** feature values for Control, MCI, and AD groups, **When** the statistical test module runs, **Then** it outputs Mann-Whitney U test results with p-values and Cohen's d effect sizes for both (Control vs. AD) and (Control vs. MCI) comparisons.
3. **Given** multiple hypothesis tests (≥3 features), **When** the correction module runs, **Then** it applies Bonferroni correction and reports both raw and adjusted p-values.

---

### User Story 3 - Predictive Modeling and Validation (Priority: P3)

The system must train logistic regression and random forest classifiers to distinguish cognitive groups. This serves as a **Preliminary Sanity Check** to verify feature utility, while the primary validation uses nested cross-validation to account for small sample sizes.

**Why this priority**: This validates the practical utility of the identified features in a preliminary manner. It moves from "do features differ?" to "can features predict status?" but acknowledges the small sample size constraints.

**Independent Test**: Can be fully tested by training a logistic regression model on [deferred] of the data, tuning on [deferred], and evaluating on the held-out [deferred] test set, verifying that the output includes AUC, accuracy, and F1-score metrics. Additionally, the system must perform nested 5-fold cross-validation on the full dataset to generate the primary performance metric.

**Acceptance Scenarios**:

1. **Given** a stratified 70/15/15 train/validation/test split (Preliminary Sanity Check), **When** the logistic regression model trains, **Then** it converges within 100 iterations and achieves a training AUC ≥ 0.65 on the training fold.
2. **Given** a trained model on the [deferred] training set, **When** evaluated on the held-out [deferred] test set (Preliminary Sanity Check), **Then** the output includes AUC, accuracy, and F1-score, and the test AUC is ≥ 0.70.
3. **Given** the full dataset, **When** nested 5-fold cross-validation runs (Primary Validation), **Then** the mean AUC is statistically significantly greater than 0.5 (p < 0.05), and the standard deviation of AUC across outer folds is ≤ 0.05.

---

### Edge Cases

- What happens when the dataset contains participants with identical feature vectors (perfect collinearity)? The system must flag these records and exclude them from feature importance ranking to prevent inflated coefficients.
- How does the system handle transcripts with fewer than 50 words? The system must exclude these records from analysis, as linguistic metrics are unreliable on such short samples.
- What happens if the ADReSS dataset is unavailable? The system must gracefully degrade to using only DementiaBank data and log a warning that sample size is reduced.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest transcripts from DementiaBank Pitt Corpus and ADReSS Challenge, removing non-verbal annotations and normalizing text to UTF-8 (See US-1).
- **FR-002**: System MUST compute at least 6 linguistic features per participant: Type-Token Ratio, MTLD (Vocabulary Richness), Mean Clause Length, T-unit Count, Sentence Embedding Cosine Similarity, and Noun/Verb ratio (See US-2).
- **FR-003**: System MUST perform Mann-Whitney U tests for each feature between (Control vs. AD) and (Control vs. MCI) groups, reporting raw and Bonferroni-corrected p-values (See US-2).
- **FR-004**: System MUST train logistic regression and random forest classifiers using a stratified 70/15/15 train/validation/test split for preliminary sanity checks, and perform nested 5-fold cross-validation on the full dataset for primary validation (See US-3).
- **FR-005**: System MUST report model performance metrics (AUC, accuracy, F1-score) for both classifiers on the held-out test set and report the mean AUC and p-value from nested cross-validation (See US-3).

### Key Entities

- **Participant**: A unique individual with an associated cognitive status label (Control, MCI, or AD) and one or more interview transcripts.
- **Linguistic Feature**: A quantitative metric (e.g., Type-Token Ratio, Mean Clause Length) derived from a participant's transcript.
- **Model**: A predictive algorithm (Logistic Regression or Random Forest) trained on linguistic features to predict cognitive status.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of participants with valid cognitive status labels is measured against the total number of records in the raw DementiaBank/ADReSS datasets (See US-1).
- **SC-002**: The statistical significance of linguistic features is measured against a p-value threshold of 0.05 with Bonferroni correction applied for multiple comparisons (See US-2).
- **SC-003**: The predictive performance of the models is measured against a target AUC ≥ 0.70 for the preliminary 70/15/15 hold-out check, and statistically significant improvement over chance (p < 0.05) for the primary nested 5-fold cross-validation (See US-3).
- **SC-004**: The stability of the model is measured against a standard deviation of AUC ≤ 0.05 across 5-fold cross-validation folds (See US-3).
- **SC-005**: The computational feasibility is measured against a total runtime of ≤ 6 hours on a CPU-only runner with ≤ 7 GB RAM (See Assumptions).

## Assumptions

- The DementiaBank Pitt Corpus and ADReSS Challenge datasets are publicly accessible and contain sufficient sample sizes (≥ 500 participants per group) to achieve statistical power for the planned analyses.
- The linguistic features extracted (lexical diversity, syntactic complexity, semantic coherence) are measurable using standard NLP libraries (NLTK, sentence-transformers) without requiring GPU acceleration.
- The cognitive status labels in the datasets are reliable and derived from independent clinical assessments, ensuring no circularity between predictors and outcomes.
- The analysis is observational; therefore, all findings will be framed as associational rather than causal, as the data lacks random assignment.
- The constrained RAM of the CI runner is sufficient to load the preprocessed dataset and train small-scale models. (logistic regression, random forest) on a sampled subset if necessary.
- The Bonferroni correction method is appropriate for the number of hypotheses tested (≤ 10 features); if more features are added, the correction method may need adjustment.
- The semantic coherence metric using sentence-BERT embeddings is computationally feasible on CPU; if inference is too slow, a smaller pre-trained model (e.g., `all-MiniLM-L6-v2`) will be used as a fallback.
- The 70/15/15 split is used only as a preliminary sanity check due to small sample size constraints; the primary validation relies on nested cross-validation to maximize data utility.