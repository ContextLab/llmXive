---
action_items:
- id: 38113ba88ec1
  severity: writing
  text: 'Figure 1: The caption states the drafter is fed ''activations and KV cache'',
    but the diagram only explicitly labels ''Last Prefilled Global Layer'' and ''Last
    Prefilled Local Layer'' as inputs; the specific ''KV cache'' input is not visually
    labeled.'
- id: b143335bb756
  severity: writing
  text: 'Figure 1: The input labels at the bottom (''t1 / p1'', ''t2 / p1'', ''t3
    / p1'') are undefined in the caption, making it unclear what ''p1'' represents
    in the context of the autoregressive process.'
- id: 8cd7cec44d8c
  severity: science
  text: 'Figure 2: The caption claims the image is resized to ''2 x 4 pooled patches'',
    but the visual grid clearly displays 3 rows and 3 columns (9 patches). This contradicts
    the text description of the pooling layout.'
- id: 769a17789a55
  severity: science
  text: 'Figure 2: The caption states the image is resized to ''2 x 4 pooled patches
    (each of size 48px^2)'', but the visual grid shows 9 patches, and the math for
    a 96x192 image with pooling kernel 3 and patch size 16 does not yield 48px^2 pooled
    patches in a 2x4 arrangement.'
- id: b99aa0dc29b3
  severity: writing
  text: 'Figure 2: The caption contains a typo ''pooled $33$'' which appears to be
    a formatting error or missing text, making the sentence ''the vision encoder representations
    are pooled $33$'' illegible.'
artifact_hash: 55958703b13d89f6f09bca63229fc87b11f6b4b47923a438bff5af617f4f5f53
artifact_path: projects/PROJ-1018-gemma-4-technical-report/paper/metadata.json
backend: dartmouth
feedback: Vision review of 2 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-09T04:28:13.761577Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure effectively visualizes the MTP drafter architecture and its connection to the main model, but the caption's mention of 'KV cache' is not explicitly labeled in the diagram, and the input variable 'p1' is undefined.

### Figure 2

The figure illustrates image resizing but contains a significant contradiction between the visual grid (3x3) and the caption's description (2x4). Additionally, the caption includes a formatting error ('pooled $33$') that obscures the technical explanation.
