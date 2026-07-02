---
action_items:
- id: 3c3248b0f746
  severity: science
  text: The evaluation relies exclusively on LLM judges (Gemini 3.1 Pro, GPT 5.5)
    without human validation or inter-rater reliability metrics. Given the paper's
    central claim that 'coherent single-category data' outperforms diverse data, a
    human study is required to rule out LLM-specific biases in scoring text-centric
    or portrait generation.
- id: f1a668732a68
  severity: science
  text: The ablation studies (Tables 1, 3, 4) report single-point scores without standard
    deviations or confidence intervals. With only 2,000 training iterations and specific
    data subsets, the reported performance differences (e.g., 3.56 vs 3.42) may not
    be statistically significant. Please report variance across multiple seeds or
    runs.
- id: 2d2d4fa84135
  severity: science
  text: The claim that 'text-centric-only' data degrades performance (Section 3.2)
    is counterintuitive. The paper attributes this to 'optimization difficulties'
    but provides no diagnostic evidence (e.g., loss curves, gradient norms, or score-field
    mismatch visualizations) to substantiate this mechanism over alternative explanations
    like data quality issues.
artifact_hash: ef29d0b509020dc2bf22b6e0953f434542633c46b7e7799f4b44106c7971c335
artifact_path: projects/PROJ-662-https-arxiv-org-abs-2606-03746/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T03:59:39.543276Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling empirical study on the training recipes for few-step distillation of visual generative models, specifically focusing on data composition, teacher guidance, and task mixture. The central thesis—that the training pipeline matters as much as the distillation objective—is well-motivated and supported by a series of ablation studies. However, the strength of the scientific evidence is currently limited by the evaluation methodology and the lack of statistical rigor in the reported results.

First, the evaluation protocol relies entirely on LLM-based judges (Gemini 3.1 Pro and GPT 5.5) for both T2I-Bench and Editing-Bench. While the system prompts are detailed (Appendix), the absence of human evaluation or inter-rater reliability metrics is a significant weakness. The paper's most surprising finding (Takeaway 1 & 2) is that training on a single coherent category (e.g., landscapes) yields better text-centric generation than training on text-centric data. This counterintuitive result is highly susceptible to LLM judge bias, as these models may have specific preferences for certain visual styles or may struggle to evaluate text rendering in generated images consistently. Without human validation, it is difficult to rule out that the observed "superiority" of single-category training is an artifact of the evaluator rather than a genuine improvement in model capability.

Second, the statistical robustness of the findings is unclear. The tables (e.g., Table 1, Table 3, Table 4) present single scalar scores for each configuration. There is no mention of standard deviations, confidence intervals, or results from multiple random seeds. Given that the training involves stochastic optimization (AdamW) and the datasets are relatively small (20k prompts per category), the observed differences in average scores (e.g., 3.56 vs 3.42 in Table 1) may not be statistically significant. The paper claims "non-obvious behaviors" and "decisive" roles for task mixtures, but without variance estimates, these claims are not fully supported by the evidence.

Finally, the explanation for the failure of text-centric-only training (Section 3.2) is somewhat speculative. The authors attribute the degradation to "optimization or distributional difficulties" and "score-field mismatch." While plausible, the paper does not provide diagnostic evidence such as training loss curves, gradient norms, or visualizations of the score field mismatch to substantiate this mechanism. Providing such evidence would strengthen the causal link between the data composition and the observed performance drop.

In summary, while the empirical observations are interesting and the proposed method (Qwen-Image-Flash) appears effective, the scientific evidence requires strengthening through human evaluation, statistical significance testing, and more rigorous diagnostic analysis of the training dynamics.
