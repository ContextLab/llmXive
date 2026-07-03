---
action_items:
- id: 6d8344eed939
  severity: writing
  text: 'Figure 1: The x-axis labels for the ''AgentDoG'' model variants are colored
    orange, while the bars are also orange, creating a visual redundancy that makes
    the text harder to distinguish from the bars compared to the grey bars.'
- id: f50ebf404f62
  severity: writing
  text: 'Figure 1: The x-axis labels are rotated at a steep angle, which is necessary
    for fit but makes the model names (e.g., ''Qwen3-235B'') difficult to read quickly.'
- id: 0f25ef54d2fe
  severity: writing
  text: 'Figure 3: The caption repeatedly refers to ''Building Pipeline of .'' and
    ''...of .'' with a missing model name, likely due to a placeholder variable not
    being replaced in the final text.'
- id: 9a3451cd4543
  severity: writing
  text: 'Figure 3: The ''Risk Sampling'' box lists ''15 Risk Sources'', ''21 Failure
    Modes'', and ''11 Real-world Harms'', but the figure does not visually depict
    these specific counts or categories, making the text feel disconnected from the
    visual flow.'
- id: f346575f6ced
  severity: science
  text: 'Figure 4: The caption claims the left panel isolates ''embedded deceptive
    instructions,'' but the visual highlights the ''Environment'' block (containing
    resume data) and the ''Key Impact Step'' (containing the instruction), failing
    to visually distinguish the ''benign data'' from the ''deceptive instruction''
    as promised.'
- id: dcb6fbcdb48f
  severity: writing
  text: 'Figure 4: The caption states ''Highlighted regions indicate the top-ranked
    components,'' yet the figure uses red text highlighting without a legend or key
    to define what the red color signifies (e.g., attribution score, confidence, or
    specific token importance).'
- id: 7c88800b3a72
  severity: science
  text: 'Figure 5: The caption claims the figure shows ''Comparative attribution analysis''
    and highlights ''high-impact drivers'' (Steps 2, 3, 4, 5), but the rendered image
    displays a chronological ''Trajectory'' of actions and thoughts with ''Traj Scores''
    rather than an attribution heatmap or importance map. The visual content does
    not match the caption''s description of an attribution analysis.'
- id: e86bf1bcc31f
  severity: writing
  text: 'Figure 5: The figure title ''Attribution Comparison: AgentDoG vs. Base Model''
    is generic and does not specify the scenario (WeChat red packet) or the specific
    models (Qwen3-4B) mentioned in the caption, making the figure standalone context
    poor.'
- id: 3744b499b6d3
  severity: writing
  text: 'Figure 6: The caption contains a grammatical error and missing subject: ''filtered
    agentic safety SFT data by .'' and ''selected by ,'' (likely missing ''AgentDoG'').'
- id: 97152b85b2fc
  severity: science
  text: 'Figure 6: The donut charts lack numerical labels or percentages on the segments,
    making it impossible to verify the distribution claims or compare segment sizes
    accurately.'
- id: 4445d3bd314b
  severity: writing
  text: 'Figure 7: The caption ''The dual-scenario environment synthesis pipeline
    for agentic safety RL'' is grammatically incomplete and lacks the specific subject
    name (e.g., ''AgentDoG'') that is present in other captions (e.g., Figure 3, Figure
    6).'
- id: 03db9a627b89
  severity: science
  text: 'Figure 7: The ''malicious query attack'' path depicts a ''Malicious User
    Request'' combined with a ''Benign Environment Context'' to create a ''Safety
    Task Bundle''. This contradicts standard safety evaluation logic where a malicious
    request is typically paired with a vulnerable or corrupted context to test for
    failure, whereas the ''Benign User Request'' path pairs with a ''Corrupted Environment
    Context'' to create a ''Clean Task Bundle'', which seems counter-intuitive for
    a safety synthesis pipeline.'
- id: 78223d21487f
  severity: science
  text: 'Figure 8: The caption claims memory footprint remains ''highly stable'' and
    consumes ''less than 2.5 GB'', but the ''Peak RSS'' data (orange dashed lines)
    in all three subplots shows a clear, monotonic increase with workload, contradicting
    the claim of stability.'
- id: 1dae69a32d93
  severity: writing
  text: 'Figure 8: The y-axis label ''Per-Env Time (ms)'' is rotated 90 degrees and
    difficult to read; it should be horizontal or the font size increased for clarity.'
- id: e112b5967ab6
  severity: writing
  text: 'Figure 9: The caption ''Our online agent safety guardrail pipeline'' is too
    generic and fails to describe the specific components shown (e.g., AgentDoG Guardrail,
    Trajectory Formatter, Agent Runtime) or the data flow between the ''Autonomous
    Agent Execution'' and ''Online Guardrail'' sections.'
- id: 5e564fbda8f6
  severity: writing
  text: 'Figure 9: The text ''Judges full trajectory'' inside the AgentDoG Guardrail
    box is grammatically awkward and likely a typo for ''Judges the full trajectory''
    or ''Judges full trajectory context''.'
- id: 59c074c3da0e
  severity: writing
  text: 'Figure 10: The caption describes the figure as ''A lightweight and scalable
    alignment framework'' but fails to name the framework (AgentDoG) or explain the
    specific components shown (Application 1 vs. Application 2), making the diagram
    difficult to interpret without reading the main text.'
- id: f6f78c101c8d
  severity: writing
  text: 'Figure 10: The central logo contains the text ''AgentDoG'', but this name
    is not explicitly defined in the caption, which refers to the system only as ''A
    lightweight and scalable alignment framework''.'
artifact_hash: 0da3b72044460a5165e111e630e8cbd536a6b5b6d368e4237e9f5b706de0008d
artifact_path: projects/PROJ-646-agentdog-1-5-a-lightweight-and-scalable/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T04:13:22.431461Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure effectively communicates the performance of AgentDoG 1.5 against baselines with clear numerical labels on bars. However, the orange text color for the x-axis labels matches the bar color, slightly reducing readability, and the steep rotation of the labels is a minor aesthetic issue.

### Figure 2

Figure 2 clearly illustrates the trajectory-level safety evaluation process by contrasting the task definitions and outputs for safe versus unsafe agent behaviors. The visual layout effectively distinguishes between the input trajectory and the resulting classification, supporting the caption's description.

### Figure 3

The figure provides a clear visual overview of the data engine and training pipeline. However, the caption contains significant grammatical errors where the model name is missing (e.g., 'Pipeline of .'), and the specific statistics listed in the 'Risk Sampling' box are not visually represented in the diagram.

### Figure 4

The figure illustrates two scenarios but fails to visually distinguish between 'benign data' and 'deceptive instructions' in the left panel as claimed in the caption. Additionally, the red highlighting lacks a legend to explain its specific meaning regarding attribution ranking.

### Figure 5

The figure displays a trajectory comparison with scores but fails to visually represent the 'attribution analysis' described in the caption, creating a disconnect between the text and the visual data. Additionally, the figure title lacks the specific context found in the caption.

### Figure 6

The figure presents a clear visual taxonomy of the dataset, but the caption contains grammatical errors with missing text, and the charts lack specific data labels to support the distribution analysis.

### Figure 7

The figure provides a clear visual workflow for the dual-scenario synthesis pipeline, but the caption is grammatically incomplete. Additionally, the logic of the 'malicious query attack' path appears counter-intuitive by pairing a malicious request with a benign context to generate a safety task.

### Figure 8

The figure effectively visualizes scalability metrics, but the caption's claim that memory footprint remains 'highly stable' is contradicted by the visible upward trend in the Peak RSS data across all subplots.

### Figure 9

The figure provides a clear visual schematic of the system architecture, but the caption is insufficiently descriptive, failing to explain the specific modules or the interaction flow depicted in the diagram.

### Figure 10

The figure provides a clear visual overview of the two application modes (Training-Based and Training-Free), but the caption is too generic, failing to identify the framework by name or explain the specific workflow steps depicted in the diagram.

### Figure 11

Figure 11 is a clear and well-structured taxonomy diagram that effectively visualizes the three-dimensional agentic safety framework. The legend is comprehensive, explicitly defining the color and border styles used to distinguish between OpenClaw and Codex customizations and strengthened items, which aligns perfectly with the caption's description.

### Figure 12

Figure 12 is a clear and well-structured diagram that effectively illustrates the ATBench family hierarchy. The visual layout logically connects the shared taxonomy and diagnosis task to the specific customizations of ATBench, ATBench-Claw, and ATBench-Codex, fully supporting the claims in the caption.
