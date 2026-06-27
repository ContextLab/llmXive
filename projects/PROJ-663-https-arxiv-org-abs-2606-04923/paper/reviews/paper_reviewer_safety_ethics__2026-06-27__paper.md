---
action_items:
- id: 5522b0c48ee6
  severity: writing
  text: Add a dedicated paragraph in the Limitations or Ethics section discussing
    the dual-use risks of releasing CHERRL, acknowledging that the hacking environment
    could theoretically be used to learn exploitation techniques, and framing the
    release as defensive research.
- id: beae0a416783
  severity: writing
  text: Clarify the ethical compliance of the 'Manual Expert Audit' in Appendix (Section
    app:manual_audit). Explicitly state whether IRB approval or exemption was obtained
    for the author annotators, as this involves human judgment on model outputs.
artifact_hash: eca43eb888bbc8155fd1bf21a6b137ce6bb47419fcb91606da445eda44a63a5a
artifact_path: projects/PROJ-663-https-arxiv-org-abs-2606-04923/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-27T04:37:33.215868Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This paper addresses a critical safety issue: reward hacking in rubric-based RL. The work is fundamentally defensive, aiming to detect and analyze misalignment behaviors rather than exploit them. The use of public datasets (HealthBench, VerInstruct) without personally identifiable information (PII) is appropriate, and the "Artifacts" section (lines 1030-1050) adequately addresses data privacy and licensing.

However, two safety/ethics considerations require clarification before acceptance:

1. **Dual-Use Risk of CHERRL:** The paper introduces and releases a "Controllable Hacking Environment" (CHERRL) that explicitly demonstrates how to inject biases to reproduce reward hacking (Section 3, Eq. 2). While the stated intent is to enable detection research, releasing a tool that systematically teaches how to exploit LLM judges carries dual-use potential. Adversaries could use CHERRL to identify and amplify biases in their own systems. The paper should include a statement in the Limitations or Ethics section acknowledging this risk and emphasizing the defensive purpose of the release.

2. **Human Annotator Ethics:** The "Manual Expert Audit" (Appendix, Section app:manual_audit) involves two paper authors annotating model outputs for shortcut visibility. While the authors note that no personal information was collected, this constitutes human-subject interaction (even if internal). Standard ethical guidelines often require a statement regarding IRB approval or exemption for such annotation tasks. A brief confirmation that this activity was exempt from IRB review or complied with institutional guidelines would strengthen the ethical rigor.

The paper responsibly highlights the negative downstream impacts of reward hacking (e.g., capability degradation in HealthBench, Tables 1-2), which is a positive safety contribution. Addressing the points above will ensure the paper meets publication standards for safety-related research releasing vulnerability tools.
