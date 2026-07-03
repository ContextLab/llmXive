---
action_items:
- id: 6045250c699d
  severity: science
  text: In Section 3 (Results), the text claims a +11.2 point gain over SpaceTools
    (Tab. 1). However, Table 1 (action_interface) shows SpaceTools (Structured Tool-Call)
    averaging 56.7% and SpatialClaw 59.9%, a difference of 3.2 points. The +11.2 figure
    appears to be the gain over the 'No-tool' baseline (53.4% -> 59.9%) or a different
    comparison not explicitly defined in the text. This misattribution of the baseline
    undermines the claim's accuracy.
- id: 509ee57e9942
  severity: writing
  text: Table 1 (action_interface) lists Omni3D results where Structured Tool-Call
    (55.7) outperforms SpatialClaw (54.3), yet the text in Section 3 states SpatialClaw
    'outperforms... across all categories.' This is factually incorrect for the Omni3D
    benchmark within the Single-image category. The claim requires qualification or
    correction to reflect that gains are not universal across every single benchmark.
- id: fb16995fe5a6
  severity: science
  text: The abstract and introduction claim the framework is 'training-free' and achieves
    gains 'without any benchmark- or model-specific adaptation.' However, the prompt
    details (App. Prompts) describe a 'Planner' that maps question shapes to specific
    tools (e.g., 'coordinates -> vlm.locate + SAM3'). If this mapping logic is hard-coded
    or requires manual tuning per benchmark type, the claim of 'no adaptation' is
    overstated. Clarify if the planner is fully zero-shot or relies on pre-defined
    heuristics.
artifact_hash: 03b4b7546f79862eef36a0d430e3a6b82062f65b52d01a2c8d4c65b5c5b34086
artifact_path: projects/PROJ-700-spatialclaw-rethinking-action-interface/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T11:10:34.651410Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper makes several strong quantitative claims regarding performance gains and generalization that are not fully supported by the provided data tables.

First, the most significant discrepancy lies in the reported improvement over the primary baseline, SpaceTools. The Abstract and Introduction state that SpatialClaw outperforms SpaceTools by **+11.2 points**. However, Table 1 (`tables/ablation_action_interface.tex`) explicitly lists the average accuracy for SpaceTools (Structured Tool-Call) as **56.7%** and SpatialClaw as **59.9%**. The actual difference is **3.2 points**. The +11.2 figure corresponds to the gain over the "No-tool" baseline (53.4% to 59.9%). Attributing the +11.2 gain to SpaceTools is a factual error that significantly misrepresents the magnitude of the improvement over the state-of-the-art method.

Second, the claim in Section 3 that SpatialClaw "outperforms... across all categories" is contradicted by the data in Table 1. In the "Single-image" category, specifically for the **Omni3D** benchmark, the Structured Tool-Call baseline achieves **55.7%**, while SpatialClaw achieves **54.3%**. Similarly, in the "General video understanding" category, **CV-Bench** shows Structured Tool-Call at **73.6%** versus SpatialClaw at **72.2%**. The text should be revised to acknowledge that while the *average* performance is superior, there are specific benchmarks where the structured tool-call approach remains competitive or superior.

Finally, the claim of being "training-free" and requiring "no benchmark-specific adaptation" is potentially overstated given the "Planner" description in the Appendix. The planner is described as mapping question shapes to specific tools (e.g., "coordinates -> vlm.locate + SAM3"). If this mapping logic is a fixed heuristic defined by the authors rather than a learned or fully zero-shot inference by the LLM, it constitutes a form of benchmark-specific engineering. The authors should clarify whether the planner's logic is static or dynamically inferred to ensure the "no adaptation" claim is accurate.
