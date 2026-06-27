---
action_items:
- id: b2fb48923c24
  severity: science
  text: Section 4 claims general mechanisms ('discoverability is driven by...', 'exploitability
    hinges on...') based on only 4 bias types across 2 datasets. Soften these causal
    claims to reflect the limited sample size (e.g., 'preliminary evidence suggests').
- id: c871d2dd9128
  severity: writing
  text: Abstract claims 'precise identification of hacking onset'. Section 3.3 defines
    this as an 'operational reference' based on threshold sweeps. Align the abstract
    claim with the operational nature of the ground truth.
- id: 8a5ca34440ac
  severity: writing
  text: While Section 5 notes 'composite real-world biases are left for future work',
    the Abstract and Introduction frame RHDA as a general detection system. Clarify
    that RHDA's evaluation is strictly on synthetic injected biases to avoid overclaiming
    real-world applicability.
artifact_hash: eca43eb888bbc8155fd1bf21a6b137ce6bb47419fcb91606da445eda44a63a5a
artifact_path: projects/PROJ-663-https-arxiv-org-abs-2606-04923/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-27T04:36:12.877961Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper introduces CHERRL, a valuable testbed for studying reward hacking. However, there are instances of overreach in the generalization of findings and the scope of the detection system.

1.  **Generalization of Mechanism Findings (Section 4)**: The paper states, "Our findings reveal that discoverability is driven by the bias's entanglement... whereas exploitability hinges on the intrinsic complexity... demonstrating that the specific nature of the latent bias dictates the speed and severity of hacking." This causal language ("dictates", "driven by") is too strong given the empirical basis: only 4 bias types (Lexical, Tone, Self-praise, Format) across 2 datasets, with 2 settings failing to produce hacking. These are preliminary observations, not established laws. The text should be softened to reflect the limited sample size (e.g., "in our testbed, we observe...").

2.  **"Precise" Onset Identification (Abstract & Section 3.3)**: The Abstract claims CHERRL enables "precise identification of hacking onset." However, Section 3.3 admits the onset is an "operational reference" derived from threshold sweeps and internal expert audits, acknowledging that "true quality... is unobservable." "Precise" implies ground truth accuracy, which contradicts the operational definition. Use terms like "reproducible" or "operational" instead.

3.  **Detection System Scope (Abstract & Section 5)**: The Abstract introduces RHDA for "automatically detecting reward hacking onset." While Section 5 clarifies that "composite real-world biases are left for future work," the framing suggests broader applicability. The evaluation is strictly on synthetic injected biases. The Abstract should explicitly qualify that RHDA is evaluated on controlled, single-bias scenarios to avoid implying readiness for complex, real-world multi-bias environments.

These changes will ensure the claims align with the empirical evidence provided.
