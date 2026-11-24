# Research: Evaluating LLM Fidelity in Commit-to-Documentation Translation

## Decision & Rationale
| Decision | Rationale |
|----------|-----------|
| **CPU‑only inference with adaptive sample sizing** | Guarantees compliance with NFR‑001 (≤60 s per commit) on the free GitHub Actions runner and isolates architecture effects (Principle VII). |
| **GitHub REST API for data extraction** | Provides a stable, programmatically verifiable source; eliminates the brittle `git`‑log parsing that caused T003. |
| **Human‑annotated gold‑standard (200 samples, κ ≥ 0.6)** | Supplies a trustworthy ground truth for intent entities, enabling robust calibration of the zero‑shot classifier. The gold set is split: [deferred] reserved for calibration, [deferred] held‑out for evaluation, preventing circular validation. |
| **Expanded regex + AST verification for surface entities** | Improves recall of file‑path, function‑signature, class‑definition, import, and version tokens, fulfilling FR‑003 and reducing false positives. |
| **Zero‑shot classifier (`facebook/bart-large-mnli`) loaded in 8‑bit quantization** | Offers a principled, reproducible intent extraction that fits within the CPU memory budget; fallback to keyword heuristic ensures pipeline continuity. |
| **Monte‑Carlo power analysis (α = 0.05, f = 0.25)** | Demonstrates ≥80 % power for the Friedman test with 500 pairs; the default CI run processes a sufficient number of samples per model for speed, but the final analysis will use the full sample set to meet the power target. |
| **Stratified sampling across repositories, language, and project size** | Controls for commit‑message length, diff size, documentation complexity **and** repository‑level factors, upholding Architectural Fidelity Isolation. |
| **Holm‑Bonferroni correction across three metrics and a Nemenyi post‑hoc test** | Controls family‑wise error rate and accounts for multiple model comparisons; the post‑hoc is only run after a significant overall Friedman/ANOVA test. |
| **Caching of model weights** | Reduces total CI runtime, keeping wall‑clock ≤ 6 h. |
| **Deterministic seed (`SEED=42`)** | Guarantees reproducibility (Constitution I). |

## Dataset Strategy
| Dataset | Source (verified) | Access Method | Variables Covered |
|---------|-------------------|---------------|-------------------|
| **GitHub commit & doc history** | Public GitHub repositories (`pandas`, `requests`, `scikit-learn`, `flask`, `django`) – URLs are immutable (`) | GitHub REST API (`/repos/:owner/:repo/commits`, `git show <sha>`) | `commit_hash`, `commit_message`, `repository_name`, `doc_diff`, `timestamp` |
| **Model weights** | HuggingFace model hub (verified URLs) | `transformers.from_pretrained(..., load_in_4bit=True)` | N/A |
| **Gold‑standard intent annotations** | Human annotators (CSV workflow) | Local CSV files (`data/gold/annotations.csv`) | `commit_hash`, `intent_entities` (semicolon‑separated) |

All data are fetched automatically; no manual downloads are required.

## Model Strategy
- **Phi‑3‑mini** – `microsoft/phi-3-mini-4bit-gguf` (≈ 3 B params).  
- **Gemma‑2‑2b** – `google/gemma-2-2b-it-4bit-gguf` (≈ 2 B params).  
- **Llama‑3.2‑3B** – `meta-llama/Meta-Llama-3.2-3B-Instruct-4bit` (≈ 3 B params).  

All models are loaded with `bitsandbytes` 4‑bit quantization, `device_map="auto"` (CPU on CI), deterministic decoding (`do_sample=False`, `temperature=0`), and a per‑commit timeout of 60 s.

## Entity Extraction Methodology
1. **Surface Entities** – Regex patterns for:  
   - File paths (`[a-zA-Z0-9_./-]+\\.(py|md|rst)`)  
   - Function signatures (`def\\s+[a-zA-Z_][a-zA-Z0-9_]*\\s*\\(`)  
   - Class definitions (`class\\s+[A-Z][a-zA-Z0-9_]*\\s*:`)  
   - Imports (`import\\s+[a-zA-Z0-9_.]+`, `from\\s+[a-zA-Z0-9_.]+\\s+import`)  
   - Version numbers (`\\d+\\.\\d+\\.\\d+`)  
   - Variable assignments (`[a-zA-Z_][a-zA-Z0-9_]*\\s*=`)  

   Each candidate is cross‑checked with `git grep -w` and parsed via Python `ast` to confirm existence in the repository; a `verified` flag is set accordingly.

2. **Technical Intent Entities** – Zero‑shot classification using `facebook/bart-large-mnli` loaded in 8‑bit mode. The classifier receives each sentence from the human diff (or generated doc) and predicts whether it expresses intent (label “entailment”) vs. non‑intent (“contradiction”). Calibration is performed **only on the [deferred] calibration subset** of the gold annotations to set a confidence threshold achieving κ ≥ 0.6. If κ falls below 0.6, the pipeline falls back to a keyword‑heuristic extractor (keywords: because, fix, improve, handle, prevent). All extracted entities are stored as `EntitySet` JSON objects and validated against the `EntitySet` definition in `project.schema.yaml`. Additionally, each intent entity is verified against the repository codebase (via `git grep` and AST) to satisfy FR‑006.

## Scoring & Metrics
- **Precision** = TP / (TP + FP) per category.  
- **Recall** = TP / (TP + FN) per category.  
- **Surface hallucination rate** = proportion of generated surface entities not found in the repository codebase.  
- **Intent hallucination rate** = proportion of generated intent entities that are not supported by any codebase token or gold intent annotation.  

Metrics are written to `data/processed/fidelity_metrics.csv` and each row conforms to the `FidelityMetric` schema. Bootstrapped 95 % confidence intervals are computed `[deferred]`.

## Statistical Analysis Plan
1. **Power Analysis** (Phase 0) estimates ≥80 % power for a Friedman test with 500 samples, α = 0.05, medium effect size (f = 0.25). The default CI run uses 200 samples per model; the final full‑scale run will use 500 samples to achieve the target power.
2. **Normality test** – Shapiro‑Wilk on intent‑precision scores (α = 0.05).  
3. **Primary test** – If non‑normal, Friedman chi‑square (`scipy.stats.friedmanchisquare`). If normal, repeated‑measures ANOVA (`statsmodels.stats.anova.AnovaRM`) with Mauchly’s sphericity check.  
4. **Multiple‑comparison correction** – Holm‑Bonferroni across the three metrics; if the overall test is significant, a Nemenyi post‑hoc test controls pairwise model comparisons.  
5. **Effect sizes** – Kendall’s W for Friedman; η² for ANOVA.  
6. **Reporting** – `results/statistics.json` and a human‑readable `results/statistics.md` include p‑values, corrected p‑values, effect sizes, and reference the originating rows in `fidelity_metrics.csv`. If the power estimate falls below 0.8, the report flags the findings as exploratory.

## Compute Feasibility
- **CPU‑only**: 4‑bit models use < 600 MB each; sequential loading keeps RAM < 2 GB.  
- **CI runtime**: Default stratified subset of a representative number of samples per model ≈ 3 h; adaptive down‑sampling ensures total wall‑clock ≤ 6 h.  
- **Caching**: Model weights cached in `models/` across runs; GitHub API rate limits respected via `tqdm`‑wrapped request loops.

## Risks & Mitigations (re‑stated)
| Risk | Mitigation |
|------|------------|
| Generation timeout | Adaptive sample reduction; strict 60 s per‑commit limit. |
| Insufficient doc diffs | Skip repo, log warning, abort if total < 500 (SC‑001). |
| Intent classifier under‑performs | Calibration; automatic fallback to keyword heuristic; κ enforcement. |
| Hallucination verification misses entities | Dual verification (git grep + AST); log unmatched tokens for manual review. |
| Low statistical power | Monte‑Carlo power analysis; flag exploratory if power < 0.8. |
| Schema drift | Contract tests executed on every CI run; version bump forces re‑validation. |

---

