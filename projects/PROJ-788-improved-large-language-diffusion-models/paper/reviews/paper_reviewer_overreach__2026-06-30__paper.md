---
action_items:
- id: 9d88f7314189
  severity: writing
  text: The claim that iLLaDA-Base is "slightly stronger" than Qwen2.5 7B (63.9 vs
    63.3 avg) lacks statistical significance testing. A 0.6 point difference is likely
    noise. Rephrase to "comparable" unless significance is proven.
- id: 26b2f8846a93
  severity: science
  text: Attributing the large instruct gap (e.g., MATH 56.7 vs 75.5) "largely" to
    missing RL is unsupported. The paper lacks ablations isolating SFT data quality
    or strategy from RL effects. This causal claim is speculative.
- id: 591475ea1116
  severity: science
  text: The conclusion that bidirectional diffusion is the key driver over scale is
    an overreach. iLLaDA uses 12T tokens vs LLaDA's 2.3T, but no controlled comparison
    isolates architecture from scale against a similarly scaled AR model.
artifact_hash: 619f929e5279533c346a7478d5b6956c60e2e6e84c89950452f3d9515b5b8b28
artifact_path: projects/PROJ-788-improved-large-language-diffusion-models/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T21:45:25.077600Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims that extrapolate beyond the provided evidence, specifically regarding statistical significance, causal attribution of performance gaps, and the isolation of architectural benefits from scale.

First, the claim in the Abstract and Introduction that iLLaDA-Base is "slightly stronger on average" than Qwen2.5 7B (63.9 vs 63.3 in Table 1) is an overreach. A 0.6 point difference on a heterogeneous benchmark suite is well within the margin of error for standard evaluation protocols. Without reporting standard deviations, multiple runs, or statistical significance tests, asserting superiority is unjustified. The text should be tempered to "comparable" or "statistically indistinguishable."

Second, the discussion in Section 3.1 attributes the remaining gap between iLLaDA-Instruct and Qwen2.5-Instruct "largely" to the lack of reinforcement learning (RL) alignment. This is a causal claim not supported by the data. While RL is a known factor, the gap is substantial (e.g., MATH: 56.7 vs 75.5). The paper does not rule out that the difference stems from the SFT corpus quality, the specific masking strategy during SFT, or the instruction tuning data itself. Attributing the gap "largely" to a missing future component without an ablation study isolating SFT vs. RL effects is speculative.

Finally, the conclusion suggests that "fully bidirectional diffusion training from scratch" is the key to strong performance. However, the primary variable changed from LLaDA (2.3T tokens) to iLLaDA (12T tokens) is the training scale. While architectural changes were made, the paper does not provide a controlled experiment comparing iLLaDA to a similarly scaled autoregressive model to isolate the architectural contribution from the scale contribution. The claim that the *method* is the primary driver of success, rather than the *scale* of pre-training, is an overreach given the confounding variables.
