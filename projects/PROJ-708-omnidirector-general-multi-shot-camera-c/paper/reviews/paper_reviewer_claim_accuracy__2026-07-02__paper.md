---
action_items:
- id: 076c57372de6
  severity: science
  text: Claim that LTX-LoRA's transitions are 'artifacts of leakage' lacks evidence.
    High leakage does not prove the transition mechanism is an artifact; ablation
    or qualitative proof is needed to support this causal assertion.
- id: 862acf4222ab
  severity: writing
  text: "T-Pre definition uses degrees (\xB0) for translation error, which is physically\
    \ incorrect. Translation is a distance metric, not angular. This typo or error\
    \ makes the reported 72.74% metric uninterpretable."
- id: 58066bc9d1da
  severity: writing
  text: The paper relies on 'Qwen3-VL' (citing a 2025 preprint) which may not exist
    yet. The methodology's validity depends on this model's actual capabilities. Clarify
    if this is a hypothetical citation or a real, available model.
artifact_hash: a65d314d17ec7712e12f1ec0ba7f4dba5e22b080c532708ee9eae2b427ffd22c
artifact_path: projects/PROJ-708-omnidirector-general-multi-shot-camera-c/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T06:46:37.429152Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and the validity of citations within the manuscript.

**Metric Definition Error (Section 5.1):**
The definition of the metric **T-Pre** contains a fundamental physical inconsistency. The text states: "T-Pre denotes the proportion of predictions with a relative translation error below 20°." Translation error (RTE) measures displacement in spatial units (e.g., meters or normalized scene units), whereas degrees (°) are units of angular measurement used for rotation (RRE). Claiming a translation error threshold in degrees is physically nonsensical. This suggests either a severe typo (confusing the threshold for RRE with RTE) or a misunderstanding of the metric itself. Consequently, the quantitative results in Table 1 (e.g., T-Pre = 72.74%) are currently uninterpretable and cannot be verified against the stated definition.

**Unsupported Causal Claim (Section 5.2):**
In the quantitative comparison, the authors assert that LTX-LoRA's ability to generate shot transitions is "actually an artifact of information leakage rather than genuine camera control." While Table 1 shows LTX-LoRA has a high leakage rate (15.04%), high leakage does not logically necessitate that the transition capability is an *artifact* of that leakage. It is possible for a model to learn transition patterns while also leaking content. The paper provides no ablation study or qualitative evidence isolating the transition mechanism from the leakage to support this specific causal attribution. This claim overstates the evidence provided by the leakage metric alone.

**Citation Validity (Section 5.1 & 5.2):**
The manuscript repeatedly cites and relies on **Qwen3-VL** (citing `bai2025qwen3`) for the Prompt Expansion Agent. The citation refers to a 2025 preprint. Given the current date, Qwen3 is not a publicly established model version (Qwen2.5 is the current state-of-the-art). If this paper is intended for a future venue (2026), the specific capabilities attributed to Qwen3-VL are speculative. If the model does not exist or the citation is a placeholder, the description of the "Prompt Expansion Agent" methodology is factually unsupported. The authors must clarify the existence and version of the model used.

**Citation Consistency:**
The paper cites `lin2025dpa3` (Depth Anything 3) for camera pose estimation. While the citation exists in the bibliography, the claim that this specific model is used for "robust" estimation in complex real-world scenes requires verification that the cited model actually outperforms existing baselines (like DPT or Depth Anything V2) in the specific context of video pose estimation, which is not explicitly detailed in the text. However, the primary issue remains the metric definition and the causal claim regarding leakage.
