---
action_items:
- id: ffb90d1e410c
  severity: science
  text: 'Figure 1: The caption claims to compare ''PPO-IS, Vanilla-IS, and TIS'',
    but the ''Reward'' and ''Mismatch-K3'' plots include a ''Baseline'' series (grey)
    that is not mentioned in the caption text.'
- id: 7c8bd796d38b
  severity: science
  text: 'Figure 1: The ''Clip Ratio'' bar chart displays a value of 7.18e-03 for TIS,
    which is an order of magnitude higher than the other methods (~2e-04), yet the
    y-axis is not labeled with units or a title, making the scale interpretation ambiguous.'
- id: c94e73929681
  severity: science
  text: 'Figure 2: The caption claims to show sensitivity to $c$ and $T_{post}$, but
    the legend only defines $c=0$, $c=0.0001$, $c=-0.0001$, and ''Ours''. The ''Ours''
    method is undefined in the caption or legend, and the $T_{post}$ metric is not
    explicitly labeled on any axis (though the rightmost panel is likely it).'
- id: 5cda5e022d80
  severity: writing
  text: 'Figure 2: The rightmost panel''s y-axis label is missing; the caption identifies
    this metric as ''$T_{post}$'', but the plot itself lacks this label, relying solely
    on the caption for identification.'
- id: b692251c384b
  severity: science
  text: 'Figure 3: The ''Inference Gap'' panel shows the ''ours'' method (yellow)
    oscillating around 0.0000, while the caption claims the full method obtains a
    ''more controlled inference-policy trajectory.'' The visual data suggests the
    ''ours'' method is unstable or noisy rather than controlled compared to the baselines.'
- id: 279c99e01124
  severity: writing
  text: 'Figure 3: The legend uses two distinct shades of orange for ''+ step 1''
    and ''+ step 2'' which are visually very similar and difficult to distinguish
    from one another in the plots, especially in the ''Mismatch-K3'' panel.'
- id: 8eb6bab8a045
  severity: science
  text: 'Figure 4: The caption describes the plot as ''Inference-training K3-KL and
    inference gap'' but does not define the colors. The legend identifies the lines
    as ''Qwen3-4B FP8'' and ''Qwen3-1.7B FP8'', yet the caption fails to specify which
    model corresponds to the orange or red lines, making the data interpretation ambiguous.'
- id: efd3968e8d54
  severity: writing
  text: 'Figure 4: The x-axis label ''Training Step'' is present, but the caption
    does not specify the total number of steps or the context of the training run
    (e.g., which specific experiment or baseline from Figure 3 this data is drawn
    from).'
artifact_hash: 532a85457b6c71e1e8174b90594afc6d1be5ab1b35a438039d06e81d212f0a7d
artifact_path: projects/PROJ-994-the-mirage-of-optimizing-training-polici/paper/metadata.json
backend: dartmouth
feedback: Vision review of 5 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T03:27:56.222869Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure presents four panels comparing methods, but the caption omits the 'Baseline' method shown in the first two plots. Additionally, the Clip Ratio chart lacks a y-axis label, though the data is legible.

### Figure 2

The figure effectively displays the sensitivity curves, but the rightmost panel lacks a y-axis label for the '$T_{post}$' metric mentioned in the caption, and the 'Ours' legend entry is undefined.

### Figure 3

The figure presents four ablation panels with a shared legend, but the color scheme for the two orange variants is ambiguous. Additionally, the 'Inference Gap' plot visually contradicts the caption's claim of a 'controlled' trajectory for the full method.

### Figure 4

The figure presents two line plots with clear axes and a legend, but the caption is insufficient as it fails to map the legend entries (model names) to the specific curves shown, leaving the reader to guess which line represents which model.

### Figure 5

Figure 5 effectively visualizes the MIPI principle and the MIPU workflow, clearly distinguishing between canonical RL and the proposed method. The diagrammatic flow, mathematical decomposition, and color coding (blue/red) are well-aligned with the detailed caption, making the conceptual argument easy to follow.
