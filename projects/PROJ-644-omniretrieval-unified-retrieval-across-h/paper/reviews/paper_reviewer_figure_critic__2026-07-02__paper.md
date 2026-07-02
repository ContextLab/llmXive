---
action_items:
- id: 1976998beab5
  severity: fatal
  text: 'Figure 2: The figure has no caption (stated as ''(no caption)''), making
    it impossible to verify if the displayed data matches the authors'' intended claims
    or context.'
- id: ff70d25f5089
  severity: science
  text: 'Figure 2: The stacked bars do not sum to 100% (e.g., the ''GPT-5.4'' bar
    sums to ~98.9% and ''Gemma-4'' sums to ~99.5%), suggesting missing data categories
    or calculation errors.'
- id: 7fe04c1f938d
  severity: writing
  text: 'Figure 2: The legend is partially obscured by the figure title, making the
    ''2+ Cand., Gold Included'' entry difficult to read.'
- id: 239a43d2efcb
  severity: writing
  text: 'Figure 3: The figure lacks a descriptive caption; the current placeholder
    ''(no caption)'' fails to explain the experimental setup, the meaning of the ''Balanced
    Reference'' line, or the specific models being compared.'
- id: 74eaad060b6a
  severity: writing
  text: 'Figure 3: The legend is positioned outside the plot area and is not enclosed
    in a box, which can make it visually disconnected from the data in some rendering
    contexts.'
- id: 362312cab73c
  severity: writing
  text: 'Figure 4: The figure lacks a descriptive caption, providing no context for
    the ''Source Selection'', ''Retrieval'', and ''Judge'' subplots or the specific
    experiment being visualized.'
- id: 3b53634a3ce2
  severity: writing
  text: 'Figure 4: The legend is located only in the rightmost subplot (''Judge''),
    making it ambiguous for the ''Source Selection'' and ''Retrieval'' subplots which
    use the same symbols but lack a direct legend.'
- id: 0579edb079df
  severity: writing
  text: 'Figure 5: The caption is missing; the provided text ''(no caption)'' prevents
    verification of the specific experimental setup, dataset, or metric definitions
    required to interpret the ''Accuracy'' and ''Candidate Sources'' axes.'
- id: 6b0db0de6ca1
  severity: writing
  text: 'Figure 5: The y-axis label ''Accuracy (%)'' is ambiguous without a caption
    specifying the exact task (e.g., retrieval, generation, or classification) or
    the baseline against which the ''Oracle'' is compared.'
artifact_hash: 6b55048d0f0cf12263aa0420c5a331e1157aabe9768489e7c4eadd1c3653e932
artifact_path: projects/PROJ-644-omniretrieval-unified-retrieval-across-h/paper/metadata.json
backend: dartmouth
feedback: Vision review of 5 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T16:49:25.142380Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 is a clear and well-structured conceptual diagram that effectively illustrates the problem of heterogeneous retrieval sources (left) and the proposed OmniRetrieval solution (right). The visual elements, including icons, colors, and flow arrows, align perfectly with the provided caption, and the internal labels are legible and sufficient to understand the architecture without needing external definitions.

### Figure 2

The figure is a stacked bar chart comparing source selection outcomes, but it lacks a caption entirely, obscuring its scientific context. Additionally, the data bars do not sum to 100%, and the legend is partially covered by the title.

### Figure 3

The figure effectively visualizes the distribution of predictions across different query types and models, but it suffers from a complete lack of a descriptive caption, leaving the context and specific definitions of the reference line to the reader's inference.

### Figure 4

The figure presents clear scaling trends across three tasks, but it is missing a descriptive caption and the legend is not explicitly repeated or referenced for the first two subplots.

### Figure 5

The figure is visually clear with distinct series and annotations, but the complete absence of a descriptive caption makes it impossible to verify the experimental context or the specific meaning of the reported accuracy metrics.
