# Implementation Plan: Evaluating the Effectiveness of LLMs for Detecting Code Smells

**Branch**: `001-gene-regulation` | **Date**: 2026-10-24 | **Spec**: `specs/001-evaluating-the-effectiveness-of-llms-for/spec.md`  
**Input**: Feature specification from `specs/001-evaluating-the-effectiveness-of-llms-for/spec.md`

## Summary
The project will compare rule‑based detection (Pylint + radon) with semantic detection (sentence‑transformer embeddings + CodeLlama‑7B‑Instruct‑GGUF) on a sampled set of Python functions. The pipeline consists of:

1. **Dataset Verification & Sampling** – Verify that the code dataset has a confirmed, programmatic download URL (see Constitution Check). If verified, sample 800 Python functions (seed = 42) from the **verified** CodeSearchNet Python subset (`code-search-net/python`).  
2. **Static Baseline Generation** – Compute LOC, cyclomatic complexity, **nesting depth** via `radon` and generate deterministic Pylint smell labels. The resulting CSV will contain the columns required by `static_baseline.schema.yaml`: `id`, `source_code`, `loc`, `cyclomatic_complexity`, `nesting_depth`, `static_labels`, `normalized_static_labels`.  
3. **Canonical Label Mapping** – Translate raw Pylint error codes and LLM‑generated names to a shared taxonomy (Table 1) to ensure comparable categories across methods.  
4. **Semantic Feature Extraction** – Produce MiniLM embeddings and run the quantised CodeLlama model on CPU (batch ≤ 10) to obtain LLM smell labels. A canonicalisation step maps raw LLM output to the same taxonomy.  
5. **Statistical Comparison** –  
   - Perform **McNemar’s test** (α = 0.05) on paired binary outcomes per smell category **only if ≥ 30 discordant pairs** are observed; otherwise pool categories or use Fisher’s exact test.  
   - Apply **Bonferroni correction** for multiple comparisons.  
   - Conduct an **a priori power analysis** (α = 0.05, power = 0.80, MDES = 0.15) estimating that ≥ 70 discordant pairs are needed; with 800 functions we expect ≥ 100 discordant pairs for common smells, satisfying the requirement.  
   - Fit **binary logistic regression** models for static‑only vs. not and LLM‑only vs. not, and an optional **multinomial logistic regression** for the three mutually exclusive outcomes (static‑only, LLM‑only, both). Predictors are structural metrics and semantic embedding statistics; VIF < 5 is enforced before fitting (FR‑010).  
   - Conduct a **sensitivity sweep** of LOC thresholds {50, 100, 150} and report the **proportion of static‑only detections** at each threshold (no FP/FN rates).  
   - Record **resource usage** (peak RAM, CPU %, batch inference time) for every LLM batch (≤ 50 functions).  
   - Summarise complementarity without implying superiority; results are framed as evidence that the two detectors capture overlapping but distinct smell sets (Principle VII).

All steps are deterministic, reproducible, and constrained to ≤ 7 GB RAM, 2 CPU cores, ≤ 6 h total runtime on a GitHub Actions free‑tier runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `datasets`, `pandas`, `radon`, `pylint`, `sentence-transformers`, `llama-cpp-python`, `scikit-learn`, `statsmodels`, `numpy`, `gc`  
- **Storage**: Local filesystem (`data/`, `results/`) with immutable raw files and checksummed derivatives.  
- **Testing**: `pytest` with contract tests against JSON/YAML schemas.  
- **Target Platform**: Linux (GitHub Actions free tier).  
- **Constraints**: CPU‑only inference; batch size ≤ 10 for LLM; peak RAM ≤ 7 GB; total wall‑clock ≤ 6 h.  

## Constitution Check
| Principle | Status | Reference in Plan |
|-----------|--------|-------------------|
| I. Reproducibility | PASS | Fixed random seed (42), deterministic dataset sampling, `requirements.txt` pinned, immutable raw data, checksum logging. |
| II. Verified Accuracy | PASS | Uses verified CodeSearchNet Python subset; verification step aborts if URL not verified. |
| III. Data Hygiene | PASS | Raw data never overwritten; all transformations write new files; checksums recorded in `data/checksums.txt`. |
| IV. Single Source of Truth | PASS | Each result in `results/` directly references rows in `data/processed/` via unique `id`. |
| V. Versioning Discipline | PASS | Content hashes for all artifacts; timestamps updated on change. |
| VI. Resource‑Constrained Execution | PASS | CPU‑only LLM inference, batch ≤ 10, explicit RAM monitoring, GC between batches. |
| VII. Dual‑Mode Detection Validation | PASS | McNemar’s test, logistic regressions, VIF check, explicit categorisation of static‑only, LLM‑only, and overlap detections. |

## FR / SC Mapping to Phases
| FR / SC | Phase | Description |
|--------|-------|-------------|
| FR‑001 | Phase 0 – Dataset Verification & Sampling | Verify dataset URL, then sample 800 functions (seed = 42). |
| FR‑002 | Phase 1 – Structural Metrics | Compute LOC, CC, **nesting depth** via `radon`. |
| FR‑003 | Phase 1 – Static Labels | Run `pylint`, normalize codes to canonical smell names (Table 1). |
| FR‑004 | Phase 2 – LLM Inference | Load CodeLlama‑7B‑Instruct‑GGUF (4‑bit) with `llama-cpp-python` on CPU. |
| FR‑005 | Phase 2 – Embeddings | Compute MiniLM‑L6‑v2 embeddings for each function. |
| FR‑006 | Phase 3 – McNemar | Perform McNemar’s test (α = 0.05) with Bonferroni correction; require ≥ 30 discordant pairs. |
| FR‑007 | Phase 3 – Logistic Regression | Fit binary logistic models (static‑only, LLM‑only) and optional multinomial model after VIF < 5. |
| FR‑008 | Phase 2 – Resource Profiling | Log peak RAM, CPU %, and batch inference time. |
| FR‑009 | Phase 3 – Sensitivity Sweep | Sweep LOC thresholds {50, 100, 150} and report proportion of static‑only detections per threshold. |
| FR‑010 | Phase 3 – VIF Check | Compute VIF; exclude predictors with VIF ≥ 5. |
| SC‑001 | Phase 3 – Correlation Reporting | Report correlation of LOC with static‑only regression coefficients. |
| SC‑002 | Phase 3 – Correlation Reporting | Report correlation of semantic embedding statistics with LLM‑only regression coefficients. |
| SC‑003 | Phase 3 – Significance Reporting | Report McNemar p‑values per smell category. |
| SC‑004 | Phase 2 – Feasibility Monitoring | Verify ≤ 6 h runtime and ≤ 7 GB RAM. |
| SC‑005 | Phase 0 – Data Validity Check | Ensure ≥ 95 % of sampled functions have all required fields. |

## Project Structure
```text
specs/001-evaluating-the-effectiveness-of-llms-for/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── static_baseline.schema.yaml
│   └── statistical_report.schema.yaml
└── tasks.md   # generated later
```

```text
projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/
├── code/
│   ├── __init__.py
│   ├── config.py                # paths, seeds, hyper‑params
│   ├── data_pipeline.py         # FR‑001‑003
│   ├── semantic_analysis.py     # FR‑004‑005, FR‑008
│   ├── statistical_analysis.py  # FR‑006‑010, SC‑001‑005
│   └── main.py                  # orchestrator
├── data/
│   ├── raw/                     # immutable download (checksumed)
│   ├── processed/
│   │   ├── static_baseline.csv
│   │   └── semantic_analysis.json
│   └── checksums.txt
├── results/
│   ├── statistical_significance.json
│   ├── logistic_regression.json
│   └── sensitivity_report.md
├── tests/
│   ├── unit/
│   └── contract/
├── requirements.txt
└── README.md
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Dual‑mode detection | Required by FR‑003, FR‑004 and Principle VII to assess complementarity. | Single‑mode analysis would not allow McNemar’s test or overlap summary. |
| VIF & multicollinearity | Required by FR‑010 to ensure interpretable logistic coefficients. | Ignoring VIF would risk misleading inference due to collinear predictors. |
| CPU‑only LLM inference | Required by FR‑004 and Principle VI; GPU unavailable on free CI. | GPU‑based inference would violate compute constraints. |
| Batch size 10 | Guarantees RAM ≤ 7 GB on the free runner (Principle VI). | Larger batch would risk OOM failures. |
| Ground‑truth limitation | Acknowledged in research design; no external label source is available. | Assuming Pylint as ground truth would breach scientific rigor. |

---


