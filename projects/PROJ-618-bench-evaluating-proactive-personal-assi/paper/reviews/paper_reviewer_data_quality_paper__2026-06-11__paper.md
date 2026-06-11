---
action_items:
- id: 1883eacb8f39
  severity: writing
  text: 'Specify the open-source license for the pi-Bench dataset and task definitions.
    Currently, only dependency licenses (Nanobot: MIT, AppWorld: Apache-2.0) are mentioned
    in 2-appendix/experiments.tex.'
- id: 12195384b0a8
  severity: writing
  text: Add a specific commit hash or release tag to the GitHub repository link in
    the Abstract to ensure reproducibility and prevent link rot over time.
- id: 42a933b85e8a
  severity: science
  text: Clarify the provenance of the realistic workflows in 2-appendix/benchmark-construction.tex.
    State whether tasks were synthesized, crowdsourced, or derived from public logs
    to support data quality claims.
- id: 7613abae3f93
  severity: science
  text: Specify the version of AppWorld used for tool simulation in 2-appendix/experiments.tex.
    The URL alone does not guarantee environment stability for future replication.
artifact_hash: 446593595ed3db0a3ea306b2f1debae06a4efb5d82e58c3ca6afc0ab4d9515cf
artifact_path: projects/PROJ-618-bench-evaluating-proactive-personal-assi/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T08:43:47.656036Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript presents a well-structured benchmark with clear schema definitions for tasks (e.g., 0.3-prompt/task_format.tex) and detailed statistics (e.g., 2-appendix/benchmark-statistics.tex). However, several critical data quality metadata elements are missing, impacting reproducibility and long-term usability.

First, **data licensing** is not explicitly stated for the benchmark artifacts themselves. While 2-appendix/experiments.tex notes that the agent scaffold (Nanobot) uses the MIT License and simulated environments (AppWorld) use Apache-2.0, the license for the pi-Bench tasks, hidden intents, and evaluation scripts is absent. This ambiguity limits legal reuse and distribution.

Second, **version control** is insufficient. The GitHub link in the Abstract points to a repository root without a commit hash or release tag. Given the rapid evolution of agent benchmarks, this risks link rot where the code state no longer matches the paper results. A specific tag is required.

Third, **provenance** details are vague. 2-appendix/benchmark-construction.tex states tasks are derived from realistic workflows but does not specify the source corpus (e.g., synthetic generation parameters, public log sources, or crowdsourcing instructions). This affects trust in the data quality and potential biases.

Finally, **dependency versioning** for external tools is incomplete. The AppWorld environment is cited via URL, but the specific version or commit used for the tool simulation is not recorded. Without this, replicating the exact tool behaviors is difficult.

Addressing these metadata gaps is essential for the benchmark to serve as a reliable, long-term resource for the community.
