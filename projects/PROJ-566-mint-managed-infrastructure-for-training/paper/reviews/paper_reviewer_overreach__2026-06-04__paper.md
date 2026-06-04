---
action_items:
- id: e5b44bb7bd61
  severity: science
  text: "Abstract and Section 5.1 claim '18.3\xD7' (4B) and '2.85\xD7' (30B) handoff\
    \ speedups, but Table e001 (tab:e1_handoff_paths) shows ~13.5\xD7 (4B cold sample)\
    \ and ~1.33\xD7 (30B cold sample) or ~1995\xD7 (4B materialization). The specific\
    \ 18.3\xD7/2.85\xD7 figures lack a clear derivation from the provided data, constituting\
    \ an unsupported quantitative claim."
- id: c02041aef35f
  severity: writing
  text: Abstract states 'Scale Out to 10^6 addressable policies' as a measured capability.
    Section e001 clarifies this is a 'sizing sketch' in the Appendix, not a measured
    result. The Abstract must qualify this claim to distinguish between measured (100k)
    and modeled (1M) evidence.
artifact_hash: b4bbb587409bb8ce9fbc13953a4d6d307cbe54e41c3196b0506aac091594e206
artifact_path: projects/PROJ-566-mint-managed-infrastructure-for-training/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-04T01:09:19.748772Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript presents a robust system design but contains specific instances where the Abstract and Introduction extrapolate beyond what the presented data justifies.

First, the quantitative claims regarding handoff speedups in the Abstract and Section 5.1 ("18.3× on 4 B dense, 2.85× on 30 B MoE") are not directly supported by the data in Table e001 (tab:e1_handoff_paths). For the 4B model, the table shows a materialization speedup of ~1995× (71.820s vs 0.036s) or a cold sample speedup of ~13.5× (55.704s vs 4.114s). Neither matches the claimed 18.3×. Similarly, for the 30B MoE model, the cold sample speedup is ~1.33×, while the materialization speedup is ~8.6×, neither matching 2.85×. Claiming specific speedup factors that do not align with the primary evidence table constitutes overreach on the empirical results. The authors must either correct the figures to match the table or explicitly define the metric used to derive 18.3×/2.85× if it differs from the table rows.

Second, the Abstract claims "Scale Out to 10^6 addressable policies" alongside measured live-load speedups. Section e001 clarifies that the 10^6 figure is an "addressable-catalog sizing sketch" in the Appendix, while the main measurements sweep up to 100k entries. Presenting the modeled 10^6 capacity as a primary scaling axis in the Abstract, without distinguishing it from the measured 100k sweep, overstates the empirical evidence. The Abstract should qualify the 10^6 claim as a modeled projection rather than a measured system limit.

These issues require re-analysis of the handoff metrics and textual clarification of the evidence levels for the scaling claims.
