# Research: llmXive follow-up: extending "GateMem: Benchmarking Memory Governance in Multi-Principal Shared-Memo"

## 1. Problem Statement
Determine whether a modular, CPU‑tractable **Gatekeeper** (DistilBERT intent classifier + regex rule engine) can **reduce unauthorized information leakage** (Access Control) and **honour deletion requests** (Forgetting) while **maintaining task success** (Utility) and **lowering computational cost** relative to the standard **Retrieval‑only** and **Long‑Context** baselines.

## 2. Dataset Strategy

### Verified Datasets
| Dataset | Source URL | Format | Role | License |
|---|---|---|---|---|
| GateMem (education domain) | https://huggingface.co/datasets/Ray368/GateMem/resolve/main/gatemem/data/education/checkpoints.jsonl | JSONL (streamable) | Primary evaluation data (all four domains are accessed via the same repository; each domain is a separate split). | CC‑BY‑4.0 |

*All four domains (medical, office, education, household) are fetched from the same HF repo using `datasets.load_dataset(..., streaming=True)`. No alternative or synthetic data are used; if any URL is unreachable, the pipeline exits with error code 1 (per FR‑001 & Constitution).*

### Variable Verification
The GateMem episodes contain the required fields:

- **Outcome / Ground‑truth**: `leak_target`, `ground_truth_success`, `ground_truth_deletion`.
- **Predictors / Covariates**: `user_role`, `domain`, `deletion_log`, `memory_state`.
- **Derived**: `intent` (produced by the DistilBERT classifier).

A schema validation step (`data_loader.py`) checks for the presence of **all** these variables against `gatemem_episode.schema.yaml`. Missing variables cause an immediate abort (exit 1).

## 3. Methodology

### 3.1. Gatekeeper Pipeline
1. **Intent Classification** – Load `distilbert-base-uncased-finetuned-sst-2-english` (CPU‑only, frozen) via HuggingFace `transformers`. Map the four sentiment labels to our intent taxonomy (`query`, `deletion`, `extraction`, `other`).  
2. **Rule Engine** – Regex checks enforce role‑based access policies and parse `deletion_log`. Ambiguous `leak-target` annotations are logged as *validation errors* and excluded from metric calculations.  
3. **Decision Logic** – If intent is `extraction` **or** the keyword leak detector fires **and** the role is unauthorized, the request is blocked; otherwise it proceeds to the LLM (EleutherAI/pythia‑410m).  

### 3.2. Baseline Pipelines
- **Retrieval‑only** – Standard RAG retrieval followed by **EleutherAI/pythia‑410m** generation, no governance filtering.  
- **Long‑Context** – Pass the full memory context (up to the model’s window) directly to **EleutherAI/pythia‑410m**, no retrieval or filtering.  

*Both baselines use identical prompts, retrieval indices, and the same random seed (`SEED=42`).*

### 3.3. Metrics (Revised Definitions)
| Metric | Numerator | Denominator | Interpretation |
|---|---|---|---|
| **Access Control** | Unauthorized exposures (ground‑truth `leak_target=False` *and* pipeline allowed) | **Total queries** (all episodes) | Proportion of leaks that should have been blocked but were not. |
| **Utility** | Successful task completions (ground‑truth `ground_truth_success=True` *and* pipeline succeeded) | Total valid queries (`ground_truth_success=True`) | Task success rate. |
| **Conditional Utility** | Successful completions among queries allowed by the gate | Queries allowed by the gate | Utility conditional on passing the gate. |
| **Forgetting** | Deletion requests correctly suppressed (`ground_truth_deletion=True` *and* pipeline blocked) | Total deletion requests (`ground_truth_deletion=True`) | Deletion compliance rate. |

All scores are computed per episode, then aggregated per pipeline and domain (see `metrics/*` modules).

### 3.4. Statistical Analysis
- **Primary Test**: **Generalized Linear Mixed‑Effects Model (GLMM)** using `statsmodels`  
  - **Binary outcomes** (Access Control, Forgetting): **logistic link**.  
  - **Continuous outcome** (Utility): **Gaussian link**.  
  - **Model**: `score ~ method + domain` where `domain` is treated as a **fixed effect** (four levels).  
  - **Assumption Checks**: Shapiro‑Wilk on residuals for Utility (`α=0.05`); Hosmer‑Lemeshow for logistic models.  
  - **Multiple‑Comparison Correction**: Benjamini‑Hochberg applied across **six** hypothesis tests (three metrics × two baseline comparisons).  
  - **Power Assessment**: Assuming a modest effect size (Cohen’s d ≈ 0.3), α = 0.05, two‑tailed test, **≈ 200 episodes per domain** give ≈0.85 power; GateMem provides >500 episodes per domain, so power is adequate. If computed power falls below 0.8, results will be labelled exploratory.  
- **Fallback** (if GLMM fails to converge or assumptions violated):  
  - **Access Control** – Paired **McNemar’s Test** (exact version if discordant pairs < 25).  
  - **Utility** – Paired **t‑test** (or Wilcoxon signed‑rank if non‑normal).  
  - **Forgetting** – Paired **logistic regression** on aggregated counts per domain.  
- **Effect Size Reporting** – Odds ratios for binary outcomes, Cohen’s d for Utility, with 95 % confidence intervals.

## 4. Decision Rationale
| Decision | Reason |
|---|---|
| **DistilBERT SST‑2** as intent classifier | FR‑002 requires a frozen DistilBERT model; the verified model ID (`distilbert-base-uncased-finetuned-sst-2-english`) satisfies the CPU‑only constraint. |
| **GLMM with logistic link** for binary metrics | Ensures appropriate distributional assumptions (addresses methodology‑d27fd01c & scientific_soundness‑bfc8f009). |
| **Domain as fixed effect** | With only four domains, a random intercept is unstable; treating as fixed effect yields reliable estimates (addresses methodology‑07b08632). |
| **Power analysis** | Provides concrete assessment; if under‑powered, results are exploratory (addresses methodology‑6b2e852c). |
| **Multiple‑test correction for six comparisons** | Controls family‑wise error rate across all baseline‑metric pairs (addresses methodology‑88eebc96). |
| **Access Control denominator corrected** | Guarantees comparability across pipelines (addresses methodology‑20fabfaa). |
| **CPU‑tractable LLM (EleutherAI/pythia‑410m)** | Meets free‑tier compute limits; replaces infeasible Llama‑3‑8B (addresses data_resources‑2d3690ce). |
| **Dataset license documented** | Satisfies Constitution Principle III (addresses data_resources‑c987466e). |
| **Fallback to stratified tests** | Guarantees results even when GLMM assumptions break (addresses methodology‑07b08632). |

## 5. Limitations & Construct Validity
- **Intent classifier** is a sentiment model repurposed for intent; may miss nuanced extraction intents.  
- **Small number of domains** limits random‑effects modeling; fixed‑effect approach mitigates this.  
- **Cost variance** of the Pythia‑410m inference may obscure subtle latency gains; power analysis quantifies detectable differences.  

## 6. Risk Assessment
| Risk | Mitigation |
|---|---|
| Dataset unreachable / checksum mismatch | Exit with error 1; no synthetic data fallback. |
| DistilBERT model download corruption | Retry once; on second failure exit with error 1 and log “Critical: Model Unavailable”. |
| Memory overflow during streaming | Process episodes in batches of ≤ 200; continuously monitor RAM via `profiling.py`. |
| GLMM non‑convergence | Automatic fallback to domain‑stratified paired tests. |
| Ambiguous `leak_target` annotations | Log as “validation error” and exclude from metric calculation. |



