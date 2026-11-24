# Data Model: Predicting the Diffusion Coefficient of Hydrogen in Metals from Compositional and Microstructural Descriptors

## Core Entities

| Entity | Description | Key Fields |
|--------|-------------|------------|
| **MaterialSample** | One real observation from the input dataset. | `sample_id: string` (unique), `composition: array<string>`, **optional** `composition_fractions: array<number>` (same length as `composition`; if omitted, equal‑weighting is assumed), `processing_params: object<string, number>`, `temperature: float` (K, retained for record‑keeping **and used as a predictor for non‑linear models**), `diffusion_coefficient: float` (m²/s, harmonized) |
| **DescriptorSet** | Derived numeric features per sample. | `sample_id: string` (FK), `mean_electronegativity: float`, `atomic_radius_variance: float`, `free_volume_proxy: float`, `grain_boundary_density: float`, `inv_temperature: float` (1/K, **used only by the linear baseline**), `log10_D: float` |
| **ModelPerformance** | Records for one model on one outer fold. | `model_type: enum[xgboost, random_forest, linear]`, `outer_fold: int` (1–5), `rmse_log10: float`, `r2_log10: float`, `hyperparameters: object<string, number>` |
| **InteractionTerm** | Pairwise SHAP interaction result. | `descriptor_a: string`, `descriptor_b: string`, `mean_abs_shap_interaction: float`, `ci_lower: float`, `ci_upper: float`, `delta_r2_ablation: float` (ΔR² when this interaction is removed from the model on the hold‑out) |
| **BootstrapResult** | One bootstrap iteration summary. | `iteration: int`, `feature_importances: object<string, number>`, `outer_r2: float` |
| **ExternalValidation** | Hold‑out evaluation of the best model. | `rmse_log10: float`, `r2_log10: float`, `interaction_variance_share: float` (primary SC‑006 metric: proportion of explained variance attributable to pairwise interactions, computed via **permutation‑based ΔR² share** on an independent hold‑out set) |
| **PowerAnalysis** | Post‑hoc power analysis record for interaction effect detection (FR‑009). | `effect_size_f2: float`, `min_detectable_f2: float`, `alpha: float`, `n_samples: int`, `ci_width_top_feature: float` |

## Relationships

- `DescriptorSet.sample_id` → `MaterialSample.sample_id` (one‑to‑one).  
- `ModelPerformance` rows are keyed by (model_type, outer_fold).  
- `InteractionTerm` derives from the best non‑linear model; CIs derive from `BootstrapResult` iterations.  
- `ExternalValidation` and `PowerAnalysis` each reference the single best‑model run.

## Provenance Rules (Constitution III, VII)

- Raw input is checksummed and never modified in place; each derivation writes a new file and records its source hash.  
- `log10_D` / `diffusion_coefficient` never enter imputation or scaling.  
- Every derived file records its generating code block.  
- **Collinearity handling**: before model training, a correlation matrix and VIF are computed; raw temperature is **retained only for non‑linear models** while the linear baseline uses only `inv_temperature` to avoid perfect collinearity. If any predictor VIF > 5, a warning is logged and reported in the results summary.  
- If `composition_fractions` is omitted, equal weighting is assumed for computing mean electronegativity and atomic‑radius variance, and this assumption is documented in the processing code.
