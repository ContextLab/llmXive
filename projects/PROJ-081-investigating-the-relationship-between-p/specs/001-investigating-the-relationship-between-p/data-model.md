# Data Model: Investigating the Relationship Between Plant Secondary Metabolite Profiles and Herbivore Resistance

## Core Entities

| Entity | Description | Key Attributes (type) |
|--------|-------------|-----------------------|
| **PlantSpecies** | Distinct plant taxon used in the analysis. | `species_id: str` (unique), `species_name: str`, `family: str` |
| **MetaboliteProfile** | Concentrations of four metabolite classes for a given species, with optional absence indicator. | `alkaloids: float`, `terpenes: float`, `phenolics: float`, `benzoxazinoids: float`, `absence_indicator: dict` (optional; e.g., `{"alkaloids": "documented_absent"}`) |
| **HerbivoryScore** | Quantitative measure of herbivore damage for the species. | `herbivory_score: float`, `measurement_method: str` |
| **AnalysisResult** | Container for any statistical output (correlation, regression, importance, power analysis). Wraps all result artifacts in a consistent schema. | `result_type: str` (enum: "correlation", "ols", "pgls", "mixed_effects", "rf", "sensitivity", "power_analysis"), `payload: dict` (free‑form JSON with result-specific fields), `timestamp: datetime` |

## Processed DataFrame Schema (used after Phase 2)

| Column | Description | dtype |
|--------|-------------|-------|
| `species_id` | Stable identifier (e.g., NCBI Taxonomy ID) | `string` |
| `species_name` | Common / scientific name | `string` |
| `family` | Plant family | `string` |
| `alkaloids` | Z‑scored concentration (0 if documented biological absence; missing data excluded) | `float64` |
| `terpenes` | Z‑scored concentration (0 if documented biological absence; missing data excluded) | `float64` |
| `phenolics` | Z‑scored concentration (0 if documented biological absence; missing data excluded) | `float64` |
| `benzoxazinoids` | Z‑scored concentration (0 if documented biological absence; missing data excluded) | `float64` |
| `herbivory_score` | Normalized herbivory index (post‑IQR capping) | `float64` |
| `absence_indicator` (optional) | JSON dict documenting which metabolite classes are documented as biologically absent (vs. missing data); e.g., `{"alkaloids": "documented_absent"}` | `string` (JSON) |

All rows must have **no missing values** in required columns (species_id, family, metabolite concentrations, herbivory_score) after preprocessing (FR‑002, FR‑007).  

**Note on zero-imputation**: A zero value in a metabolite concentration column indicates **documented biological absence** (recorded in `absence_indicator`), NOT missing data. Missing data are excluded from the dataset.

## Model Output Structures (all conform to AnalysisResult)

### 1. CorrelationResult (`result_type="correlation"`):
```json
{
  "result_type": "correlation",
  "payload": {
    "matrix": { "alkaloids": { "terpenes": 0.25, ... }, ... },
    "p_values": { ... },
    "q_values": { ... },
    "significant_negative_classes": ["alkaloids", "phenolics"],
    "method": "Pearson",
    "fdr_method": "Benjamini-Hochberg"
  },
  "timestamp": "2026-10-19T14:30:00Z"
}
```

### 2. OLSResult (`result_type="ols"`):
```json
{
  "result_type": "ols",
  "payload": {
    "coefficients": { "alkaloids": 0.15, "terpenes": -0.08, ... },
    "p_values": { "alkaloids": 0.02, ... },
    "q_values": { "alkaloids": 0.05, ... },
    "r2": 0.42,
    "adj_r2": 0.38,
    "rmse": 0.89,
    "vif": { "alkaloids": 2.1, "terpenes": 1.8, ... },
    "family_effect": { "coefficient": 0.05, "p_value": 0.15 },
    "train_n": 40,
    "test_n": 10,
    "fdr_method": "Benjamini-Hochberg"
  },
  "timestamp": "2026-10-19T14:35:00Z"
}
```

### 3. PGLSResult (`result_type="pgls"`):
```json
{
  "result_type": "pgls",
  "payload": {
    "coefficients": { "alkaloids": 0.12, ... },
    "p_values": { ... },
    "q_values": { ... },
    "r2": 0.38,
    "adj_r2": 0.34,
    "rmse": 0.92,
    "phylogeny_source": "Open Tree of Life",
    "species_matched": 48,
    "species_unmatched": 2,
    "lrt_statistic": 3.5,
    "lrt_p_value": 0.03,
    "lrt_interpretation": "PGLS significantly improves fit vs OLS (p < 0.05)",
    "train_n": 40,
    "test_n": 10,
    "fdr_method": "Benjamini-Hochberg"
  },
  "timestamp": "2026-10-19T14:40:00Z"
}
```

### 4. MixedEffectsResult (`result_type="mixed_effects"`):
```json
{
  "result_type": "mixed_effects",
  "payload": {
    "fixed_effects": { "alkaloids": 0.14, "terpenes": -0.07, ... },
    "fixed_p_values": { ... },
    "fixed_q_values": { ... },
    "random_intercept_std": 0.35,
    "r2_marginal": 0.40,
    "r2_conditional": 0.52,
    "rmse": 0.88,
    "train_n": 40,
    "test_n": 10,
    "fdr_method": "Benjamini-Hochberg"
  },
  "timestamp": "2026-10-19T14:45:00Z"
}
```

### 5. RFResult (`result_type="rf"`):
```json
{
  "result_type": "rf",
  "payload": {
    "feature_importance": [
      { "metabolite": "alkaloids", "importance": 0.35, "p_value": 0.01, "q_value": 0.025 },
      { "metabolite": "phenolics", "importance": 0.28, "p_value": 0.03, "q_value": 0.05 },
      ...
    ],
    "cv_r2": 0.39,
    "cv_adj_r2": 0.35,
    "cv_rmse": 0.91,
    "test_r2": 0.41,
    "test_adj_r2": 0.37,
    "test_rmse": 0.88,
    "train_n": 40,
    "test_n": 10,
    "permutation_method": "sklearn.inspection.permutation_importance",
    "n_repeats": 100,
    "fdr_method": "Benjamini-Hochberg"
  },
  "timestamp": "2026-10-19T14:50:00Z"
}
```

### 6. SensitivityResult (`result_type="sensitivity"`):
```json
{
  "result_type": "sensitivity",
  "payload": {
    "p_threshold_sweep": {
      "0.01": { "n_significant_classes": 2 },
      "0.02": { "n_significant_classes": 3 },
      ...
      "0.10": { "n_significant_classes": 4 }
    },
    "outlier_cap_variation": {
      "minus_10_percent": { "ols_r2": 0.40, "rf_r2": 0.38 },
      "baseline": { "ols_r2": 0.42, "rf_r2": 0.41 },
      "plus_10_percent": { "ols_r2": 0.43, "rf_r2": 0.42 }
    },
    "raw_vs_standardized": {
      "standardized_biomarker_ranking": ["alkaloids", "phenolics", "terpenes"],
      "raw_biomarker_ranking": ["alkaloids", "terpenes", "phenolics"],
      "ranking_agreement": "high (top 2 consistent)"
    }
  },
  "timestamp": "2026-10-19T14:55:00Z"
}
```

### 7. PowerAnalysisResult (`result_type="power_analysis"`):
```json
{
  "result_type": "power_analysis",
  "payload": {
    "observed_n": 50,
    "phylogenetic_lambda": 0.7,
    "effective_n": 35,
    "effect_size_target": 0.3,
    "alpha_per_test": 0.0125,
    "power_ols": 0.65,
    "power_pgls": 0.55,
    "power_rf": 0.60,
    "under_power_flag": false,
    "interpretation": "Adequate power for hypothesis-generating research; modest power for confirmatory claims."
  },
  "timestamp": "2026-10-19T15:00:00Z"
}
```

All result JSONs conform to the `AnalysisResult` schema defined in `model_output.schema.yaml`.

---