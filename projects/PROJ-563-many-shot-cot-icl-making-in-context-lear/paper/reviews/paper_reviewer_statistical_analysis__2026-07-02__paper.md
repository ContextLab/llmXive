---
action_items:
- id: 75aad38f9b18
  severity: science
  text: In Section 4.2 (Principle 1), the claim that self-generated CoTs outperform
    ground-truth CoTs relies on visual inspection of Figures 3 and 4. The text must
    explicitly report the statistical significance (e.g., p-values from paired t-tests
    or bootstrap confidence intervals) of these differences to rule out random variance,
    especially given the small number of seeds (n=5) mentioned in Appendix B.
- id: 188edc45dfe6
  severity: science
  text: Section 4.3 reports Pearson correlation coefficients (e.g., r=-0.547) between
    curvature and accuracy. The manuscript must provide the corresponding p-values
    and confidence intervals for these correlations to establish that the observed
    relationships are statistically significant and not artifacts of the specific
    random permutations sampled.
- id: eeee01fa5474
  severity: science
  text: Table 3 and Table 4 report mean and standard deviation across five random
    seeds. For the CDS method, which is deterministic given a set, the variance should
    ideally be reported across multiple random *initializations* of the TSP heuristic
    or multiple random *subsets* of demonstrations, rather than just the ordering
    seeds used for the baseline. Clarify the source of variance for the CDS results.
- id: bacd0af315e5
  severity: science
  text: The 'High-curvature control' experiment in Section 5.1 compares CDS against
    a high-curvature baseline. The text claims CDS 'consistently outperforms' this
    baseline. A formal statistical test (e.g., paired t-test across tasks/models)
    should be reported to confirm that the observed gains (e.g., the 5.42 pp gain
    mentioned in the abstract) are statistically significant and not due to chance.
artifact_hash: da80d19d18126d829231e022c90784234c941daee73db4750a219950884e0e6f
artifact_path: projects/PROJ-563-many-shot-cot-icl-making-in-context-lear/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:15:32.565822Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in this paper is generally sound in its experimental design, particularly the use of multiple random seeds (n=5) to assess order sensitivity and the inclusion of standard deviation in the results tables (Appendix B, Tables 1-3). However, the manuscript relies heavily on visual trends and point estimates without providing formal statistical significance testing for its key claims.

First, in Section 4.2, the conclusion that "self-generated demonstrations consistently outperform dataset-provided CoTs" is drawn from Figures 3 and 4. While the trends are visible, the text does not report p-values or confidence intervals for these differences. Given the small sample size (5 seeds), it is crucial to verify that the observed performance gaps (e.g., the ~3-5% gains) are statistically significant and not within the margin of error. The authors should perform paired t-tests or bootstrap resampling on the seed-level results to support these claims.

Second, Section 4.3 introduces a correlation analysis between embedding curvature and accuracy, reporting specific Pearson coefficients (e.g., r = -0.547). While the direction of the correlation is informative, the manuscript omits the associated p-values and confidence intervals. Without these, it is impossible to determine if the correlation is statistically distinguishable from zero, especially given the limited number of random permutations used to generate the data points.

Finally, the ablation study in Section 5.1 (Table 4) compares CDS against a high-curvature baseline. The text asserts that CDS "consistently outperforms" this baseline. To substantiate this, the authors should report the results of a statistical test (e.g., a paired t-test across the different tasks and models) to confirm that the improvements are significant. The current presentation of mean values alone is insufficient to rule out random variation, particularly for the smaller gains observed in some settings. Adding these statistical validations would significantly strengthen the empirical claims.
