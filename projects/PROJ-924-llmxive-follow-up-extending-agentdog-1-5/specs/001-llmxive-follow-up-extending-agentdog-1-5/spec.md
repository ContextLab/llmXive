# AgentDoG Follow-up: Extending AgentDoG 1.5 with Zero-Shot Drift Detection

## Overview
This project extends the AgentDoG 1.5 safety taxonomy with a zero-shot drift detection mechanism. The system uses centroid embeddings of safety categories to score new logs for potential drift (novel harmful patterns).

## User Stories

### US-01: Zero-Shot Drift Scoring
**As a** safety researcher,
**I want** the system to compute drift scores for agent logs using centroid embeddings,
**So that** I can identify potentially novel harmful patterns without manual labeling.

**Acceptance Criteria:**
1. System computes cosine distance between log embeddings and safety category centroids.
2. Logs with drift scores above a threshold are flagged for review.
3. Statistical validation shows significant separation between benign and novel logs (p < 0.05, Cohen's d ≥ 0.5).
4. Output includes `log_id`, `drift_score`, and `review_flag`.

### US-02: Human-in-the-Loop Validation
**As a** safety engineer,
**I want** to validate drift scores with human annotations,
**So that** I can ensure the drift detection system is accurate and reliable.

**Acceptance Criteria:**
1. System stratifies logs into high/low drift bins.
2. System generates blinded annotation batches for human review.
3. Human annotations are ingested and merged.
4. Cohen's Kappa is computed between annotators (κ ≥ 0.6).
5. Logistic regression and Mann-Whitney U tests validate drift score correlation with human labels.

### US-03: Baseline Performance Comparison
**As a** system architect,
**I want** to compare the drift detection method against an LLM baseline,
**So that** I can evaluate computational efficiency and accuracy trade-offs.

**Acceptance Criteria:**
1. System runs a zero-shot LLM classifier (google/flan-t5-small) on a subset of logs.
2. AUC-ROC is computed for both drift-based and LLM-based methods.
3. The drift-based method is flagged as a 'computationally efficient alternative' if its AUC is within 0.10 of the Flan-T5 baseline.
4. Inference time is measured and compared between methods.

## Data Model

### Taxonomy
The AgentDoG safety taxonomy includes four categories:
- **Safety**: Harmful content that may cause physical or psychological harm.
- **Privacy**: Exposure of personal identifiable information (PII).
- **Bias**: Discriminatory or biased language targeting protected groups.
- **Jailbreak**: Attempts to bypass safety filters or generate restricted content.

### Drift Score
- **log_id**: Unique identifier for the log entry.
- **drift_score**: Cosine distance to the nearest centroid (0.0 = identical, 2.0 = maximally different).
- **review_flag**: Boolean indicating if the score exceeds the threshold.

## Execution Pipeline
1. **Data Loading**: Fetch AgentDoG taxonomy and validation datasets.
2. **Taxonomy Building**: Generate centroid embeddings for safety categories.
3. **Drift Scoring**: Compute drift scores for all logs.
4. **Stratification**: Bin logs by drift score for annotation.
5. **Human Validation**: Ingest annotations and compute agreement metrics.
6. **Baseline Comparison**: Run Flan-T5 and compare AUC-ROC.
7. **Final Report**: Generate comparison report with statistical validation.

## Resource Constraints
- Maximum RAM: GB (GitHub Actions free-tier)
- Maximum runtime: a bounded duration suitable for benchmark tasks
- Model: google/flan-t5-small (substituted from gpt-4o-mini due to memory constraints)

## Success Metrics
- US-01: p < 0.05 and Cohen's d ≥ 0.5 for drift score separation.
- US-02: Cohen's Kappa ≥ 0.6 between annotators.
- US-03: Drift AUC within 0.10 of Flan-T5 baseline AUC.
