# Results

## Data Quality Summary
[This section will be populated after pipeline execution.]

### Participant Exclusion
- Total participants: [N]
- Excluded participants: [N] ([X]%)
- Primary exclusion reasons: [Data loss >20%, Missing ROI, Zero fixations]

### Data Loss Analysis
- Mean data loss: [X]%
- Standard deviation: [X]%
- Distribution of data loss across participants: [Histogram/summary]

## Valence Calculation
[This section will be populated after pipeline execution.]

### Lexicon Usage
- NRC coverage: [X]%
- Lexicon switch (NRC → VADER): [Yes/No]
- Reason for switch: [Coverage <50%]

## Regression Analysis

### Model Fit Statistics
[This section will be populated after pipeline execution.]

- Fixed effects: [Number]
- Random effects: [Participants, Headlines]
- AIC: [Value]
- BIC: [Value]
- Log-likelihood: [Value]

### Fixed Effects Coefficients
[Table will be generated from `data/derived/regression_results.csv`]

| Term | Coefficient | SE | t-value | p-value (raw) | p-value (adj) | CI (95%) |
|------|-------------|----|---------|---------------|---------------|----------|
| Intercept | [β] | [SE] | [t] | [p] | [p_adj] | [CI] |
| fixation_duration | [β] | [SE] | [t] | [p] | [p_adj] | [CI] |
| valence | [β] | [SE] | [t] | [p] | [p_adj] | [CI] |
| cognitive_reflection_score | [β] | [SE] | [t] | [p] | [p_adj] | [CI] |
| fixation_duration:valence | [β] | [SE] | [t] | [p] | [p_adj] | [CI] |
| fixation_duration:cognitive_reflection_score | [β] | [SE] | [t] | [p] | [p_adj] | [CI] |
| valence:cognitive_reflection_score | [β] | [SE] | [t] | [p] | [p_adj] | [CI] |
| fixation_duration:valence:cognitive_reflection_score | [β] | [SE] | [t] | [p] | [p_adj] | [CI] |
| headline_length | [β] | [SE] | [t] | [p] | [p_adj] | [CI] |
| total_fixation_duration | [β] | [SE] | [t] | [p] | [p_adj] | [CI] |

### Key Finding: Three-Way Interaction
[This section will be populated after pipeline execution.]

The three-way interaction term (`fixation_duration:valence:cognitive_reflection_score`) was [significant/not significant] (β = [value], p_adj = [value], 95% CI: [lower, upper]).

**Interpretation**: [Will be generated based on coefficient sign and significance. Example: "For participants with higher cognitive reflection scores, the effect of fixation duration on belief rating is more strongly moderated by headline valence."]

## Robustness Analysis

### Threshold Sensitivity
[This section will be populated after pipeline execution.]

| Threshold (ms) | Mean Belief Rating | Std Dev | Range | Three-Way β | p_adj |
|----------------|-------------------|---------|-------|-------------|-------|
| 50 | [X] | [X] | [X-Y] | [β] | [p] |
| 100 | [X] | [X] | [X-Y] | [β] | [p] |
| 150 | [X] | [X] | [X-Y] | [β] | [p] |

### Stability Assessment
[This section will be populated after pipeline execution.]

- **Direction Consistency**: [Consistent/Inconsistent] across thresholds
- **Significance Consistency**: [Consistent/Inconsistent] across thresholds
- **CI Overlap**: [Summary of confidence interval overlap]

## Causal Framing Statement
[This section will be populated from `output/causal_framing_statement.txt`]

[The causal framing statement will describe the nature of the three-way interaction effect, its statistical significance, and its practical implications for understanding how visual attention, headline valence, and cognitive reflection jointly influence belief formation.]
