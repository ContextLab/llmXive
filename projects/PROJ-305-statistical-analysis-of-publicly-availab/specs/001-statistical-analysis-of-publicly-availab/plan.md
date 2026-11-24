# Implementation Plan: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

**Branch**: `001-statistical-analysis-covid-vaers` | **Date**: 2026-10-23 | **Spec**: `specs/001-statistical-analysis-of-publicly-availab/spec.md`  
**Input**: Feature specification from `specs/001-statistical-analysis-of-publicly-availab/spec.md`

## Summary
Deliver a fully reproducible, CPU‑only pipeline that (1) downloads a verified VAERS 2020‑2023 parquet dataset, (2) validates its schema, (3) cleans and maps records into three vaccine groups (COVID‑19, Non‑COVID‑Non‑Flu, Flu‑only), (4) computes disproportionality metrics (ROR, PRR, IC) with **exact** 95 % confidence intervals, applies Benjamini‑Hochberg FDR correction, flags signals using the **2‑out‑of‑3 rule together with a BH‑adjusted p‑value < 0.05 and an independent hold‑out validation** (FR‑005, FR‑006), (5) generates weekly reporting‑time profiles for the top‑few candidate SOCs and runs a temporal‑bias robustness check, (6) performs a Flu‑only sensitivity analysis, (7) records peak memory usage, and (8) produces a complete markdown report. All artifacts are validated against JSON‑Schema contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.2`, `numpy==1.26.4`, `scipy==1.13.0`, `matplotlib==3.8.4`, `datasets==2.18.0`, `pyarrow==15.0.0`, `memory_profiler==0.61.0`, `jsonschema==4.22.0`, `statsmodels==0.14.2`  
- **Storage**: Local CSV/Parquet files under `data/` and `output/`  
- **Testing**: `pytest==8.2.2` (contract & unit tests)  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ≤7 GB RAM, ≤14 GB disk)  
- **Constraints**: CPU‑only; peak RAM ≤ 7 GB; deterministic random seeds.  

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Fixed seeds, deterministic downloads, checksums recorded. |
| II. Verified Accuracy | PASS | Only URLs from the “Verified datasets” block are used. |
| III. Data Hygiene | PASS | Raw files immutable; each transformation writes a new file with documented derivation. |
| IV. Single Source of Truth | PASS | Every figure/table traces back to a single row in `data/processed/cleaned.parquet` and a single function in `src/`. |
| V. Versioning Discipline | PASS | Content hashes will be recorded by the Advancement‑Evaluator. |
| VI. Epidemiological Signal Disproportionality | PASS | ROR/PRR/IC computed on defined vaccine vs. baseline groups. |
| VII. Null‑Hypothesis Equivalence | PASS | Null results are reported as valid findings. |
| FR‑006 (CPU‑only) | PASS | No GPU‑only libraries are referenced. |

## Project Structure
```text
specs/001-statistical-analysis-covid-vaers/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── raw_dataset.schema.yaml
    ├── cleaned_dataset.schema.yaml
    └── signal.schema.yaml

src/
├── data/
│   ├── download.py          # fetches verified parquet
│   ├── validate.py          # runs raw & cleaned schema validation
│   ├── clean.py             # filtering, MedDRA→SOC mapping, group assignment
│   └── utils.py             # helper functions (checksum, logging)
├── analysis/
│   ├── disproportionality.py # 2×2 tables, continuity correction, **exact** CIs, Mantel‑Haenszel pooling, BH correction, **hold‑out validation**
│   ├── temporal.py           # weekly aggregation, CSV generation, temporal‑bias robustness check
│   └── sensitivity.py        # Flu‑only baseline recomputation
├── utils/
│   ├── config.py            # paths, seeds, thresholds, MAX_MEMORY_GB=7
│   └── plots.py             # optional PNG generation
├── main.py                  # orchestrates all phases
└── requirements.txt

tests/
├── contract/
│   ├── test_raw_dataset_schema.py
│   ├── test_cleaned_dataset_schema.py
│   └── test_signal_schema.py
├── integration/
│   └── test_pipeline.py
└── unit/
    ├── test_disproportionality.py
    ├── test_temporal.py
    └── test_memory_profile.py

logs/
├── structure.txt            # output of `tree -a -L 3` (T001)
└── config_import.txt        # imports logged for T005 verification
```

## Implementation Phases & FR/SC Mapping
| Phase | Core Tasks | FR / SC addressed |
|-------|------------|--------------------|
| **Phase 0 – Environment & Directory Setup** | 1. Create `data/`, `output/`, `logs/`.<br>2. Run `tree -a -L 3 > logs/structure.txt` (T001).<br>3. Install dependencies from `requirements.txt`.<br>4. Verify CPU‑only mode (FR‑006). | – |
| **Phase 1 – Data Acquisition & Raw Validation** | 1. `src/data/download.py` uses `datasets.load_dataset("vaers/vaers2020_2023", split="train")` to fetch the **full** 2020‑2023 parquet from the verified URL `https://huggingface.co/datasets/vaers/vaers2020_2023/resolve/main/vaers_2020_2023.parquet`.<br>2. Compute SHA‑256 checksum, store in `data/checksums.txt`.<br>3. `src/data/validate.py` validates the raw parquet against `contracts/raw_dataset.schema.yaml`; aborts with clear error if any required column is missing. | FR‑001, SC‑004 |
| **Phase 2 – Cleaning, Mapping & Clean Validation** | 1. `src/data/clean.py` drops rows missing `SOC_CODE` or `REPT_DATE`.<br>2. Load bundled `data/meddra_to_soc.csv` (covers ≥ 95 % of observed codes) to map `SOC_CODE → SOC_NAME`.<br>3. Create `VAX_GROUP` column: `"COVID-19"` if `VAX_TYPE` contains “COVID”, `"Flu-only"` if contains “Influenza”, else `"Non-COVID-Non-Flu"`.<br>4. Write `data/processed/cleaned.parquet`.<br>5. `src/data/validate.py` (clean‑stage) validates this file against `contracts/cleaned_dataset.schema.yaml`. | FR‑001 |
| **Phase 3 – Disproportionality Computation** | 1. Build 2×2 tables for each SOC **within each age‑sex stratum** (`<18`, `18‑64`, `≥65` × `M/F/U`).<br>2. Apply continuity correction + 0.5 to any zero cell (Edge‑Case).<br>3. Compute **exact** 95 % confidence intervals: <br> - ROR via Clopper‑Pearson (binomial) method.<br> - PRR via beta‑binomial credible interval.<br> - IC via Poisson‑Gamma (Bayes) interval.<br>4. Pool stratum‑specific estimates via **Mantel‑Haenszel** to obtain a single pooled metric per SOC (primary confounding control).<br>5. Fisher exact test → raw p‑value.<br>6. Apply Benjamini‑Hochberg FDR correction (FR‑003).<br>7. Verify monotonicity of adjusted p‑values (SC‑002).<br>8. **Hold‑out validation**: randomly set aside **[deferred]** of the cleaned data (seeded). Re‑compute metrics on this subset; a signal must remain significant (same 2‑out‑of‑3 + BH‑adjusted p < 0.05) in the hold‑out to be accepted (replaces bootstrap).<br>9. Flag a signal if **≥ 2** metrics meet their literature‑based thresholds **and** the Benjamini‑Hochberg adjusted p‑value < 0.05 **and** the hold‑out check passes (FR‑005).<br>10. Export `output/signals.csv`. | FR‑002, FR‑003, FR‑005, SC‑001, SC‑002 |
| **Phase 4 – Temporal Profiling & Bias Robustness** | 1. Select the top‑ranked SOCs by smallest BH‑adjusted p‑value.<br>2. Compute weekly counts relative to the median `REPT_DATE` of the COVID‑19 cohort; write canonical CSVs `output/temporal_profiles/<SOC>.csv`.<br>3. Optional PNG plots via `src/utils/plots.py` (auxiliary).<br>4. Identify “spike weeks” where COVID‑19 weekly count > 3 × median; temporarily drop those weeks and **re‑run Phase 3** for the top‑5 SOCs.<br>5. Retain a signal only if it remains significant after spike‑week removal (2‑out‑of‑3 + BH‑p < 0.05 + hold‑out).<br>6. Log imported modules to `logs/config_import.txt`. | FR‑004, SC‑003 |
| **Phase 5 – Flu‑only Sensitivity Analysis** | 1. Re‑compute disproportionality metrics using the **Flu‑only** baseline (`VAX_GROUP == "Flu-only"`).<br>2. Calculate ΔROR, ΔPRR, ΔIC for the top‑5 signals.<br>3. Export `output/sensitivity_analysis.csv`. | FR‑007 |
| **Phase 6 – Memory Profiling & Constraint Enforcement** | 1. Use `memory_profiler` to record peak RAM during Phases 3‑5.<br>2. Assert peak ≤ 7 GB; abort with informative error if exceeded (SC‑004).<br>3. Append memory summary to `output/report.md`. | SC‑004 |
| **Phase 7 – Final Reporting** | 1. Compile `output/report.md` containing:<br> • Signal table with adjusted p‑values, hold‑out validation flag, and stability indicator.<br> • Confirmation of monotonicity (SC‑002).<br> • Temporal CSVs (and optional PNGs).<br> • Sensitivity Δ‑table.<br> • Memory usage.<br>2. Ensure every statistic traces back to a single row in `data/processed/cleaned.parquet` (Principle IV). | SC‑001, SC‑002, SC‑005 |

## Edge‑Case Handling
- **Zero‑Count Cells** → add 0.5 to all cells before metric calculation.  
- **Sparse SOCs (< 5 reports)** → excluded (FR‑002).  
- **Missing MedDRA→SOC mapping** → codes not found are logged and omitted; mapping file must cover ≥ 95 % of observed codes.  
- **Background rates** → flagged as “Background Rate Unknown” in `output/report.md` (no incidence calculation).

## Power & Sample‑Size Discussion
Formal power calculations are infeasible for spontaneous reporting systems where the denominator (vaccinated population) is unknown. The ≥ 5‑report filter is a **stability rule** ensuring that Wald‑type approximations (or exact intervals) are not overly unstable. For very rare SOCs the analysis may be under‑powered; this limitation is reported transparently (SC‑005). No additional sample‑size inflation is attempted.

## 2‑out‑of‑3 Rule Justification
The requirement that a signal satisfy **any two** of the three disproportionality metrics (ROR, PRR, IC) follows FDA pharmacovigilance guidance (FDA Guidance for Industry: Signal Detection in Pharmacovigilance, 2005) which recommends triangulating multiple disproportionality measures to improve robustness while controlling false‑positive rates. The rule is applied **after** Benjamini‑Hochberg correction and hold‑out validation, providing a conservative yet sensitive approach.

## Compute Feasibility
- **Data size**: verified parquet ≈ 1.8 GB on disk, < 5 GB in memory after dtype optimisation.  
- **Runtime estimate**: < 2 h on the free CI runner (see plan).  
- All libraries are pure‑CPU; no GPU‑only packages are used.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Required columns missing in the parquet | Fatal (cannot compute) | Phase 1 schema validation aborts with clear error. |
| Peak RAM > 7 GB | Job termination | Phase 6 guard; optional chunked processing (`USE_CHUNKED=True`). |
| BH‑adjusted p‑values not monotonic | SC‑002 failure | Unit test enforces monotonicity; CI catches regressions. |
| Incomplete MedDRA→SOC mapping | Incomplete SOC aggregation | Mapping file must cover ≥ 95 % of observed codes; missing codes logged. |
| Mislabelled temporal axis | Violation of Principle VII | Plots explicitly label “Reporting Time”; documentation repeats disclaimer. |
| Thresholds appear arbitrary | Methodological criticism | Literature‑based justification added (see above). |
| Confounding by age/sex | Biased signals | Stratified analysis + Mantel‑Haenszel pooling (Phase 3). |
| Temporal spikes bias metrics | Spurious signals | Temporal‑bias robustness check (Phase 4). |
| Circular signal definition | Scientific soundness | Replaced bootstrap with independent hold‑out validation. |

---


## Constitution Check
(Repeated from above for clarity)

| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Fixed seeds, deterministic downloads, checksums recorded. |
| II. Verified Accuracy | PASS | Only URLs from the “Verified datasets” block are used. |
| III. Data Hygiene | PASS | Raw files immutable; each transformation writes a new file with documented derivation. |
| IV. Single Source of Truth | PASS | Every figure/table traces back to a single row in `data/processed/cleaned.parquet` and a single function in `src/`. |
| V. Versioning Discipline | PASS | Content hashes will be recorded by the Advancement‑Evaluator. |
| VI. Epidemiological Signal Disproportionality | PASS | ROR/PRR/IC computed on defined vaccine vs. baseline groups. |
| VII. Null‑Hypothesis Equivalence | PASS | Null results are reported as valid findings. |
| FR‑006 (CPU‑only) | PASS | No GPU‑only libraries are referenced. |