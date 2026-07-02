---
action_items:
- id: e2c28b836940
  severity: writing
  text: The abstract claims 10^6-scale catalogs and thousand-adapter waves, but data
    only shows 100k sweeps and 64-batch limits. The 1M figure is an Appendix extrapolation,
    not measured. Clarify this is a projection, not empirical validation.
- id: fe4c994902fb
  severity: writing
  text: The 8.5-8.7x loading speedup applies only to the tensor-registration slice,
    not total cold-start latency which includes fetch/queueing. The abstract implies
    end-to-end improvement. Qualify the claim to specify it applies only to the loading
    phase.
- id: a3550c57ad4e
  severity: writing
  text: The claim that concurrent GRPO shortens wall time 'without increasing peak
    memory' is true but misleading. Speedup comes from utilizing idle time in the
    same allocation, not reducing base model memory. Clarify that memory efficiency
    is via time-slicing, not footprint reduction.
artifact_hash: 9b74dd1f4b8f2d4815ea056f5e26899cdd80d0bb7bac2914c7ef2512791b5d74
artifact_path: projects/PROJ-566-mint-managed-infrastructure-for-training/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:02:37.422479Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding scale and performance that extend beyond the direct empirical evidence presented in the main text and appendices. While the system design is sound, the extrapolation from single-engine measurements to fleet-wide capabilities requires clearer demarcation to avoid over-claiming.

First, the abstract and Section 4 assert that MinT supports a "$10^6$-scale addressable policy catalog" and "thousand-adapter active waves at cluster scale." The experimental validation in Section 5 (specifically Table 4 and the Appendix) only demonstrates single-engine sweeps through 100k entries and a same-batch limit of 64 adapters. The $10^6$ figure is derived from a "fleet-level sizing sketch" in Appendix Table 6, which is a theoretical capacity model based on extrapolating single-engine limits, not a measured result from a million-adapter deployment. The main text currently presents this extrapolation as a demonstrated capability ("supports $10^6$-scale"). To correct this overreach, the authors must explicitly state that the million-scale figure is a projected capacity based on the measured single-engine bounds, rather than an empirically validated system state.

Second, the claim that "packed MoE LoRA tensors improve live engine loading by 8.5–8.7x" (Abstract, Section 4) conflates a specific sub-step with the total cold-load latency. Table 4 and Figure 6 clearly show that the 8.5–8.7x speedup applies to the "live engine-load slice" (the time to register tensors after they are fetched). However, the total cold path includes routing, queueing, and network fetch time, which are not accelerated by tensor packing. The current phrasing implies the entire cold-start latency is reduced by this factor, which is not supported by the data. The claim should be refined to specify that the speedup applies strictly to the tensor-loading and registration phase.

Finally, the claim that concurrent GRPO shortens wall time "without increasing peak memory" (Abstract, Section 4) is technically accurate based on Table 2 but risks misinterpretation. The speedup is achieved by filling idle gaps in the sequential schedule using the *same* resident base allocation, not by reducing the memory required for the base model. The text should clarify that the memory efficiency comes from time-slicing the existing base model rather than eliminating the base model's memory footprint, ensuring readers do not infer a reduction in the fundamental memory requirements for the base architecture.
