# Data Model: Investigating the Relationship Between Plant Secondary Metabolite Profiles and Herbivore Resistance

## Core Entities

| Entity | Description | Key Attributes (type) |
|--------|-------------|-----------------------|
| **PlantSpecies** | Distinct plant taxon used in the analysis. | `species_id: str` (unique), `species_name: str`, `family: str` |
| **MetaboliteProfile** | Concentrations of four metabolite classes for a given species, with optional absence indicator. | `alkaloids: float`, `terpenes: float`, `phenolics: float`, `benzoxazinoids: float`, `absence_indicator: dict` (optional) |
| **HerbivoryScore** | Quantitative measure of herbivore damage for the species. | `herbivory_score: float`, `measurement_method: str` |
| **AnalysisResult** | Wrapper for any statistical output (correlation, regression, importance, power analysis). | `result_type: str` (enum), `payload: dict`, `timestamp: datetime` |

## Processed DataFrame Schema (output of Phase 2)

| Column | Description | dtype |
|--------|-------------|-------|
| `species_id` | Stable taxonomic identifier (e.g., NCBI Taxonomy ID) | `string` |
| `species_name` | Scientific or common name | `string` |
| `family` | Plant family | `string` |
| `alkaloids` | Z‑scored concentration; zero **only** for true missing values after standardization (imputed on raw scale before Z‑scoring). | `float64` |
| `terpenes` | Z‑scored concentration; zero **only** for true missing values after standardization. | `float64` |
| `phenolics` | Z‑scored concentration; zero **only** for true missing values after standardization. | `float64` |
| `benzoxazinoids` | Z‑scored concentration; zero **only** for true missing values after standardization. | `float64` |
| `herbivory_score` | Normalized herbivory index after IQR capping. | `float64` |
| `absence_indicator` (optional) | JSON dict documenting which metabolite classes are documented as biologically absent (vs. missing data); e.g., `{"alkaloids":"documented_absent"}`. Rows with a class marked absent are **excluded from imputation and standardization for that class**. | `string` (JSON) |

All rows must have **no missing values** in the required columns after preprocessing (FR‑002, FR‑007). Zero values now denote imputed missing data **after** standardization; documented biological absences are captured separately in `absence_indicator` to avoid conflating with missing data.

## Model Output Structures (all conform to `AnalysisResult` schema defined in `contracts/model_output.schema.yaml`)

### 1. CorrelationResult (`result_type="correlation"`)

```json
{
  "result_type": "correlation",
  "payload": {
    "class_matrix": { "alkaloids": { "herbivory_score": "negative", "...": "…" }, "...": "…" },
    "compound_matrix": { "compound_A": { "herbivory_score": "negative (indicating reduced herbivory)", "...": "…" }, "...": "…" },
    "p_values": { "alkaloids": "statistically significant", "...": "…" },
    "q_values": { "alkaloids": "a low proportion", "...": "…" },
    "significant_negative_classes": ["alkaloids","phenolics"],
    "method": "Pearson",
    "fdr_method": "Benjamini-Hochberg"
  },
  "timestamp": "2026-10-26T14:30:00Z"
}
```

### 2. OLSResult (`result_type="ols"`)

```json
{
  "result_type": "ols",
  "payload": {
    "coefficients": { "alkaloids": "positive association", "terpenes": "negative association", "...": "…" },
    "p_values": { "alkaloids": "statistically significant", "...": "…" },
    "q_values": { "alkaloids": 0.05, "...": "…" },
    "r2": "a modest proportion of variance explained",
    "adj_r2": "moderate explanatory power",
    "rmse": "a relatively low error",
    "vif": { "alkaloids": "elevated", "...": "…" },
    "family_effect": { "coefficient": 0.05, "p_value": 0.15 },
    "additional_covariates": { "plant_size": { "coefficient": 0.03, "p_value": 0.22 } },
    "train_n": "a suitable number of training instances to be determined during the implementation phase",
    "test_n": "a modest sample size",
    "fdr_method": "Benjamini-Hochberg"
  },
  "timestamp": "2026-10-26T14:35:00Z"
}
```

### 3. PGLSResult (`result_type="pgls"`)

```json
{
  "result_type": "pgls",
  "payload": {
    "coefficients": { "alkaloids": "small positive effect", "...": "…" },
    "p_values": { "alkaloids": "statistically significant (p < 0.05)", "...": "…" },
    "q_values": { "alkaloids": 0.06, "...": "…" },
    "r2": "moderate explanatory power",
    "adj_r2": "moderate explanatory power",
    "rmse": "low (indicative of good model performance)",
    "phylogeny_source": "Open Tree of Life",
    "species_matched": "multiple species",
    "species_unmatched": "non-zero",
    "lrt_statistic": "value indicating significant evidence",
    "lrt_p_value": "significant (below conventional threshold)",
    "lrt_interpretation": "PGLS significantly improves fit vs OLS (p < 0.05)",
    "train_n": <appropriate training set size>,
    "test_n": "a suitable sample size",
    "fdr_method": "Benjamini-Hochberg"
  },
  "timestamp": "2026-10-26T14:40:00Z"
}
```

### 4. MixedEffectsResult (`result_type="mixed_effects"`)

```json
{
  "result_type": "mixed_effects",
  "payload": {
    "fixed_effects": { "alkaloids": "a small positive effect", "...": "…" },
    "fixed_p_values": { "alkaloids": "a small significance threshold", "...": "…" },
    "fixed_q_values": { "alkaloids": 0.07, "...": "…" },
    "random_intercept_std": "to be estimated from the data",
    "r2_marginal": "moderate",
    "r2_conditional": "a moderate level of conditional R‑squared",
    "rmse": (low),
    "train_n": "a suitable training set size",
    "test_n": "a suitable sample size",
    "fdr_method": "Benjamini-Hochberg"
  },
  "timestamp": "2026-10-26T14:45:00Z"
}
```

### 5. RFResult (`result_type="rf"`)

```json
{
  "result_type": "rf",
  "payload": {
    "feature_importance": [
      { "metabolite": "alkaloids", "importance": "moderate" },
      { "metabolite": "phenolics", "importance": "moderate" },
      { "metabolite": "terpenes", "importance": "moderate" }
    ],
    "cv_r2": "moderate",
    "cv_adj_r2": "moderate adjusted R-squared indicating reasonable model fit",
    "cv_rmse": "a low value indicating good predictive performance",
    "test_r2": "moderate predictive performance",
    "test_adj_r2": "moderate adjusted R-squared",
    "test_rmse": "within an acceptable range",
    "train_n": 40,
    "test_n": 10,
    "permutation_method": "sklearn.inspection.permutation_importance",
    "n_repeats": 100,
    "fdr_method": "Benjamini-Hochberg"
  },
  "timestamp": "2026-10-26T14:50:00Z"
}
```

### 6. SensitivityResult (`result_type="sensitivity"`)

```json
{
  "result_type": "sensitivity",
  "payload": {
    "p_threshold_sweep": {
      "0.01": { "n_significant_classes": "a limited number of classes" },
      "0.02": { "n_significant_classes": "a few" },
      "...": "…",
      "0.10": { "n_significant_classes": "several" }
    },
    "outlier_cap_variation": {
      "minus_10_percent": { "ols_r2": 0.40, "rf_r2": "comparable to OLS performance" },
      "baseline": { "ols_r2": 0.42, "rf_r2": "comparable to OLS performance" },
      "plus_10_percent": { "ols_r2": "moderate explanatory power", "rf_r2": "comparable explanatory power" }
    },
    "raw_vs_standardized": {
      "standardized_biomarker_ranking": ["alkaloids","phenolics","terpenes"],
      "raw_biomarker_ranking": ["alkaloids","terpenes","phenolics"],
      "ranking_agreement": "high (top 2 consistent)"
    }
  },
  "timestamp": "2026-10-26T14:55:00Z"
}
```

### 7. PowerAnalysisResult (`result_type="power_analysis"`)

```json
{
  "result_type": "power_analysis",
  "payload": {
    "observed_n": "a suitable sample size",
    "phylogenetic_lambda": "a moderate value indicating an intermediate level of phylogenetic signal",
    "effective_n": "adequate",
    "effect_size_target": "a modest effect size (r≈0.2, conservative)",
    "alpha_per_test": "0.05 divided by total number of compound‑level tests",
    "power_ols": "moderate effect",
    "power_pgls": "a moderate level of statistical power",
    "power_rf": "moderate level",
    "under_power_flag": false,
    "interpretation": "Adequate power for hypothesis‑generating research; modest power for confirmatory claims."
  },
  "timestamp": "2026-10-26T15:00:00Z"
}
```

All JSON results conform to the `AnalysisResult` schema defined in `contracts/model_output.schema.yaml`.


