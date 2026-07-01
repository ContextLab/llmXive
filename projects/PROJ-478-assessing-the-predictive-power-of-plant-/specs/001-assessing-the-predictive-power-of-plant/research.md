# Research: Assessing the Predictive Power of Plant Functional Traits for Species Distribution Models

## 1. Research Question & Hypothesis

**Question**: Do functional traits (SLA, Seed Mass, Height) significantly improve the predictive performance of Species Distribution Models (SDMs) for Asteraceae species beyond climate‑only baselines when evaluated on held‑out species?

**Hypothesis**: Models incorporating functional traits will achieve a statistically significant higher mean AUC (≥ 0.02 improvement) compared to climate‑only models in a Leave‑One‑Species‑Out (LOSO) cross‑validation framework.

## 2. Dataset Strategy

| Dataset | Description | Source / URL | Access Method | Notes |
|:--- |:--- |:--- |:--- |:--- |
| **GBIF Occurrences** | Global, georeferenced occurrence records for all Asteraceae species (≥ 100 records/species). | GBIF API ` (taxonKey = family = Asteraceae) | `requests` with pagination | Query is global; no geographic restriction. |
| **WorldClim v2.1** | 19 bioclimatic variables, 1 km resolution. | WorldClim v2.1, release 2023‑08‑01 | `rasterio` download via official HTTP endpoint | Version and download date recorded for reproducibility. |
| **TRY Plant Trait** | Specific Leaf Area, Seed Mass, Plant Height. | TRY public subset, version 2022‑07 | `requests` to TRY API | Includes `source` metadata; values with `source` = “Handbook 2013” are flagged as verified. |

**Dataset Fit Verification**:
- **GBIF**: Provides latitude/longitude and taxon keys for Asteraceae; meets FR‑001.
- **WorldClim**: Supplies required 19 bioclim variables; meets FR‑002.
- **TRY**: Contains the three required traits; meets FR‑003 and FR‑010 (source verification). Missing traits trigger exclusion per FR‑006; unverified sources are flagged, not excluded.

## 3. Methodology

### 3.1 Data Preprocessing
1. **GBIF**: Download globally filtered by Asteraceae family; remove duplicate coordinates; apply spatial thinning (10 km default). If retained records fall below [deferred] of raw, iteratively reduce thinning distance by 1 km steps down to 1 km (fallback per FR‑001). Species that still fail the 80 % threshold are flagged as `insufficient_data` and omitted from modeling.
2. **Climate**: Extract the 19 WorldClim layers for the convex hull of cleaned occurrences; align raster stack to occurrence coordinates.
3. **Traits**: Retrieve SLA, Seed Mass, Height from TRY. Verify `trait_source`; set `is_verified = true` only if source matches “Handbook 2013”. Flag unverified traits (`is_verified = false`) but retain them. Species missing any trait receive `exclusion_reason = "missing_trait"` and are excluded from the trait‑augmented branch (FR‑006).

### 3.2 Modeling Strategy (LOSO)
- **Design**: Leave‑One‑Species‑Out (LOSO) cross‑validation across all species with complete trait data.
- **Training**: For each fold, train two Random Forest classifiers (CPU‑only, `scikit‑learn`):
 - **Climate‑only**: A set of climate predictors.
 - **Climate + traits**: climate + 3 trait predictors, using the *known* trait values of the held‑out species (no imputation, per FR‑004).
- **Hyperparameters**: `n_estimators=100`, `max_depth=10`, `random_state=42`; inner 5‑fold CV for tuning.
- **Outputs**: Per‑species AUC and TSS on the held‑out species; VIF scores for the full predictor set; `collinearity_flag` if any VIF > 5 (FR‑011).

### 3.3 Statistical Analysis
1. **Paired t‑test**: Conduct a paired two‑sided t‑test comparing AUC (and separately TSS) between climate‑only and climate + traits models across all LOSO folds.
2. **Bonferroni correction**: Apply family‑wise correction for the two metrics (FR‑008).
3. **Effect size**: Report Cohen’s d.
4. **Sensitivity sweep**: Evaluate ΔAUC thresholds {0.01, 0.02, 0.05}; produce a table showing the proportion of species with ΔAUC > threshold; success if ≥ 67 % of thresholds show improvement (FR‑009).

### 3.4 Decision Rationale
- The spec (FR‑004) explicitly requires using *known* trait values for the held‑out species; therefore the LOSO design tests whether traits are **associatively** predictive when they are available, not whether they can be inferred for completely novel species. This aligns with the contractual requirement while remaining methodologically sound for the intended analysis.
- Paired t‑tests are mandated by FR‑005 and FR‑008; LMM is unnecessary and would violate the spec, so the analysis follows the paired t‑test framework.

## 4. Compute Feasibility & Constraints
- **Hardware**: 2 CPU cores, 7 GB RAM, ≤ 6 h runtime on GitHub Actions.
- **Memory**: Species processed sequentially; each raster stack ≤ 200 MB.
- **Runtime**: Estimated ≤ 4 h for 50 species with the chosen RF parameters.

## 5. Decision Rationale (re‑iterated)
- **Known traits**: Required by FR‑004; the analysis therefore assesses the *additional associative information* traits provide when they are known.
- **Statistical test**: Paired t‑test with Bonferroni correction satisfies FR‑005, FR‑008, and avoids unnecessary complexity.
