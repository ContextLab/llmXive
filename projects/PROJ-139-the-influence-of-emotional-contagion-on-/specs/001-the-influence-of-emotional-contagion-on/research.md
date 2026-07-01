# Research: Emotional Contagion in Online Forums

## Research Question

Does the emotional tone of early contributions (seed posts) in online forums bias subsequent participants, thereby affecting the quality (consensus alignment, diversity) and efficiency (time-to-decision) of collective decisions?

## Dataset Strategy

The study utilizes pre-processed, verified datasets from HuggingFace to ensure reproducibility and avoid API rate limits. **Note**: Explicit 'expert-verified' ground truth is not present in these raw datasets. We use 'Solved' flags (in AskScience) as a *proxy* for ground truth, with a strict validation requirement.

| Dataset Name | Source URL (Verified) | Usage | Variables Needed |
|:--- |:--- |:--- |:--- |
| **AskScience** | ` (and variants) | Primary source for 'decision-making' threads. 'Solved' flag used as proxy for ground truth. | `text`, `timestamp`, `author`, `parent_id`, `subreddit`, `is_solved` (if available). |
| **FDR** | ` | Secondary source for sentiment/structure. **NOT** used for decision quality validation due to lack of decision metadata. | `text`, `timestamp`, `author`, `parent_id`. |

**Dataset-Variable Fit Assessment**:
- **Sentiment**: All datasets contain `text` fields. VADER can process these directly.
- **Decision Points**: AskScience is selected for its question-answer structure. 'Solved' flags are used as a proxy for 'ground truth' (external validation), acknowledging this is an internal heuristic, not a true external benchmark.
- **Ground Truth**: The spec requires ≥30% of threads to have verifiable ground truth. **Critical Note**: If the 'Solved' proxy yields <30% valid threads, the study **cannot** satisfy SC-006. The plan does NOT pivot to 'Consensus Alignment' as a substitute for ground truth. Instead, it reports the failure to meet SC-006 and restricts primary analysis to the valid subset.
- **Missing Variables**: If 'time-to-decision' metadata is absent, it is computed from `timestamp` deltas.

## Methodology

### 1. Data Extraction & Preprocessing (FR-001, FR-002)
- **Source**: Load JSONL/Parquet from verified HuggingFace URLs. **Fallback**: If APIs (Pushshift/Reddit) are available, use them first (FR-001). If APIs fail, load from archives.
- **Filtering**: Select threads with ≥3 top-level posts (seed posts). Exclude threads with <3 seeds.
- **Seed Identification**: Extract the first 3 top-level comments per thread as `seed_posts`.
- **Reply Selection**: Extract the **first 5 replies** for sentiment trajectory analysis. Threads with <5 replies are excluded from contagion analysis (to ensure vector equality for the slope metric).

### 2. Sentiment Analysis (FR-003, FR-004)
- **Tool**: VADER (NLTK) for CPU feasibility (Assumption 3).
- **Metric**: Compound score ∈ [-1.0, 1.0].
- **Contagion Index**:
 - Compute $S_{seed}$ (mean of 3 seed posts).
 - Compute $S_{reply\_i}$ for the first 5 replies.
 - Fit a linear regression of $S_{reply}$ vs. Position (1..5) to get the **Slope**.
 - Calculate Pearson correlation ($r$) between $S_{seed}$ and the **Slope** across threads.
 - *Constraint*: Threads with <5 replies are excluded. This avoids the circularity of correlating X with (Y-X) and ensures a temporal separation (early trend predicts final state).

### 3. Decision Quality Metrics (FR-005)
- **Agreement Proportion**: Ratio of replies agreeing with the **Seed Sentiment** direction (Positive/Negative/Neutral). This breaks tautology with 'Majority Stance'.
- **Shannon Entropy**: $H = -\sum p_i \log p_i$ calculated on sentiment buckets (Positive, Neutral, Negative) to measure diversity.
 - **Hypothesis Direction**: High emotional contagion is hypothesized to lead to **low entropy** (forced consensus, low diversity). Low contagion is expected to allow **high entropy** (diverse/polarized opinions).
 - **Statistical Test**: The Wald test will evaluate the association between the Contagion Index and Entropy. The alternative hypothesis is directional: $H_1: \beta_{contagion} < 0$ (negative coefficient implies higher contagion leads to lower entropy). If a two-tailed test is used, the interpretation will strictly adhere to this pre-registered directional expectation.
- **External Validation**:
 - If 'Solved' flag exists: Compare 'Majority Consensus' (mode of reply sentiments) to 'Solved' label. Score = 1.0 if match, 0.0 otherwise.
 - If no 'Solved' flag: Metric set to `null`.
 - **Validity Check**: Analysis valid only if ≥30% of threads have a valid 'Solved' flag. If <30%, report failure to meet SC-006; do not pivot to internal proxies.

### 4. Statistical Modeling (FR-006, FR-007)
- **Model**: Generalized Linear Mixed Models (GLMM).
 - **Unit of Analysis**: Thread.
 - **Fixed Effects**: Contagion Index (Slope correlation), Thread Length, Time-to-Decision.
 - **Random Effects**: **Subreddit** (random intercept) to account for platform-level clustering. (Thread ID is the unit of analysis, so no random intercept for it).
 - **Link Functions**:
 - Beta regression (logit link) for bounded outcomes (Agreement Proportion).
 - Gaussian or Gamma (log link) for continuous outcomes (Entropy, Time-to-Decision).
- **Significance**: Wald tests ($\alpha=0.05$).
- **Multiple Comparison Correction**: Benjamini-Hochberg FDR applied if ≥3 hypotheses are tested (SC-003).

### 5. Sensitivity Analysis (FR-008)
- Sweep agreement cutoff: $\{0.5, 0.6, 0.7\}$.
- Sweep entropy threshold: $\{0.2, 0.4, 0.6\}$.
- **FP/FN Rates**: For threads with valid ground truth, compute False Positive (Consensus==True, GroundTruth==False) and False Negative (Consensus==False, GroundTruth==True) rates. Report stability of these rates across thresholds.

## Statistical Rigor & Assumptions

- **Causal Framing**: The study is **observational** (Assumption 4). No random assignment of sentiment. All claims will be framed as **associational**.
- **Collinearity**: If sentiment correlates strongly with topic keywords, Variance Inflation Factor (VIF) will be computed. Joint relationships will be described descriptively, not as independent effects (Assumption 7).
- **Power Analysis**: Sample size ($N=500$) is a target. An explicit acknowledgement of power limitations will be included if $N < 100$ (Assumption 5).
- **Multiple Comparisons**: Mandatory correction (SC-003) to control family-wise error rate.
- **Ground Truth Limitation**: Explicitly acknowledge that 'Solved' flags are a proxy, not true external ground truth. If the proxy fails the 30% threshold, the study reports this as a limitation, not a pivot.
- **Directional Hypothesis**: The entropy analysis is pre-registered with a directional expectation (Contagion $\uparrow$ $\Rightarrow$ Entropy $\downarrow$).

## Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (multi-core CPU, 7 GB RAM).
- **Strategy**:
 - **No GPU**: VADER and GLMM (`statsmodels`) are CPU-optimized.
 - **Data Sampling**: If the raw dataset exceeds a size threshold that exceeds available memory, a stratified sample of threads will be drawn to fit memory.
 - **Runtime**: Target <6 hours.
 - **Libraries**: `pandas`, `nltk`, `scikit-learn`, `statsmodels`, `scipy` (all CPU-wheel compatible).

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Ground Truth Unavailable** | >70% of threads lack 'Solved' flags, invalidating FR-005/SC-006. | Report failure to meet SC-006. Do not pivot to 'Consensus Alignment' as a substitute for ground truth. Restrict primary analysis to valid subset. |
| **Dataset Mismatch** | Datasets lack 'decision point' metadata. | Use 'Solved' flag heuristic in AskScience. FDR used for sentiment only. |
| **GLMM Convergence** | Complex models fail to converge on small N. | Simplify to Fixed Effects models with robust standard errors if GLMM fails. |
| **API Rate Limits** | Pushshift/Reddit API blocked. | Rely on pre-downloaded HuggingFace dumps (Verified Datasets) as fallback. |
| **Directional Ambiguity** | Entropy interpretation is unclear. | Explicitly define hypothesis: Contagion $\uparrow$ $\Rightarrow$ Entropy $\downarrow$. Use one-tailed tests or pre-registered interpretation. |