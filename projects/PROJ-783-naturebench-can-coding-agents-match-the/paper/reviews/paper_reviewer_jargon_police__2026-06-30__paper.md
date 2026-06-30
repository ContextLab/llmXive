---
action_items:
- id: 9cf0b7f9586a
  severity: writing
  text: The manuscript relies heavily on field-specific shorthand that obscures meaning
    for non-specialist readers. The most critical issue is the unexplained use of
    "SOTA" (State-Of-The-Art) in the title, abstract, and throughout the text. While
    common in AI circles, this acronym is undefined at first use, violating standard
    accessibility guidelines. It should be expanded to "state-of-the-art" or "best
    published performance" on first mention and subsequently replaced with plain language
    where possible.
artifact_hash: a6c4bf4c6300b132fd82818749a0c8d087f9c694f2c1e50110083271605915a9
artifact_path: projects/PROJ-783-naturebench-can-coding-agents-match-the/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T20:48:54.078793Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on field-specific shorthand that obscures meaning for non-specialist readers. The most critical issue is the unexplained use of "SOTA" (State-Of-The-Art) in the title, abstract, and throughout the text. While common in AI circles, this acronym is undefined at first use, violating standard accessibility guidelines. It should be expanded to "state-of-the-art" or "best published performance" on first mention and subsequently replaced with plain language where possible.

In Section 4 (NatureBench), the metric $g$ is introduced via a formula without a preceding plain-English definition of what "relative gap" implies in this context. The symbol $\gimp_i$ is also used without clear textual explanation of its components for a general audience.

Section 5 introduces the term "harnesses" to describe the evaluation environments. This is industry jargon; "evaluation frameworks" or "testing environments" would be more universally understood. Similarly, the phrase "methodological translation" is used as a specific category of success (45.5% of cases) but is never defined. Does this mean converting a scientific problem into a standard machine learning task? This concept needs a brief, jargon-free explanation.

Finally, terms like "information firewall" (Section 2) and "containerized task packages" are used without context. While "containerized" is standard in software engineering, "information firewall" is metaphorical here and should be clarified as "a mechanism that prevents access to solution-specific code." These changes are necessary to ensure the paper's findings on scientific discovery are accessible to the broader scientific community, not just AI engineers.
