# Research: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

## Dataset Strategy

The project relies on two primary data sources. Per the project constitution and verified dataset list, we will use the following sources. **Note:** The verified list contains some datasets that do not perfectly match the global reanalysis requirements. The plan is explicitly scoped to **Methodology Validation** using verified test data.

| Dataset | Purpose | Verified URL / Source | Strategy |
|:--- |:--- |:--- |:--- |
| **USGS Earthquake Catalog** | Seismic events (M≥4.0, depth≤70km) | ` | Load CSV. Filter by magnitude, depth, and date range. Deduplicate by event ID. |
| **Atmospheric Pressure** | Global sea-level pressure (SLP) | **Gap Identified**: No verified source for full global NCEP/NCAR daily reanalysis grid (2013-2023). | **Action**: Use verified test datasets (`lowo/ncep-TestData1`) to validate the pipeline logic. **Conclusion**: The global analysis is **blocked**. This study is a **Pilot/Methodology Validation** only. |
| **Climate Indices (ENSO/PDO)** | Control window stratification | **Gap Identified**: No verified URL for ENSO/PDO indices. | **Action**: FR-011 is **DEFERRED**. No stratification will be performed. The analysis will rely on temporal matching only, acknowledging this limitation. |

**Dataset Variable Fit Check**:
- **USGS**: Contains `time`, `mag`, `depth`, `latitude`, `longitude`, `id`. **Fit**: Yes.
- **Pressure**: The verified test datasets (`lowo/ncep-TestData1`) are small. **Fit**: No, not for global 2013-2023 analysis. **Conclusion**: The plan explicitly states that the *global* analysis is blocked. The implementation will run on the available test data to demonstrate the *methodology*.

## Statistical Methodology

### 1. Pre-processing & Anomaly Definition
- **Interpolation**: 2.5° grid → 1° grid (bilinear) for pressure.
- **Data Thinning**: To address autocorrelation, the earthquake catalog will be thinned to ensure temporal independence (e.g., one event per 30 days per region) before statistical testing.
- **Anomaly Calculation**: For each earthquake event $t$:
 - **Baseline Window**: $t-90$ to $t-60$ (30 days).
 - **Event Window**: $t-48$ to $t$ (48 hours).
 - **Gap**: A 12-day gap exists between the baseline end ($t-60$) and event start ($t-48$).
 - $P_{anomaly}(t) = P(t) - \mu_{baseline}$.
 - **Note**: Precursors shorter than 12 days may still contaminate the baseline. This is a known limitation of the 30-day baseline requirement.
- **Control Windows**: Defined as the **exact 48-hour UTC interval** (same start time, same calendar date, same year offset) in non-event years. This ensures diurnal cycle alignment for the entire window.

### 2. Primary Hypothesis Tests
- **Kolmogorov-Smirnov (KS) Test**: Compare distribution of $P_{anomaly}$ in event windows vs. control windows.
 - $H_0$: Distributions are identical.
 - $H_1$: Distributions differ.
- **Permutation Test**:
 - Shuffle event/control labels [deferred] times.
 - Calculate KS statistic for each shuffle.
 - $p = \frac{\text{count}(\text{stat}_{perm} \ge \text{stat}_{obs}) + 1}{N_{perm} + 1}$.

### 3. Robustness & Sensitivity
- **Stratification**: **DEFERRED** (No ENSO/PDO data).
- **Sensitivity**: Sweep anomaly cutoff $\in \{0.5\sigma, 1.0\sigma, 1.5\sigma\}$.
 - **Critical**: $\sigma$ (standard deviation) is calculated from a **clean dataset** that excludes all event windows, control windows, and the 90-day buffer zones to ensure independence.
- **Multiple Comparisons**: Apply Benjamini-Hochberg FDR correction to all p-values generated across strata.

### 4. Causal Framing
- **Constraint**: All results must be framed as **associational**. No causal claims (e.g., "pressure causes earthquakes") will be made. The study is observational.

## Feasibility & Constraints

- **Compute**: CPU-only. Permutation test (10k iterations) on the test dataset subset is feasible (< 2 hours).
- **Memory**: Test datasets are small. Global datasets would require chunking, but global analysis is blocked.
- **Disk**: Raw data checksums stored. Interim files cleaned after processing.

## Limitations & Gaps

1. **Data Gap (Critical)**: No verified source for global NCEP/NCAR reanalysis (2013-2023) exists. The project is limited to **Methodology Validation** on test data. Global results cannot be produced.
2. **Climate Indices (Deferred)**: No verified source for ENSO/PDO indices. Stratification is not performed.
3. **Baseline Contamination**: The 12-day gap between baseline and event window may not fully exclude precursors shorter than 12 days.
4. **Causal Inference**: Observational nature prevents causal claims.
5. **Temporal Independence**: Data thinning is required to satisfy KS test assumptions.
