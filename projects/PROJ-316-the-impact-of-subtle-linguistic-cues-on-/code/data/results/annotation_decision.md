# Annotation Sample Size Decision

## Decision Summary
**Final Sample Size (N): 85**

## Power Analysis Results
- **Required Sample Size (N)**: 85
- **Source**: Based on power analysis in `data/results/power_analysis_results.yaml`
- **Effect Size (f²)**: 0.15 (medium effect, sourced from `data/results/effect_size_citation.md`)
- **Target Power**: 0.80
- **Alpha Level**: 0.05
- **Test Type**: Multiple Linear Regression (FR-011)

## Budget Assessment
- **Annotation Budget**: 150 annotated turns
- **Required N vs Budget**: 85 <= 150
- **Status**: **WITHIN BUDGET**

## Decision Logic
1. Power analysis determined a minimum sample size of N=85 is required to achieve statistical power ≥ 0.80 for detecting a medium effect size (f²=0.15) in the multiple linear regression model (FR-011).
2. The project annotation budget is set at 150 annotated turns.
3. Since 85 (required) ≤ 150 (budget), the project has sufficient resources to proceed.
4. **Decision**: Proceed with N=85 as the final annotation sample size.

## Next Steps
- Phase 0 (Data Acquisition & Annotation) may now proceed.
- Annotation protocol (T001b) and tool (T002) will be used to annotate exactly 85 turns.
- The annotation trigger (T001g) will use this N value when generating the gold standard subset.

## Gate Confirmation
- [x] Power requirements met (≥0.80)
- [x] Within annotation budget
- [x] Decision recorded
- [x] Project cleared to proceed to Phase 0

**Note**: This decision is based on the effect size documented in T000a and the power analysis executed in T000. If the actual effect size in the data differs significantly from the assumed f²=0.15, post-hoc power analysis will be conducted after data collection.

---
*Generated: Automated Decision Gate (T000b)*
*Project: PROJ-316-the-impact-of-subtle-linguistic-cues-on-*