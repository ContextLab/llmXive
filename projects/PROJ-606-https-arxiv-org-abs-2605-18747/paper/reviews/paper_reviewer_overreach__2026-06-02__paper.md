---
action_items:
- id: 6d26dc8e74a6
  severity: writing
  text: The contribution box claims to 'formalize' code as agent harness (e000). However,
    the paper provides a conceptual definition rather than a mathematical formalism
    (e.g., axioms, tuples). Use 'conceptualize' or 'define' to avoid overclaiming
    rigor.
- id: 6770f15f8d2f
  severity: science
  text: "In \xA75.1 (e003), the claim 'Productivity/usability studies show harness\
    \ matters' cites inline-completion studies (Copilot) which differ from the paper's\
    \ definition of agent harness (sandboxes, execution). Clarify if these studies\
    \ support the specific 'agent harness' definition or adjust the claim."
- id: be009599fa6e
  severity: writing
  text: Section 4.3 (e002) states 'The literature lacks formal, persistent representations
    of shared code state.' While qualified later as 'Majority', the heading and initial
    claim overgeneralize given the explicit mention of SyncMind which *does* formalize
    this. Temper the language to 'The dominant literature lacks...'.
artifact_hash: cbd4e8e17c331b3d11d6d3473a72ca30389ded91296199ea84247ea30361db9d
artifact_path: projects/PROJ-606-https-arxiv-org-abs-2605-18747/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T05:25:38.005981Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on over-claiming and over-reach in the manuscript's claims relative to its evidence and scope. The survey provides a comprehensive taxonomy, but several framing claims exceed the provided rigor or evidence.

First, in the `agentcontrib` box (e000), the authors state: "Conceptual framing: We formalize code as agent harness." The term "formalize" typically implies a mathematical or logical structure (e.g., state spaces, transition functions, axioms). The paper defines the concept conceptually ("An agent harness is the software layer...") but does not provide a formal specification. This is a semantic overreach that should be corrected to "define" or "conceptualize" to accurately reflect the contribution's level of rigor.

Second, in Section 5.1 "Code Assistants" (e003), the text claims: "Productivity/usability studies show harness matters," citing `vaithilingam2022expectation` and `mozannar2022reading`. These studies primarily evaluate GitHub Copilot's inline completion capabilities, which differ significantly from the paper's definition of an "agent harness" (which emphasizes sandboxes, execution loops, tool mediation, and state management). Citing inline-completion usability to support claims about *agent harnesses* risks overgeneralizing the evidence. The claim should be qualified to specify that early *tooling* showed value, or the citations should be swapped for studies explicitly evaluating agent-like execution environments.

Third, Section 4.3 (e002) asserts: "The literature lacks formal, persistent representations of shared code state." While the subsequent discussion qualifies this as "Majority of literature," the initial statement and section title present it as a blanket fact. Given that the survey explicitly identifies SyncMind (`Guo2025SyncMind`) as a system that "formally defines repository substrate as ground-truth," the claim that the literature "lacks" such representations is slightly overreaching. It should be phrased as "The majority of surveyed systems..." to avoid contradicting the specific evidence presented within the survey itself.

These issues are primarily semantic and evidentiary framing rather than fatal flaws in the taxonomy or coverage. Adjusting the language to match the level of rigor and evidence will strengthen the manuscript's credibility.
