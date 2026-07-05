# Feature Specification: Statistical Analysis of Topic Drift in Academic Abstracts

**Feature Branch**: `001-topic-drift-analysis`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of Publicly Available Academic Paper Abstracts for Topic Drift"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition & Preprocessing Pipeline (Priority: P1)

As a researcher, I need to download abstracts from arXiv and PubMed APIs, filter by field and publication year (2000–2024), and preprocess them with tokenization, stopword removal, and lemmatization so that I have a clean, reproducible corpus for topic modeling.

**Why this priority**: This is the foundational step without which no analysis can proceed. All downstream components depend on having valid, preprocessed text data.

**Independent Test**: Can be fully tested by downloading a sample of abstracts from each source, preprocessing them with window-specific stopword lists, and verifying that the output CSV contains ≥95% of total fetched records (passing API validation) with ≥20 tokens after preprocessing.

**Acceptance Scenarios**:

1. **Given** valid API credentials and field tags, **When** the system queries arXiv and PubMed for abstracts from 2000–2024, **Then** the system attempts to fetch ≥10,000 abstracts per source and successfully retrieves all available abstracts up to the API limit, preserving publication year and field metadata.
2. **Given** a raw abstract corpus, **When** the system applies window-specific tokenization, stopword removal, and lemmatization using NLTK/spaCy, **Then** at least 95% of abstracts retain ≥20 tokens after preprocessing.

---

### User Story 2 - Topic Modeling & Temporal Analysis (Priority: P2)

As a researcher, I need to fit LDA topic models with k=10 topics on 5-year temporal windows and compute topic proportion vectors so that I can measure how research themes evolve across time periods.

**Why this priority**: This implements the core research methodology. Without topic modeling, the drift measurement cannot be computed.

**Independent Test**: Can be fully tested by fitting an LDA model on a sampled subset, validating k=10 via the elbow method (coherence vs. k), extracting topic proportions, and verifying that all topics have non-zero probability mass and coherence score ≥0.4 using the c_v metric.

**Acceptance Scenarios**:

1. **Given** preprocessed abstracts partitioned into 5-year windows (2000–2004, 2005–2009, 2010–2014, 2015–2019, 2020–2024), **When** the system validates k=10 via the elbow method and fits LDA with k=10 topics and max_iter=20, **Then** each window produces a topic proportion vector summing to 1.0 with no NaN values.
2. **Given** an LDA model, **When** the system computes topic coherence using the c_v metric, **Then** the coherence score is ≥0.4; if <0.4, the run is flagged for discarding per the validation protocol.

---

### User Story 3 - Statistical Testing & Visualization (Priority: P3)

As a researcher, I need to compute Jensen-Shannon divergence between consecutive window topic distributions, apply permutation resampling (n=1000) for null distributions, and generate visualizations so that I can determine whether observed drift is statistically significant.

**Why this priority**: This validates the findings with statistical rigor and produces the final outputs. It depends on US-2 completing successfully.

**Independent Test**: Can be fully tested by running a permutation test (shuffling abstracts across windows, n=1000) on a small dataset and verifying that p-values are computed, confidence intervals have width ≤0.2, and PNG figures are saved.

**Acceptance Scenarios**:

1. **Given** topic proportion vectors for two consecutive windows, **When** the system computes Jensen-Shannon divergence using `scipy.spatial.distance.jensenshannon` with base=2, **Then** the divergence value is ≥0.0 and ≤1.0 (normalized range).
2. **Given** an observed divergence value, **When** the system applies a permutation test (shuffling abstracts across windows, n=1000) to generate a null distribution, **Then** p-values are computed and 95% bootstrapped confidence intervals have a width ≤0.2.
3. **Given** topic proportion vectors across all windows, **When** the system generates line plots using matplotlib, **Then** figures are saved as PNG files with ≥300 DPI resolution.

---

### Edge Cases

- What happens when arXiv or PubMed API returns rate-limited responses (HTTP 429)? The system MUST implement exponential backoff with at most 3 retry attempts per endpoint.
- How does system handle abstracts with <20 tokens after preprocessing? The system MUST exclude these records and log the exclusion count to the reproducibility manifest.
- What happens when LDA coherence score <0.4 for a window? The system MUST flag the run, record the coherence value, and prevent downstream divergence calculations for that window.
- How does system handle empty windows (e.g., no abstracts in a 5-year period)? The system MUST skip the window and log the gap in the reproducibility manifest.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download abstracts from arXiv (http://export.arxiv.org/oai2) and PubMed (https://pubmed.ncbi.nlm.nih.gov/) APIs filtering by field tags and publication year 2000–2024 (See US-1)
- **FR-002**: System MUST preprocess abstracts using tokenization, stopword removal, and lemmatization via NLTK/spaCy, excluding records with <20 tokens after preprocessing (See US-1). *Rationale: A token count sufficient for stable LDA topic distribution estimation in short-text domains is the community-standard minimum..*
- **FR-003**: System MUST fit Latent Dirichlet Allocation (LDA) with k=10 topics and max_iter=20 iterations using scikit-learn (See US-2)
- **FR-004**: System MUST partition abstracts into 5-year windows (2000–2004, 2005–2009, 2010–2014, 2015–2019, 2020–2024) and compute topic proportion vectors for each window (See US-2)
- **FR-005**: System MUST compute Jensen-Shannon divergence between consecutive window topic distributions using `scipy.spatial.distance.jensenshannon` with base=2 (See US-2)
- **FR-006**: System MUST validate topic quality using coherence scoring (c_v metric) and discard runs with coherence <0.4 (See US-2)
- **FR-007**: System MUST apply a permutation test (shuffling abstracts across time windows, n=1000 permutations) to generate a null distribution for divergence values, testing against the hypothesis of no drift (See US-3)
- **FR-008**: System MUST apply multiple-comparison correction (e.g., Benjamini-Hochberg) when testing >1 hypothesis across the 4 consecutive window pairs (See US-3)
- **FR-009**: System MUST perform sensitivity analysis sweeping the coherence threshold over {0.35, 0.40, 0.45} and report how inconsistency rates vary across cutoffs (See US-3). *Rationale: Sensitivity analysis is required to ensure drift findings are robust to the coherence threshold selection.*
- **FR-010**: System MUST log all random seeds, parameter settings, and dataset versions in a single JSON manifest file for reproducibility (See US-3)
- **FR-011**: System MUST execute all analysis on CPU-only infrastructure without GPU/CUDA dependencies (See US-3). *Rationale: CPU-only execution ensures reproducibility across standard research hardware where GPU access is not guaranteed.*
- **FR-012**: System MUST complete total wall-clock time ≤6 hours on 2 CPU cores with ≤7 GB RAM usage (See US-3). *Rationale: 6-hour/2-core/7GB target ensures feasibility on standard research workstations without HPC.*
- **FR-013**: System MUST validate the choice of k=10 topics using the elbow method (intrinsic coherence vs. k) or held-out likelihood; if k=10 is not optimal, the system MUST select the k with maximum coherence within a 10% tolerance of the global maximum (See US-2)
- **FR-014**: System MUST apply window-specific stopword lists and lemmatization rules to account for language drift over time (See US-1)

### Key Entities

- **Abstract Record**: Represents a single academic paper abstract with attributes: id, source (arXiv/PubMed), publication_year, field_tag, raw_text, processed_text, token_count
- **Topic Vector**: Represents topic proportion distribution for a temporal window with attributes: window_start, window_end, topic_0 through topic_9 (each ≥0.0, sum=1.0), coherence_score
- **Divergence Measurement**: Represents Jensen-Shannon divergence between two windows with attributes: window_pair (e.g., "2000-2004_to_2005-2009"), divergence_value, p_value, confidence_interval_lower, confidence_interval_upper, significance_flag

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Topic coherence score is measured against the validated threshold of ≥0.4 (c_v metric) (See US-2)
- **SC-002**: Wall-clock runtime is measured against the 6-hour constraint on 2 CPU cores (See US-3)
- **SC-003**: Memory usage is measured against the 7 GB RAM limit during peak LDA execution (See US-3)
- **SC-004**: Statistical significance (p-value) is measured against the p < 0.05 threshold with permutation-based 95% confidence intervals (See US-3)
- **SC-005**: Reproducibility is measured against the completeness of the JSON manifest (≥10 logged parameters including random seeds) (See US-3)

## Assumptions

- arXiv and PubMed APIs remain accessible and rate limits permit ≥10,000 abstract downloads per source within the 6-hour window
- The arXiv/PubMed dataset contains sufficient abstracts in each 5-year window to support LDA fitting with k=10 topics (minimum 500 abstracts per window)
- k=10 topics is sufficient to capture meaningful variation in research themes for statistics/machine learning fields
- 5-year windows provide adequate sample sizes for stable topic proportion estimates
- CPU-only execution is feasible for LDA with max_iter=20 and permutation n=1000 on a sampled subset of the corpus
- All cited URLs (http://export.arxiv.org/oai2, https://pubmed.ncbi.nlm.nih.gov/) remain valid throughout the project lifecycle
- The research design is observational (no random assignment); all findings will be framed as associational rather than causal
- Multiple hypothesis tests across window pairs require family-wise error rate correction per methodological soundness requirements
- 20 tokens is the minimum for stable LDA topic distribution estimation in short-text domains
- Sensitivity analysis is required to ensure drift findings are robust to the coherence threshold selection
- CPU-only execution ensures reproducibility across standard research hardware where GPU access is not guaranteed
- 6-hour/2-core/7GB target ensures feasibility on standard research workstations without HPC
- Window-specific preprocessing is required to prevent language drift from mimicking topic drift