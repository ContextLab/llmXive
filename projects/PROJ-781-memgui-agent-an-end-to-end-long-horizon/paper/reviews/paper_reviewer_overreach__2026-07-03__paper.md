---
action_items:
- id: 113d231f1cf5
  severity: writing
  text: The claim that CONACT 'saves ~1.5k input tokens by step 150' (Intro) lacks
    a defined baseline comparison or calculation methodology. Specify the exact ReAct
    context growth rate and the folding compression ratio used to derive this figure.
- id: be26427673cb
  severity: writing
  text: The statement that MemGUI-8B-SFT 'generalizes to MobileWorld' (Conclusion)
    overstates the evidence. The results in Table 4 show a 17.9% SR, which is lower
    than the 43.9% SR of GUI-Owl-1.5-32B. Clarify that the gain is relative to the
    8B baseline, not a generalization to state-of-the-art performance.
- id: e55677bf9573
  severity: writing
  text: The claim that the method 'reduces total failures by 41%' (Sec 5.4) is based
    on a specific ablation variant (Full CONACT vs ReAct) on a specific model (235B).
    Ensure the text does not imply this reduction applies universally to all model
    sizes or task difficulties without qualification.
artifact_hash: 7ba9201f0f49d9384a35f3eca07d4fd8d448c0da222a8a4e9472044b7e857c18
artifact_path: projects/PROJ-781-memgui-agent-an-end-to-end-long-horizon/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T19:22:50.393929Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the efficacy of the proposed CONACT framework and the MemGUI-3K dataset. While the experimental results generally support the core hypothesis that proactive context management improves long-horizon performance, there are instances of over-claiming where the language extrapolates beyond the specific conditions of the reported data.

First, the Introduction states that CONACT "saves ~1.5k input tokens by step 150 compared to ReAct." This is a precise quantitative claim that currently lacks the necessary context to be verified. The paper does not explicitly define the baseline ReAct context growth rate (tokens per step) or the specific compression ratio achieved by the folding mechanism that leads to this 1.5k figure. Without a clear definition of the baseline or a reference to a specific calculation in the appendix, this number appears to be an extrapolation rather than a directly measured result in the provided text. The authors should clarify the baseline assumptions or provide the calculation methodology.

Second, the Conclusion asserts that "MemGUI-8B-SFT generalizes to MobileWorld." While the model does show improvement over its zero-shot baseline on MobileWorld (Table 4), the term "generalizes" in this context risks overstating the capability. The achieved Success Rate (17.9%) is significantly lower than other agents on the same benchmark (e.g., GUI-Owl-1.5-32B at 43.9%). The claim should be tempered to reflect that the model demonstrates *relative* improvement or *transfer* of the CONACT strategy to a new benchmark, rather than implying a robust, general-purpose capability that matches or exceeds existing specialized agents.

Finally, the error analysis in Section 5.4 claims that "Full CONACT reduces total failures by 41% (99→58)." This statistic is derived from a specific comparison between the Full CONACT variant and the ReAct baseline using the Qwen3-VL-235B-Thinking model. The phrasing could be misinterpreted as a universal property of the method across all model scales or task difficulties. Given that Table 1 shows smaller models (2B, 4B, 8B) actually regress when using CONACT zero-shot, the 41% reduction is not a generalizable fact for the method itself but rather a result specific to the 235B model configuration. The text should explicitly qualify this reduction to the specific experimental setup to avoid misleading readers about the method's universal applicability.
