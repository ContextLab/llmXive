---
action_items:
- id: 7547f582c5fb
  severity: writing
  text: The manuscript relies heavily on specialized terminology and internal project
    shorthand that excludes non-specialist readers. While the authors define some
    terms (like 'session'), several key concepts are introduced without sufficient
    plain-language explanation. First, the term 'claws' is introduced in the Introduction
    as a synonym for 'harnesses' following a 'recent line of Claw-style benchmarks.'
    However, the text does not explicitly state that 'claw' is a shorthand for 'agent
    harness' before
artifact_hash: 436f60fbb896e41d063ceb9811d2249a06e1b5eaa235430cfaccb20cf6596607
artifact_path: projects/PROJ-773-enterpriseclawbench-benchmarking-agents/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T13:15:27.393796Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on specialized terminology and internal project shorthand that excludes non-specialist readers. While the authors define some terms (like 'session'), several key concepts are introduced without sufficient plain-language explanation.

First, the term **'claws'** is introduced in the Introduction as a synonym for 'harnesses' following a 'recent line of Claw-style benchmarks.' However, the text does not explicitly state that 'claw' is a shorthand for 'agent harness' before using it as a standalone noun. This creates a barrier for readers unfamiliar with the specific 'Claw' ecosystem. The phrase 'we call such harnesses claws' is a definition, but it is buried in a complex sentence. A clearer, standalone definition is needed.

Second, the term **'fixtures'** is used repeatedly (Abstract, Section 2) to refer to input files or data dependencies required for a task. In software testing, 'fixtures' is standard, but in the context of general AI agent evaluation, 'input files' or 'required data' is more accessible. The text assumes the reader understands that 'recovered fixtures' means 'recovered input files.'

Third, **'TaskInstances'** (Section 2, 'Benchmark statistics') is capitalized and used as a proper noun without definition. It appears to refer to raw, unprocessed task candidates from the session archive. Defining this as 'raw task candidates' or 'initial task records' would improve clarity.

Fourth, the abbreviation **'hm'** (for 'harness--model') is defined via a LaTeX macro but the concept of the 'harness--model combination' is central to the paper's argument. The text often refers to 'hm combinations' or 'hm performance' without ensuring the reader fully grasps that this refers to the specific pairing of an agent framework (harness) and a language model.

Finally, terms like **'rubrics'** (Abstract, Section 2) and **'skill subclasses'** (Section 2) are used without plain-English equivalents. 'Rubrics' should be clarified as 'scoring criteria' or 'evaluation guidelines,' and 'skill subclasses' should be explained as 'specific types of tasks within a broader role category.'

These issues, while fixable with minor edits, currently create a jargon-heavy barrier that limits the paper's accessibility to a broader audience beyond the immediate 'Claw' research community.
