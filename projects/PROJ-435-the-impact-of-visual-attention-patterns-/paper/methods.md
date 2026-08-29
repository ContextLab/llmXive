# Methods

## Data Collection and Sources

### Eye-Tracking Dataset
The primary dataset consists of eye-tracking recordings from participants viewing news headlines. Data were obtained from a publicly available repository (Dundee Eye-Tracking Corpus or equivalent as specified in `research.md`). The dataset includes:
- Gaze coordinates (x, y) with timestamps
- Headline text and metadata
- Participant identifiers
- Source attribution and headline body ROI definitions

### Ethical Considerations
All data used in this analysis are from publicly available, anonymized sources. No personally identifiable information was processed.

## Preprocessing Pipeline

### 1. Data Ingestion and Validation
- Raw data fetched from configured URL and validated against SHA-256 checksums
- Schema validation ensures required columns: `headline_text`, `belief_rating`, `cognitive_reflection_score`, `fixation_duration`
- ROI definitions validated against configuration specifications

### 2. Fixation Detection
- **Algorithm**: I-VT (I-VT = I-VT Fixation Detection) with duration threshold of 100ms (configurable)
- **Parameters**:
 - Minimum fixation duration: 100ms (FR-001 compliance)
 - Dispersion threshold: Configurable via `code/config.yaml`
- I-DT algorithm available but not enabled by default

### 3. ROI Mapping
- Point-in-polygon algorithm assigns each gaze point to a ROI
- ROIs: `source_attribution` and `headline_body`
- Trials with missing ROI coordinates excluded
- Zero-fixation ROIs handled with duration = 0

### 4. Participant Filtering
- Participants with ≥20% data loss excluded
- Exclusion reasons logged in `output/exclusion_log.txt`
- Data quality report generated with participant counts and exclusion statistics

## Feature Engineering

### Valence Calculation
- **Primary Lexicon**: NRC Emotion Lexicon
- **Fallback**: VADER Sentiment Lexicon (if NRC coverage < 50%)
- Lexicon usage tracked in `lexicon_used` column
- Switch events logged as "Automatic Lexicon Fallback"

### Data Merging
- Datasets merged on `participant_id` and `headline_id`
- Outlier capping: CRT scores capped at 1st and 99th percentiles
- Control variables:
 - `headline_length` (word count)
 - `total_fixation_duration` (sum of fixation durations)

## Statistical Analysis

### Mixed-Effects Regression Model
**Formula**:
```
belief_rating ~ fixation_duration * valence * crt + headline_length + total_fixation_duration + (1|participant_id) + (1|headline_id)
```

**Model Components**:
- **Fixed Effects**:
 - Main effects: fixation_duration, valence, crt
 - Two-way interactions: fixation_duration×valence, fixation_duration×crt, valence×crt
 - Three-way interaction: fixation_duration×valence×crt
 - Controls: headline_length, total_fixation_duration
- **Random Effects**:
 - Random intercepts for participant_id
 - Random intercepts for headline_id

### Multiple Comparison Correction
- **Method**: Holm-Bonferroni correction
- **Scope**: Applied to ALL fixed effects (main effects, two-way interactions, three-way interaction)
- **Purpose**: Control family-wise error rate (FR-007 compliance)

### Robustness Analysis
- **Threshold Sweep**: 50ms, 100ms, 150ms fixation duration thresholds
- **Procedure**:
 1. Reset random seed to config value before each iteration
 2. Re-run preprocessing with current threshold
 3. Execute regression analysis
 4. Compute belief statistics (mean, std, range)
- **Stability Check**: Verify consistency of three-way interaction sign and significance across thresholds

## Quality Assurance

### Contract Tests
- Ingestion schema validation
- Regression output schema validation
- Robustness report schema validation

### Integration Tests
- I-VT algorithm on noisy sample data
- Coefficient recovery on synthetic data
- Threshold sweep stability verification

### Data Integrity
- All artifacts checksummed in `state/data_hashes.json`
- Runtime events logged to `state/runtime_events.json`
- Pipeline execution time tracked in `state/runtime_metrics.json`

## Limitations

1. **Dataset Constraints**: Analysis limited to available eye-tracking data; generalizability depends on sample representativeness
2. **Lexicon Coverage**: Automatic fallback to VADER when NRC coverage insufficient (logged but may introduce minor confounds)
3. **Threshold Sensitivity**: Results vary across fixation duration thresholds; stability check confirms robustness but absolute thresholds remain somewhat arbitrary
4. **Causal Inference**: While mixed-effects models control for observed confounds, unmeasured variables may still influence results

## Reproducibility

- Random seed: 42 (configurable in `code/config.yaml`)
- All code version-controlled and documented
- Synthetic data generator available for coefficient recovery testing
- Full pipeline execution time tracked and reported
