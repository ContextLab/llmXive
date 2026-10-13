# Implementation Plan: Evaluating the Impact of Code Generation Models on Code Documentation Completeness

**Branch**: `001-eval-code-doc-completeness` | **Date**: 2026-10-13 | **Spec**: `specs/001-eval-code-doc-completeness/spec.md`

**Input**: Feature specification from `/specs/001-eval-code-doc-completeness/spec.md`

## Summary
The pipeline implements a reproducible end‑to‑end study that (1) extracts public method signatures and existing human docstrings from the top PyPI repositories, (2) generates docstrings for each method using the `Salesforce/codegen-350M-mono` model quantized to low‑bit precision on CPU, and (3) computes a **Parameter Coverage Score** (AST‑grounded) as the primary metric, complemented by secondary **Return‑Value Coverage**, **Exception Coverage**, and an auxiliary **Semantic Similarity Score** (all‑MiniLM‑L6‑v2). A Wilcoxon signed‑rank test evaluates whether the LLM’s coverage differs significantly from the human baseline at α = 0.05.

All steps respect the Constitution’s hard constraints, especially Principle VII’s mandatory 4‑bit quantization and fixed temperature.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**:
  - `datasets` (optional HF utilities)
  - `transformers`, `torch`, `bitsandbytes` (4‑bit CPU quantization)
  - `sentence-transformers` (all‑MiniLM‑L6‑v2)
  - `docstring_parser`
  - `scipy`
  - `requests`, `gitpython`
  - `pyyaml` (contract validation)
- **Storage**: JSON files under `data/` (raw, processed) and a YAML state file under `state/`.
- **Testing**: `pytest` (unit tests for AST parsing, coverage calculation, and end‑to‑end integration on a single repo).
- **Target Platform**: GitHub Actions free tier (Ubuntu‑latest, 2 CPU cores, ≤7 GB RAM, CPU‑only).
- **Performance Goals**: Process ≤20 repos × ≤1 000 methods/repo ≤ 6 h total runtime, peak RAM ≤ 7 GB.
- **Constraints**: No fallback to higher‑bit or 8‑bit quantization; 4‑bit quantization is **mandatory** (Principle VII). Fixed temperature = 0.2. ≤1 000 methods/repo enforced.

## Constitution Check
| Principle | Compliance | Verification |
|-----------|------------|--------------|
| I. Reproducibility | ✅ | Fixed `repo_list.json`, pinned seeds, `requirements.txt`. |
| II. Verified Accuracy | ✅ | All citations will be validated by the Reference‑Validator Agent. |
| III. Data Hygiene | ✅ | Checksums recorded in `state/projects/...yaml`; raw data never edited in place. |
| IV. Single Source of Truth | ✅ | All figures/tables derived programmatically from JSON artifacts. |
| V. Versioning Discipline | ✅ | Content hashes stored in project state YAML. |
| VI. AST‑Grounded Completeness | ✅ | Primary metric is Parameter Coverage Score derived from AST. |
| VII. Deterministic Generation | ✅ | 4‑bit quantization, temperature = 0.2, ≤1 000 methods/repo enforced. No fallback. |

## Project Structure
### Documentation (this feature)
```
specs/001-eval-code-doc-completeness/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   └── results.schema.yaml
└── tasks.md   # (generated later)
```

### Source Code (repository root)
```
projects/PROJ-318-evaluating-the-impact-of-code-generation/code/
├── requirements.txt
├── extract.py           # AST extraction & JSON export
├── generate.py          # 4‑bit CodeGen inference
├── post_process.py      # clean generated docs, add status fields
├── analyze.py           # Coverage, similarity, Wilcoxon test
├── utils/
│   ├── ast_parser.py
│   ├── coverage.py
│   └── stats.py
└── data/
    ├── raw/
    │   ├── frozen_repo_list.json
    │   └── repos/                # per‑repo extraction JSONs
    └── processed/
        ├── generation_batch_*.json
        ├── generation_batch_*_cleaned.json
        ├── results.json
        ├── results_with_coverage.json
        ├── results_with_scores.json
        └── final_report.json
```
*Structure Decision*: A single‑project layout with a dedicated `code/` directory aligns with the CLI nature of the pipeline and simplifies CI orchestration.

## Complexity Tracking
All functional requirements (FR‑001 – FR‑006) and success criteria (SC‑001 – SC‑004) are explicitly addressed by the following pipeline phases:

| Phase | FRs Covered | SCs Covered |
|-------|-------------|-------------|
| Extraction (`extract.py`) | FR‑001, FR‑006 | SC‑002 |
| Generation (`generate.py` + `post_process.py`) | FR‑002, FR‑006, VII (deterministic generation) | SC‑004 |
| **Coverage** (`analyze.py --step=coverage`) | FR‑003, FR‑004 (parameter coverage) | SC‑001, SC‑002 |
| **Return‑Value & Exception Coverage** (`analyze.py --step=coverage`) | FR‑003 (extended to return/exception) | SC‑001 (reported as secondary) |
| **Semantic Similarity** (`analyze.py --step=similarity`) | FR‑004 (auxiliary) | **SC‑003** |
| Statistical Test (`analyze.py --step=stats`) | FR‑005 | SC‑001 |
| Logging & Monitoring (shared utilities) | FR‑006 | SC‑004 |

*Note on Metric Limitations*: Parameter Coverage Score captures only the presence of parameter names. It does **not** assess the quality of explanations, return‑value or exception descriptions, or overall narrative completeness. Those aspects are reported via secondary Return‑Value and Exception Coverage scores but are excluded from the primary hypothesis test, satisfying Constitution Principle VI.

*Note on Selection Bias*: The top‑20 PyPI packages are likely to have higher‑quality human docstrings. To mitigate this bias, we also sample **Multiple additional medium‑star PyPI repositories** (randomly selected) and run the same pipeline; results are reported separately for transparency.

## Risk Mitigation
| Risk | Mitigation |
|------|------------|
| **AST parse failures** (non‑standard syntax) | Wrap `ast.parse` in `try/except`; log `AST_PARSE_FAIL` and skip the file. |
| **Rate limiting (PyPI / GitHub)** | Exponential backoff (1 s, 2 s, 4 s, 8 s) with a max of 5 retries; abort with clear error if still failing. |
| **Quantization load error** | Job aborts with explicit error; **no fallback** to higher‑bit precision (Constitution VII). |
| **Generation timeout** | Enforce per‑method timeout of 30 s; skip and flag as `generation_status="timeout"` if exceeded. |
| **Memory overflow** | Process one repository at a time; `del` intermediate objects and call `gc.collect()` after each repo. |

## Final Report Output
The statistical analysis writes `data/processed/final_report.json` conforming to `contracts/results.schema.yaml` with the following fields:

- `total_pairs` (int)
- `human_scores` (list of floats)
- `llm_scores` (list of floats)
- `wilcoxon_statistic` (float)
- `wilcoxon_p_value` (float)
- `significance` (bool)
- `execution_time_seconds` (float)

## Conclusion
The proposed pipeline satisfies every functional requirement and success criterion while staying within the free‑tier compute budget. By grounding the primary metric in AST‑derived parameter lists, adding secondary coverage metrics, acknowledging selection bias, and aligning all outputs with validated contracts, the study adheres to all Constitution principles and delivers a rigorous answer to the research question.

---


