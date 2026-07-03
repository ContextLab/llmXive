---
action_items:
- id: 73c50e52e1c0
  severity: science
  text: The claim that masking harms saturated models by removing 'crucial signals'
    contradicts the attention evidence showing models ignore the middle. The paper
    must explain why saturated models suddenly rely on ignored middle evidence while
    mid-capacity models do not.
- id: a9a3c683f0a1
  severity: science
  text: The 'Model Saturated' regime is defined by No-CM accuracy >70%, yet GPT-OSS-120B
    shows +8.0 gain on xBench (78% No-CM) but -4.8 on GAIA (72.8% No-CM). The paper
    fails to logically derive why the same capacity threshold yields opposite results
    based solely on 'noise' without a quantitative interaction term.
- id: 0da6d76bb932
  severity: science
  text: 'The regression probe claims SNR is the bottleneck because saturated models
    have high AUC but low gain. This logic is incomplete: it does not prove masking
    lowers SNR for these cases or that the model fails due to SNR rather than simply
    having sufficient capacity to ignore noise without help.'
artifact_hash: 0662f086c971957827b984215e812ef5eb19c982637f2c1511efa72d77075eda
artifact_path: projects/PROJ-652-https-arxiv-org-abs-2606-00408/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T02:30:40.511930Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a compelling empirical "regime map" for observation masking, but the logical consistency between the proposed mechanisms and the observed "collapse" in the saturated regime requires strengthening.

**1. Mechanism for the "Collapse" in Saturated Models**
The central claim is that masking helps by removing "neglected middle noise" (supported by attention maps showing U-shaped attention and bimodal re-opening). However, the paper argues that in the "Model Saturated" regime (No-CM accuracy > 70%), masking *harms* performance because it "removes evidence the model would otherwise use."
*   **Logical Gap:** The evidence provided (attention decay, re-opening patterns) suggests models *do not* attend to the middle. If saturated models also ignore the middle (as the attention data implies), why does masking them cause a collapse? The paper asserts that saturated models "rely on" this evidence but fails to provide a mechanism explaining *why* their reliance changes compared to the "sweet spot" models. Is it that saturated models perform a different type of reasoning (e.g., long-range verification) that requires the raw text, whereas mid-capacity models rely on the immediate context? Without this distinction, the claim that masking "evicts crucial signals" for saturated models contradicts the earlier finding that models generally ignore the middle.

**2. Inconsistent Application of the "SNR Bottleneck" Argument**
The paper posits that "optimizing input context's signal-to-noise ratio (SNR) when context is complex is the bottleneck for advanced agents."
*   **Logical Gap:** The regression probe shows that saturated models (e.g., GPT-OSS-120B) have high separability (AUC 0.74) for predicting CM rescue, yet they show near-zero or negative gain. The authors interpret this as "high separability but low net utility." However, the logical leap to "SNR is the bottleneck" is unsupported. If SNR were the bottleneck, improving it (via masking) should help. The fact that masking *hurts* these models suggests the bottleneck is *not* SNR, but perhaps the model's inability to distinguish signal from noise *without* the full context, or that the "noise" is actually a distractor that saturated models can handle but masking disrupts their specific attention pattern. The paper does not logically rule out the alternative: that the "signal" in the middle is only useful when the model is *not* saturated, or that the "noise" is actually a distractor that saturated models can handle but masking disrupts their specific attention pattern.

**3. Regime Boundary Definition vs. Empirical Variance**
The "Model Saturated" regime is defined by a No-CM accuracy threshold (>70%).
*   **Logical Gap:** The data shows that the same model (GPT-OSS-120B) falls into different regimes depending on the benchmark: it is "saturated" (gain +0.1) on BrowseComp-Plus, "mismatch" (gain +8.0) on xBench, and "harmed" (gain -4.8) on GAIA. The paper attributes this to "live-web noise" but does not logically derive a unified condition. If the regime is defined by model capacity, why does the *same* capacity yield different regimes? The paper needs to explicitly define the regime boundary as a function of *both* model capacity and *task complexity/noise level*, rather than just model accuracy, to maintain logical consistency across the different benchmarks.

**Recommendation:**
The authors should clarify the mechanism for the "collapse" in saturated models. Specifically, they must explain why models that generally ignore the middle (per attention data) suddenly require it when they are "saturated." Additionally, the definition of the "Model Saturated" regime should be refined to account for the variance across benchmarks, or the "SNR bottleneck" argument should be revised to explain why high SNR optimization (masking) fails for these specific cases.
