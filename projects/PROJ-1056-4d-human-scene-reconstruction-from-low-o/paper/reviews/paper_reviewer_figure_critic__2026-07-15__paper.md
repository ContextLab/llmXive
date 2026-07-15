---
action_items:
- id: 8393cb989f25
  severity: writing
  text: 'Figure 1: The caption reads ''Overview of the proposed .'' with a missing
    noun (e.g., ''method'' or ''pipeline'') after ''proposed''.'
- id: a52f00f6a1a2
  severity: writing
  text: 'Figure 1: Section references in the diagram (e.g., ''Sec 3.1'', ''Sec 3.2'')
    are present, but the caption''s stage descriptions do not explicitly map to these
    section numbers for clarity.'
- id: 4407d204cad6
  severity: writing
  text: 'Figure 2: The caption contains a placeholder ''(Sec. )'' with a missing section
    number, failing to cross-reference the detailed text.'
- id: daba29aea336
  severity: science
  text: 'Figure 2: The diagram shows a ''Motion-Adaptive Consistency Injection'' loop
    but lacks the specific components mentioned in the related Figure 3 caption (e.g.,
    RAFT, backward flow, EMA), making the mechanism opaque.'
- id: 57db54cf73a8
  severity: science
  text: 'Figure 3: The diagram shows ''Refined Output'' ($O_{t-K}$) being warped,
    but the caption states ''previous enhanced outputs'' are warped. While likely
    referring to the same thing, the diagram should explicitly label the input to
    the warping step as the ''Enhanced Output'' or ''Refined Output'' to match the
    caption''s description of the recursive process.'
- id: 747e061a1a97
  severity: writing
  text: 'Figure 3: The ellipsis (...) between the $t-K$ and $t-1$ blocks implies a
    sequence, but the arrows from the ''Refined Output'' blocks go directly into the
    warping step without showing the recursive loop where the output of one step becomes
    the input of the next. This makes the ''recursive'' nature described in the caption
    visually ambiguous.'
- id: 513aa4d5b04c
  severity: writing
  text: 'Figure 5: The caption states ''Dance  Xu et al. (Mobile Stage); Yoga  Xu
    et al. (SelfCap)'', but the image labels only show ''Tennis'', ''Fencing'', ''Dance'',
    and ''Yoga'' without specifying which dataset corresponds to which column, creating
    ambiguity about the source of the Tennis and Fencing data.'
- id: 1be5516b7139
  severity: science
  text: 'Figure 5: The ''Ours'' row shows significantly cleaner results than the ''GT''
    (Ground Truth) row in the Tennis and Fencing columns, where ''GT'' appears to
    have motion blur or artifacts not present in the proposed method; this contradicts
    the expectation that GT should be the cleanest reference and suggests the ''GT''
    label may be misapplied or the comparison is misleading.'
- id: bc71f36d14b2
  severity: writing
  text: 'Figure 6: The caption references ''Sec. .'' with a missing section number;
    please insert the correct section reference.'
- id: fd5600bc884a
  severity: science
  text: 'Figure 7: The caption claims to show qualitative results on EgoExo-4D, but
    the rendered image is identical to Figure 5 (Dance scene) and Figure 1 (CPR scene),
    failing to demonstrate the claimed diversity or specific dataset application.'
- id: 083ae412bb62
  severity: writing
  text: 'Figure 8: The caption contains empty section references ''(Sec. )'' that
    need to be filled with the correct section numbers.'
- id: 2525d112e60b
  severity: writing
  text: 'Figure 9: The caption contains a broken cross-reference ''Sec. .'' where
    the section number is missing.'
- id: a846e4245dd8
  severity: writing
  text: 'Figure 9: The caption lists ''per-pixel confidence map'' as the third item,
    but the image label uses the variable ''$c$'' without explicitly defining it as
    a map in the text.'
- id: 0158bca9f708
  severity: science
  text: 'Figure 10: The legend defines a ''Start'' (green circle) and ''End'' (orange
    square), but the rendered trajectory shows the orange square at the start of the
    path and the green circle is not visible, contradicting the legend.'
- id: a5af15101f43
  severity: writing
  text: 'Figure 10: The labels ''V0'', ''V1'', ''V2'', and ''V3'' are present on the
    plot but are not defined in the legend or the caption.'
- id: f18394f7abe7
  severity: science
  text: 'Figure 11: The caption claims ''Each color represents the same person matched
    across 4 cameras'', but the image shows multiple people (Person A, B, C) simultaneously
    in the same frame, each with different colored boxes. This contradicts the caption''s
    explanation of the color coding scheme.'
- id: cbd42bfc7787
  severity: writing
  text: 'Figure 11: The caption references ''Table .'' with a missing table number,
    making it impossible to verify the claimed 97.8% association accuracy.'
artifact_hash: ca7acd8eb96627c08c8e24703eed6a4159188067f14a19009f5f71e7f58b21ed
artifact_path: projects/PROJ-1056-4d-human-scene-reconstruction-from-low-o/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-15T02:36:34.126576Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 provides a clear visual overview of the four-stage pipeline with distinct modules and data flow. However, the caption contains a grammatical error ('proposed .') and could better align its text with the specific section labels shown in the diagram.

### Figure 2

The figure provides a high-level schematic of the recursive enhancement module but lacks specific implementation details in the diagram itself. The caption is incomplete due to a missing section number reference.

### Figure 3

The figure provides a clear schematic of the data flow but lacks explicit visual cues for the recursive loop described in the caption, and the labeling of 'Refined Output' vs 'Enhanced Output' could be more precise to match the text.

### Figure 4

Figure 4 effectively presents a qualitative comparison across four scenes (Legoassemble, Grappling, Sword, Karate) and five methods (Dyn-3DGS, MonoFusion, STG, Ours, GT). The grid layout is clear, labels are legible, and the visual evidence strongly supports the caption's claim that the proposed method produces sharper backgrounds and more robust human reconstructions than the baselines.

### Figure 5

The figure presents a qualitative comparison but suffers from ambiguous dataset attribution in the caption and a potentially misleading 'GT' row that appears lower quality than the proposed method in some columns, undermining the validity of the comparison.

### Figure 6

The figure effectively demonstrates the visual improvement of the recursive enhancement module by comparing raw and enhanced renders. However, the caption contains two instances of missing section numbers ('Sec. .') that need to be filled in.

### Figure 7

The figure is visually clear but fails to support its caption's claim of showing results on the EgoExo-4D dataset, as the images appear to be duplicates of scenes shown in other figures (Figure 1 and Figure 5).

### Figure 8

The figure effectively demonstrates the visual improvement of background reconstruction after refinement, but the caption contains empty section references that should be corrected.

### Figure 9

The figure effectively visualizes the four stages of the enhancement module with clear labels. However, the caption contains a missing section number reference and could be slightly more explicit about the variable definitions.

### Figure 10

The figure effectively visualizes the augmented camera trajectory, but the start/end markers in the legend contradict the visual path, and the specific view labels (V0-V3) lack definition.

### Figure 11

Figure 11's color-coding scheme is confusing and contradicts its caption, which claims each color represents the same person across cameras while showing multiple people with different colors in the same frame. Additionally, the caption references an incomplete table number.

### Figure 12

Figure 12 effectively visualizes the initialized human poses across four distinct scenes using overlaid SMPL meshes on point clouds. The caption clearly explains the content, and the images demonstrate the method's ability to estimate body poses from sparse multi-view inputs without any missing labels or confusing elements.
