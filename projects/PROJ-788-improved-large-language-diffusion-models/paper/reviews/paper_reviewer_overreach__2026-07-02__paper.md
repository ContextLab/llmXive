---
action_items:
- id: deee54cfab84
  severity: writing
  text: The abstract and introduction claim iLLaDA is 'competitive' with Qwen2.5 7B
    and 'slightly stronger on average' (Sec 1). However, Table 2 shows iLLaDA-Instruct
    (Avg 67.1) significantly underperforms Qwen2.5 7B Instruct (Avg 77.1) by ~10 points.
    The claim of competitiveness in the instruct setting is an over-interpretation
    of the data and should be qualified to reflect the substantial gap.
- id: 96af96d66c75
  severity: writing
  text: The abstract states iLLaDA improves by '14.5 points on MATH' and '16.5 points
    on HumanEval' compared to LLaDA. While these deltas are numerically correct against
    LLaDA, the abstract frames this as a general improvement without explicitly contrasting
    it with Dream (which outperforms iLLaDA on HumanEval). This selective highlighting
    risks overstating the model's universal superiority over all diffusion baselines.
- id: 0c5f32284573
  severity: writing
  text: The conclusion states that 'fully bidirectional diffusion training from scratch
    can achieve strong language modeling performance' based on iLLaDA's results. However,
    the paper admits iLLaDA-Instruct lags behind Qwen2.5 Instruct and attributes this
    to missing RL alignment. The claim that the *training paradigm itself* is fully
    competitive is premature without controlling for the alignment stage, which is
    a confounding variable in the comparison.
artifact_hash: 619f929e5279533c346a7478d5b6956c60e2e6e84c89950452f3d9515b5b8b28
artifact_path: projects/PROJ-788-improved-large-language-diffusion-models/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T10:45:01.535575Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims regarding the competitiveness of iLLaDA with state-of-the-art autoregressive models (specifically Qwen2.5 7B) that appear to overreach the provided empirical evidence, particularly in the instruction-tuned setting.

In the Abstract and Introduction, the authors state that iLLaDA is "competitive" with Qwen2.5 7B and that the Base model is "slightly stronger on average." While the Base model average (63.9 vs 63.3) supports a marginal lead, the Abstract's claim of broad competitiveness glosses over the significant performance gap in the instruction-tuned setting. Table 2 clearly shows iLLaDA-Instruct (67.1 average) trailing Qwen2.5 7B Instruct (77.1 average) by a substantial margin (~10 points). Describing a model that lags by 10 points on average as "competitive" in the abstract is an over-interpretation that may mislead readers about the current state of diffusion models relative to aligned autoregressive models. The text in Section 3.1 attempts to mitigate this by attributing the gap to missing RL alignment, but the initial claims in the Abstract and Introduction remain too strong given the data.

Furthermore, the Abstract highlights specific improvements over LLaDA (e.g., +14.5 on MATH, +16.5 on HumanEval) to suggest broad superiority. While these numbers are accurate relative to LLaDA, the Abstract omits the context that the "Dream" baseline (a diffusion model fine-tuned from Qwen2.5) actually outperforms iLLaDA on HumanEval (57.9 vs 50.0 in Table 1). By selectively comparing only against LLaDA in the summary, the paper overstates the universality of its improvements across all diffusion baselines.

Finally, the Conclusion asserts that "fully bidirectional diffusion training from scratch is a competitive path toward strong language models." This conclusion extrapolates beyond the evidence because the "strong" performance of the autoregressive baseline (Qwen2.5) includes a post-training alignment phase (RL) that iLLaDA lacks. Without an ablation showing that iLLaDA + RL would close the gap, or a comparison against an unaligned Qwen2.5, the claim that the *diffusion training paradigm itself* is the primary driver of competitiveness is not fully supported. The paper should temper these claims to reflect that iLLaDA is competitive *in the base setting* or *before alignment*, rather than broadly competitive with fully aligned SOTA models.
