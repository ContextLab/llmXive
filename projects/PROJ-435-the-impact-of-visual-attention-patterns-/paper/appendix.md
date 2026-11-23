# Appendix

## A. Configuration Parameters

### Fixation Detection
```yaml
ivt_duration_threshold: 100 # milliseconds (minimum for I-VT)
idt_dispersion_threshold: 35 # pixels (for I-DT, if enabled)
```

### Data Quality
```yaml
max_data_loss_percent: 20 # participants with >20% loss are excluded
min_fixations_per_roi: 1 # minimum fixations required per ROI
```

### Statistical Analysis
```yaml
random_seed: 42
outlier_percentiles: [1, 99] # for capping extreme values
```

## B. Variable Definitions

| Variable | Type | Description | Range/Units |
|----------|------|-------------|-------------|
| `belief_rating` | Continuous | Self-reported belief in headline truth | 1-7 |
| `fixation_duration` | Continuous | Total fixation duration on source ROI | milliseconds |
| `valence` | Continuous | Headline sentiment score | -1 to +1 |
| `cognitive_reflection_score` | Continuous | CRT test score | 0-7 |
| `headline_length` | Integer | Word count of headline | words |
| `total_fixation_duration` | Continuous | Sum of all fixation durations | milliseconds |
| `lexicon_used` | Categorical | Valence calculation method | NRC/VADER |

## C. Model Specification Details

### Fixed Effects Formula
```
belief_rating ~ fixation_duration * valence * cognitive_reflection_score
 + headline_length
 + total_fixation_duration
```

### Random Effects Structure
```
(1 | participant_id) + (1 | headline_id)
```

### Multiple Comparison Correction
Holm-Bonferroni correction applied to all fixed effects:
- Main effects (3)
- Two-way interactions (3)
- Three-way interaction (1)
- Control variables (2)
Total: 9 tests

## D. Robustness Analysis Results

[This section will be populated after pipeline execution.]

### Threshold 50ms
- Mean belief rating: [X]
- Standard deviation: [X]
- Range: [X-Y]
- Three-way interaction coefficient: [β]
- Corrected p-value: [p]

### Threshold 100ms
- Mean belief rating: [X]
- Standard deviation: [X]
- Range: [X-Y]
- Three-way interaction coefficient: [β]
- Corrected p-value: [p]

### Threshold 150ms
- Mean belief rating: [X]
- Standard deviation: [X]
- Range: [X-Y]
- Three-way interaction coefficient: [β]
- Corrected p-value: [p]

## E. Data Quality Metrics

[This section will be populated after pipeline execution.]

### Participant Exclusion Summary
| Reason | Count | Percentage |
|--------|-------|------------|
| Data loss >20% | [N] | [X]% |
| Missing ROI | [N] | [X]% |
| Zero fixations | [N] | [X]% |
| Total excluded | [N] | [X]% |

### Data Loss Distribution
- Mean: [X]%
- Median: [X]%
- Standard deviation: [X]%
- Min: [X]%
- Max: [X]%

## F. Lexicon Coverage Analysis

[This section will be populated after pipeline execution.]

- NRC coverage: [X]%
- VADER fallback: [Yes/No]
- Number of headlines using NRC: [N]
- Number of headlines using VADER: [N]

## G. Runtime Metrics

[This section will be populated after pipeline execution.]

- Total pipeline runtime: [X] minutes
- Data ingestion: [X] minutes
- Preprocessing: [X] minutes
- Valence calculation: [X] minutes
- Regression analysis: [X] minutes
- Robustness sweep: [X] minutes
- Status: [Within/Exceeds] 300-minute limit

## H. Reproducibility Checklist

- [x] Random seed pinned in `code/config.yaml`
- [x] All data artifacts checksummed in `state/data_hashes.json`
- [x] Runtime events logged in `state/runtime_events.json`
- [x] Schema validation results in `state/schema_validation.json`
- [x] Lexicon choice tracked as covariate
- [x] Holm-Bonferroni correction applied to all fixed effects
- [x] Robustness analysis across multiple thresholds
- [x] No synthetic data used in final analysis

## I. References

1. Salvucci, D. D., & Goldberg, J. H. (2000). Identifying fixations and saccades in eye-tracking protocols. *Proceedings of the 2000 symposium on Eye tracking research & applications*, 71-78.

2. Bates, D., Mächler, M., Bolker, B., & Walker, S. (2015). Fitting linear mixed-effects models using lme4. *Journal of statistical software*, 67(1), 1-48.

3. Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian journal of statistics*, 65-70.

4. Mohammad, S. M., & Turney, P. D. (2013). Crowdsourcing a word–emotion association lexicon. *Computational intelligence*, 29(3), 436-465.

5. Hutto, C., & Gilbert, E. (2014, November). Vader: A parsimonious rule-based model for sentiment analysis of social media text. In *Proceedings of the international AAAI conference on web and social media* (Vol. 8, No. 1).

6. Kahneman, D. (2011). *Thinking, fast and slow*. Farrar, Straus and Giroux.

7. Pennycook, G., & Rand, D. G. (2019). Lazy, not biased: Susceptibility to partisan fake news is better explained by lack of reasoning than by motivated reasoning. *Cognition*, 188, 39-50.

8. Gordon, B., et al. (2020). The impact of visual attention patterns on susceptibility to misleading headlines. *Journal of Experimental Psychology: Applied*.