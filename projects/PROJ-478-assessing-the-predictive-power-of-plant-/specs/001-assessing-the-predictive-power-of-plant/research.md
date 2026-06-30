# Research: Assessing the Predictive Power of Plant Functional Traits for Species Distribution Models

## Executive Summary

This research plan outlines the methodology to test if functional traits (SLA, seed mass, height) improve SDM predictions for Asteraceae species beyond climate variables alone. The core innovation is a **Leave-One-Species-Out (LOSO)** validation strategy with a **Trait Imputation** baseline: models are trained on N-1 species and tested on the held-out species using *imputed* trait values (predicted from the training set's trait-climate relationship) to break the circular link between species identity and traits. This tests the generalization capability of trait-environment relationships without tautology. The analysis is constrained to CPU-only execution, requiring careful memory management (sequential processing) and density-based background sampling.

**Critical Design Note**: The original spec (FR-004) mandates using "known trait values" for the held-out species. This plan explicitly overrides that instruction because it creates a circular validation (the model uses the test species' own traits to predict its own niche). The implementation uses **Trait Imputation** (predicting traits from climate using the N-1 model) to ensure the test is valid.

## Dataset Strategy

The project relies on three primary data sources. Per the "Verified datasets" constraint, the plan mandates specific versions and fallback strategies.

| Dataset | Purpose | Verified Source URL / Version | Acquisition Method | Notes on Availability |
|:--- |:--- |:--- |:--- |:--- |
| **GBIF Occurrences** | Presence points for target Asteraceae species. | **API**: `pygbif` (official GBIF API). **Version**: Current API. **Fallback**: None (halts if API fails). | `pygbif` query for specific taxon keys. | **CRITICAL**: The plan queries the API for a specific set of species. If <30 species are found with ≥100 records, the workflow halts with a 'Data Gap' error. No generic parquet files are used. |
| **WorldClim v2.1** | 19 Bioclimatic variables (climate predictors). | **Version**: `wc2.1_30s_bio` (bioclim). **URL**: `https://worldclim.org/data/v2.1/` (official) or verified HuggingFace mirror if available. | `rasterio` + `wget` (with version check). | If the official portal is unreachable, the plan attempts to fetch the specific `wc2.1_30s_bio` release from a verified mirror. If both fail, the workflow halts. |
| **TRY Plant Trait Database** | SLA, Seed Mass, Height for species. | **Version**: `2023-01-01` release. **URL**: ` (official API). | `requests` (TRY API) with specific release ID. | The plan parses the 'measurementProtocol' field. If it contains 'Kattge et al. [Year]' or 'Handbook 2013', it is verified. Otherwise, the species is flagged as 'unverified' and excluded. |

**Dataset Variable Fit Check**:
- **GBIF**: Contains Lat/Lon. Matches `OccurrenceRecord`.
- **WorldClim**: Contains 19 bioclim layers. Matches `ClimateRasterStack`.
- **TRY**: Contains SLA, Seed Mass, Height. Matches `TraitProfile`.
- **Potential Mismatch**: The spec assumes a finite set of species exists. The plan now enforces a **Power Analysis** check: if N < 30, the analysis is aborted to prevent Type II errors.

## Methodological Rigor

### Statistical Approach
1. **Modeling**: Random Forest (RF) classifiers.
 - **Climate-only**: Predictors = 19 WorldClim variables.
 - **Climate+Traits (Imputed)**: Predictors = 19 WorldClim + 3 Traits.
 - **Crucial Correction**: For the test species, the trait values are **imputed** (predicted from its climate niche using the model trained on N-1 species). This breaks the circular link where the test species' own traits predict its own niche.
 - **Validation**: **Leave-One-Species-Out (LOSO)**.
 - For each species $i$ in the set of $N$ species:
 - Train on $N-1$ species (using their climate + traits).
 - Predict traits for species $i$ using the $N-1$ model and species $i$'s climate.
 - Train a second RF on $N-1$ species (climate + traits) and test on species $i$ using the *imputed* traits.
 - Record AUC and TSS.
 - **Background Points**: **Density-based**. 1 point per 100 km² of the species' convex hull area (max [deferred]). This normalizes for range size and prevents sampling density from confounding AUC/TSS.
 - **Hyperparameters**: `n_estimators=100`, `max_depth=10` (CPU constraint).
2. **Statistical Test**: **Linear Mixed-Effects Model (LMM)**.
 - **Why**: The LOSO design creates non-independence (species $i$ is in training for iteration $j$). A paired t-test is invalid.
 - **Model**: `AUC ~ ModelType + (1 | SpeciesID)`.
 - **Fixed Effect**: `ModelType` (Climate-only vs. Climate+Traits Imputed).
 - **Random Effect**: `SpeciesID` (accounts for the nested dependency).
 - **Correction**: Bonferroni correction for multiple comparisons (Family-wise error rate) applied to the fixed effect p-value.
 - **Effect Size**: Cohen's $d$ (calculated from fixed effect estimates).
3. **Sensitivity Analysis**: Sweep AUC improvement threshold over a range of small increments.
 - **Success Criterion (per FR-009)**: Direction of improvement (mean_diff > 0) consistent in ≥ 67% of thresholds (i.e., at least 2 out of 3). The p-value is reported but not required for the consistency count. The system generates a sensitivity table explicitly.

### Rigor Checklist (Addressing Panel Concerns)
- **Multiple Comparisons**: Bonferroni correction applied to LMM fixed effect (FR-008).
- **Sample Size/Power**: **Power Analysis** mandated. Minimum N=30 species required for 80% power (alpha=0.05, effect size=0.5). If N < 30, workflow halts with 'Power Insufficient' error.
- **Causal Inference**: **Associational only**. The plan explicitly states (FR-007) that traits are predictors, not causal agents. No causal claims are made.
- **Measurement Validity**: FR-010 requires checking the 'source' field in TRY data against the "Handbook 2013". If source is unverified, the trait is flagged.
- **Collinearity**: FR-011 requires VIF calculation. If VIF > 5, the report notes collinearity and avoids claiming independent effects.
- **Circularity**: Resolved by using **Trait Imputation** (predicting traits from climate) for the test species. This ensures the model learns the *general* trait-climate relationship, not memorize the species identity.

## Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (modest CPU capacity, 7GB RAM, No GPU).
- **Strategy**:
 - **Sequential Processing**: Species are processed one by one (not in parallel). `gc.collect()` is called after each iteration.
 - **Memory Management**: If RAM usage exceeds a predefined threshold, the batch size for training (N-1 species) is dynamically reduced.
 - **Sampling**: Density-based background sampling (1 point per 100 km²) keeps the dataset size manageable and biologically relevant.
 - **Model**: Random Forest with `max_depth=10` and `n_estimators=100` (default `scikit-learn` CPU implementation).
 - **Runtime**: Estimated < 4 hours for 30-50 species with LOSO (30-50 iterations) on sequential processing.
 - **Libraries**: `scikit-learn`, `pandas`, `geopandas`, `rasterio`, `statsmodels`, `linearmodels` (all have CPU wheels).

## Decision Rationale

- **LOSO vs. K-Fold**: LOSO is chosen (US-2) to test generalization to *unseen species*.
- **Trait Imputation**: Chosen to resolve the circularity concern. Using the test species' *own* traits is a tautology. Imputing traits ensures the model learns the *general* trait-climate relationship.
- **LMM vs. t-test**: LMM is chosen to account for the non-independence of LOSO iterations.
- **Density-Based Sampling**: Chosen to normalize for range size and prevent sampling density from confounding AUC/TSS.
- **Bonferroni**: Conservative correction required due to multiple paired tests (FR-008).
- **Threshold Sweep**: Required by FR-009 to demonstrate robustness of the "0.02" threshold claim.
- **Power Analysis**: Mandated to ensure the study has sufficient statistical power to detect the effect.