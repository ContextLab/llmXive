---
action_items:
- id: 6ce0df805de2
  severity: writing
  text: The 1M catalog claim is an extrapolation from Appendix Table F, not a measured
    result. Clarify that 100k is the measured limit and 1M is a capacity model projection
    to avoid over-claiming empirical validation.
- id: efa7913706e7
  severity: writing
  text: The 8.5-8.7x speedup applies only to the 'live engine-load slice' (Table 5),
    not total cold latency (~190s). Restrict the claim to the specific registration
    phase to prevent over-generalization of end-to-end performance.
- id: eef6f23589c1
  severity: writing
  text: The DSA support is described as a solution but admits lacking full replay
    (Section 4). Rephrase to state MinT offers a partial mitigation (IcePop masking)
    rather than a complete resolution of the DSA mismatch problem.
artifact_hash: 9b74dd1f4b8f2d4815ea056f5e26899cdd80d0bb7bac2914c7ef2512791b5d74
artifact_path: projects/PROJ-566-mint-managed-infrastructure-for-training/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:19:30.658323Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the scale and completeness of the MinT system that extend beyond the direct empirical evidence provided.

First, the claim of supporting "$10^6$-scale addressable policy catalogs" (Abstract, Section 4) is not directly validated by the experiments. The empirical data in Section 5 (Table 4) and the Appendix (Table F) only demonstrate single-engine sweeps up to 100k entries. The 1M figure is derived from a "fleet-level sizing sketch" and an extrapolation model (Appendix Table F) based on a "2300-distinct-adapter active-wave assumption." While this modeling is reasonable, presenting the 1M figure alongside measured results without a clear distinction between "measured" and "projected" constitutes an over-claim of empirical validation. The text should explicitly frame the 1M number as a capacity model projection rather than a measured system limit.

Second, the performance claims regarding "packed MoE LoRA tensors" (Abstract, Section 4) risk over-generalization. The paper states these tensors improve "live engine loading by 8.5–8.7x." Table 5 confirms this speedup applies to the specific "live engine-load slice" (the registration phase, reducing time from ~1.36s to ~0.16s). However, the abstract and main text imply this improvement benefits the broader "cold loading" process. The data in Table 4 and Figure 4 clearly show that total cold p95 latency remains dominated by other factors (e.g., ~190s), largely unaffected by the packing optimization. The claim should be strictly scoped to the "live load" phase to avoid misleading readers about the end-to-end cold-start performance.

Finally, the handling of Dynamic Sparse Attention (DSA) in GLM-5 models (Section 4) is presented as a solved problem ("MinT treats..."), yet the text admits significant limitations: "MinT currently lacks replay for every DSA indexer selection" and "does not reconstruct the exact sparse-attention token set." The system relies on a mitigation strategy (IcePop-style masking) rather than a full solution. The current phrasing overstates the completeness of the DSA support. The claim should be revised to accurately reflect that MinT provides a partial mitigation for DSA mismatch, not a full reconstruction of the training-serving path.
