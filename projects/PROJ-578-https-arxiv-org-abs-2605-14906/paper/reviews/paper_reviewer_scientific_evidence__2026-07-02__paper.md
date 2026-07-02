---
action_items:
- id: f614550e0cbe
  severity: science
  text: The claim that 'removing evidence images drops two frontier LVLMs below 2%
    accuracy' (Abstract, Sec 3.4) relies on a sample of n=634. While the effect size
    is massive, the paper lacks a statistical test (e.g., McNemar's test) to confirm
    this drop is significant against the baseline, especially given the binary nature
    of the metric. Please add p-values or confidence intervals for the ablation study.
- id: e92eaa41db71
  severity: science
  text: The error analysis in Sec 4.3 claims '90% of IE/KU errors are Visual' and
    '73% of MSR errors are Reasoning' based on LLM-as-Judge classification. Without
    a human-annotated gold standard for error types (only 484 items were human-verified
    for answer correctness, not error taxonomy), these percentages are subject to
    the judge's own hallucination biases. Provide inter-annotator agreement (Kappa)
    for the error classification task or a human audit of a stratified sample of these
    error labels.
- id: a53296d87ef0
  severity: science
  text: "The paper reports a correlation of \u03C1=0.62 (p=0.002) between model size\
    \ and retention (App E002). However, the sample size for this regression is small\
    \ (n=22 open-source models, but likely fewer with complete data across all lengths).\
    \ The p-value seems suspiciously precise for such a small, noisy dataset. Please\
    \ report the exact N used for the regression and the 95% confidence interval for\
    \ the correlation coefficient to assess robustness."
artifact_hash: 894b3a058a7c60576126fae0e86fbf0afb5e6919dad970b01a23558253a18ccf
artifact_path: projects/PROJ-578-https-arxiv-org-abs-2605-14906/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:52:13.887307Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a substantial empirical contribution with a well-constructed benchmark (789 questions) and a rigorous data curation pipeline. The central claim—that current LVLMs and memory agents fail to jointly handle multimodal long-term memory—is supported by the main results tables (Tables 3, 4, and Appendix Tables). The image-ablation study (Table 2) provides strong evidence for the necessity of visual grounding, showing a catastrophic drop in performance when images are removed.

However, the statistical rigor of the supporting analyses requires strengthening. First, the ablation study in Section 3.4 and Table 2 reports a drop to <2% accuracy but does not provide statistical significance testing (e.g., McNemar's test for paired proportions) to formally reject the null hypothesis that the drop is due to chance, although the effect size is intuitively large. Second, the detailed error analysis in Section 4.3 (e.g., "90% of IE/KU errors are Visual") relies entirely on an LLM-as-Judge classifier for error taxonomy. While the paper validates the judge for *answer correctness* (κ=0.86 vs. human), it does not validate the judge's ability to *categorize error types*. Without a human-annotated gold standard for error classification or an inter-annotator agreement score for the error taxonomy, these specific percentages are potentially biased by the judge's own reasoning patterns. Finally, the scaling analysis in Appendix E002 reports a correlation (ρ=0.62, p=0.002) based on a small sample of models; reporting the exact N and confidence intervals for this correlation would improve the robustness of the claim regarding model size.

The evidence is strong enough to support the paper's main conclusions, but the secondary statistical claims need formal validation to rule out spurious correlations or judge bias.
