---
action_items:
- id: f1cd14c81012
  severity: writing
  text: 'The logical consistency of the paper''s core claims requires clarification
    in three areas. First, in Section 3.1, the authors claim that training a teacher
    model on a single reference-garment pair with a *mismatch* (where the reference
    person wears a different garment than the target) implicitly enables the model
    to learn "single-garment switching." The logical leap here is significant: the
    paper does not provide a mechanism explaining how a model trained on *one* specific
    mismatched pair can gen'
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:09:26.859328Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The logical consistency of the paper's core claims requires clarification in three areas.

First, in Section 3.1, the authors claim that training a teacher model on a single reference-garment pair with a *mismatch* (where the reference person wears a different garment than the target) implicitly enables the model to learn "single-garment switching." The logical leap here is significant: the paper does not provide a mechanism explaining how a model trained on *one* specific mismatched pair can generalize to *arbitrary* garment switching during inference without ever seeing multi-garment sequences. The premise that "mismatch = switching capability" is asserted but not derived from the training objective or architecture.

Second, the logic governing the "Training-Free KV Cache Rescheduling" in Section 3.3 contains a potential contradiction. The authors argue that "Historical KV Withdraw" is necessary because the model relies too heavily on historical context, preventing the new garment from appearing. However, immediately after withdrawing history, they introduce "Reference KV Disentangle," which replaces the static reference KV with the KV of the *last historical frame*. If the model is already biased toward historical KVs (causing the garment to persist), reintroducing a historical frame as the new reference seems to reinforce the very bias the authors are trying to break. The causal chain explaining how these two opposing operations (withdrawing history vs. re-injecting history as reference) jointly result in "seamless transitions" is not clearly articulated.

Third, the ablation study in Table 2 attributes the reduction in motion distortion primarily to "Gradient-Reweighted DMD." However, the baseline "Naive DMD" is compared against a setup that also includes "Self-Forcing" (as mentioned in Sec 3.2). The paper does not isolate whether the improvement comes from the reweighting strategy itself or simply from the interaction between Self-Forcing and the specific temperature coefficient $\tau$. The claim that the *reweighting* specifically solves the "unequal difficulty of frames" is plausible but not rigorously proven by the provided ablation, which conflates the distillation strategy with the forcing mechanism.
