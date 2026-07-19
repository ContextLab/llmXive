# Specification: Zero-Shot Drift Detection for AgentDoG 1.5

## User Stories

### US-01: Zero-Shot Drift Scoring
**As a** security analyst,
**I want** the system to compute a "Drift Score" for each log entry based on its semantic distance from known safety patterns,
**So that** I can prioritize logs that deviate significantly from the norm for further review.

**Acceptance Criteria:**
- The system computes a cosine distance between log embeddings and taxonomy centroids.
- Empty or whitespace-only logs receive a Drift Score at the maximum distance and are flagged for review.
- The output CSV includes `log_id`, `drift_score`, and `review_flag`.
- Statistical validation shows a significant difference (p < 0.05, Cohen's d ≥ 0.5) between benign and novel attack logs.

### US-02: Human-in-the-Loop Validation
**As a** researcher,
**I want** to stratify logs for human annotation and validate the drift scores against human judgment,
**So that** I can refine the taxonomy and improve the detector's accuracy.

**Acceptance Criteria:**
- The system generates stratified bins (high/low drift) for annotation.
- Human annotations are ingested and merged with drift scores.
- Inter-annotator agreement (Cohen's Kappa) is calculated and must exceed a threshold indicative of substantial agreement.
- Logistic regression and Mann-Whitney U tests are performed to validate the drift score's predictive power.
- Annotation exports are blinded (no drift scores visible to annotators).

### US-03: Baseline Performance Comparison
**As a** system architect,
**I want** to compare the drift-based detector against a standard zero-shot LLM classifier,
**So that** I can evaluate the trade-off between computational efficiency and detection accuracy.

**Acceptance Criteria:**
- The system runs a zero-shot LLM classifier (gpto-mini) on a subset of logs.
- AUC-ROC and inference time metrics are calculated for both methods.
- The drift-based method is flagged as a "computationally efficient alternative" if its AUC is within 0.10 of the LLM baseline.

## Data Model
- **Log**: `log_id` (UUID), `text` (string), `timestamp` (datetime)
- **DriftResult**: `log_id` (UUID), `drift_score` (float), `review_flag` (boolean)
- **Annotation**: `log_id` (UUID), `label` (string), `annotator_id` (string)
- **Taxonomy**: `category` (string), `description` (string), `centroid_embedding` (array)

## Edge Cases
- **Empty Logs**: Assign a Drift Score and set `review_flag` to true.
- **Memory Limits**: Batch processing must respect system memory constraints; raise exception if exceeded.
- **Missing Data**: The system must fail loudly if required data (taxonomy, checksums) is missing.

## Performance Requirements
- **Memory**: Peak RAM < 7GB during batch processing.
- **Time**: Large-scale benchmark (100k+ logs) must complete in < 30 minutes.
- **Accuracy**: Drift score distribution must be statistically distinguishable between benign and attack logs (p < 0.05, Cohen's d ≥ 0.5).
