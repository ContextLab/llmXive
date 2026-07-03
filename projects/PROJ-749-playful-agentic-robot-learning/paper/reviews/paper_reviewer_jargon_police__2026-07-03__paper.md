---
action_items:
- id: 5fcd1ab09d43
  severity: writing
  text: The manuscript relies heavily on domain-specific jargon and undefined acronyms,
    which creates a barrier for readers outside the immediate sub-fields of robotics
    and intrinsic motivation. First, the term Code-as-Policy is introduced in the
    Abstract and Introduction as a central concept but is never explicitly defined.
    While the title suggests it involves code, the specific mechanism (using LLMs
    to synthesize executable programs for control) should be briefly explained upon
    first mention to aid no
artifact_hash: 50abfa42bd37b77889e3563a6ea1bdb0e8be3fa0ecf45caffb5d23cfc888d2a4
artifact_path: projects/PROJ-749-playful-agentic-robot-learning/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T18:59:23.856755Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on domain-specific jargon and undefined acronyms, which creates a barrier for readers outside the immediate sub-fields of robotics and intrinsic motivation.

First, the term **Code-as-Policy** is introduced in the Abstract and Introduction as a central concept but is never explicitly defined. While the title suggests it involves code, the specific mechanism (using LLMs to synthesize executable programs for control) should be briefly explained upon first mention to aid non-specialists.

Second, the acronyms **VLM** (Vision-Language Model) and **VLA** (Vision-Language Action) are used frequently (e.g., Abstract, Section 1, Limitations) without being spelled out at their first occurrence. Standard academic practice requires defining these immediately.

Third, the abbreviation **pp** for "percentage points" appears in the Abstract ("+20.6 pp") and throughout Section 4. This is informal shorthand that should be written out in full for clarity in a formal publication.

Fourth, in Appendix A.1, the term **BDDL** is used to describe the environment generation format. This is a specific planning language acronym that should be defined (e.g., "Basic Domain Definition Language (BDDL)") for readers unfamiliar with automated planning.

Finally, the phrase "**Wilson-bounded** empirical success rate" in Section 3.2 is dense jargon. While the Wilson interval is a standard statistical tool, the phrasing obscures the meaning. A clearer phrasing would be "success rate bounded by the Wilson interval" or "Wilson lower bound of the success rate."

Addressing these points will significantly improve the accessibility of the paper without altering its scientific content.
