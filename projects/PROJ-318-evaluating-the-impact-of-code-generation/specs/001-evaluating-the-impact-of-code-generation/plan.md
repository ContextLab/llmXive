# Implementation Plan: Evaluating the Impact of Code Generation Models on Code Documentation Completeness

**Branch**: `001-eval-code-doc-completeness` | **Date**: 2026-10-23 | **Spec**: `specs/001-eval-code-doc-completeness/spec.md`  
**Input**: Feature specification from `/specs/001-eval-code-doc-completeness/spec.md`

## Summary
The project implements a reproducible end‑to‑end pipeline that (1) selects a stratified sample of PyPI repositories, (2) extracts up to 1 000 public method signatures and any human docstrings per repository via the Python `ast` module, (3) generates docstrings for each method using the **CPU‑only full‑precision** `Salesforce/codegen-350M-mono` model (temperature = 0.2, deterministic seeds), (4) generates a **signature‑copy baseline** to quantify circularity, (5) computes **Parameter Coverage**, **Description Coverage** (averaged over **all** parameters, giving zero tokens for undocumented parameters), and a **Composite Documentation Completeness Score** (0.4 × Parameter Coverage + 0.6 × Description Coverage), (6) runs a **Wilcoxon signed‑rank test on method‑level paired Composite Scores** as the primary inferential analysis, (7) conducts an **exploratory repository‑level test** with Bonferroni correction (clearly labelled as exploratory), (8) evaluates semantic similarity as an auxiliary metric, (9) conducts a human‑evaluation sampling study, and (10) produces a final JSON report validated against contracts.

The plan explicitly addresses the circularity limitation (the prompt contains the signature) by (a) providing the baseline, (b) down‑weighting the Parameter Coverage component, and (c) reporting the baseline comparison separately. It also frames the study as assessing an **association** rather than a causal impact, respecting Constitution Principle VII.

## Technical Context

| Item | Detail |
|------|--------|
| **Language / Version** | Python 3.11 |
| **Primary Dependencies** | `datasets`, `transformers`, `torch`, `sentence-transformers`, `docstring_parser`, `scipy`, `requests`, `gitpython`, `pyyaml`, `nltk` |
| **Storage** | JSON files under `data/` (raw, processed) and a YAML state file under `state/` |
| **Testing** | `pytest` unit tests for AST parsing, coverage calculation, generation handling, baseline generation, human‑evaluation sampling, and an end‑to‑end integration test on a single repository |
| **Target Platform** | GitHub Actions free tier (Ubuntu‑latest, 2 CPU cores, ≤ 7 GB RAM, CPU‑only) |
| **Performance Goals** | ≤ 6 h total wall‑clock time, peak RAM ≤ 3 GB, ≤ 1 000 methods per repo |
| **Constraints** | Full‑precision model loading on CPU, temperature = 0.2, deterministic seeds via `seed_manager.py`, stratified sampling across three popularity tiers (≥ 5 repos per tier) plus supplemental low‑tier repos, no GPU fallback (Principle VII) |

## Constitution Check

| Principle | Compliance | Verification |
|-----------|------------|--------------|
| I. Reproducibility | ✅ | Fixed `frozen_repo_list.json`, seeded randomness, pinned `requirements.txt` |
| II. Verified Accuracy | ✅ | All citations will be validated by the Reference‑Validator Agent |
| III. Data Hygiene | ✅ | Checksums recorded; raw files immutable |
| IV. Single Source of Truth | ✅ | All figures/tables derived from JSON artifacts; no hand‑typed numbers |
| V. Versioning Discipline | ✅ | Content hashes stored in `state/projects/...yaml` |
| VI. AST‑Grounded Completeness | ✅ | Primary metric is Parameter Coverage (AST‑grounded); Composite score uses it as a weighted component |
| VII. Deterministic Generation | ✅ | Full‑precision CPU load, temperature = 0.2, fixed seeds via `seed_manager.py`; no GPU fallback |

## Project Structure

```
specs/001-eval-code-doc-completeness/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   └── results.schema.yaml
└── tasks.md               # generated later

code/
├── requirements.txt
├── utils/
│   ├── api_helpers.py          # backoff, retry logic
│   ├── ast_parser.py           # safe AST extraction
│   ├── coverage.py             # coverage & composite score logic (implements FR‑018 deterministic matching)
│   ├── repo_fetcher.py          # PyPI list, stratified sampling, freeze
│   ├── git_clone.py            # Clone repos via GitHub REST API
│   └── seed_manager.py         # deterministic seed handling
├── extract.py                  # Phase 1 – extraction
├── generate.py                 # Phase 2 – LLM generation (CPU full‑precision)
├── baseline_copy.py            # Phase 2b – signature‑copy baseline
├── post_process.py            # Phase 3 – flag empty docs, add status fields
├── aggregate.py                # Phase 4 – concatenate batches (excludes null‑human records from aggregates)
├── human_eval.py               # Phase 5 – random subset human rating (FR‑017)
├── analyze.py                  # Phase 6/7/8/9 – coverage, similarity, primary Wilcoxon, exploratory test, report
└── data/
    ├── raw/
    │   ├── frozen_repo_list.json
    │   └── repos/                 # per‑repo extraction JSONs (≤ 1 000 rows each)
    └── processed/
        ├── generation_batch_*.json
        ├── generation_batch_*_cleaned.json
        ├── baseline_batch_*.json
        ├── results.json
        ├── results_with_coverage.json
        ├── results_with_scores.json
        ├── final_report.json
        ├── flagged_records.json
        └── human_eval_results.json
```

## Phase‑by‑Phase Mapping of Functional Requirements & Success Criteria

| Phase | Script | FRs Covered | SCs Covered |
|-------|--------|--------------|-------------|
| **0 – Repo List Freeze** | `utils/repo_fetcher.py` | FR‑010 (stratified sampling + low‑tier supplement) | — |
| **1 – Extraction** | `extract.py` | FR‑001, FR‑006, FR‑015 (null handling) | SC‑002 |
| **2 – Generation** | `generate.py` | FR‑002, FR‑006, FR‑007 (rate‑limit handling), FR‑012 (prompt from signature) | SC‑004 |
| **2b – Baseline Copy** | `baseline_copy.py` | FR‑013 (circularity control) | — |
| **3 – Post‑process** | `post_process.py` | FR‑008 (empty‑docstring flag), FR‑015 (null‑human handling) | — |
| **4 – Aggregation** | `aggregate.py` | FR‑006 (batch‑wise memory handling), **Excludes null‑human records from per‑repo aggregates** (addresses FR‑015 bias) | — |
| **5 – Human Evaluation Sampling** | `human_eval.py` | FR‑017 (random subset Likert) | SC‑007 |
| **6 – Coverage Calculation** | `analyze.py --step=coverage` | FR‑003, FR‑011 (description coverage over **all** parameters), FR‑013 (baseline diagnostic), FR‑014 (per‑repo aggregation), **FR‑018 deterministic token‑exact matching** (implemented in `coverage.py`) | SC‑001, SC‑002 |
| **7 – Semantic Similarity** | `analyze.py --step=similarity` | FR‑004 (auxiliary metric) | SC‑003 |
| **8 – Primary Statistical Testing** | `analyze.py --step=stats` | Primary: Wilcoxon signed‑rank test on **method‑level paired Composite Scores** (human vs. LLM). Baseline: LLM vs. signature‑copy (circularity). | SC‑001, SC‑006 |
| **8b – Exploratory Repository‑Level Test** | `analyze.py --step=exploratory` | Exploratory Wilcoxon on per‑repo means with Bonferroni correction (clearly labelled exploratory). | — |
| **9 – Reporting** | `analyze.py --step=final_report` | FR‑013 (document limitation), FR‑015 (null‑human inclusion in descriptive stats) | SC‑001, SC‑005 |
| **10 – Reproducibility Checks** | `scripts/verify_repro.sh` | FR‑006 (checksum verification) | — |

All functional requirements (FR‑001 – FR‑017) and success criteria (SC‑001 – SC‑007) are explicitly addressed.

## Compute Feasibility (CPU‑First)

| Component | Peak RAM | Approx. CPU time |
|-----------|----------|------------------|
| Repo cloning & AST extraction | ≤ 2 GB (per repo) | ~30 s per repo |
| CodeGen load (full‑precision CPU) | ≤ 1 GB | < 1 min (once) |
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


