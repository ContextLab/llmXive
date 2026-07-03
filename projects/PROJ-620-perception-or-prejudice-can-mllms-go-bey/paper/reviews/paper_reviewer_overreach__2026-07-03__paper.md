---
action_items:
- id: 91675bacc522
  severity: writing
  text: The '51% ungrounded' claim (Abstract) relies on fixed thresholds. Provide
    a sensitivity range for this metric or clarify it is threshold-dependent to avoid
    over-claiming a fixed statistic.
- id: 19ebd5a79f2b
  severity: science
  text: The 'significant' -26.6% gap between Top-3 closed/open models (Sec 5.1) lacks
    a statistical significance test (e.g., t-test) for n=3 groups. Replace 'significant'
    with 'large observed' or add statistical validation.
- id: 3b62a09aebc0
  severity: writing
  text: The 'pervasive' Prejudice Gap claim (Conclusion) overgeneralizes from Western-centric,
    short-video data. Qualify the scope to the dataset's specific constraints in the
    main conclusion.
artifact_hash: 46c2ca87e5752401742be8e75f855167112497e54e4e0af681d19e8bf31d8374
artifact_path: projects/PROJ-620-perception-or-prejudice-can-mllms-go-bey/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T19:35:38.938778Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes strong claims regarding the "Prejudice Gap" and MLLM failures in grounding personality ratings. While the benchmark is rigorous, the interpretation occasionally extrapolates beyond the data's specific constraints.

First, the central statistic that "51% of correct ratings are not grounded" (Abstract, Section 5.1) is derived from the Prejudice Rate (PR) metric, which depends on specific thresholds ($\theta_1=0.5, \theta_2=0.7, \theta_3=0.5$). Although Appendix F shows model *rankings* are stable across threshold variations, the paper does not quantify how the absolute "51%" figure shifts if these cutoffs change. Presenting this as a fixed, pervasive statistic without a sensitivity range for the metric itself is an over-claim. The authors should clarify that this figure is contingent on the specific threshold choices.

Second, the claim that proprietary and open models differ "significantly" in cue retrieval with a "-26.6% gap" (Section 5.1, Conclusion) is based on the mean performance of the Top-3 models in each category. The paper does not report a statistical significance test (e.g., a t-test or confidence intervals) for the difference between these two small groups ($n=3$). Given the variance in model performance and the small sample size, asserting a "significant" difference is statistically premature. The data supports a *large observed gap*, but the statistical significance of this gap between the two populations is not established.

Finally, the conclusion characterizes the Prejudice Gap as "pervasive" (Abstract, Conclusion). While the data supports this within the specific context of the MM-OCEAN benchmark (derived from ChaLearn First Impressions V2), the dataset is limited to short, single-speaker, English videos with a known Western cultural bias (acknowledged in Appendix Ethics). Generalizing this failure mode as a universal trait of MLLMs in "human-centric roles" (Introduction) overreaches the scope of the data. The paper should temper its conclusion to reflect that this gap is pervasive *within the specific constraints of short-form, Western-centric video clips* rather than as a general law of MLLM behavior.
