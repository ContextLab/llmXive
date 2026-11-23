# Requirements Specification

This document outlines the functional and non-functional requirements for the llmXive Drift Detection system.

## Functional Requirements

### FR-01: Zero-Shot Drift Scoring
- The system shall compute a drift score for each log entry based on its cosine distance to known taxonomy centroids.
- The system shall handle empty or whitespace-only logs by assigning a default drift score of 2.0 and setting a review flag.
- The system shall export results to a CSV file with columns: `log_id`, `drift_score`, `review_flag`.

### FR-02: Taxonomy Management
- The system shall download the OWASP Top LLM taxonomy from Hugging Face.
- The system shall map OWASP categories to the AgentDoG 1.5 safety taxonomy.
- The system shall compute centroid embeddings for each mapped category using `all-MiniLM-L6-v2`.

### FR-03: Human-in-the-Loop Validation
- The system shall stratify logs into top and bottom percentiles based on drift scores.
- The system shall generate blinded annotation batches (removing drift scores) for human review.
- The system shall ingest human annotations and merge them with drift scores.
- The system shall calculate inter-annotator agreement (Kappa) and fail if < 0.6.

### FR-04: Baseline Comparison
- The system shall run a local zero-shot LLM classifier (`facebook/bart-large-mnli`) on annotated logs.
- The system shall compare the AUC-ROC of the drift score method against the baseline.
- The system shall flag the drift score method as a "computationally efficient alternative" if the AUC difference is ≤ 0.10.

### FR-05: Statistical Validation
- The system shall calculate p-values and Cohen's d to validate the distinguishability of drift scores between benign and attack logs.
- The system shall perform logistic regression and Mann-Whitney U tests on merged annotations.

## Non-Functional Requirements

### NFR-01: Performance
- The system shall process logs within a 7GB RAM limit.
- The system shall complete a large-scale benchmark within 30 minutes.

### NFR-02: Reproducibility
- All random seeds shall be configurable and fixed by default.
- Inference results shall be cached to ensure reproducibility.
- No external API calls shall be made for drift scoring or baseline comparison.

### NFR-03: Data Integrity
- All raw data files shall be verified against checksums.
- The system shall fail loudly if real data fetches fail, without synthetic fallbacks.

### NFR-04: Usability
- The system shall provide a clear command-line interface for running the pipeline.
- Documentation shall include a quickstart guide and API reference.

### NFR-05: Extensibility
- The system shall be modular, allowing for easy addition of new taxonomies or models.
- Configuration shall be centralized in `config.py`.

## Constraints

- **Compute**: Must run on CPU (GPU optional but not required).
- **Memory**: Max 7GB RAM usage.
- **Data**: Must use real data sources; no synthetic data for validation.
- **Dependencies**: Must use only pip-installable packages listed in `requirements.txt`.

## Acceptance Criteria

- US-01: Drift scores are statistically distinguishable between benign and attack logs (p < 0.05, Cohen's d ≥ 0.5).
- US-02: Human annotators achieve Kappa > 0.6 on stratified logs.
- US-03: Drift score method is computationally efficient compared to the baseline (AUC difference ≤ 0.10).
- Full pipeline runs end-to-end without errors on the reference dataset.