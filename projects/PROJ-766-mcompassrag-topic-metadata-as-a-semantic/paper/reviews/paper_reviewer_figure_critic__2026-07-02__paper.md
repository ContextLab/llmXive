---
action_items:
- id: f0ae371b3e06
  severity: writing
  text: 'Figure 1: The caption is explicitly marked as ''(no caption)'', leaving the
    diagram''s components and flow unexplained.'
- id: 9e1f92e9d8a8
  severity: writing
  text: 'Figure 1: The diagram contains a placeholder text ''Overview of .'' where
    the model name or system description should be.'
- id: 633062e74c11
  severity: writing
  text: 'Figure 2: The caption contains multiple grammatical gaps where the model
    name ''MCompassRAG'' is missing (e.g., ''Overview of .'', ''At inference time,
    selects...''). Additionally, the caption states that icons indicate trainability
    (fire for trained, snowflake for frozen), but the rendered figure lacks a legend
    or key to define these symbols.'
- id: f3d85fc5fe62
  severity: writing
  text: 'Figure 3: The x-axis label ''Topics'' is ambiguous; the caption specifies
    ''number of topics'', but the axis ticks (2, 4, ..., 20) are not explicitly labeled
    as counts, which could be confused with topic IDs.'
- id: 229c0d9c3ac8
  severity: writing
  text: 'Figure 3: The y-axis label ''IE'' is undefined in the figure and caption;
    the metric (e.g., Inverse Entropy, Information Efficiency) should be spelled out
    for clarity.'
- id: e972b59ee385
  severity: writing
  text: 'Figure 5 caption: The sentence ends abruptly with ''query--gold alig'', indicating
    a truncation error.'
- id: 20099f21d97d
  severity: writing
  text: 'Figure 5 caption: ''shareholde structure'' contains a typo (missing ''r'').'
artifact_hash: 5e7163c1713464843d620f2c37705ca96ededa7c235cfa3e5a0986f0a19b0aa7
artifact_path: projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/paper/metadata.json
backend: dartmouth
feedback: Vision review of 5 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T23:54:28.363840Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

### Figure 1

Figure 1 is a schematic overview of the pipeline, but it lacks a functional caption and contains a placeholder text error in the title area.

### Figure 2

The figure provides a clear visual pipeline of the system architecture, but the caption is grammatically incomplete and fails to explicitly define the trainability icons (fire and snowflake) shown in the diagram.

### Figure 3

The figure clearly presents the ablation study results with consistent formatting across panels, but the y-axis metric 'IE' is undefined and the x-axis label 'Topics' is slightly ambiguous regarding whether it represents a count or ID.

### Figure 4

Figure 4 effectively illustrates the qualitative retrieval comparison between dense retrieval and MCompassRAG. The layout is clear, with distinct sections for retrieval candidates, dense retrieval scores, and the proposed method's topic signals and MLP scores, all of which align perfectly with the detailed caption.

### Figure 5

The figure effectively visualizes the separation of the gold chunk from distractors in the topic-enriched space, but the caption contains a significant truncation error and a typo.
