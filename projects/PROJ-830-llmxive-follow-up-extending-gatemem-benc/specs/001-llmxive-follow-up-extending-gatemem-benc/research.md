# Research: llmXive follow-up: extending "GateMem: Benchmarking Memory Governance in Multi-Principal Shared-Memo"

## Research Question

Can a modular, CPU-tractable "Gatekeeper" governance layer (combining a lightweight intent classifier and rule engine) effectively reduce unauthorized information leakage (Access Control) in LLM agents without significantly degrading task performance (Utility), while offering lower computational overhead compared to integrated baselines?

## Hypotheses

1. **H1 (Security)**: The Gatekeeper configuration will demonstrate a statistically significant reduction in the Access Control score (unauthorized exposure rate) compared to the "Retrieval-only" baseline.
2. **H2 (Utility - Conditional)**: The Gatekeeper configuration will maintain **Conditional Utility** (task success rate among *allowed* queries) at a level non-inferior to the baseline, isolating the LLM's capability from the gatekeeper's filtering.
3. **H2b (Utility - Net)**: The **Overall Task Success Rate** (including blocked valid queries) will reflect the cost of False Positives, quantifying the real-world trade-off.
4. **H3 (Cost)**: The Gatekeeper configuration will exhibit a lower **Cost per Successful Task** (Total Time / Successful Tasks) compared to the "Retrieval-only" baseline, acknowledging that raw latency may be higher due to preprocessing overhead.
5. **H4 (Forgetting)**: The Gatekeeper configuration will achieve higher Forgetting compliance rates (successful data deletion) compared to the baseline, demonstrating effective enforcement of deletion requests.

## Dataset Strategy

The study relies on the **GateMem** dataset, which provides multi-domain episodes with explicit `leak-target` annotations, role definitions, and deletion request logs.

| Dataset Name | Source URL (Verified) | Usage | Key Variables |
|:--- |:--- |:--- |:--- |
| **GateMem** | ` | Primary evaluation data. Used to extract episodes, `leak-target` labels, roles, and deletion logs. | `intent`, `leak-target`, `role`, `deletion-log`, `ground-truth-answer`, `domain` |

**Domain Verification Strategy**:
- The implementation will programmatically verify the existence of all four required domain files (medical, office, education, household) by constructing expected URLs based on the verified repository structure.
- If any domain file is missing, the pipeline will **fail fast** with a clear error message: "Critical: Missing domain data for [domain]. Required for statistical validity."
- This prevents silent assumption failures and ensures the study is only run on complete data.

**Data Loading Strategy**:
- Use `huggingface_hub` to download the JSONL file directly to `data/raw/`.
- Parse JSONL into a Pandas DataFrame for processing.
- **Memory Constraint**: If the full dataset exceeds available RAM, the data will be processed in batches or streamed using `datasets` library's `iter` mode.

## Methodology

### 1. System Architecture

The evaluation compares three configurations:
1. **Gatekeeper (Proposed)**:
 - **Input**: User query + Memory context.
 - **Gatekeeper Layer**:
 - **Intent Classifier**: Frozen DistilBERT (CPU-tractable) to classify query intent (e.g., "leak attempt", "valid query", "deletion request").
 - **Rule Engine**: Regex-based logic to validate user roles against authorization boundaries and check deletion logs.
 - **Action**: If `deny`, return a safe response. If `allow`, pass to the LLM.
 - **LLM**: Same backbone as baselines (e.g., Llama-3-8B via CPU-compatible endpoint or local cache).
2. **Baseline A (Retrieval-only)**: Standard RAG pipeline without the Gatekeeper layer.
3. **Baseline B (Long-Context)**: LLM with full context window (no filtering).

### 2. Metrics Definition

To address the circularity of conflating gating decisions with LLM performance, we define two distinct utility metrics:

- **Access Control Score**: Rate of unauthorized exposure. Calculated as:
 $$ \text{Access Control} = \frac{\text{Count of episodes where leak occurred and was allowed}}{\text{Total episodes with leak-target}} $$
 *Source of Truth*: **Human-annotated `ground_truth_leak` labels** in GateMem. This metric measures the Gatekeeper's ability to block episodes *pre-labeled* as leaks, independent of the LLM's actual generation in that run, avoiding circularity.

- **Conditional Utility Score**: Task success rate **among allowed queries**. Calculated as:
 $$ \text{Utility}_{\text{allowed}} = \frac{\text{Count of allowed episodes where response matches ground-truth}}{\text{Total allowed episodes}} $$
 *Source of Truth*: Human-annotated `ground-truth-answer` in GateMem. This decouples the Gatekeeper's decision from the LLM's performance, answering "If the gatekeeper allows it, how well does the LLM perform?"

- **Overall Task Success Rate**: Measures the total impact of the Gatekeeper, including False Positives (valid queries blocked).
 $$ \text{Success}_{\text{overall}} = \frac{\text{Count of episodes where response matches ground-truth}}{\text{Total episodes}} $$
 *Note*: If a query is blocked (False Positive), it is counted as a failure here. This metric captures the real-world cost of the governance layer.

- **Forgetting Score**: Deletion compliance rate. Calculated as:
 $$ \text{Forgetting} = \frac{\text{Count of deletion requests successfully honored}}{\text{Total deletion request episodes}} $$
 *Source of Truth*: `deletion-log` and resulting response in GateMem.

### 3. Statistical Analysis Plan

- **Primary Test**: **Paired** Linear Mixed-Effects Model (LMM) to compare means between Gatekeeper and Baselines.
 - **Fixed Effects**: Configuration (Gatekeeper vs. Baseline), Domain.
 - **Random Effects**: Random intercept for **'Episode ID'** (to account for within-episode correlation across configurations) and **'Domain'** (to account for hierarchical data structure).
 - **Formula**: `score ~ configuration + (1 | episode_id) + (1 | domain)`
 - **Fallback Logic**: If the dataset contains only one domain (N_domains == 1), the 'Domain' random effect is removed, and the model simplifies to `score ~ configuration + (1 | episode_id)`. If 'Episode ID' is not unique across configurations (rare), a **paired t-test** (if normality holds) or **Wilcoxon signed-rank test** (if normality fails) is used as the constitutional fallback.
- **Assumption Checks**: Shapiro-Wilk test for normality of residuals ($\alpha=0.05$).
 - If normality holds: Parametric post-hoc tests (Tukey HSD).
 - If normality fails: Non-parametric alternatives (**Wilcoxon signed-rank** or **Kruskal-Wallis**).
- **Power Limitation**: Acknowledged. If sample size is insufficient for definitive conclusions, results will be framed as exploratory.

### 4. Computational Profiling

- **Instrumentation**: `time` module for wall-clock latency; `psutil` for peak RAM usage.
- **Measurement**: Recorded for every episode in both Gatekeeper and Baseline runs.
- **Aggregation**: Mean and standard deviation reported per configuration.
- **Cost Metric**: **Cost per Successful Task** = (Total Wall-Clock Time) / (Number of Successful Tasks). This accounts for the added preprocessing overhead of the Gatekeeper.

### 5. Failure Case Analysis

- **Sampling**: Simple random sample of 50 failure cases (stratified by domain if N > 50) with seed 42.
- **Definitions**:
 - *False Positive*: Valid query blocked by Gatekeeper (contributes to lower Overall Success, but not to Conditional Utility).
 - *False Negative*: Leak allowed by Gatekeeper.
- **Output**: Saved to `data/samples/failure_cases.json` for manual review.

## Decision Rationale

- **DistilBERT Choice**: Selected for CPU feasibility. Full BERT or larger models may exceed RAM constraints on the free-tier runner. DistilBERT provides a balance of performance and speed suitable for intent classification.
- **Regex Rule Engine**: Chosen to minimize overhead and avoid the need for a database, aligning with the "modular" and "lightweight" hypothesis.
- **LMM with Episode ID**: Preferred to account for the nested structure of data (episodes within domains) and the paired nature of the design (same episodes run under different configs), reducing Type I error risk.
- **Dual Utility Metrics**: Explicitly separating **Conditional Utility** from **Overall Success** resolves the circularity concern. It allows the study to claim "The Gatekeeper does not hurt the LLM's ability to answer valid queries" (Conditional Utility) while simultaneously reporting "The Gatekeeper reduces overall throughput due to blocking" (Overall Success), providing a complete trade-off picture.
- **CPU-Only Constraint**: The plan explicitly avoids GPU-dependent methods (e.g., 8-bit quantization requiring CUDA) to ensure the project can run on the specified GitHub Actions free-tier environment.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Dataset Missing Variables** | High | The plan relies on `leak-target` and `deletion-log`. If the verified dataset lacks these, the study cannot proceed. *Mitigation*: Code will validate schema presence immediately after download; fail fast with clear error if missing. |
| **Domain Availability** | High | If only one domain is available, LMM with Domain random effect is invalid. *Mitigation*: Code will verify all four domains exist. If not, it falls back to a paired t-test/Wilcoxon on the single domain, explicitly documenting the limitation. |
| **Memory Overflow** | High | Loading full LLM + DistilBERT + Data may exceed substantial memory capacity. *Mitigation*: Process data in batches; use `streaming=True` in datasets; unload LLM between batches if necessary. |
| **Statistical Power** | Medium | Small sample size may yield non-significant results. *Mitigation*: Report effect sizes and confidence intervals; frame conclusions as exploratory if p > 0.05. |
| **Ambiguous Annotations** | Medium | `leak-target` ambiguity may skew metrics. *Mitigation*: Log ambiguous cases as "validation errors" and exclude from metric calculation (per Edge Cases in spec). |
| **Circular Utility Metric** | High | Conflating gating and LLM performance. *Mitigation*: Implemented dual-metric approach (Conditional vs. Overall) as defined in Methodology section. |