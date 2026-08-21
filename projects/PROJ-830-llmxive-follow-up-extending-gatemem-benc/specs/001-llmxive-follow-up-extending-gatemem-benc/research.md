# Research: llmXive follow-up: extending "GateMem: Benchmarking Memory Governance in Multi-Principal Shared-Memo"

## 1. Problem Statement

The central research question is whether a modular, CPU-tractable governance layer (Gatekeeper) can effectively reduce unauthorized information leakage (improving Access Control) and handle deletion requests (Forgetting) without significantly degrading task performance (Utility) or incurring prohibitive computational costs, compared to integrated baselines (Retrieval-only, Long-Context).

## 2. Dataset Strategy

### Verified Datasets
The implementation relies exclusively on the following verified, programmatic sources:

| Dataset | Source URL | Format | Purpose |
|:--- |:--- |:--- |:--- |
| **GateMem (Medical)** | ` | JSONL | Primary evaluation data (Medical domain). |
| **GateMem (Office)** | ` | JSONL | Primary evaluation data (Office domain). |
| **GateMem (Education)** | ` | JSONL | Primary evaluation data (Education domain). |
| **GateMem (Household)** | ` | JSONL | Primary evaluation data (Household domain). |

*Note: The GateMem dataset is accessed via direct JSONL URLs provided. The implementation uses `datasets.load_dataset` with `streaming=True` to handle large files within the available RAM constraint.*

### Data Availability & Failure Mode
- **Strict Source Adherence**: No supplementary datasets (e.g., MixSub) are used. The GateMem benchmark is self-contained.
- **Failure Protocol**: If any of the canonical URLs above are unreachable, or if the dataset schema validation fails (missing required variables), the system **MUST** exit with error code 1 and log "CRITICAL: Data Source Invalid". No synthetic fallback or alternative dataset is permitted, in strict adherence to Constitution Principle I (Reproducibility) and FR-001.

### Dataset Fit & Variable Verification
The GateMem dataset contains all required variables for the analysis:
- **Outcome**: `leak_target` (binary: allowed/blocked), `ground_truth_success` (binary: success/failure).
- **Predictors**: `intent` (derived via Zero-Shot), `role` (user role), `domain` (context).
- **Covariates**: `deletion_log` (history of deletion requests), `memory_state` (current context).
- **Ground Truth**: Independent human annotations for leakage and deletion compliance, ensuring non-circular validation.

*Verification*: The dataset structure is verified against the `contracts/gatemem_episode.schema.yaml` before processing. Missing variables or schema mismatches trigger an immediate exit with error code 1.

## 3. Methodology

### 3.1. Gatekeeper Pipeline (Proposed Method)
1. **Intent Classification**: A **Zero-Shot Intent Classifier** (`facebook/bart-large-mnli`) is used with candidate labels: `['query', 'deletion', 'extraction', 'other']`.
 - *Rationale*: No public intent classifier exists for this specific schema. Zero-shot classification avoids the construct validity failure of using SST-2 (sentiment) or AG News (topic) models.
 - *Constraint*: Runs on CPU only (`device="cpu"`).
2. **Rule Engine**: A regex-based engine validates user roles against access policies and checks deletion logs.
3. **Secondary Leak Detector**: A keyword-based filter (e.g., "password", "secret", "SSN") acts as a safety net for leaks that bypass intent classification (e.g., leaks triggered by "query" intent).
4. **Filtering**: If the intent is "extraction" OR the keyword filter triggers, AND the role is unauthorized, memory access is blocked. Otherwise, the query proceeds to the LLM.

### 3.2. Baseline Pipelines
1. **Retrieval-only**: Standard RAG pipeline without governance filters.
2. **Long-Context**: LLM processes full context window without filtering.
*Both baselines use the same LLM backbone (e.g., Llama-3-8B) and retrieval index as the Gatekeeper to ensure a fair comparison.*

### 3.3. Metrics Calculation
- **Access Control**: Rate of unauthorized exposure.
 - *Denominator*: **Total Unauthorized Requests** (based on `ground_truth_leak` = True in dataset, independent of model decision).
 - *Numerator*: Number of these requests where the model **allowed** the leak.
- **Utility**: Task success rate.
 - *Denominator*: **Total Valid Requests** (based on `ground_truth_success` = True in dataset).
 - *Numerator*: **True Positives** (Requests Allowed by Gatekeeper AND `ground_truth_success` = True).
 - *Note*: This measures the proportion of *potentially successful* tasks that were actually successful, accounting for False Positives (valid queries blocked).
- **Conditional Utility**: Task success rate *among queries allowed by the Gatekeeper*.
- **Overall Task Success Rate**: Net success rate across all queries (including False Positives).
- **Forgetting**: Deletion compliance rate (Successful Deletions / Total Deletion Requests).

*Note: The definitions of denominators (Ground Truth based) prevent circular validation.*

### 3.4. Statistical Analysis
- **Primary Test**: **McNemar's Test** (paired binary data) for Access Control and Utility.
 - *Rationale*: Data is paired (same episode run under Gatekeeper and Baseline). Outcomes are binary (0/1). McNemar's is the correct test for this structure.
 - *Fallback*: If the number of discordant pairs is small (<25), use **Exact McNemar's Test** (binomial distribution). If zero discordant pairs exist, report raw counts and Odds Ratio without a p-value, labeling the result "Inconclusive due to lack of discordance".
- **Secondary/Exploratory Test**: **Fixed-Effects Logistic Regression (GLM)** with logit link (`score ~ method + Domain`).
 - *Rationale*: Accounts for hierarchical data structure. Fixed-effects for Domain are valid with a limited number of levels (unlike random effects in LMM). **LMM is NOT used** for binary data with N=4.
- **Multiple Comparison Correction**: Apply Benjamini-Hochberg procedure if multiple metrics are tested simultaneously.
- **Power Analysis**: Acknowledge power limitations if sample size is small; interpret results as exploratory if power < 0.8.

### 3.5. Computational Profiling
- **Metrics**: Wall-clock inference time, peak RAM usage.
- **Method**: `time` module and `psutil` for memory tracking.
- **Comparison**: Percentage reduction in cost for Gatekeeper vs. Baselines.
- **Power Analysis for Cost Detection**: With an expected sample size of N ~ 1000 per domain and the high variance of LLM inference (σ [deferred]), we have >80% power to detect a mean latency difference of 50ms (approx. [deferred] of baseline). This justifies the feasibility of the cost hypothesis test. The hypothesis that "decoupling governance reduces cost" is valid only if the Gatekeeper blocks a significant portion of queries, reducing LLM calls.

## 4. Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **Zero-Shot Classification** | No public intent classifier exists for this schema. Zero-shot with custom labels avoids construct validity failure of SST-2/AG News. |
| **McNemar's Test** | Correct statistical test for paired binary data (0/1). Wilcoxon is invalid for binary outcomes. |
| **Fixed-Effects GLM** | Correct mixed-model alternative for binary data with N=4 domains. LMM is invalid for small N. |
| **CPU-First Execution** | The project targets GitHub Actions free-tier (no GPU). Zero-shot BART is small enough for CPU inference. |
| **Strict Data Failure** | Adheres to Constitution Principle I (Reproducibility). No synthetic data or alternative datasets. |

## 5. Limitations & Construct Validity

- **Intent Classifier Proxy**: The Zero-Shot classifier is a proxy for "leak risk". It may fail to detect leaks triggered by non-"extraction" intents (e.g., prompt injection via "query").
- **Metric Interpretation**: The "Access Control" metric will be lower-bounded by the classifier's recall. Improvements in Access Control are relative to the *intent-filtered* subset. The secondary keyword filter mitigates this but does not eliminate the limitation.
- **Sample Size**: With only 4 domains, GLMM variance estimation may be unstable. Results will be interpreted with caution.
- **Cost Variance**: High variance in LLM inference times may obscure small cost differences; power analysis confirms detectability of 50ms differences.

## 6. Risk Assessment

| Risk | Mitigation |
|:--- |:--- |
| **Dataset Unavailable** | Hardcoded fallback to exit with error code 1; no synthetic stand-ins. |
| **GLMM Singularity** | Primary reliance on McNemar's Test. Fixed-Effects GLM is secondary/exploratory. |
| **Memory Overflow** | Use `streaming=True` and batch processing; profile memory usage continuously. |
| **Model Load Failure** | Retry download once; exit with error code 1 if retry fails (per spec edge cases). |