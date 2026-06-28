---
action_items:
- id: 3adfbec2682e
  severity: science
  text: Resolve contradiction between text claiming 'highly consistent' seed results
    and Figure 12 caption stating 'variation 20 pp'. 20pp variance undermines benchmark
    reliability.
- id: 863a93bfd19f
  severity: science
  text: Clarify potential bias from using GPT-5.2 for data construction when evaluating
    GPT-5.4. Provide ablation or justification.
- id: 27f6d4162d07
  severity: science
  text: Justify 327-task sample size for statistical power across 10 models and multiple
    blocking conditions.
artifact_hash: 0fb9253adef42dcbc903c972875abcf8435cbde0a29a43054fe5430b0edd419c
artifact_path: projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T21:32:52.481287Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The paper presents a novel benchmark for long-horizon planning, but the scientific evidence supporting the stability and validity of the reported results requires strengthening.

First, there is a critical contradiction regarding experimental stability. The text in Appendix E003 claims that rerun evaluations with different seeds show results "highly consistent across seeds." However, the caption for Figure 12 (e002) explicitly states "variation 20 pp" for DeepSeek and Llama. A 20 percentage point variance across seeds is substantial and contradicts the claim of high consistency. This variance suggests the benchmark scores are sensitive to stochasticity, which undermines the reliability of the reported accuracy differences (e.g., the 40pp drop under blocking). The authors must reconcile this discrepancy, either by correcting the figure caption, re-running experiments to reduce variance, or explicitly discussing the instability as a limitation of the benchmark.

Second, the data construction methodology introduces potential bias. The authors use GPT-5.2 for both tool generation and filtering (Appendix E003), yet evaluate GPT-5.4. While versions differ, using the same model family for ground-truth creation and evaluation risks overfitting or leakage, where the evaluation model might recognize patterns from its own generation process. An ablation study using a different model family for construction (e.g., Llama) would strengthen the claim that the benchmark measures general planning ability rather than model-specific artifacts.

Finally, the sample size of 327 tasks is reasonable but requires justification given the number of conditions. With 10 models, multiple blocking settings, and seed variations, the effective sample size per condition is reduced. The reported 95% confidence intervals (Appendix E003) are narrow (2.94 pp), but this assumes the bootstrap resampling captures the true variance. If the seed variance is indeed 20 pp, the bootstrap intervals may be underestimating the true uncertainty. A power analysis or explicit discussion of the sample size's adequacy for the claimed statistical significance is necessary.

Addressing these points is essential to establish the robustness of the central claims regarding planning failures in large-scale tool ecosystems.
