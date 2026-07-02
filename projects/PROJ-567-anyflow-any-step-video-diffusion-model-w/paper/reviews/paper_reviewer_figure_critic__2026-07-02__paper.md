---
action_items:
- id: 37a6cb8abb36
  severity: science
  text: 'Figure 1: The legend defines ''Zero Init Time Emb'' as ''Emb(t) + Emb''(t
    - r)'', but the plot shows this method''s norm increasing significantly over training
    iterations. If this were a simple sum of embeddings, it should remain constant
    or behave differently; the label likely misrepresents the actual method being
    plotted (perhaps it is the ''distilled'' or ''trained'' version, not the initialization).'
- id: bc3e8d8f006f
  severity: writing
  text: "Figure 1: The legend text for 'Interpolated Time Emb (Ours)' is cut off or\
    \ poorly formatted, showing 'g \xB7 Emb(t) + (1 - g) \xB7 Emb'(r)' on a new line\
    \ without clear alignment, making it hard to associate with the red line."
- id: dd4ead16c54f
  severity: science
  text: 'Figure 2: The green line labeled ''w(t) = Uniform(0, 1)'' is plotted as a
    linearly increasing function (slope 1), which contradicts the definition of a
    uniform distribution (constant density). Additionally, the caption defines $f(t)
    = p(t)w(t)$, but the legend labels the curves as $w(t)$, creating a mismatch between
    the plotted density and the legend''s variable name.'
- id: fbe9749e6c1e
  severity: science
  text: "Figure 3: The 'Annotations' box defines $f_\theta(z_t, t)$ as 'Consistency\
    \ Model' and $f_\theta(z_t, t, r)$ as 'Flow Map Model', but the diagram labels\
    \ in (a) and (b) use inconsistent notation (e.g., $f_\theta(z_{t_1}, t_1)$ vs\
    \ $f_\theta(z_T, T, t)$) without explicitly mapping them to the defined model\
    \ types, creating ambiguity about which model is used at each step."
- id: c4fff0c944e6
  severity: writing
  text: 'Figure 3: The ''Annotations'' box is visually separated from the main diagrams
    and lacks a clear border or background distinction, making it easy to overlook;
    integrating it closer to the relevant panels or using a more prominent visual
    style would improve clarity.'
- id: 5a1c35464b08
  severity: writing
  text: 'Figure 4: The text inside the diagram boxes (e.g., ''Self-Forcing Causal
    Model v1.0'', ''ODE-Int + DMD'') is extremely small and illegible, making the
    specific steps of the pipeline unreadable.'
- id: 114d6944f313
  severity: science
  text: 'Figure 4: The diagram depicts a ''Self-Forcing'' pipeline where the model
    is discarded (trash can icon) after fine-tuning, which contradicts the caption''s
    claim that the method ''bypasses the complexities of retraining'' by implying
    the model is not adapted for use.'
- id: 53d5a0c9ed3f
  severity: science
  text: 'Figure 5: The caption claims the pre-trained model (a) struggles with ''robot
    arm type'' identity preservation, but the images in (a) and (b) show the same
    robot arm model; the actual difference is the generated motion (arm reaching vs.
    static), which contradicts the specific ''identity'' claim.'
- id: fff0bf090e1c
  severity: science
  text: 'Figure 5: The caption claims the pre-trained model (a) struggles with ''trajectory
    accuracy'' for pedestrians, but the pedestrian in (a) moves across the frame similarly
    to (b); the visible failure in (a) is actually the generation of a large white
    car artifact, not the pedestrian trajectory.'
- id: aef34c2c93f4
  severity: science
  text: 'Figure 6: The caption states that (a) Consistency distillation learns a mapping
    from $z_t$ to $z_0$, but the ''Forward Consistency Training'' panel shows trajectories
    mapping $z_0$ to $z_T$ (or $z_t$ to $z_T$), which contradicts the text description
    of the learning objective.'
- id: a40ea506e255
  severity: writing
  text: 'Figure 6: The ''Re-Noise State'' label in panel (a) points to a grey circle,
    but the caption does not define this symbol or explain the re-noising process
    visually depicted.'
- id: c33480c85e9e
  severity: science
  text: 'Figure 8: The y-axis ''Vbench Score'' scales differ significantly across
    the three subplots (approx. 82.0-84.1, 75.0-84.5, and 61.0-84.5), yet the plots
    are presented side-by-side without explicit visual separation or individual axis
    labels, which risks misleading the reader into comparing absolute values across
    panels that are not on the same scale.'
- id: 739ed03ab7e6
  severity: writing
  text: 'Figure 8: The tables at the top of the figure (labeled ''Table 2'', ''Table
    2-1'', ''Table 2-1-1'') are not referenced in the figure caption, making their
    relationship to the line plots below unclear.'
artifact_hash: 3aad81d8a133042c5a798b8bf30d90974b62e8f4dc5a0e7e17e6ccdaa711ef9d
artifact_path: projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/paper/metadata.json
backend: dartmouth
feedback: Vision review of 8 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:29:27.469388Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 presents a comparison of embedding norms across sample steps, but the legend contains a potentially misleading mathematical definition for the 'Zero Init' method and has formatting issues that reduce clarity.

### Figure 2

The figure contains a scientific error where the 'Uniform' distribution is plotted as a linear ramp rather than a constant, and the legend labels the curves as $w(t)$ while the caption and y-axis indicate the plotted values are the resulting density $f(t)$.

### Figure 3

Figure 3 effectively compares backward simulation paradigms but suffers from inconsistent notation between the annotation definitions and diagram labels, and the annotations box is visually underemphasized, risking reader confusion.

### Figure 4

The figure illustrates the pipeline but suffers from illegible text within the diagram boxes. Additionally, the visual depiction of discarding the model after fine-tuning appears to contradict the caption's claim about bypassing retraining complexities.

### Figure 5

The figure effectively visualizes the fine-tuning results, but the caption's specific claims regarding 'identity preservation' and 'trajectory accuracy' do not align with the visual evidence, which instead shows motion differences and object hallucination artifacts.

### Figure 6

The figure effectively illustrates the difference between consistency and flow map distillation, but the caption's description of the mapping direction in panel (a) contradicts the visual trajectory shown, and the 'Re-Noise State' symbol lacks a definition in the caption.

### Figure 7

Figure 7 provides a clear and well-structured overview of the AnyFlow pipeline, effectively illustrating the Forward Flow Map Training and On-Policy Flow Map Distillation stages. The diagram includes a comprehensive legend defining model types and training states, and the flow of data and gradients is logically presented.

### Figure 8

The figure presents quantitative comparisons of AnyFlow against baselines, but the y-axis scales vary drastically between the three subplots, potentially misleading readers about the magnitude of differences. Additionally, the data tables at the top are not explained in the caption.
