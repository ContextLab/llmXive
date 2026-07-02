---
action_items:
- id: 68e2eadcde5e
  severity: science
  text: 'Figure 2: The right panel (''Directly Truncate'') shows a triangular attention
    mask where attention is restricted to the causal past (lower triangle), yet the
    caption claims it ''forces attention to spread uniformly across all historical
    frames.'' The visualization contradicts the text description; the attention is
    sparse (triangular), not uniform across the full history.'
- id: 8098ceac88c1
  severity: writing
  text: 'Figure 2: The y-axis label ''Key'' is rotated 90 degrees and partially cut
    off at the bottom (e.g., the ''y'' in ''Key'' is missing or obscured), and the
    tick labels on the right plot''s y-axis are misaligned or missing for some values.'
- id: 1b4f799c4fe3
  severity: writing
  text: 'Figure 3: The title for Stage 2 is cut off on the right edge (''...Causal
    Initial''), making the full stage name illegible.'
- id: 75bd1939e165
  severity: writing
  text: 'Figure 3: The legend in Stage 2 defines ''Bid. Model'' but the corresponding
    block in Stage 1 is labeled ''Bidirect. DiT'', creating inconsistent terminology.'
- id: 1b94ac5ddd37
  severity: science
  text: 'Figure 4: The ''Temporal IoU Distribution'' histogram shows a mean of 0.016%,
    yet the x-axis is labeled ''Pixel Change Rate (%)''. IoU (Intersection over Union)
    and Pixel Change Rate are distinct metrics; the axis label should match the metric
    name or the caption should clarify the relationship.'
- id: 2b41ac21db1d
  severity: writing
  text: 'Figure 4: The ''Difference Matrix'' row lacks a colorbar or legend to define
    the mapping between the heatmap colors (blue to red) and the magnitude of pixel
    differences.'
- id: dc27c778821b
  severity: writing
  text: 'Figure 5: The row labels ''LucyEdit'', ''InsV2V'', ''Stream.V2'', and ''Ours''
    are rotated 90 degrees and placed inside the image grid, which is visually cluttered
    and unconventional for a comparison table.'
- id: c342e62cca38
  severity: writing
  text: 'Figure 5: The instruction text is placed directly over the image content
    in the top row, reducing readability and obscuring parts of the source video.'
- id: bc6ee1867744
  severity: writing
  text: 'Figure 7: The caption states the plot shows ''token cosine similarity between
    consecutive denoising step'' (singular), but the figure displays two distinct
    distributions (Self-Attn and FFN) without clarifying in the text that these represent
    different attention mechanisms or layers.'
- id: 4a0eacc0f2f6
  severity: writing
  text: 'Figure 7: The caption contains a grammatical error (''denoising step'' should
    be ''denoising steps'').'
- id: d4a139ee8aaf
  severity: science
  text: 'Figure 8: The caption states ''line plots indicate the proportion of top-3
    selections,'' but the line plots track the ''Best'' category (dark blue) and the
    ''Second'' category (medium blue) separately, not a combined top-3 sum. Additionally,
    the ''Best'' line for ''Ours'' reaches 100% in the top chart, which contradicts
    the stacked bar showing ~96% ''Best'' and ~4% ''Second'' (implying <100% ''Best'').'
- id: aa206ecf0c17
  severity: writing
  text: 'Figure 8: The legend defines ''Best'', ''Second'', ''Third'', and ''Others'',
    but the line plots only visualize ''Best'' and ''Second'' (or a mix of them),
    leaving the ''Third'' and ''Others'' categories unrepresented in the line plot
    overlay, creating ambiguity about what the lines specifically represent.'
- id: 87fea9a98fd9
  severity: science
  text: 'Figure 12: The ''User Input'' row displays four distinct video frames, but
    the editing instruction is a single static text prompt. This implies the input
    is a video, yet the instruction does not specify how the edit should apply across
    the temporal dimension (e.g., to all frames or a specific segment), making the
    evaluation setup ambiguous.'
- id: a10f9e77c297
  severity: writing
  text: 'Figure 12: The caption ''More comparison between baseline and our LiveEdit''
    is generic and fails to describe the specific editing task shown (changing goose
    feathers to blue), forcing the reader to rely on the image text which is not part
    of the formal caption.'
- id: 80484d3c824e
  severity: writing
  text: 'Figure 12: The row labels (e.g., ''InsV2V'', ''LucyEdit'', ''Stream.'') are
    abbreviations that are not defined in the caption or the figure itself, requiring
    the reader to guess the full method names.'
artifact_hash: ad807d68c3634218d8a37b306582366b9db8e405a9dcf34fb28dd7323fcbdd9e
artifact_path: projects/PROJ-807-liveedit-towards-real-time-diffusion-bas/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T22:48:18.768266Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 effectively communicates the paper's core contribution by visually contrasting three video editing paradigms. The layout is clear, the check/cross indicators are unambiguous, and the visual examples directly support the claims made in the caption regarding accuracy and efficiency.

### Figure 2

Figure 2 contains a significant contradiction between the right panel's visualization (triangular mask) and its caption (claiming uniform spread). Additionally, the y-axis label 'Key' is poorly formatted and partially illegible.

### Figure 3

The figure provides a clear overview of the three-stage framework and the AR-oriented Mask Cache. However, the title for Stage 2 is truncated at the right edge, and there is a minor inconsistency in the naming of the bidirectional model between the diagram and the legend.

### Figure 4

The figure effectively visualizes the mask generation process, but the top-right histogram mislabels its x-axis as 'Pixel Change Rate' while displaying 'Temporal IoU' statistics, and the difference matrix row is missing a color scale legend.

### Figure 5

The figure effectively demonstrates the qualitative superiority of the proposed method over baselines, but the layout is cluttered with rotated row labels embedded in the grid and instruction text overlaid on the source images.

### Figure 6

Figure 6 effectively visualizes the impact of different cache locations on video editing quality. The grid layout clearly compares the input against three ablation settings, and the caption provides the necessary context regarding the editing instruction.

### Figure 7

The figure clearly visualizes the distribution of cosine similarity for two mechanisms, but the caption is grammatically incorrect and lacks specificity regarding what the two distributions represent.

### Figure 8

The figure presents user study results clearly, but the caption's claim that lines represent 'top-3 selections' is inaccurate as the lines track specific rank categories ('Best'/'Second') rather than a cumulative sum, and the 'Best' line value in the top chart conflicts with the stacked bar data.

### Figure 9

Figure 9 effectively demonstrates the versatility of the LiveEdit system through a series of qualitative examples. The layout clearly distinguishes between user inputs and the resulting edits, with descriptive captions for each row explaining the specific transformation applied.

### Figure 10

Figure 10 effectively demonstrates the versatility of the LiveEdit system through a series of qualitative examples. The layout is clear, with distinct 'User input' and 'LiveEdit' columns, and the text descriptions below each row provide necessary context for the edits performed.

### Figure 11

Figure 11 effectively demonstrates the versatility of the LiveEdit system through seven distinct qualitative examples, ranging from material changes (chess pieces, statues) to lighting and texture modifications. The layout is clear, with 'User input' images on the left and the resulting 'LiveEdit' outputs on the right, accompanied by descriptive text explaining the specific transformation for each case.

### Figure 12

Figure 12 presents a qualitative comparison of video editing methods but suffers from a generic caption that omits the specific task details and uses undefined abbreviations for the baseline methods, reducing its standalone clarity.
