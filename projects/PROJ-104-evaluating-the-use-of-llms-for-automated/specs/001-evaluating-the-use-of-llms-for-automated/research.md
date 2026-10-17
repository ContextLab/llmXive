# Research: Evaluating LLM Fidelity in Commit-to-Documentation Translation

## Decision & Rationale
| Decision | Rationale |
|----------|-----------|
| **CPU‑first 4‑bit inference** for all three models | Meets NFR‑001 (≤60 s per commit) on the free‑tier runner; baseline hardware is identical across models. |
| **Uniform GPU escape hatch** if any model exceeds the time budget | Guarantees that **all** models are evaluated on the same hardware (Kaggle GPU) when needed, preserving Principle VII (Architectural Fidelity Isolation). |
| **Open‑source repositories** (`pandas`, `requests`, `scikit‑learn`, `flask`, `django`) | Directly downloadable via GitHub; no gated access, satisfying data‑availability rule. |
| **Expanded regex surface extraction + AST verification** | Captures a broader set of surface changes (class names, variables, imports) and reduces false‑negative hallucination counts (FR‑003, FR‑006). |
| **Zero‑shot intent classifier with adaptive threshold** | Confidence threshold is **calibrated** on the 50‑sample gold‑standard to achieve Cohen’s κ ≥ 0.6. If κ falls below 0.6, the pipeline **automatically switches** to a deterministic rule‑based heuristic (keyword + noun‑phrase). This addresses construct validity concerns. |
| **Gold‑standard of an appropriately large sample size.** | Provides empirical validation of intent classification (FR‑008) and satisfies the required inter‑annotator agreement. |
| **Power‑analysis simulation** | Confirms that ≥500 pairs give ≥80 % power for detecting a medium effect with the Friedman test; if power is insufficient, results are flagged as exploratory (FR‑005, SC‑004). |
| **Friedman test (non‑parametric) with Holm‑Bonferroni correction** | Appropriate for repeated‑measures design with >2 related groups; correction controls family‑wise error across intent precision, surface precision, and hallucination rate (FR‑005). |
| **Repeated‑measures ANOVA as sensitivity check** | Allows reporting of both non‑parametric and parametric results if normality holds (FR‑005). |
| **AST‑augmented verification for hallucinations** | Reduces false‑positive hallucination counts by handling aliased imports and renamed symbols (FR‑006). |
| **Default CI sample size of a sufficient number of commits per model** | Keeps total wall‑clock time ≤ 6 h on the free runner; full 500‑pair analysis is available via an optional manual workflow (addresses compute feasibility). |

## Dataset Strategy
| Dataset | Source (verified) | Access Method | Variables Covered |
|---------|-------------------|---------------|-------------------|
| Repository commits & docs | GitHub (public URLs) | `git clone` + `git log` (Python `GitPython`) | `commit_hash`, `commit_message`, `repo_name`, `doc_diff`, `timestamp` |
| Model weights | HuggingFace model hub (e.g., `microsoft/phi-3-mini-4bit-gguf`, `google/gemma-2-2b-it-4bit-gguf`, `meta-llama/Meta-Llama-3.2-3B-Instruct-4bit`) | `transformers` `from_pretrained(..., load_in_4bit=True)` | N/A (model artifacts) |
| Gold‑standard annotations | Manually created (internal) | CSV/JSON stored under `data/gold/` | `sample_id`, `intent_entities`, `annotator_id` |

All data are programmatically fetched; no manual download steps.

## Model Strategy
- **Phi‑3‑mini** (`microsoft/phi-3-mini-4bit-gguf`) – 3 B parameters, CPU‑optimized, 4‑bit quant.  
- **Gemma‑2‑2b** (`google/gemma-2-2b-it-4bit-gguf`) – 2 B parameters, same quantization.  
- **Llama‑3.2‑3B** (`meta-llama/Meta-Llama-3.2-3B-Instruct-4bit`) – 3 B parameters, CPU‑compatible.  

All models are loaded with `device_map="auto"`; on the CI runner this resolves to CPU. If a model exceeds the 60 s timeout, the same code runs on a Kaggle GPU (`torch.cuda.is_available()`).

## Entity Extraction Methodology
1. **Surface Entities** – Expanded regex patterns: <br>
   - File paths: `r"[a-zA-Z0-9_./-]+\.(py|md|rst)"` <br>
   - Function signatures: `r"def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\("` <br>
   - Version numbers: `r"\d+\.\d+\.\d+"` <br>
   - Class names: `r"class\s+[A-Z][a-zA-Z0-9_]*"` <br>
   - Variable assignments: `r"[a-zA-Z_][a-zA-Z0-9_]*\s*="` <br>
   - Import statements: `r"(import|from)\s+[a-zA-Z0-9_.]+"`  
2. **Technical Intent Entities** – Zero‑shot classifier using `facebook/bart-large-mnli`. The confidence threshold is **calibrated** on the 50‑sample gold‑standard to achieve κ ≥ 0.6; the resulting threshold may differ from a fixed 0.7 value. If κ < 0.6, the pipeline **switches** to a deterministic rule‑based heuristic (keyword + noun‑phrase). |
3. **Verification against codebase** – For each surface token, run `git grep -w <token>` **and** parse the repository’s Python AST (via `ast` module) to locate definitions, handling renamed or aliased symbols. Absence after both checks ⇒ hallucination. |

## Scoring & Metrics
- **Precision** = TP / (TP + FP) per category.  
- **Recall** = TP / (TP + FN) per category.  
- **FidelityMetric** stored per `(sample_id, model_id)` with fields: `precision_intent`, `recall_intent`, `precision_surface`, `recall_surface`, `hallucination_rate`.  
- Aggregated means and 95 % CI (bootstrapped, `[deferred]`) per model.

## Statistical Analysis Plan
1. **Power analysis** (Phase 0) estimates ≥80 % power for the Friedman test with 500 pairs; if power < 80 %, the analysis is labelled exploratory.  
2. Test normality of intent‑precision across models (Shapiro‑Wilk, α = 0.05).  
3. If non‑normal → Friedman chi‑square test (`scipy.stats.friedmanchisquare`) on paired intent‑precision scores.  
4. If normal → Repeated‑measures ANOVA (`statsmodels.stats.anova.AnovaRM`).  
5. **Holm‑Bonferroni correction** applied across the three metrics (intent precision, surface precision, hallucination rate) to control family‑wise error.  
6. Report p‑values `[deferred]`; significance threshold p < 0.05 (SC‑004).  
7. Effect size (Kendall’s W for Friedman, η² for ANOVA) `[deferred]`.

## Compute Feasibility
- **CPU profile**: 4‑bit models occupy a few hundred MB each; loading sequentially keeps RAM < 2 GB. Generation ≤ 60 s per commit (benchmark on a comparable runner).  
- **Default CI run**: 200 randomly sampled commits per model (≈ on the order of a few hundred generation calls) → estimated wall‑clock ≤ 3 h on CPU; if any model exceeds the timeout, **all** models are re‑run on a Kaggle free GPU (uniform fallback) within the 9‑h GPU limit.  
- **Full‑scale run** (≥500 pairs) is provided as an optional manual workflow for environments with extended compute.  
- **Caching**: Model weights are cached between CI runs to avoid repeated downloads.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Model inference exceeds 60 s on CPU | Failure of NFR‑001 | Uniform GPU fallback for all models + token cap (200) to keep runtimes low. |
| Insufficient documentation changes in a repo | Dataset size < 500 | Skip repo, log warning; abort with explicit message if total < 500 (SC‑001 violation). |
| Zero‑shot classifier mislabels intent | Invalid scores | Validate classifier on gold‑standard; if κ < 0.6, fallback to rule‑based intent extraction. |
| Hallucination verification false negatives | Inflated hallucination rate | Use combined `git grep` + AST parsing; log unmatched tokens for manual review. |
| Multiple‑comparison inflation | Type I error | Apply Holm‑Bonferroni correction across all tested metrics. |
| Power insufficient for Friedman test | Low statistical confidence | Conduct Monte‑Carlo power analysis; flag exploratory if power < 80 %. |

---


