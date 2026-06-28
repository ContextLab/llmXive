---
action_items:
- id: 83982cbee704
  severity: writing
  text: Clarify the specific criteria used to exclude security-sensitive issues from
    the 350-instance benchmark, as claimed in Appendix I. Upstream SWE-bench datasets
    have historically contained security-related bugs.
- id: 226de5d1c64c
  severity: writing
  text: Add a statement regarding the scrubbing of Personally Identifiable Information
    (PII) from GitHub issue discussions included in the benchmark dataset.
- id: f57d366d7611
  severity: writing
  text: Include a Conflict of Interest statement regarding the evaluation of models
    from companies where authors may have affiliations (e.g., TokenRhythm, Infinigence
    AI).
- id: 333f12222651
  severity: science
  text: Detail the security measures ensuring Docker containers cannot escape to the
    host system during agent execution, given the exec tool access granted to agents.
artifact_hash: d91d9216ec1b23d5ae21a0d631e31b9f94ceb55943984c394279379a22a67899
artifact_path: projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T17:51:23.324098Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This review focuses on safety, ethics, and dual-use risks associated with the Claw-SWE-Bench dataset and evaluation protocol.

**Dual-Use and Security Risks**
The paper acknowledges dual-use risks in Appendix I ("Broader impacts and ethical considerations"), noting that improved coding agents could be applied to "autonomous exploitation." However, the mitigation claim—"inheriting the upstream curation that excludes security-sensitive issues"—requires stronger substantiation. SWE-bench and its derivatives have historically included instances related to security vulnerabilities. Without explicit documentation of the filtering process used to ensure no security-critical bugs remain in the 350-instance set, there is a risk that the benchmark inadvertently facilitates vulnerability discovery or exploitation training. Please provide specific exclusion criteria or a statement confirming that security-related issues were manually vetted and removed.

**Data Privacy and Consent**
The benchmark aggregates real GitHub issues and repository code. While public, these issues may contain Personally Identifiable Information (PII) such as email addresses, usernames, or internal code references. The manuscript does not explicitly state whether PII scrubbing was performed during dataset construction. To align with data ethics standards (e.g., Datasheets for Datasets~\cite{gebru_datasheets}), please add a section detailing how PII was handled and whether consent was considered for any non-public code snippets included.

**Conflict of Interest**
Several authors are affiliated with TokenRhythm and Infinigence AI, while the evaluation includes proprietary models (e.g., GPT-5.5, Claude Opus 4.7). A formal Conflict of Interest statement is missing from the manuscript. This should be added to ensure transparency regarding potential biases in model selection or result reporting.

**Sandbox Security**
Section D.1 describes granting agents `exec` tool access within Docker containers. While sandboxed, the evaluation infrastructure itself must be secure against container escape vulnerabilities. Please detail the security measures (e.g., seccomp profiles, read-only filesystems) implemented to prevent agents from affecting the host system during evaluation.

These revisions are necessary to ensure the benchmark does not inadvertently enable harmful activities and adheres to responsible AI research standards.
