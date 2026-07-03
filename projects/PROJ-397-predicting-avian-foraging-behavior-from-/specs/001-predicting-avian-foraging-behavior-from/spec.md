# Feature Specification: Predicting Avian Foraging Guilds from Public eBird Data and Land Cover Maps

**Feature Branch**: `001-avian-foraging-land-cover`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Predicting Avian Foraging Behavior from Public eBird Data and Land Cover Maps"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Extraction and Merging Pipeline (Priority: P1)

The research pipeline extracts eBird Basic Dataset (EBD) occurrence records for a selected set of bird species with documented foraging guilds. (ground, canopy, aerial) and merges them with land cover composition data from NLCD 2019 within 100m buffers around each observation point. Foraging guild labels are assigned to species based on external ornithological literature (e.g., Birds of the World), not directly from the EBD.

**Why this priority**: This forms the foundational dataset without which no analysis can proceed. It is independently testable by verifying that the species selection rule (top 25 by count) is executed, filtering criteria (≥50 observations per species) are correctly applied, and that merged records contain all required fields (species_id, foraging_guild, land_cover_proportions).

**Independent Test**: Can be fully tested by running the data extraction script and validating that: (1) the top 25 species by record count were selected; (2) species with <50 observations were excluded; and (3) the output CSV contains complete land cover proportions and assigned foraging guilds for all retained records.

**Acceptance Scenarios**:

1. **Given** the EBD containing occurrence records for >50 species, **When** the extraction pipeline runs, **Then** the merged dataset contains records for exactly the top 25 species by total record count, with complete land cover proportions for each point
2. **Given** species with <50 observations in the source data, **When** filtering is applied, **Then** those species are excluded from the analysis dataset and logged in a summary report

---

### User Story 2 - Classification Model Training and Evaluation (Priority: P2)

The pipeline trains a random forest classifier to predict the species-level foraging guild (ground, canopy, aerial) from land cover proportions and evaluates performance using 5-fold cross-validation. To control for species identity confounding, the pipeline conducts a stratified permutation test (stratified by species) to assess whether land cover predicts guild membership independent of species-specific habitat preferences.

**Why this priority**: This is the core analytical step that directly addresses the research question. It is independently testable by verifying that model performance metrics are computed and that the stratified permutation test validates signal beyond taxonomic identity.

**Independent Test**: Can be fully tested by running the training script and verifying that: (1) balanced accuracy is measured against chance performance; (2) per-class F1 scores are computed; and (3) the stratified permutation test (1000 iterations) yields p < 0.05 for the null hypothesis that performance equals chance after controlling for species identity.

**Acceptance Scenarios**:

1. **Given** the merged dataset from User Story 1, **When** the random forest classifier is trained with 5-fold cross-validation, **Then** balanced accuracy is measured against chance performance and per-class F1 scores are computed for all three foraging guilds
2. **Given** a trained model, **When** stratified permutation tests run (1000 iterations, stratified by species), **Then** the observed balanced accuracy exceeds the upper percentile of permuted accuracies (p < 0.05), confirming signal beyond species identity

---

### User Story 3 - Visualization and Feature Importance Reporting (Priority: P3)

The pipeline generates visualizations including a confusion matrix, feature importance bar chart, and spatial map of high-probability foraging habitats for the top 2 species by observation count, along with a summary report of which land cover types most strongly predict each foraging guild.

**Why this priority**: This delivers the interpretable output needed for conservation planning decisions. It is independently testable by verifying that all three visualization types are generated for the deterministic set of focal species and that the feature importance report lists the top 3 land cover predictors per foraging guild.

**Independent Test**: Can be fully tested by running the visualization script and verifying that: (1) output files include a confusion matrix image, feature importance chart, and spatial map for the top 2 species by observation count; and (2) the feature importance report lists the top land cover predictors for each of the foraging guilds.

**Acceptance Scenarios**:

1. **Given** a trained model with feature importance scores, **When** visualization generation runs, **Then** three output files are created: confusion matrix (PNG), feature importance bar chart (PNG), and spatial habitat map (GeoJSON/PNG) for the top 2 species by observation count
2. **Given** the feature importance output, **When** the summary report is generated, **Then** it lists the top 3 land cover predictors for each of the 3 foraging guilds with their importance scores

---

### Edge Cases

- What happens when a species has observations in land cover types not present in the training data distribution?
- How does the system handle NLCD tiles that are partially missing or have invalid values at observation coordinates?
- What occurs when the foraging guild database lacks entries for a species included in the top 25 selection?
- How does the pipeline behave when eBird API rate limits are hit during data download?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract eBird Basic Dataset (EBD) occurrence records for the top-ranked species by total record count that have documented foraging guilds (See US-1)
- **FR-002**: System MUST obtain NLCD land cover data via HTTPS and extract composition proportions within 100m buffers around each observation point (See US-1)
- **FR-003**: System MUST filter the merged dataset to retain only species with ≥50 observations each to ensure statistical power (See US-1)
- **FR-004**: System MUST train a random forest classifier using scikit-learn with k-fold cross-validation to predict foraging guild from land cover proportions (See US-2)
- **FR-005**: System MUST conduct stratified permutation tests with a sufficient number of iterations (stratified by species) to ensure robust statistical inference. to assess whether classification performance exceeds chance at p < 0.05 threshold, controlling for species identity (See US-2)
- **FR-006**: System MUST compute and report balanced accuracy and per-class F1 scores to account for class imbalance across foraging guilds (See US-2)
- **FR-007**: System MUST generate three visualization outputs: confusion matrix, feature importance bar chart, and spatial map for the top species by observation count (See US-3)
- **FR-008**: System MUST include species identity as a covariate or use stratified resampling in all significance tests to control for the confounding effect of species-specific habitat preferences (See US-2)

### Key Entities

- **ObservationRecord**: Represents a single eBird sighting with attributes (species_id, observation_date, latitude, longitude)
- **LandCoverProfile**: Represents land cover composition at a location with attributes (location_id, forest_proportion, grassland_proportion, wetland_proportion, urban_proportion, other_proportions)
- **ForagingGuild**: Represents a categorical foraging strategy with values (ground, canopy, aerial) assigned to species based on external literature

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Balanced accuracy of the foraging-guild classifier is measured against chance performance (theoretical baseline) to confirm predictive signal independent of species identity (See US-2)
- **SC-002**: Stratified permutation test p-value is measured against the α = 0.05 significance threshold to validate that observed performance exceeds chance after controlling for species identity (See US-2)
- **SC-003**: Feature importance rankings are measured against domain literature on habitat-foraging associations to assess ecological validity (See US-3)
- **SC-004**: Total pipeline runtime is measured against the CI job limit. to confirm CPU-only feasibility (See US-1, US-2, US-3)

## Assumptions

- eBird Basic Dataset contains sufficient occurrence records for ≥25 species with documented foraging guilds in the ground/canopy/aerial categories
- NLCD 2019 land cover classification includes the necessary classes to distinguish habitat types relevant to the three foraging guilds (forest, grassland, wetland, urban)
- Foraging guild labels for each species are available from authoritative ornithological sources (e.g., Cornell Lab of Ornithology, Birds of the World) and are consistent across the study species; these labels are assigned at the species level, not the observation level
- The observational nature of this design means all findings will be framed as associations between land cover profiles and species-level foraging guilds, not causal claims about individual behavior
- Land cover data at moderate resolution is sufficient to capture the habitat features influencing foraging behavior at the spatial scale of eBird observations
- No GPU or CUDA acceleration is required; all computations use scikit-learn's CPU-only implementations with default precision
- The merged dataset will fit within 7 GB RAM and 14 GB disk when filtered to the top 25 species with ≥50 observations each
- Total pipeline runtime including data download, processing, training, and visualization will complete within 6 hours on a 2 CPU core runner