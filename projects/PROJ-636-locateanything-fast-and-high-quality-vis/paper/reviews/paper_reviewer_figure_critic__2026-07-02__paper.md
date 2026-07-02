---
action_items:
- id: de4a808518dc
  severity: writing
  text: 'Figure 1: The caption contains a grammatical error and likely typo: ''predicts
    points representing geometric units (, bounding box corners)'' includes a dangling
    comma and missing word before the parenthesis.'
- id: 210d065d36e0
  severity: writing
  text: 'Figure 1: The caption states ''coordinate tokens in the bottom panel are
    rendered at high resolution to ensure legibility at print scale,'' but the bottom
    panel is a schematic diagram, not a print-scale rendering of the actual model
    output.'
- id: 8a4fd240a36b
  severity: science
  text: 'Figure 2: The ''Generic Multi-Token Prediction'' row shows a sequence of
    tokens (e.g., <911>, <832>) that are not explicitly defined as coordinate values
    in the caption, creating ambiguity about whether they represent coordinates or
    other data. The caption mentions ''irregular distributions'' but the visual representation
    does not clearly illustrate this concept.'
- id: 6594f327c9ca
  severity: writing
  text: 'Figure 2: The scissors icons and warning symbols lack explicit definitions
    in the caption or legend, making their meaning unclear to readers unfamiliar with
    the context.'
- id: ae153b7aaea2
  severity: science
  text: 'Figure 4: The ''Spatial Ambiguity'' panel shows the model discarding the
    erroneous block ''<121>'' and reverting to NTP to predict ''<647>'', yet the diagram
    visually depicts the model *accepting* the erroneous block ''<121>'' (highlighted
    with a cursor icon) before the correction arrow appears. This contradicts the
    caption''s claim that the model ''discards the erroneous block'' and misrepresents
    the re-decoding mechanism.'
- id: 4eb2a3f5acd6
  severity: writing
  text: 'Figure 4: The legend in the top-right corner (''Correct''/''Wrong'') is not
    explicitly referenced in the caption or figure labels, making it ambiguous whether
    the red boxes represent ''Wrong'' predictions or simply ''Format Irregularity''/''Spatial
    Ambiguity'' states.'
- id: a9e0556b68ba
  severity: science
  text: 'Figure 5: The bottom panel''s ''Detection'' category lists ''NuImages (382.1K)''
    and ''MOT17DET (5.3K)'', but the pie chart for ''LocateAnything-Data-Queries''
    (138M) shows Detection at 66.9% (93M). The sum of the listed datasets (93M) matches
    the total, but the breakdown includes datasets like ''NuImages'' which are typically
    video-based, raising questions about the ''unique images'' count in the rightmost
    pie chart (12M) versus the query count.'
- id: b9cdfcff72d1
  severity: writing
  text: 'Figure 5: The legend for ''Pointing'' (3M, 2.2%) is cut off at the bottom
    of the image, making it impossible to see the full list of contributing datasets
    (only ''Object365'', ''OpenImages'', ''PixmoPoints'', ''RoboAfford'' are visible,
    but the row is truncated).'
- id: a584ed322f61
  severity: writing
  text: 'Figure 5: The legend row for ''Pointing'' is partially cut off at the bottom
    edge of the image, truncating the list of source datasets.'
- id: 5e75c86faa43
  severity: science
  text: 'Figure 5: The ''LocateAnything-Data-Images'' pie chart indicates 12M unique
    images, yet the ''Detection'' query breakdown lists datasets like NuImages (382.1K)
    and MOT17DET (5.3K) which are video-centric; the caption does not clarify how
    video frames are aggregated into ''unique images'' or if the 12M count excludes
    these sources.'
- id: 24efe7a584b8
  severity: science
  text: 'Figure 6: The right panel''s legend defines ''Textual (BPS)'', ''Quantized
    (BPS)'', and ''Parallel (BPS)'' as line plots, but the chart only displays lines
    for ''Textual'' and ''Quantized''. The ''Parallel'' throughput line is missing,
    despite the caption claiming a comparison of all three methods.'
- id: f3364867b97a
  severity: writing
  text: 'Figure 6: The right panel''s right y-axis label reads ''Throughput+, BPS
    (Box per Second)''. The ''+'' symbol appears to be a typo or rendering artifact
    and should be removed for clarity.'
- id: b7e967bad7c8
  severity: writing
  text: 'Figure 7: The caption lists four query categories (MyRedattribute, MyBluepart,
    MyOrangereasoning, MyGreenspatial) corresponding to the box colors, but the figure
    lacks a visual legend or key to map these specific names to the colors, forcing
    the reader to guess the mapping.'
- id: 1613ee6617af
  severity: writing
  text: 'Figure 7: The text labels below each image (e.g., ''yellow leaves scattered
    among the purple leaves'') are not explicitly defined as the ''free-form textual
    queries'' mentioned in the caption, creating ambiguity about whether these are
    the inputs or just descriptions.'
- id: 2113b83d74b9
  severity: writing
  text: 'Figure 8: The caption text is truncated at the end (''produce bo''), cutting
    off the description of the final output (likely ''bounding boxes'').'
- id: 67ffbacf5fb3
  severity: writing
  text: 'Figure 8: The top-left label contains a typo, spelling ''Category'' as ''Categroy''.'
- id: d68e014e1b83
  severity: writing
  text: 'Figure 8: The bottom-middle query box contains a typo, spelling ''center''
    as ''centerx''.'
- id: 25e5adf43226
  severity: science
  text: 'Figure 9: The legend defines six task categories (Detection, GUI, Referring,
    OCR, Layout, Pointing), but the x-axis groups (e.g., 10-20, 20-30) show missing
    bars for several categories (e.g., GUI, Layout, Pointing) without explanation
    in the caption or visual indication (e.g., zero-height bars) of their absence.'
- id: 66fabf8605e3
  severity: writing
  text: 'Figure 9: The x-axis label ''Bbox/Point Count'' contradicts the caption''s
    description (''number of targets per query''); clarify whether the axis represents
    targets, boxes, or points to ensure consistency.'
- id: b215ec5301b5
  severity: science
  text: 'Figure 10: The ''LocateAnything'' column (right) shows a failure in the third
    row (trees) where the model produces fragmented, overlapping boxes for ''bare
    trees'' instead of a single coherent region, contradicting the caption''s claim
    of ''superior compositional grounding capabilities''.'
- id: c2f361bc7b7d
  severity: writing
  text: 'Figure 10: The text labels inside the bounding boxes (e.g., ''black helmet
    with TCU logo'', ''man wearing glasses'') are rendered at a resolution that makes
    them illegible in the provided image, hindering verification of the specific queries
    being tested.'
- id: 233d4ac4de20
  severity: writing
  text: 'Figure 11: The rendered image displays a ''Dense Object Detection'' title
    and a ''Ground Truth'' column, but the caption describes it as a ''Qualitative
    comparison on Dense Object Detection (DOD)'' without explicitly mentioning the
    inclusion of ground truth labels or the specific column layout.'
- id: 5867f82e4860
  severity: science
  text: 'Figure 11: The ''Ground Truth'' column shows red bounding boxes, but the
    caption does not define this color coding, potentially causing confusion with
    the ''LocateAnything'' column which uses blue boxes.'
- id: 6238d0c42e46
  severity: writing
  text: 'Figure 12: The column headers ''Qwen3-VL'', ''Rex-Omni'', and ''LocateAnything''
    are not defined in the caption; the caption only mentions ''baseline models''
    without specifying which are which.'
- id: 106dec804ca8
  severity: science
  text: 'Figure 12: The ''Ground Truth'' column displays bounding boxes that are not
    perfectly tight around text elements (e.g., the ''GURGEL'' logo boxes include
    significant whitespace), which contradicts the caption''s claim that LocateAnything
    yields ''tightly bounded boxes'' compared to baselines.'
artifact_hash: c8578cab24ae10f85328a488241d9cfe1b5d4266743783cf5e0239d549de8c29
artifact_path: projects/PROJ-636-locateanything-fast-and-high-quality-vis/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T12:28:33.240842Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 effectively illustrates the paper's versatile tasks and decoding paradigms. However, the caption contains a grammatical error with a dangling comma and a confusing note regarding the resolution of the schematic diagram.

### Figure 2

Figure 2 effectively contrasts three token decoding methods visually, but the caption does not fully explain the meaning of certain symbols (scissors, warnings) or clarify what the token sequences represent, potentially confusing readers.

### Figure 3

Figure 3 effectively illustrates the model architecture and the block-based output representation described in the caption. The diagram clearly maps the input processing through the Moon-ViT and Qwen2.5 components to the specific structured output blocks (Semantic, Box, Negative, End), with all labels and flow directions being legible and consistent with the text.

### Figure 4

The figure illustrates the re-decoding process but contains a visual contradiction in the 'Spatial Ambiguity' panel where an erroneous token appears to be accepted before correction, conflicting with the caption's description of discarding errors. Additionally, the legend's specific role in the diagram is not clearly defined.

### Figure 5

Figure 5 effectively visualizes the dataset composition with clear pie charts and a detailed legend, but the bottom of the legend is cut off, obscuring part of the 'Pointing' category breakdown, and there is a potential inconsistency between the 'unique images' count and the dataset sources listed for detection queries.
issues:
  - severity: writing
    text:

### Figure 6

The figure effectively compares box ordering strategies and decoding speeds, but the right panel is incomplete as it fails to plot the 'Parallel' throughput line defined in the legend, and the right y-axis label contains a likely typo.

### Figure 7

The figure effectively demonstrates the model's robustness across diverse scenes and object counts, but it lacks a visual legend to map the box colors to the specific query categories listed in the caption, and the relationship between the bottom text labels and the 'free-form queries' is not explicitly clarified.

### Figure 8

The figure effectively illustrates the data engine workflow with clear visual steps, but the caption is truncated at the end, and there are minor typos in the labels ('Categroy') and generated text ('centerx').

### Figure 9

Figure 9 presents a log-scale distribution of query counts by target/box count but suffers from a mismatch between the x-axis label and caption, and unexplained missing data bars for certain task categories in higher count ranges.

### Figure 10

The figure provides a visual comparison of three models on referring expression tasks, but the text labels are too small to read, and the 'LocateAnything' model exhibits a clear failure in the third row that contradicts the caption's claim of superior performance.

### Figure 11

The figure effectively demonstrates the model's performance on dense objects compared to baselines, but the caption lacks explicit reference to the 'Ground Truth' column and the color coding scheme used for the different models.

### Figure 12

The figure effectively demonstrates the qualitative differences in OCR performance between models, but the column headers are not explicitly defined in the caption, and the ground truth boxes appear looser than the claimed 'tight' localization of the proposed method.
