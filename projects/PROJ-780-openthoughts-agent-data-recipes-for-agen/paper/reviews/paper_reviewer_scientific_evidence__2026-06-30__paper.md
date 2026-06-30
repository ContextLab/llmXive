---
action_items:
- id: 0408a2c4d529
  severity: science
  text: The claim of 'compute-controlled comparisons' for scaling curves (Fig 1) is
    not fully supported. While Table 2 (Appendix) shows a token-matched filter ablation,
    the main scaling curves (Fig 1, Fig 2) compare models trained for different epochs
    (5 vs 7) and with different gradient clipping norms (Table SFT_hp_per_scale_32b).
    This introduces a confounding variable (training duration/steps) that must be
    explicitly addressed or the claim qualified.
- id: 7eece42a54f0
  severity: science
  text: The RL section reports a 7.6 pp performance range across sources (Table 4),
    but the run-to-run reproducibility table (Table 6) shows variance of ~1.6-2.0
    pp. The paper claims gains 'exceed this variance' but does not provide statistical
    significance tests (e.g., t-tests or confidence intervals) for the differences
    between the top source (pymethods2test) and the runner-up (r2egym), which are
    separated by only ~4 pp.
- id: 38e04a7e38a9
  severity: writing
  text: The '100 ablations' claim in the abstract and introduction is vague. The text
    lists specific ablation categories (task generation, mixing, filtering, teacher,
    augmentation), but a consolidated table or count of the exact number of unique
    experimental configurations run is missing. This makes it difficult to assess
    the scope of the empirical evidence.
artifact_hash: 1762f575d6ad502232c74311f4c0e12a6d2ed21a38bf5e7d1493821d45367039
artifact_path: projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T18:23:13.896298Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a substantial empirical study on data curation for agentic models, supported by a large number of ablation experiments and a 100K dataset. However, the strength of the scientific evidence is slightly compromised by potential confounding variables in the scaling analysis and a lack of rigorous statistical validation for the RL results.

First, the central claim that the dataset exhibits "strong scaling" and outperforms alternatives in "compute-controlled comparisons" (Abstract, Fig 1) is not fully substantiated by the provided hyperparameter tables. While the authors perform a token-matched ablation for the filtering stage (Table `tab:compute_controlled_filtering`), the main scaling curves (Fig 1, Fig 2) and the comparison of different data scales (Table `tab:sft_hp_per_scale_32b`) utilize different training epochs (7 for small scales, 5 for large scales) and different gradient clipping norms. Since the total number of training steps (epochs × dataset size) varies significantly, the observed performance differences could be partially attributed to training duration rather than data quality alone. The authors should either re-run the scaling experiments with fixed total steps or explicitly acknowledge this confounding factor.

Second, the RL results (Section 5) show a performance spread of 7.6 percentage points across data sources (Table `tab:rl_data_ablation`). However, the reproducibility table (Table `tab:rl_reproducibility`) indicates a run-to-run variance of approximately 1.6–2.0 pp. The difference between the top-performing source (`pymethods2test`, 21.72 avg) and the second-best (`r2egym`, 17.42 avg) is ~4.3 pp. Without reported p-values or confidence intervals, it is difficult to determine if this gap is statistically significant or within the noise floor of the training process. The claim that "performance varies well beyond noise" is plausible but requires statistical backing to be scientifically robust.

Finally, the abstract and introduction repeatedly cite ">100 ablations." While the paper details several ablation categories (task generation, mixing, filtering, teacher models, augmentation), a consolidated summary or exact count of the unique experimental configurations is missing. Providing a clear enumeration of the ablation space would strengthen the transparency of the evidence presented.
