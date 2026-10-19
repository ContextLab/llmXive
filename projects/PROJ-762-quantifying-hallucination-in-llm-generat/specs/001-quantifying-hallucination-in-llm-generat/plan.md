# Implementation Plan: Quantifying Hallucination in LLM‑Generated API Documentation

**Branch**: `001-quantifying-hallucination-in-llm-generat` | **Date**: 2026-10-18 | **Spec**: `specs/001-quantifying-hallucination-in-llm-generat/spec.md`  
**Input**: Feature specification from `/specs/001-quantifying-hallucination-in-llm-generat/spec.md`

## Summary
We will build a reproducible, CPU‑only pipeline that (1) downloads the Python subset of CodeSearchNet, (2) generates a single‑sentence API description for each function with two open‑source models (`codegen-350M` and `starcoderbase-1b`), (3) computes an entity‑overlap F1 and a semantic‑similarity score, (4) combines them into the HallucinationIndex per FR‑003, (5) extracts intrinsic code characteristics, (6) runs partial Spearman correlations (controlling for generated description length) and a multiple linear regression **excluding description length** (source‑code length only), (7) applies Bonferroni correction, (8) performs a sensitivity sweep on the HallucinationIndex classification threshold, (9) validates **both** the entity‑overlap and semantic‑similarity components against a manually annotated stratified subset, (10) compares model‑specific results, (11) fits a mixed‑effects model that includes `model` as a fixed effect to isolate model‑specific variance, (12) produces a single JSON/CSV report satisfying all functional requirements (FR‑001 – FR‑020) and success criteria (SC‑001 – SC‑007).

All steps are ordered so that data is fetched before any computation, models are run before analysis, and the final report is generated before any downstream use.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers`, `torch` (CPU‑only), `datasets`, `spacy` (`en_core_web_sm`), `radon`, `pandas`, `numpy`, `scikit-learn`, `scipy`, `statsmodels`, `seaborn`, `matplotlib`, `jsonschema`, `bitsandbytes`, `pwr` (for power analysis)  
- **Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/manual/`, `results/`)  
- **Testing**: `pytest` + contract validation against YAML schemas in `contracts/`  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU, ~7 GB RAM, ≤6 h)  
- **Constraints**: CPU‑only inference, peak RAM ≤ 7 GB, total runtime ≤ 4 h for 1 000 functions, deterministic seeding, no placeholder scores (FR‑012).  

## Decision/Rationale: Compute Feasibility & Power
- **CPU‑first**: `codegen-350M` loads in ~2 GB (16‑bit) and `starcoderbaseb` loads in ~3 GB after 4‑bit quantization. Batch size 1 keeps memory < 5 GB.  
- **No GPU Escape Hatch**: All required operations (including SBERT similarity) have faithful CPU implementations.  
- **Power Analysis**: Using the `pwr` package, detecting a Spearman ρ = 0.1 with α = 0.05 and power = 0.8 requires ≈ 825 samples. Processing **1 000** functions therefore satisfies the power requirement (SC‑001).  

## Constitution Check
| Principle | Status | Evidence / Action |
|-----------|--------|-------------------|
| I. Reproducibility | PASS | Random seeds pinned; data download uses canonical URLs; pipeline fully scriptable. |
| II. Verified Accuracy | PASS | Only verified HuggingFace URLs are referenced. |
| III. Data Hygiene | PASS | Downloads are checksummed; raw parquet files never overwritten; every transformation writes a new file. |
| IV. Single Source of Truth | PASS | Final statistics live solely in `results/final_report.json`; no hand‑typed numbers elsewhere. |
| V. Versioning Discipline | PASS | Artifact hashes updated after each major artifact creation. |
| VI. Metric Alignment | PASS | Both entity‑overlap and semantic‑similarity components are validated against a human‑annotated subset (FR‑020). |
| VII. Code‑Metric Isolation | PASS | Regression controls only for source‑code predictors; model‑specific variance is handled by separate regressions and a mixed‑effects model (FR‑010, T015). |

## Project Structure
```
specs/001-quantifying-hallucination/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── analysis_result.schema.yaml
│   └── manual_score.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```
projects/PROJ-762-quantifying-hallucination-in-llm-generat/
├── code/
│   ├── __init__.py
│   ├── config.py               # seeds, model paths, thresholds
│   ├── download.py             # fetch CodeSearchNet parquet files
│   ├── generate.py             # model inference, one‑sentence enforcement
│   ├── metrics.py              # entity extraction, F1, semantic similarity
│   ├── analyze.py              # stats, regression, sensitivity, correction
│   ├── validate.py             # manual annotation workflow & aggregation
│   └── main.py                 # orchestrates the full pipeline
├── data/
│   ├── raw/                    # parquet files
│   ├── processed/              # `records.csv`
│   └── manual/                 # human scores
├── results/
│   ├── performance_log.json
│   └── final_report.json
├── tests/
│   ├── contract/               # schema validation tests
│   └── integration/            # end‑to‑end pipeline test
└── requirements.txt
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Two model runs | Required by Principle VII to isolate model‑specific variance and by FR‑010. | Single‑model runs would conflate code‑characteristic effects with model bias. |
| Manual validation step | Required by Principle VI to ensure metric alignment (FR‑020) and by SC‑003. | Purely automated metrics lack proven factual validity. |
| CPU‑only inference | Required by compute‑feasibility gate (free‑tier runner). | GPU‑only models would exceed memory limits and breach the CPU‑first rule. |
| Stratified sampling for validation | Required to meet FR‑009 (≥ 5 % stratified) and to provide power for SC‑003. | Random sampling without stratification could produce unbalanced subsets. |
| Inclusion of model as factor / mixed‑effects model | Addresses methodology‑43d71544 concern; ensures model variance does not confound code‑metric relationships (Principle VII). | Ignoring model would violate Principle VII. |

## Tasks (Mapping to Functional Requirements)

| Task ID | Description | FR(s) Covered |
|---------|-------------|---------------|
| **T001** | `download.py`: programmatically fetch the two verified CodeSearchNet parquet files, verify checksums, store under `data/raw/`. | FR‑001 |
| **T002** | `generate.py`: load `codegen-350M` (16‑bit) and `starcoderbase-1b` (4‑bit) on CPU, generate one‑sentence descriptions, enforce deterministic truncation, record provenance metadata (`generation_id`, `timestamp`, `model_name`, `input_function_hash`). | FR‑002, FR‑018, FR‑012 |
| **T003** | `metrics.py`: extract parameters/return types from source AST (ground truth) and from generated text (using spaCy), compute entity‑overlap F1, precision‑hallucination, recall‑omission, and semantic‑similarity (SBERT cosine). Combine into HallucinationIndex per FR‑003. | FR‑003 |
| **T004** | Edge‑case handling: empty LLM output (`entity_f1=0.0`, `empty_output=True`), missing reference docstring (`skip`, `missing_docstring=True`), Radon parse failure (`NaN`, `radon_parse_failure=True`). | FR‑014, FR‑015, FR‑016 |
| **T005** | Compute intrinsic code predictors – token count, identifier‑entropy, cyclomatic complexity, naming‑style classification. | FR‑001 (via radon), FR‑004 |
| **T006** | `analyze.py`: partial Spearman correlation (FR‑019) for each predictor controlling for generated description length, then Bonferroni correction (FR‑005). | FR‑004, FR‑005 |
| **T007** | `analyze.py`: fit multiple linear regression **HallucinationIndex ~ token_count_source + identifier_entropy + cyclomatic_complexity** (per model), report β‑coefficients with 95 % CI, compute VIFs. **DescriptionLength is NOT a predictor** (Principle VII). | FR‑008 |
| **T008** | Sensitivity sweep over thresholds {0.01, 0.05, 0.1} (FR‑006) and record high‑hallucination rates. | FR‑006 |
| **T009** | `validate.py`: stratified random sample ≥ 5 % (≥ 50 items) **jointly stratified on HallucinationIndex quartiles and source token‑count deciles** → CSV template for human annotators. | FR‑009 |
| **T010** | `validate.py`: aggregate manual scores → median factual score, median entity‑F1, compute Krippendorff’s α; flag if α < 0.7. | FR‑009 |
| **T011** | `validate.py`: compute Pearson r between automated `entity_f1` and median manual entity‑F1; flag “needs review” if r < 0.7 and report 95 % CI. | FR‑011 |
| **T012** | **Semantic‑Similarity Validation (FR‑020)**: sample the same stratified subset, collect human similarity ratings (0‑1 Likert), compute Pearson r between automated SBERT similarity and human ratings; require r ≥ 0.7, otherwise flag for review. | FR‑020 |
| **T013** | **Manual Verification Workflow Orchestration (FR‑013 & FR‑017)**: `validate.py` coordinates annotation distribution, collection, senior‑reviewer adjudication (invoked when α < 0.7 or score spread > 1.0), and produces an adjudication report. | FR‑013, FR‑017 |
| **T014** | `analyze.py`: compare model‑specific regression coefficients (`codegen-350M` vs `starcoderbase-1b`), ensure absolute difference ≤ 0.15 (SC‑006). | FR‑010, SC‑006 |
| **T015** | **Mixed‑Effects Model (optional)**: fit a linear mixed‑effects model with `model` as a fixed effect and source‑code predictors as random effects to verify that model‑specific variance does not confound relationships. | FR‑010 |
| **T016** | **Power Analysis Documentation (FR‑001 & SC‑001)**: run `pwr` to compute required sample size for detecting Spearman ρ > 0.1 with α = 0.05, power = 0.8; store results in `results/power_analysis.json`. | SC‑001 |
| **T017** | **Senior Reviewer Invocation (FR‑017)**: command‑line flag `--senior-review` triggers the adjudication step; logs reviewer ID and resolution notes. | FR‑017 |
| **T018** | `main.py`: orchestrate the full pipeline, enforce runtime & memory guards (SC‑001, SC‑002) via `psutil`. | SC‑001, SC‑002 |
| **T019** | `tests/contract/`: validate `records.csv`, `manual/scores.csv`, and `final_report.json` against schemas in `contracts/`. | All FRs (ensures data‑hygiene, reproducibility). |

All tasks are designed to run within the free‑tier CPU budget; no GPU escape hatch is required.

---

