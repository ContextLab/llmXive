# Feature Specification: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

**Feature Branch**: `001-predicting-species-distribution-shifts`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing (US-1)

The system MUST download historical occurrence records (from a multi-decade baseline period) and corresponding climate rasters (WorldClim), then preprocess them by filtering for breeding season, removing duplicates, and spatially thinning points to reduce autocorrelation.

**Why this priority**: This is the foundational step; without clean, temporally-aligned occurrence and climate data, no model can be trained or validated.

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying that the output CSV contains unique coordinates where no two points are within the minimum distance defined in FR-014, and that climate variables are successfully extracted for every record.

**Acceptance Scenarios**:

1. **Given** a list of target species names, **When** the pipeline runs, **Then** occurrence records are filtered to breeding months and duplicates removed.
2. **Given** occurrence coordinates, **When** spatial thinning is applied, **Then** points are separated by at least the minimum distance specified in FR-014 to reduce spatial autocorrelation.
3. **Given** climate rasters, **When** extracted at occurrence points, **Then** every record has non‑null values for temperature and precipitation variables.

---

### User Story 2 - Model Training and Validation (US-2)

The system MUST train three SDM algorithms (MaxEnt‑style, Random Forest, Bioclim) on the historical dataset using spatial block cross‑validation as defined in FR-007 (K = 5 equidistant blocks, rotating held‑out block). All computations must run on CPU without GPU acceleration.

**Why this priority**: This delivers the core analytical capability to assess predictive skill, directly addressing the research question regarding SDM reliability.

**Independent Test**: Can be fully tested by training models on a single species subset and verifying that training completes successfully and outputs performance metrics (AUC, TSS) without CUDA errors.

**Acceptance Scenarios**:

1. **Given** the preprocessed historical dataset, **When** the training script runs, **Then** models are trained using scikit‑learn or equivalent CPU‑optimized libraries.
2. **Given** the spatial block configuration defined in FR-007, **When** validation occurs, **Then** performance metrics (AUC, TSS) are calculated on the held‑out blocks.
3. **Given** hardware constraints, **When** models train, **Then** no GPU/CUDA dependencies are invoked (verified via process monitoring).

---

### User Story 3 - Future Projection and Evaluation (US-3)

The system MUST project trained models onto future climate scenarios (CMIP SSP, mid‑21st century) and evaluate predictive performance against recent occurrence records (2005‑2020). Baseline historic performance is derived exclusively from the spatial‑block CV results (FR‑007). Recent occurrence records (2005-2020) are used solely as the independent ground-truth for evaluating the 2050 projection, preventing circularity. Niche stability is assessed using both ΔAUC/TSS and a climate‑novelty index (MESS) to separate model transferability from genuine ecological change.

**Why this priority**: This completes the forecasting loop, allowing comparison of historic predictions against independent recent observations and quantifying both performance decline and environmental novelty.

**Independent Test**: Can be fully tested by loading pre‑trained models, running projections against the 2050 rasters, and then computing AUC/TSS on the recent test set plus MESS scores for each projection.

**Acceptance Scenarios**:

1. **Given** trained models and future climate rasters, **When** projection runs, **Then** suitability maps are generated for 2050 scenarios.
2. **Given** recent occurrence records (2005‑2020), **When** evaluated against projections, **Then** AUC and TSS metrics are computed and compared to historic CV baselines.
3. **Given** the projection results, **When** niche‑stability analysis runs, **Then** both ΔAUC/TSS and MESS scores are reported, highlighting areas of climate novelty.
4. **Given** the bias‑correction layer created during preprocessing, **When** applied to recent test records, **Then** the same bias adjustment is used for both historic and recent datasets (see FR‑017).

---

### Edge Cases

- What happens when a species has very few occurrence records after thinning? (System MUST skip or flag with status 'INSUFFICIENT_DATA' – note: the system will proceed without a hard filter but will log a warning.)
- How does system handle missing climate data for specific coordinates? (System MUST impute using nearest neighbor or exclude the point).
- What happens if recent test records (2005‑2020) are unavailable for a target species? (System MUST log a warning and exclude from evaluation metrics).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download North American bird occurrence data (mid‑to‑late twentieth century) via GBIF API or eBird and climate rasters from WorldClim v2 via wget or equivalent, ensuring all required predictor variables are present for every record (See US-1). *(All URLs must be pre‑verified static links with published SHA‑256 checksums – see FR-016.)*
- **FR-002**: System MUST download recent occurrence records (early twenty‑first century to present) via GBIF API or eBird for evaluation purposes (See US-3). *(All URLs must be pre‑verified static links with published SHA‑256 checksums – see FR-016.)*
- **FR-003**: System MUST spatially thin occurrence points using a maximum distance thinning method with a default minimum distance threshold of **10 km** (or a dynamic calculation based on the 95th percentile of nearest‑neighbor distances if specified) to reduce spatial autocorrelation before model training (See US-1). *(Reference to FR-014)*
- **FR-004**: System MUST train all SDM algorithms using CPU‑only libraries (e.g., `scikit-learn`) with no GPU/CUDA dependencies to ensure compatibility with free‑tier CI runners (See US-2).
- **FR-007**: System MUST use spatial block cross‑validation for training and validation, dividing the spatial domain into **K = 5** blocks using an equidistant grid algorithm and rotating the held‑out block to ensure spatial independence between train and test sets (See US-2).
- **FR-009**: System MUST assess niche stability by (a) calculating ΔAUC and ΔTSS between historic CV performance and future‑projection performance, and (b) computing the Multivariate Environmental Similarity Surface (MESS) between historic and future climate layers; both results are reported to distinguish model transferability (indicated by high climate novelty/MESS) from genuine niche change (indicated by ΔAUC decline in low-novelty areas) (See US-3).
- **FR-014**: System MUST define the minimum distance for spatial thinning as **10 km** unless overridden by a dynamic calculation (see FR-003).
- **FR-016**: System MUST verify that all external data sources (GBIF/eBird APIs, WorldClim download URLs) are referenced by static, version‑pinned URLs and that a SHA‑256 checksum file is provided; the pipeline shall abort if a downloaded file’s checksum does not match the published value (See US-1, US-2).
- **FR-017**: System MUST apply the same bias‑correction layer (generated during preprocessing) to both historic and recent test datasets to ensure comparable sampling bias treatment (See US-2, US-3).
- **FR-018**: System MUST perform a simulation-based power analysis using bootstrapped AUC distributions to ensure $\ge 0.8$ power to detect a $\Delta \text{AUC} \ge 0.05$ (See US-2).
- **FR-019**: To comply with the 6-hour compute limit, the system MUST limit the analysis to $\le 5$ species and $\le 500$ bootstrap iterations per model (See US-2).

### Key Entities

- **Occurrence Record**: Represents a species sighting with latitude, longitude, date, and source.
- **Climate Variable**: Represents environmental data (temperature, precipitation) at a specific grid resolution.
- **Model Artifact**: Represents the trained SDM object (MaxEnt, RF, or Bioclim) ready for projection.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Predictive performance (AUC) is measured against a baseline null‑model that predicts mean prevalence; the system must achieve **AUC $\ge$ 0.70** on spatial‑block cross‑validated historic data (See US-2).
- **SC-002**: Total pipeline execution time is measured against the GitHub Actions free-tier limit; the system MUST complete all tasks within $\le 6$ hours (See US-2).
- **SC-004**: Data acquisition completeness is measured: $\ge 95\%$ of target species must have $\ge 100$ records after thinning, and $\ge 99\%$ of extracted climate values must be non-null (See US-1).
- **SC-005**: All external downloads must pass SHA‑256 checksum verification; any mismatch aborts the pipeline (See FR-016).

## Assumptions

- Users have stable internet connectivity to access GBIF and WorldClim APIs without firewall restrictions.
- A subset of North American bird species (e.g., a representative number of common species) will be selected to ensure the analysis fits within available compute resources.
- The WorldClim grid resolution is sufficient for the spatial scale of the target bird species' ranges.
- The bias‑correction layer adequately captures sampling bias for both historic and recent datasets.