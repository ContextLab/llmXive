---
action_items:
- id: 451d2015abfb
  severity: science
  text: 'Figure 1: The Sankey diagram lacks a legend defining the color coding (e.g.,
    purple, beige, yellow, green, grey) for the nodes and flows, making it impossible
    to distinguish between data sources, intermediate stages, and specific filter
    types.'
- id: 7c186bfaf830
  severity: science
  text: 'Figure 1: The diagram is missing quantitative units or values (e.g., number
    of samples, percentages) on the flows or nodes, rendering the ''pipeline'' visualization
    qualitative and unable to support claims about data volume reduction or filtering
    efficiency.'
- id: fae1ef6c113e
  severity: writing
  text: 'Figure 5: The caption contains a typo, spelling the dataset as ''WordelModelBench''
    instead of ''WorldModelBench''.'
- id: af7780ccd319
  severity: writing
  text: 'Figure 8: The caption ''Human evaluation results'' is too generic for a complex
    multi-panel figure; it should specify that the figure compares Kairos against
    four specific baselines (cosmos-predict2.5, lingbot-14B, wan2.2) across three
    datasets.'
- id: 0cdaabde363f
  severity: writing
  text: 'Figure 8: The y-axis labels ''Paibench robot-subset'', ''WorldModelBench
    robot-subset'', and ''Dreamgen'' are repeated in every subplot; consolidating
    these into a single shared axis or using a grid layout would reduce visual clutter.'
- id: df981330d65a
  severity: writing
  text: 'Figure 9: The caption states ''Kairos samples on the PAI-Bench dataset''
    but does not specify that the images show ''Input frame'' followed by ''Predicted
    frames'', making the temporal nature of the samples unclear.'
- id: 653cc5bde725
  severity: writing
  text: 'Figure 9: The column headers ''Input frame'' and ''Predicted frames'' are
    present but the number of predicted frames per input is not specified in the caption,
    leaving the reader to infer the temporal span.'
- id: ae1cf3baf7a3
  severity: writing
  text: 'Figure 10: The caption ''Kairos samples(TI2V)'' is ambiguous; it does not
    explicitly state that the left column represents the input frame and the subsequent
    columns represent the predicted frames, forcing the reader to infer the temporal
    progression.'
- id: 1b0f69dd5973
  severity: writing
  text: 'Figure 10: The image contains internal labels (''input frame'', ''Predicted
    frames'') that are not referenced or defined in the caption, creating a disconnect
    between the visual annotation and the textual description.'
- id: 5a48bad98158
  severity: science
  text: 'Figure 12: The ''Generated Frames'' columns show significant visual artifacts
    and temporal inconsistencies (e.g., flickering mixer, morphing coffee stream,
    unstable waterfall) compared to the ''Prompt'' column, which undermines the claim
    of generating high-quality physical AI samples.'
- id: 6168f15b0997
  severity: writing
  text: 'Figure 12: The caption is overly brief and does not explain the layout (e.g.,
    that the first column is the prompt and subsequent columns are generated frames)
    or the nature of the ''VideoPhy dataset'' samples shown.'
artifact_hash: 926e7dfe86ab0c8e4b8d20a90a842eec681ad7b82ae76075a7b3082533c6260d
artifact_path: projects/PROJ-740-kairos-a-native-world-model-stack-for-ph/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T18:04:39.693791Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 presents a Sankey diagram of the data filtering pipeline but fails to include a legend for color coding or any quantitative values on the flows, making the visualization ambiguous and lacking the necessary data to support pipeline claims.

### Figure 2

Figure 2 effectively displays representative examples from the dataset across four distinct categories (General, Human, Physics, Robot). The column headers clearly identify the domains, and the visual content is high-quality and legible, matching the caption's description.

### Figure 3

Figure 3 effectively illustrates the 'Divide-and-Conquer' captioning strategy by visually contrasting a basic VLM-generated caption (green box) with a more detailed, tag-enhanced version (blue box). The layout is clear, the text is legible, and the figure aligns perfectly with its caption's description of the comparison.

### Figure 4

Figure 4 effectively illustrates the paper's 'Enhanced Text with Chain of Thought' concept by visually contrasting physics-centric captions with long-term task captions. The layout is clear, the text is legible, and the content aligns perfectly with the provided caption description.

### Figure 5

The figure displays a grid of robot simulation frames consistent with the dataset name, but the caption contains a spelling error ('WordelModelBench').

### Figure 6

Figure 6 presents a grid of representative video frames from the DreamGen dataset, illustrating diverse robotic manipulation tasks. The visual content is clear, and the caption accurately describes the figure as samples from the specified dataset.

### Figure 7

Figure 7 presents a grid of video frames showing robot manipulation tasks, consistent with the caption's description of 'Kairos samples on the Paibench robot dataset.' The figure is clear, legible, and effectively communicates the visual content of the dataset without requiring additional legends or axes.

### Figure 8

The figure effectively communicates human evaluation results with clear data labels and a legend, but the caption is overly brief and the repetitive y-axis labels across subplots create unnecessary visual redundancy.

### Figure 9

Figure 9 displays input and predicted frames from the PAI-Bench dataset but lacks explicit description in the caption of the temporal structure (number of predicted frames) and the meaning of the column headers.

### Figure 10

The figure effectively displays video generation results with clear internal labels, but the caption fails to explicitly define the layout (input vs. predicted frames) or the meaning of the 'TI2V' acronym, relying on visual inference.

### Figure 11

Figure 11 effectively displays text-to-video generation samples from the WorldModelBench dataset. The layout clearly pairs descriptive prompts on the left with the corresponding generated video frames on the right, demonstrating the model's ability to render complex physical scenes and actions.

### Figure 12

The figure displays generated video frames but suffers from visible temporal artifacts and lacks a descriptive caption to contextualize the visual content or the dataset.
