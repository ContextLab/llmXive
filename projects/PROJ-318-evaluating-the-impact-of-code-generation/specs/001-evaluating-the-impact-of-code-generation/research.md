# Research: Evaluating the Impact of Code Generation Models on Code Documentation Completeness

## Executive Summary
We quantify how well the `Salesforce/codegen-350M-mono` model can generate docstrings that **cover the parameters** defined in a method’s AST signature, compared with the existing human‑written docstrings in a stratified sample of top‑tier PyPI packages (plus a supplemental low‑tier sample). The **primary metric** is a **Composite Documentation Completeness Score** (0.6 × Parameter Coverage + 0.4 × Description Coverage), with **Parameter Coverage** retained as the essential AST‑grounded component. Secondary metrics capture Return‑Value Coverage, Exception Coverage, Description Coverage, and an auxiliary **Semantic Similarity** score (all‑MiniLM‑L6‑v2). A **baseline “signature‑copy” model** provides a control for circularity. The primary statistical evidence is a **Wilcoxon signed‑rank test on method‑level paired Composite Scores**, complemented by a repository‑level aggregate test and baseline comparison.

## Dataset Strategy

| Dataset | Source | Access Method | Notes |
|---------|--------|---------------|-------|
| **Top‑N PyPI repositories** | PyPI JSON API (`https://pypi.org/pypi/{pkg}/json`) | Programmatic HTTP GET → `repo_fetcher.py` → `data/raw/frozen_repo_list.json` (committed) | Open, no auth required; stratified across three popularity tiers (≥ 5 repos per tier). |
| **Supplemental low‑tier sample** | Same PyPI API, packages ranked 21‑100 | Same pipeline as above | Mitigates selection bias; additional repositories were added. |
| **GitHub source code** | Public GitHub URLs from the PyPI metadata | `git clone` via `git_clone.py` | Open‑source; cloning is fully automated. |
| **Sentence‑Transformer model** | Hugging Face (`sentence-transformers/all-MiniLM-L6-v2`) | `sentence_transformers` library download | Small CPU‑friendly model; verified open source. |

No gated datasets are required; all sources are directly downloadable on a CI runner.

## Model & Methodology

### LLM Generation
- **Model**: `Salesforce/codegen-350M-mono`
- **Quantization**: **8‑bit** via `bitsandbytes` (CPU‑compatible)
- **Device**: CPU (`torch.device("cpu")`)
- **Temperature**: 0.2 (fixed)
- **Deterministic seeds**: `torch.manual_seed(42)`, `numpy.random.seed(42)`, `random.seed(42)` (ensures reproducibility)
- **Prompt**: Only the method signature (name, parameters, return annotation) – FR‑012
- **Max new tokens**: 64 (prevent runaway generation)
- **Generation status handling**: per‑method timeout = 30 s; status recorded (`success`, `timeout`, `error`).

### Baseline “Signature‑Copy” Control
- Generates a docstring that is exactly the method signature string.
- Coverage scores computed identically; serves as a lower bound to quantify copying effects (addresses FR‑013).

### Primary Metric – Composite Documentation Completeness Score
1. **Parameter Coverage**: `|P ∩ D| / |P|` where `P` = AST parameters, `D` = documented parameters in docstring.  
2. **Description Coverage**: average number of non‑stop‑word tokens per documented parameter (≥ 5 tokens considered satisfactory).  
3. **Composite Score**: `0.6 * ParameterCoverage + 0.4 * DescriptionCoverage`.  
4. If `human_docstring` is `null`, the record is **excluded** from the primary paired Wilcoxon test but included in descriptive aggregates (FR‑015).  
5. Empty or whitespace‑only generated docstrings receive 0.0 for both component scores and are flagged (FR‑008).

### Secondary Metrics
- **Return‑Value Coverage**: same intersection logic on `:return:` sections.  
- **Exception Coverage**: same logic on `:raises:` sections.  
- **Semantic Similarity** (FR‑004): Encode human and generated docstrings with `all‑MiniLM‑L6‑v2`; compute cosine similarity (range ‑1 to 1). Used only for descriptive reporting (Constitution VI).

### Statistical Analysis
- **Primary Test**: Wilcoxon signed‑rank test on **method‑level paired** Composite Scores (human vs. LLM) across all ≥ 2 000 paired records.  
- **Secondary Test**: Wilcoxon on **per‑repository mean** Composite Scores (human vs. LLM) to respect independence across methods.  
- **Baseline Comparison**: Wilcoxon comparing LLM Composite Scores vs. baseline signature‑copy scores (quantifies circularity).  
- **Null hypothesis** `H₀`: No median difference.  
- **Alternative**: Two‑tailed.  
- **α** = 0.05.  
- **Effect‑size threshold**: Δ > 0.05 required for practical relevance; significance reported only if both p‑value < 0.05 **and** effect size > 0.05.  
- **Power note**: With ≥ 2 000 pairs the test is well‑powered; a warning is logged if total pairs < 30 (FR‑009).  

### Bias & Scope Limitations
- **Selection bias**: Top‑20 PyPI packages tend to have higher documentation quality; mitigated by stratified sampling across three tiers and a supplemental low‑tier sample of 15 repos.  
- **Metric scope**: Composite score incorporates both structural (parameter) and narrative (description) aspects, addressing construct‑validity concerns.  
- **Circularity**: Baseline signature‑copy control quantifies the extent to which high parameter‑name coverage arises from simple copying.  
- **Null human docstrings**: Excluded from primary paired test; included in descriptive statistics with a 0.0 score (method‑level).  

## Compute Feasibility & Resource Plan
| Component | Estimated RAM | Estimated CPU time |
|-----------|---------------|--------------------|
| Repo cloning & AST extraction | ≤ 2 GB (per repo) | ~30 s per repo |
| 8‑bit CodeGen loading | ≤ 1 GB | < 1 min (once) |
| Generation (≤ 1 000 methods/repo) | ≤ 1 GB | ≤ 8 min per repo |
| Baseline copy generation | ≤ 0.2 GB | negligible |
| Coverage & similarity | ≤ 0.5 GB | < 5 min total |
| **Overall peak** | **≤ 3 GB** | **≈ 3 h** (well under 6 h limit) |

All steps run on the GitHub Actions CPU runner; the 8‑bit quantization is CPU‑compatible, satisfying Principle VII.

## Risk Mitigation
| Risk | Mitigation |
|------|------------|
| **AST parse failures** (non‑standard syntax) | Wrapped in `try/except`; log `AST_PARSE_FAIL` and continue (FR‑006). |
| **Rate limiting (PyPI / GitHub)** | Exponential backoff (1 s → 2 s → 4 s → 8 s → 16 s) with max 5 retries; abort with clear error if still failing (FR‑007). |
| **BitsAndBytes load error** | Job aborts with explicit message; **no fallback** per Principle VII. |
| **Generation timeout** | Per‑method timeout = 30 s; flagged as `generation_status="timeout"` (FR‑008). |
| **Memory overflow** | Process one repository at a time; explicit `del` and `gc.collect()` after each batch (FR‑006). |
| **Low statistical power** | Log warning when total paired records < 30 (FR‑009). |

## Conclusion
The revised pipeline satisfies **every functional requirement (FR‑001 – FR‑015)** and **all success criteria (SC‑001 – SC‑006)** while remaining within the free‑tier compute budget. By grounding the primary evidence in a Composite, AST‑grounded score, providing a baseline control for circularity, and employing a method‑level paired Wilcoxon test, the study delivers a reproducible, constitution‑compliant answer to the research question.

---


