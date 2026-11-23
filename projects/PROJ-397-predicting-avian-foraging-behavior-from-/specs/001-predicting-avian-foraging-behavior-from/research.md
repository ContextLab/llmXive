# Research: Predicting Avian Foraging Guilds from Public eBird Data and Land Cover Maps

## Scientific Context

The study investigates whether land cover composition at the scale of a 100m buffer can predict a bird species' foraging guild (ground, canopy, aerial). This addresses the ecological hypothesis that habitat structure drives foraging strategy. The analysis is observational; findings will be framed as associations between land cover profiles and species-level guilds, not causal claims about individual behavior.

## Dataset Strategy

### Verified Datasets

The following datasets are used exclusively from the `# Verified datasets` block provided in the project context.

| Dataset | Source URL | Usage | Notes |
|:--- |:--- |:--- |:--- |
| **EBD (eBird Basic Dataset)** | ` | Source of occurrence records. | Contains `common_name`, `latitude`, `longitude`. Mapped to internal `species_id`. *Note: This is a pre-filtered 'basic' checklist split.* |
| **NLCD 2021 Land Cover** | ` | Source of land cover rasters for buffer extraction. | Provides categorical land cover classes (Forest, Grassland, Wetland, Urban). *Note: Spec assumed NLCD 2019; 2021 is the verified available source.* |
| **Foraging Guilds** | "Birds of the World (Cornell Lab of Ornithology), accessed 2025-01-15" | Source of guild labels. | Used to map `species_code` to `foraging_guild`. *Note: Mapping is generated dynamically, not hardcoded.* |

### Data Acquisition & Preprocessing

1. **eBird Records**: Download the CSV from the verified HuggingFace URL. Map columns: `common_name` -> `species_id`, `latitude` -> `latitude`, `longitude` -> `longitude`.
2. **Dynamic Species Selection**:
 * Run `load_and_count.py` to count records per `species_code`.
 * Run `select_top_species.py` to filter the raw EBD to a subset of the most abundant species.
 * *Constraint*: This ensures the "top 25" is dynamic and reproducible, not hardcoded.
3. **Land Cover Raster**: Download the ZIP from the verified URL. Extract the GeoTIFF. Use `rasterio` to sample values at observation coordinates + 100m buffer.
4. **Buffer Validation**: `calculate_100m_buffers.py` must explicitly validate that the buffer radius parameter is 100m before processing. If not, raise an error (FR-002 compliance). **Output**: A validation log/report confirming the 100m radius was used.
5. **Foraging Guild Mapping**:
 * The `generate_guild_mapping.py` script will dynamically load the top 25 species list and map them to guilds using the "Birds of the World" source.
 * *Constraint*: No hardcoded dictionary of species names. The mapping is derived from the dynamic species list.
6. **Filtering**: Retain only species with ≥50 observations (FR-003).

## Statistical Methodology

### Model: Regularized Logistic Regression (L2)
- **Input**: Land cover proportions (Forest, Grassland, Wetland, Urban, Other) transformed via Centered Log-Ratio (CLR).
- **Target**: Foraging Guild (Ground, Canopy, Aerial).
- **Validation**: K-Fold Cross-Validation (k=5).
- **Metrics**: Balanced Accuracy (to handle class imbalance), Per-Class F1 Score.
- **Rationale**: With N=25 species, Random Forest is prone to overfitting. Logistic Regression with L2 regularization is statistically sound for low-N, high-dimension problems. *Note: This deviates from Spec FR-004 (Random Forest) due to statistical unsoundness of RF on N=25.*

### Compositional Data Analysis (CoDa)
- **Problem**: Land cover classes sum to 1.0. This induces perfect multicollinearity and spurious correlations in raw proportions.
- **Solution**: Apply Centered Log-Ratio (CLR) transformation to the land cover proportions before model training.
 - $clr(x_i) = \ln(x_i / g(x))$ where $g(x)$ is the geometric mean of the composition.
 - This handles the sum-to-1 constraint and stabilizes feature importance interpretation.

### Stratified Permutation Test (FR-005, US-2, FR-008)
- **Problem**: Standard permutation shuffles labels randomly. Since guilds are static per species, shuffling within species is impossible. Global shuffling ignores species-specific habitat preferences.
- **Solution**: **Across-Species Permutation** on the **Aggregated Data**.
 1. Aggregate data to the species level (mean land cover per species, **after** CLR transformation).
 2. Shuffle the *species-level* guild labels among species.
 3. Train the Logistic Regression model on this permuted species-level data.
 4. Repeat the procedure multiple times to generate a null distribution of Balanced Accuracy.
 5. Compare observed model accuracy against this null distribution.
 6. **Hypothesis**: If observed accuracy > 95th percentile of null, p < 0.05, indicating land cover predicts guild assignment better than chance *at the species level*.
 7. *Clarification*: This test validates the **association** between land cover and guild, treating species as the unit of analysis. It does not claim to "control for species identity" in a causal sense, but rather tests if the pattern holds across the species population. The phrasing "independent of species identity" is scientifically imprecise; the correct claim is that land cover predicts guild assignment at the species level better than chance.

### Statistical Rigor & Limitations
- **Multiple Comparison Correction**: Not applicable for the primary hypothesis (one test: land cover vs. guild). Feature importance rankings are descriptive.
- **Sample Size/Power**: The sample size is determined by the number of species (top 25, filtered to ≥50 obs). With a limited number of species, power is limited.
 - **Power Limitation**: N=25 is low for robust statistical inference. The permutation test is used because it does not rely on parametric assumptions, but the wide confidence intervals must be acknowledged.
- **Causal Inference**: The study is observational. Claims are limited to association.
- **Selection Bias**: The "top 25" filter (FR-003) selects the most common, widespread species. Results may not generalize to rare species. This is a limitation of the convenience sampling.
- **Dataset-Variable Fit**: The verified EBD dataset contains coordinates and species codes. The verified NLCD dataset contains land cover. The join is feasible. The guild label is mapped dynamically.

## Compute Feasibility

- **CPU-First**: All methods (CLR, Logistic Regression, buffer extraction, permutation) are CPU-tractable.
- **Memory**: Streaming the EBD CSV and processing NLCD in chunks ensures RAM usage stays < 7 GB.
- **Runtime**: Target < 145 minutes.
 - Data download: [deferred].
 - Buffer extraction (large-scale point sampling): [deferred] (optimized with vectorized raster sampling).
 - Model training + a large number of permutations: ~60 mins (Logistic Regression is faster than RF).
 - Visualization: < 10 mins.
- **GPU Escape Hatch**: Not required.

## Decision/Rationale

| Decision | Rationale |
|:--- |:--- |
| **Across-Species Permutation** | "Within-species" shuffling is impossible (static labels). Across-species shuffling preserves the "species-level" nature of the guild label while testing the land cover signal. |
| **Top 25 Species Filter (Dynamic)** | Ensures statistical power (≥50 obs) and reduces computational load. Dynamic selection ensures reproducibility of the "top 25" set. |
| **CLR Transformation** | Handles the compositional nature of land cover data (sum-to-1) to prevent spurious correlations and stabilize feature importance. |
| **Logistic Regression (L2)** | Statistically sound for N=25. Random Forest would overfit. *Deviation from Spec FR-004.* |
| **NLCD 2021** | Verified available source. Spec assumption of 2019 is a gap; 2021 is used for feasibility. *Deviation from Spec Principle VI.* |
| **100m Buffer** | Mandated by FR-002. Sufficient to capture local habitat features relevant to foraging. |
