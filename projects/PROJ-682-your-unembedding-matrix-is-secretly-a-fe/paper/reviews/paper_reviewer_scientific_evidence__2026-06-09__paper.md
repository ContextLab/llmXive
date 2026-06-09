---
action_items:
- id: 7e3d595f5472
  severity: science
  text: Report standard deviations and confidence intervals across multiple random
    seeds. All MTEB results in Tables 1-4 appear to be single-run averages without
    variance estimates.
- id: '671015828049'
  severity: science
  text: Add statistical significance testing (e.g., paired t-tests or bootstrap confidence
    intervals) between EmbFilter and baseline methods. Claims of 9-14% improvements
    lack statistical validation.
- id: f4375e6a98e5
  severity: science
  text: "Clarify whether the optimal \u03C4=2 configuration was pre-specified or selected\
    \ post-hoc from \u03C4={2,4,8} trials. Multiple \u03C4 testing without correction\
    \ risks cherry-picking."
- id: 447dab7e93a9
  severity: science
  text: Provide causal evidence for the edge spectrum mechanism. Currently relies
    on correlational Logit Lens analysis; consider ablation studies that isolate edge
    spectrum effects from general dimensionality reduction.
artifact_hash: 694aa60fc8ffd3b190e6ddc550509dfa2e47bde4175f0797a9228a9e466061a8
artifact_path: projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T16:19:38.822775Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents promising results but lacks sufficient statistical rigor to support its central claims. The MTEB benchmark results in Tables 1-4 report single-run point estimates without standard deviations or confidence intervals across random seeds. This is a critical gap: without variance estimates, we cannot assess whether the reported 9-14% improvements are robust or potentially due to random variation.

The ablation study in Table 5 tests multiple filtering configurations (Truncation, Random, Dominant, Secondary, Bulk, Optimal) but all on a single model (Qwen2.5-0.5B) with what appears to be a single run. The "Optimal" configuration achieves 54.19 vs. EmbFilter's 54.57—a difference too small to be meaningful without variance estimates. This raises p-hacking concerns: testing multiple τ values (2, 4, 8) and multiple filtering strategies without pre-specification risks cherry-picking the best result.

The mechanistic claim that the edge spectrum specifically encodes high-frequency tokens rests on correlational Logit Lens analysis (Section 3.2.3, Figure 2). While the Δπ metric shows edge spectrum sensitivity, this is observational evidence. The paper does not rule out alternative explanations: general dimensionality reduction (via Matryoshka-style truncation, Table 5 config 1) could explain improvements independently of the edge spectrum hypothesis.

The three model families tested (Qwen, Llama, Mistral) show consistent patterns, but this represents limited replication. More diverse architectures and independent replication would strengthen claims about universality.

To strengthen scientific evidence: (1) report results across ≥3 random seeds with mean±std, (2) add statistical significance tests between methods, (3) pre-register or clearly justify τ selection, and (4) provide stronger causal evidence distinguishing edge spectrum filtering from generic dimensionality reduction.
