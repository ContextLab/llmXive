# Research: llmXive follow-up: extending "GateMem: Benchmarking Memory Governance in Multi-Principal Shared-Memo"

## 1. Problem Statement
Determine whether a modular, CPU‑tractable **Gatekeeper** (DistilBERT intent classifier + regex rule engine) can **reduce unauthorized information leakage** (Access Control) and **honour deletion requests** (Forgetting) while **maintaining task success** (Utility) and **lowering computational cost** relative to the standard **Retrieval‑only** and **Long‑Context** baselines.

## 2. Dataset Strategy

### Verified Datasets
| Dataset | Source URL | Format | Role | License |
|---|---|---|---|---|
| GateMem (all domains) | https://huggingface.co/datasets/Ray368/GateMem/resolve/main/gatemem/data/education/checkpoints.jsonl | JSONL (streamable) | Primary evaluation data (four domain splits are accessed via the same HF repo) | CC‑BY‑4.0 |

*All four domains (medical, office, education, household) are fetched from the same Hugging Face repository using `datasets.load_dataset(..., streaming=True)`. No synthetic or alternative data are used; if the URL is unreachable the pipeline aborts with error 1 (per FR‑001 & Constitution).*

### Variable Verification
The GateMem episodes contain the required fields:

- **Outcome / Ground‑truth**: `leak_target`, `ground_truth_success`, `ground_truth_deletion`.
- **Predictors / Covariates**: `user_role`, `domain`, `deletion_log`, `memory_state`.
- **Derived**: `intent` (produced by the DistilBERT classifier).

`utils/data_loader.py` validates each record against `gatemem_episode.schema.yaml`. Missing fields cause immediate abort (exit 1).

## 3. Methodology

### 3.1. Gatekeeper Pipeline
1. **Intent Classification** – Load `distilbert-base-uncased-finetuned-sst-2-english` (CPU‑only, frozen) via HuggingFace `transformers`. Map the four sentiment labels to our intent taxonomy (`query`, `deletion`, `extraction`, `other`).  
2. **Rule Engine** – Regex checks enforce role‑based access policies and parse `deletion_log`. Ambiguous `leak_target` annotations are logged as *validation errors* and excluded from metric calculations.  
3. **Decision Logic** – If intent is `extraction` **or** the regex leak detector fires **and** the role is unauthorized, the request is blocked; otherwise it proceeds to the LLM (`EleutherAI/pythia-410m`).  

### 3.2. Baseline Pipelines
- **Retrieval‑only** – Standard RAG retrieval followed by generation, no governance layer.  
- **Long‑Context** – Pass the full memory context (up to the model’s window) directly to the LLM, no retrieval or filtering.  

*Both baselines use identical prompts, retrieval parameters, and the fixed random seed (`SEED=42`).*

### 3.3. Metrics (Revised Definitions)
| Metric | Numerator | Denominator | Interpretation |
|---|---|---|---|
| **Access Control** | Unauthorized exposures (ground‑truth `leak_target=False` & pipeline allowed) | **Total queries** (all episodes) | Proportion of leaks that should have been blocked but were not. |
| **Utility** | Successful task completions (ground‑truth `ground_truth_success=True` & pipeline succeeded) | Total valid queries (`ground_truth_success=True`) | Task success rate. |
| **Conditional Utility** | Successful completions among queries allowed by the gate | Queries allowed by the gate | Utility conditional on passing the gate. |
| **Forgetting** | Deletion requests correctly suppressed (`ground_truth_deletion=True` & pipeline blocked) | Total deletion requests (`ground_truth_deletion=True`) | Deletion compliance rate. |

All scores are computed per episode, then aggregated per pipeline and domain.

### 3.4. Statistical Analysis
- **Primary Test**: **Generalized Linear Mixed‑Effects Model (GLMM)** via `statsmodels`  
  - **Binary outcomes** (Access Control, Forgetting): **logistic link**.  
  - **Continuous outcome** (Utility): **Gaussian link**.  
  - **Model**: `score ~ method + domain` with `domain` as a **fixed effect** (four levels).  
  - **Assumption Checks**: Shapiro‑Wilk on residuals for Utility (`α=0.05`); Hosmer‑Lemeshow for logistic models.  
  - **Multiple‑Comparison Correction**: **Holm‑Bonferroni** across the six hypothesis tests (three metrics × two baseline comparisons) → family‑wise α = 0.0083.  
  - **Power Assessment**: Assuming a medium effect size (Cohen’s h ≈ 0.3), α = 0.05, two‑tailed, **≈ 200 episodes per domain** give ≈ 0.85 power; GateMem provides > 500 episodes per domain, so power is adequate. If computed power < 0.8, results are labelled exploratory.  
- **Fallback** (if GLMM fails to converge or assumptions violated):  
  - **Access Control** – Paired **McNemar’s Test** (exact version if discordant pairs < 25).  
  - **Utility** – Paired **t‑test** (or Wilcoxon signed‑rank if non‑normal).  
  - **Forgetting** – Paired **logistic regression** on aggregated counts per domain.  
- **Effect Size Reporting** – Odds ratios for binary outcomes, Cohen’s d for Utility, with 95 % confidence intervals.

## 4. Decision Rationale
| Decision | Reason |
|---|---|
| **DistilBERT SST‑2** as intent classifier | Satisfies FR‑002 (frozen DistilBERT) and runs comfortably on CPU. |
| **GLMM with logistic link** for binary metrics | Provides appropriate distributional modeling and aligns with FR‑005. |
| **Domain as fixed effect** | With only four domains, a random intercept is unstable; fixed effects yield reliable estimates. |
| **Power analysis** | Guarantees sufficient sample size; if insufficient, results are marked exploratory (per FR‑005). |
| **Holm‑Bonferroni correction** | Controls family‑wise error across the six planned tests (addresses SC‑004). |
| **CPU‑tractable LLM (pythia‑410m)** | Meets free‑tier compute limits; replaces any infeasible larger model. |
| **Dataset license documented** | Satisfies Constitution Principle III (CC‑BY‑4.0). |
| **Fallback to stratified tests** | Ensures results are produced even when GLMM assumptions break (methodology robustness). |

## 5. Limitations & Construct Validity
- **Intent classifier** is a sentiment model repurposed for intent; may miss nuanced extraction intents.  
- **Only four domains** limit random‑effects modeling; fixed‑effect approach mitigates this.  
- **Latency variance** of the Pythia‑410m inference may obscure subtle cost differences; power analysis quantifies detectable differences.  

## 6. Risk Assessment
| Risk | Mitigation |
|---|---|
| Dataset unreachable / checksum mismatch | Abort with error 1; no synthetic fallback. |
| DistilBERT model download corruption | Retry once; on second failure exit with error 1 and log “Critical: Model Unavailable”. |
| Memory overflow during streaming | Process episodes in batches ≤ 200; monitor RAM via `profiling.py`. |
| GLMM non‑convergence | Automatic fallback to domain‑stratified paired tests. |
| Ambiguous `leak_target` annotations | Log as “validation error” and exclude from metric calculation. |

---
