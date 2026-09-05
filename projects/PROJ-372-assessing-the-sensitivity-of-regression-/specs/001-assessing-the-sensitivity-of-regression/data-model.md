# Data Model: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

## Overview
This document defines the data structures used for ingestion, profiling, resampling, and stratified analysis. All data is serialized to JSON/CSV for the `artifacts/` directory to ensure reproducibility and single-source-of-truth compliance.

## 1. SubsetProfile

**Purpose**: Stores the OLS assumption violation metrics for a *single subset*.
**Location**: `artifacts/profiles/{dataset}_{tier}_{subset_id}.json` (Intermediate) and `artifacts/profiles/aggregated_profiles.json` (Aggregated).

```json
{
  "dataset_name": "california_housing",
  "tier": 10,
  "subset_id": 1,
  "n_rows": 2064,
  "condition_number": 14.2,
  "breusch_pagan_p_value": 0.08,
  "max_cooks_distance": 0.12,
  "violation_severity": "Medium",
  "timestamp": "2026-08-15T12:00:00Z"
}
```

**Fields**:
- `dataset_name`: Identifier.
- `tier`: Sample size tier (10, 25, 50, 75, 90).
- `subset_id`: Unique ID for the subset.
- `condition_number`: Float.
- `breusch_pagan_p_value`: Float.
- `max_cooks_distance`: Float.
- `violation_severity`: Enum ["Low", "Medium", "High"] based on BP p-value.

## 2. StabilityResult

**Purpose**: Stores the empirical standard deviation of coefficients for a specific tier.
**Location**: `artifacts/stability/coefficient_sd.json` (Aggregated).

```json
{
  "dataset": "california_housing",
  "tier": 10,
  "n_subsets": 200,
  "coefficient_sd": {
    "MedInc": 0.004,
    "HouseAge": 0.002,
    "AveRooms": 0.008
  },
  "convergence_check": {
    "se_of_sd": 0.0002,
    "ratio": 0.065,
    "passed": true
  }
}
```

**Fields**:
- `coefficient_sd`: Map of predictor name to SD of that coefficient across 200 subsets.
- `convergence_check`: Object containing the calculated SE of SD and the ratio (SE/SD). `passed` is true if ratio < 0.07. If false, this tier is excluded from final analysis.

## 3. StratifiedAnalysisResult

**Purpose**: Stores the results of the binning and non-parametric tests.
**Location**: `artifacts/stratified_analysis/results.json`

```json
{
  "dataset": "california_housing",
  "tier": 10,
  "predictor": "MedInc",
  "bins": [
    {
      "severity": "Low",
      "count": 120,
      "mean_sd": 0.003,
      "median_sd": 0.0029
    },
    {
      "severity": "Medium",
      "count": 50,
      "mean_sd": 0.005,
      "median_sd": 0.0048
    },
    {
      "severity": "High",
      "count": 30,
      "mean_sd": 0.012,
      "median_sd": 0.011
    }
  ],
  "test_statistic": {
    "method": "Kruskal-Wallis",
    "h_statistic": 15.4,
    "p_value": 0.0004
  },
  "interpretation": "Significant difference in stability across severity bins (p < 0.05)."
}
```

**Fields**:
- `bins`: List of objects containing count and stability stats per severity bin.
- `test_statistic`: Result of the non-parametric test comparing bins.

## 4. ConvergenceLog

**Purpose**: Text log of convergence checks.
**Location**: `artifacts/convergence.log`

```text
2026-08-15 12:05:00 | california_housing | tier_10 | SE/SD: 0.065 | PASSED
2026-08-15 12:05:01 | california_housing | tier_25 | SE/SD: 0.072 | FAILED (Excluded)
2026-08-15 12:05:02 | delaney | tier_10 | SE/SD: 0.060 | PASSED
```

**Format**: `timestamp | dataset | tier | SE/SD value | status`