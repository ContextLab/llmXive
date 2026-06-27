# Feature Specification: Predicting Avian Foraging Behavior from Public eBird Data and Land Cover Maps

**Feature Branch**: `001-avian-foraging-land-cover`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Predicting Avian Foraging Behavior from Public eBird Data and Land Cover Maps"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Extraction and Merging Pipeline (Priority: P1)

The research pipeline extracts eBird occurrence records for 20–30 bird species with documented foraging strategies and merges them with land cover composition data from NLCD 2019 within 100m buffers around each observation point.

**Why this priority**: This forms the foundational dataset without which no analysis can proceed. It is independently testable by verifying that merged records contain all required fields (species, foraging strategy, land cover proportions) and that filtering criteria (≥50 observations per species) are correctly applied.

**Independent Test**: Can be fully tested by running the data extraction script and validating that the output CSV contains ≥1000 total records with no missing values in the foraging-strategy or land-cover columns, and that each species has ≥50 observations.

**Acceptance Scenarios**:

1. **Given** eBird data for 25 species with documented foraging strategies, **When** the extraction pipeline runs, **Then** the merged dataset contains ≥1000 observation records with complete land cover proportions for each point
2. **Given** species with <50 observations in the source data, **When** filtering is applied, **Then** those species are excluded from the analysis dataset and logged in a summary report

---

### User Story 2 - Classification Model Training and Evaluation (Priority: P2)

The pipeline trains a random forest classifier to predict foraging strategy (ground, canopy, aerial) from land cover proportions and evaluates performance using 5-fold cross-validation with balanced accuracy and per-class F1 scores.

**Why this priority**: This is the core analytical step that directly addresses the research question. It is independently testable by verifying that model performance metrics are computed and that classification performance exceeds chance via permutation testing.

**Independent Test**: Can be fully tested by running the training script and verifying that balanced accuracy ≥0.55 and that permutation tests (1000 iterations) yield p < 0.05 for the null hypothesis that performance equals chance.

**Acceptance Scenarios**:

1. **Given** the merged dataset from User Story 1, **When** the random forest classifier is trained with 5-fold cross-validation, **Then** balanced accuracy is ≥0.55 and per-class F1 scores are computed for all three foraging guilds
2. **Given** a trained model, **When** permutation tests run (1000 iterations), **Then** the observed balanced accuracy exceeds the 95th percentile of permuted accuracies (p < 0.05)

---

### User Story 3 - Visualization and Feature Importance Reporting (Priority: P3)

The pipeline generates visualizations including a confusion matrix, feature importance bar chart, and spatial map of high-probability foraging habitats for 2–3 focal species, along with a summary report of which land cover types most strongly predict each foraging strategy.

**Why this priority**: This delivers the interpretable output needed for conservation planning decisions. It is independently testable by verifying that all three visualization types are generated and that the feature importance report lists the top 3 land cover predictors per foraging guild.

**Independent Test**: Can be fully tested by running the visualization script and verifying that output files include a confusion matrix image, feature importance chart, and spatial map for at least 2 focal species.

**Acceptance Scenarios**:

1. **Given** a trained model with feature importance scores, **When** visualization generation runs, **Then** three output files are created: confusion matrix (PNG), feature importance bar chart (PNG), and spatial habitat map (GeoJSON/PNG) for ≥2 focal species
2. **Given** the feature importance output, **When** the summary report is generated, **Then** it lists the top 3 land cover predictors for each of the 3 foraging guilds with their importance scores

---

### Edge Cases

- What happens when a species has observations in land cover types not present in the training data distribution?
- How does the system handle NLCD tiles that are partially missing or have invalid values at observation coordinates?
- What occurs when the foraging strategy database lacks entries for a species included in the eBird query?
- How does the pipeline behave when eBird API rate limits are hit during data download?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract eBird occurrence records for 20–30 species with documented foraging strategies from the eBird Basic Dataset (See US-1)
- **FR-002**: System MUST obtain NLCD 2019 land cover data via HTTPS and extract composition proportions within 100m buffers around each observation point (See US-1)
- **FR-003**: System MUST filter the merged dataset to retain only species with ≥50 observations each to ensure statistical power (See US-1)
- **FR-004**: System MUST train a random forest classifier using scikit-learn with 5-fold cross-validation to predict foraging strategy from land cover proportions (See US-2)
- **FR-005**: System MUST conduct permutation tests with 1000 iterations to assess whether classification performance exceeds chance at p < 0.05 threshold (See US-2)
- **FR-006**: System MUST compute and report balanced accuracy and per-class F1 scores to account for class imbalance across foraging guilds (See US-2)
- **FR-007**: System MUST generate three visualization outputs: confusion matrix, feature importance bar chart, and spatial map for ≥2 focal species (See US-3)

### Key Entities

- **ObservationRecord**: Represents a single eBird sighting with attributes (species_id, observation_date, latitude, longitude, foraging_strategy)
- **LandCoverProfile**: Represents land cover composition at a location with attributes (location_id, forest_proportion, grassland_proportion, wetland_proportion, urban_proportion, other_proportions)
- **ForagingGuild**: Represents a categorical foraging strategy with values (ground, canopy, aerial) and associated species membership

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Balanced accuracy of the foraging-strategy classifier is measured against chance performance (theoretical baseline) to confirm predictive signal (See US-2)
- **SC-002**: Permutation test p-value is measured against the α = 0.05 significance threshold to validate that observed performance exceeds chance (See US-2)
- **SC-003**: Feature importance rankings are measured against domain literature on habitat-foraging associations to assess ecological validity (See US-3)
- **SC-004**: Total pipeline runtime is measured against the 6-hour CI job limit to confirm CPU-only feasibility (See US-1, US-2, US-3)

## Assumptions

- eBird Basic Dataset contains sufficient occurrence records for ≥20 species with documented foraging strategies in the ground/canopy/aerial categories
- NLCD 2019 land cover classification includes the necessary classes to distinguish habitat types relevant to the three foraging guilds (forest, grassland, wetland, urban)
- Foraging strategy labels for each species are available from authoritative ornithological sources (e.g., Cornell Lab of Ornithology, Birds of the World) and are consistent across the study species
- The observational nature of this design means all findings will be framed as associational relationships between land cover profiles and foraging strategies, not causal claims
- Land cover data at 30m resolution is sufficient to capture the habitat features influencing foraging behavior at the spatial scale of eBird observations
- No GPU or CUDA acceleration is required; all computations use scikit-learn's CPU-only implementations with default precision
- The merged dataset will fit within 7 GB RAM and 14 GB disk when filtered to species with ≥50 observations each
- Total pipeline runtime including data download, processing, training, and visualization will complete within 6 hours on a 2 CPU core runner
