---
action_items:
- id: 79e837d6d406
  severity: science
  text: The evaluation relies on a single deterministic run (temperature 0.0) for
    all 5 backbone models across 13 datasets. Without multiple seeds or variance reporting,
    the observed gains (e.g., +4.66 pp in Retrieval Accuracy) cannot be distinguished
    from stochastic noise or specific prompt sensitivities. Re-run experiments with
    at least 3 seeds to report mean and standard deviation.
- id: fea7dae4b011
  severity: science
  text: The 'LLM-as-a-Judge' metric (GPT-5.4-mini) is used as a primary evaluation
    signal but lacks calibration against human annotations. Given the potential for
    LLM judges to exhibit bias toward their own outputs or specific phrasing, the
    paper must include a validation study (e.g., correlation with human ratings on
    a subset) to establish the metric's reliability.
- id: 21385cfa7dd8
  severity: science
  text: The 'Oracle' baseline is defined as perfect source selection, yet the gap
    between OmniRetrieval and Oracle remains significant (e.g., 65.71 vs 100.00 in
    Source Selection). The paper does not sufficiently analyze the specific failure
    modes of the source selection module (e.g., hallucinated KBs vs. missed relevant
    KBs) to explain why the gap persists despite the 'broad exploration' strategy.
artifact_hash: 6b55048d0f0cf12263aa0420c5a331e1157aabe9768489e7c4eadd1c3653e932
artifact_path: projects/PROJ-644-omniretrieval-unified-retrieval-across-h/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T16:48:19.023850Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence presented in OmniRetrieval is generally robust in its experimental design regarding the breadth of datasets (13 datasets, 309 knowledge bases) and the variety of baselines. The comparison against single-backend and KB Routing baselines effectively isolates the contribution of the unified framework. However, the statistical rigor of the reported results is compromised by the lack of variance estimation.

The authors explicitly state in the Implementation Details (Section 5.4) that a sampling temperature of 0.0 was used, making predictions deterministic. Consequently, all reported metrics in Table 1 and subsequent analyses are based on a single run per configuration. In LLM-based research, performance can be highly sensitive to prompt phrasing and model initialization even at temperature 0.0 due to non-deterministic token sampling in some backends or floating-point variations. Without reporting results across multiple random seeds (e.g., n=3 or n=5) and providing standard deviations, it is impossible to determine if the observed improvements (e.g., the 4.66 percentage point gain in Retrieval Accuracy over KB Routing) are statistically significant or artifacts of a specific run. This is a critical omission for a paper claiming a new state-of-the-art framework.

Furthermore, the reliance on "LLM-as-a-Judge" (GPT-5.4-mini) as a primary metric for Retrieval Accuracy and semantic equivalence introduces a potential confounding variable. The paper does not provide evidence that this specific judge model correlates well with human judgment or that it is not biased toward the outputs of the models being evaluated (e.g., if the judge is from the same family as the backbone). A validation study comparing the judge's scores against a human-annotated subset is necessary to substantiate the claims made in the "Main Results" section.

Finally, while the "Oracle" baseline is useful, the paper does not deeply analyze the residual gap between OmniRetrieval and the Oracle. The claim that "evidence selection recovers answers even if source selection misses" is supported by the narrowing gap, but the specific reasons for the remaining 34+ point gap in source selection are not empirically dissected. A more granular error analysis of the source selection failures would strengthen the evidence for the framework's limitations and future directions.
