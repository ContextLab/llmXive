---
action_items:
- id: 79e14041aba7
  severity: science
  text: 'Figure 1: The y-axis label ''Length of Coding Tasks AI Agents Can Complete''
    and the caption''s definition of ''50%-time horizon'' as ''median task completion
    length'' are contradictory. A ''time horizon'' typically refers to the duration
    an agent can operate or plan ahead (e.g., 12 hours of continuous execution), whereas
    ''task completion length'' implies the time taken to finish a single task. The
    caption claims the metric is ''median task completion length,'' but the data points
    (e.g., 718.8 min) and the '
- id: f293c258e9de
  severity: writing
  text: 'Figure 1: The y-axis scale is non-linear and misleading. The distance between
    0 secs and 3.3 hours is visually similar to the distance between 3.3 hours and
    10 hours, despite the latter being a much larger absolute interval. This distorts
    the perceived rate of growth, making the exponential curve appear less steep than
    it would on a linear or properly logarithmic scale. The axis labels (0 secs, 3.3
    hours, 6.7 hours, 10 hours) are also inconsistently spaced, further confusing
    the reader about the'
- id: b529843dbb51
  severity: writing
  text: 'Figure 1: The ''Key Takeaway'' box at the bottom states ''over 12 hours for
    the leading models in early 2026,'' but the highest data point shown (Opus 4.6)
    is 718.8 minutes (~12 hours) and is positioned at the very end of the x-axis (2026),
    not ''early 2026.'' Additionally, the y-axis only goes up to 10 hours, yet the
    data point for Opus 4.6 (718.8 min) is plotted above the 10-hour line, creating
    a visual inconsistency between the axis limit and the data presented.'
- id: a986ccff322b
  severity: writing
  text: 'Figure 4: The caption describes a generic ''Agent Era'' loop, but the rendered
    image is a detailed, cartoon-style infographic labeled ''AI Agent Era'' with specific
    numbered sections (1 Inputs, 2 Agent Controller, 3 Environment & Tools) and human
    characters that are not described in the caption.'
- id: 75fe660c71c8
  severity: writing
  text: 'Figure 4: The code snippet in the ''Environment & Tools'' panel is illegible
    due to low resolution, making the specific Python implementation details unreadable.'
- id: 864beb1c4243
  severity: science
  text: 'Figure 6: The figure depicts the ''Workspace Substrate'' (blue box) and ''Work-Oriented
    Task Delivery'' as part of the solution, but the caption describes Figure 6 as
    highlighting ''Simple tool invocation'' and its limitations. The visual content
    actually illustrates the ''Workspace + Skill paradigm'' (matching Figure 7''s
    description) rather than just the limitations of simple tool calls.'
- id: a66c495910ee
  severity: science
  text: 'Figure 6: The figure is a composite diagram showing both the ''Ephemeral
    Tool Calls'' (red box) and the ''Workspace Substrate'' (blue box). However, the
    caption only describes the limitations of tool invocation (the red box part) and
    does not mention the persistent workspace solution (the blue box part) which occupies
    50% of the visual space.'
- id: 63be6eac29cf
  severity: writing
  text: 'Figure 6: The caption states ''The figure highlights why a workspace is needed'',
    but the figure itself is titled ''Ephemeral Tool Calls'' (top) and ''Workspace
    Substrate'' (bottom). The figure lacks a unifying title that reflects the comparison
    being made, making the relationship between the two halves less clear from the
    visual alone.'
- id: 1a373db5d19c
  severity: science
  text: 'Figure 7: The visual content depicts a three-stage workflow (Ad-hoc Prompts
    -> Skill Packaging -> Composable Digital Worker) rather than the ''Workspace +
    Skill paradigm'' described in the caption. The figure illustrates the process
    of creating a skill but fails to show the ''persistent workspace'' or the ''combination
    of workspace context with skill assets'' that the caption claims to demonstrate.'
- id: 6e6ae0cbbccd
  severity: writing
  text: 'Figure 7: The caption describes a ''Workspace + Skill paradigm'' but the
    figure is titled ''Ad-hoc Prompts'', ''Skill Packaging'', and ''Composable Digital
    Worker'', creating a disconnect between the figure''s internal narrative and the
    caption''s summary.'
- id: 75d225ee3bf6
  severity: writing
  text: 'Figure 8: The bottom banner contains a typo (''Batter alignment'' instead
    of ''Better alignment'').'
- id: 36f2568cdd96
  severity: writing
  text: 'Figure 8: The caption claims the figure shows ''why'' systems require specific
    data types, but the figure only illustrates ''what'' the data types are (descriptive
    rather than explanatory).'
- id: fe934175f19f
  severity: science
  text: 'Figure 10: The caption claims to summarize bottlenecks around ''task closure''
    and ''context management,'' but the figure only depicts ''Long-Horizon & Rollback,''
    ''Safety & Governance,'' and ''Persistent Memory,'' omitting the other two claimed
    categories.'
- id: 959a0f93199f
  severity: writing
  text: 'Figure 10: The legend in Panel I uses a dashed line for ''Planned Path''
    and a solid line for ''Actual Trajectory,'' but the visual representation of the
    ''Actual Trajectory'' (the black line) is thick and stylized, making it difficult
    to distinguish from the ''Safe Checkpoint'' icons along the path.'
- id: ac0b61088e0a
  severity: science
  text: 'Figure 11: The figure is a cartoon infographic rather than a scientific diagram;
    it lacks the specific technical components (models, contexts, tools, skills, workspaces,
    memories, evaluators, governance mechanisms) mentioned in the caption, instead
    showing generic ''Trace Capture'' and ''Synthesizer'' boxes.'
- id: e169cbd753af
  severity: writing
  text: 'Figure 11: The caption claims the figure illustrates a path from ''reactive
    chatbots'' to ''digital colleagues,'' but the figure starts at ''Stage I: Trace
    Capture'' without showing the preceding chatbot or agent eras described in the
    paper''s narrative.'
- id: c329afa5a8a3
  severity: writing
  text: 'Figure 12: The caption contains raw LaTeX formatting code (e.g., ''0.7mmbluemybluemyblue0.7mm0.7mm'')
    instead of readable text describing the color legend for open-source vs. closed
    systems.'
- id: 6cd5d89fdacc
  severity: science
  text: 'Figure 12: The timeline includes future dates (e.g., ''Apr 2026'', ''Mar
    2026'') for unreleased models, which contradicts the caption''s claim that nodes
    are labeled by ''release month''.'
artifact_hash: 5b20d0674a4eae3ce29e5aed0e38438a3ae13f2792cd32291d876c2888c926ec
artifact_path: projects/PROJ-705-from-chatbot-to-digital-colleague-the-pa/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T22:59:54.663498Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 presents a clear visual trend of increasing AI agent capabilities over time, but it suffers from significant conceptual and scaling issues. The caption's definition of '50%-time horizon' as 'median task completion length' contradicts the likely intended meaning of 'maximum task duration an agent can sustain,' leading to confusion. The y-axis uses a non-linear, inconsistently spaced scale that distorts the growth rate, and the 'Key Takeaway' claims data beyond the plotted axis limits without clear justification.

### Figure 2

Figure 2 effectively visualizes the 'Chatbot Era' workflow described in the caption, clearly depicting the linear, stateless, single-pass nature of the process from input to output. The diagram is well-labeled, legible, and accurately supports the claim of fast inference without external loops or persistent memory.

### Figure 3

The figure is a clear, well-structured infographic that effectively visualizes the 'Thinking LLM' workflow described in the caption. It successfully illustrates the core concepts of exploring multiple reasoning paths, detecting errors, backtracking, and self-correcting to reach a final answer.

### Figure 4

The figure is a clear, illustrative infographic of an agent loop, but the caption fails to describe the specific visual elements (numbered sections, human characters, and cartoon style) present in the rendered image.

### Figure 5

Figure 5 is a clear and well-structured infographic that effectively illustrates the OpenClaw workflow. The visual elements, including the numbered steps, icons, and UI mockups, align perfectly with the caption's description of a persistent workspace with skills and verification loops. The diagram is readable, logically organized, and successfully communicates the concept of inspectable and recoverable task closure.

### Figure 6

The figure effectively contrasts ephemeral tool calls with a persistent workspace, but the caption is misaligned with the visual content. The caption focuses only on the limitations of tool calls (top half) while ignoring the detailed depiction of the workspace solution (bottom half), which is the primary visual element. The figure appears to be a duplicate or mislabeled version of Figure 7.

### Figure 7

The figure illustrates a workflow for packaging skills but fails to visually represent the 'Workspace + Skill paradigm' described in the caption, specifically omitting the persistent workspace and the interaction between workspace context and skill assets.

### Figure 8

The figure effectively visualizes the three stages of data evolution (SFT, CoT/PRM, Trajectories) with clear examples, but the bottom banner contains a typo ('Batter' vs 'Better') and the caption overclaims the figure's explanatory scope.

### Figure 9

The figure effectively visualizes the evaluation paradigm shift described in the caption, clearly distinguishing between Stage I (Final Output), Stage II (Process), and Stage III (Task Closure) with appropriate icons and text. The visual flow and specific examples (e.g., 'Logical Error' checks, 'Diagnostic Sandbox') align well with the summary of assessing reasoning validity and environment state changes.

### Figure 10

The figure effectively visualizes three major challenges with clear icons and legends, but the caption overpromises by listing 'task closure' and 'context management' as summarized bottlenecks which are not explicitly represented in the three panels shown.

### Figure 11

The figure is a stylized cartoon that fails to visually represent the specific technical components listed in the caption, and it omits the 'reactive chatbot' starting point described in the text.

### Figure 12

The figure provides a clear visual roadmap of AI evolution, but the caption is marred by raw LaTeX formatting code that obscures the legend definition, and the timeline includes future-dated models that contradict the 'release month' description.
