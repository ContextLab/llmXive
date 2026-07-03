---
action_items:
- id: 60d7b18bfa74
  severity: science
  text: The claim that masking removes 'crucial signals' in saturated regimes lacks
    direct causal proof. Provide a case study or analysis showing that the specific
    masked tokens contained the gold evidence required for the correct answer, rather
    than just inferring this from performance drops.
- id: '302261046249'
  severity: science
  text: The regression probe uses a 'citation proxy' for live-web benchmarks where
    gold documents are unavailable. This risks circularity as the proxy depends on
    the model's own output. Clarify the limitations of this proxy or provide a sensitivity
    analysis against ground-truth relevance if possible.
- id: a4f3b66098c2
  severity: science
  text: The performance drop in the saturated regime correlates with a surge in tool
    calls. Disentangle whether the collapse is due to 'information loss' (masked content
    was needed) or 'retrieval cost' (agent failed to re-find masked info). Current
    analysis conflates these mechanisms.
artifact_hash: 0662f086c971957827b984215e812ef5eb19c982637f2c1511efa72d77075eda
artifact_path: projects/PROJ-652-https-arxiv-org-abs-2606-00408/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T02:33:01.827441Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper provides a robust empirical characterization of observation masking across a wide range of model sizes (4B–284B) and retrievers, establishing a clear "regime map" where gains are non-monotonic. The sample sizes (e.g., 830 examples for BrowseComp-Plus, 150 trajectories for attention analysis) appear sufficient for the reported statistical trends, and the use of multiple benchmarks strengthens the generalizability of the "three regimes" claim.

However, the mechanistic explanation for the "Model Saturated" collapse relies on a plausible but unproven causal link. The authors argue that masking harms high-capacity models because it removes evidence the model *would* have used (Section 5, "Model-saturated collapse"). While attention maps (Figure 3) show low attention to middle turns, low attention does not equate to "unused" information; the model may rely on a "latent" representation of that context or re-derive it. The paper lacks a direct "ablation of the masked content" experiment (e.g., restoring only the specific tokens that were masked in failed cases) to prove that the *content* of the masked observations was the specific cause of the error, rather than the disruption of the context window structure or the cost of re-searching.

Additionally, the regression probe's use of a "citation proxy" for live-web benchmarks (Appendix A.5) introduces uncertainty. Since gold documents are unavailable for xBench, the SNR metric is derived from the model's own citations. This risks circularity: the model might cite correctly in the No-CM setting simply because it has more context, making the "signal" a byproduct of the context length rather than an intrinsic property of the query. The AUC scores (0.70–0.71) are presented as evidence of separability, but without ground-truth relevance judgments, the interpretation of "signal sparsity" remains speculative.

Finally, the surge in tool calls (+68.7 for GPT-OSS-120B) in the saturated regime suggests that the performance drop might be driven by the agent's inability to efficiently recover from the masking (increased search cost) rather than pure information loss. The current analysis conflates these two factors. Disentangling the "information loss" hypothesis from the "retrieval overhead" hypothesis is necessary to fully validate the proposed mechanism.
