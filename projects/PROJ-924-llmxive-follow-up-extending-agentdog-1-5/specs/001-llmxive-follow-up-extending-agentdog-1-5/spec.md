# AgentDoG Follow-up: Extending AgentDoG 1.5 with Zero-Shot Drift Detection

## Overview
This project extends the AgentDoG 1.5 safety taxonomy with a zero‑shot drift detection mechanism. The system uses centroid embeddings of safety categories to score new logs for potential drift (novel harmful patterns). Embeddings are generated with the **all‑MiniLM‑L6‑v2** sentence‑transformer (CPU‑friendly) as mandated by the methodology.

## User Stories

### US-01: Zero‑Shot Drift Scoring
**As a** safety researcher,  
**I want** the system to compute drift scores for agent logs using centroid embeddings,  
**So that** I can identify potentially novel harmful patterns without manual labeling.

**Acceptance Criteria:**
1. System computes cosine distance between log embeddings and safety category centroids.  
2. Logs with drift scores **≥ 0.5** (a pre-registered operating point) are flagged for review (`review_flag = true`).  
3. Statistical validation shows significant separation between **human‑annotated novel** and **human‑annotated benign** logs (p < 0.05, rank-biserial correlation ≥ 0.5). *Note: this test depends on the human gold‑standard produced in **US‑02**.*  
4. Output includes `log_id`, `drift_score`, and `review_flag`.

### US-02: Human‑in‑the‑Loop Validation
**As a** safety engineer,  
**I want** to validate drift scores with human annotations,  
**So that** I can ensure the drift detection system is accurate and reliable.

**Acceptance Criteria:**
1. System stratifies logs into **high‑drift** (top [deferred] of `drift_score`) and **low‑drift** (bottom [deferred] of `drift_score`) bins.
2. System generates blinded annotation batches for human review (annotators do **not** see drift scores or bin assignments).  
3. Human annotations are ingested and merged.  
4. Mean pairwise Cohen's Kappa is computed between annotators; overall agreement must be **κ ≥ 0.6**.  
5. Logistic regression predicts the human “novel” label from `drift_score` (coefficient p‑value < 0.05, report AUC‑ROC) **and** a Mann‑Whitney U test compares `drift_score` distributions between human‑labeled **novel** vs **benign** logs (p < 0.05, rank-biserial correlation ≥ 0.5). To avoid range-restriction bias, these specific metrics must be computed on a random sample of logs across the full drift range.
6. A chi‑squared test evaluates whether the proportion of “novel” labels differs between the high‑drift and low‑drift bins (α = 0.05, null hypothesis must be rejected).  
7. Human annotators label each log with one of three categories: **“novel attack”**, **“known attack”**, or **“benign”**. Exactly three independent annotators are required. The binary “novel” gold standard is determined by majority vote: a log is labeled “novel” if the majority of annotators label it “novel attack”; otherwise, it is labeled “benign” (this includes “known attack” and “benign” labels).

### US-03: Baseline Performance Comparison
**As a** system architect,  
**I want** to compare the drift detection method against an LLM baseline,  
**So that** I can evaluate computational efficiency and accuracy trade‑offs.

**Acceptance Criteria:**
1. System runs a zero‑shot LLM classifier (**google/flan‑t5‑small**) on a subset of logs.  
2. AUC‑ROC is computed for both drift-based and LLM‑based methods **against the human‑annotated gold‑standard (novel vs benign)**.  
3. The drift‑based method is flagged as a “computationally efficient alternative” if its AUC is within **0.10** of the Flan‑T5 baseline AUC **and** the Flan‑T5 baseline achieves an AUC ≥ 0.70 (ensuring the baseline is sufficiently accurate).  
4. Per‑log inference latency of the drift method must be **≤ 0.5 ×** the latency of Flan‑T5; both latencies are measured on the same CPU hardware.  
5. System produces a final report summarizing all metrics, thresholds, and resource usage.

## Data Model

### Taxonomy
The AgentDoG safety taxonomy includes four categories:
- **Safety**: Harmful content that may cause physical or psychological harm.  
- **Privacy**: Exposure of personally identifiable information (PII).  
- **Bias**: Discriminatory or biased language targeting protected groups.  
- **Jailbreak**: Attempts to bypass safety filters or generate restricted content.

### Drift Score
- **log_id**: Unique identifier for the log entry.  
- **drift_score**: Cosine distance to the nearest category centroid (0.0 = identical, 2.0 = maximally different).  
- **review_flag**: Boolean indicating if `drift_score ≥ 0.5`.

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute cosine distance between a log embedding and each safety‑category centroid to produce `drift_score`. *(See US‑01)*
- **FR-002**: System MUST set `review_flag = true` for any log with `drift_score ≥ 0.5` (pre-registered operating point). *(See US‑01 AC2)*
- **FR-003**: System MUST generate embeddings using the **all‑MiniLM‑L6‑v2** sentence‑transformer. *(Methodology requirement)*
- **FR-004**: System MUST construct each category centroid from **≥ 100** curated example logs per category drawn from the verified dataset **`agentdog/safety-v1`**. *(See Data Model)*
- **FR-005**: System MUST stratify logs into high‑drift (top [deferred] of `drift_score`) and low‑drift (bottom [deferred] of `drift_score`) bins for annotation. *(See US‑02 AC1)*
- **FR-006**: System MUST collect human annotations from **three independent annotators**, each labeling logs as **“novel attack”**, **“known attack”**, or **“benign”**. Annotators are blinded to drift scores and bin membership. *(See US‑02)*
- **FR-007**: System MUST compute mean pairwise Cohen's Kappa between annotators; overall agreement must be **κ ≥ 0.6**. *(See US‑02 AC4)*
- **FR-008**: System MUST evaluate separation between human‑labeled novel and benign logs using a Mann‑Whitney U test (p < 0.05) and report rank-biserial correlation ≥ 0.5. *(See US‑01 AC3, US‑02 AC5)*
- **FR-009**: System MUST fit a logistic regression model predicting the human “novel” label from `drift_score`; report coefficient p‑value < 0.05 and AUC‑ROC. *(See US‑02 AC5)*
- **FR-010**: System MUST run a zero‑shot **google/flan‑t5‑small** classifier on the same log set and compute AUC‑ROC against the human gold‑standard. *(See US‑03 AC1)*
- **FR-011**: System MUST compare inference latency: drift method per‑log latency ≤ 0.5 × Flan‑T5 latency. *(See US‑03 AC4)*
- **FR-012**: System MUST enforce resource limits of **≤ 7 GB RAM** and **≤ 6 hours** total wall‑clock time on GitHub Actions free‑tier. *(Constitution Principle VII)*
- **FR-013**: System MUST produce a final report summarizing all metrics, thresholds, and resource usage. *(See US‑03 AC5)*
- **FR-014**: System MUST acquire a **novel‑log corpus** of **≥ 500** post‑2025 agent interaction logs from public GitHub issue threads (e.g., `github.com/*/issues`) to ensure exposure to emergent attack patterns. *(Scope requirement from idea)*
- **FR-015**: System MUST perform a chi‑squared test on the distribution of “novel” labels across the high‑drift and low‑drift bins; the test must reject the null hypothesis at **α = 0.05**. *(See US‑02 AC6)*
- **FR-016**: System MUST verify that the Flan‑T5 baseline achieves an AUC‑ROC ≥ 0.70 on the human‑annotated gold‑standard before it is used as the reference for the drift‑method efficiency comparison. *(Ensures baseline validity)*
- **FR-017**: System MUST collect annotations for a random sample of **≥ 100 logs** across the full drift range to provide an unbiased estimate of AUC-ROC and regression coefficients. *(See US-02 AC5)*

### Key Entities *(include if feature involves data)*

- **LogEntry**: Represents a single agent interaction log; attributes include `log_id`, raw text, and metadata.  
- **Centroid**: Mean embedding vector for each safety category.  
- **DriftScoreRecord**: Tuple (`log_id`, `drift_score`, `review_flag`).  

## Success Criteria

- **SC-001**: US‑01 is considered successful when FR‑001 – FR‑004 and FR‑008 are satisfied and statistical thresholds (p < 0.05, rank-biserial correlation ≥ 0.5) are met. *(See US‑01)*
- **SC-002**: US‑02 is successful when FR‑006 – FR‑009, FR‑015, and FR-017 are satisfied, mean pairwise Cohen's Kappa ≥ 0.6, logistic regression coefficient p‑value < 0.05, Mann‑Whitney U test meets its thresholds, and the chi‑squared test rejects at α = 0.05. *(See US‑02)*
- **SC-003**: US‑03 is successful when FR‑010 – FR‑011 and FR‑016 are satisfied, drift AUC‑ROC is within **0.10** of Flan‑T5 AUC‑ROC, Flan‑T5 baseline AUC ≥ 0.70, and latency criterion holds. *(See US‑03)*
- **SC-004**: Resource usage meets FR‑012 (RAM ≤ 7 GB, runtime ≤ 6 h). *(Constitution Principle VII)*

## Assumptions

- Users have stable internet connectivity to fetch datasets and models.  
- Mobile support is out of scope for v1.  
- Existing AgentDoG taxonomy and `agentdog/safety-v1` dataset are publicly accessible and verified.  
- The embedding model **all‑MiniLM‑L6‑v2** fits within the RAM budget on CPU.  

## Execution Pipeline
1. **Data Loading** (US‑01, US‑02, US‑03, FR‑014): Fetch AgentDoG taxonomy, the verified dataset `agentdog/safety-v1`, and acquire the novel‑log corpus (≥ 500 logs).  
2. **Taxonomy Building** (FR‑003, FR‑004): Generate embeddings for taxonomy examples using **all‑MiniLM‑L6‑v2** and compute category centroids from ≥ 100 examples per category.  
3. **Drift Scoring** (FR‑001, FR‑002): Compute cosine distance between each log embedding and all centroids; record the minimum as `drift_score` and set `review_flag` per FR‑002.  
4. **Stratification & Sampling** (FR‑005, FR-017): Bin logs into high‑drift (top [deferred]) and low‑drift (bottom [deferred]) groups, and select a random sample of ≥ 100 logs across the full distribution for unbiased validation.
5. **Human Validation** (FR‑006‑FR‑009, FR‑015, FR-017): Collect blinded annotations from three annotators, derive binary gold standard via majority vote, compute mean pairwise Cohen's Kappa, run Mann‑Whitney U and logistic regression analyses (using the random sample), and perform the chi‑squared test on label distribution across bins.  
6. **Baseline Comparison** (FR‑010‑FR‑011, FR‑016): Run **google/flan‑t5‑small** on the same logs, compute AUC‑ROC against the human gold‑standard, verify baseline AUC ≥ 0.70, and measure per‑log latency for both methods.  
7. **Final Report** (FR‑013): Compile metrics, thresholds, resource usage, and analysis results into a comprehensive report.

## Resource Constraints
- **Maximum RAM**: **7 GB** (Constitution Principle VII)  
- **Maximum runtime**: **6 hours** wall‑clock time on GitHub Actions free‑tier (Constitution Principle VII)  
- **Model**: **google/flan‑t5‑small** (CPU‑only) – fits within the RAM budget when combined with all‑MiniLM‑L6‑v2 embeddings.

## Success Metrics
- US‑01: p < 0.05 and rank-biserial correlation ≥ 0.5 for drift‑score separation; κ ≥ 0.6 between annotators.  
- US‑02: Mean pairwise Cohen's Kappa ≥ 0.6; logistic regression coefficient p < 0.05; Mann‑Whitney U p < 0.05, rank-biserial correlation ≥ 0.5; chi‑squared test rejects at α = 0.05.  
- US‑03: Drift AUC within 0.10 of Flan‑T5 baseline AUC; Flan‑T5 baseline AUC ≥ 0.70; drift latency ≤ 0.5 × Flan‑T5 latency.  