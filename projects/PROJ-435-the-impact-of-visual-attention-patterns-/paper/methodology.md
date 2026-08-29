# Methodology

## Data Collection
This study utilizes eye-tracking data from the Dundee Eye-Tracking Corpus, a publicly available dataset containing gaze recordings from participants reading news articles. The dataset includes:
- Gaze coordinates (x, y) with timestamps
- Headline text and source attribution
- Participant identifiers
- Pre-defined Regions of Interest (ROIs) for source attribution and headline body

## Preprocessing Pipeline

### 1. Data Ingestion and Validation
Raw eye-tracking data is ingested and validated against a predefined schema requiring:
- `headline_text`
- `belief_rating`
- `cognitive_reflection_score`
- `fixation_duration`
- ROI bounding boxes (`source_attribution`, `headline_body`)

### 2. Fixation Detection
We implement the I-VT (I-VT: Identification of Fixations via Velocity Threshold) algorithm as the primary fixation detection method, with a minimum duration threshold of 100ms as per FR-001. The algorithm:
- Calculates velocity between consecutive gaze points
- Classifies points as fixations or saccades based on velocity thresholds
- Groups consecutive fixations into discrete events

### 3. ROI Mapping
Gaze points are mapped to Regions of Interest using a point-in-polygon algorithm:
- Points falling within the `source_attribution` ROI are labeled accordingly
- Points falling within the `headline_body` ROI are labeled accordingly
- Points outside defined ROIs result in trial exclusion

### 4. Participant Filtering
Participants with >20% data loss (due to missing ROIs, zero fixations, or poor data quality) are excluded from analysis. Exclusion reasons are logged in `output/exclusion_log.txt`.

## Valence Calculation

Headline valence is calculated using a two-tiered approach:
1. **Primary**: NRC Lexicon for lexical coverage assessment
2. **Fallback**: VADER Sentiment Analyzer if NRC coverage <50%

The lexicon choice is tracked as a covariate (`lexicon_used`) to control for potential confounds.

## Statistical Analysis

### Mixed-Effects Regression Model
We fit a linear mixed-effects model with the following structure:

```
belief_rating ~ fixation_duration * valence * cognitive_reflection_score
 + headline_length
 + total_fixation_duration
 + (1 | participant_id)
 + (1 | headline_id)
```

Where:
- `fixation_duration`: Total fixation duration on source attribution ROI
- `valence`: Headline sentiment score (-1 to +1)
- `cognitive_reflection_score`: Participant's CRT score
- `headline_length`: Word count of the headline
- `total_fixation_duration`: Sum of all fixation durations for the trial

### Multiple Comparison Correction
All fixed effects (main effects, two-way interactions, and three-way interaction) are corrected using the Holm-Bonferroni method to control the family-wise error rate.

### Robustness Analysis
To ensure methodological stability, we conduct a sensitivity analysis across three fixation duration thresholds (50ms, 100ms, 150ms). For each threshold:
1. Re-run the preprocessing pipeline
2. Fit the regression model
3. Extract the three-way interaction coefficient and corrected p-value
4. Verify consistency of direction and significance across thresholds

## Data Quality Assurance
- All data artifacts are checksummed (SHA-256) and recorded in `state/data_hashes.json`
- Runtime events and metrics are logged to `state/runtime_events.json` and `state/runtime_metrics.json`
- Schema validation results are stored in `state/schema_validation.json`
- Data quality reports are generated in `output/data_quality_report.csv`

## Ethical Considerations
This study uses publicly available, anonymized eye-tracking data. No personally identifiable information is collected or analyzed. All participants in the original dataset provided informed consent.
