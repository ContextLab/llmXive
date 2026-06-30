---
action_items:
- id: 7cd387ee6269
  severity: science
  text: The statistical analysis in Section 4 (Experiments) is insufficient to support
    the strong claims of superiority made in the abstract and conclusion. The primary
    issue is the treatment of the human evaluation data. The paper reports aggregate
    win rates (77.6% vs Doubao, 87.9% vs Gemini) derived from 58 cases rated by 5
    raters. However, no confidence intervals are provided for these proportions, nor
    is there a statistical significance test (such as a binomial test or a permutation
    test) to determi
artifact_hash: 5266e7279b96ba8c30af6614b2b08bda02ec2220e0d4769bb56ba9df667b0fe5
artifact_path: projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T08:11:09.760754Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical analysis in Section 4 (Experiments) is insufficient to support the strong claims of superiority made in the abstract and conclusion. The primary issue is the treatment of the human evaluation data. The paper reports aggregate win rates (77.6% vs Doubao, 87.9% vs Gemini) derived from 58 cases rated by 5 raters. However, no confidence intervals are provided for these proportions, nor is there a statistical significance test (such as a binomial test or a permutation test) to determine if these margins are distinguishable from chance or a 50/50 split given the sample size. With only 58 total comparisons, the margin of error is substantial, and presenting a single point estimate as definitive evidence of a "wide margin" is statistically unsound.

Furthermore, the construction of the evaluation metric is problematic. The authors average two axes—quality and timing—each rated on a 3-level ordinal scale (good, fair, poor). Averaging ordinal categories assumes equal intervals between "good," "fair," and "poor," which is a strong and unverified assumption. A more robust approach would be to treat the ratings as ordinal and use non-parametric tests for paired data (e.g., Wilcoxon signed-rank test) to compare the distributions of scores between JoyAI-VL-Interaction and the baselines.

A critical confounding factor is identified in the "Long-horizon memory" scenario. The paper admits that the baselines (Doubao and Gemini) automatically disconnect after 5 and 2.25 minutes, respectively, leading to a "score nothing" outcome for questions asked after these cutoffs. Including these structural disconnections as "losses" for the baselines inflates the win rate of JoyAI-VL-Interaction without necessarily proving superior *reasoning* or *timing* capabilities within the active session window. The analysis fails to disentangle "system availability" from "model performance." A sensitivity analysis excluding cases where baselines timed out, or a separate reporting of "availability" vs. "response quality," is necessary to validate the claim that the interaction model paradigm is superior.

Finally, while the authors state that "inter-rater agreement is high," they provide no quantitative measure (e.g., Krippendorff's alpha or Fleiss' kappa). Given the subjective nature of evaluating "timing" in a streaming context, establishing the reliability of the human labels is a prerequisite for any statistical claim. Without these metrics, the validity of the ground truth used to calculate win rates remains unverified.
