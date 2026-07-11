# Feature Specification: llmXive Follow-up: Extending "A Stylometric Application of Large Language Models"

**Feature Branch**: `001-llmxive-followup`  
**Created**: 2026-07-04  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'A Stylometric Application of Large Language Models'"

## User Scenarios & Testing

### User Story 1 - Corpus Construction and Preprocessing (Priority: P1)

The researcher must be able to download a specific subset of scientific abstracts (cs.CL, physics.gen-ph, q-bio.QM) from the arXiv dataset via HuggingFace, filter for exactly 20 distinct lead authors with a minimum of 10 abstracts each (totaling 500+ abstracts), and preprocess this data into a normalized, character-tokenized format ready for model training.

**Why this priority**: This is the foundational data layer. Without a clean, balanced, and author-labeled dataset, no statistical analysis or model training can occur. It is the prerequisite for all subsequent steps.

**Independent Test**: The system can be tested by running the data ingestion script and verifying that the output directory contains exactly 20 author folders, each with ≥10 normalized text files, and that a summary log confirms the total count and author distribution.

**Acceptance Scenarios**:

1. **Given** the HuggingFace arXiv dataset is accessible, **When** the ingestion script runs with filters for `cs.CL`, `physics.gen-ph`, and `q-bio.QM`, **Then** the system downloads and extracts exactly 20 authors with ≥10 abstracts each, totaling ≥500 abstracts.
2. **Given** raw abstract text is retrieved, **When** the preprocessing module runs, **Then** the output files are lowercased, punctuation is removed, and text is tokenized into character sequences, with no semantic tokens remaining.
3. **Given** the dataset contains authors with <10 abstracts, **When** the filtering logic executes, **Then** those authors are excluded from the final training set, and a warning log is generated listing the excluded authors.

---

### User Story 2 - Character-Level N-gram Model Training and Perplexity Calculation (Priority: P2)

The researcher must be able to train a character-level n-gram language model (n=4 to n=6) for each of the 20 authors using an 80/20 train/test split, and subsequently compute the perplexity of the held-out test abstracts under every author's trained model to generate a perplexity matrix.

**Why this priority**: This implements the core "predictive comparison" mechanism. It transforms the raw data into the statistical signal (perplexity differentials) required to answer the research question.

**Independent Test**: The system can be tested by training a single author's model on a small subset and verifying that the computed perplexity for that author's own held-out text is significantly lower than the perplexity for a text from a different author.

**Acceptance Scenarios**:

1. **Given** a specific author's training corpus ([deferred] of their abstracts), **When** the n-gram model (order n=4 to 6) is trained using a CPU-efficient implementation, **Then** the model training completes within ≤ 300 seconds per author and the loss stabilizes (Δ < 0.01 over 5 epochs) or hits the maximum epoch limit, without requiring GPU resources or exceeding substantial RAM capacity.
2. **Given** a set of held-out abstracts for Author A and a set of abstracts from Author B, **When** the perplexity is calculated using Author A's model, **Then** the perplexity for Author A's held-out text is strictly lower than for Author B's text in ≥ 80% of held-out abstracts.
3. **Given** the full set of 20 authors, **When** the cross-evaluation loop completes, **Then** a complete perplexity matrix is generated, storing the perplexity score of every held-out abstract under every author's model.

---

### User Story 3 - Classification, Baseline Comparison, and Statistical Validation (Priority: P3)

The researcher must be able to assign predicted author labels based on minimum perplexity, calculate classification accuracy, compare this against a function-word frequency baseline using McNemar's test, and generate a robustness report on synthetic hybrid abstracts.

**Why this priority**: This delivers the final scientific result (accuracy and significance) and validates the method against both a traditional baseline and a synthetic stress test, completing the research loop.

**Independent Test**: The system can be tested by running the classification pipeline on the generated perplexity matrix and verifying that the output includes an accuracy score, a p-value from McNemar's test, and a degradation metric for hybrid texts.

**Acceptance Scenarios**:

1. **Given** the perplexity matrix, **When** the classification logic assigns the author with the minimum perplexity to each held-out abstract, **Then** the system calculates the overall classification accuracy and reports it as a percentage.
2. **Given** the n-gram model results and a function-word baseline, **When** McNemar's test is applied to the error rates, **Then** the system outputs a p-value and determines if the n-gram model's improvement is statistically significant (p < 0.05).
3. **Given** synthetic "hybrid" abstracts created by swapping sentences between authors, **When** these are evaluated, **Then** the system reports a classification accuracy drop of ≥ 20 percentage points compared to the original abstracts, confirming sensitivity to intra-author consistency.

### Edge Cases

- What happens if the arXiv dataset subset contains fewer than 20 authors with ≥10 abstracts? (System must fail gracefully with a clear error message and halt execution).
- How does the system handle abstracts that are too short to generate valid n-grams (e.g., < n characters)? (System must exclude these from training and testing, logging the count).
- How does the system handle the case where the n-gram model predicts equal perplexity for two authors? (System must implement a deterministic tie-breaking rule, e.g., alphabetical order of author ID, and log the frequency of ties).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and filter the arXiv dataset to include exactly 20 distinct lead authors with a minimum of 10 abstracts each, totaling at least 500 abstracts (See US-1).
- **FR-002**: System MUST normalize text by lowercasing and removing punctuation, then tokenize into character sequences for n-gram processing (See US-1).
- **FR-003**: System MUST train a character-level n-gram language model (order n=4 to 6) for each of the 20 authors using an 80/20 training split ratio (See US-2).
- **FR-004**: System MUST compute the perplexity of all held-out abstracts under every author's trained model to generate a complete cross-evaluation matrix (See US-2).
- **FR-005**: System MUST classify held-out abstracts by assigning the label of the model yielding the minimum perplexity and calculate the overall classification accuracy (See US-3).
- **FR-006**: System MUST implement a function-word frequency baseline using a Naive Bayes classifier trained on function-word counts, and compare its error rates against the n-gram model using McNemar's test on paired binary outcomes (See US-3).
- **FR-007**: System MUST generate synthetic "hybrid" abstracts by swapping sentences between authors and evaluate the degradation of the predictive signal on these samples (See US-3).
- **FR-008**: System MUST execute all data processing and model training steps on CPU-only resources without requiring GPU acceleration or CUDA libraries (See US-2).
- **FR-009**: System MUST implement an author disambiguation rule where authors are distinguished by the exact string match of the 'lead author' name as it appears in the `authors` list; in cases of name collisions (e.g., 'John Smith'), the system treats them as distinct entities based on the specific string token found in the metadata, and MUST log a warning for any name appearing >50 times across the dataset and flag it for potential manual review (See US-1).
- **FR-010**: System MUST apply Bonferroni correction to the p-value when comparing the best-performing n-gram order (selected from n=4, 5, 6) against the baseline to account for multiple hypothesis testing (See US-3).
- **FR-011**: System MUST implement Kneser-Ney smoothing (or modified Kneser-Ney) for all n-gram models to mitigate data sparsity issues given the limited abstract count per author (See US-2).

### Key Entities

- **Author**: A unique identifier for a scientific writer, associated with a set of abstracts.
- **Abstract**: A text unit (approx. 250 words) containing the title and body of a scientific paper, linked to an Author.
- **N-gram Model**: A probabilistic model trained on an Author's abstracts, characterized by order (n) and token counts.
- **Perplexity Score**: A scalar value representing the uncertainty of a model when predicting a specific abstract.
- **Hybrid Abstract**: A synthetic text unit constructed by combining sentences from two different Authors.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: Classification accuracy of the n-gram model is measured against the random chance baseline ([deferred]) and the expected target (>75%) (See US-3).
- **SC-002**: Statistical significance of the performance difference between the n-gram model and the function-word baseline is measured against the McNemar's test p-value threshold (p < 0.05) (See US-3).
- **SC-003**: Robustness of the model is measured by the drop in accuracy on synthetic hybrid abstracts compared to the original abstracts (See US-3).
- **SC-004**: Computational feasibility is measured by the total execution time against a limit of ≤ 2 hours and peak memory usage against a limit of ≤ 6 GB RAM (See US-2).
- **SC-005**: Methodological validity is measured by the successful application of Bonferroni correction (for multiple n-gram orders) and a reported statistical power ≥ 0.80 or a documented sample size justification (See US-3).

## Assumptions

- The arXiv dataset on HuggingFace contains sufficient metadata to reliably identify the "lead author" for at least 20 distinct individuals with ≥10 abstracts each in the specified categories (cs.CL, physics.gen-ph, q-bio.QM).
- The "predictive comparison" principle is observable in the data; if the dataset lacks sufficient stylistic variance in formulaic writing, the null hypothesis (accuracy ≈ random chance) is a valid and expected outcome.
- The arXiv dataset abstracts are sufficiently long (≥ n characters) to support n-gram modeling; abstracts shorter than the n-gram order will be excluded without biasing the results.
- The computational environment (GitHub Actions free tier) provides sufficient disk space to store the raw dataset and intermediate model artifacts without compression artifacts affecting the text.
- The "function-word" baseline uses a standard, validated list of English function words, as the specific list is not defined in the idea but is required for the Naive Bayes classifier.
- The synthetic hybrid abstracts are constructed by swapping exactly one sentence between two authors to create a clear "break" in consistency, rather than a partial or subtle mix.