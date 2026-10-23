# Research: Evaluating the Impact of Code Generation Models on Code Documentation Completeness

## Executive Summary
We **assess the association** between the `Salesforce/codegen-350M-mono` model’s generated docstrings and existing human‑written docstrings in terms of **documentation completeness**. The study does **not** claim a causal impact; it measures differences while explicitly acknowledging external confounds beyond the signature‑copy baseline, framing the work as an associative analysis.

## Dataset Strategy

| Dataset | Source | Access Method | Notes |
|---------|--------|---------------|-------|
| Top‑N PyPI repositories | PyPI JSON API (`https://pypi.org/pypi/{pkg}/json`) | Programmatic GET → `repo_fetcher.py` → `data/raw/frozen_repo_list.json` (committed) | Open, no auth; stratified across three popularity tiers (≥ 5 repos per tier). |
| Supplemental low‑tier sample | Same PyPI API, packages ranked 21‑100 | Same pipeline | Mitigates selection bias. |
| GitHub source code | Public GitHub URLs from PyPI metadata | `git clone` via `git_clone.py` | Open‑source; fully automated. |
| Sentence‑Transformer model | Hugging Face (`sentence-transformers/all-MiniLM-L6-v2`) | `sentence_transformers` download | Small CPU‑friendly model; verified open source. |

All sources are directly downloadable on a CI runner; no gated data is required.

## Model & Methodology

### LLM Generation
- **Model**: `Salesforce/codegen-350M-mono`  
- **Quantization**: **Full‑precision CPU** (no bitsandbytes) – fits within the free‑tier memory budget.  
- **Device**: CPU (`torch.device("cpu")`)  
- **Temperature**: 0.2 (fixed)  
- **Deterministic seeds**: `torch.manual_seed(42)`, `numpy.random.seed(42)`, `random.seed(42)` (via `seed_manager.py`)  
- **Prompt**: Only the method signature (name, parameters, return annotation) – FR‑012  
- **Max new tokens**: 64  
- **Per‑method timeout**: 30 s; status recorded (`success`, `timeout`, `error`).  

### Baseline “Signature‑Copy” Control
- Generates a docstring that is exactly the method signature string.  
- Used to quantify how much Parameter Coverage can be achieved by trivial copying (addresses FR‑013).  

### Primary Metric – Composite Documentation Completeness Score
1. **Parameter Coverage** = `|P ∩ D| / |P|` where `P` = AST parameters, `D` = documented parameters (case‑insensitive token‑exact match per FR‑018).  
2. **Description Coverage** = average number of non‑stop‑word tokens **per parameter across all parameters** (undocumented parameters contribute 0 tokens). This resolves the denominator bias noted in earlier critiques.  
3. **Composite Score** = `0.4 * ParameterCoverage + 0.6 * DescriptionCoverage`. The weighting down‑plays the circularity‑prone Parameter Coverage while rewarding richer narrative.  
4. Records with `human_docstring = null` receive a **human Parameter Coverage of 0.0** but are **excluded from per‑repository aggregates and the primary paired Wilcoxon test** (to avoid inflating the human baseline). They remain in descriptive statistics.  
5. Empty or whitespace‑only generated docstrings receive 0.0 for both component scores and are flagged (`needs_review = true`) (FR‑008).

### Secondary Metrics
- **Return‑Value Coverage** and **Exception Coverage** (same intersection logic on `:return:` / `:raises:` sections).  
- **Semantic Similarity**: Encode human and generated docstrings with `all‑MiniLM‑L6‑v2`; compute cosine similarity (range ‑1 to 1). Used only for descriptive reporting (Constitution VI).  

### Human‑Evaluation Sampling (FR‑017)
- Randomly sample **200 method pairs** (uniform across repositories).  
- Collect 5‑point Likert ratings of “overall documentation completeness” from crowd‑source annotators (simulated locally).  
- Compute average rating; **SC‑007** requires **≥ 4.0** to claim comparable completeness.  

### Statistical Analysis
- **Primary Test**: Wilcoxon signed‑rank test on **method‑level paired Composite Scores** (human vs. LLM) across all paired records (≥ 2 000 pairs expected).  
- **Baseline Comparison**: Wilcoxon LLM vs. signature‑copy Composite Scores (quantifies circularity).  
- **Exploratory Test**: Wilcoxon on **per‑repository mean Composite Scores** (human vs. LLM) with Bonferroni correction to respect independence across methods (FR‑014). This test is clearly labelled exploratory and does not constitute the confirmatory inference.  
- **Null hypothesis** `H₀`: No median difference.  
- **Alternative**: Two‑tailed.  
- **α** = 0.05.  
- **Effect‑size threshold**: Δ > 0.05 required for practical relevance; significance reported only if both p‑value < 0.05 **and** effect size > 0.05.  
- **Power note**: Log warning if total paired records < 30 (FR‑009).  

### Bias & Scope Limitations
- **Selection bias**: Mitigated by stratified sampling across high, medium, low popularity tiers and a supplemental low‑tier sample (several repos)  
- **Metric scope**: Composite score balances structural (parameter) and narrative (description) aspects, satisfying construct validity while acknowledging the weakness of token count as a proxy.  
- **Circularity**: Baseline signature‑copy quantifies copying effect; composite weight reduced to limit its influence.  
- **Null human docstrings**: Excluded from primary paired test and per‑repo aggregates; included in overall descriptive stats with 0.0 scores (FR‑015).  

## Compute Feasibility & Resource Plan
| Component | Estimated RAM | Estimated CPU time |
|-----------|---------------|--------------------|
| Repo cloning & AST extraction | ≤ 2 GB (per repo) | ~30 s per repo |
| CodeGen loading (full‑precision CPU) | ≤ 1 GB | < 1 min (once) |
| Generation (≤ 1 000 methods/repo) | ≤ 1 GB | ≤ 8 min per repo |
| Baseline copy generation | ≤ 0.2 GB | negligible |
| Coverage & similarity | ≤ 0.5 GB | < 5 min total |
| **Overall peak** | **≤ 3 GB** | **≈ 3.5 h** (well under 6 h limit) |

All steps run on the GitHub Actions CPU runner; the full‑precision model fits within the memory budget, satisfying Principle VII.

## Risk Mitigation
| Risk | Mitigation |
|------|------------|
| AST parse failures (non‑standard syntax) | Wrapped in `try/except`; log `AST_PARSE_FAIL` and continue (FR‑006). |
| Rate limiting (PyPI / GitHub) | Exponential backoff (1 s → 2 s → 4 s → 8 s → 16 s) with max 5 retries; abort with clear error if still failing (FR‑007). |
| Model load error (bitsandbytes) | Switched to full‑precision CPU load; any load failure aborts with explicit message (Principle VII). |
| Generation timeout | Per‑method timeout = 30 s; flagged as `generation_status="timeout"` (FR‑008). |
| Memory overflow | Process one repository at a time; explicit `del` and `gc.collect()` after each batch (FR‑006). |
| Low statistical power | Log warning when total paired records < 30 (FR‑009). |
| Human‑evaluation logistics | Use deterministic random seed for sampling; store annotator ratings in `human_eval_results.json`. |
| Selection bias | Stratified sampling + low‑tier supplement; baseline control. |

## Conclusion
The revised pipeline now (a) frames the study as an **association** rather than a causal impact, (b) explicitly acknowledges and controls for the circularity inherent in prompting with the signature, (c) uses a CPU‑compatible full‑precision model to satisfy compute constraints, (d) defines Description Coverage over **all** parameters, (e) excludes null‑human records from both per‑repository aggregates and the primary paired test to avoid bias, (f) implements FR‑018 deterministic matching, (g) conducts a single primary Wilcoxon test with an exploratory, Bonferroni‑corrected secondary test, and (h) provides a clear baseline for interpretation. All functional requirements and success criteria are met within the free‑tier resource limits.

---


