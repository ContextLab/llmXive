# Research: Visual Detail and False Memory Susceptibility

## Executive Summary

This research investigates the relationship between visual scene complexity/detail and the susceptibility to false memories. Using a modified misinformation paradigm with visual stimuli, we hypothesize that increased visual detail may either increase false alarms (due to source confusion) or decrease them (due to stronger encoding), depending on the specific nature of the detail. The study relies on open-source data (COCO 2017 as a verified substitute for Visual Genome) and a web-based participant interface.

## Dataset Strategy

### Primary Dataset: COCO 2017 (Verified Open Substitute)

* **Source**: Hugging Face Datasets (`coco`).
* **URL**: ` (Verified open source).
* **Rationale**: The input block contained a URL for numerical data, not visual scenes. Visual Genome is not available via a verified open URL in the input block. COCO 2017 is selected as the verified open substitute because it provides scene images and object annotations suitable for complexity calculation and manipulation.
* **Constraint**: The "Complexity Score" metric is recalibrated for COCO's annotation density.

### Dataset Variable Fit (SC-004)

| Required Variable | Source (COCO) | Availability | Status |
|:--- |:--- |:--- |:--- |
| **Image Data** | `image` field | Yes | ✅ |
| **Object Annotations** | `annotations` (bounding boxes) | Yes | ✅ |
| **Complexity Score** | Derived (Object Count / Density) | Calculated (Recalibrated) | ✅ |
| **False Memory Outcome** | Participant Response | Generated | ✅ |

### Complexity Stratification & Calibration

To satisfy FR-001 (varied baseline complexity scores spanning ≥3 quantile bins, Q1-Q3 range ≥0.3):
1. **Batch Download**: Download a large batch of COCO images.
2. **Density Calculation**: Calculate object density (number of bounding boxes / image area) for each.
3. **Filtering**: Sort by density and select images that span the 25th, 50th, and 75th percentiles to ensure the Q1-Q3 range ≥0.3.
4. **Annotation Density Check**: Verify that each selected image has at least 5 distinct object categories. If not, skip the image.

### Manipulation Algorithm (FR-002)

To ensure the "detail" variable is controlled and not random:
1. **Object Selection**: Identify "minor objects" (bounding box area < 5% of image area).
2. **Enhanced Detail**: Add a few minor objects from a verified "minor object library" (e.g., small tools, cups) using compositing. Selection is deterministic based on a seed.
3. **Reduced Detail**: Blur or remove minor objects matching the "minor" criteria.
4. **Semantic Coherence Control**: Ensure added/removed objects are semantically plausible (co-occurring in the same ImageNet class) to distinguish "detail" effects from "confusion" effects.

### Lure Generation Logic (FR-004)

To ensure false details are "items that never appeared in baseline image":
1. **Extract Baseline**: Get all object labels present in the baseline image.
2. **Select Lure**: Choose a lure object from a global pool that is NOT in the baseline list.
3. **Plausibility Check**: Verify the lure is semantically plausible (e.g., 'cup' in a kitchen) using WordNet.
4. **Enforcement**: The question generator dynamically filters the global pool against the specific baseline's metadata.

## Statistical Methodology

### Experimental Design

**Within-Subjects (Repeated Measures)**:
- Each participant views a set of baseline images.
- For half the set, they are tested on the "Enhanced" version's details.
- For the other half, they are tested on the "Reduced" version's details.
- **Factor**: `detail_condition` (Enhanced vs. Reduced) is a within-subjects factor.
- **Justification**: This design allows the use of Repeated-Measures ANOVA, controlling for individual differences in memory ability.

### Power Analysis (SC-002)

* **Method**: A priori power analysis for repeated-measures ANOVA.
* **Parameters**:
 * Effect Size (f): A medium effect size, based on visual memory literature. **Sensitivity Analysis**: Test a range of values to ensure robustness.
 * Alpha (α): a conventional significance threshold.
 * Power (1-β): Sufficient statistical power to detect the effect of interest.
 * Correlation among repeated measures: moderate.
* **Target Sample**: N ≥ 50 participants (as per spec).
* **Verification**: The `code/analysis/stats.py` script will output the calculated power for the actual N achieved. If N < 50, the report will explicitly flag "Underpowered".
* **Blocking Gate**: This analysis must run before Phase 2 (Participant Interface).

### Hypothesis Testing (FR-005, FR-006)

* **Test**: Repeated-measures ANOVA (within-subjects factor: `detail_condition` [enhanced vs. reduced]).
* **Dependent Variable**: False Alarm Rate (proportion of "Yes" responses to lure items).
* **Covariate**: `complexity_score` (continuous) to control for baseline complexity.
* **Correction**: Bonferroni correction applied if multiple comparisons are made (e.g., comparing Enhanced vs. Baseline AND Reduced vs. Baseline).
* **Assumptions**:
 * **Observational**: The study is observational regarding the "detail" variable (manipulated, but not randomized across participants in a causal trial of nature). Claims are framed as "association between detail level and false memory rate."
 * **Collinearity**: Complexity metrics (object count vs. texture) are correlated. We will report descriptive correlations and avoid claiming independent effects of each without variance inflation factor (VIF) analysis.

### Data Handling
* **Missing Data**: Participants with < 80% completion will be excluded from the primary analysis but logged in `data/logs/dropouts.log`.
* **Outliers**: Responses with reaction times < 200ms (guessing) will be flagged.

## Ethical Considerations (Constitution VI)

* **IRB**: The system includes a placeholder for IRB approval number in `data/ethics/consent_template.md`. No data collection begins without this field populated.
* **Consent**: Mandatory 5-minute reading time enforced in `code/interface/consent.py` via a JavaScript timer in the Streamlit app that prevents the "Start" button from being clickable until 5 minutes have elapsed.
* **PII**: Participant IDs are hashed using SHA-256 with a salt stored separately. No names or emails stored in `data/responses/`.

## Limitations

* **Dataset Substitution**: Due to the lack of a verified Visual Genome URL in the input block, COCO 2017 is used. This may alter the "complexity" distribution compared to the original spec intent. The "Complexity Score" is recalibrated for COCO.
* **Compute**: Analysis is CPU-bound. Large-scale simulations (>1000 participants) are not feasible on the free tier; the study is capped at ~-100 sessions.
* **Generalizability**: Results apply to the specific stimuli set (COCO scenes) and may not generalize to all visual domains.
* **Mock Fallback**: The "Mock Generator" is strictly a prototype fallback. Final analysis requires real data (COCO). Results from mock runs will be flagged as "Pilot Only".