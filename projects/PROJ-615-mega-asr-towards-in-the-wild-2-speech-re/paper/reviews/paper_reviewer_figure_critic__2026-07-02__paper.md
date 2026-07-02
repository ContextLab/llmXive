---
action_items:
- id: 9bee9878cc18
  severity: science
  text: 'Figure 1: The left radar chart''s radial axis is labeled ''100'' at the outermost
    ring, but the data points for ''CommonVoice22'' (6.97) and ''Voxpopuli'' (6.25)
    are plotted near the 80% mark, implying the axis represents a percentage scale
    (0-100%) while the labels suggest absolute values or a different metric. This
    creates a severe visual distortion where low scores appear high.'
- id: 4859eefc6e6b
  severity: writing
  text: 'Figure 1: The legend at the bottom is cut off on the left side, making the
    full name of the blue line (''Qwen3-ASR-1.7B(Previous SOTA)'') partially illegible.'
- id: 4af725f745df
  severity: science
  text: "Figure 3: The right panel's y-axis (0.45\u20130.65) is unlabeled, making\
    \ it impossible to interpret the 'comparison of difficulty sampling distributions'\
    \ claimed in the caption."
- id: ffea8eeb90cf
  severity: science
  text: "Figure 3: The right panel legend lists four sampling methods (Gaussian, Linear,\
    \ Sqrt-Bwd, Sqrt-Fwd), but the caption does not define these terms or link them\
    \ to the left panel\u2019s 'atomic effects'."
- id: ab7d3fbd4fdf
  severity: writing
  text: 'Figure 3: Left panel subplots lack individual y-axis labels; while ''1 -
    WER'' is shown on the first subplot, it is not repeated or clarified for the other
    seven, risking misinterpretation.'
- id: a4791ecfa989
  severity: fatal
  text: 'Figure 4: The caption is a placeholder (''Enter Caption [figure3.pdf]'')
    and does not describe the figure content, making it impossible to verify if the
    figure supports its claims.'
- id: 7cbfbeaf54f5
  severity: fatal
  text: 'Figure 4: The filename in the caption (''figure3.pdf'') contradicts the figure
    label (''Figure 4''), indicating a likely copy-paste error or mislabeling.'
- id: 74df5968e3e2
  severity: science
  text: 'Figure 4: The diagram contains undefined abbreviations and symbols (e.g.,
    ''q'', ''O1'', ''R1'', ''A1'', ''WER'', ''LCS'') without a legend or explanation
    in the caption.'
- id: 00ded679b4b2
  severity: science
  text: 'Figure 5: The caption describes the framework as ''DG-WGPO'', but the diagram
    explicitly labels the initialization stage as ''A2S-SFT'' and the core mechanism
    as ''Recov-Recon Dynamic Reward'' without ever mentioning ''DG-WGPO'' or ''gated
    fusion'' in the visual elements, creating a disconnect between the text and the
    figure content.'
- id: 2b6425930169
  severity: writing
  text: 'Figure 5: The ''Word-level Reward'' box contains a formula for ''n_recal''
    that is illegible due to low resolution; the subscripts and specific terms in
    the fraction cannot be read.'
- id: b6c1be29cdf9
  severity: fatal
  text: 'Figure 6: The caption is ''Enter Caption [figure3.pdf]'', indicating a placeholder
    error where the figure content (likely a pipeline diagram) does not match the
    assigned caption file or text.'
- id: d105eee64262
  severity: science
  text: 'Figure 6: The diagram displays a complex ''Recov-Recon Dynamic Reward'' framework
    with specific components like ''A2S-SFT'' and ''Mega-ASR'', but the missing caption
    fails to define these terms or explain the workflow, rendering the figure unintelligible
    without external context.'
- id: 85a23cb65a19
  severity: science
  text: 'Figure 7: The ''WER'' (Word Error Rate) for the Ground Truth row is labeled
    as ''--'', which is technically incorrect as the WER of a reference against itself
    is 0.0%. This creates a confusing baseline for the comparison.'
- id: 21f902bc78bc
  severity: writing
  text: 'Figure 7: The WER for the ''Qwen3-ASR'' model in the ''Far field'' case is
    listed as 100.0% for an ''<Empty>'' output. While understandable, WER is typically
    undefined or requires a specific convention for empty predictions; a note or alternative
    metric (like ''Empty Output'') would be clearer.'
- id: 619048c70f17
  severity: writing
  text: 'Figure 7: The ''Entity Recovery'' case shows a WER of 14.3% for Mega-ASR,
    yet the text output appears to match the Ground Truth exactly (ignoring capitalization).
    If the WER is non-zero, the text should reflect the specific error (e.g., ''VictorNet''
    vs ''Victor Company''), or the WER should be 0.0%.'
artifact_hash: b76830428db6f31ab0213200b5916231003e882ec498765fb220acf8020a5333
artifact_path: projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/paper/metadata.json
backend: dartmouth
feedback: Vision review of 9 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T03:56:23.603469Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure presents a radar chart comparison, but the radial axis scaling on the left plot is misleading, causing low numerical scores to appear visually high. Additionally, the legend text is partially cropped at the bottom edge.

### Figure 2

Figure 2 is a clear and effective infographic that visually communicates the scale and diversity of the 'Voices-in-the-wild-2M' dataset. The text overlay explicitly lists the 7 domains and 54 hybrid scenarios mentioned in the caption, while the background collage and network diagram illustrate the variety of acoustic degradations.

### Figure 3

Figure 3 presents training curves and a sampling distribution comparison, but the right panel’s unlabeled y-axis and undefined legend terms undermine clarity, and the left panel’s y-axis labeling is inconsistent across subplots.

### Figure 4

The figure is a complex workflow diagram but is rendered useless by a placeholder caption that fails to describe the content or define the numerous symbols and abbreviations used.

### Figure 5

The figure provides a clear visual workflow for the reward mechanism but fails to visually represent the 'DG-WGPO' framework named in the caption, and the mathematical formula within the Word-level Reward box is too blurry to read.

### Figure 6

The figure is a detailed pipeline diagram, but the caption is a placeholder ('Enter Caption'), which is a critical error that prevents the figure from being understood or verified.

### Figure 7

The figure effectively demonstrates the qualitative advantages of Mega-ASR in challenging scenarios. However, the quantitative metrics (WER) contain inconsistencies, specifically the '--' label for Ground Truth and a potential mismatch between the 14.3% WER and the identical text output in the Entity Recovery case.

### Figure 8

Figure 8 is a clear and well-constructed line plot that effectively visualizes the four difficulty mapping functions described in the caption. All axes are properly labeled with units, the legend is distinct, and the curves accurately reflect the textual descriptions of how each function transforms the uniform sample into the severity variable.

### Figure 9

Figure 9 effectively presents five qualitative case studies comparing Qwen3-ASR and Mega-ASR across distinct error modes. The layout is clear, with reference transcripts, model outputs, and specific observations for each example, fully supporting the caption's claims.
