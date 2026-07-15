# Research: Predicting Insect Pollinator Networks from Floral Trait Data

## Dataset Strategy

This project relies on two primary data sources: the **Web of Life** database for bipartite interaction matrices and associated **Dryad** repositories or literature for floral trait metadata.

### Verified Datasets

| Dataset Name | Description | Verified Source / URL | Status |
|:--- |:--- |:--- |:--- |
| **Web of Life** | Global database of plant-pollinator interaction networks (bipartite matrices). | ` (Programmatic access via their API or direct CSV download links found in their "Data" section). | **Verified** |
| **Dryad (Floral Traits)** | Repository of supplementary data for ecological studies, often containing trait measurements (color, corolla depth, scent) linked to Web of Life networks. | ` (Search terms: "Web of Life traits", "pollinator traits"). Specific datasets must be mapped to ecosystem IDs. | **Verified** (Requires mapping to specific study IDs) |
| **Global Plant Trait Database (TRY)** | (Fallback) If Dryad lacks specific traits, TRY database may provide species-level trait averages. | ` (Requires registration, but public API exists for some data). | **Conditional** (May require registration) |

**Note**: The spec explicitly warns against using access-gated data (ADNI, HCP, etc.) unless an open substitute is named. The Web of Life and Dryad data are generally open access for research, but specific trait datasets may require citing the original authors. The implementation will prioritize direct download links from the Web of Life "Data" page or associated Dryad DOIs. If a specific ecosystem lacks trait data in these open sources, it will be skipped (per spec edge case handling).

### Data Availability & Feasibility

* **Open Access**: Web of Life provides CSVs directly. Dryad datasets are downloadable without credentials for research purposes.
* **Feasibility Check**: The plan targets ecosystems. Historical analysis suggests that while interaction matrices are abundant, *complete* trait metadata (color, scent, morphology) for all species in a network is rare.
* **Mitigation**: The pipeline is designed to handle missing data (imputation) and skip ecosystems where trait coverage is < 50% (or as defined by the "[deferred] missingness" flag in the spec). The "[deferred] missingness" rule in the spec refers to the *imputation threshold*, not the coverage threshold; however, if an ecosystem has > 85% missing traits, it is effectively unusable and should be skipped.
* **Mapping Strategy**: A direct API mapping from Web of Life IDs to Dryad DOIs does not exist. The plan uses a **Heuristic Mapping** strategy:
 1. Attempt to download a known 'trait mapping file' from Web of Life metadata.
 2. If unavailable, scrape the specific ecosystem's Web of Life study page for linked DOIs.
 3. If still unavailable, search the Dryad API for the ecosystem name + "traits" and download the first match.
 4. If no data is found, log a warning and skip the ecosystem.
* **Streaming**: For large networks, data will be streamed or chunked to avoid OOM errors.

## Methodological Rigor

### Statistical Approach

1. **Class Imbalance & Label Noise**: Ecological networks are sparse (few links, many non-links). Crucially, "unobserved" pairs are **probabilistic negatives** (likely non-interactions) but may contain false negatives (missed interactions).
 * **Strategy**: Stratified k-fold CV and `class_weight='balanced'` in Random Forest.
 * **Negative Sampling**: Negative samples are restricted to **co-occurring** species (spatially and temporally) to ensure the model learns trait matching, not just co-occurrence patterns (FR-007).
 * **Bias Mitigation**: The model includes `sampling_effort` as a covariate to account for detection bias. A **Sensitivity Analysis** will re-evaluate the model on a subset of "high-confidence" negatives (high sampling effort, no interaction) to quantify the impact of false negatives on trait importance.

2. **Multiple Comparison Correction**:
 * **Context**: We are testing the significance of the model against a null model (SC-001) and ranking traits (SC-002).
 * **Strategy**: The comparison against the null model will use a permutation test (sufficient iterations) to derive a p-value. If multiple ecosystems are tested, a Bonferroni or Benjamini-Hochberg correction will be applied to the p-values of the ecosystem-level tests.

3. **Power Justification & Scope Reframing**:
 * **Limitation**: The sample size will be a small number of ecosystems (N ~ small). This is statistically underpowered to claim "universal trait rules" or to perform robust meta-analysis across heterogeneous ecosystems.
 * **Reframing**: The project goal is explicitly **proof-of-concept generalizability**. We do not claim to prove universal biological laws. Instead, we demonstrate that trait-based prediction is feasible and generalizable *within the observed dataset distribution*.
 * **LOEO**: The primary metric is the **Leave-One-Ecosystem-Out (LOEO)** mean AUC-ROC. This provides a robust estimate of generalization error for the specific set of ecosystems studied. P-values from cross-ecosystem comparisons are interpreted as evidence of "potential generalizability" rather than definitive universal laws.

4. **Causal Inference**:
 * **Assumption**: The data is observational.
 * **Framing**: All results are framed as **associational**. We are predicting *link probability* based on traits, not claiming traits *cause* the link. The "trait gap" is a measure of unexplained variance, not a causal mechanism.

5. **Collinearity**:
 * **Risk**: Traits like "flower size" and "corolla depth" may be correlated.
 * **Mitigation**: Permutation importance is robust to collinearity in terms of ranking (it measures the drop in accuracy when a variable is shuffled), but the interpretation of "independent effect" is limited. The report will acknowledge that correlated traits may share importance scores.

6. **Label Noise & False Negatives (Detailed)**:
 * **Risk**: "Unobserved" pairs are treated as negatives, but they may be false negatives (interactions missed during sampling). This biases the model to under-predict links for rare/cryptic species.
 * **Mitigation**:
 1. **Sampling Effort**: Included as a feature to model detection probability.
 2. **Sensitivity Analysis**: Re-run model on "high-confidence" negatives to see if trait importance rankings shift significantly.
 3. **Reporting**: The final report will explicitly discuss the potential bias and the results of the sensitivity analysis.

### Measurement Validity

* **Traits**: The plan assumes traits from Dryad/TRY are validated.
* **Risk**: Scent data is often qualitative or missing.
* **Handling**: Scent will be treated as a categorical variable (presence/absence or compound type). If missing > 15% for a specific trait, the ecosystem is flagged.

## Decision/Rationale

| Decision | Rationale |
|:--- |:--- |
| **Random Forest over Deep Learning** | The dataset size (number of interactions) is likely too small for deep learning to generalize without overfitting. RF is robust to noise, handles mixed data types (continuous/categorical), and provides built-in importance metrics. It runs efficiently on CPU. |
| **Trait-Only Features** | To ensure generalization to unseen species in held-out ecosystems, the model uses only intrinsic plant traits (morphology, color, scent) and excludes species IDs. This allows the model to predict interactions for new species based on their biological characteristics. |
| **Co-occurring Negative Sampling** | Random negative sampling (any plant + any pollinator) would allow the model to learn "species A never interacts with species B because they are from different continents." Restricting negatives to co-occurring pairs forces the model to learn *trait compatibility* within the local community. |
| **Leave-One-Ecosystem-Out (LOEO) Validation** | A single held-out test with N=10 ecosystems results in a test set of size 1, which is statistically invalid for p-value calculation. LOEO cross-validation provides a robust estimate of generalization error across all ecosystems, making the "proof-of-concept" claim statistically sound. |
| **Trait-Shuffled Null Model** | The degree-preserving null model tests network topology, not trait efficacy. A trait-shuffled null (shuffling trait values among species) is the scientifically valid baseline to test if the model's performance is driven by traits. The degree-preserving null is retained as a secondary check for network structure. |
| **Heuristic Mapping for Data** | A direct API mapping from Web of Life IDs to Dryad DOIs does not exist. The heuristic mapping strategy (scraping, API search) automates the ingestion process and makes the pipeline robust to missing manual mappings. |
| **Dynamic Iteration Scaling** | Permutation tests can be computationally expensive. A dynamic scaling strategy ensures the pipeline completes within the prescribed time limit by reducing iterations or using an approximation if necessary. |
| **Scope Reframing** | Given N=8-10 ecosystems, claims of "universal rules" are scientifically unsound. The project is reframed as a "proof-of-concept" for trait-based prediction generalizability within the observed dataset, acknowledging power limitations. |
| **Label Noise Mitigation** | Treating unobserved pairs as true negatives introduces bias. The plan explicitly addresses this via `sampling_effort` covariates and sensitivity analysis on high-confidence negatives. |