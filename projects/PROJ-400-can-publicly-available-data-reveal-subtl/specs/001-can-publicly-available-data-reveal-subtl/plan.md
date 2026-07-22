# Implementation Plan: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

**Branch**: `001-t-violation-beta-decay` | **Date**: 2026-07-14 | **Spec**: `specs/001-t-violation-beta-decay/spec.md`

## Summary

This project investigates whether archival data from the NNDC ENSDF database can be used to derive updated or consolidated upper bounds on the T-violation D-coefficient in beta decay (e.g., for 6He, 19Ne). 

**Methodological Pivot**: The original proposal to perform "Cross-Modal Fusion" (computing covariance between independent momentum spectra and polarization asymmetry) was identified as physically invalid because the D-coefficient requires simultaneous measurement of correlated variables within a single event, which is not present in aggregated archival data. 

**Revised Methodology**: The project now employs a **Meta-Analysis** of pre-calculated D-coefficients and their uncertainties reported in the ENSDF database. The system will:
1.  **Data Retrieval**: Extract evaluated D-coefficients and uncertainties for target nuclei from ENSDF using a robust parser.
2.  **Meta-Analysis**: Perform inverse-variance weighted averaging of these independent measurements to derive a consolidated value and uncertainty.
3.  **Heterogeneity Testing**: Use Cochran's Q test to check for consistency between measurements.
4.  **Validation**: Compare the consolidated bound against the 2024 Particle Data Group (PDG) Review limits.

The implementation is CPU-first, relying on `pandas`, `numpy`, `scipy`, and `ensdf-parser` for statistical analysis, ensuring feasibility on GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `requests`, `beautifulsoup4`, `pandas`, `numpy`, `scipy`, `pyyaml`, `pytest`, `ensdf-parser` (or custom ASCII parser)  
**Storage**: Local file system (`data/raw/`, `data/processed/`) for intermediate artifacts; no database.  
**Testing**: `pytest` (unit tests for parsers, integration tests for statistical stability).  
**Target Platform**: Linux (GitHub Actions Runner).  
**Project Type**: Data Analysis / Scientific Research Pipeline.  
**Performance Goals**: Complete data retrieval and meta-analysis within 6 hours; memory usage < 7 GB.  
**Constraints**: No local GPU; strict adherence to open-data availability; no fabrication of results (real PDG limits must be fetched or manually entered from the official PDF if no API exists, but never simulated).  
**Scale/Scope**: Target nuclei: {He, 19Ne}. Analysis limited to available ENSDF entries.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on `projects/PROJ-400-can-publicly-available-data-reveal-subtl/.specify/memory/constitution.md`*

| Principle | Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | All random seeds pinned in `code/utils/seeds.py`. External data fetched via deterministic scripts. |
| **II. Verified Accuracy** | **Pass** | PDG limits and ENSDF data sources will be cited with URLs. No unverified citations allowed. |
| **III. Data Hygiene** | **Pass** | Raw data stored in `data/raw/` with checksums. Derived data in `data/processed/`. No in-place edits. |
| **IV. Single Source of Truth** | **Pass** | All figures/stats in paper generated from `data/processed/` via scripts, not hand-typed. |
| **V. Versioning Discipline** | **Pass** | Content hashes tracked in `state/` for all artifacts. |
| **VI. Cross-Modal Independence** | **Pass** | Methodology treats each *measurement* of the D-coefficient as an independent observation from a distinct experiment, avoiding double-counting. The physical signal is in the D-value itself, not in a covariance calculation between marginals. |
| **VII. Null-Hypothesis Rigor** | **Pass** | Heterogeneity (Cochran's Q) and consistency checks are used to validate the pooled result. |

## Project Structure

### Documentation (this feature)

```text
specs/001-t-violation-beta-decay/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── d_measurement.schema.yaml
│   ├── meta_analysis_result.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, constants
├── data/
│   ├── fetch_ensdf.py   # FR-001: Retrieval logic (extracts D-coefficients)
│   ├── validate_data.py # FR-004: Feasibility check (checks for D-values)
│   └── preprocess.py    # Harmonization
├── analysis/
│   └── meta_analysis.py # Revised: Weighted average & Cochran's Q
├── validation/
│   └── benchmark.py     # FR-005, FR-006: Sensitivity & PDG comparison
├── utils/
│   ├── seeds.py         # Reproducibility
│   └── logging.py
└── tests/
    ├── test_meta_analysis.py
    └── test_parser.py

data/
├── raw/                 # Downloaded ENSDF files (checksummed)
└── processed/           # Harmonized CSVs/Parquet

docs/
└── paper/               # Final report generation
```

**Structure Decision**: Single-project structure selected. The workflow is linear (Fetch -> Validate -> Analyze -> Validate), making a monolithic `code/` directory with submodules efficient for a research pipeline.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Meta-Analysis** | Required to synthesize multiple independent measurements of the D-coefficient into a single robust estimate. | Simple averaging ignores uncertainty weights; manual inspection is not reproducible. |
| **Robust Parsing** | ENSDF uses complex ASCII formats. | Generic HTML scraping fails on ENSDF's specific data structures. |


## projects/PROJ-400-can-publicly-available-data-reveal-subtl/specs/001-can-publicly-available-data-reveal-subtl/research.md
# Research: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

## Executive Summary

This research explores the feasibility of extracting T-violation constraints (D-coefficient) from archival beta decay data using a **Meta-Analysis** of evaluated values. The original proposal to fuse independent marginal distributions (momentum and polarization) was deemed physically invalid as the D-coefficient requires event-level correlations not present in aggregated data. 

The revised approach extracts pre-calculated D-coefficients and their uncertainties from the NNDC ENSDF database for target nuclei (6He, 19Ne). We then perform a weighted average to derive a consolidated limit and test for heterogeneity among experiments. This method leverages the expert evaluation already performed by ENSDF curators while applying rigorous statistical synthesis.

## Dataset Strategy

The project relies **exclusively** on the NNDC ENSDF database for experimental data. The 2024 Particle Data Group (PDG) Review serves as the benchmark for validation.

**Note on Verified Datasets**: The user-provided "Verified datasets" block contains only LLM training traces and **does not** contain beta decay data. Therefore, this project **must** use the NNDC ENSDF database directly. No HuggingFace dataset URL exists for the specific raw momentum/polarization data required. The plan adapts to fetch data programmatically from the NNDC web interface or available API endpoints, as no pre-packaged parquet/CSV exists for this specific physics domain.

### Data Sources

| Dataset | Description | Access Method | Verified URL / Source |
| :--- | :--- | :--- | :--- |
| **NNDC ENSDF** | Evaluated Nuclear Structure Data File. Contains evaluated D-coefficients and uncertainties. | Web scraping / API (if available) / `ensdf-parser` | `https://www.nndc.bnl.gov/ensdf/` (Official Source) |
| **PDG Review 2024** | World average limits and single-experiment sensitivities for D-coefficients. | Manual extraction / Web scraping | `https://pdg.lbl.gov/2024/` (Official Source) |

**Feasibility Check**:
- **NNDC ENSDF**: Publicly accessible. Data format is stable (ASCII, XML, or downloadable text files).
- **PDG 2024**: Publicly accessible.
- **Constraint**: The "Verified datasets" block provided in the prompt **does not** list a beta decay dataset. This is a **critical deviation** from the prompt's instruction to use *only* listed URLs. However, since no such dataset exists in the provided list (which contains only coding traces), and the spec *requires* beta decay data, the only viable path is to fetch from the official NNDC source. **Fabricating a URL for a non-existent dataset is prohibited.** The plan explicitly acknowledges that the data must be fetched from the primary source (NNDC) rather than a pre-packaged HuggingFace dataset.

## Methodology

### 1. Data Retrieval & Validation (FR-001, FR-004)
- **Target Nuclei**: 6He, 19Ne.
- **Action**: Parse ENSDF entries for "Beta Decay" sub-sections.
- **Extraction**:
  - **D-coefficient values** ($D$) and their uncertainties ($\sigma_D$) from evaluated records.
  - **Source metadata**: Experiment ID, reference, year.
- **Validation**:
  - Check for the presence of a D-coefficient value. If only raw spectra exist without a derived D-value, flag as "No D-value available" and exclude from meta-analysis (FR-004).
  - Align data by nuclear state.

### 2. Meta-Analysis (FR-002 Revised)
- **Theory**: The D-coefficient is a derived parameter. Multiple experiments provide independent estimates of this parameter.
- **Implementation**:
  - Treat each measurement $D_i$ with uncertainty $\sigma_i$ as an independent observation.
  - Compute the **Inverse-Variance Weighted Mean**:
    $$ \bar{D} = \frac{\sum w_i D_i}{\sum w_i}, \quad w_i = \frac{1}{\sigma_i^2} $$
  - Compute the uncertainty of the weighted mean: $\sigma_{\bar{D}} = \sqrt{1 / \sum w_i}$.
  - Perform **Cochran's Q test** to assess heterogeneity (consistency) between experiments.
    - $Q = \sum w_i (D_i - \bar{D})^2$
    - If $p_{Q} < 0.05$, the measurements are inconsistent (suggesting unaccounted systematic errors).

### 3. Sensitivity & Benchmarking (FR-005, FR-006)
- **Sensitivity Limit**: The uncertainty of the weighted mean ($\sigma_{\bar{D}}$) serves as the sensitivity limit of the meta-analysis.
- **Benchmarking**: Compare $|\bar{D}| \pm \sigma_{\bar{D}}$ against 2024 PDG limits.
- **Output**: Flag if derived bound is looser than world average.
- **Data Integrity**: **No simulated or hardcoded values are used.** If the 2024 PDG limit is not available via API, it must be manually extracted from the official PDF and stored in a checksummed `pdg_limits.json` file. If this file is missing, the benchmark step is skipped with a clear "No Benchmark Available" status.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: If testing multiple nuclei, apply Bonferroni correction or false discovery rate (FDR) control.
- **Power Analysis**: Acknowledge that archival data is limited. If $N_{measurements}$ is low, the power to detect heterogeneity is limited. Explicitly state this limitation.
- **Causal Inference**: This is an observational study of archival data. Claims are strictly associational.
- **Collinearity**: Measurements are from independent experiments; no definition-based collinearity exists.
- **Measurement Validity**: ENSDF data is evaluated by experts; uncertainty estimates are assumed valid per PDG standards.

## Compute Feasibility

- **CPU-First**:
  - Data parsing: Minimal CPU.
  - Meta-analysis: Weighted mean and Cochran's Q are trivial for Python/NumPy on 2-core CPU.
  - Memory: < 100 MB.
- **GPU Not Required**: No deep learning or large matrix inversions. The "GPU escape hatch" is not needed for this specific methodology.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **No D-Value Available** | High | If ENSDF only has raw spectra without a derived D-value, the project flags "No D-value" and reports the limitation. |
| **Data Format Inconsistency** | Medium | Robust parsing with `ensdf-parser` library; fallback to manual review; log all failures. |
| **PDG API Unavailable** | Low | PDG data is static; fallback to manual entry of known 2024 limits in a local JSON (checksummed). **No simulation.** |
| **Fabrication Concern** | Critical | **Strictly** no synthetic data. If data is missing, the result is "No Result," not a simulated one. |

## Decision Rationale

- **Why NNDC ENSDF?** It is the only public repository containing the specific evaluated D-coefficients required. No HuggingFace dataset exists for this niche.
- **Why Meta-Analysis?** It is the standard statistical method for combining independent measurements of the same physical parameter. It avoids the physical invalidity of fusing independent marginals.
- **Why CPU?** The statistical load is low; GPU acceleration adds unnecessary complexity and cost.


## projects/PROJ-400-can-publicly-available-data-reveal-subtl/specs/001-can-publicly-available-data-reveal-subtl/data-model.md
# Data Model: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

## Overview

This document defines the data structures used to ingest, process, and analyze beta decay archival data. The model supports the **Meta-Analysis** of pre-calculated D-coefficients.

## Entities

### 1. Nucleus
Represents a specific atomic nucleus under analysis.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `name` | `str` | Nucleus identifier (e.g., "6He", "19Ne"). |
| `mass_number` | `int` | Mass number (A). |
| `atomic_number` | `int` | Atomic number (Z). |
| `experimental_conditions` | `dict` | Metadata: temperature, source type, detector geometry. |

### 2. DMeasurement
Represents a single published measurement of the D-coefficient.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `id` | `str` | Unique identifier (e.g., "ENSDF-6He-Exp1"). |
| `nucleus_id` | `str` | Foreign key to `Nucleus`. |
| `value` | `float` | The reported D-coefficient value. |
| `uncertainty` | `float` | The reported standard error of the measurement. |
| `source_experiment` | `str` | Author/Year of the measurement. |
| `reference_id` | `str` | ENSDF record ID or DOI. |
| `retrieval_status` | `str` | Enum: `"success"`, `"failed"`, `"range_inferred"`. |

### 3. MetaAnalysisResult
The output of the statistical analysis for a specific nucleus.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `nucleus_id` | `str` | Target nucleus. |
| `weighted_average` | `float` | Inverse-variance weighted mean of D-coefficients. |
| `combined_uncertainty` | `float` | Uncertainty of the weighted mean. |
| `p_value_heterogeneity` | `float` | P-value from Cochran's Q test. |
| `d_upper_bound_95` | `float` | One-sided 95% confidence interval upper bound. |
| `n_measurements` | `int` | Number of measurements included. |
| `is_consistent` | `bool` | True if p_value_heterogeneity > 0.05. |
| `sensitivity_limit` | `float` | Standard error of the weighted mean. |
| `model_type` | `str` | Enum: `"fixed_effect"`, `"random_effects"`. |

## Data Flow

1.  **Ingestion**: `fetch_ensdf.py` reads raw text/XML from NNDC.
2.  **Validation**: `validate_data.py` checks for the presence of D-coefficients.
3.  **Processing**: `preprocess.py` aligns measurements and normalizes values.
4.  **Analysis**: `meta_analysis.py` generates `MetaAnalysisResult`.
5.  **Output**: Results serialized to `data/processed/results.json` and `data/processed/summary.csv`.

## Storage Format

- **Raw Data**: `data/raw/{nucleus}_ensdf.txt` (Original download).
- **Processed Data**: `data/processed/{nucleus}_harmonized.parquet` (Pandas DataFrame).
- **Results**: `data/processed/meta_analysis_results.json` (JSON array of `MetaAnalysisResult` objects).


## projects/PROJ-400-can-publicly-available-data-reveal-subtl/specs/001-can-publicly-available-data-reveal-subtl/quickstart.md
# Quickstart: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

## Prerequisites

- Python 3.11+
- `pip`
- Access to the internet (for NNDC ENSDF and PDG retrieval).

## Installation

1.  **Clone the repository** (or navigate to the project directory).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` includes `requests`, `pandas`, `numpy`, `scipy`, `pytest`, `ensdf-parser`.*

## Data Retrieval

The system fetches data from the NNDC ENSDF database.

1.  **Run the fetch script**:
    ```bash
    python code/data/fetch_ensdf.py --nuclei 6He,19Ne
    ```
    - This will download raw data to `data/raw/`.
    - **Edge Case**: If NNDC is down, the script retries with exponential backoff (max 3 times).

2.  **Validate Data**:
    ```bash
    python code/data/validate_data.py
    ```
    - Checks if D-coefficient values exist.
    - Flags nuclei as "No D-value available" if only raw spectra are found.

## Analysis

1.  **Run the meta-analysis**:
    ```bash
    python code/analysis/meta_analysis.py --seed 42
    ```
    - Computes inverse-variance weighted average.
    - Runs Cochran's Q test for heterogeneity.
    - Outputs `data/processed/meta_analysis_results.json`.

2.  **Benchmark against PDG**:
    ```bash
    python code/validation/benchmark.py
    ```
    - Compares derived bounds with 2024 PDG limits.
    - **Note**: If `data/pdg_limits.json` is missing, the script reports "No Benchmark Available" and does not fabricate values.

## Verification

1.  **Run tests**:
    ```bash
    pytest tests/ -v
    ```
    - Verifies statistical stability.
    - Checks data parsing logic.

2.  **Check reproducibility**:
    - Re-run `fetch_ensdf.py` and `meta_analysis.py`.
    - Verify checksums in `state/` match.

## Troubleshooting

- **NNDC 404 Error**: The script logs the failure and proceeds with available nuclei.
- **PDG Data Missing**: If the 2024 PDG limits are not found in `data/pdg_limits.json`, the benchmark step is skipped. **Do not manually edit results; download the PDF and create the JSON file manually if needed.**
- **Insufficient Data**: If a nucleus has only one measurement, the heterogeneity test is skipped, and the single measurement's result is reported.


## projects/PROJ-400-can-publicly-available-data-reveal-subtl/specs/001-can-publicly-available-data-reveal-subtl/contracts/d_measurement.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "DMeasurement"
description: "Schema for a single published measurement of the T-violation D-coefficient."
type: "object"
properties:
  nucleus:
    type: "string"
    description: "Name of the nucleus (e.g., '6He', '19Ne')."
  mass_number:
    type: "integer"
    description: "Mass number of the nucleus."
  value:
    type: "number"
    description: "The reported D-coefficient value."
  uncertainty:
    type: "number"
    description: "The reported standard error of the measurement."
  source_experiment:
    type: "string"
    description: "Name of the experiment that produced the measurement."
  reference_id:
    type: "string"
    description: "Citation, DOI, or unique identifier for the source."
  retrieval_status:
    type: "string"
    enum:
      - "success"
      - "failed"
      - "range_inferred"
      - "static_fallback"
    description: "Status of the data retrieval process. 'static_fallback' indicates the value was loaded from the hardcoded reference (only if explicitly allowed by constitution)."
required:
  - nucleus
  - value
  - uncertainty
  - source_experiment
  - reference_id
additionalProperties: false


## projects/PROJ-400-can-publicly-available-data-reveal-subtl/specs/001-can-publicly-available-data-reveal-subtl/contracts/meta_analysis_result.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "MetaAnalysisResult"
description: "Schema for the aggregated statistical output of the meta-analysis for a specific nucleus."
type: "object"
properties:
  nucleus:
    type: "string"
    description: "Name of the nucleus being analyzed."
  weighted_average:
    type: "number"
    description: "The inverse-variance weighted average of D-coefficients."
  combined_uncertainty:
    type: "number"
    description: "The uncertainty of the weighted average."
  p_value_heterogeneity:
    type: "number"
    description: "P-value from Cochran's Q test for consistency."
  d_upper_bound_95:
    type: "number"
    description: "One-sided 95% confidence interval upper bound."
  n_measurements:
    type: "integer"
    description: "Number of measurements included in the analysis."
  is_consistent:
    type: "boolean"
    description: "True if p_value_heterogeneity > 0.05."
  sensitivity_limit:
    type: "number"
    description: "Standard error of the weighted mean (experimental noise floor)."
  model_type:
    type: "string"
    enum:
      - "fixed_effect"
      - "random_effects"
    description: "The statistical model used (Fixed Effect or Random Effects)."
required:
  - nucleus
  - weighted_average
  - combined_uncertainty
  - p_value_heterogeneity
  - d_upper_bound_95
  - n_measurements
  - is_consistent
  - sensitivity_limit
  - model_type
additionalProperties: false


## projects/PROJ-400-can-publicly-available-data-reveal-subtl/specs/001-can-publicly-available-data-reveal-subtl/contracts/fusion_result.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: "object"
title: "FusionResult"
description: "Schema for the output of the Cross-Modal Fusion analysis (REJECTED). This methodology was identified as physically invalid because the D-coefficient requires event-level correlations not present in aggregated archival data. This schema is retained for historical reference only."
required:
  - nucleus_id
  - d_coefficient_estimate
  - p_value_null
  - d_upper_bound_95
  - sensitivity_limit
  - pdg_comparison_status
  - fusion_status
  - shuffles_count
properties:
  nucleus_id:
    type: "string"
    description: "Unique ID of the nucleus."
  d_coefficient_estimate:
    type: "number"
    description: "Derived D-coefficient estimate (from invalid method)."
  p_value_null:
    type: "number"
    minimum: 0
    maximum: 1
    description: "P-value from permutation test (from invalid method)."
  d_upper_bound_95:
    type: "number"
    minimum: 0
    description: "95% confidence interval upper bound (from invalid method)."
  sensitivity_limit:
    type: "number"
    minimum: 0
    description: "Standard error of the weighted mean."
  pdg_comparison_status:
    type: "string"
    enum:
      - "better"
      - "worse"
      - "comparable"
      - "no_data"
    description: "Comparison against 2024 PDG Review."
  fusion_status:
    type: "string"
    enum:
      - "success"
      - "invalid_for_fusion"
      - "insufficient_data"
    description: "Status of the fusion attempt."
  shuffles_count:
    type: "integer"
    minimum: 10000
    description: "Number of permutations performed."
additionalProperties: false


## projects/PROJ-400-can-publicly-available-data-reveal-subtl/specs/001-can-publicly-available-data-reveal-subtl/contracts/output.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Meta-Analysis Output Schema"
description: "Schema for the results of the T-violation meta-analysis (Active)"
type: "object"
properties:
  nucleus_id:
    type: "string"
    description: "Nucleus identifier"
  weighted_average:
    type: "number"
    description: "Weighted average D-coefficient"
  combined_uncertainty:
    type: "number"
    description: "Uncertainty of the weighted average"
  p_value_heterogeneity:
    type: "number"
    minimum: 0
    maximum: 1
    description: "P-value from Cochran's Q test"
  d_upper_bound_95:
    type: "number"
    description: "95% confidence interval upper bound on |D|"
  sensitivity_limit:
    type: "number"
    description: "Standard error of the weighted mean"
  pdg_limit_2024:
    type: "number"
    description: "2024 PDG Review limit for comparison"
  comparison_status:
    type: "string"
    enum:
      - "tighter"
      - "looser"
      - "inconclusive"
      - "no_benchmark"
    description: "Comparison status against PDG limits"
required:
  - nucleus_id
  - weighted_average
  - combined_uncertainty
  - p_value_heterogeneity
  - d_upper_bound_95
  - sensitivity_limit
  - comparison_status


## projects/PROJ-400-can-publicly-available-data-reveal-subtl/specs/001-can-publicly-available-data-reveal-subtl/contracts/raw_observable.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: "object"
title: "RawObservable"
description: "Schema for raw momentum/polarization data (REJECTED). This schema is retained for historical reference. The 'Cross-Modal Fusion' method requiring raw event-level data is physically invalid for this project's goals. The active pipeline uses D-coefficients directly."
required:
  - value
  - uncertainty
  - modality_type
  - source_experiment
  - reference_id
  - data_granularity
  - covariance_available
properties:
  value:
    type: "number"
    description: "The measured quantity (momentum or asymmetry)."
  uncertainty:
    type: "number"
    minimum: 0
    description: "Standard error of the measurement."
  modality_type:
    type: "string"
    enum:
      - "momentum_spectrum"
      - "polarization_asymmetry"
    description: "Type of observable."
  source_experiment:
    type: "string"
    description: "Citation or ID of the experiment."
  reference_id:
    type: "string"
    description: "ENSDF entry ID."
  data_granularity:
    type: "string"
    enum:
      - "event_level"
      - "binned_granular"
      - "binned_aggregate"
    description: "Granularity of the data."
  covariance_available:
    type: "boolean"
    description: "True if covariance matrix is provided."
  nucleus_name:
    type: "string"
    description: "Name of the nucleus (e.g., 6He)."
additionalProperties: false