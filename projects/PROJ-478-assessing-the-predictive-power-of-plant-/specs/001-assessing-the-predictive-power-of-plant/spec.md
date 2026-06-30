# Feature Specification: Assessing the Predictive Power of Plant Functional Traits for Species Distribution Models

**Feature Branch**: `feat-assess-plant-traits`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: *"Assess whether plant functional traits (specific leaf area, seed mass, plant height) add predictive value to climate‑only species distribution models for multiple Asteraceae species, using GBIF occurrences, WorldClim climate layers, and TRY trait data; compare AUC/TSS via paired t‑tests and report significance."*

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Generate a climate‑only SDM for a single species (Priority: P1)

A researcher wants to build a baseline SDM using only climate variables so that the model’s performance can be used as a reference point.

**Why this priority**: Establishes the essential baseline against which any trait‑augmented model is evaluated.

**Independent Test**: Run the workflow for one species (e.g., *Helianthus annuus*) and verify that a cleaned occurrence file, climate rasters, and cross‑validated AUC/TSS values are produced.

**Acceptance Scenarios**:

1. **Given** a valid GBIF taxon key, **When** the system downloads occurrences, removes duplicates and spatially biased points, **Then** a cleaned presence dataset containing ≥ 80 % of raw records is saved.  
2. **Given** the cleaned presence dataset, **When** the system extracts the 19 WorldClim v2.1 bioclimatic layers for the species’ extent, **Then** a raster stack aligned to occurrence coordinates is created and used to train a Random Forest classifier (k‑fold cross‑validation), yielding an average AUC value that is reported for comparison.

---

### User Story 2 – Add functional trait covariates and re‑train the SDM (Priority: P2)

A researcher wants to augment the climate‑only model with species‑level functional traits to test whether predictive performance improves, using a cross-species validation design to ensure generalization.

**Why this priority**: Directly addresses the research question about the marginal value of traits by testing if traits predict distributions of species with *held-out occurrence data* (but known traits).

**Independent Test**: Run the workflow for a subset of species (e.g., a representative sample) and validate the model against the held-out species, comparing the two sets of performance metrics.

**Acceptance Scenarios**:

1. **Given** the species name, **When** the system retrieves specific leaf area, seed mass, and plant height from the TRY public subset, **Then** these values are attached to the species record (or flagged if missing).  
2. **Given** climate rasters and trait values, **When** a Random Forest model is trained with climate + trait predictors using a **leave-one-species-out (LOSO)** strategy (where the model is trained on N-1 species and evaluated on the 1 held-out species using that species' *known* trait values), **Then** the model outputs AUC and TSS scores on the *held-out* species that can be directly compared to the climate‑only baseline.

---

### User Story 3 – Conduct a comparative statistical analysis across 50 species (Priority: P3)

A researcher wants to evaluate, at the community level, whether trait‑augmented models outperform climate‑only models in terms of generalization to species with *held-out occurrence data*.

**Why this priority**: Provides the aggregate evidence needed for the manuscript‑level conclusion.

**Independent Test**: Execute the full pipeline for all focal Asteraceae species using the cross-species validation design and run the paired statistical tests; verify that the reported p‑values, effect sizes, and sensitivity analyses meet the success criteria.

**Acceptance Scenarios**:

1. **Given** the per‑species generalization AUC/TSS results for both model configurations (climate-only vs. climate+traits), **When** the system performs a paired two‑sided t‑test (with Bonferroni correction) across the target set of species, **Then** it reports a corrected p‑value, Cohen’s d, and indicates whether the improvement meets the predefined 0.02 AUC threshold.  
2. **Given** the t‑test outcome, **When** the system sweeps the improvement threshold over {0.01, 0.02, 0.05}, **Then** it produces a sensitivity table showing that the direction of improvement is consistent in ≥ 67% of thresholds (i.e., at least 2 of 3).

---

### Edge Cases

- **No occurrence records**: If GBIF returns zero records for a species, the workflow aborts with a clear log message and skips that species in the aggregate analysis.  
- **Missing trait data**: If any of the three required traits are unavailable for a species, the system flags the species, excludes it from the trait‑augmented analysis, and records the exclusion reason.  
- **Model training failure**: If the Random Forest fails to converge (e.g., due to too few background points), the system retries with reduced `max_depth` (≤ 10) and logs the fallback parameters.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST retrieve GBIF occurrence records for a given species, remove duplicate coordinates, and apply spatial thinning (default 10 km, minimum 1 km) to produce a cleaned presence dataset. If thinning reduces records to an insufficient level, the system MUST reduce the thinning distance or flag the species as 'insufficient data'. *(See US-1)*
- **FR-002**: System MUST download the complete set of WorldClim bioclimatic rasters covering the convex hull of the cleaned occurrences and align them to the occurrence points. *(See US-1)*
- **FR-003**: System MUST retrieve species‑level values for specific leaf area, seed mass, and plant height from the TRY public subset and join them to the species record; missing values trigger a "[missing trait]" flag. *(See US-2)*
- **FR-004**: System MUST train two Random Forest classifiers (CPU‑only, scikit‑learn) – (a) climate‑only, (b) climate + traits – using a **full leave-one-species-out (LOSO) cycle** on the set of species with complete trait data (N), where each of the N species serves as the test set exactly once. For the test species, the 'climate+traits' model MUST use the *known* trait values of that species as inputs. Cross-validation is used internally for hyperparameter tuning within each training fold. *(See US-2)*
- **FR-005**: System MUST conduct a paired two‑sided t‑test comparing mean generalization AUC (and TSS) between the two model configurations across all species, apply a Bonferroni correction for multiple comparisons, and report corrected p‑values and effect sizes. The 'climate+traits' model's AUC is calculated using the known trait values of the held-out species. *(See US-3)*
- **FR-006**: System MUST verify that all three trait variables are present for each species; if any are absent, the species is excluded from the trait‑augmented branch and logged. *(See US-2)*  
- **FR-007**: System MUST frame all reported relationships as associative (predictive) rather than causal, and include an explicit disclaimer in the final report. *(See US-3)*
- **FR-008**: System MUST implement a Bonferroni (family‑wise error) correction for the multiple paired tests and expose the corrected significance level. *(See US-3)*
- **FR-009**: System MUST adopt a minimum AUC improvement threshold of **0.02** (justified as essential to distinguish ecologically meaningful signal from noise per methodology panel feedback) and perform a sensitivity sweep over thresholds {0.01, 0.02, 0.05}, reporting how ΔAUC varies. The system succeeds if it produces the sensitivity table and the report. *(See US-3)*
- **FR-010**: System MUST ensure that trait measurements originate from validated instruments as documented in the 2013 "Handbook for Standardised Measurement of Plant Functional Traits Worldwide" (cited in the idea) by checking the 'source' metadata field in the TRY export. If the source is not 'Handbook 2013' or equivalent, the value is flagged as 'unverified protocol'. *(See US-2)*
- **FR-011**: System MUST compute Variance Inflation Factor (VIF) for the full predictor set (climate + traits) and report any VIF > 5; if such collinearity is detected, the report must avoid claiming independent effects of the correlated predictors. This is required to ensure valid attribution of predictive power in multivariate models, per methodology panel feedback. *(See US-2)*

### Key Entities *(include if feature involves data)*

- **Species**: Represents an individual plant taxon (genus + species) with associated GBIF occurrence points.  
- **OccurrenceRecord**: Latitude, longitude, timestamp, and source metadata for a single observation.  
- **ClimateRasterStack**: Set of 19 aligned bioclimatic layers (WorldClim v2.1) covering the species’ extent.  
- **TraitProfile**: Species‑level values for specific leaf area, seed mass, and plant height.  
- **ModelResult**: Cross‑validated performance metrics (AUC, TSS) for a given predictor configuration, specifically the *generalization* score on a held-out species.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The cleaned occurrence dataset for each processed species retains ≥ 80 % of raw GBIF records after duplicate removal and spatial thinning, and contains ≤ 10 000 background points. *(See US-1)*
- **SC-002**: The system calculates and reports the mean cross‑validated AUC across the N species; if the mean AUC is < 0.70, the report must flag this as below the minimal predictive‑performance benchmark. *(See US-2)*
- **SC-003**: The paired t‑test (Bonferroni‑corrected) reports the corrected p‑value and mean ΔAUC; the system succeeds if it correctly executes the test and reports these values, regardless of whether p < 0.05. *(See US-3)*
- **SC-004**: Sensitivity analysis across thresholds {0.01, 0.02, 0.05} shows the direction of improvement (ΔAUC > 0) in ≥ 67% of the 3 thresholds (i.e., at least 2 out of 3), demonstrating robustness of the result. *(See US-3)*
- **SC-005**: All VIF values for predictors are ≤ 5; if any exceed this limit, the report explicitly notes the collinearity and refrains from attributing independent predictive power to the affected variables. *(See US-2)*

## Assumptions

- The focal taxa are limited to **50 Asteraceae species** with ≥ 100 GBIF occurrence records each.  
- The **TRY public subset** includes at least the three required traits for ≥ 90 % of the selected species.  
- Spatial thinning distance defaults to **10 km** unless otherwise specified, with a minimum of 1 km.  
- **Background sampling** uses a uniform random selection of **10 000** points per species within the study extent.  
- All computations run on a **CPU‑only GitHub Actions runner** (2 cores, ~7 GB RAM, ≤ 6 h runtime); Random Forest hyperparameters are capped at `n_estimators=100`, `max_depth=10` to stay within memory limits.  
- No GPU, CUDA, or large‑model inference is required; the workflow relies exclusively on `scikit‑learn`, `pandas`, `geopandas`, and `rasterio`, all of which are free‑CPU compatible.  
- The analysis treats the relationship between traits, climate, and species presence as **associational**, not causal.  
- The **cross-species validation (LOSO)** design tests whether traits improve prediction for a species whose *occurrence data* was not in the training set, assuming its *trait values* are available from the TRY database.

--- 

*End of Specification*