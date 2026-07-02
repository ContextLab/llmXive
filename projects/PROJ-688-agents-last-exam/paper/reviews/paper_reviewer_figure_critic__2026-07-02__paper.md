---
action_items:
- id: ca546006c0fb
  severity: writing
  text: 'Figure 1: The caption references ''Table'' without a number, making it impossible
    to verify the harness-backbone configurations shown in the bubbles.'
- id: a6f6fc5e4e1d
  severity: science
  text: "Figure 1: The legend defines bubble area as proportional to 'Total tokens'\
    \ (100M\u20131000M), but the caption states 'bubble area is proportional to total\
    \ token consumption' without specifying units or scale, creating ambiguity in\
    \ interpretation."
- id: c3bd7a755fe1
  severity: writing
  text: 'Figure 1: Panel (a) x-axis label ''Total API Cost (USD)'' lacks currency
    symbol formatting consistency with scientific convention; consider ''$'' prefix
    or explicit note.'
- id: a88642da2f66
  severity: writing
  text: 'Figure 2: The caption contains a typo ''Point size $$ total task instances
    per cluster'' where a verb (e.g., ''indicates'') is missing between the subject
    and the definition.'
- id: f0b8aca605ab
  severity: writing
  text: 'Figure 2: The legend is missing from the rendered image; the caption defines
    point size but does not define the color mapping for the taxonomy clusters shown
    in the plot.'
- id: 66657e01bf4d
  severity: science
  text: 'Figure 3: The ''Vary Harness (GPT-5.5 fixed)'' group contains ''Codex'',
    ''OpenClaw'', ''ALE-Claw'', ''Cursor'', and ''Droid''. However, the caption states
    the spread is 5.3--6.0pp, while the visual range for this group is ~19% to ~25%
    (a 6pp spread). The ''Vary Harness (Opus 4.7 fixed)'' group shows ''Cursor'',
    ''ALE-Claw'', ''Claude Code'' with a range of ~14.5% to ~19% (a 4.5pp spread).
    The caption claims 5.3-6.0pp for the latter, but the visual data suggests a smaller
    spread. The text ''5.3pp'' and ''6.0pp'' are pl'
- id: eee654b8b9f1
  severity: writing
  text: 'Figure 3: The legend distinguishes ''Harness effect'' (orange) and ''Model
    effect'' (blue), but the x-axis labels are ''Vary Harness (GPT-5.5 fixed)'', ''Vary
    Harness (Opus 4.7 fixed)'', and ''Vary Model (OpenClaw fixed)''. The first two
    groups are both ''Vary Harness'' but use different fixed models, which is not
    reflected in the legend. The legend should clarify that orange represents varying
    harnesses (with different fixed models) and blue represents varying models (with
    a fixed harness).'
- id: 6e3e7a43d1cd
  severity: writing
  text: 'Figure 4: The caption contains a placeholder error: ''Near-Term tier ( task
    instances)'' is missing the count (likely 59, matching the plot title).'
- id: d1cb4497eddb
  severity: writing
  text: 'Figure 4: The x-axis labels (model/harness names) are rotated and densely
    packed, making them difficult to read without zooming.'
- id: edb6d8356b79
  severity: writing
  text: 'Figure 5: The caption contains a placeholder error, reading ''Full-Spectrum
    tier ( task instances)'' with a missing integer count for the number of instances.'
- id: f0833f72590a
  severity: writing
  text: 'Figure 5: The x-axis labels (model/harness combinations) are rotated and
    densely packed, making them difficult to read without significant zooming.'
- id: 7c8812deeb3a
  severity: writing
  text: 'Figure 6: The caption contains a placeholder error: ''Last-Exam tier ( task
    instances)'' is missing the specific count of instances.'
- id: cf3cdca99190
  severity: writing
  text: 'Figure 6: The x-axis labels are rotated and densely packed, making model
    names (e.g., ''OpenClaw / Grok 4.3'') difficult to read.'
- id: d52cec8aa361
  severity: science
  text: 'Figure 6: The y-axis lists task instance names but lacks the color-coded
    domain indicators shown in the legend, forcing reliance on text color which is
    hard to distinguish.'
- id: c8e170634927
  severity: writing
  text: 'Figure 7: The caption contains a broken cross-reference (''appear in Figure
    .'') where the figure number is missing.'
- id: 1a6bf4cc9cc0
  severity: science
  text: 'Figure 7: The ''Visual & Media Arts'' label is positioned in a central overlap
    region, but the associated icons (e.g., Unity, Blender) are scattered across the
    center and right, making the domain boundary ambiguous.'
- id: 596b1412ba5c
  severity: writing
  text: 'Figure 8: The caption describes a linear pipeline, but the diagram includes
    a feedback loop from ''QC Committee Review'' back to ''Expert Task'' (Submission/Editing)
    without a legend or label explaining the iteration logic.'
- id: fa243ba084d7
  severity: writing
  text: 'Figure 8: The text ''Website Display'' and ''Backend Trigger & Email Notified''
    are positioned ambiguously between the pipeline steps and the UI screenshots,
    lacking clear arrows or connectors to indicate their specific role in the workflow.'
- id: 395ff8636ebe
  severity: science
  text: 'Figure 9: The ''Hands'' (Tools) row for CLI-Agents is marked ''Full'', but
    CLI agents typically lack GUI tool interaction; the diagram implies CLI agents
    have full tool capabilities which contradicts the standard definition of CLI vs
    GUI agents.'
- id: 5a0440901f9c
  severity: writing
  text: 'Figure 9: The legend at the bottom right is incomplete; it defines ''Full'',
    ''Limited'', and ''N/A'' symbols, but the ''Limited'' symbol (half-filled circle)
    is not explicitly defined in the text, relying on visual inference.'
- id: c292daff6146
  severity: fatal
  text: 'Figure 10: The caption describes four panels (a, b, c, d), but the rendered
    image displays only a single panel (domain-level mean scores). The figure is incomplete.'
- id: d5c6ba391d42
  severity: science
  text: 'Figure 10: The x-axis label ''Mean score (%)'' is present, but the axis lacks
    tick marks and grid lines, making it difficult to accurately read the specific
    values for each domain.'
- id: dc391aae567c
  severity: science
  text: 'Figure 12: The legend defines orange as ''Unverified'' (expert submissions
    awaiting QC), but the caption states ''All subdomains receive non-zero coverage.''
    The ''Transport. & Safety'' subdomain ''Maritime & Port Operations'' shows only
    a blue bar (13) and no orange bar, contradicting the claim that all subdomains
    have unverified submissions.'
artifact_hash: 326ff13c3b60fc13345363439d3391333425191b488bb3324c7d31083263c3e8
artifact_path: projects/PROJ-688-agents-last-exam/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T03:13:51.464660Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 effectively visualizes performance vs. resource trade-offs with clear axes and legends, but the caption’s incomplete table reference and ambiguous token unit definition reduce reproducibility and precision.

### Figure 2

The figure effectively visualizes the correlation between public subset and full pool pass rates, but the caption contains a grammatical typo and the rendered image lacks a legend to map the bubble colors to the specific taxonomy clusters.

### Figure 3

Figure 3 visually compares the impact of varying harnesses versus varying models on pass rates. However, the caption's stated spreads (5.3--6.0pp) do not accurately match the visual ranges for the 'Vary Harness (Opus 4.7 fixed)' group, and the legend does not fully clarify the different fixed models used in the 'Vary Harness' groups.

### Figure 4

The heatmap effectively visualizes per-task scores across models and instances, but the caption contains a missing number placeholder and the x-axis labels are cluttered.

### Figure 5

The heatmap effectively visualizes performance across tasks and models, but the caption contains a missing number placeholder, and the x-axis labels are too crowded to be easily legible.

### Figure 6

The heatmap effectively visualizes performance across the Last-Exam tier, but the caption contains a missing number placeholder and the dense x-axis labels reduce readability.

### Figure 7

The figure provides a qualitative overview of the software ecosystem but suffers from a missing figure number in the caption and ambiguous spatial grouping for the central 'Visual & Media Arts' domain.

### Figure 8

The figure effectively visualizes the task construction pipeline with clear step labels and supporting UI screenshots, but the feedback loop logic and the specific function of the backend notification text are not explicitly defined in the diagram or caption.

### Figure 9

The figure effectively visualizes the agent taxonomy but contains a potential scientific inaccuracy regarding CLI agent tool capabilities and has a minor legend definition gap.

### Figure 10

The figure is incomplete as it only renders panel (a) despite the caption describing four distinct panels (a-d). Additionally, the x-axis lacks tick marks, hindering precise data interpretation.

### Figure 11

Figure 11 is a clear, high-quality teaser diagram that effectively visualizes the broad taxonomy of professional tasks covered by the 'Agents' Last Exam' benchmark. The central wheel categorizes domains, while surrounding panels provide concrete examples of realistic workflows (e.g., Manufacturing, Game Development) linked to their respective sectors, fully supporting the caption's claim.

### Figure 12

The figure is generally clear and well-structured, but the claim in the caption that 'All subdomains receive non-zero coverage' (referring to the orange QC category) is contradicted by the data shown for 'Maritime & Port Operations', which lacks an orange bar.
