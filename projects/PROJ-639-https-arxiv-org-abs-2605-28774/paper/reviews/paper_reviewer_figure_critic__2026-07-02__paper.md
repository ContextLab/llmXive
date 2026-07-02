---
action_items:
- id: 1c7dd1842276
  severity: writing
  text: 'Figure 2: The caption contains a formatting artifact ''4$$'' instead of ''4x''
    or ''4x larger''.'
- id: e1da967b3079
  severity: writing
  text: 'Figure 2: The x-axis label ''Model size (log scale)'' is technically inaccurate
    as the tick spacing (2B, 4B, 8B, 32B) represents a linear doubling progression
    rather than a logarithmic scale.'
- id: 3ed6125c4e72
  severity: science
  text: 'Figure 3: The legend labels (''All Tool'', ''All No-Tool'') contradict the
    caption''s description of ''tool-using rollout count''. The stacked areas sum
    to 100% (proportion of questions), but the legend implies these are counts or
    categories of rollouts rather than the proportion of questions falling into specific
    tool-use frequency buckets (e.g., 0, 1-4, 5-8 rollouts). The specific counts defining
    the ''Major'' and ''Minor'' categories are not defined in the caption or legend.'
- id: 688992e0652d
  severity: writing
  text: "Figure 3: The legend text 'Tool Major (>half)' and 'Tool Minor (\u2264half)'\
    \ is ambiguous without defining the denominator. Does 'half' refer to half of\
    \ the 8 rollouts (i.e., 4), or half of the questions? The caption mentions '8\
    \ rollouts/question', but the legend does not explicitly link the threshold to\
    \ this number."
- id: 7c3f4ee86d61
  severity: fatal
  text: 'Figure 4: The caption describes ''Left & Middle'' and ''Right'' panels, but
    the image only contains two plots (Left and Right). The ''Middle'' panel described
    in the caption is missing.'
- id: b20d81cee0bc
  severity: science
  text: 'Figure 4: The caption claims ''Both symptoms reverse during AXPO training
    but stay flat under GRPO,'' yet the legend only defines GRPO (red) and AXPO (blue).
    There is no third line or color representing a ''flat'' GRPO baseline for comparison
    in the plots.'
- id: 7b68dcca0c6e
  severity: writing
  text: 'Figure 4: The y-axis label ''questions with tool'' on the right plot is ambiguous;
    the caption refers to ''all-wrong rate on tool-using subgroups,'' but the axis
    label does not specify that it is a rate or percentage of wrong answers.'
- id: bded95bc22c1
  severity: science
  text: 'Figure 5: The caption claims ''Only AXPO expands both axes simultaneously,''
    but the plot shows the ''SFT+GRPO'' point (red circle) having a higher conditional
    pass@1 than the ''SFT'' point (orange diamond), indicating an expansion in the
    y-axis without AXPO. The visual data contradicts the specific claim made in the
    caption.'
- id: cfeade2bc985
  severity: writing
  text: 'Figure 5: The legend labels ''SFT+AXPO'', ''SFT+GRPO'', ''SFT'', ''Base+GRPO'',
    and ''Base'' are rendered as floating text directly on the plot area rather than
    in a formal legend box, which can be ambiguous regarding which symbol corresponds
    to which method.'
- id: 4a961155312b
  severity: writing
  text: 'Figure 6: The x-axis label reads ''-confidence'' while the caption describes
    plotting ''mean confidence''; the negative sign contradicts the text description
    and standard confidence ranges (0-1).'
- id: b03fa584f6d5
  severity: writing
  text: 'Figure 6: The colorbar label ''training step'' is ambiguous; the caption
    states points represent ''failed tool-using rollouts'' per step, but the colorbar
    implies a continuous variable without specifying if it represents the step index
    or a count.'
artifact_hash: c3a0cadd7f6fad4530caf3425af37b062e581bf6756717caa2b10b397e7c3c2b
artifact_path: projects/PROJ-639-https-arxiv-org-abs-2605-28774/paper/metadata.json
backend: dartmouth
feedback: Vision review of 6 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T05:17:48.390121Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 effectively visualizes the conceptual difference between GRPO and AXPO using a clear tree diagram and a comprehensive legend. The visual elements, including the 'Fixed point' pin and color-coded nodes, align perfectly with the provided caption to explain the resampling mechanism.

### Figure 2

The figure effectively communicates the performance gains of AXPO with clear data points and a shared legend. However, the caption contains a typo ('4$$'), and the x-axis label mischaracterizes the linear doubling scale as logarithmic.

### Figure 3

The figure visualizes the distribution of tool-use frequency but suffers from a disconnect between the caption's description of 'rollout count' and the legend's categorical labels. The specific thresholds for 'Major' and 'Minor' tool use are not explicitly defined in the text, making the data interpretation ambiguous.

### Figure 4

Figure 4 is critically flawed as it is missing the 'Middle' panel described in the caption, and the visual data (only two lines) contradicts the caption's claim of comparing AXPO against a 'flat' GRPO baseline. Additionally, the y-axis label on the right plot lacks the specificity found in the caption.

### Figure 5

The figure effectively visualizes the training stages, but the caption's claim that only AXPO expands both axes is contradicted by the visual data showing SFT+GRPO improving pass@1 over SFT. Additionally, the lack of a formal legend box makes the method-to-symbol mapping rely on proximity to floating text.

### Figure 6

The scatter plot effectively visualizes the correlation between confidence and entropy, but the x-axis label includes a negative sign that contradicts the caption's description of 'mean confidence', and the colorbar label lacks specific context regarding the training steps.
