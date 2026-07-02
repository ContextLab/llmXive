---
action_items:
- id: 98d2f23b73a1
  severity: science
  text: The human evaluation protocol lacks statistical rigor. With only 5 raters
    and 58 cases, the paper reports raw win rates (e.g., 77.6%) without confidence
    intervals, p-values, or a description of the statistical test used to determine
    significance. The claim of a 'wide margin' is unsupported by inferential statistics.
- id: 269aea17b320
  severity: science
  text: The evaluation design introduces a severe confounding variable. The text admits
    baselines (Doubao/Gemini) disconnect after 2-5 minutes, causing ~50% of 'long-horizon
    memory' cases to be ungradable for baselines. The reported 77.8% win rate likely
    excludes these failures or treats them as wins without explicit statistical correction,
    invalidating the comparison.
- id: 1f035886c383
  severity: science
  text: The inter-rater reliability (IRR) is mentioned as 'high' but no quantitative
    metric (e.g., Cohen's Kappa, Fleiss' Kappa, or Krippendorff's Alpha) is provided.
    Without this, the consistency of the 'quality' and 'timing' scores across the
    5 raters cannot be verified.
- id: f90e53211c3a
  severity: science
  text: The 'timing' metric is defined as a 3-level ordinal scale (good/fair/poor)
    but is averaged with 'quality' to produce a single score. The paper does not justify
    the linearity of this scale or the validity of averaging ordinal data, which may
    distort the statistical interpretation of the results.
artifact_hash: 5266e7279b96ba8c30af6614b2b08bda02ec2220e0d4769bb56ba9df667b0fe5
artifact_path: projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T10:41:48.579266Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical analysis in Section 4 (Experiments) is insufficient to support the paper's central claims of superiority. The evaluation relies on a small sample size (5 raters, 58 cases) and reports only descriptive statistics (win/tie/loss percentages) without any inferential statistics. Specifically, there are no confidence intervals around the reported win rates (e.g., 77.6% vs 5.2%), nor are there p-values from appropriate tests (e.g., McNemar's test for paired nominal data) to establish that the observed differences are statistically significant rather than due to chance.

Furthermore, the experimental design contains a critical flaw in the 'long-horizon memory' scenario. The authors admit that baseline systems disconnect after 2-5 minutes, rendering them unable to respond to questions asked later in the stream. The paper states that "in around half of the memory cases the question we ask falls past these cutoffs and neither baseline is even present to respond, scoring nothing." It is unclear how these non-responses are handled in the win-rate calculation. If they are counted as wins for JoyAI-VL-Interaction, the metric is biased; if they are excluded, the sample size for that scenario is drastically reduced, yet the paper reports a robust 77.8% win rate without addressing the reduced statistical power or the potential selection bias.

Additionally, the paper mentions "inter-rater agreement is high" but fails to provide a standard metric such as Cohen's Kappa or Fleiss' Kappa. Given that the evaluation involves subjective judgments of "timing" and "quality," quantifying this agreement is essential to validate the reliability of the dataset. Finally, the methodology of averaging two 3-level ordinal scales (quality and timing) into a single continuous score lacks statistical justification, as ordinal data does not support arithmetic operations like averaging without specific assumptions about interval spacing. The authors must re-analyze the data with proper statistical tests, report confidence intervals, clarify the handling of baseline disconnections, and provide inter-rater reliability metrics.
