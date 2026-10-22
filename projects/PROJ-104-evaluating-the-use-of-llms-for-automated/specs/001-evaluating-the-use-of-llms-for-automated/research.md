# Research: Evaluating LLM Fidelity in Commit-to-Documentation Translation

## Decision & Rationale
| Decision | Rationale |
|----------|-----------|
| **CPU‑only inference with adaptive sample sizing** | Meets NFR‑001 (≤60 s per commit) on the free‑tier runner; avoids hardware confounds by keeping hardware constant across models. |
| **Uniform GPU escape hatch removed** | Guarantees that any performance differences are due to model architecture, not hardware acceleration (Principle VII). |
| **GitHub REST API for data extraction** | Provides a stable, programmatically verifiable source, eliminating the brittle `git` parsing that caused T003. |
| **Human‑annotated gold‑standard** | Supplies a valid ground truth for intent entities, satisfying FR‑008 and avoiding circular validation. |
| **Expanded regex surface extraction + AST verification** | Captures a broader set of surface changes, reducing false negatives and improving construct validity (FR‑003, FR‑006). |
| **Zero‑shot intent classifier calibrated on held‑out validation split** | Prevents data leakage; if κ < 0.6, falls back to a simple keyword‑heuristic extractor, preserving independence from the gold reference. |
| **Power‑analysis simulation with explicit parameters** | Confirms ≥80 % power for 500 pairs given α = 0.05 and medium effect size; flags exploratory status if power is lower (SC‑004). |
| **Stratified sampling across repositories** | Controls for repository‑level variability (documentation style, commit frequency), reducing confounds (Phase 1). |
| **Default CI run on a stratified subset of samples** | Keeps total wall‑clock time ≤ 3 h on CPU; full 500‑pair analysis available via manual workflow (addressing compute feasibility). |

## Dataset Strategy
| Dataset | Source (verified) | Access Method | Variables Covered |
|---------|-------------------|---------------|-------------------|
| Repository commits & docs | GitHub public URLs (e.g., `) | GitHub REST API (`/repos/:owner/:repo/commits`, `/commits/:sha`) | `commit_hash`, `commit_message`, `repository_name`, `doc_diff`, `timestamp` |
| Model weights | HuggingFace model hub (verified URLs) | `transformers.from_pretrained(..., load_in_4bit=True)` | N/A |
| Gold‑standard annotations | Human annotation process (see Phase 2) | Local file creation (`data/gold/annotations.csv`) | `commit_hash`, `intent_entities` (semicolon‑separated) |

All data are fetched programmatically; no manual download steps are required.

## Model Strategy
- **Phi‑3‑mini** (`microsoft/phi-3-mini-4bit-gguf`) – ~3 B parameters, CPU‑optimized, 4‑bit quantization.  
- **Gemma‑2‑2b** (`google/gemma-2-2b-it-4bit-gguf`) – ~2 B parameters, same quantization.  
- **Llama‑3.2‑3B** (`meta-llama/Meta-Llama-3.2-3B-Instruct-4bit`) – ~3 B parameters, CPU‑compatible.  

All models are loaded with `device_map="auto"`; on the CI runner this resolves to CPU. No GPU fallback is used.

## Entity Extraction Methodology
1. **Surface Entities** – Expanded regex patterns for file paths, multi‑line function signatures, class definitions, imports, version numbers, and variable assignments. Each token is cross‑checked with `git grep -w` **and** AST parsing of the cloned repository to confirm existence.  
2. **Technical Intent Entities** – Zero‑shot classification using `facebook/bart-large-mnli`. The classifier’s confidence threshold is calibrated on a **held‑out [deferred] validation split** of the human‑annotated gold set to achieve κ ≥ 0.6. If κ < 0.6, the pipeline **falls back to a simple keyword‑heuristic extractor** (keywords: because, fix, improve, handle, prevent).

All extracted entities are stored as `EntitySet` JSON objects and validated against `contracts/project.schema.yaml`.

## Scoring & Metrics
- **Precision** = TP / (TP + FP) per category.  
- **Recall** = TP / (TP + FN) per category.  
- **Hallucination rate** = proportion of generated surface entities not found in the repository codebase.  
- **FidelityMetric** records per `(sample_id, model_id)` the fields `precision_intent`, `recall_intent`, `precision_surface`, `recall_surface`, `hallucination_rate`, and a timestamp.  

Aggregated means and 95 % confidence intervals (bootstrapped, `[deferred]`) are stored in `data/processed/fidelity_metrics.csv`.

## Statistical Analysis Plan
1. **Power analysis** (Phase 0) estimates ≥80 % power for the Friedman test with 500 pairs (α = 0.05, effect size f = 0.25). If power < 0.8, results are labelled exploratory.  
2. Normality test (Shapiro‑Wilk, α = 0.05) on intent‑precision scores.  
3. If non‑normal → Friedman chi‑square test (`scipy.stats.friedmanchisquare`).  
4. If normal → Repeated‑measures ANOVA (`statsmodels.stats.anova.AnovaRM`).  
5. **Holm‑Bonferroni correction** across intent precision, surface precision, hallucination rate.  
6. Report p‑values `[deferred]`; significance threshold p < 0.05 (SC‑004).  
7. Effect size (Kendall’s W for Friedman, η² for ANOVA) `[deferred]`.

## Compute Feasibility
- **CPU**: 4‑bit models occupy < 500 MB each; sequential loading keeps RAM < 2 GB. Generation ≤ 60 s per commit (benchmark on a comparable runner).  
- **Default CI run**: 200 stratified random commits per model → ≤ 3 h wall‑clock on CPU. If any model exceeds the timeout, the pipeline **reduces the per‑model sample size** to stay within the 6 h CI limit.  
- **Full‑scale run** (≥500 pairs) is available as an optional manual workflow.  
- **Caching**: Model weights cached between CI runs.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Model inference exceeds 60 s on CPU | Violates NFR‑001 | Adaptive sample size reduction; no hardware switch. |
| Insufficient documentation changes in a repo | Dataset size < 500 | Skip repo, log warning; abort with explicit message if total < 500 (SC‑001 violation). |
| Zero‑shot classifier mislabels intent | Invalid scores | Calibrate on held‑out validation split; fallback to keyword‑heuristic if κ < 0.6. |
| Hallucination verification false negatives | Inflated hallucination rate | Use combined `git grep` + AST parsing; log unmatched tokens for manual review. |
| Multiple‑comparison inflation | Type I error | Apply Holm‑Bonferroni correction across all tested metrics. |
| Power insufficient for Friedman test | Low statistical confidence | Conduct Monte‑Carlo power analysis; flag exploratory if power < 0.8. |

---

