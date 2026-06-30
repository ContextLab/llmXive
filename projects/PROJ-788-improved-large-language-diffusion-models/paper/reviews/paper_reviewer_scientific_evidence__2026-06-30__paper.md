---
action_items:
- id: ff383a6efd8c
  severity: writing
  text: 'The paper presents compelling empirical results for iLLaDA, an 8B masked
    diffusion language model, but the scientific evidence supporting its central claims
    requires strengthening in three key areas: statistical rigor, experimental controls,
    and effect size interpretation. First, the claim that iLLaDA-Base "is slightly
    stronger on average" than Qwen2.5 7B (63.9 vs 63.3 in Tab. 1) lacks statistical
    validation. With no reported standard errors, confidence intervals, or results
    from multiple random'
artifact_hash: 619f929e5279533c346a7478d5b6956c60e2e6e84c89950452f3d9515b5b8b28
artifact_path: projects/PROJ-788-improved-large-language-diffusion-models/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T21:46:20.860204Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents compelling empirical results for iLLaDA, an 8B masked diffusion language model, but the scientific evidence supporting its central claims requires strengthening in three key areas: statistical rigor, experimental controls, and effect size interpretation.

First, the claim that iLLaDA-Base "is slightly stronger on average" than Qwen2.5 7B (63.9 vs 63.3 in Tab. 1) lacks statistical validation. With no reported standard errors, confidence intervals, or results from multiple random seeds, it is impossible to determine whether this 0.6-point difference reflects a genuine improvement or random noise. Given the high variance typical in LLM benchmarking, this marginal gain should be treated as inconclusive without significance testing (e.g., paired t-tests across seeds).

Second, the ablation studies suffer from insufficient controls. Fig. 3 (SFT epoch ablation) shows monotonic improvement with more epochs, but the curves lack error bars or seed-based variance estimates. Without this, the observed "data-reuse effect" could be an artifact of a single favorable initialization. Similarly, Tab. 4 (scoring rule ablation) reports point improvements (e.g., +2.3 on HellaSwag) but provides no measure of uncertainty. In multiple-choice benchmarks with finite candidate sets, small score differences can easily arise from stochastic sampling; confidence intervals are essential to validate these claims.

Third, the comparison with Dream 7B introduces confounding variables. Dream is fine-tuned from Qwen2.5 (an autoregressive model), while iLLaDA is trained from scratch with bidirectional attention. The paper attributes performance gaps to "training strategy" but does not control for pre-training data quality, architecture differences (e.g., GQA vs MHA), or the impact of fine-tuning on a large AR model. A more rigorous analysis would either match architectures/data or explicitly disentangle these factors.

To address these issues, the authors should: (1) report results averaged over ≥3 random seeds with standard errors for all benchmark tables; (2) add statistical significance tests for key comparisons (e.g., iLLaDA vs Qwen2.5); (3) include variance estimates in ablation figures; and (4) clarify whether performance gains are robust to architectural/data confounders. Without these, the evidence for iLLaDA's superiority remains suggestive but not definitive.
