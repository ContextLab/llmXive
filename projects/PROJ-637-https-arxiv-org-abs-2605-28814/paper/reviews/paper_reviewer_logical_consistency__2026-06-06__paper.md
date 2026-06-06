---
action_items:
- id: e87e33d159e7
  severity: writing
  text: Clarify whether 'answer reweighting' is an integral component of BES or an
    external MaxRL technique. The Method section defines BES as a search algorithm
    agnostic to training, but the Ablation study treats reweighting as a BES component.
    Explicitly distinguish 'BES Search' from 'BES + Training Tricks' to ensure logical
    consistency between definition and experimental claims.
- id: 2bbbd447c111
  severity: writing
  text: Align the title 'Self-Improving Language Models' with the inclusion of inference-time
    experiments. While the abstract clarifies both post-training and inference, the
    title suggests model weight updates. Consider refining the title or explicitly
    stating that 'self-improvement' encompasses inference-time search refinement to
    avoid semantic inconsistency.
artifact_hash: d74e7ce3cbfe7aea4f0dad766af5b0e41093c35f05a067517ae8e48026ef85b2
artifact_path: projects/PROJ-637-https-arxiv-org-abs-2605-28814/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-06T15:33:52.955100Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a logical framework where Bidirectional Evolutionary Search (BES) addresses sparse verification and limited exploration. The theoretical claims (Theorem 1: Shell Escape, Theorem 2: Sample Complexity) follow logically from the stated assumptions (e.g., linear block total correlation, independent sub-goal satisfaction). The mathematical derivations in the Appendix are consistent with the main theorems. The experimental results (Tables 1-3) logically support the claim that BES outperforms baselines by demonstrating improvements in accuracy and search efficiency across tasks.

However, there are definitional inconsistencies between the Method section and the Experiments. In Section 5.3, BES is defined as a sampling/search algorithm agnostic to the training method. Yet, in the Ablation Study (Section 6.3), "answer reweighting" (a MaxRL component) is treated as a component of "Ours" that can be removed. The text states "removing answer reweighting... still outperforming... MaxRL baselines," implying BES Search alone is effective, but the "Full Ours" curve includes external reweighting. This creates ambiguity about what "BES" contributes versus what the training loop contributes. For logical consistency, the definition of "BES" must be uniform: either reweighting is part of the proposed framework (and thus described in Method) or it is an external booster (and thus "BES" in the ablation refers only to the search component).

Additionally, the title "Self-Improving Language Models" primarily connotes post-training weight updates. While the paper covers inference-time search (Open Problem Solving), where weights remain static, the title does not explicitly reflect this scope. The abstract clarifies this, but the title remains slightly semantically inconsistent with the inference claims.

Finally, Theorem 2 assumes binary sub-goal satisfaction probabilities ($p_i$) to derive sample complexity, while the MuSiQue experiment uses continuous embedding similarity scores for sub-goals. While this is a reasonable practical extension, the paper should explicitly acknowledge that the theoretical bound applies to the binary case, and the continuous implementation is an empirical adaptation. This ensures the theoretical claim is not overstated relative to the experimental setup. These issues require clarification but do not invalidate the core logical argument.
