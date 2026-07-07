---
action_items:
- id: 4578c241c2cf
  severity: writing
  text: 'Figure 2: The legend uses ''IC'' and ''IT'' (e.g., ''10% IC, 70% IT''), but
    the caption defines the mixtures using ''c'' and ''i'' (e.g., ''10c-70i''). This
    inconsistency between the visual legend and the text description is confusing.'
- id: b31f5b51e649
  severity: writing
  text: 'Figure 2: The y-axis label ''Micro Avg (%)'' is ambiguous; it is unclear
    if the values (e.g., 41, 42) represent raw percentages (41%) or a scaled score
    (e.g., 41.0 out of 100).'
- id: 4826bf2487a2
  severity: science
  text: 'Figure 3: The caption claims the optimal configuration at medium scale is
    ''70%IT (+2.0% over baseline)'', but the chart shows the baseline (dotted line)
    at ~54.3% and the best point at 56.3%, which is a +2.0% absolute difference, not
    a relative one. However, the text says ''+2.0% over baseline'' which is ambiguous
    (could mean percentage points or relative percent). Given the context of micro
    avg %, it likely means percentage points, but the phrasing is slightly imprecise.
    More critically, the capti'
- id: 2c43681bd511
  severity: writing
  text: 'Figure 3: The y-axis label ''Micro Avg (%)'' is present, but the tick labels
    on the left plot start at 41.0 and go to 43.5, while the right plot starts at
    54.25 and goes to 56.25. This makes direct visual comparison between scales difficult.
    Consider using a shared y-axis scale or adding a note explaining the different
    baselines.'
- id: 784d7fb7285b
  severity: writing
  text: "Figure 4: The title text 'Only 3 of 39 filters show any gain \u2014 all <\
    \ 1% and wash out at larger scale' contradicts the caption's claim that gains\
    \ are '>= +0.5%'; the title's '< 1%' is ambiguous and potentially misleading regarding\
    \ the magnitude of the positive results."
- id: 86f48d650a86
  severity: writing
  text: 'Figure 4: The title text ''Small scale (1B model, 6.25B tokens)'' is redundant
    with the caption and makes the header cluttered; this information is better placed
    in the caption or a subtitle.'
- id: d5af6d59a5a7
  severity: writing
  text: 'Figure 7: The caption contains a typo ''flattening ($T 2$)'' which is missing
    the inequality symbol (likely $T \ge 2$ or $T > 1$) and does not match the x-axis
    label ''2.0 (sqrt)''.'
- id: ce5ba2be91c7
  severity: science
  text: 'Figure 7: The orange line labeled ''T=1 baseline'' extends from T=1.0 to
    approximately T=2.5 without data points, implying a trend that is not supported
    by the discrete sampling shown for the red line.'
- id: 2cef3f5e1b7d
  severity: science
  text: 'Figure 8: The caption claims a +13.2% gain in ''General'' and +18.1% in ''Vision'',
    but the chart shows +13.2% (68.4 vs 55.2) and +18.1% (57.2 vs 39.1) respectively.
    However, the caption states ''outperforms on 5 of 6 categories'', but the chart
    shows ''Ours'' trailing in ''Knowledge'' (67.6 vs 68.0) and ''OCR'' (54.1 vs 58.9).
    This is only 4 out of 6 categories where ''Ours'' outperforms, contradicting the
    caption''s claim of 5.'
- id: dcb0caaa3c54
  severity: writing
  text: 'Figure 8: The title mentions ''+5.8% Micro Avg improvement'', which matches
    the chart (58.9 vs 53.1), but the caption does not mention this specific value,
    creating a disconnect between the visual title and the textual description.'
- id: 373d6e1580a9
  severity: writing
  text: 'Figure 9: The caption states ''The largest drops are on ScienceQA (-10.7%),
    nq (-7.6%), and ChartQA (-5.9%)'', but the chart shows ''ChartQA_TEST'' at -5.9%
    and ''nq'' at -7.6%, while ''ScienceQA_VAL'' is -10.7%. The caption omits the
    ''_VAL'' and ''_TEST'' suffixes present in the chart labels, creating a minor
    inconsistency in dataset naming.'
- id: 4978a91e26cc
  severity: writing
  text: 'Figure 9: The caption text ''...categories where appeared strongest'' contains
    a missing subject (likely ''DataComp-VLM'' or ''the model''), making the sentence
    grammatically incomplete.'
- id: 8dd8121e71f0
  severity: writing
  text: 'Figure 10: The caption ends with ''closing roughly half the remaining gap
    with decontaminated .'' which is grammatically incomplete and missing the noun
    (likely ''FineVision'') that the bar labels imply.'
- id: 3cd91accf4ed
  severity: science
  text: 'Figure 10: The title claims ''Upsampling OCR to 25% yields +3.1% gain'',
    but the visual comparison between the ''Ours (standard)'' bar (45.8) and the ''+
    OCR Upsampled 25%'' bar (48.9) shows a difference of 3.1, which is correct, yet
    the caption text ''closing roughly half the remaining gap'' is vague without explicitly
    stating the gap size to the FineVision baseline in the text.'
- id: 2c9abe3be8da
  severity: writing
  text: "Figure 11: The rightmost bar chart lacks a y-axis label; the axis shows values\
    \ (0.90\u20131.15) but does not explicitly state the unit or metric (e.g., 'Runtime\
    \ multiplier' or 'Relative runtime'), relying solely on the caption for context."
- id: cb3b9db3db8c
  severity: writing
  text: 'Figure 12: The x-axis label contains a typo (''orignal'' instead of ''original'').'
- id: 3014e716fe89
  severity: science
  text: 'Figure 12: The title claims ''no significant gain,'' but the ''MTL'' category
    shows a +1.2% gain for synthetic spatial captions, which appears to contradict
    the title''s absolute claim without a statistical significance indicator (e.g.,
    error bars) to justify the dismissal.'
artifact_hash: d4a22931e6b886440cd41104bb215d7473154b2e0677ff1cb31fe0010e81d224
artifact_path: projects/PROJ-1001-datacomp-vlm-improved-open-datasets-for/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T10:43:38.922584Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 is a clear and well-structured flowchart that effectively visualizes the data collection pipeline described in its caption. All steps, data types, and final corpus sizes are legible and logically connected.

### Figure 2

The figure effectively visualizes the scaling trends described in the caption, but the legend abbreviations ('IC', 'IT') contradict the caption's notation ('c', 'i'), and the y-axis unit label is slightly ambiguous.

### Figure 3

Figure 3 effectively displays the line search results with clear annotations for best points, but the caption's claim of 'competitive' baseline at small scale lacks quantitative support, and the differing y-axis scales between subplots hinder direct comparison.

### Figure 4

The figure effectively visualizes the filter ablation results with clear color coding and value labels. However, the title text contains a minor contradiction regarding the magnitude of gains ('< 1%' vs '>= +0.5%') and includes redundant information that clutters the header.

### Figure 5

Figure 5 is clear and effectively supports its caption. The bar chart clearly displays the 'No Filter' vs. 'NVIDIA Mixtral Text-Only' comparison across four mixture/model configurations, with explicit numerical labels and delta annotations ($\Delta$) that match the caption's claims.

### Figure 6

The figure clearly compares sample-level versus shard-level sampling across four configurations on validation and core sets. The legend, axis labels, and units are present and legible, and the green annotations accurately reflect the performance gains described in the caption.

### Figure 7

The figure effectively visualizes the performance drop at extreme temperatures, but the caption contains a typo regarding the flattening condition, and the orange baseline line implies a continuous trend without data points.

### Figure 8

The figure clearly displays the comparison data with appropriate labels and values, but the caption's claim that the method outperforms in 5 of 6 categories is factually incorrect based on the visual data, which shows it trailing in two categories (Knowledge and OCR).

### Figure 9

The figure is a clear and well-organized bar chart that effectively visualizes per-dataset score changes. The caption accurately describes the data trends and the average drop line, though it contains a minor grammatical omission and slightly simplifies the dataset names compared to the axis labels.

### Figure 10

The bar chart effectively visualizes the performance gains from upsampling OCR data, but the figure caption contains a grammatical error where the sentence trails off after 'decontaminated', failing to name the baseline model.

### Figure 11

The figure effectively demonstrates the negligible overhead of online filtering as claimed in the caption, but the rightmost bar chart is missing a y-axis label to explicitly define the plotted metric.

### Figure 12

The figure is visually clear and the legend is well-defined, but the x-axis label contains a typo ('orignal'). Additionally, the title's claim of 'no significant gain' is visually contradicted by the +1.2% data point in the MTL category, which lacks error bars to statistically justify the dismissal.
