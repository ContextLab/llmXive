---
action_items:
- id: 10c8e6afd818
  severity: science
  text: Report statistical significance (e.g., p-values, confidence intervals, or
    standard deviations) for the reported improvements on MMAU (58.15 vs 57.81) and
    CoVoST2 (+15.72 BLEU). Single-point averages without variance estimates make it
    impossible to assess if gains are robust or due to random seed variance.
- id: 439a3fb66c87
  severity: science
  text: Clarify the statistical methodology for the 'Proactive-Sound-Bench' results.
    With 644 events, report the 95% confidence intervals for the Single (61.2) and
    Multi (62.8) tier accuracies. Additionally, specify if the 'human-designed' events
    were evaluated by multiple annotators and report inter-annotator agreement (e.g.,
    Cohen's kappa) to validate the ground truth labels.
- id: 02a1fccf24c4
  severity: science
  text: 'The ablation study (Table 4) presents performance differences (e.g., V2 vs
    V5 on Trigger Acc: 92.42% vs 96.77%) as absolute facts. Include standard deviations
    or results from multiple random seeds to demonstrate that these improvements are
    statistically significant and not artifacts of a specific initialization or data
    split.'
artifact_hash: d722b827ffcc42ef33cad3308518a181a01c5d135cbbac51efaf0289e64033d0
artifact_path: projects/PROJ-666-https-arxiv-org-abs-2606-05121/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T00:12:09.510973Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a novel framework for streaming audio interaction, but the statistical rigor of the empirical evaluation requires strengthening to support the claims of superiority and robustness.

First, the primary results in Table 1 (MMAU) and Table 3 (CoVoST2) report single-point averages (e.g., 58.15 vs 57.81 on MMAU; +15.72 BLEU gain on CoVoST2). In deep learning benchmarks, performance can vary significantly based on random seeds, data shuffling, or evaluation stochasticity. Without reporting standard deviations, confidence intervals, or p-values from significance tests (e.g., paired t-tests or bootstrap resampling), it is impossible to determine if the observed improvements are statistically significant or within the margin of error. The claim that the model "surpasses" baselines is currently unsupported by statistical evidence.

Second, the evaluation of the new **Proactive-Sound-Bench** (Section 5.2, Table 5) relies on 644 human-designed events. While the sample size is reasonable, the paper does not detail the statistical validation of the ground truth. Were these events annotated by multiple human raters? If so, what is the inter-annotator agreement (e.g., Cohen's kappa)? Without this, the reported accuracy (61.2% / 62.8%) may reflect label noise rather than model capability. Furthermore, confidence intervals for these accuracy metrics are missing, making it difficult to assess the precision of the benchmark results.

Third, the ablation studies (Tables 4 and 5) attribute performance changes to specific components (e.g., TFJP preprocessing, chunk size). However, these tables present results from single runs. To validate the necessity of components like the dual-loss weight $\lambda$ or the FIFO scheduler, the authors should report results averaged over multiple seeds with variance. For instance, the drop in MMAU from 58.3 to 57.3 when $\lambda=2.0$ (Table 5) needs to be shown as a statistically significant degradation, not just a point estimate difference.

Finally, the "Real-World Validation" in the Appendix reports a correlation of 0.91 between synthetic and real-world silence rates. While this is a strong correlation, the sample size (2 hours of audio) and the lack of a formal statistical test (e.g., Pearson correlation significance) weaken the claim of generalization. A more robust statistical analysis of the variance in real-world performance across the four scenarios (Travel, Work, Home, Commute) is needed.
