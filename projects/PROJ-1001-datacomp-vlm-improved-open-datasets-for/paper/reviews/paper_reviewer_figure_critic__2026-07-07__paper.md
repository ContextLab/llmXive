---
action_items:
- id: fac021935461
  severity: writing
  text: 'Figure 2: The caption contains multiple instances of missing text where the
    model name ''DCVLM-Baseline'' should appear (e.g., ''-Baseline outperforms...'',
    ''trained on -Baseline'', ''beats an 8B model trained on FineVision... a 4 compute
    reduction''). The text ''DCVLM-'' is missing before ''Baseline'' and the word
    ''four'' is missing before ''compute reduction''.'
- id: 2d72f6417846
  severity: writing
  text: 'Figure 2: The caption cites specific dataset references (deshmukh2025nvidia,
    an2025llava, wiedm...)'
- id: 0444fea2d3d7
  severity: writing
  text: 'Figure 2: The caption cites specific dataset references (deshmukh2025nvidia,
    an2025llava, wiedmann2025finevision) that are not defined or explained in the
    caption itself, making it unclear which lines in the chart correspond to which
    dataset.'
- id: a2f7554f075c
  severity: science
  text: 'Figure 2: The x-axis label ''Params, Tokens'' is ambiguous; it is unclear
    if the values represent parameter count, token count, or a combination, and the
    specific mapping of each point (e.g., ''1B, 6.25B'') to these metrics is not explicitly
    defined in the axis or caption.'
- id: e0e889384f68
  severity: writing
  text: 'Figure 3: The legend in the 4B Model panel uses ''IC'' and ''IT'' abbreviations
    (e.g., ''10% IC, 70% IT''), but the caption defines the mixtures using ''c'' and
    ''i'' (e.g., ''10c-70i''). The legend should be updated to match the caption''s
    terminology for consistency.'
- id: e351eb0e6964
  severity: writing
  text: 'Figure 3: The legend in the 4B Model panel is not visible in the other two
    panels (1B and 2B), forcing the reader to look at the far right panel to identify
    the lines in the left panels. A legend should be present in each subplot or the
    layout should be adjusted.'
- id: 5ce4f51aedb8
  severity: science
  text: 'Figure 4: The caption claims the orange ring highlights the best configuration
    at each scale, but the left plot''s ring highlights 15% IT (43.7%) while the data
    shows 40% IT (43.4%) is lower; however, the ring is at 15% IT which is indeed
    the highest point shown. Wait, looking closer at the left plot, the point at 15%
    IT is ~43.7%, and the point at 40% IT is ~43.4%. The ring is correctly placed
    on the highest point. However, the caption states ''At small scale, the 65%IC
    baseline is competitive''. '
- id: a2bc380d3de1
  severity: writing
  text: "Figure 4: The x-axis label 'Instruction-Tuning %' is clear, but the caption\
    \ refers to 'IC% <-> IT%', implying a trade-off. The axis only shows IT%, which\
    \ is fine, but the caption's mention of '65%IC baseline' requires the reader to\
    \ infer that 65% IC = 35% IT. This is not explicitly stated in the figure or caption,\
    \ though it is a reasonable assumption. However, the caption says '9-point sweep',\
    \ and counting the points on the x-axis: 15, 20, 25, 30, 35, 40, 50, 60, 70 \u2014\
    \ that is 9 points. So that i"
- id: 3ff905684950
  severity: science
  text: 'Figure 4: The caption states ''+2.0% over baseline'' for the medium scale
    optimal (70% IT), but visually comparing the 70% IT point (56.3%) to the 35% IT
    point (baseline, ~54.8%) yields a difference of approximately 1.5%, not 2.0%.
    This numerical discrepancy between the caption and the plotted data undermines
    the claim.'
- id: f13c0eaef9c3
  severity: writing
  text: 'Figure 5: The caption states ''Only 3 of 39 configurations show gains,''
    but the chart displays four bars with positive values (Mixtral >0.9, Nemotron
    >0.9, Nemotron >0.9, Core-benchmaxxed), creating a contradiction between the text
    and the visual data.'
- id: f19f9a660e20
  severity: writing
  text: 'Figure 5: The caption claims gains are ''all from text quality classifiers
    applied exclusively to the text-only data pool,'' but the chart shows ''Mixtral
    >0.9 (text only)'' and ''Nemotron >0.9 (text only)'' as blue bars (Text-only modality),
    while ''Core-benchmaxxed (text only)'' is also blue; however, the caption''s phrasing
    implies a specific subset that might be confusingly mapped to the ''Text-only
    (T)'' legend entry which includes other negative bars.'
- id: 37110e25dce6
  severity: science
  text: 'Figure 5: The y-axis labels are extremely dense and overlapping (e.g., ''Length
    text only (rm short <0.1)''), making specific filter configurations difficult
    to read and distinguish without zooming.'
- id: 059c0339c188
  severity: writing
  text: 'Figure 7: The x-axis labels (e.g., ''65c no-filter'', ''65c + Mixtral'')
    are not defined in the caption or figure; the meaning of ''65c'', ''40c'', and
    ''+ Mixtral'' is unclear without external context.'
- id: f9a9ede6b433
  severity: science
  text: 'Figure 7: The green delta values (+2.2, +1.1, etc.) indicate the improvement
    of Sample-Level over Shard-Level, but the y-axis shows absolute ''Micro Avg (%)''
    values. The caption claims a ''+1--2%'' improvement, yet the first bar shows a
    +2.2% gain, which slightly exceeds the stated range.'
- id: 71945fe38f75
  severity: writing
  text: 'Figure 8: The x-axis label ''Temperature (T)'' is ambiguous because the tick
    labels (0.5, 0.8, 1.0, 2.0, 4.0) do not explicitly state the unit or scale (e.g.,
    ''x10^3'' or ''seconds''), and the caption does not define the temperature scale.'
- id: 92a42e6ecb48
  severity: writing
  text: 'Figure 8: The orange line segment labeled ''T=1 baseline'' extends beyond
    the data point at T=1.0 without a clear endpoint or legend entry explaining its
    purpose, which may confuse readers about whether it represents a trend or a reference
    line.'
- id: b18a16ebb138
  severity: science
  text: 'Figure 9: The title claims a ''+5.8% Micro Avg improvement'', but the chart
    shows ''Ours'' (58.9) is only +5.8 points higher than ''FineVision'' (53.1). If
    these are percentages, the relative improvement is ~10.9%, not 5.8%. If 5.8 is
    the absolute point difference, labeling it as a ''%'' improvement in the title
    is misleading.'
- id: 90c37eeca8b1
  severity: writing
  text: 'Figure 9: The title contains raw LaTeX formatting artifacts (''4B x 100B''
    rendered as ''4B x 100B'' with potential encoding issues or just poor typography)
    and the caption text ''outperforms on 5 of 6 categories'' is missing the subject
    name (likely ''DCVLM'' or ''Ours'') due to a copy-paste error in the manuscript.'
- id: fadd67896726
  severity: science
  text: 'Figure 9: The caption claims a +13.2% gain in ''General'' and +18.1% in ''Vision'',
    but the chart shows absolute point gains of 13.2 (68.4-55.2) and 18.1 (57.2-39.1).
    Describing absolute percentage point differences as ''% improvement'' is ambiguous
    and often mathematically incorrect (e.g., 13.2 points on a 55.2 base is a 24%
    relative increase).'
- id: e864548195b0
  severity: writing
  text: 'Figure 10: The caption states ''The largest drops are on ScienceQA (-10.7%),
    nq (-7.6%), and ChartQA (-5.9%)'', but the chart shows ''nq'' at -7.6% and ''ChartQA_TEST''
    at -5.9%, while ''AI2D_TEST_NO_MASK'' is at -3.9%. The caption omits ''AI2D_TEST_NO_MASK''
    which is visually distinct, and the text ''appeared strongest'' is grammatically
    incomplete (missing subject, likely ''DataComp-VLM'').'
- id: af2cbbd15768
  severity: writing
  text: 'Figure 10: The caption text ''categories where appeared strongest'' is missing
    the subject (e.g., ''where DataComp-VLM appeared strongest''), making the sentence
    grammatically incomplete and confusing.'
- id: 4497a56818fd
  severity: writing
  text: 'Figure 11: The caption contains a sentence fragment at the end (''closing
    roughly half the remaining gap with decontaminated .'') where the model name (likely
    ''Baseline'') is missing.'
- id: d91e018cfad4
  severity: science
  text: 'Figure 11: The title claims a ''+3.1% gain'' from upsampling, but the visual
    difference between the ''Ours (standard)'' bar (45.8) and the ''+ OCR Upsampled
    25%'' bar (48.9) is 3.1 points; however, the caption implies this closes the gap
    with ''decontaminated'' (51.7), yet the gap between 48.9 and 51.7 is 2.8, which
    is not ''roughly half'' of the total gap (51.7 - 45.8 = 5.9). The math in the
    caption is slightly confusing or imprecise relative to the bars shown.'
- id: bd0bd6dd9ba2
  severity: writing
  text: 'Figure 12: The rightmost bar is labeled ''3 filters (80%)'', but the caption
    states ''Scaling to 3 filters at 80% rejection each''. The x-axis label is ambiguous
    and could be misinterpreted as a single filter with 80% rejection; it should explicitly
    state ''3 filters (80% each)'' to match the caption.'
artifact_hash: d4a22931e6b886440cd41104bb215d7473154b2e0677ff1cb31fe0010e81d224
artifact_path: projects/PROJ-1001-datacomp-vlm-improved-open-datasets-for/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T10:31:19.604890Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 is a clear and well-structured flowchart that effectively visualizes the data collection pipeline described in its caption. All steps, data types, and final corpus pools are legible, and the logical flow from sourcing to the final compute-scale pools is easy to follow.

### Figure 2

The figure is visually clear and effectively communicates the dataset composition and performance gains. However, the caption contains significant text errors (missing model name 'DCVLM' and the word 'four') and fails to explicitly map the cited dataset references to the specific lines in the chart, reducing its standalone clarity.

### Figure 3

The figure effectively visualizes the scaling grid and supports the caption's claims about mixture performance. However, the legend is only present in the rightmost panel, and the abbreviations used in the legend ('IC', 'IT') do not match the notation in the caption ('c', 'i').

### Figure 4

The figure is well-structured with clear axes and legends, but the caption contains a numerical inaccuracy: it claims a +2.0% gain over the baseline for the medium scale optimal configuration, whereas the plotted data shows a gain of approximately 1.5%.

### Figure 5

The figure effectively visualizes the ablation study with clear color coding, but the caption contains a factual error regarding the count of positive-gain configurations (stating 3 when 4 are shown) and the y-axis labels are overly dense, reducing readability.

### Figure 6

Figure 6 is a clear and well-constructed bar chart that effectively supports its caption's claim. The axes, units, legend, and specific data values (including delta annotations) are all present, legible, and correctly labeled.

### Figure 7

The figure clearly visualizes the performance difference between sampling strategies with helpful delta annotations, but the x-axis configuration labels are undefined and the specific gain values slightly exceed the range described in the caption.

### Figure 8

The figure effectively communicates that T=1 is near-optimal, but the x-axis lacks explicit units for temperature, and the orange baseline line is visually ambiguous without further explanation in the caption or legend.

### Figure 9

The figure effectively displays the performance comparison, but the title and caption contain significant mathematical ambiguities regarding 'improvement' (absolute points vs. relative percent) and missing subject names. Additionally, the title includes raw LaTeX artifacts.

### Figure 10

The figure is a clear bar chart showing per-dataset score changes, but the caption contains a grammatical error ('where appeared strongest') and slightly misaligns with the specific dataset names shown (e.g., 'ChartQA_TEST' vs 'ChartQA').

### Figure 11

The bar chart clearly displays the performance gains from upsampling OCR data, but the caption contains a missing model name at the end and the textual claim about 'closing half the gap' is mathematically ambiguous compared to the bar values.

### Figure 12

Figure 12 effectively demonstrates that online filtering adds negligible overhead, with clear axes and data points. However, the x-axis label for the 3-filter configuration is slightly ambiguous compared to the precise wording in the caption.
