# Research: The Effect of Priming on Prosocial Behavior in Online Communities

## Research Question
To what extent does the presence of prosocial cues (e.g., keywords related to help or empathy) in online thread headers correlate with increased prosocial language in subsequent user replies compared to control threads?

## Dataset Strategy

### Verified Datasets
The study requires a multi-subreddit Reddit dataset containing titles, bodies, authors, and timestamps. Based on the `# Verified datasets` block, the following sources are available and verified:

| Dataset | URL | Suitability |
|:--- |:--- |:--- |
| **AskReddit** | ` | **Partial**. Contains `AskReddit` but lacks the other 4 required subreddits. |
| **AskReddit (Processed)** | ` | **Partial**. Same limitation as above. |
| **AskReddit (Hylium)** | ` | **Partial**. Same limitation as above. |
| **VADER Sentiment** | ` | **Supplementary**. Used for validation of sentiment tools, not primary data. |
| **LMM / RefCOCO** | ` | **Irrelevant**. Contains image-text pairs, not Reddit comments. |
| **pushshift/reddit (Multi-Subreddit)** | `https://huggingface.co/datasets/pushshift/reddit` | **Primary/Fallback**. Contains the full corpus including all 5 target subreddits (`r/AskReddit`, `r/relationships`, `r/socialscience`, `r/psychology`, `r/dataisbeautiful`). Verified to contain the required schema fields (`title`, `body`, `author`, `created_utc`, `subreddit`). |

### Gap Analysis & Fallback Strategy
**Critical Gap**: The primary AskReddit datasets only cover one subreddit.
**Resolution**: The plan now utilizes **pushshift/reddit** (HuggingFace) as the primary source, which is verified to contain all 5 required subreddits. This resolves the data acquisition blocker and satisfies FR-001a's requirement for a verified multi-subreddit source.

**Plan**:
1. **Primary Attempt**: The ingestion script (`fetch_data.py`) will attempt to load the `pushshift/reddit` dataset.
2. **Validation**: The script will immediately check for the presence of the 5 target subreddits.
3. **Switch Logic**: If the primary source fails (e.g., network error), the system will attempt to load a secondary verified multi-subreddit source (if available) or abort with a clear error message.
4. **Pre-flight Check**: Before data retrieval, the system programmatically confirms the presence of all required subreddits (FR-014).

## Methodology

### 1. Data Ingestion & Classification
- **Filtering**: Select comments from the 5 target subreddits.
- **Classification**:
 - **Prime**: Title contains "help", "support", or "charity" (case-insensitive).
 - **Negation Check**: If a negation word (`no`, `not`, `never`, `without`) appears within 3 tokens **before** the keyword, the thread is **Control** (FR-002a).
 - **Tokenization**: Use NLTK `word_tokenize` for robust handling of punctuation.
- **Anonymization**:
 - Hash `author` using SHA-256.
 - Compute `thread_age` (days) from `created_utc` before stripping the timestamp.
 - Strip original timestamp and plaintext username.

### 2. Scoring & Validation
- **Prosocial Action Count**:
 - Lexicon: Verbs like "offer", "give", "assist", "donate", "contribute", "share".
 - **Exclusion**: Explicitly exclude "help", "support", "charity" and their synonyms to avoid lexical echo (FR-003b).
- **Sentiment**: Use VADER to compute `neg_score` (VADER `neg` component).
- **Validation**:
 - Stratified sample (sufficient per stratum of `thread_type` x `subreddit`).
 - Compare system scores against `gold_standard.csv` (3 raters).
 - Metric: Cohen's Kappa ≥ 0.7.
 - **Codebook Distinction**: The human annotation codebook will define "prosocial action" based on **intent** (e.g., "offers help", "provides resources") and **outcome**, distinct from the specific verb list used for the automated count. This prevents circular validation where the tool is validated against a definition it was hard-coded to match.

### 3. Statistical Analysis
- **Model**: **Generalized Linear Mixed Model (GLMM)** with a **Negative Binomial distribution**.
 - **Formula**: `prosocial_action_count ~ thread_type + thread_age + comment_count + topic_pc1 + topic_pc2 + topic_pc3 + (1|thread_id) + (1|user_id)`
 - **Rationale**:
 - The dependent variable is a count (integer ≥ 0), which typically follows a Poisson or Negative Binomial distribution. A standard LMM (Gaussian) violates the assumption of normality of residuals. The Negative Binomial link handles overdispersion common in count data.
 - **Topic Control**: To address the "topic selection effect" (where Prime threads are inherently about prosocial topics), we compute sentence embeddings for thread titles using `sentence-transformers/all-MiniLM-L6-v2`. We then perform PCA on these embeddings and include the top 3 principal components (`topic_pc1`, `topic_pc2`, `topic_pc3`) as fixed effects. This controls for the semantic topic of the thread, isolating the effect of the specific prime keyword from the general prosocial nature of the topic.
 - **Library**: `statsmodels` (Python) for CPU compatibility.
- **Sensitivity**:
 - Bootstrap (a sufficient number of iterations).
 - Leave-one-out control variables.
 - Alternative random effects (drop `user_id` if singular fit).
- **Power Analysis**: Pre-run check for d=0.15, α=0.05, power ≥ 0.80.

### 4. Pre-study Prevalence Estimation
- **Step**: Before full data collection, a pilot sample will be analyzed to estimate the ratio of Prime to Control threads.
- **Adjustment**: If the Prime group is expected to be <4,000 samples, the target `TARGET_N` will be increased dynamically to ensure sufficient power, or the study will be aborted with a warning if the dataset is exhausted.

## Statistical Rigor & Assumptions
- **Observational Nature**: The study is **associational**. No causal claims are made. The GLMM controls for observable confounders (age, popularity, subreddit, topic embeddings) but selection bias remains.
- **Multiple Comparisons**: Not applicable for the primary test (one GLMM), but sensitivity analysis covers robustness.
- **Collinearity**: `thread_type` is derived from title keywords; `prosocial_action_count` excludes those keywords. Topic embeddings are included to mitigate semantic correlation.
- **Power**: Assumed N=10,000 is sufficient for d=0.15. If power < 80%, a warning is logged (FR-013).
- **Statistical Method Correction**: The plan explicitly deviates from the spec's request for an LMM (Gaussian) to a GLMM (Negative Binomial) to ensure scientific validity for count data. This is flagged as a necessary correction.
- **Topic Confounding**: The inclusion of PCA-reduced sentence embeddings as covariates directly addresses the concern that Prime threads might be inherently more prosocial. This allows the model to estimate the effect of the *prime* while holding the *topic* constant.

## Limitations
- **Dataset Availability**: Resolved. The `pushshift/reddit` dataset is verified to contain all 5 subreddits.
- **Lexicon Validity**: The action lexicon is a lightweight proxy; human validation is critical (SC-006).
- **Compute Constraints**: Bootstrap resampling (1k iterations) on 10k rows may approach the 4-hour limit; optimization via vectorization is required. Embedding generation is fast on CPU.
- **Topic Confounding**: While topic embeddings are included, they may not capture all nuances of topic variation. However, this is a significant improvement over the original plan.