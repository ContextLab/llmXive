---
action_items:
- id: d64fef0de2c1
  severity: writing
  text: Section 5.1 uses 'AKS' without expansion. Define as 'Adaptive Keyframe Sampling
    (AKS)' at first use.
- id: e31189a664c6
  severity: writing
  text: Section 3.3 refers to 'sensitivity check' and 'redundancy checks' without
    linking to the capitalized definitions in 3.1. Clarify as 'the Sensitivity test'
    and 'the Redundancy test' to distinguish from generic terms.
- id: b6a54e2b9690
  severity: writing
  text: Section 5.2 introduces 'Qwen3-VL_voting' as an 'oracle ensemble baseline'
    without defining the aggregation rule. Specify 'logical OR' or 'majority vote'
    explicitly in the definition clause.
- id: eb842a545f08
  severity: writing
  text: Section 3.1 introduces 'Bag-of-Frames (BoF)' but the acronym 'BoF' is used
    immediately. Ensure the full expansion 'Bag-of-Frames (BoF)' is clearly presented
    before the acronym is used in subsequent sentences.
artifact_hash: f0c16b304e278e372ae68ce72c73490fb948c6f63a71aa660ad21d1de4b7a1fb
artifact_path: projects/PROJ-1038-video-oasis-rethinking-evaluation-of-vid/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-11T04:08:12.436938Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The paper is generally accessible to a competent researcher in adjacent fields, with most standard acronyms (e.g., Video-LLM, SFT) either well-known or defined upon first use. However, there are specific instances where subfield-specific acronyms or method names are introduced without explicit expansion, creating minor barriers for an outsider.

In Section 5.1, the authors refer to "AKS" to denote the method from the cited paper "Adaptive keyframe sampling for long video understanding." The acronym is used without first spelling out "Adaptive Keyframe Sampling (AKS)." While the citation provides the source, the text itself assumes prior knowledge of the acronym, which violates the self-containment requirement for an adjacent-field reader.

Additionally, in Section 3.3, the terms "sensitivity check" and "redundancy checks" are used in lowercase. These refer to the specific "Sensitivity" and "Redundancy" tests defined in Section 3.1. Without capitalization or a clarifying reference (e.g., "the Sensitivity test defined in Section 3.1"), a reader might interpret these as generic statistical checks rather than the specific protocols of the Video-Oasis framework.

Finally, in Section 5.2, the "Qwen3-VL_voting" baseline is described as an "oracle ensemble," but the specific aggregation logic (e.g., logical OR vs. majority vote) is not explicitly stated in the definition sentence, relying on the reader to infer the mechanism from the following sentence. Explicitly stating the rule (e.g., "accepts a response if either mode succeeds") would remove this ambiguity.

These issues are minor and can be resolved with simple parenthetical expansions or clarifying phrases, ensuring the paper remains fully self-contained.
