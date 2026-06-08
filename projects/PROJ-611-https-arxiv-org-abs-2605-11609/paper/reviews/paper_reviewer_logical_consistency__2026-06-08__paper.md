---
action_items:
- id: cba824a5abfa
  severity: writing
  text: Conclusion (Sec 6) claims 'sign reversal carrying most of the gain' but Qwen3-8B
    ablation (Table ablation_qn_table) shows 'rev. KL' (30.6 Avg) matches SD (30.6
    Avg), implying JSD shape is the primary driver on that model. Clarify this nuance
    to avoid over-attribution.
- id: f963997650ac
  severity: writing
  text: Claim of 'naturally bounded advantage' (Sec 3.2) is imprecise; Lemma 1(iii)
    shows bounds apply only to the deliberation side (positive advantage), while negative
    advantages are unbounded. Refine phrasing to reflect one-sided bounding.
artifact_hash: 5a5c1b2fc5b93010078510a2719b14ae8df452ff19cefaab0b0cc9b505e14712
artifact_path: projects/PROJ-611-https-arxiv-org-abs-2605-11609/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-08T14:11:12.870701Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a logically coherent framework: it diagnoses a structural PMI bias in standard self-distillation (Sec 3.1), proposes AntiSD to invert the gradient via JSD ascent (Sec 3.2), and validates the mechanism with ablations (Sec 4.3). The derivation of the per-token advantage $-\varphi(u_t)$ and its properties (Appendix Lemma 1) consistently support the stability claims, particularly regarding the entropy gate.

However, there is a discrepancy between the conclusion and the ablation evidence regarding the source of performance gains. The conclusion states the gain is "consistent with sign reversal carrying most of the gain on top of an already-bounded shape" (Sec 6). Yet, the Qwen3-8B ablation (Table `ablation_qn_table`) shows "rev. KL" (sign reversal only) achieves 30.6 Avg, identical to default SD (30.6 in Table `main_table`), while canonical AntiSD reaches 65.7. On this model, the JSD shape accounts for the entire gain, contradicting the claim that sign reversal carries "most" of it. While Qwen3-4B shows some gain from sign reversal alone (45.9 → 49.5 in Table `ablation_q4_table`), the generalization in the conclusion overstates the role of direction inversion on models where stability relies on the shape.

Additionally, the claim that AntiSD yields a "naturally bounded advantage" (Sec 3.2) is slightly imprecise. Lemma 1(iii) demonstrates the advantage is bounded only on the deliberation side ($-\varphi(u) \le 0.34$), while the shortcut side (negative advantage) remains unbounded. This distinction is critical for understanding the stability mechanism but is glossed over in the main text.

These issues are primarily matters of precision and claim calibration rather than fatal logical flaws. The core mechanism holds, but the text should be adjusted to accurately reflect the ablation data and mathematical bounds.
