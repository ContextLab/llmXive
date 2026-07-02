---
action_items:
- id: 6cb63c4c2f72
  severity: writing
  text: The manuscript relies heavily on specialized terminology and coined phrases
    that may alienate non-specialist readers, particularly those outside the immediate
    field of agentic AI systems. First, the term "computer-use agent" is introduced
    in the Abstract and Section 1 without definition. While the authors later describe
    it as an agent that "perceives the rendered interface through actions such as
    clicking and scrolling," the initial usage treats it as a known category. A brief
    parenthetical expl
artifact_hash: c961c4f131b3e6127c44320a12751b53bf58ee9a86ae78d22dc551848222c6a2
artifact_path: projects/PROJ-719-data-journalist-agent-transforming-data/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T21:38:55.883851Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on specialized terminology and coined phrases that may alienate non-specialist readers, particularly those outside the immediate field of agentic AI systems.

First, the term **"computer-use agent"** is introduced in the Abstract and Section 1 without definition. While the authors later describe it as an agent that "perceives the rendered interface through actions such as clicking and scrolling," the initial usage treats it as a known category. A brief parenthetical explanation (e.g., "an agent that interacts with a browser interface") at first use is necessary.

Second, the paper frequently uses **"scrollytelling"** (Section 5, "Analytical genres amplify..."). This is a niche term from the data visualization community. Replacing it with "scroll-driven storytelling" or "interactive scrolling narratives" would improve accessibility without losing meaning.

Third, the **"Inspector"** is a core contribution, yet it is introduced in the Abstract and Section 1 as a proper noun without a functional definition for the lay reader. The text assumes the reader understands it is a UI panel or a specific agent role immediately. A phrase like "a transparency panel (the 'Inspector') that..." would bridge this gap.

Fourth, the metric **"angle coverage"** (Section 4) is used repeatedly. While the mathematical definition follows, the term itself is jargon. "Narrative angle overlap" or "topic coverage similarity" would be more intuitive.

Finally, the term **"cross-family verifier"** (Section 4) appears in the context of using a different model family to verify claims. This is a specific technical constraint that should be briefly explained (e.g., "a verifier from a different model family to prevent bias") rather than left as a black-box term.

These changes are minor but essential for ensuring the paper's contributions are accessible to the broader data journalism and general AI communities, not just those deeply embedded in the current agentic workflow literature.
