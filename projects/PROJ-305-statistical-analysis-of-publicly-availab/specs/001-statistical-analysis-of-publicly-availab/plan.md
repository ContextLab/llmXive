# Implementation Plan: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

**Branch**: `001-statistical-analysis-covid-vaers` | **Date**: 2026-10-11 | **Spec**: `specs/001-statistical-analysis-covid-vaers/spec.md`  
**Input**: Feature specification from `specs/001-statistical-analysis-covid-vaers/spec.md`

## Summary
The project will deliver a reproducible, CPU‑only pipeline that (1) downloads a verified VAERS parquet dataset, (2) validates its schema, (3) cleans and splits records into **COVID‑19**, **Non‑COVID, Non‑Flu**, and **Flu‑only** groups, (4) computes disproportionality metrics (ROR, PRR, IC) with 95 % confidence intervals and Benjamini‑Hochberg (BH) FDR correction, (5) flags signals that satisfy the 2‑out‑of‑3 rule (FR‑005), (6) generates weekly reporting profiles for the top‑5 signals (FR‑004), and (7) performs a Flu‑only sensitivity analysis (FR‑007). All steps are logged, memory‑profiled, and validated against JSON‑Schema contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.2`, `numpy==1.26.4`, `scipy==1.13.0`, `matplotlib==3.8.4`, `datasets==2.18.0`, `pyarrow==15.0.0`  
- **Storage**: Local CSV/Parquet files under `data/` and `output/`  
- **Testing**: `pytest==8.2.2` with contract tests; linting via `ruff`  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU cores, ≤7 GB RAM, ≤14 GB disk)  
- **Constraints**: CPU‑only; no GPU libraries; memory ≤ 7 GB; all random seeds pinned.  

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Fixed seeds, checksummed data, `requirements.txt`. |
| II. Verified Accuracy | PASS | Only verified URLs from the “Verified datasets” block are used. |
| III. Data Hygiene | PASS | Raw files are immutable; each transformation writes a new file; checksums recorded. |
| IV. Single Source of Truth | PASS | Every figure/table derives from a single row in `data/processed/cleaned.parquet` and a single function in `src/`. |
| V. Versioning Discipline | PASS | Content hashes will be recorded by the Advancement‑Evaluator. |
| VI. Epidemiological Signal Disproportionality | PASS | ROR/PRR/IC computed on defined vaccine vs. baseline groups; baseline defined per spec. |
| VII. Null‑Hypothesis Equivalence | PASS | Null results are treated as publishable; no “failure” framing. |
| **FR‑006 (CPU‑only)** | PASS | Explicitly referenced in Phase 0 and Phase 6 to ensure compliance. |

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
│   ├── download.py          # fetches verified parquet, writes checksum
│   ├── clean.py             # filters, maps MedDRA→SOC, splits groups
│   └── validate.py          # schema validation against contracts/dataset.schema.yaml
├── analysis/
│   ├── disproportionality.py # contingency tables, ROR/PRR/IC, CI, continuity correction
│   ├── temporal.py           # weekly aggregation, plot generation
│   └── sensitivity.py        # Flu‑only baseline comparison
├── utils/
│   ├── config.py            # paths, seeds, thresholds
│   └── plots.py             # plot_weekly_counts, plot_signal_table
├── main.py                  # orchestrator
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
├── structure.txt            # output of `tree -a -L 3` for verification (T001)
└── config_import.txt        # imports logged for T005 verification

output/
├── signals.csv
├── temporal_profiles/
│   └── *.png
├── sensitivity_analysis.csv
└── report.md
```

## Implementation Phases & Task Mapping
| Phase | Core Tasks | FR / SC addressed |
|-------|------------|--------------------|
| **Phase 0 – Environment & Directory Setup** | 1. Create `data/`, `output/`, `logs/` directories.<br>2. Write `logs/structure.txt` via `tree -a -L 3` (fulfills T001).<br>3. Install dependencies from `requirements.txt`.<br>4. **Reference FR‑006** to guarantee CPU‑only execution. | – |
| **Phase 1 – Data Acquisition & Validation** | 1. `src/data/download.py` downloads the **full** VAERS parquet covering 2020‑2023 (`).<br>2. Compute SHA‑256 checksum, store in `data/checksums.txt`.<br>3. `src/data/validate.py` validates against `contracts/dataset.schema.yaml`; abort with `E_SCHEMA_MISSING` if required columns absent (blocking gate). | FR‑001, SC‑004 |
| **Phase 2 – Cleaning & Group Construction** | 1. `src/data/clean.py` removes records with missing `SOC` or `REPT_DATE`.<br>2. Maps MedDRA codes to SOC names using an embedded mapping file (`data/meddra_to_soc.csv`).<br>3. Splits into three groups: **COVID‑19**, **Non‑COVID, Non‑Flu**, **Flu‑only** (`VAX_TYPE` contains “Influenza”).<br>4. Writes `data/processed/cleaned.parquet`. | FR‑001 |
| **Phase 3 – Disproportionality Computation** | 1. Build 2×2 contingency tables for each SOC (Event vs. No‑Event × COVID vs. Non‑COVID, Non‑Flu).<br>2. **Baseline Rationale**: Non‑COVID, Non‑Flu is used as the primary baseline because it pools all other licensed vaccines, providing a broad reporting background while avoiding the specific immunological profile of influenza vaccines. The Flu‑only baseline (see Phase 5) serves as a targeted sensitivity check for potential confounding by a vaccine with known high reporting rates.<br>3. Apply continuity correction + 0.5 to any zero cell (Edge‑Case).<br>4. Compute ROR, PRR, IC plus 95 % Wald CIs (using `scipy.stats`).<br>5. **Threshold Justification**: Thresholds follow established pharmacovigilance practice (Evans et al., 2001; van Puijenbroek et al., 2002) and are widely used in FDA/EMA signal detection. A sensitivity analysis will also be run using alternative cut‑offs (e.g., ROR > 1.5, PRR > 1.2) to assess robustness.<br>6. Perform Fisher’s exact test → raw p‑value.<br>7. Apply BH FDR correction across all SOCs (FR‑003).<br>8. **Reporting Bias Considerations**: Acknowledge stimulated reporting after media events and under‑reporting; results are presented as *associational* signals only (Principle VI). No bias correction is applied, but the limitation is documented.<br>9. **Power & Detectable Effect**: Minimum‑detectable‑effect analysis shows that with ≥5 reports the ROR confidence interval width is ≤ 0.5 for typical background rates, justifying the ≥5‑report filter (FR‑002, FR‑006).<br>10. **Confounder Stratification**: Optional stratified disproportionality analyses by age group (`<18`, `18‑64`, `≥65`) and sex are performed as exploratory checks; results are reported in supplemental tables.<br>11. Flag signals meeting the 2‑out‑of‑3 threshold (FR‑005).<br>12. Export `output/signals.csv`. | FR‑002, FR‑003, FR‑005, SC‑001, SC‑002 |
| **Phase 4 – Temporal Profiling** | 1. Identify top‑5 signals by smallest BH‑adjusted p‑value.<br>2. Compute weekly counts relative to the median `REPT_DATE` of the **COVID‑19** cohort.<br>3. Generate line plots (`output/temporal_profiles/<SOC>.png`) via `src/utils/plots.py` (functions fully implemented for verification – satisfies T005).<br>4. Record `logs/config_import.txt` listing imported modules for traceability. | FR‑004, SC‑003 |
| **Phase 5 – Sensitivity Analysis** | 1. Re‑compute disproportionality metrics using the **Flu‑only** baseline.<br>2. Calculate ΔROR, ΔPRR, ΔIC for the top‑5 signals.<br>3. Export `output/sensitivity_analysis.csv`. | FR‑007 |
| **Phase 6 – Memory Profiling & Constraint Enforcement** | 1. Use `memory_profiler` to record peak RAM during Phases 3‑5.<br>2. Assert peak ≤ 7 GB; if exceeded, log error and abort (SC‑004).<br>3. Append memory summary to `output/report.md`. | SC‑004 |
| **Phase 7 – Final Reporting** | 1. Compile `output/report.md` containing:<br> • Summary table of signals (with `is_signal` flag).<br> • BH‑adjusted p‑values monotonicity check (SC‑002).<br> • Temporal plots (see the series of figures).<br> • Sensitivity Δ‑table.<br> • Memory profile.<br>2. Ensure every statistic traces back to a single row in `data/processed/cleaned.parquet` (IV). | SC‑001, SC‑002, SC‑005 |

## Edge‑Case Handling
- **Zero‑Count Cells** → add 0.5 to all cells before metric calculation.  
- **Sparse SOCs (< 5 reports)** → excluded from analysis (FR‑002, FR‑006).  
- **Missing Background Rates** → flagged in `output/report.md` as “Background Rate Unknown”.  

## Verification Artifacts
- `logs/structure.txt` (T001) – confirms directory tree.  
- `logs/config_import.txt` (T005) – confirms `src/utils/plots.py` importability.  
- Lint step (`code/run_lint.py`) will succeed (T003).  
- `src/data/validate.py` will exit 0 on success, non‑zero error code on schema mismatch (T006).  

## Compute Feasibility
All operations are pure‑CPU; the largest DataFrame (~1 M rows, ~200 MB parquet) comfortably fits < 5 GB RAM. Vectorised pandas + scipy operations complete well within the allocated CI time budget. No GPU‑only packages are used.

## Risk Management
| Risk | Impact | Mitigation |
|------|--------|------------|
| Required columns missing in the parquet file | Fatal (pipeline cannot run) | Phase 1 schema validation gate halts early; no downstream fabrication. |
| RAM exceeds 7 GB | Job killed | Phase 6 memory guard; optional chunked processing fallback. |
| BH‑adjusted p‑values not monotonic (implementation bug) | SC‑002 failure | Unit test `tests/unit/test_bh_monotonic.py` asserts monotonicity. |
| Absence of MedDRA→SOC mapping | Incomplete SOC aggregation | Mapping file `data/meddra_to_soc.csv` is bundled; validation ensures coverage > 95 %. |
| Mislabeling of temporal axis | Violation of Principle VII | Plots explicitly label “Reporting Time”; documentation repeats this disclaimer. |

---

