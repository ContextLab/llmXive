---
action_items:
- id: 9b8cbc227a96
  severity: science
  text: 'Figure 1b: The caption claims ''Benchmarks with higher shortcut ratios tend
    to report higher accuracy,'' but the chart shows a negative correlation where
    accuracy (blue bars) generally decreases as the shortcut ratio (red line) decreases.
    The trend contradicts the caption''s claim.'
- id: 78f98be70f55
  severity: writing
  text: 'Figure 1b: The x-axis labels for the benchmarks are rotated at a steep angle,
    making them difficult to read and cluttered.'
- id: cbdf6d99ca84
  severity: science
  text: 'Figure 3: The caption claims panel (b) shows ''Questions incorrectly filtered
    by the frame shuffling test,'' but the visual examples (baseball, basketball)
    explicitly highlight ''Temporal Context'' and sequential events (''after the second
    ball''), which are the exact type of temporal dependencies the frame shuffling
    test is designed to detect. This contradicts the caption''s assertion that these
    were ''incorrectly filtered'' and should have been removed.'
- id: 6eccadc58bcf
  severity: writing
  text: 'Figure 3: Panel (a) bottom example uses the label ''Ambiguous Subject'' to
    describe a scene with multiple bounding boxes, but the visual evidence (red vs.
    green boxes) suggests the issue is ''Object Tracking'' or ''Identity Consistency''
    rather than subject ambiguity, as the question asks for a relation between two
    specific entities.'
- id: 9e6fa1c2d411
  severity: writing
  text: 'Figure 5: The caption states this figure shows ''Fine-Grained Perception
    Challenges,'' but the internal text labels explicitly categorize the examples
    as ''Living Room Recognition'' and ''Background Tracking'' (Spatial Temporal Grounding),
    creating a mismatch between the figure''s title and its content.'
- id: f6a578fe562c
  severity: writing
  text: 'Figure 5: The text ''Why Video Native Challenges?'' is repeated as a header
    for both examples, which is redundant and disrupts the visual flow of the qualitative
    examples.'
artifact_hash: f0c16b304e278e372ae68ce72c73490fb948c6f63a71aa660ad21d1de4b7a1fb
artifact_path: projects/PROJ-1038-video-oasis-rethinking-evaluation-of-vid/paper/metadata.json
backend: dartmouth
feedback: Vision review of 9 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-11T04:08:58.254138Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 effectively illustrates the existence of shortcuts in panel (a) and the performance gap in panel (c), but panel (b) presents a confusing negative correlation that contradicts the caption's claim of a positive relationship between shortcut ratios and accuracy.

### Figure 2

Figure 2 is a clear and well-structured schematic that effectively communicates the three components of the Video-Oasis diagnostic suite. The visual flow from input to specific tests and final agreement metrics is logical, and the caption accurately describes the figure's content.

### Figure 3

The figure presents qualitative examples of video QA failures, but the caption for panel (b) contradicts the visual evidence by claiming temporal questions were 'incorrectly filtered' when they clearly demonstrate the temporal reasoning the filter is meant to catch.

### Figure 4

Figure 4 effectively visualizes the distinction between previous benchmarks containing shortcuts and the video-native challenges distilled by Video-Oasis. The layout is clear, the legend defining the checkmarks and crosses is present, and the qualitative examples align perfectly with the caption's description of the five challenge categories.

### Figure 5

The figure provides clear visual examples of video QA tasks with bounding boxes and text, but the internal labels ('Living Room Recognition', 'Background Tracking') contradict the caption's classification of 'Fine-Grained Perception Challenges,' and the layout contains redundant headers.

### Figure 6

Figure 6 provides clear qualitative examples of spatial world understanding challenges, featuring distinct video frames, specific navigation questions with fill-in-the-blank prompts, and a breakdown of the required reasoning steps. The layout is uncluttered, and the text is legible, effectively supporting the caption's description.

### Figure 7

Figure 7 provides clear qualitative examples of temporal dynamics and tracking challenges using video frames with bounding boxes and descriptive text. The visual layout effectively illustrates the specific tasks (Fish Tracking, Location Linking, Order Reconstruction, etc.) without requiring additional legends or controls.

### Figure 8

Figure 8 provides clear qualitative examples of causality and logical reasoning challenges, effectively illustrating the 'Video Native Challenges' workflow described in the caption. The visual layout, including the video frames, bounding boxes, and the step-by-step reasoning breakdown, is legible and well-structured.

### Figure 9

Figure 9 provides clear qualitative examples of Global Narrative Challenges, using video frames with bounding boxes to highlight specific events and text to explain the temporal reasoning required. The layout is uncluttered, and the connection between the visual evidence and the narrative question is explicit.
