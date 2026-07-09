---
action_items:
- id: 619d8ba3cb5c
  severity: writing
  text: The paper presents a compelling method (HiLS-Attention) with extensive empirical
    results across model scales. However, the evidentiary strength of the core claims
    is weakened by a lack of variance reporting and potential confounds in the large-scale
    comparisons. First, the small-scale experiments (Section 4.1) rely heavily on
    single-run results for the RULER benchmark. Tables 345M_main_ruler and 345M_ablation_ruler
    report integer scores (e.g., 100, 95, 72) without any indication of standard devi
artifact_hash: c95e527feac1da55ce3c1a4f78a6e7762db38d741afaaaef5a9558e2491c1f16
artifact_path: projects/PROJ-1014-hierarchical-sparse-attention-done-right/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-09T02:55:15.605443Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling method (HiLS-Attention) with extensive empirical results across model scales. However, the evidentiary strength of the core claims is weakened by a lack of variance reporting and potential confounds in the large-scale comparisons.

First, the small-scale experiments (Section 4.1) rely heavily on single-run results for the RULER benchmark. Tables 345M_main_ruler and 345M_ablation_ruler report integer scores (e.g., 100, 95, 72) without any indication of standard deviation, standard error, or the number of random seeds used. In sparse attention mechanisms, the chunk selection process is inherently stochastic; a difference of 1-2 points in retrieval accuracy on a synthetic task can easily arise from a lucky seed rather than a structural advantage. Without reporting results across at least 3-5 seeds, the claim that HiLS "significantly leads" over baselines like Naive-BSA or NSA is not statistically robust. The authors must regenerate these results with multiple seeds and report mean ± SD to confirm the effect is real.

Second, the large-scale continued pretraining results (Section 4.3, Table 7B_longbench) introduce a potential confound in the baseline comparison. The paper compares HiLS-Attn against a "YaRN-extended" baseline. It is unclear if this baseline was subjected to the same 50B-token continued pretraining (CPT) regimen as the HiLS models, or if it represents a static extension of a pre-existing checkpoint. If the baseline was not trained with the same CPT budget, the observed performance gap could be attributed to the additional training tokens rather than the attention mechanism itself. To isolate the contribution of HiLS, the authors must ensure the baseline receives an identical CPT budget or clarify the training protocol.

Finally, the efficiency claims in Section 5.1 are based on a single configuration (345M model, batch size 1, H800 GPU). While the trend of linear vs. quadratic scaling is theoretically sound, the specific speedup factors (13.5x/15.7x) are presented as precise measurements without reporting variance across multiple runs or different batch sizes. System-level noise (e.g., kernel warm-up, memory bandwidth contention) can significantly affect latency measurements. Reporting latency distributions (p50, p99) over multiple runs would strengthen the evidence for the claimed efficiency gains.

Addressing these points—specifically adding seed variance to the small-scale results and clarifying the training budget parity for the 7B baseline—would significantly improve the robustness of the paper's central claims.
