---
action_items:
- id: 36455a1c20c8
  severity: science
  text: 'Figure 3: ''MapCoder'' appears in both the ''Planning'' and ''Tool Use''
    rows, but the figure provides no visual distinction (e.g., color, icon, or label)
    to indicate if it is the same work or different variants, creating ambiguity.'
- id: dd499c7a964e
  severity: science
  text: 'Figure 3: ''AgentCoder'' appears in both the ''Tool Use'' and ''Control''
    rows with the same logo and year (2023), yet the figure lacks a mechanism to clarify
    if this is a single work spanning categories or a duplicate entry.'
- id: ebb1b96b150f
  severity: science
  text: 'Figure 3: ''OpenHands'' appears in both the ''Tool Use'' and ''Optimization''
    rows with the same logo and year (2025), but the figure does not visually distinguish
    between these instances or explain the relationship.'
- id: c72c3d2483c3
  severity: science
  text: 'Figure 3: ''SWE-Agent'' appears in both the ''Memory'' and ''Control'' rows
    with the same logo and year (2024), but the figure lacks a legend or visual cue
    to clarify if this is the same work or distinct variants.'
- id: 73dbf344af2a
  severity: writing
  text: 'Figure 3: The timeline at the top uses colored dots (2023-2026) but lacks
    a legend defining what the colors represent or how they map to the specific years
    listed below.'
- id: 8d25e4837200
  severity: science
  text: 'Figure 8: The timeline includes publication years 2025 and 2026 (e.g., ''CodePRM
    (2025)'', ''ExecVerify (2026)'') for works that have not yet been published, which
    is factually impossible for a scientific roadmap of existing literature.'
- id: f0759ac6a050
  severity: writing
  text: 'Figure 8: The logos for various institutions and companies (e.g., Google,
    NVIDIA, TUM) are used to identify the authors of the works but are not defined
    in a legend or caption, requiring external knowledge to interpret.'
- id: a16cfc224032
  severity: writing
  text: "Figure 10: The top-right text '(\u25B7\xA7Sec. 3.5)' is a raw LaTeX cross-reference\
    \ command that was not rendered into a clean section link or title, indicating\
    \ a compilation or formatting oversight."
- id: 62c32bd03657
  severity: writing
  text: 'Figure 12: The caption lists ''adaptive coordination'' as the fourth category,
    but the figure''s y-axis label reads ''Adaptive Orchestration''; align the text
    to match the visual label.'
- id: 7429e04af479
  severity: writing
  text: 'Figure 12: Several logos (e.g., ''sea | AI lab'', ''aws'') are used as markers
    without a legend or explicit definition in the caption explaining their role as
    institutional affiliations.'
artifact_hash: cbd4e8e17c331b3d11d6d3473a72ca30389ded91296199ea84247ea30361db9d
artifact_path: projects/PROJ-606-https-arxiv-org-abs-2605-18747/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T15:42:04.103272Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 is a clear and well-structured taxonomy diagram that effectively visualizes the hierarchy of the 'Code as Agent Harness' concept. The layout logically flows from the high-level loop to specific mechanisms, interfaces, and applications, with all text legible and icons distinct.

### Figure 2

Figure 2 is a clear and well-organized infographic that effectively visualizes the five emerging domains of code as an agent harness. The layout is uncluttered, the icons are distinct, and the text labels are legible, fully supporting the caption's description.

### Figure 3

Figure 3 provides a clear visual roadmap of agent harness mechanisms across five categories, but it suffers from significant ambiguity due to repeated entries (e.g., MapCoder, AgentCoder, OpenHands, SWE-Agent) appearing in multiple rows without visual distinction or explanation.

### Figure 4

Figure 4 is a clear and well-structured diagram that effectively visualizes the taxonomy of planning mechanisms for agent harnesses. The four categories are distinct, the icons are intuitive, and the layout aligns perfectly with the provided caption.

### Figure 5

Figure 5 is a clear and well-organized schematic that effectively illustrates the taxonomy of memory and context engineering mechanisms. The visual distinction between different memory types (Working, Semantic, Experiential, etc.) is intuitive, and the diagram aligns perfectly with its caption.

### Figure 6

Figure 6 is a clear, well-organized schematic that effectively illustrates four distinct categories of tool use for agent harnesses. The visual icons and accompanying text labels are legible and directly support the caption's description of the taxonomy.

### Figure 7

Figure 7 is a clear, well-organized schematic that effectively visualizes the taxonomy of code as an agent harness. The three distinct columns (Reasoning, Acting, Environment Modeling) are clearly labeled with icons and text, and the bottom row provides concrete examples of the underlying artifacts (Executor, Robot, Repo, etc.). The visual hierarchy and color coding support the caption's description of connecting agents to these three core functions.

### Figure 8

The figure provides a clear visual taxonomy of works by role, but it contains a significant scientific error by listing future publication years (2025-2026) as if they are established works. Additionally, the reliance on unlabelled logos for authorship identification reduces accessibility.

### Figure 9

Figure 9 is a clear, well-structured diagram illustrating the 'Harness Control through the Plan, Execute, and Verify Loop' via four distinct components. The visual icons, flow arrows, and descriptive text labels effectively communicate the concepts of Static Analysis, Sandboxed Execution, Deterministic Verification, and Permissioned State Transition without ambiguity.

### Figure 10

The figure provides a clear, high-level schematic of the adaptive harness optimization process with distinct steps and icons. However, it contains a minor formatting error where a raw LaTeX section reference command is visible in the title area.

### Figure 11

Figure 11 is a clear and well-structured conceptual diagram that effectively visualizes the taxonomy of multi-agent orchestration. The layout logically contrasts single-agent limitations with multi-agent solutions, and all components are clearly labeled and consistent with the provided caption.

### Figure 12

The figure provides a clear visual roadmap of multi-agent orchestration works, but the caption contains a terminology mismatch ('coordination' vs 'Orchestration') and lacks a legend defining the institutional logos used as markers.
