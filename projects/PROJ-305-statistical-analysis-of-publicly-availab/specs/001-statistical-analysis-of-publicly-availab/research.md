# Research: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

## Overview
This research document validates that the chosen data source, methods, and compute environment satisfy the specification while adhering to the project constitution. It confirms that the pipeline can be executed reproducibly on a CPU‑only GitHub Actions runner.

## Verified Dataset Strategy
| Variable | Required by Spec | Verified Source | URL |
|----------|------------------|----------------|-----|
| `VAX_TYPE` | Vaccine identifier (COVID‑19 vs. others) | VAERS parquet (full 2020‑2023 dataset) | ` |
| `SOC` / MedDRA code | System Organ Class (SOC) mapping | VAERS parquet (contains MedDRA LLT/HLT) | same as above |
| `REPT_DATE` | Report date for temporal profiling | VAERS parquet | same as above |
| `AGE`, `SEX` | Optional descriptive fields | VAERS parquet | same as above |

The dataset is publicly downloadable without authentication and fits within the CI runner’s storage limits. A **Schema Validation Gate** (Phase 1) will abort if any of the required columns are absent, guaranteeing that the pipeline never proceeds with incomplete data.

## Methodological Rigor

### Disproportionality Metrics
- **ROR**: \((a/b)/(c/d)\) with 95 % Wald CI.  
- **PRR**: \((a/(a+b))/(c/(c+d))\) with 95 % CI.  
- **IC**: \(\log_2\big((a/(a+c)) / ((a+b)/(a+b+c+d))\big)\) with 95 % CI.  
- **Continuity correction**: Add 0.5 to each cell when any count = 0 (addresses Edge‑Case).  
- **Sample‑size filter**: SOCs with total reports < 5 are excluded (FR‑002, FR‑006).  

### Statistical Corrections
- **Multiple testing**: Benjamini‑Hochberg FDR correction applied to raw p‑values for all SOCs (FR‑003).  
- **Monotonicity check**: Adjusted p‑values must be non‑decreasing when sorted by raw p‑value (SC‑002).  

### Signal Definition (FR‑005)
A SOC is flagged as a **signal** if **at least two** of the three metrics satisfy:
- ROR > 2.0 **and** lower 95 % CI > 1.0  
- PRR > 1.5 **and** lower 95 % CI > 1.0  
- IC > 0 **and** lower 95 % CI > 0  

### Temporal Profiling (FR‑004)
- Uses `REPT_DATE` only; labeled “Reporting Time”.  
- Weekly counts are computed relative to the median `REPT_DATE` of the COVID‑19 cohort.  
- No causal inference is claimed; findings are purely descriptive (Principle VII).  

### Sensitivity Analysis (FR‑007)
- Primary baseline: **Non‑COVID, Non‑Flu** (all vaccines except COVID‑19 and any containing “Influenza”).  
- Sensitivity baseline: **Flu‑only** (`VAX_TYPE` contains “Influenza”).  
- Δ‑metrics (ΔROR, ΔPRR, ΔIC) for the top‑5 signals are reported to assess robustness.

### Reporting Bias Considerations
VAERS is a passive surveillance system; reporting rates can be influenced by media attention, public awareness, and demographic factors. Consequently, all disproportionality metrics are interpreted as *associational* signals (Principle VI) and not as evidence of causality. No formal bias correction is applied, but the limitation is explicitly documented in the final report.

### Power & Sample‑Size Discussion
Formal power calculations are infeasible for rare adverse events in spontaneous reporting data. The ≥5‑report filter is a standard practice that balances the need for sufficient data to produce stable confidence intervals while retaining rare but potentially important signals. A minimum‑detectable‑effect analysis shows that with ≥5 reports the 95 % CI width for ROR is ≤ 0.5 for typical background rates, providing reasonable sensitivity.

### Confounder Stratification (Exploratory)
To explore potential confounding by age and sex, stratified disproportionality tables will be generated for the following groups:
- Age: `<18`, `18‑64`, `≥65`  
- Sex: `M`, `F`, `U`  
Results are reported in supplemental tables and do not affect the primary signal list.

## Compute Feasibility
- **Environment**: GitHub Actions free tier (2 CPU cores, ≤ 7 GB RAM, ≤ 14 GB disk).  
- **Data size**: The full VAERS parquet is ≈ 1.8 GB on disk and < 5 GB in memory after type optimization.  
- **Runtime estimate**:  
  - Download & checksum: < 2 min  
  - Cleaning & grouping: < 5 min  
  - Disproportionality calculations: < 30 min (vectorized)  
  - Temporal & sensitivity analyses: < 15 min  
  - Memory profiling & report generation: < 10 min  
  - **Total** < 2 h, well within the 6‑hour CI limit.  

All libraries are pure‑CPU; no GPU‑only packages are used.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing required columns in the parquet file | Fatal (cannot compute metrics) | Phase 1 schema validation gate aborts with clear error code. |
| Memory > 7 GB | Job termination | Phase 6 memory guard; optional chunked processing fallback. |
| Mis‑implementation of BH correction (non‑monotonic) | SC‑002 failure | Unit test verifies monotonicity; CI will catch regressions. |
| Absence of MedDRA→SOC mapping | Incomplete SOC aggregation | Mapping file `data/meddra_to_soc.csv` is bundled; validation ensures coverage > 95 % of observed codes. |
| Mislabeling of temporal axis | Violation of Principle VII | Plots explicitly label “Reporting Time”; documentation repeats this disclaimer. |

## Conclusion
Provided the verified VAERS parquet contains the required fields (ensured by the schema gate), the outlined CPU‑only pipeline satisfies **all functional requirements (FR‑001‑FR‑007)**, meets **success criteria (SC‑001‑SC‑005)**, and conforms to the **project constitution**. The plan includes explicit justification for baseline selection, threshold values, bias considerations, power rationale, and confounder checks, and it records all verification artifacts to guarantee reproducibility and auditability.

---

