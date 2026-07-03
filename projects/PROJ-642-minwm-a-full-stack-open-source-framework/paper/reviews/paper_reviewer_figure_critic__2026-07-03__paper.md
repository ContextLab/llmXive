---
action_items:
- id: 9408c559ae55
  severity: fatal
  text: 'Figure 1: The rendered image displays a fantasy landscape with video game
    UI overlays (WASD keys) rather than the scientific data (e.g., loss curves, sample
    comparisons) described in the caption regarding ''Training with very small batch
    sizes'' and ''Wan2.1-based model'' failure.'
- id: 9283efafdf8b
  severity: fatal
  text: 'Figure 2: The rendered image displays a fantasy landscape with game UI overlays
    (WASD keys) rather than scientific data, charts, or training curves. It fails
    to visually support the caption''s claim about ''Training with estimated camera
    poses'' or ''SpatialVid data''.'
- id: f96ea2a2bb0d
  severity: science
  text: 'Figure 2: The image contains no axes, units, legends, or error bars, making
    it impossible to evaluate the ''reliable camera-controllable generation'' or ''perception-estimated
    camera poses'' mentioned in the caption.'
- id: 4c26c7e1112f
  severity: writing
  text: 'Figure 3: The figure displays a grid of images with overlaid keyboard controls
    (WASD, arrows) but lacks a legend or explicit labels defining what specific camera
    action (e.g., pan, tilt, zoom) corresponds to each column or row.'
- id: ab110fb45b0f
  severity: writing
  text: 'Figure 3: The caption states the model supports generation under ''different
    camera actions'' but does not describe the specific actions shown in the grid,
    making it difficult to verify the claim without guessing based on the icons.'
- id: 29f7ae00c632
  severity: fatal
  text: 'Figure 5: The rendered image displays three identical screenshots of a desert
    landscape with game UI overlays (WASD/arrow keys), which does not visually support
    the caption''s claim about ''early-stage training'' or ''camera controllability''
    failure. There are no axes, data plots, or comparative metrics shown to substantiate
    the scientific claim.'
artifact_hash: 0ee056e55f4c06cb2eab61e5c44334fbdff8ec177adecd2d7f6251ef9b5e9f6a
artifact_path: projects/PROJ-642-minwm-a-full-stack-open-source-framework/paper/metadata.json
backend: dartmouth
feedback: Vision review of 5 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T15:45:58.027383Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure is a complete mismatch for its caption; it shows a fantasy scene with game controls instead of the required experimental results on batch size training effects.

### Figure 2

The figure is a fantasy landscape image with game controls that is completely unrelated to the scientific claims in the caption regarding camera pose training and data filtering. It lacks all necessary scientific visualization elements such as axes, data plots, or legends.

### Figure 3

The figure demonstrates visual results of camera control but fails to explicitly map the displayed keyboard inputs to specific camera movements in the caption or via a legend, leaving the viewer to infer the actions.

### Figure 4

Figure 4 is a clear and well-structured pipeline diagram that effectively visualizes the minWM framework. The flow from inputs through data, training, and inference stages is logical, and the output examples clearly demonstrate the system's capabilities. The caption accurately describes the figure's content.

### Figure 5

The figure is a mismatch for its caption; it shows game interface screenshots rather than the training data or metrics described. Consequently, the visual content fails to provide any evidence for the claim that the model has not acquired camera controllability.
