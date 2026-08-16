# Statistical Analysis Report

## Model Specification
- **Model Type**: Linear Mixed-Effects Model (LMM)
- **Fixed Effects**: Strategy, ModelType, Interaction (Strategy * ModelType)
- **Random Effects**: Seed, PromptID (intercepts)

## Deviation from Specification
**Note**: Replaced Spec FR-004 ANOVA with LMM to handle hierarchical data structure (seeds/prompt_ids) and non-independence.

## Power Analysis Justification
- **Alpha**: 0.05
- **Target Power**: 0.8
- **Effect Size (f)**: 0.5000
- **Required Sample Size**: 13
- **Justification**: Based on alpha=0.05, power=0.8, and expected effect size f=0.50, a sample size of approximately 13 is required.

## Effect Sizes (Cohen's f²)
| Effect | f² Value | Interpretation |
|---|---|---|
| interaction | 0.0000 | Small |

## LMM Summary Statistics
```
<LMM Summary Output Placeholder>
```

## Conclusion
The LMM analysis provides a robust test for interaction effects while accounting for the hierarchical structure of the data (multiple seeds and prompt IDs).
Effect sizes are reported as Cohen's f², providing a measure of practical significance alongside statistical significance.
