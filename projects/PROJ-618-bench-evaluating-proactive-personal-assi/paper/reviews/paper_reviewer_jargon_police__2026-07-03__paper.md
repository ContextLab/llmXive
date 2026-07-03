---
action_items:
- id: 11ab00d7b83c
  severity: writing
  text: The manuscript relies heavily on specialized terminology that creates a barrier
    for non-specialist readers, particularly in the Abstract, Introduction, and Evaluation
    Protocol sections. First, the core concept of "hidden intents" is introduced without
    a plain-language definition. The text describes them as "habits, constraints,
    preferences" but relies on the jargon "underspecification" to explain the problem.
    A general reader needs a sentence explaining that this means "requirements the
    user for
artifact_hash: b1a603c95e647ace07f81d632546efe6a0dc736020efd850e81aa8fbc6bf0d17
artifact_path: projects/PROJ-618-bench-evaluating-proactive-personal-assi/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T11:29:52.795644Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on specialized terminology that creates a barrier for non-specialist readers, particularly in the Abstract, Introduction, and Evaluation Protocol sections.

First, the core concept of **"hidden intents"** is introduced without a plain-language definition. The text describes them as "habits, constraints, preferences" but relies on the jargon "underspecification" to explain the problem. A general reader needs a sentence explaining that this means "requirements the user forgot to mention or didn't think to state." Similarly, **"proactivity"** is defined via a citation and abstract concepts like "anticipate user needs." The authors should provide a concrete, jargon-free example (e.g., "an agent that notices you usually order coffee at 9 AM and asks if you want one before you ask") before using the formal definition.

Second, the metrics **"Proc"** and **"Comp"** are introduced as acronyms but then used as standalone nouns throughout the text (e.g., "average Proc spans 43.1–67.0%"). This is a common academic shorthand that alienates readers unfamiliar with the specific notation. The full terms "Proactivity Score" and "Completeness Score" should be used at least once in every paragraph where they appear, or the acronyms should be defined more prominently.

Third, terms like **"terminal status"** (Section 3.1) and **"scaffold"** (Section 4.1) are used without explanation. "Terminal status" is a state-machine term; "final resolution state" is clearer. "Scaffold" is engineering jargon for the underlying code framework; "framework" or "architecture" is more accessible.

Finally, the phrase **"long-horizon"** is used repeatedly. While standard in Reinforcement Learning, it is opaque to generalists. "Long-term" or "multi-step" would be more inclusive. The paper would benefit from a "Glossary of Terms" or a dedicated paragraph in the Introduction translating these technical concepts into plain English.
