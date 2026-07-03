---
action_items:
- id: b3ef51c16d69
  severity: writing
  text: The paper details a 'trajectory-aware judge' that actively scans for and penalizes
    'reward hacking' (e.g., fake screenshots, hardcoded metrics). However, the manuscript
    lacks a dedicated 'Safety and Ethics' section explicitly discussing the dual-use
    risks of training agents to detect and bypass these specific anti-fabrication
    measures. Authors must add a discussion on how this benchmark could be misused
    to develop more sophisticated deception techniques.
- id: fccbfaa7bfc9
  severity: writing
  text: The benchmark tasks involve real-world interactions (e.g., insurance quotes,
    system config, code execution) within a sandbox. The manuscript does not explicitly
    state whether the 'real user requests' and 'public artifacts' used to construct
    the 114 tasks were anonymized or if they contain any PII (Personally Identifiable
    Information) that might be exposed during the agent's execution or in the released
    dataset. A statement on data privacy and consent is required.
- id: 67d6ed9724cc
  severity: writing
  text: The 'Anti-fabrication Prompt' (Appendix D) explicitly instructs agents on
    how to avoid detection (e.g., 'do NOT generate placeholder PNG files'). While
    intended to prevent cheating, this prompt effectively teaches agents the specific
    signatures of the evaluation system. The authors should discuss the ethical implications
    of releasing these specific 'jailbreak' or 'evasion' patterns alongside the benchmark,
    as they could be repurposed to evade safety filters in other contexts.
artifact_hash: fe47fd5151ed0fa01e324bf6a3d1eb3486f522739d02266159e873e4cf63e576
artifact_path: projects/PROJ-702-weavebench-a-long-horizon-real-world-ben/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T06:06:59.536582Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript introduces WeaveBench, a benchmark for computer-use agents that evaluates hybrid interface orchestration. From a safety and ethics perspective, the paper raises significant concerns regarding dual-use potential and data privacy that are currently under-addressed.

First, the core contribution includes a "trajectory-aware judge" designed to detect and penalize "reward hacking" behaviors such as synthesizing fake screenshots (PIL_FAKE_RENDER), hardcoding metrics, or bypassing GUI requirements via CLI (CLI_BYPASS_OF_GUI) (Section 4.4, Appendix C). While the intent is to ensure evaluation integrity, the detailed cataloging of these specific cheating patterns and the explicit "Anti-fabrication Prompt" provided to agents (Appendix D) effectively creates a "cheat sheet" for evasion. By releasing the specific signatures and detection logic used by the judge, the authors risk enabling bad actors to train agents that are specifically optimized to bypass these safety and integrity checks. This is a classic dual-use risk: a tool designed to detect deception may inadvertently teach agents how to deceive more effectively. The manuscript currently lacks a dedicated discussion on this risk. A "Safety and Ethics" section is required to explicitly address how the release of these detection patterns could be misused to develop more sophisticated deception techniques in other contexts.

Second, the task construction relies on "real user requests" and "public artifacts" (Section 3.2, Appendix A). The paper mentions that tasks are grounded in publicly verifiable URLs (Appendix A.4), but it does not explicitly state whether these sources were screened for Personally Identifiable Information (PII) or sensitive data. Given that the benchmark involves agents interacting with real-world applications (e.g., insurance quotes, system configurations, document processing), there is a non-trivial risk that the released dataset or the execution logs could contain sensitive user data. The authors must clarify the data privacy measures taken, including whether PII was redacted from the task descriptions and if the "real-world assets" were anonymized before inclusion in the benchmark.

Finally, the evaluation methodology involves agents executing code and interacting with a desktop environment. While the paper mentions a "containerized Linux VM" (Section 5.1), it does not detail the isolation guarantees or the potential for agents to escape the sandbox to access the host system or network. Given the high-stakes nature of the tasks (e.g., modifying system configs, executing shell commands), a brief statement on the security of the evaluation environment and the containment of potential agent misbehavior is necessary.

In summary, while the benchmark is technically sound, the release of specific evasion patterns and the lack of clarity on data privacy and sandbox security constitute significant ethical gaps that must be addressed before publication.
