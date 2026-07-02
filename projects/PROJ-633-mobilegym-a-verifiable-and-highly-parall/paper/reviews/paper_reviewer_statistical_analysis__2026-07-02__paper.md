---
action_items:
- id: d68fbcd4989b
  severity: science
  text: "In Table 1 (Main Results), standard deviations are reported for some models\
    \ (e.g., Gemini 3.1 Pro: \xB11.4) but not others (e.g., Doubao-Seed-2.0-Pro).\
    \ Clarify if the latter are single-run results and justify the lack of variance\
    \ reporting for the primary baselines to ensure statistical comparability."
- id: ff73237480e0
  severity: science
  text: The Sim-to-Real transfer claim (95.1% gain retention) relies on a small subset
    of 59 tasks. Report confidence intervals or a statistical test (e.g., paired t-test
    or bootstrap) for the difference between simulation gain (+42.8 pt) and real-device
    gain (+40.7 pt) to validate the 'retention' metric.
- id: 48ae62bfc63a
  severity: writing
  text: The difficulty stratification (L1-L4) is calibrated using 8 reference models,
    but the specific models and their performance distributions are not fully detailed
    in the main text. Provide the full list of reference models and their mean SRs
    in the appendix to verify the robustness of the strata boundaries.
artifact_hash: a548124f155c8c790b0f8380f840762b6a4c9bd7b88cafb98ce50a865152c78b
artifact_path: projects/PROJ-633-mobilegym-a-verifiable-and-highly-parall/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T08:11:58.234903Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the paper is generally sound in its presentation of point estimates and diagnostic metrics, but it lacks necessary rigor in variance reporting and significance testing for its key empirical claims.

First, regarding the benchmark results in **Table 1 (Main Results)**, there is an inconsistency in the reporting of uncertainty. The proprietary model "Gemini 3.1 Pro" includes a standard deviation ($\pm 1.4$), while other models like "Doubao-Seed-2.0-Pro" and "Qwen3.6-Plus" do not. The footnote mentions that $\dagger$ marks single-run results, but it is unclear if the non-daggered open-source models were also single-run or if the variance was simply omitted. For a fair statistical comparison of model performance, especially when differences are small (e.g., 13.8% vs 15.4%), the absence of variance estimates for the majority of baselines weakens the statistical validity of the ranking. The authors should either report standard deviations for all models (via multiple seeds) or explicitly state which are single-run and treat the others as such in the discussion.

Second, the central claim of **Sim-to-Real transfer** (Section 4.2, **Table 3** and **Figure 3**) relies on a comparison of gains: simulation gain of +42.8 pt versus real-device gain of +40.7 pt, resulting in a "95.1% retained gain." This calculation is based on a subset of only **59 tasks** (the "signal-bucket"). While the point estimates are close, the paper does not provide a statistical test (e.g., a paired t-test or a bootstrap confidence interval) to determine if the difference between the simulation gain and the real-device gain is statistically significant. Given the small sample size (n=59) and the inherent noise in real-device execution, claiming "95.1% retention" as a definitive metric without a confidence interval is statistically premature. The authors should provide a 95% confidence interval for the difference in gains to support the claim that the transfer is robust.

Finally, the **difficulty stratification** (L1-L4) described in Section 3.4 is calibrated using 8 reference models. While the appendix mentions a sensitivity check with 4 models, the main text does not list the specific 8 models used for the primary calibration. To ensure the reproducibility of the difficulty levels and the validity of the stratification, the full list of reference models and their individual performance distributions should be explicitly provided in the appendix or a supplementary table. This is crucial for verifying that the strata boundaries (e.g., L1 $\ge$ 75%) are not artifacts of a specific model selection bias.
