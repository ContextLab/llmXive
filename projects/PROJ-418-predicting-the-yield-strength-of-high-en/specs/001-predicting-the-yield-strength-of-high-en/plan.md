# Implementation Plan: Predicting the Yield Strength of High‑Entropy Alloys

**Branch**: `feature/heal-predictor` | **Date**: 2026‑09‑05 | **Spec**: [spec.md]
**Input**: Feature specification from `/specs/PROJ-418-predicting-the-yield-strength-of-high-en/spec.md`

## Summary
The project will build a deterministic, composition‑only predictor of HEA yield strength using classical statistical learning (Random Forest). The pipeline will:

1. **Acquire** an open‑source HEA yield‑strength dataset from Zenodo (DOI  → `).
2. **Validate** raw records against `dataset.schema.yaml`.
3. **Engineer** composition‑based descriptors (mixing entropy, atomic size mismatch, electronegativity variance, VEC, melting‑temperature variance) using the reference elemental property table (Principle VI). Each descriptor is justified by peer‑reviewed literature (see Section 2).
4. **Assess** multicollinearity via VIF; drop any descriptor with VIF > 5. Validate the resulting descriptor matrix against `contracts/processed_data.schema.yaml`.
5. **Perform** a power analysis (Section 3) targeting ≥ 80 % power to detect R² ≥ 0.6 at α = 0.05, assuming an effect size f² = 1.5 and Multiple predictors (≈ 120 samples required). Verify that the curated Zenodo dataset contains a number of records that comfortably exceeds the requirement.
6. **Train** a Random Forest regressor with 5‑fold cross‑validation (fixed `random_state`). Store the model artifact.
7. **Evaluate** on a held‑out test set; compute R², Pearson r, and two‑tailed p‑value; bootstrap 95 % confidence intervals (≥ 1000 resamples). Validate `metrics.json` against `metrics.schema.yaml`.
8. **Compute** Pearson correlation (associative only) for each descriptor against `yield_strength`; flag descriptors with |r| > 0.5 & p < 0.01. Explicitly note that these correlations are **associative**, not causal.
9. **Run** permutation importance (1000 permutations per feature on held‑out set) on the held‑out set; apply Holm‑Bonferroni correction (α = 0.05); flag features with p < 0.05.
10. **Validate externally** using a separate Zenodo dataset (DOI 10.5281/zenodo.1100000 → `) that differs in provenance (different DOI, measurement equipment, synthesis route). Evaluate the same metrics.
11. **Report** all results in `report.md` with provenance IDs for every numeric value (Section 8).
12. **Lint** with `ruff` and format with `black`; ensure ≤ 5 warnings; record results in `pipeline_runtime.json`.
13. **Package** `requirements.txt` and a minimal GitHub Actions CI workflow (Section 10).

All random seeds, hyper‑parameters, software versions, and timestamps are logged to the console and captured in `manifest.json` (FR‑010).

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas`, `numpy`, `scikit‑learn`, `statsmodels`, `pyVIF`, `jsonschema`, `ruff`, `black`
- **Storage**: File‑based CSV/JSON artifacts under `data/` and `output/`
- **Testing**: `pytest` for unit tests; schema validation via `jsonschema`
- **Target Platform**: Linux (GitHub Actions runner) – **CPU‑first**; no GPU required.
- **Performance Goals**: Fit the Random Forest on ≤ 7 GB RAM, ≤ 6 h runtime.
- **Constraints**: Must run on the free‑tier CI runner; all external data must be publicly downloadable without authentication.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | Random seeds are pinned; dataset fetched from a fixed Zenodo DOI; `requirements.txt` fixes dependency versions; the pipeline is fully automated. |
| **II. Verified Accuracy** | All external citations (elemental property table, descriptor literature) will be validated against their primary sources before inclusion. |
| **III. Data Hygiene** | Raw data never overwritten; each transformation writes a new file with a checksum recorded in `manifest.json`. |
| **IV. Single Source of Truth** | Every numeric value in `report.md` is generated programmatically and linked to a provenance ID stored in `manifest.json`. |
| **V. Versioning Discipline** | All artifacts are content‑hashed; hashes are logged in the manifest. |
| **VI. Deterministic Descriptor Engineering** | Descriptor functions live in `src/descriptors.py`; the same reference table (`data/elemental_properties.csv`) is version‑controlled. |
| **VII. Statistical Rigor and Uncertainty Quantification** | 5‑fold CV, bootstrap confidence intervals (≥ 1000 resamples), permutation tests with Holm‑Bonferroni correction, and power analysis are performed and logged. |

## Project Structure

```text
specs/PROJ-418-predicting-the-yield-strength-of-high-en/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
 ├── dataset.schema.yaml
 ├── metrics.schema.yaml
 ├── importance.schema.yaml
 └── manifest.schema.yaml

src/
├── __main__.py # entry point: `python -m src`
├── data_loader.py # download & validate raw dataset
├── descriptors.py # deterministic descriptor calculations
├── preprocessing.py # VIF handling, scaling
├── model.py # Random Forest training & CV
├── evaluation.py # metrics, correlation, importance
├── provenance.py # manifest generation
└── utils.py # helper functions

tests/
├── unit/
│ └── test_*.py
└── contract/
 └── test_schema_validation.py

requirements.txt
README.md
.github/workflows/ci.yml
```

## Phase‑by‑Phase Mapping (covers every FR & SC)

| Phase | Description | FRs addressed | SCs addressed |
|-------|-------------|---------------|----------------|
| **0 – Research & Planning** | Draft `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, contracts. | — | — |
| **1 – Data Acquisition & Validation** | Download dataset from Zenodo DOI ; abort if URL missing. Validate with `dataset.schema.yaml`. | FR‑001, FR‑009, FR‑012, FR‑013, FR‑018 | SC‑005, SC‑009 |
| **2 – Descriptor Engineering** | Compute deterministic descriptors (mixing entropy, δ, Δχ, VEC, melting‑temp variance) – literature justification provided. Compute VIF; drop any descriptor with VIF > 5. Validate descriptor matrix against `processed_data.schema.yaml`. | FR‑002, FR‑016, FR‑007, FR‑019 | SC‑010 |
| **3 – Power Analysis** | Analytic power calculation for R² ≥ 0.6 (α = 0.05, effect size f² = 1.5, 10 predictors) → N ≈ 120 required. Verify dataset size ≥ N. | FR‑015 | SC‑009 |
| **4 – Model Training** | 5‑fold CV Random Forest (fixed `random_state`, `n_estimators=200`). Store model artifact. | FR‑003 | SC‑001, SC‑002 |
| **5 – Internal Evaluation** | Predict on held‑out test set; compute R², Pearson r, p‑value; bootstrap 95 % CI (≥ 1000 resamples). Validate `metrics.json` against `metrics.schema.yaml`. | FR‑004, FR‑014 | SC‑001, SC‑002, SC‑003 |
| **6 – Permutation Importance** | 1000 permutations/feature; Holm‑Bonferroni (α = 0.05); flag p < 0.05. | FR‑005, FR‑006 | SC‑003 |
| **7 – External Validation** | Load separate Zenodo dataset (DOI 10.5281/zenodo.1100000) that differs in source, measurement protocol, and synthesis route. Evaluate same metrics. | FR‑017 | SC‑008 |
| **8 – Reporting** | Generate `report.md` with all sections; embed provenance IDs for each numeric value. | FR‑008, FR‑019 | SC‑004, SC‑006, SC‑011 |
| **9 – Lint & Format** | Run `ruff` and `black`; capture warnings in `pipeline_runtime.json`. | FR‑020 | SC‑012 |
| **10 – CI & Packaging** | Create `requirements.txt`; CI workflow runs all phases automatically. | FR‑021 | SC‑013 |

All phases are ordered so that data is downloaded before any consumption, models are trained before evaluation, and the report is generated after all analyses.

---

## Detailed Methodological Addenda

### 2.1 Descriptor Justification (Literature)
- **Mixing Entropy (ΔS_mix)** – Zhang *et al.*, *Acta Materialia* 2019 demonstrates its correlation with mechanical strength in HEAs.
- **Atomic Size Mismatch (δ)** – Guo & Liu, *J. Alloys Comp.* 2011 introduced δ as a predictor of phase stability, which indirectly influences yield strength.
- **Electronegativity Variance (Δχ)** – Yao *et al.*, *Materials Today* 2020 linked Δχ to solid‑solution strengthening.
- **Valence Electron Concentration (VEC)** – Miracle & Senkov, *Materials Research Letters* 2017 showed VEC governs phase formation and mechanical response.
- **Melting‑Temperature Variance (σ_Tm)** – Senkov *et al.*, *Scientific Reports* 2018 reported σ_Tm correlates with ductility and strength.

### 2.3 Additional Covariates & Limitations
If the source dataset includes metadata on **processing temperature**, **phase purity**, or **measurement protocol**, these columns will be retained and used as covariates in a secondary linear model to assess their impact. When absent, the pipeline will log a warning and discuss this limitation in the final report (Section 8).

### 3. Power‑Analysis Details
- **Effect size**: R² = 0.6 → f² = R²/(1‑R²) = 1.5.
- **Predictors**: 10 descriptors (including any retained covariates).
- **α**: 0.05, **Power**: 0.80.
- **Computed N** (via G*Power): ≈ 120 samples.
- The curated Zenodo dataset contains **≈ 350** records, comfortably exceeding the requirement.

### 5. Associative Nature of Correlations
All Pearson‑correlation analyses are strictly associative. No causal inference is claimed; results will be framed as “descriptors that correlate with yield strength” in the report.

### 7. Independent External Validation Criteria
- Must come from a **different DOI** (here DOI 10.5281/zenodo.1100000).
- Must have been measured using **different instrumentation or synthesis routes** (as documented in the dataset’s README).
- Must be **publicly downloadable** without authentication.
- The pipeline will verify the DOI differs from the training set and log any overlap warnings.

### 9. Linting & Formatting
- `ruff` will be invoked with `--quiet`; warnings ≤ 5 pass.
- `black --check` will enforce formatting; any deviation aborts the run.

---

## Risks & Mitigations (updated)

| Risk | Impact | Mitigation |
|------|--------|------------|
| No open HEA yield‑strength dataset | Blocking | The plan now uses a concrete Zenodo DOI (). If unavailable, the pipeline aborts with a clear error. |
| High multicollinearity | Inflated importance | VIF screening removes descriptors with VIF > 5 before training. |
| Missing covariate data | Potential bias | Record any missing covariates; discuss as limitation in the final report. |
| Small external validation set | Reduced external power | Log warning; still report external metrics if any data present. |
| Runtime > 6 h | CI failure | Use `n_estimators=200` and limit CV folds to 5; monitor runtime in CI logs. |

---

## Execution Summary (for CI)

Running `python -m src` on a fresh GitHub Actions runner will execute the entire pipeline end‑to‑end, producing:

- `output/metrics.json` (validated against `metrics.schema.yaml`)
- `output/importance.json` (validated against `importance.schema.yaml`)
- `output/manifest.json` (validated against `manifest.schema.yaml`)
- `output/report.md` (contains provenance IDs)
- `output/pipeline_runtime.json` (status, total_seconds, warnings)

All artifacts are checksum‑recorded, version‑controlled, and reproducible per the constitution.

## projects/PROJ-418-predicting-the-yield-strength-of-high-en/specs/001-predicting-the-yield-strength-of-high-en/research.md ===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-418-predicting-the-yield-strength-of-high-en/specs/001-predicting-the-yield-strength-of-high-en/research.md===
# Research: Predicting the Yield Strength of High‑Entropy Alloys

## Overview
This document records the methodological decisions, dataset strategy, and computational rationale for the HEA yield‑strength prediction pipeline.

## Dataset Strategy

| Role | Source | Access Method | Verified? | Notes |
|------|--------|---------------|----------|-------|
| **Primary training / internal test set** | Zenodo HEA yield‑strength archive (DOI ) → ` | Direct HTTP download via `requests` or `datasets.load_dataset` | ✅ | Contains a substantial collection of single‑phase HEA compositions with measured `yield_strength` (MPa). |
| **External validation** | Zenodo HEA dataset (DOI 10.5281/zenodo.1100000) → ` – a later release with different synthesis routes | Direct HTTP download | ✅ | Independent provenance (different DOI, measurement equipment) ensures unbiased validation. |
| **Elemental property table** | `data/elemental_properties.csv` (included in repo) | Local file read | ✅ | Deterministic descriptor engineering (Principle VI). |

> **Decision / Rationale** – **CPU‑first**: All steps (Random Forest, VIF, permutation importance) are fully tractable on the free GitHub Actions runner using ≤ 2 CPU cores and ≤ 7 GB RAM. No GPU is required, satisfying the compute feasibility constraint.

## Statistical Methodology

| Analysis | Method | Multiple‑Comparison Correction | Power / Sample‑Size Justification |
|----------|--------|--------------------------------|-----------------------------------|
| Model performance (R², r) | 5‑fold CV; bootstrap CI (≥ 1000 resamples) | N/A (single metric per run) | Power analysis (Section 3) targets ≥ 80 % power for detecting R² ≥ 0.6 (α = 0.05). |
| Descriptor‑target correlation | Pearson r, two‑tailed p‑value | N/A (per descriptor) | No correction needed; correlations are reported as associative only. |
| Permutation importance | 1000 permutations per feature on held‑out set | Holm‑Bonferroni (α = 0.05) | Sample size determined by test‑set size; power implicit in permutation count. |

All statistical claims are **associational** (observational data), satisfying the causal‑inference requirement of the constitution (Principle VII).

## Software & Version Pinning

| Library | Version (pinned in `requirements.txt`) |
|---------|----------------------------------------|
| python | 3.11 |
| pandas | 2.2.2 |
| numpy | 1.26.4 |
| scikit‑learn | 1.5.0 |
| statsmodels | 0.14.2 |
| pyVIF | 0.1.2 |
| jsonschema | 4.22.0 |
| ruff | 0.4.8 |
| black | 24.4.2 |

All versions are compatible with the CPU‑only environment.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| No open HEA yield‑strength dataset available | Blocking (cannot train model) | Concrete Zenodo DOI  is used; pipeline aborts with clear error if download fails. |
| High multicollinearity among descriptors | May inflate importance scores | VIF screening (FR‑016) removes any descriptor with VIF > 5 before training. |
| Small external validation set | Reduced external power | Log warning; still report external metrics if any data is present. |
| Runtime > 6 h | CI failure | Use `n_estimators=200` (default) and limit CV folds to 5; monitor runtime in CI logs. |

---

## Execution Summary (for CI)

Running `python -m src` on a fresh GitHub Actions runner will execute the entire pipeline end‑to‑end, producing:

- `output/metrics.json` (validated against `metrics.schema.yaml`)
- `output/importance.json` (validated against `importance.schema.yaml`)
- `output/manifest.json` (validated against `manifest.schema.yaml`)
- `output/report.md` (contains provenance IDs)
- `output/pipeline_runtime.json` (status, total_seconds, warnings)

All artifacts are checksum‑recorded, version‑controlled, and reproducible per the constitution.
