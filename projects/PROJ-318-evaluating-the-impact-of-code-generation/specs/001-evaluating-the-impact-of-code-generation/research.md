# Research: Evaluating the Impact of Code Generation Models on Code Documentation Completeness

## Executive Summary
This study quantifies how well the `Salesforce/codegen-350M-mono` model can generate docstrings that cover the parameters defined in a method’s AST signature, compared with the existing human‑written docstrings in the top PyPI repositories. The primary metric is an **AST‑grounded Parameter Coverage Score**; secondary metrics capture **Return‑Value Coverage**, **Exception Coverage**, and an auxiliary **Semantic Similarity Score** (all‑MiniLM‑L6‑v2) for contextual reporting only. A Wilcoxon signed‑rank test evaluates whether the LLM’s coverage differs significantly from the human baseline at α = 0.05.

## Dataset Strategy

| Dataset | Source | Access Method | Notes |
|---------|--------|---------------|-------|
| **Top‑N PyPI repositories** | PyPI JSON API + GitHub | Programmatic HTTP calls (`https://pypi.org/pypi/{pkg}/json`) → `git clone` of the `source_url` field | The list is fetched **once**, saved to `data/raw/frozen_repo_list.json`, and committed. Subsequent runs read this frozen file, guaranteeing reproducibility (Constitution I). |
| **Repository source code** | Public GitHub repos | `git clone` (no authentication required) | All repositories are open‑source; cloning is fully automated. |
| **Sentence‑Transformer model** | Hugging Face (`sentence-transformers/all-MiniLM-L6-v2`) | `sentence_transformers` library download | Small CPU‑friendly model; verified open source. |
| **Supplemental random sample** | PyPI JSON API | Same method as above, selecting a moderate number of medium‑star packages at random | Mitigates selection‑bias concerns; analyzed separately. |

*No alternative dataset is required* because the above sources are fully open and directly downloadable on a CI runner. The frozen repo list ensures the “top‑20” snapshot is reproducible.

## Model & Methodology

### Model Selection
- **LLM**: `Salesforce/codegen-350M-mono`
  - **Quantization**: 4‑bit via `bitsandbytes` (mandatory; no fallback).
  - **Device**: CPU (`torch.device("cpu")`).
  - **Temperature**: 0.2 (fixed per Constitution VII).
  - **Maximum new tokens**: 64 (prevents runaway generation).

### Metric Definitions
1. **Parameter Coverage Score (Primary)**
   - Extract AST parameters (`ast` module) → list `P`.
   - Parse docstring parameters via `docstring_parser` → list `D`.
   - Score = `|P ∩ D| / |P|`. Excludes `self`/`cls`. Complex type hints not mentioned count as unmatched.
2. **Return‑Value Coverage (Secondary)**
   - Same set‑intersection logic applied to `:return:` sections when present. Reported for completeness but **not** used in the primary hypothesis test.
3. **Exception Coverage (Secondary)**
   - Same logic applied to `:raises:` sections. Also reported only as auxiliary information.
4. **Semantic Similarity (Auxiliary)**
   - Encode human and generated docstrings with `all‑MiniLM‑L6‑v2`.
   - Compute cosine similarity (range ‑1 to 1). Used only for descriptive reporting (Constitution VI).

### Statistical Analysis
- **Test**: Wilcoxon signed‑rank (paired) on the two coverage vectors (parameter coverage only for the hypothesis).
- **Null hypothesis** `H₀`: No median difference between human and LLM parameter coverage scores.
- **Alternative hypothesis** `H₁`: Two‑tailed difference.
- **α** = 0.05.
- **Minimum Effect Size (MES)**: Δ > 0.05 required for practical relevance; both statistical significance and MES must be satisfied for a “significant” finding.
- **Power note**: With ≥ 2 000 paired observations (20 repos × ≤ 1 000 methods), the test is well‑powered; a warning will be logged if the actual pair count falls below 30.

### Bias & Scope Limitations
- **Selection Bias**: Top‑20 PyPI packages tend to have higher‑quality human docstrings. Findings are interpreted with this bias acknowledged; the supplemental random sample (5 medium‑star repos) provides a sanity check on generality.
- **Metric Scope**: Parameter Coverage Score captures only the presence of parameter names. It does **not** assess the quality of explanations, return‑value descriptions, or overall narrative completeness. Those aspects are reported via the secondary Return‑Value and Exception Coverage scores but are excluded from the primary hypothesis test, satisfying Constitution Principle VI.

## Compute Feasibility & Resource Plan
| Component | Estimated RAM | Estimated CPU time |
|-----------|---------------|--------------------|
| Repo cloning & AST extraction | ≤ 2 GB (per repo) | ~30 s per repo |
| 4‑bit CodeGen loading | 0.8 GB – 1 GB | Brief load |
| Generation (≤ 1 000 methods/repo) | ≤ 1 GB (model + batch) | ≤ 8 min per repo |
| Coverage & similarity calculation | ≤ 0.5 GB | < 5 min total |
| Overall pipeline | **Peak ≤ 4 GB** | **≈ 3 h** (well under 6 h limit) |

All steps run on the GitHub Actions CPU runner; no GPU escape hatch is required.

## Risk Mitigation
| Risk | Mitigation |
|------|------------|
| **AST parse failures** (non‑standard syntax) | Wrap `ast.parse` in `try/except`; log `AST_PARSE_FAIL` and skip the file. |
| **Rate limiting (PyPI / GitHub)** | Exponential backoff (1 s, 2 s, 4 s, 8 s) with a max of 5 retries; abort with clear error if still failing. |
| **Quantization load error** | Job aborts with explicit error; **no fallback** to higher‑bit precision (Constitution VII). |
| **Generation timeout** | Enforce per‑method timeout of 30 s; skip and flag as `generation_status="timeout"` if exceeded. |
| **Memory overflow** | Process one repository at a time; `del` intermediate objects and call `gc.collect()` after each repo. |

## Conclusion
The proposed pipeline satisfies every functional requirement and success criterion while staying within the free‑tier compute budget. By grounding the primary metric in AST‑derived parameter lists, adding secondary coverage metrics, acknowledging selection bias, and explicitly aligning all outputs with validated contracts, the study adheres to Principle VI. The statistical plan includes both significance testing and a practical effect‑size threshold, delivering a rigorous answer to the research question.

---


