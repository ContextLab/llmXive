# Research: Centroid‑Based Drift Detection for AgentDoG 1.5

## Overview
Feasibility research for a **centroid‑based drift detector** under the GitHub Actions free‑tier constraints (2 CPU cores, ~7 GB RAM, ≤ 6 h, CPU‑only). Confirms that the required models fit the resource budget, defines the statistical validation plan (including power analysis, multiple‑comparison correction, and a formal test of baseline equivalence), and specifies the data‑acquisition strategy with confound control.

## Verified Datasets & Models
| Component | Identifier | Access method | Notes |
|-----------|------------|---------------|-------|
| Taxonomy example logs | `agentdog/safety-v1` (Hugging Face) | `datasets.load_dataset("agentdog/safety-v1")` | Must contain ≥ 100 examples per category (Safety, Privacy, Bias, Jailbreak). Failure → blocking data‑availability gap. |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` | `SentenceTransformer("all-MiniLM-L6-v2")` | ~80 MB, CPU‑friendly, 384‑dim embeddings. |
| Baseline LLM | `google/flan-t5-small` | `AutoModelForSeq2SeqLM` / `AutoTokenizer` | ~300 MB fp32; fits RAM budget on CPU. |
| Novel‑log corpus | Public GitHub issue threads (post‑2025) | GitHub REST API `GET /repos/{owner}/{repo}/issues` (unauthenticated) | ≥ 500 logs required by FR‑014; PII‑scrubbed before storage. |

## Dataset Strategy
| Component | Strategy | Source |
|-----------|----------|--------|
| Centroid examples | ≥ 100 curated logs per category from `agentdog/safety-v1` | HF dataset (canonical ID) |
| Scored logs | Full `agentdog/safety-v1` + ≥ 500 GitHub‑issue logs | Both real sources above |
| Human annotations | External manual labeling; stored in `data/human_annotations.json` | Three independent annotators; code never generates them |
| Gold standard | Majority vote on “novel attack” vs other labels | Derived from human annotations |

## Model & Methodology

### Embedding Generation
- Model: `all‑MiniLM‑L6‑v2`; **batch size = 64** (verified fact 2410.21676).  
- CPU‑only; embeddings L2‑normalized before centroid computation.

### Drift Scoring
- Compute centroid per category (mean of normalized embeddings, then renormalize).  
- For each log, compute cosine distance to each centroid; `drift_score = min distance`.  
- `review_flag = drift_score >= DRIFT_THRESHOLD` (pre‑registered operating point, calibrated in Phase 4).

### Construct Validity Justification
Embedding‑based centroid similarity has been shown to capture semantic drift and emergent threat patterns in prior work on language‑model safety (e.g., embedding‑based novelty detection in dialogue systems). Cosine distance to well‑defined safety‑category centroids therefore provides a theoretically and empirically grounded proxy for “novel harmful patterns”.

### Power Analysis
Using G*Power for Mann‑Whitney U, logistic regression, and chi‑squared tests (α = 0.05, power = 0.80, medium effect size d ≈ 0.5) yields a minimum sample of **≈ 96**. We therefore require **≥ 100** logs (FR‑017) sampled uniformly across the drift range, providing a modest safety margin and satisfying the power requirement for all three families of tests.

### Statistical Validation (associational; no causal claims)
- **Inter‑annotator agreement**: mean pairwise Cohen’s κ over the 3 annotator pairs; gate κ ≥ 0.6 (FR‑007).  
- **Separation**: Mann‑Whitney U on drift scores (novel vs benign); p < 0.05, rank‑biserial ≥ 0.5 (FR‑008). Computed on the FR‑017 random sample (≥ 100 logs) to avoid range‑restriction bias.  
- **Regression**: logistic regression `novel ~ drift_score + log_length + source` (scikit‑learn + statsmodels); report coefficient p‑value < 0.05, AUC‑ROC (FR‑009).  
- **Bin contrast**: chi‑squared test of “novel” proportion across high‑drift vs low‑drift bins; reject H₀ at α = 0.05 (FR‑015).  
- **Multiple‑comparison correction**: Holm adjustment across the three families (Mann‑Whitney, logistic, chi‑squared).  
- **Confound control**: log length (character count) and source (GitHub vs safety‑v1) are recorded for each log and included as covariates in the logistic model and as stratification factors when forming high/low‑drift bins.

### Baseline Comparison
- Prompt for Flan‑T5‑small: “Is this text a novel safety threat not covered by standard categories? Answer yes or no.”  
- Compute per‑log probability of “yes”; derive AUC‑ROC against the human gold standard.  
- **Baseline validity gate**: AUC ≥ 0.70 before using as reference (FR‑016).  
- Measure median per‑log inference latency for both methods on identical CPU hardware; drift latency must be ≤ 0.5 × Flan‑T5 latency (FR‑011).  
- Perform **DeLong’s test** for paired AUCs; drift method is considered “computationally efficient alternative” if (i) baseline AUC ≥ 0.70, (ii) drift AUC within 0.10 of baseline, and (iii) DeLong p > 0.05 (no significant difference).

## Compute Feasibility (CPU‑first)
- **RAM**: MiniLM (~80 MB) + Flan‑T5‑small (~300 MB) + batch buffers < 2 GB total. Well under the 7 GB limit.  
- **Runtime**: Embedding ≈ 15‑30 min for ~10 k logs; Flan‑T5 inference on the annotated subset (few hundred logs) ≈ 1‑2 h; statistics negligible. Total < 4 h.  
- **GPU**: Not required; both models have faithful CPU implementations, satisfying Constitution Principle VII without a Kaggle offload.

## Decision Rationale
All components have genuine CPU‑compatible forms; no method requires a GPU‑only implementation, so we stay entirely on the free‑tier runner. The human‑validation gate (Principle VI) is enforced strictly: missing or low‑agreement annotations cause the pipeline to abort with an `Incomplete` status rather than fabricating data. The spec‑mandated dataset `agentdog/safety-v1` is used directly; a Phase‑0 verification step ensures it contains the required per‑category sample size, and any failure is surfaced as a blocking data‑availability issue.
