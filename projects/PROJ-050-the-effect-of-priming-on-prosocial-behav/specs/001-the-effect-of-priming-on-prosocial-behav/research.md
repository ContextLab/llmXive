# Research: The Effect of Priming on Prosocial Behavior

## Dataset Strategy

### Verified Dataset
- **Name**: `fddemarco/pushshift-reddit-comments` (Hugging Face)  
- **Access**: `datasets.load_dataset("fddemarco/pushshift-reddit-comments", split="train", streaming=True)`  
- **Size**: 15 034 827 records (verified via `get_dataset_infos`).  
- **Fields**: `author`, `body`, `created_utc`, `link_id`, `subreddit`, `subreddit_id`, `id`, `score`, `controversiality`.  

### Dataset Fit Analysis
| Required Variable | Present? | Comment |
|-------------------|----------|---------|
| `title` (thread title) | **No** | Needed for priming classification (regex). |
| `body` (comment text) | Yes | Used for VADER and prosocial keyword counting. |
| `author` | Yes | Hashed for anonymity. |
| `subreddit` | Yes | Random effect in LMM. |
| `created_utc` | Yes | Removed for privacy; could be used for tenure but not available. |
| `user_tenure` | No | Not derivable without additional API calls; omitted from model. |

**Conclusion**: The dataset satisfies all variables **except** `title`. Because FR‑001 explicitly requires classification based on thread titles, the dataset is **incompatible** with the original hypothesis.  

**Proposed Paths**  
1. **Scope Revision** – Obtain an open Reddit dump that includes both comment bodies and parent post titles (e.g., the full Pushshift archive).  
2. **Temporary Redesign** – Remove the priming condition, treat all comments as a single group, and focus on prosocial scoring and validation (requires project‑lead approval).

### Data Availability & Feasibility
- **Download Method**: Streaming via `datasets` library; no local storage of the full raw dump.  
- **Disk Use**: Processed CSVs estimated < 2 GB.  
- **Runtime**: Streaming + processing of a large‑scale dataset (on the order of tens of millions of rows) expected ≈ 2 h on CPU.  

## Methodology & Statistical Rigor

### 1. Data Ingestion & Anonymization (FR‑001)
- **Streaming Load**: Iterate over the dataset, filter for subreddits `AskReddit`, `science`, `relationships`.  
- **Anonymization**: SHA‑256 hash of `author`; drop `created_utc`.  
- **Thread‑type Classification**: *Pending* – cannot be derived without `title`. If a title‑bearing dataset becomes available, apply regex `/(thank|help|support|care)/i`.  

### 2. Prosocial Scoring & Validation (FR‑002, FR‑004)
- **VADER**: Compute `compound`, `pos`, `neu`, `neg` scores for each `body`.  
- **Distinct Prosocial Lexicon**: A curated list that **excludes** the prime words (`thank`, `help`, `support`, `care`).  
- **Human Annotation**: Randomly sample 200 comments stratified by subreddit (and, if possible, by provisional `thread_type`). Two blind raters label “Prosocial Intent” (binary).  
- **Metrics**:  
  - Cohen’s Kappa (reported, no pass/fail).  
  - Pearson correlation *r* between VADER `compound` and human prosocial ratings (require *r* ≥ 0.7 per SC‑004).  

### 3. Linear Mixed Model (FR‑003)
- **Formula** (after dropping unavailable predictors):  
  `prosocial_intent_score ~ thread_type + thread_length + (1|subreddit) + (1|user_id)`  
- **Estimator**: `statsmodels` `MixedLM`.  
- **Convergence Check**: `model.converged` flag.  
- **Sensitivity Analysis**: Re‑fit with optimizer tolerances `1e‑4`, `1e‑5`, `1e‑6`; record p‑values and convergence flags.  
- **Multiple Comparisons**: Single primary test (`thread_type`); no correction needed.  
- **Causal Claim**: Observational; results framed as *associational*.  
- **Collinearity**: Compute VIF for `thread_length`; report if VIF > 5.  

### 4. CPU Feasibility (FR‑002c)
- **Estimate**: VADER + regex on a large‑scale dataset processes rows efficiently, completing within a practical runtime.  
- **Memory**: Streaming ensures ≤ 1 GB.  
- **Decision**: Feasible on CPU; no deferral needed. A comment “FR‑002c Feasible on CPU” will be logged in `02_score.py`.  

## Compute Feasibility
All steps are CPU‑tractable; no GPU off‑load required. The pipeline respects the 6‑hour CI limit.

## Unresolved Panel Concerns
- **Missing Thread Title**: Fatal for priming classification. Must be resolved before any hypothesis test involving `thread_type`.  
- **User Tenure**: Already omitted; documented as a spec deviation.  

---
