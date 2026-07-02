---
action_items:
- id: f35a9e0e90d8
  severity: writing
  text: The abstract and Section 4 claim a 18.3x handoff reduction on a 4B model.
    Table 1 (e1_handoff_paths) shows 71.82s (merge) vs 0.036s (adapter load), which
    is ~1995x. The 18.3x figure likely refers to the total step time (55.7s vs 4.1s).
    The text must clarify that the 18.3x applies to the end-to-end step, not just
    the handoff artifact transfer, to avoid misrepresenting the data.
- id: 00b27aa9d867
  severity: writing
  text: The abstract claims a 2.85x handoff reduction on a 30B MoE model. Table 1
    shows 402.2s (merge) vs 46.5s (adapter load), a ratio of ~8.6x. The 2.85x figure
    corresponds to the total step time (156s vs 117s). The text incorrectly attributes
    the step-time speedup to the 'handoff step' specifically, conflating the artifact
    transfer with the full generation latency.
- id: 97d722b155bb
  severity: writing
  text: "Section 4 claims packed MoE LoRA tensors improve 'live engine loading' by\
    \ 8.5\u20138.7x. Table 4 (e4_packed_loader) confirms this speedup for the 'live\
    \ engine loading' slice (1.36s -> 0.16s). However, the text implies this is the\
    \ total cold-load time. The paper explicitly states elsewhere that total cold\
    \ latency includes routing and fetch (199s). The claim needs to strictly specify\
    \ that the 8.5x speedup applies only to the tensor-loading slice, not the full\
    \ cold-path latency."
- id: 14a72a58bd20
  severity: writing
  text: The abstract states the system supports '10^6-scale addressable policy catalogs'
    and 'measured single-engine sweeps through 100K entries'. Section 4 clarifies
    the 1M number is an extrapolation from Appendix Table F (fleet_model), while the
    100K is the measured sweep. The abstract presents the 1M figure as a direct system
    capability without immediately qualifying it as a modeled extrapolation, which
    risks overstating the empirical evidence.
artifact_hash: 9b74dd1f4b8f2d4815ea056f5e26899cdd80d0bb7bac2914c7ef2512791b5d74
artifact_path: projects/PROJ-566-mint-managed-infrastructure-for-training/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:18:47.952392Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper makes several specific quantitative claims regarding performance improvements (speedups and latency reductions) that are not fully supported by the cited tables when read in isolation.

In the Abstract and Section 4, the authors claim that the "adapter-only handoff reduces the measured handoff step by 18.3x on a 4B dense model and by 2.85x on a 30B MoE model." A review of Table 1 (`tab:e1_handoff_paths`) reveals a discrepancy in terminology. For the 4B model, the "Materialization or load" time drops from 71.82s to 0.036s, a reduction of approximately 1995x. The 18.3x figure actually corresponds to the "Cold first sample" time (55.704s vs 4.114s). Similarly, for the 30B model, the materialization time drops from 402.2s to 46.5s (~8.6x), while the 2.85x figure corresponds to the cold first sample time (156.07s vs 117.30s). The text incorrectly attributes the total step-time speedup to the "handoff step" (artifact transfer), which is misleading. The "handoff step" in the table is the materialization/load phase, which sees a much larger speedup. The claims should be rephrased to specify that the 18.3x and 2.85x figures refer to the *end-to-end cold start latency* or *total step time*, not the handoff artifact transfer alone.

Regarding the "Scale Out" claims, the Abstract states that "packed MoE LoRA tensors improve live engine loading by 8.5–8.7x." Table 4 (`tab:e4_packed_loader`) supports this specific metric for the "Live engine loading" slice (reducing 1.36s to ~0.16s). However, the Abstract and Section 4 contextually link this to the broader "cold loading" bottleneck. The paper correctly notes in Section 4 that total cold latency (199s) is dominated by other factors (routing, fetch), but the phrasing "improve live engine loading" is accurate only if strictly interpreted as the tensor-loading slice. The text must ensure readers do not infer that the *total* cold-load latency is reduced by 8.5x, which would be factually incorrect based on the provided data.

Finally, the claim of supporting "$10^6$-scale addressable policy catalogs" is presented as a system capability in the Abstract. Section 4 and Appendix Table F clarify that the 1M figure is a "capacity model" or extrapolation based on single-engine limits (100k sweep), not a direct measurement of a single engine holding 1M adapters. While the distinction is made in the body, the Abstract's phrasing ("supports 10^6-scale...") is slightly stronger than the evidence (which is a sweep up to 100k and a model for 1M). A minor clarification in the Abstract to explicitly label the 1M figure as an extrapolated capacity model would align the claim more precisely with the evidence.
