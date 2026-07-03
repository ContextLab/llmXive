---
action_items:
- id: cad3a5c2d7b6
  severity: writing
  text: The claim of 'real-time' interaction in the title and abstract is not fully
    supported by the reported latencies. Table 1 shows a first-frame latency of 1.137s
    for Wan2.1 and 3.446s for HY1.5. While this is a significant speedup, a >1s delay
    contradicts the standard definition of 'real-time' (typically <100ms or <33ms
    for 30fps) in interactive systems. The text should temper this claim to 'low-latency'
    or explicitly define the specific interactive scenario where >1s latency is acceptable.
- id: 4fa763ae8ad3
  severity: writing
  text: The paper claims the framework is 'architecture-extensible' and 'modular'
    (Abstract, Intro), yet the experimental validation is limited to only two specific
    backbones (Wan2.1 and HY1.5). There is no evidence provided that the pipeline
    works on other architectures (e.g., U-Net based models or different MMDiT variants)
    without significant re-engineering. The claim of general extensibility is an over-extrapolation
    from the current limited instantiation.
- id: 240ce6154f15
  severity: science
  text: The ablation on 'minimal batch size' (Sec 4.3) claims that batch size 16 is
    required for 'high controllability' based on visual inspection of Figure 4. However,
    the paper does not provide a quantitative metric (e.g., pose error, trajectory
    alignment score) to substantiate the qualitative jump from 'unstable' (BS=8) to
    'high controllability' (BS=16). Without quantitative evidence, the specific threshold
    of 16 is an over-claim based on subjective visual assessment.
artifact_hash: 0ee056e55f4c06cb2eab61e5c44334fbdff8ec177adecd2d7f6251ef9b5e9f6a
artifact_path: projects/PROJ-642-minwm-a-full-stack-open-source-framework/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T15:44:30.563633Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims that extend beyond the immediate evidence provided in the text and tables, specifically regarding the definitions of "real-time," the generality of the framework, and the quantitative basis for ablation conclusions.

First, the title and abstract repeatedly characterize minWM as a framework for "Real-Time Interactive Video World Models." However, the empirical results in Table 1 (Section 4.1) report a first-frame latency of 1.137 seconds for the Wan2.1 model and 3.446 seconds for the HY1.5 model. In the context of interactive systems, "real-time" typically implies latencies below 100ms (or at least below the frame interval of 33ms for 30fps) to ensure responsiveness. A delay of over one second creates a noticeable lag that contradicts the standard definition of real-time interaction. While the authors correctly note this is a massive speedup over the bidirectional baseline, extrapolating this to "real-time" is an over-claim. The terminology should be adjusted to "low-latency" or the specific use-case where >1s latency is acceptable must be explicitly defined and justified.

Second, the authors claim the framework is "architecture-extensible" and "modular" (Abstract, Introduction), suggesting it can be easily applied to various video backbones. The evidence provided, however, is limited to two specific instantiations: Wan2.1 (cross-attention) and HY1.5 (MMDiT). There is no discussion or experimental validation regarding the framework's application to other common architectures (e.g., standard U-Nets or different transformer variants) that might require non-trivial modifications to the PRoPE injection or distillation stages. Claiming broad extensibility based on only two successful cases is an over-extrapolation. The text should qualify this claim to reflect that it has been demonstrated on these specific architectures, or provide a theoretical argument for why it generalizes without empirical proof.

Finally, the ablation study on "Minimal batch size" (Section 4.3, Figure 4) concludes that a batch size of 16 is necessary for "high controllability," while batch size 8 is "unstable." This conclusion relies entirely on visual inspection of the generated video samples in Figure 4. The paper lacks a quantitative metric (such as camera pose error, trajectory alignment score, or a user study) to objectively distinguish between "unstable" and "high" controllability. Without such metrics, the specific threshold of 16 is a subjective over-claim. The authors should either provide quantitative data supporting this specific threshold or soften the language to reflect that the finding is based on qualitative observation.
