---
action_items:
- id: 6f24cbb745e8
  severity: writing
  text: Add a Data Availability statement explicitly confirming that all released
    synthetic scenarios have been scrubbed of PII (e.g., phone numbers, employee IDs)
    to prevent privacy leakage under the open-source license.
- id: 0f9fa270fbad
  severity: writing
  text: Include a Dual-Use statement addressing the potential misuse of the 9 adversarial
    ITSM scenarios (Section "Enterprise ITSM Workflows") for training agents to bypass
    safety guardrails.
- id: 08fb81144cfb
  severity: writing
  text: Disclose funding sources and potential Conflicts of Interest, particularly
    given the framework is hosted on the ServiceNow GitHub organization while evaluating
    competitors (OpenAI, Google, ElevenLabs).
artifact_hash: 9779db764c5e6d634d1311a56a0ec38a708da09d28018889a272cb266ef418fe
artifact_path: projects/PROJ-574-eva-bench-a-new-end-to-end-framework-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-07T16:38:19.887269Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on safety, ethics, and data privacy concerns within the EVA-Bench framework.

**Data Privacy and Consent:**
The manuscript states in the Abstract that the benchmark data will be released under an open-source license. While the "Conversation Simulation" section (Section 3.1) correctly identifies the use of bot-to-bot audio conversations rather than human participants—avoiding IRB requirements for human subjects—the provided text lacks an explicit Data Privacy statement. The "Enterprise ITSM Workflows" (Section "Data Workflows") and "Scenario Examples" (Section 5.1) include synthetic PII such as employee IDs (`EMP093274`), phone numbers (`6158`), and OTP codes (`481629`). Although these appear synthetic, there is no declaration confirming that the released dataset has been rigorously scrubbed to prevent accidental leakage of real-world patterns or residual PII. Given the open-source release plan, a formal statement on data sanitization is required to mitigate privacy risks.

**Dual-Use Risks:**
The framework includes "adversarial variants" in the ITSM domain (Section "Data Workflows", 9 scenarios) and a specific "Adversarial" Healthcare HRSD example (Section 5.3, Scenario A10). These scenarios are designed to test agent robustness against policy violations (e.g., backdated FMLA requests). However, releasing these adversarial scripts without restriction could inadvertently aid malicious actors in training voice agents to bypass safety guardrails or manipulate enterprise systems. A Dual-Use statement is necessary to contextualize the release of these specific adversarial materials and outline any intended usage restrictions.

**Conflicts of Interest:**
The project metadata indicates the repository is hosted under `servicenow.github.io/eva`, and the authors are affiliated with ServiceNow. The paper evaluates commercial systems from competitors (OpenAI, Google, ElevenLabs). There is no Funding or Conflict of Interest disclosure section visible in the provided text. Standard ethical practice requires transparency regarding potential biases in benchmarking competitor technologies, especially when the benchmark provider is a direct industry competitor.

**Recommendations:**
To proceed, the authors must add the three action items listed in the frontmatter: a data sanitization confirmation, a dual-use warning regarding adversarial scenarios, and a conflict of interest disclosure. These are writing-level fixes but are critical for the ethical integrity of the release.
