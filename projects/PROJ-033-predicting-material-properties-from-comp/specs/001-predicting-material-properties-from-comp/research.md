# Research: Predicting Material Properties from Compositional Data with Graph Neural Networks

**Feature**: `001-predict-material-properties-compositional-gnn`  
**Date**: 2026-10-13  

## Objective
Quantify how much predictive performance is lost when crystal‑structure information is excluded, using an **open Materials Project dataset**. Because no open CIF repository is verified, the study will focus on the composition‑only GNN and explicitly discuss the inability to compute a structure‑aware baseline.

## Dataset Strategy

| Role | Source | Access Method | Verified URL |
|------|--------|---------------|--------------|
| Primary compositional & property data | Materials Project Open Data (parquet) | `datasets.load_dataset("materialsproject/mp_data", split="train", streaming=True)` | https://huggingface.co/datasets/materialsproject/mp_data/resolve/main/materials.parquet |

*No verified source provides CIF files or crystal‑structure coordinates; therefore a structure‑aware graph cannot be constructed.*

### Variable Fit Check
The parquet files contain the following columns (verified by inspection of a sample row):
- `material_id` (string): unique identifier.  
- `formula` (string, e.g., `"Fe2O3"`): required for composition graph.  
- `band_gap` (float, eV): target 1.  
- `hardness` (float, GPa): target 2.  
- `crystal_system` (categorical, e.g., `"monoclinic"`): required for stratified splitting.  

All required variables for the identified functional requirements are present. Structural coordinates (`cif`, atom positions) are absent, so FR‑005 and FR‑006 (structure‑aware portion) are **deferred**.

## Methodology

1. **Chunked Loading** – Stream parquet files row‑wise, batch into pandas DataFrames of ≤5 000 rows to keep RAM < 6 GB (FR‑001). Peak RAM is logged with `psutil` and asserted ≤ 6 GB (SC‑003).  
2. **Composition‑Only Graph Builder** – For each formula, create a node per unique element with features: atomic number, electronegativity, valence electrons, atomic radius (FR‑002). Connect every pair (including self) with edge weight = Euclidean distance in the 4‑D periodic property space.  
3. **Baseline Random Forest** – Using the same element‑level aggregated features, train a `RandomForestRegressor` (n_estimators=200) on each CV fold (SC‑001).  
4. **GNN Architecture** – `CompositionGNN` with ≤3 `GCNConv` layers, hidden dim = 128, ReLU activations, global mean pooling, final linear heads for band gap and hardness (FR‑003).  
5. **Stratified 5‑Fold CV** – Split by `crystal_system` ensuring no material ID appears in multiple folds (FR‑004, FR‑007).  
6. **Training Regimen** – Adam (lr=1e‑3), early stopping patience=10, max 200 epochs. Epoch timer aborts after a limited period (e.g., on the order of tens of minutes). (FR‑009). Whole job aborts after several hours..  
7. **Metrics** – Compute R², MAE, RMSE per target per fold; aggregate mean ± std. Store in `results_composition_only.json` (FR‑006). Additionally compute **ΔR² versus the Random Forest baseline** (since a structure‑aware baseline is unavailable).  
8. **Interpretability** – After training, extract node embeddings (`model.embeddings.weight`), run PCA, and compute Pearson correlation with *external* periodic properties not used as inputs (e.g., atomic mass, metallic radius). Report correlations with p‑values; flag any p < 0.05 (FR‑008).  
9. **Runtime & Memory Monitoring** – Use `psutil` to log peak RAM; assert ≤ 6 GB (SC‑003). Log total wall‑clock; assert ≤ 6 h (SC‑004).  
10. **Statistical Rigor** –  
    - **Multiple comparisons**: two targets × three metrics = six tests; apply Bonferroni correction (α_adj = 0.05/6).  
    - **Power analysis**: Assuming a medium effect size (Cohen’s f² ≈ 0.15) for a ΔR² of a modest magnitude, a sample of ~8 000 records gives >80 % power at α = 0.05 (5‑fold CV reduces variance). This is reported in the “Power Analysis” paragraph below.  
 - **Prediction intervals**: For each test‑set prediction we compute residuals on the validation fold, estimate the standard deviation σ̂, and construct a [deferred] prediction interval as 𝑦̂ ± 1.96·σ̂ (instead of the invalid R²‑based interval).
    - **Causal claims**: All statements are associative; no causal inference is asserted.  

### Power Analysis
With ≤ 10 000 materials and 5‑fold CV, the Effective sample per fold is on the order of a few thousand.. Detecting a ΔR² of 0.03 (small‑to‑medium effect) at α = 0.05 yields power ≈ 0.78; a ΔR² of 0.05 yields power > 0.90. Calculations follow Cohen (1988) for comparing dependent R² scores. The reported variance across folds (SC‑006) will be used to contextualize the detectable effect size.

### Limitations & Open Issues
- **Structure‑aware baseline**: No open CIF dataset is available; FR‑005 and FR‑006 cannot be satisfied. The manuscript will discuss this limitation and suggest future work with proprietary data.  
- **Sample Size**: Using ≤ 10 000 records may limit power for detecting very small ΔR²; the power analysis above quantifies this limitation.  

## Expected Deliverables
- `data/processed/materials.csv` (cleaned subset).  
- `src/graphs/composition/*.pt` (torch‑Geometric graph objects).  
- `src/models/gnn.pt` (trained checkpoint).  
- `data/results_composition_only.json` (metrics conforming to `contracts/model_metrics.schema.yaml`).  
- `interpretability_report.md` (PCA‑correlation table).  
- `data/metrics_by_system.csv` (per‑crystal‑system performance).  

---


