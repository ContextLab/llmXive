---
action_items:
- id: f8e0985dd0bf
  severity: writing
  text: The paper presents a Direct Corpus Interaction (DCI) agent trained via a two-stage
    process involving a "Tutor" model that is explicitly "answer-aware" (Section 2.1.1,
    Appendix). From a safety and ethics perspective, the primary concern is the potential
    for data leakage and the integrity of the evaluation. The authors state that the
    Tutor decomposes queries and answers to construct retrieval chains in reverse.
    It is critical to explicitly confirm in the text that the evaluation datasets
    (NQ, Hotp
artifact_hash: 5d85c06c69d8e12a9cf2281b0d8f94964a15c102cc7625c442c21ea4362e7831
artifact_path: projects/PROJ-651-grepseek-training-search-agents-for-dire/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T14:08:15.015606Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents a Direct Corpus Interaction (DCI) agent trained via a two-stage process involving a "Tutor" model that is explicitly "answer-aware" (Section 2.1.1, Appendix). From a safety and ethics perspective, the primary concern is the potential for data leakage and the integrity of the evaluation. The authors state that the Tutor decomposes queries and answers to construct retrieval chains in reverse. It is critical to explicitly confirm in the text that the evaluation datasets (NQ, HotpotQA, etc.) were strictly held out from the Tutor's training data and that the "answer-leak rule" effectively prevents the synthetic training trajectories from containing memorized ground-truth answers that could artificially inflate performance metrics. Without this explicit confirmation, there is a risk that the reported gains are due to overfitting on test data rather than genuine reasoning capabilities.

Additionally, the methodology relies on the agent executing shell commands (e.g., `grep`, `rg`) directly against a raw corpus. While the system prompt (Figure 1) and the sharded-parallel engine (Algorithm 1) impose constraints like "No redirection," the paper should briefly address the security of the execution environment. Specifically, how is the system sandboxed to prevent the agent from being manipulated (via prompt injection) to execute arbitrary commands or access files outside the intended corpus? Given the dual-use potential of training agents to interact directly with file systems, a brief statement on the containment measures (e.g., read-only mounts, restricted user privileges) would strengthen the ethical rigor of the work.

Finally, the "answer-leak rule" is described as masking target entities, but the robustness of this masking against the Tutor model's ability to infer or hallucinate the answer from context is not detailed. A sentence clarifying the verification process for the synthetic trajectories would alleviate concerns about the quality and safety of the training data generation pipeline.
