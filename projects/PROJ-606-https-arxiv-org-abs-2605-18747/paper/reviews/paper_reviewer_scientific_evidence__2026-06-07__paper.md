---
action_items:
- id: 61d8c436797a
  severity: science
  text: Add a table categorizing evidence sources (peer-reviewed, preprint, tech report,
    blog) to clarify reliability of performance claims.
- id: ae9fde6b0846
  severity: science
  text: Include explicit caveats on the reproducibility and verification of proprietary
    system evaluations (e.g., Claude Code, Codex).
- id: 4d8fe91e438f
  severity: science
  text: Expand discussion on benchmark metric comparability when aggregating results
    across SWE-bench, AgentBench, and proprietary evals.
artifact_hash: cbd4e8e17c331b3d11d6d3473a72ca30389ded91296199ea84247ea30361db9d
artifact_path: projects/PROJ-606-https-arxiv-org-abs-2605-18747/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-07T10:27:00.413895Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

This re-review confirms that the three prior action items regarding scientific evidence remain unaddressed in the current revision. First, regarding Item 61d8c436797a, no table categorizing evidence sources (peer-reviewed vs. preprint vs. proprietary blog) is present in Section 6 (Emerging Fields) or Section 7 (Open Problems). This omission obscures the reliability hierarchy of the performance claims cited, such as LingmaAgent's 43.3% resolution rate in Section 6.1 which relies on internal benchmarks. Second, Item ae9fde6b0846 requested explicit caveats on proprietary evaluations (Claude Code, Codex). While Section 6.1 mentions these systems, it lacks a specific disclaimer on the reproducibility barriers inherent to closed-source evals compared to open benchmarks like SWE-bench. Readers cannot assess the verification status of claims derived from these black-box systems. Third, Item 4d8fe91e438f asked for expanded discussion on benchmark metric comparability. Section 7.1 discusses oracle adequacy but does not explicitly address the heterogeneity of metrics when aggregating results across SWE-bench, AgentBench, and proprietary dashboards. Without these clarifications, the survey's synthesis of performance claims risks conflating disparate evidence qualities. These items are critical for maintaining the scientific rigor expected of a survey paper establishing a new taxonomy, ensuring readers distinguish between empirically verified results and vendor-reported metrics. Please address these evidence transparency issues before acceptance.
