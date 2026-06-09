---
action_items:
- id: 6ca2a2850101
  severity: science
  text: Report confidence intervals or statistical significance tests (e.g., paired
    t-tests, bootstrapping) for the accuracy comparisons in Table 2 to validate the
    claimed 'substantial improvements' over baselines.
- id: d223306d4051
  severity: science
  text: Explicitly state the number of test samples (N) for each benchmark in Section
    4.1 to allow assessment of statistical power, particularly for the 'Avg Gap' metric.
- id: dfe4b2aa5aab
  severity: science
  text: Address multiple-comparisons correction in the recipe ablation study (Table
    2) where 8 DPO variants are compared to select the best performing recipe.
- id: e098be9a641c
  severity: science
  text: Quantify the reliability of the GPT-5.4 judge used for parsing free-form outputs
    (e.g., inter-judge agreement or calibration against human labels) to ensure evaluation
    noise does not obscure small effects.
artifact_hash: e83058c54d1a49095166f0ef2ff7177a4db8d52f3626563ad7ae59fa949315e9
artifact_path: projects/PROJ-610-https-arxiv-org-abs-2605-16403/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T10:28:43.884927Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis framework is conceptually sound, employing counterfactual interventions to measure the "Clever Hans" effect. However, the reporting of quantitative results lacks necessary statistical rigor to support the strength of the claims.

First, Table 2 compares eight different alignment recipes. The selection of the "Ours" recipe based on the highest average accuracy (63.3%) does not account for multiple comparisons. Without correction (e.g., Bonferroni or Holm-Bonferroni), there is an elevated risk of Type I error in claiming the best recipe is superior to others like "DPO w/ CTP + FV-D + FV-A" (62.6%).

Second, Table 1 and Table 2 report point estimates of accuracy without confidence intervals or standard deviations. While the gap between Qwen3-Omni (34.3%) and "Ours" (83.1%) on Sync is large, the smaller margins between DPO variants (e.g., 62.7% vs 62.6%) are not statistically distinguishable without variance estimates. Please report 95% confidence intervals calculated via bootstrapping or multiple evaluation seeds.

Third, the evaluation relies on a GPT-5.4 judge to parse free-form model outputs into discrete labels (Appendix \ref{app:prompts}). The variance introduced by the LLM judge is not quantified. If the judge agreement is low, it adds noise to the accuracy metrics, potentially masking real model improvements. A calibration study against human annotations is recommended.

Finally, the sample sizes for the test sets (e.g., VGGSoundSync, Video-MME) are not explicitly stated in the main text. The "Avg Gap" calculation assumes equal weighting across dimensions, but if sample counts vary significantly across Shift, Mute, and Swap, the metric may be biased. Please clarify $N$ for each diagnostic condition.

These additions are critical to ensure the reported gains reflect genuine model capabilities rather than sampling variance or evaluation noise.
