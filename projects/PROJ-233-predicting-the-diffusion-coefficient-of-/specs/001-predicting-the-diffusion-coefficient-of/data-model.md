# Data Model: Predicting the Diffusion Coefficient of Hydrogen in Metals

## Core Entities

| Entity | Description | Key Fields |
|--------|-------------|------------|
| **MaterialSample** | Raw observation from the diffusion dataset (or synthetic generator). | `sample_id: string` (unique), `composition: list<string>`, `processing_params: dict<string, float>`, `temperature: float` (K), `diffusion_coefficient: float` (m²/s) |
| **DescriptorSet** | Derived numeric features for a `MaterialSample`. | `sample_id: string` (FK), `mean_electronegativity: float`, `atomic_radius_variance: float`, `free_volume_proxy: float`, `grain_boundary_density: float`, `temperature: float`, `log10_D: float` |
| **ModelPerformance** | Metrics for a trained model on a given outer‑fold test set. | `model_type: enum[xgboost, random_forest, linear]`, `outer_fold: int`, `rmse_log10: float`, `r2_log10: float`, `hyperparameters: dict<string, any>` |
| **InteractionTerm** | Pairwise SHAP interaction result. | `descriptor_a: string`, `descriptor_b: string`, `mean_abs_shap_interaction: float`, `ci_lower: float`, `ci_upper: float`, `delta_r2_ablation: float` |
| **BootstrapResult** | One bootstrap iteration’s summary. | `iteration: int`, `feature_importances: dict<string, float>`, `outer_r2: float` |

## Relationships
- `DescriptorSet.sample_id` → `MaterialSample.sample_id` (one‑to‑one).  
- `ModelPerformance` is linked to a specific outer fold.  
- `InteractionTerm` is derived from the best performing non‑linear model (global).  
- `BootstrapResult` aggregates across all samples; each iteration is independent.

## Schema Contracts
- See `contracts/dataset.schema.yaml` (raw & derived tables).  
- See `contracts/model_performance.schema.yaml` (performance, interactions, and bootstrap results).

---