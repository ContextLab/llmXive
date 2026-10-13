# Implementation Plan: Evaluating the Impact of Code Generation Models on Code Documentation Completeness

**Branch**: `001-eval-code-doc-completeness` | **Date**: 2026-10-13 | **Spec**: `specs/001-eval-code-doc-completeness/spec.md`  
**Input**: Feature specification from `/specs/001-eval-code-doc-completeness/spec.md`

## Summary
The project delivers an end‑to‑end, reproducible pipeline that (1) builds a frozen list of the top PyPI packages **plus** an additional stratified sample of multiple lower‑tier packages (randomly selected from ranks beyond the top tier, up to rank 100, 15 repos) to improve external validity, (2) extracts up to 1 000 public method signatures and any existing human docstrings per repository using the Python `ast` module, (3) generates docstrings for every extracted method with the `Salesforce/codegen-350M-mono` model quantized to **8‑bit** via `bitsandbytes` (CPU‑only, temperature = 0.2, deterministic seeds), (4) generates a **baseline “signature‑copy”** docstring for each method to control for circularity, (5) computes a **Composite Documentation Completeness Score** (`0.6 * ParameterCoverage + 0.4 * DescriptionCoverage`) and a **Parameter Coverage Score** as the AST‑grounded component, (6) runs a **Wilcoxon signed‑rank test on method‑level paired Composite Scores** (primary) and a secondary test on per‑repository aggregated scores, and (7) reports results with full diagnostics. All steps respect the constitution’s constraints and the free‑tier GitHub Actions compute budget.

## Technical Context
| Item | Detail |
|------|--------|
| **Language / Version** | Python 3.11 |
| **Primary Dependencies** | `datasets`, `transformers`, `torch`, `bitsandbytes`, `sentence-transformers`, `docstring_parser`, `scipy`, `requests`, `gitpython`, `pyyaml` |
| **Storage** | JSON files under `data/` (raw, processed) and a YAML state file under `state/` |
| **Testing** | `pytest` unit tests for AST parsing, coverage calculation, generation‑status handling, baseline copy generation, and an end‑to‑end integration test on a single repository |
| **Target Platform** | GitHub Actions free tier (Ubuntu‑latest, 2 CPU cores, ≤ 7 GB RAM, CPU‑only) |
| **Performance Goals** | ≤ 6 h total wall‑clock time, peak RAM ≤ 3 GB, ≤ 1 000 methods per repo |
| **Constraints** | 8‑bit quantization, temperature = 0.2, deterministic seeds, ≤ 1 000 methods per repo, stratified sampling across three popularity tiers (≥ 5 repos per tier) plus 15 low‑tier repos; **no GPU fallback** |

## Constitution Check
| Principle | Compliance | Verification |
|-----------|------------|--------------|
| I. Reproducibility | ✅ | Fixed `frozen_repo_list.json`, seeded randomness, `requirements.txt` version‑pinned |
| II. Verified Accuracy | ✅ | All citations will be validated by the Reference‑Validator Agent |
| III. Data Hygiene | ✅ | Checksums recorded; raw files immutable |
| IV. Single Source of Truth | ✅ | All figures/tables derived from JSON artifacts; no hand‑typed numbers |
| V. Versioning Discipline | ✅ | Content hashes stored in project state YAML |
| VI. AST‑Grounded Completeness | ✅ | **Primary metric** is the Composite Documentation Completeness Score; **Parameter Coverage** remains the AST‑grounded component per the constitution |
| VII. Deterministic Generation | ✅ | 8‑bit quantization, temperature = 0.2, fixed random seeds via `seed_manager.py`; no GPU fallback |

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
│   ├── api_helpers.py            # backoff, retry logic
│   ├── ast_parser.py             # AST extraction, safe parsing
│   ├── coverage.py               # Parameter/Description coverage, composite score
│   ├── repo_fetcher.py           # PyPI list & frozen JSON, stratified + low‑tier supplement
│   ├── git_clone.py              # Clone repos
│   └── seed_manager.py           # deterministic seed handling
├── extract.py                    # Phase 1 – extraction
├── generate.py                   # Phase 2 – LLM generation (8‑bit)
├── baseline_copy.py              # Phase 2b – signature‑copy baseline
├── post_process.py               # Phase 3 – clean/flag generations
├── aggregate.py                  # Phase 4 – concatenate batches
├── analyze.py                    # Phase 5/6/7/8 – coverage, similarity, stats, report
└── data/
    ├── raw/
    │   ├── frozen_repo_list.json
    │   └── repos/                 # per‑repo extraction JSONs
    └── processed/
        ├── generation_batch_*.json
        ├── generation_batch_*_cleaned.json
        ├── baseline_batch_*.json
        ├── results.json
        ├── results_with_coverage.json
        ├── results_with_scores.json
        ├── final_report.json
        └── flagged_records.json
```

## Phase‑by‑Phase Mapping of Functional Requirements & Success Criteria
| Phase | Script | FRs Covered | SCs Covered |
|-------|--------|--------------|-------------|
| **0 – Repo List Freeze** | `utils/repo_fetcher.py` | FR‑010 (stratified sampling + low‑tier supplement) | — |
| **1 – Extraction** | `extract.py` | FR‑001, FR‑006, FR‑015 | SC‑002 |
| **2 – Generation** | `generate.py` | FR‑002, FR‑006, FR‑007 (rate‑limit handling), FR‑012 (prompt from signature) | SC‑004 |
| **2b – Baseline Copy** | `baseline_copy.py` | FR‑013 (circularity control) | — |
| **3 – Post‑process** | `post_process.py` | FR‑008 (empty‑docstring flag), FR‑015 (null handling) | — |
| **4 – Aggregation** | `aggregate.py` | FR‑006 (memory‑friendly batch handling) | — |
| **5 – Coverage Calculation** | `analyze.py --step=coverage` | FR‑003, FR‑011 (description coverage), FR‑013 (circularity diagnostic), FR‑014 (per‑repo aggregation) | SC‑001, SC‑002 |
| **6 – Semantic Similarity** | `analyze.py --step=similarity` | FR‑004 (auxiliary metric) | SC‑003 |
| **7 – Statistical Testing** | `analyze.py --step=stats` | **Primary**: Wilcoxon signed‑rank on **method‑level paired Composite Scores**; **Secondary**: repository‑level aggregated scores; **Baseline**: LLM vs. signature‑copy (addresses FR‑013). Also FR‑009 (power warning). | SC‑001, SC‑006 |
| **8 – Reporting** | `analyze.py --step=final_report` | FR‑013 (document limitation), FR‑015 (null‑human handling) | SC‑001, SC‑005 |
| **9 – Sensitivity Analyses** | `analyze.py --step=sensitivity` | FR‑015 (null‑human bias), FR‑222a492b (exclusion sensitivity) | — |
| **10 – Reproducibility Checks** | `scripts/verify_repro.sh` | FR‑006 (checksum verification) | — |

All functional requirements (FR‑001 – FR‑015) and success criteria (SC‑001 – SC‑006) are explicitly addressed by one or more phases.

## Compute Feasibility (CPU‑First)
| Component | Peak RAM | Approx. CPU time |
|-----------|----------|------------------|
| Repo cloning & AST extraction | ≤ 2 GB (per repo) | On the order of tens of seconds per repository. |
| 8‑bit CodeGen load | ≤ 1 GB | < 1 min (once) |
| Generation (≤ 1 000 methods/repo) | ≤ 1 GB | ≤ 8 min per repo |
| Baseline copy generation | ≤ 0.2 GB | negligible |
| Coverage & similarity | ≤ 0.5 GB | < 5 min total |
| **Overall peak** | **≤ 3 GB** | **≈ 3.5 h** (well under 6 h limit) |

All steps run on the GitHub Actions CPU runner; the 8‑bit quantization is CPU‑compatible, satisfying Principle VII.

## Risk Mitigation
| Risk | Mitigation |
|------|------------|
| **AST parse failures** (non‑standard syntax) | Wrapped in `try/except`; log `AST_PARSE_FAIL` and continue (FR‑006). |
| **Rate limiting (PyPI / GitHub)** | Exponential backoff (1 s → 2 s → 4 s → 8 s → 16 s) with max 5 retries; abort with clear error if still failing (FR‑007). |
| **BitsAndBytes 8‑bit load error** | Job aborts with explicit message; **no fallback** per Principle VII. |
| **Generation timeout** | Per‑method timeout = 30 s; flagged as `generation_status="timeout"` (FR‑008). |
| **Memory overflow** | Process one repository at a time; explicit `del` and `gc.collect()` after each batch (FR‑006). |
| **Low statistical power** | Log warning when total paired records < 30 (FR‑009). |
| **Circularity** | Baseline signature‑copy control quantifies the extent of pure copying. |
| **Selection bias** | Added supplemental low‑tier sample (15 repos) and stratified sampling across three tiers. |
| **Deterministic generation** | Seed manager sets `torch.manual_seed(42)`, `numpy.random.seed(42)`, `random.seed(42)` before model load (Principle VII). |

## Timeline (within a single CI job)
1. **0‑5 min** – Freeze repo list (once, cached).  
2. **5‑45 min** – Clone all target repositories (parallelized 2 at a time).  
3. **45‑90 min** – Extraction (AST).  
4. **90‑180 min** – Generation (LLM) + baseline copy.  
5. **180‑210 min** – Post‑process & aggregation.  
6. **210‑240 min** – Coverage & description scores.  
7. **240‑260 min** – Semantic similarity.  
8. **260‑280 min** – Wilcoxon test (method‑level) + per‑repo aggregate test.  
9. **280‑295 min** – Sensitivity analyses (null‑human exclusion, baseline comparison).  
10. **295‑300 min** – Verification, checksum, and test suite.

All steps are scripted to be idempotent; re‑runs start from the last successful artifact.

## Deliverables
- `data/raw/frozen_repo_list.json` (reproducible repository list)  
- `data/raw/repos/*.json` (extracted signatures, ≤ 1 000 per repo)  
- `data/processed/generation_batch_*.json` (LLM outputs, status fields)  
- `data/processed/baseline_batch_*.json` (signature‑copy baseline)  
- `data/processed/results.json` (concatenated raw batches)  
- `data/processed/results_with_coverage.json` (coverage scores)  
- `data/processed/results_with_scores.json` (semantic similarity)  
- `data/processed/final_report.json` (Wilcoxon test, significance flag, diagnostics)  
- Corresponding JSON schemas in `contracts/` (validated by test suite)  

---


