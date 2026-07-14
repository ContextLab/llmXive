---
action_items:
- id: bdcf3bb085b9
  severity: writing
  text: 'Figure 1: The caption contains a typo ''Methdology'' and omits the model
    name (e.g., ''Our model'') in the first sentence, making the text grammatically
    incomplete.'
- id: dc6f79994803
  severity: writing
  text: 'Figure 1: The caption text ''shows strong performance'' lacks a subject,
    failing to explicitly link the ''Emerging Behaviors'' section to the model.'
- id: 39378415b16a
  severity: writing
  text: 'Figure 2: The caption text is truncated mid-sentence at the end (''...outperforms
    the largest available variants alter [results_combined.png]''), leaving the description
    of the Data Efficiency plot incomplete.'
- id: e7a60c485173
  severity: science
  text: 'Figure 2: The right panel''s y-axis contains a visual break (indicated by
    jagged lines) between 0.16 and 0.26, but the data points in that range (e.g.,
    ''Ours (WAN 1.3B, 0.9M frames)'' at ~0.125) are plotted below the break, creating
    a misleading visual gap and distorting the perceived performance difference between
    the top and bottom clusters.'
- id: 79af45f83251
  severity: writing
  text: 'Figure 2: The left radar chart lacks a clear legend defining the specific
    colors/shapes for the competitor models (e.g., D4RT, Sapiens-2B, DepthAnythingV3),
    relying solely on direct labels which can be cluttered and hard to distinguish.'
- id: 89fdd27d1882
  severity: fatal
  text: 'Figure 3: The caption is explicitly ''(no caption)'', providing no context
    for the visual content. Without a description, it is impossible to determine what
    the different columns (e.g., depth maps, segmentation masks, skeleton overlays)
    represent or what the figure is intended to demonstrate.'
- id: a663a57f7a2f
  severity: science
  text: 'Figure 3: The figure lacks any axis labels, units, or legends to explain
    the color mappings in the intermediate columns (e.g., depth, surface normals)
    or the specific tasks being visualized in the rightmost columns.'
- id: 199d0de2602a
  severity: writing
  text: 'Figure 4: The caption contains a grammatical error and missing subject: ''Architecture
    overview of , a simple yet powerful architecture...'' (missing model name).'
- id: 5bba7ecb355c
  severity: writing
  text: 'Figure 4: The caption contains a sentence fragment: ''During multi-task post-training,
    the model is adapted to feed-forward model fine-tuned on predominantly synthetic
    data to handle diverse perception tasks.'' This appears to be a copy-paste error
    from Figure 1''s caption.'
- id: b6cf4a879a2c
  severity: science
  text: 'Figure 4: The diagram shows ''Learnable Tokens'' entering the Pretrained
    DiT, but the caption states sparse tasks are realized by adding them as ''additional
    inputs to the diffusion transformer (DiT)''. The visual flow is clear, but the
    caption phrasing is slightly ambiguous regarding whether they are added to the
    input or the transformer layers.'
- id: e8bca8f820b4
  severity: science
  text: 'Figure 5: The caption claims the ''Rothko'' Raymap assembles rotation and
    translation components into a single three-channel map, but the image shows a
    green rectangle (translation) embedded in a gradient (rotation) without any indication
    of how these are combined into RGB channels or what the color mapping represents.'
- id: 72851e861377
  severity: writing
  text: 'Figure 5: No colorbar, legend, or axis labels are present to explain the
    meaning of the colors or spatial dimensions in either the ''Rotation Raymap''
    or ''Rothko Raymap'' visualizations.'
- id: a82d26c74360
  severity: writing
  text: Figure 6 caption contains a grammatical error ('Demonstration of 's depth...')
    where the model name is missing before the possessive.
- id: f14cebc5a560
  severity: science
  text: 'Figure 6: The rightmost column displays surface normals, but the image is
    rendered with a distinct color map (purple/green) compared to the middle column
    (orange/blue). Without a legend or explicit label, it is difficult to verify if
    the color mapping corresponds to the correct normal vector components.'
- id: 6c4fc4d7205b
  severity: writing
  text: 'Figure 7: The caption claims the model recognizes ''spatial relationships''
    and ''motion'', but the figure only displays static input frames and predicted
    masks without visualizing the temporal or spatial reasoning process (e.g., no
    arrows, trajectory lines, or multi-frame sequences).'
- id: 31069076e702
  severity: writing
  text: 'Figure 7: The ''Emerging Behavior'' section includes a prompt stating ''rocket''
    is not in training data, but the figure lacks a visual comparison or baseline
    to substantiate the claim of generalization to unseen objects.'
- id: 00c33ce2f558
  severity: writing
  text: 'Figure 8: The legend uses inconsistent singular/plural phrasing (''0 pretrained
    layer'' vs ''8 pretrained layer''); standardize to ''layers'' for all entries.'
- id: eb5eb8d5515f
  severity: writing
  text: 'Figure 8: The legend entry ''40 pretrained layer (fully pretrained model)''
    contains a typo (''fully pretrained'' should be ''fully pretrained'').'
- id: 4454dfe597f4
  severity: writing
  text: 'Figure 9: The caption ''(a) Generalize to multiple instances'' implies a
    multi-panel figure, but only a single image grid is shown; remove the ''(a)''
    or add the missing panel.'
- id: f981759a9999
  severity: writing
  text: 'Figure 9: The caption is grammatically incomplete and lacks a subject (e.g.,
    ''Our model generalizes...''); it currently reads as a fragment.'
artifact_hash: bd9b8338c9ef684f69ecde6cb02952f1373be2d283e651b95c30cd6af9990c46
artifact_path: projects/PROJ-1047-video-generation-models-are-general-purp/paper/metadata.json
backend: dartmouth
feedback: Vision review of 9 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-14T04:10:53.862982Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 effectively visualizes the methodology and paradigm shift, but the caption contains a spelling error ('Methdology') and grammatical omissions that leave sentences without clear subjects.

### Figure 2

Figure 2 presents a radar chart and a scatter plot to demonstrate generalist capability and data efficiency. However, the caption is truncated, and the right panel's y-axis break is visually confusing, potentially misrepresenting the performance gap between models. The radar chart also lacks a formal legend for the various competitor models.

### Figure 3

Figure 3 is a teaser-style visualization that is rendered clearly but is scientifically unusable due to a complete lack of a descriptive caption and internal labels. The viewer cannot identify the specific tasks or data modalities shown without guessing.

### Figure 4

The figure provides a clear visual overview of the architecture, but the caption contains significant grammatical errors and appears to include a sentence fragment from another figure's description.

### Figure 5

Figure 5 visually depicts a transformation from separate rotation and translation maps to a combined 'Rothko' map, but lacks any quantitative or qualitative legend to explain the color encoding or channel composition described in the caption.

### Figure 6

The figure effectively demonstrates depth and normal estimation capabilities with clear visual separation between RGB, depth, and normal outputs. However, the caption contains a missing model name, and the surface normal visualization lacks a legend to define the color mapping.

### Figure 7

The figure provides clear qualitative examples of segmentation masks for various prompts, but the static presentation fails to visually demonstrate the 'spatial relationships' and 'motion' reasoning claimed in the caption.

### Figure 8

The figure effectively demonstrates the impact of layer transfer on training loss, but the legend contains inconsistent grammar ('layer' vs 'layers') and a minor typo in the final entry.

### Figure 9

The figure visually demonstrates the model's ability to handle multiple people, but the caption is grammatically fragmented and includes a panel label '(a)' that does not correspond to the single image grid shown.
