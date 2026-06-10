---
action_items:
- id: d9d4f5a33ca9
  severity: writing
  text: Define 'LLM' (Large Language Model) at first use in Abstract.
- id: 14d1ebe01acf
  severity: writing
  text: Spell out 'SOC' (Standard Occupational Classification) and 'O*NET' (Occupational
    Information Network) in Abstract.
- id: 88fe7e6ca8fb
  severity: writing
  text: Define 'harness' and 'backbone' with plain English equivalents (e.g., 'orchestration
    system', 'foundation model') in Abstract/Intro.
- id: acb36a08dce0
  severity: writing
  text: Define common acronyms (CLI, GUI, VM, API, JSON, TSV) at first occurrence
    in Introduction or Appendix.
- id: 2828ef28dd24
  severity: writing
  text: Define domain-specific acronyms (CAD, CAM, PLC, SCADA, SPC, URDF, MSA, VST,
    DAW, MIDI) in relevant Appendix sections.
- id: cc6dff66529b
  severity: writing
  text: Replace 'GDP relevant' with 'economically significant' for broader accessibility.
- id: b07100c643b3
  severity: writing
  text: Define 'MCP' (Model Context Protocol?) in Appendix A.1 where 'CUA MCP bridge'
    is mentioned.
- id: 95f3fc40eb30
  severity: writing
  text: Clarify 'vCPUs', 'RAM', and 'GPU' definitions in Appendix A.4.
artifact_hash: f7c4cdebe7449d4f51e2127cea7b868f7e8092d99e5958aa9629c6a9a2cf1332
artifact_path: projects/PROJ-688-agents-last-exam/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T19:36:31.769404Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on jargon overuse and accessibility for non-specialist readers. While the paper introduces a significant benchmark, the density of undefined acronyms and field-specific terminology creates unnecessary barriers.

**1. Undefined Acronyms at First Use**
The Abstract introduces several acronyms without definition. "LLM" appears in "LLM-as-judge" without spelling out "Large Language Model". "SOC" and "O*NET" are referenced as "the U.S. federal occupational taxonomy," but the full names (Standard Occupational Classification; Occupational Information Network) should be provided on first mention to aid general readers. Similarly, "GDP relevant" (Abstract, Conclusion) is slightly opaque; "economically significant" is clearer.

**2. Internal Terminology (Harness, Backbone, GCUA)**
The terms "harness" and "backbone" are used throughout (Abstract, Table 1, Section 2.2) to describe the agent orchestration system and the foundation model, respectively. These are community-specific metaphors. Section 2.2 defines "Generalist CUA-agent (GCUA)," but "CUA" (Computer-Use Agent) and "GCUA" should be introduced with plain English descriptors (e.g., "a generalist agent capable of interacting with computer interfaces") before relying on the acronym. In Section 2.2, "CLI-agents" and "GUI-agents" appear; "CLI" and "GUI" should be defined as Command Line Interface and Graphical User Interface upon first use in the main text.

**3. Domain-Specific Jargon in Appendices**
The appendices contain numerous industry-specific acronyms that remain undefined, assuming reader expertise. For example:
- **Appendix A.1:** "MCP server" (Model Context Protocol?) is not defined.
- **Appendix A.3:** "CAD/CAM", "PLC", "SCADA", "SPC", "URDF", "MSA" appear without expansion.
- **Appendix A.4:** "STL", "point cloud", "VST", "DAW", "MIDI", "UV" are used assuming familiarity with manufacturing, audio, and 3D graphics standards.
- **Appendix A.6:** "vCPUs", "RAM", "GPU" are standard but should be briefly noted if the paper claims broad relevance.

**4. Recommendation**
To improve accessibility, the authors should add a "Glossary" or ensure every acronym is expanded at first mention. Where possible, replace community jargon ("backbone", "harness") with descriptive plain English ("foundation model", "orchestration system") or provide explicit definitions in the Introduction. This will align with the paper's stated goal of measuring "GDP-relevant impact" by making the evaluation instrument understandable to a wider economic and policy audience.
