---
action_items:
- id: a6e1e397b42a
  severity: writing
  text: The claim of 'comparable visual quality' to industrial baselines (LingBot-World,
    HY-WorldPlay) is over-claimed. Table 1 shows SANA-WM+Refiner achieves 80.62 VBench
    Overall vs. LingBot's 81.82. While close, the baselines are 480p while SANA-WM
    is 720p; the paper conflates resolution differences with quality parity without
    normalizing for resolution or providing perceptual user studies to justify 'comparable'
    status.
- id: d03cebe31720
  severity: writing
  text: The '36x higher throughput' claim (Abstract) lacks a clear, fair baseline
    definition. The paper compares SANA-WM (single GPU, 720p) against baselines running
    on 8 GPUs at 480p. The throughput difference is driven by both resolution and
    hardware count. The claim implies architectural superiority alone drives this,
    but the comparison is confounded by the 8x GPU difference and resolution gap.
- id: e9fe636a6efe
  severity: writing
  text: The claim that the model 'natively trained for one-minute generation' (Abstract)
    is slightly misleading. Section 3.1 describes a progressive training strategy
    starting from 5s clips (Stage 1-2) before extending to minute-scale (Stage 3).
    While the final model is trained on minute data, the 'native' implication of skipping
    short-horizon pre-training is not fully accurate.
- id: 81208c217ab3
  severity: writing
  text: The 'single RTX 5090' deployment claim (Abstract) is speculative. The RTX
    5090 is not a released product at the time of writing (implied by the paper's
    context). Claiming specific performance (34s) on unreleased hardware without a
    clear extrapolation methodology or disclaimer is an overreach.
artifact_hash: e5cefeb8f5a622284bf4bd8a2b4800bf995401cb7708f8533b8b272aa0c905d4
artifact_path: projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:44:31.261883Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims that extrapolate beyond the provided evidence, primarily regarding comparative performance and hardware specifications.

First, the assertion in the Abstract and Introduction that SANA-WM achieves "visual quality comparable to large-scale industrial baselines such as LingBot-World and HY-WorldPlay" is an overstatement. Table 1 (Main Results) shows SANA-WM+Refiner scoring 80.62 on VBench Overall, while LingBot-World scores 81.82. While the gap is small, the baselines operate at 480p resolution, whereas SANA-WM operates at 720p. The paper does not provide a resolution-normalized comparison or a perceptual user study to substantiate that the 720p output is "comparable" in perceived quality to the 480p outputs of larger models. The claim conflates resolution advantages with model quality.

Second, the "36x higher throughput" claim (Abstract) is misleading due to confounding variables. The comparison pits a single-GPU SANA-WM inference against baselines running on 8 GPUs (e.g., LingBot-World uses 8 H100s). The throughput difference is driven significantly by the 8x hardware difference and the resolution gap, not solely by the architectural efficiency of the Hybrid Linear Attention. The paper frames this as a pure efficiency win of the architecture, which over-reaches the data.

Third, the claim of deployment on a "single RTX 5090" (Abstract) is speculative. As of the likely submission date, the RTX 5090 is an unreleased product. Providing specific latency numbers (34s) for hardware that does not yet exist, without detailing the extrapolation method or explicitly labeling it as a projection, constitutes an over-claim.

Finally, the description of the model as "natively trained for one-minute generation" (Abstract) glosses over the progressive training strategy detailed in Section 3.1. The model is trained on 5s clips for Stages 1 and 2 before extending to minute-scale in Stage 3. While the final model handles minute sequences, the "native" phrasing suggests it was never exposed to shorter horizons, which contradicts the methodology.

These issues require textual clarification to align the claims with the actual experimental setup and available data.
