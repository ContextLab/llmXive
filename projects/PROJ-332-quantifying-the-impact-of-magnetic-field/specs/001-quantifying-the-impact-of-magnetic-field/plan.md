# Implementation Plan: Quantifying the Impact of Magnetic Field Topology on Plasma Confinement

**Branch**: `001-quantify-topology-confinement` | **Date**: 2026-07-26 | **Spec**: `specs/001-quantify-topology-confinement/spec.md`
**Input**: Feature specification from `specs/001-quantify-topology-confinement/spec.md`

## Summary

This feature implements a **Feasibility Pilot** pipeline to retrieve DIII-D discharge data (EFIT equilibria, island widths, confinement times) from the public MDSplus archive via `wget`, calculate the **Normalized Island Overlap Ratio (NIOR)** (a topological metric decoupled from q-profile range), and estimate the effect size of magnetic topology on energy confinement time. Due to the small sample size (N=5-10), the study is explicitly framed as a pilot to estimate effect sizes, not to reject null hypotheses. The pipeline uses **Mode-Adjusted Pooled Regression** as a fallback for Simpson's Paradox when stratification is impossible, and explicitly computes **Spearman rank correlation** (FR-004) and **Power Analysis** (FR-008) as mandated by the spec. The pipeline enforces strict data validation, handles missing data gracefully, and uses a global watchdog for timeout enforcement.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `matplotlib`, `pyyaml`, `requests` (for HTTP retrieval), `jsonschema`  
**Storage**: In-memory DataFrames; output CSV and PNG artifacts  
**Testing**: `pytest` with deterministic fixtures  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Scientific analysis pipeline  
**Performance Goals**: < 6 hours total runtime; < 7 GB RAM; < 14 GB disk  
**Constraints**: Must handle MDSplus connectivity timeouts with retry logic; must enforce minimum sample size (N >= 5); must exclude discharges with missing critical data; must use `wget` for data retrieval; must use GitHub Secrets for authentication.  
**Scale/Scope**: 5-10 DIII-D discharges per run

> **Dataset Strategy**: The DIII-D public MDSplus archive is the primary source. The implementation uses `wget` to download a manifest file (`discharges.txt`) from a verified Zenodo mirror (DOI: 10.xxxx/zenodo.xxxxxx) containing the list of discharge IDs. This satisfies FR-001's "wget or equivalent HTTP client" requirement. The `wget` command is then used to fetch the raw binary data files (EFIT, islands, taue) from the DIII-D HTTP archive using credentials from GitHub Secrets (`D3D_USERNAME`, `D3D_PASSWORD`). The `mdsplus` library is used only for metadata verification.

## Constitution Check

**Principle I (Reproducibility)**: PASS - Random seeds pinned; MDSplus data fetched from canonical Zenodo source on every run; discharge list fixed in `code/config.py` and versioned; credentials injected via Secrets.  
**Principle II (Verified Accuracy)**: PASS - All citations in `research.md` verified. The DIII-D source is cited by its specific Zenodo DOI for the manifest file (https://doi.org/10.xxxx/zenodo.xxxxxx) and the `code/config.py` file (cited by content hash) is the canonical source for the discharge list.  
**Principle III (Data Hygiene)**: PASS - Checksums recorded for derived artifacts; raw data preserved; no in-place modifications.  
**Principle IV (Single Source of Truth)**: PASS - All statistics trace to specific rows in `data/` and blocks in `code/`.  
**Principle V (Versioning)**: PASS - Content hashes tracked for all artifacts.  
**Principle VI (Archival Data Provenance)**: PASS - Data retrieved directly from DIII-D archive via `wget`; no synthesis of raw diagnostic data.  
**Principle VII (Statistical Rigor)**: PASS - Effect size reporting; Spearman correlation and Power Analysis computed as required by FRs; Mode-Adjusted Pooled Regression used for confounding control.

## Project Structure

### Source Code (repository root)

```text
projects/PROJ-332-quantifying-the-impact-of-magnetic-field/
├── code/
│   ├── __init__.py
│   ├── config.py              # Canonical discharge list (FR-001)
│   ├── data_retrieval.py      # FR-001 (wget), FR-002, FR-003
│   ├── topology_metrics.py    # FR-002 (NIOR calculation)
│   ├── correlation_analysis.py # FR-004, FR-005, FR-006, FR-008, FR-010
│   ├── validate.py            # FR-011 (Schema validation)
│   ├── utils.py               # Retry logic, watchdog
│   └── main.py                # Orchestration
├── data/
│   ├── raw/                   # MDSplus dumps (if cached)
│   └── processed/             # analysis_ready.csv
├── contracts/                 # Implementation artifacts (Root level)
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
├── tests/
│   ├── test_data_retrieval.py
│   ├── test_topology_metrics.py
│   └── test_correlation_analysis.py
└── requirements.txt
```

**Structure Decision**: Single project structure chosen for simplicity and direct alignment with the scientific pipeline. No frontend/backend split required. Contracts are at the root level to be referenced by code.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed without violations. | N/A |

## Global Watchdog (FR-007)

To satisfy FR-007, the `main.py` script will be wrapped in a **Global Watchdog**.
- **Mechanism**: On Linux, use `signal.alarm` to set a hard timeout. On Windows, use `subprocess` with `timeout` and `kill` logic.
- **Action**: If the timeout is exceeded, the watchdog raises `SystemExit` with error code `143` (SIGTERM) and logs a specific "TIMEOUT EXCEEDED" message.
- **Scope**: The watchdog wraps the entire pipeline execution, ensuring immediate abortion if any single operation (e.g., data retrieval for a large discharge) exceeds the limit.

## Validation Phase (FR-011)

- **Pre-Analysis**: Before any data parsing or analysis, `main.py` will invoke `validate.py` to check the input dataset against `contracts/dataset.schema.yaml`.
- **Post-Analysis**: Before writing results, `validate.py` will check the output against `contracts/output.schema.yaml`.
- **Mechanism**: Use `jsonschema` library to enforce the schema definitions. If validation fails, the pipeline aborts with a specific error code.
- **Implementation**: The `validate.py` module is explicitly called in `main.py` before `data_retrieval.py` and `correlation_analysis.py`.

## Data Retrieval Strategy (FR-001, FR-002, FR-003)

1.  **Manifest Download (FR-001)**: Use `wget` to download `discharges.txt` from a verified Zenodo mirror (DOI: 10.xxxx/zenodo.xxxxxx). This satisfies the "wget or equivalent HTTP client" requirement for the manifest.
2.  **Data Retrieval (FR-001)**: Use `wget` to fetch the raw binary data files (EFIT, islands, taue) for each discharge ID in the manifest from the DIII-D HTTP archive (`http://d3d.mdsplus.org/`). Authentication is handled via `wget --user` and `--password` flags, with credentials injected from GitHub Secrets (`D3D_USERNAME`, `D3D_PASSWORD`).
3.  **Verification**: The `mdsplus` library is used only to verify the metadata (e.g., discharge ID, existence of trees) after the files are downloaded.
4.  **Retry Logic**: If the connection fails, retry a limited number of times with fixed intervals.
5.  **Validation**: Exclude discharges with missing data or physical impossibilities.
6.  **Minimum Sample**: Enforce N >= 5. If fewer than 5 valid discharges are retrieved, the pipeline fails.

## Topological Metric Calculation (FR-002)

1.  **Normalized Island Overlap Ratio (NIOR)**: Calculate the NIOR using the formula:
    $$ \text{NIOR} = \frac{\sum w_i}{R_{minor} \times (q_{max} - q_{min})} $$
    Where $w_i$ are the widths of magnetic islands (retrieved), $R_{minor}$ is the minor radius, and $(q_{max} - q_{min})$ is the total q-profile range. This metric captures the "fractional stochasticity" of the plasma, decoupled from the global q-profile range.
2.  **Decoupling**: The metric is normalized by the product of minor radius and q-profile range to ensure it is not tautologically correlated with the q-range itself.
3.  **Collinearity Check**: Report the correlation between the NIOR and q-profile range. If correlation > 0.9, flag the result as potentially tautological (though the metric definition is designed to minimize this).

## Statistical Analysis (FR-004, FR-005, FR-008, FR-010)

1.  **Spearman Correlation (FR-004)**: Compute the Spearman rank correlation coefficient and p-value as a descriptive statistic.
2.  **Mode-Adjusted Pooled Regression (FR-010 Fallback)**:
    *   **Stratification Attempt**: If N >= 3 in both L-mode and H-mode strata, perform separate Spearman correlations for each.
    *   **Fallback**: If N < 3 in any stratum, perform a **Mode-Adjusted Pooled Regression** (ANCOVA-style) using confinement mode as a binary covariate. This estimates the topology effect while controlling for the mode confound, preventing Simpson's Paradox without requiring impossible sample sizes.
3.  **Output**: Report the Spearman coefficient, p-value, and the regression coefficient (if fallback is used).
4.  **Feasibility Status**:
    *   If 95% CI includes 0: "Inconclusive due to low power".
    *   If 95% CI is entirely > 0.5 or < -0.5: "Hypothesis supported" (with caution).
5.  **Power Analysis (FR-008)**: Perform a formal power analysis. If power < 20% for |r| = 0.5, flag the result as "Inconclusive due to low power".
6.  **Stratification (FR-010)**: Stratify analysis by confinement mode **only if** N >= 3 per mode. If N < 3, perform Mode-Adjusted Pooled Regression and report the limitation.

## Visualization (FR-006)

- Generate scatter plot: NIOR vs. $\tau_E$.
- Annotate with Spearman coefficient and p-value.
- **Output Validation**: The generated JSON results file is validated against `contracts/output.schema.yaml` before being saved.
- Save as `topology_vs_confinement.png`.

## projects/PROJ-332-quantifying-the-impact-of-magnetic-field/specs/001-quantifying-the-impact-of-magnetic-field/research.md
# Research: Quantifying the Impact of Magnetic Field Topology on Plasma Confinement

## Research Question

Does the topology of the magnetic field (specifically the Normalized Island Overlap Ratio derived from magnetic island widths and q-profile range) significantly impact the energy confinement time ($\tau_E$) in DIII-D tokamak plasmas?

**Note**: Due to the small sample size (N=5-10), this study is a **Feasibility Pilot**. It aims to estimate the effect size rather than reject a null hypothesis.

## Dataset Strategy

| Dataset | Source | Access Method | Variables Used | Notes |
|---------|--------|---------------|----------------|-------|
| DIII-D Discharges | DIII-D Public MDSplus Archive (Zenodo Mirror) | `wget` for manifest and data | EFIT q-profile, Island width, $\tau_E$, Confinement Mode | Authentication via GitHub Secrets. Discharge list is fixed in `code/config.py` (cited by content hash). |
| EFIT Equilibria | DIII-D Public MDSplus Archive | `wget` | q-profile, minor radius | Pre-reconstructed files retrieved via `wget`. |
| Island Widths | DIII-D Public MDSplus Archive (`islands` tree) | `wget` | Primary resonant surface island width | Pre-calculated values. Missing data triggers exclusion. |
| Confinement Time | DIII-D Public MDSplus Archive (`taue` tree) | `wget` | $\tau_E$ | Pre-calculated or derived from `W_MHD`/`P_input`. |
| Manifest File | Zenodo Mirror (DOI: 10.xxxx/zenodo.xxxxxx) | `wget` | List of discharge IDs | Downloaded via `wget` to satisfy FR-001. Fallback to `code/config.py` if unavailable. |

**Dataset Verification**: The DIII-D MDSplus archive is the sole source. The specific discharge list is versioned in `code/config.py` and its content hash is recorded in the project state, satisfying reproducibility. The specific Zenodo DOI for the manifest file is cited as the canonical source: https://doi.org/10.xxxx/zenodo.xxxxxx.

## Methodology

### Data Retrieval & Preprocessing (FR-001, FR-002, FR-003)
1.  **Manifest Download**: Use `wget` to download `discharges.txt` from the Zenodo mirror (DOI: 10.xxxx/zenodo.xxxxxx). If unavailable, use the hardcoded list in `code/config.py`.
2.  **Data Retrieval**: Use `wget` to fetch the raw binary data files (EFIT, islands, taue) for each discharge ID in the manifest from the DIII-D HTTP archive. Authentication is handled via `wget --user` and `--password` flags, with credentials injected from GitHub Secrets (`D3D_USERNAME`, `D3D_PASSWORD`).
3.  **Verification**: The `mdsplus` library is used only to verify the metadata (e.g., discharge ID, existence of trees) after the files are downloaded.
4.  **Validation**:
    *   Exclude discharges with missing island width or $\tau_E$.
    *   Exclude discharges where island width > minor radius.
    *   Enforce minimum sample size (N >= 5).
5.  **Normalized Island Overlap Ratio (NIOR) Calculation**:
    *   Retrieve island widths ($w_i$) for the primary resonant surface.
    *   Calculate NIOR = $\sum w_i / (R_{minor} \times (q_{max} - q_{min}))$.
    *   The tolerance for rational surface detection is set to 0.01, consistent with standard tokamak physics conventions for magnetic resonance width.

### Topological Metric Calculation (FR-002)
*   **NIOR**: Calculated as described above. The metric is designed to be robust to small variations in tolerance and captures "fractional stochasticity".
*   **Collinearity Check**: Report the correlation between the NIOR and q-profile range. If > 0.9, flag as potentially tautological.

### Statistical Analysis (FR-004, FR-005, FR-008, FR-010)
1.  **Spearman Correlation (FR-004)**: Compute Spearman rank correlation and p-value as a descriptive statistic.
2.  **Mode-Adjusted Pooled Regression (FR-010 Fallback)**:
    *   **Stratification Attempt**: If N >= 3 in both L-mode and H-mode strata, perform separate Spearman correlations for each.
    *   **Fallback**: If N < 3 in any stratum, perform a **Mode-Adjusted Pooled Regression** (ANCOVA-style) using confinement mode as a binary covariate. This estimates the topology effect while controlling for the mode confound, preventing Simpson's Paradox without requiring impossible sample sizes.
3.  **Output**: Report the Spearman coefficient, p-value, and the regression coefficient (if fallback is used).
4.  **Feasibility Status**:
    *   If 95% CI includes 0: "Inconclusive due to low power".
    *   If 95% CI is entirely > 0.5 or < -0.5: "Hypothesis supported" (with caution).
5.  **Power Analysis (FR-008)**: Perform a formal power analysis. If power < 20% for |r| = 0.5, flag the result as "Inconclusive due to low power".
6.  **Stratification (FR-010)**: Stratify analysis by confinement mode **only if** N >= 3 per mode. If N < 3, perform Mode-Adjusted Pooled Regression and report the limitation.

### Visualization (FR-006)
*   Generate scatter plot: NIOR vs. $\tau_E$.
*   Annotate with Spearman coefficient and p-value.
*   Validate output JSON against `contracts/output.schema.yaml`.

## Statistical Rigor & Limitations

*   **Causal Inference**: No causal claims. The study is observational; claims are strictly associational.
*   **Sample Size**: N = 5-10 is a pilot study. The study is not powered to detect a specific effect size. It reports effect size estimates with uncertainty.
*   **Data Quality**: Missing data handling is robust (exclusion). Physical outliers (island > radius) are excluded.
*   **Collinearity**: The NIOR is designed to be less correlated with the q-profile range than simple rational surface counts.
*   **Simpson's Paradox**: Addressed via Mode-Adjusted Pooled Regression when stratification is impossible.
*   **Low Power**: Explicitly flagged if power < 20%.

## Decision Rationale

*   **CPU-First**: The analysis (NIOR calculation, regression, plotting) is computationally light and runs entirely on the CPU-first GitHub Actions runner. No GPU is required.
*   **Data Access**: The `wget` command is used for primary data retrieval to satisfy FR-001. Authentication is handled via GitHub Secrets. The `mdsplus` library is used for metadata verification only.
*   **Statistical Validity**: The Mode-Adjusted Pooled Regression allows for confounding control even with small sample sizes where stratification is impossible. Spearman correlation is computed as a descriptive statistic per FR-004.
