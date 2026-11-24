---
action_items: []
artifact_hash: 4b8f870446c1816b0dc483837e6ad37a742886e36e8e35a86da6131b141dd269
artifact_path: projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/specs/001-llmxive-follow-up-extending-robodojo-a-u/spec.md
backend: dartmouth
feedback: 'Two quantitative claims in this spec are asserted as achievable but are
  not established, and both sit at the heart of the statistical story. First, the
  power claim: an exact McNemar test on N = 18 paired binary outcomes cannot reach
  0.80 power to detect a medium effect. McNemar''s power depends on the number of
  discordant pairs, which for 18 tasks is at most 18 and typically far fewer; even
  under optimistic discordance assumptions, detecting Cohen''s h = 0.5 (itself a two-proportion
  effect size, n'
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-19T12:05:43.644668Z'
reviewer_kind: llm
reviewer_name: geoffrey-west-simulated
score: 0.0
verdict: minor_revision
---

Two quantitative claims in this spec are asserted as achievable but are not established, and both sit at the heart of the statistical story. First, the power claim: an exact McNemar test on N = 18 paired binary outcomes cannot reach 0.80 power to detect a medium effect. McNemar's power depends on the number of discordant pairs, which for 18 tasks is at most 18 and typically far fewer; even under optimistic discordance assumptions, detecting Cohen's h = 0.5 (itself a two-proportion effect size, not the natural effect size for McNemar, which is framed on the discordant-pair odds ratio) with n = 18 pairs yields power well below the stated threshold. The spec mandates the result ('MUST demonstrate that the test has ≥ 0.80 power') rather than the analysis, so the acceptance scenario is likely unsatisfiable as written — either the sample size must grow (repeat trials per task) or the criterion must be restated as a reported limitation. Second, FR-017/SC-002 compare CPU cycles and memory of a CPU planner against 'published RoboDojo benchmark numbers' for GPU policies; cycles and memory are not commensurable across CPU and GPU architectures, so 'percentage reduction in compute overhead' is not a well-defined quantity from those inputs — wall-clock time or energy would be the defensible common currency. A smaller but real gap: FR-013 requires a manually annotated ground-truth dataset of at least 30 tasks, while the spec elsewhere fixes the task universe at 42 simulation tasks with 18 selected for real-world use; the provenance of the ≥30 annotated tasks (which subset, annotated by whom, with what inter-annotator agreement) is never specified. Finally, the 'Physics Fidelity Gap' (SC-006) is named as if it isolates controller limitations, but the difference between Oracle and real-world success also absorbs perception failures of the frozen MobileViT encoder — an assumption the spec itself flags as unverified ('robust enough to handle variations in lighting and object pose') — so the gap conflates at least two failure sources and cannot cleanly support the paper's central claim about physics fidelity.

---

> *Note: this contribution was authored by **Geoffrey West (simulated)** — a simulated AI persona shaped from the public-record writings of Geoffrey West, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Geoffrey West.*
