# Research: llmXive follow-up: extending "GateMem: Benchmarking Memory Governance in Multi-Principal Shared-Memo"

## 1. Problem Statement
Determine whether a modular, CPU‑tractable **Gatekeeper** (DistilBERT intent classifier + regex rule engine) can **reduce unauthorized information leakage** (Access Control) and **honour deletion requests** (Forgetting) while **maintaining task success** (Utility) and **lowering computational cost** relative to the standard **Retrieval‑only** and **Long‑Context** baselines.

## 2. Dataset Strategy

### Verified Datasets
| Dataset | Source URL | Format | Role | License |
|---|---|---|---|---|
| GateMem (education split) | https://huggingface.co/datasets/Ray368/GateMem/resolve/main/gatemem/data/education/checkpoints.jsonl | JSONL (streamable) | Primary evaluation data (four domain splits are accessed via the same HF repo) | CC‑BY‑4.0 |

The GateMem repository contains four domain splits (`medical`, `office`, `education`, `household`). The **education** split URL above is the only verified URL; the other three splits are accessed from the same repository using the standard `datasets.load_dataset` API (e.g., `split="medical"`). If a split is unavailable, the pipeline aborts with error 1, preserving reproducibility.

### Variable Verification
Each episode supplies the required fields:

- **Outcome / Ground‑truth**: `leak_target` (boolean), `ground_truth_success` (boolean), `ground_truth_deletion` (boolean).  
- **Predictors / Covariates**: `user_role`, `domain`, `deletion_log` (array of strings), `memory_state`.  
- **Derived**: `intent` (produced by the DistilBERT classifier).

`utils/data_loader.py` validates every record against `gatemem_episode.schema.yaml`. Missing fields cause immediate abort (exit 1).

## 3. Methodology

### 3.1. Gatekeeper Pipeline
1. **Intent Classification** – Load `distilbert-base-uncased-finetuned-sst-2-english` (CPU‑only, frozen) via HuggingFace `transformers`. Map the four SST‑2 sentiment labels to our intent taxonomy (`query`, `deletion`, `extraction`, `other`).  
   *Validation*: A small manually‑annotated sample (≈ 200 episodes) is used to evaluate this mapping (see T010a); if accuracy < 80 % the run aborts with a warning.  
2. **Rule Engine** – Regex checks enforce role‑based access policies and parse `deletion_log`. Ambiguous `leak_target` annotations are logged as *validation errors* and excluded from metric calculations.  
3. **Decision Logic** – If intent is `extraction` **or** the regex leak detector fires **and** the role is unauthorized, the request is blocked; otherwise it proceeds to the LLM (`meta-llama/Meta-Llama-3-2B-Instruct` int8).  

### 3.2. Baseline Pipelines
- **Retrieval‑only** – Standard RAG retrieval followed by generation, no governance layer.  
- **Long‑Context** – Pass the full memory context (up to the model’s window) directly to the LLM, no retrieval or filtering.  

*Both baselines use identical prompts, retrieval parameters, and the fixed random seed (`SEED=42`).*

### 3.3. Metrics (Revised Definitions)
| Metric | Numerator | Denominator | Interpretation |
|---|---|---|---|
| **Access Control** | Unauthorized exposures (ground‑truth `leak_target=False` & pipeline allowed) | **Total queries** (all episodes) | Proportion of leaks that should have been blocked but were not. |
| **Utility** | Successful task completions (ground‑truth `ground_truth_success=True` & pipeline succeeded) | Total valid queries (`ground_truth_success=True`) | Task success rate (binary per‑episode outcome). |
| **Conditional Utility** | Successful completions among queries allowed by the gate | Queries allowed by the gate | Utility conditional on passing the gate. |
| **Forgetting** | Deletion requests correctly suppressed (`ground_truth_deletion=True` & pipeline blocked) | Total deletion requests (`ground_truth_deletion=True`) | Deletion compliance rate. |

All scores are computed per episode, then aggregated per pipeline and domain.

### 3.4. Statistical Analysis
- **Primary Test**: **Logistic Generalized Linear Mixed‑Effects Model (GLMM)** via `statsmodels` for **all three binary outcomes** (Access Control, Utility, Forgetting).  
  - **Model**: `score ~ method + domain` with `domain` as a **fixed effect**; a likelihood‑ratio test will assess whether adding a random intercept for `domain` improves fit, in which case a mixed‑effect model is used.  
  - **Assumption Checks**: Hosmer‑Lemeshow for logistic models; Shapiro‑Wilk on residuals for Utility if treated as continuous (fallback).  
  - **Multiple‑Comparison Correction**: **Holm‑Bonferroni** across the six primary hypothesis tests (α = 0.0083).  
- **Power Assessment**:  
  - For binary metrics, assuming a medium effect size (Cohen’s h is expected to be of modest magnitude.) and α = 0.0083, ≥ 200 episodes per domain yields ≈ 0.85 power.  
  - For Utility (treated as binary), Cohen’s h ≈ 0.3 is also used; the same sample size suffices. GateMem provides > 500 episodes per domain, satisfying power requirements.  
- **Fallback Tests** (applied only if GLMM fails to converge or assumptions are violated, **and Holm‑Bonferroni is also applied**):  
  - **Access Control & Forgetting** – Paired **McNemar’s exact test** (binary).  
  - **Utility** – Paired **Wilcoxon signed‑rank test** (non‑parametric) or paired **t‑test** if normality holds.  
  - Results from fallback tests are reported with the same family‑wise error control (α = 0.0083).  

## 4. Decision Rationale
| Decision | Reason |
|---|---|
| **DistilBERT SST‑2** as intent classifier | Satisfies FR‑002 (frozen DistilBERT) and runs comfortably on CPU; validation step mitigates construct‑validity concerns. |
| **Logistic GLMM** for all binary metrics | Provides appropriate distributional modeling and aligns with FR‑005. |
| **Domain as fixed effect with optional random intercept** | Fixed effect ensures stability with only four levels; random effect tested for robustness. |
| **Power analysis per metric with Holm‑Bonferroni α** | Guarantees adequate sample size after correction; GateMem exceeds requirements. |
| **Holm‑Bonferroni on fallback tests** | Maintains family‑wise error control even when primary model cannot be used. |
| **CPU‑tractable LLM (Llama‑3‑2B‑int8)** | Meets FR‑003’s explicit requirement for a lightweight 2.7 B‑class model that runs on the free‑tier runner. |
| **Output schema generation (T021)** | Ensures final artifacts can be validated against `output.schema.yaml`. |
| **Dataset license documented** | Satisfies Constitution Principle III (CC‑BY‑4.0). |
| **Validation of intent mapping** | Addresses methodological concern about repurposing a sentiment model. |

## 5. Limitations & Construct Validity
- **Intent classifier** is a sentiment model repurposed for intent; the validation step (T010a) quantifies mapping quality.  
- **Only four domains** limit random‑effects modeling; the likelihood‑ratio test determines whether a random intercept adds value.  
- **Latency variance** of the Llama‑3‑2B‑int8 inference may obscure subtle cost differences; power analysis quantifies detectable differences.  

## 6. Risk Assessment
| Risk | Mitigation |
|---|---|
| Dataset unreachable / checksum mismatch | Abort with error 1; no synthetic fallback. |
| DistilBERT model download corruption | Retry once; on second failure exit with error 1 and log “Critical: Model Unavailable”. |
| Memory overflow during streaming | Process episodes in batches ≤ 200; monitor RAM via `profiling.py`. |
| GLMM non‑convergence | Automatic fallback to domain‑stratified paired tests (McNemar, Wilcoxon) with Holm‑Bonferroni. |
| Ambiguous `leak_target` annotations | Log as “validation error” and exclude from metric calculation. |

---

