# Implementation Plan: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

**Branch**: `001-statistical-analysis-covid-vaers` | **Date**: 2026-10-18 | **Spec**: `specs/001-statistical-analysis-of-publicly-availab/spec.md`  
**Input**: Feature specification from `specs/001-statistical-analysis-of-publicly-availab/spec.md`

## Summary
The project will deliver a reproducible, CPU‑only pipeline that (1) programmatically downloads a verified VAERS 2020‑2023 parquet dataset from Hugging Face, (2) validates the raw schema, (3) cleans and groups records into **COVID‑19**, **Non‑COVID‑Non‑Flu**, and **Flu‑only** vaccine groups, (4) computes disproportionality metrics (ROR, PRR, IC) with 95 % Wald confidence intervals, applies Benjamini‑Hochberg FDR correction, and **performs stratified primary analyses by age × sex with Mantel‑Haenszel pooling** (addressing confounding), (5) flags safety signals that satisfy the 2‑out‑of‑3 rule **and passes a bootstrap‑estimated empirical FDR check (≤ 0.05)**, (6) generates weekly reporting‑time profiles (CSV files `output/temporal_profiles/<SOC>.csv`; optional PNG visualisations) for the top‑few signals, performs a **temporal‑bias robustness check** by re‑computing metrics after removing weeks with extreme spikes, (7) performs a Flu‑only sensitivity analysis, and (8) records memory usage. All artifacts are verified against JSON‑Schema contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.2`, `numpy==1.26.4`, `scipy==1.13.0`, `matplotlib==3.8.4`, `datasets==2.18.0`, `pyarrow==15.0.0`, `memory_profiler==0.61.0`  
- **Storage**: Local CSV/Parquet files under `data/` and `output/`  
- **Testing**: `pytest==8.2.2` with contract tests; linting via `ruff`  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU cores, ≤7 GB RAM, ≤14 GB disk)  
- **Constraints**: CPU‑only; peak RAM ≤ 7 GB; all random seeds pinned.  

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Fixed seeds, deterministic downloads, checksums recorded. |
| II. Verified Accuracy | PASS | Only URLs from the “Verified datasets” block are used. |
| III. Data Hygiene | PASS | Raw files immutable; each transformation writes a new file with documented derivation. |
| IV. Single Source of Truth | PASS | Every figure/table traces back to a single row in `data/processed/cleaned.parquet` and a single function in `src/`. |
| V. Versioning Discipline | PASS | Content hashes will be recorded by the Advancement‑Evaluator. |
| VI. Epidemiological Signal Disproportionality | PASS | ROR/PRR/IC computed on defined vaccine vs. baseline groups; baseline is **Non‑COVID‑Non‑Flu** (primary) and **Flu‑only** (sensitivity). |
| VII. Null‑Hypothesis Equivalence | PASS | Null results are reported as valid findings. |
| FR‑006 (CPU‑only) | PASS | No GPU‑only libraries are referenced; all steps run on CPU. |

## Project Structure
```text
specs/001-statistical-analysis-covid-vaers/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    └── signal.schema.yaml

src/
├── data/
│   ├── download.py          # uses huggingface_hub to fetch verified parquet
│   ├── validate.py          # schema validation against contracts/dataset.schema.yaml
│   └── clean.py             # filtering, MedDRA→SOC mapping, group assignment
├── analysis/
│   ├── disproportionality.py # contingency tables, ROR/PRR/IC, CI, continuity correction, **stratified tables**, Mantel‑Haenszel pooling, bootstrap validation
│   ├── temporal.py           # weekly aggregation, CSV generation, temporal‑bias robustness check
│   └── sensitivity.py        # Flu‑only baseline recomputation
├── utils/
│   ├── config.py            # paths, seeds, thresholds, MAX_MEMORY_GB=7
│   └── plots.py             # plot_weekly_counts (optional PNG)
├── main.py                  # orchestrates all phases
└── requirements.txt

tests/
├── contract/
│   ├── test_dataset_schema.py
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

output/
├── signals.csv
├── temporal_profiles/
│   ├── <SOC>.csv            # weekly counts (canonical)
│   └── <SOC>.png            # optional visualisation (auxiliary)
├── sensitivity_analysis.csv
└── report.md
```

## Implementation Phases & FR/SC Mapping
| Phase | Core Tasks | FR / SC addressed |
|-------|------------|--------------------|
| **Phase 0 – Environment & Directory Setup** | 1. Create `data/`, `output/`, `logs/`.<br>2. Generate `logs/structure.txt` via `tree -a -L 3` (T001).<br>3. Install dependencies from `requirements.txt`.<br>4. Verify CPU‑only mode (FR‑006). | – |
| **Phase 1 – Data Acquisition & Validation** | 1. `src/data/download.py` uses `datasets.load_dataset("chrisvoncsefalvay/vaers-outcomes", data_dir="data", split="train")` to fetch the parquet from the verified URL `.<br>2. Compute SHA‑256 checksum, store in `data/checksums.txt`.<br>3. `src/data/validate.py` validates against `contracts/dataset.schema.yaml`; aborts with `E_SCHEMA_MISSING` if required columns (`VAX_TYPE`, `SOC_CODE`, `REPT_DATE`) are absent. | FR‑001, SC‑004 |
| **Phase 2 – Cleaning & Group Construction** | 1. `src/data/clean.py` drops rows with missing `SOC_CODE` or `REPT_DATE`.<br>2. Loads `data/meddra_to_soc.csv` (bundled mapping) to translate MedDRA codes to SOC names.<br>3. Creates `VAX_GROUP` column: `"COVID-19"` if `VAX_TYPE` contains “COVID”, `"Flu-only"` if `VAX_TYPE` contains “Influenza”, else `"Non-COVID-Non-Flu"`.<br>4. Writes `data/processed/cleaned.parquet`. | FR‑001 |
| **Phase 3 – Disproportionality Computation** | 1. Build 2×2 tables for each SOC (COVID vs. Non‑COVID‑Non‑Flu).<br>2. Apply continuity correction + 0.5 to any zero cell (Edge‑Case).<br>3. Compute ROR, PRR, IC with Wald 95 % CIs (using `scipy.stats`).<br>4. **Stratified analysis (primary)**: repeat steps 1‑3 within each age‑group (`<18`, `18‑64`, `≥65`) × sex (`M`, `F`, `U`).<br>5. Combine stratified estimates via **Mantel‑Haenszel pooling** to obtain pooled ROR/PRR/IC – this pooled result is the primary signal‑detection statistic, directly addressing confounding by age and sex.<br>6. Perform Fisher exact test → raw p‑value.<br>7. Apply Benjamini‑Hochberg FDR correction (FR‑003).<br>8. Verify monotonicity of adjusted p‑values (SC‑002).<br>9. **Threshold Justification**: thresholds are drawn from established pharmacovigilance literature (van Puijenbroek et al., *Drug Saf* 2002 for ROR > 2.0; Evans et al., *Pharmacoepidemiol Drug Saf* 2001 for PRR > 1.5; WHO‑UMC Bayesian CP‑NN for IC > 0).<br>10. **Power and Sample‑Size Discussion**: the ≥5‑report filter is a stability rule; with ≥5 reports Wald CIs are reasonably bounded, providing detectable effect sizes typical for spontaneous reporting systems. Formal power calculations are infeasible, and the limitation is reported (SC‑005).<br>11. **Bootstrap validation**: 1 000 bootstrap resamples of the cleaned dataset estimate the empirical false‑discovery rate of the 2‑out‑of‑3 rule; the median empirical FDR is recorded in `output/report.md` and must be ≤ 0.05 for a signal to be accepted (independent validation, addressing circularity).<br>12. Flag a signal if **≥ 2** of the three metrics meet thresholds **and** the bootstrap‑estimated empirical FDR ≤ 0.05 (FR‑005, scientific‑soundness).<br>13. Export `output/signals.csv`. | FR‑002, FR‑003, FR‑005, SC‑001, SC‑002, scientific‑soundness, methodology‑df5ae842, methodology‑6256a970, methodology‑28a8b7c5 |
| **Phase 4 – Temporal Profiling & Bias Check** | 1. Select the top signals by smallest BH‑adjusted p‑value.<br>2. Compute weekly counts relative to median `REPT_DATE` of the COVID‑19 cohort.<br>3. Write canonical CSV files `output/temporal_profiles/<SOC>.csv`. Optional PNG visualisations may be generated via `src/utils/plots.py` (auxiliary).<br>4. **Temporal‑bias robustness**: identify weeks where COVID count exceeds 3 × median weekly count; temporarily drop those weeks and re‑run Phase 3 metrics for the top‑5 SOCs.<br>5. **Signal stability requirement**: a candidate signal is retained in the final report only if it remains significant (passes the 2‑out‑of‑3 rule and bootstrap‑FDR ≤ 0.05) both in the full analysis and after spike‑week removal.<br>6. Log imported modules to `logs/config_import.txt`. | FR‑004, SC‑003, methodology‑60b09b65 |
| **Phase 5 – Sensitivity Analysis** | 1. Re‑compute metrics using the **Flu‑only** baseline.<br>2. Calculate ΔROR, ΔPRR, ΔIC for the top‑5 signals.<br>3. Export `output/sensitivity_analysis.csv`. | FR‑007 |
| **Phase 6 – Memory Profiling & Constraint Enforcement** | 1. Use `memory_profiler` to record peak RAM during Phases 3‑5.<br>2. Assert peak ≤ 7 GB; abort with clear error if exceeded (SC‑004).<br>3. Append memory summary to `output/report.md`. | SC‑004 |
| **Phase 7 – Final Reporting** | 1. Compile `output/report.md` containing:<br> • Signal table with adjusted p‑values, bootstrap‑FDR, and stability flag.<br> • Confirmation of monotonicity (SC‑002).<br> • Temporal CSVs (and optional PNGs).<br> • Sensitivity Δ‑table.<br> • Memory usage.<br>2. Ensure every statistic traces back to a single row in `data/processed/cleaned.parquet` (Principle IV). | SC‑001, SC‑002, SC‑005 |

## Edge‑Case Handling
- **Zero‑Count Cells** → add 0.5 to all cells before metric calculation.  
- **Sparse SOCs (< 5 reports)** → excluded from analysis (FR‑002, FR‑006).  
- **Missing Background Rates** → flagged in `output/report.md` as “Background Rate Unknown”.  

## Compute Feasibility
- **Environment**: GitHub Actions free tier (2 CPU cores, ≤ 7 GB RAM, ≤ 14 GB disk).  
- **Data size**: The selected parquet is ≈ 1.8 GB on disk and < 5 GB in memory after type optimization.  
- **Runtime estimate**:  
  - Download & checksum: < 2 min  
  - Cleaning & grouping: < 5 min  
  - Disproportionality (including stratified & bootstrap): < 45 min  
  - Temporal & sensitivity analyses: < 20 min  
  - Memory profiling & report generation: < 10 min  
  - **Total** < 2 h, well within the 6‑hour CI limit.  

All libraries are pure‑CPU; no GPU‑only packages are used.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Required columns missing in the parquet | Fatal (cannot compute) | Phase 1 schema validation gate aborts with clear error. |
| Peak RAM > 7 GB | Job termination | Phase 6 memory guard; optional chunked processing fallback (`USE_CHUNKED=True`). |
| BH‑adjusted p‑values not monotonic | SC‑002 failure | Unit test `tests/unit/test_bh_monotonic.py` asserts monotonicity. |
| Incomplete MedDRA→SOC mapping | Incomplete SOC aggregation | Mapping file `data/meddra_to_soc.csv` must cover ≥ 95 % of observed codes; validation logs uncovered codes. |
| Mislabelled temporal axis | Violation of Principle VII | Plots explicitly label “Reporting Time”; documentation repeats disclaimer. |
| Thresholds appear arbitrary | Methodological criticism | Added literature‑based justification (see research.md). |
| Confounding by age/sex in baseline | Biased signals | Primary analysis now stratified and pooled (Mantel‑Haenszel). |
| Temporal spikes bias metrics | Spurious signals | Temporal‑bias robustness check evaluates robustness; signals must survive both analyses. |
| Circular signal definition | Scientific soundness | Bootstrap‑estimated empirical FDR added as independent validation. |

---


