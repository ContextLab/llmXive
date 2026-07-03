---
action_items:
- id: 0ea30aa57e1e
  severity: writing
  text: 'Figure 1: The caption contains a placeholder artifact ''with ,'' and the
    model name ''grayMuonH-1B'' appears to be a raw filename or variable name rather
    than a clean description.'
- id: b30f65d6195d
  severity: science
  text: 'Figure 1: The legend labels ''MuonH'' and ''MuonH w. MPI'' do not explicitly
    identify which line corresponds to the ''router design'' mentioned in the caption,
    making the claimed 0.013 reduction difficult to verify visually.'
- id: 1dc9b44897b5
  severity: science
  text: 'Figure 2: The caption claims the method facilitates ''faster convergence,''
    but the x-axis is ''Tokens'' (compute budget), not ''Wall-clock time'' or ''Steps.''
    Since the curves overlap significantly in the loss plot (a), the claim of faster
    convergence is not supported by the provided axes.'
- id: 42500f56b575
  severity: writing
  text: 'Figure 2: The caption contains a missing variable placeholder (a backslash
    ''\'') before ''facilitates,'' likely referring to the specific router design
    or method name which is absent from the text.'
- id: 347a2042904d
  severity: fatal
  text: 'Figure 3: The caption states ''Load balancing loss for 3B MoE with [missing
    method]'', but the rendered plot shows two distinct lines (''MoE'' and ''MoE w.
    MPI'') without defining what the purple line represents in the text. The caption
    is incomplete and fails to describe the comparison shown.'
- id: 47745b50112c
  severity: science
  text: 'Figure 3: The y-axis scale is extremely narrow (0.016 to 0.017), which visually
    exaggerates the difference between the two curves. While the absolute difference
    is small, the visual presentation may mislead readers regarding the magnitude
    of the improvement in load balancing loss.'
- id: 8f46a5c3eafe
  severity: fatal
  text: 'Figure 4: The caption claims to show ''pretraining collapses'' without Router
    Retraction, but the plot displays ''Accuracy (%)'' on the y-axis, not pretraining
    loss. Furthermore, the ''MPI w.o Retraction'' line (pink) shows high accuracy
    (~53%) and does not collapse, directly contradicting the caption''s claim of instability.'
- id: b6e8933c45ef
  severity: science
  text: 'Figure 4: The x-axis labels (100B, 125B, 150B, 175B, 200B) imply a 200B token
    training run, but the caption specifies this is for a ''3B MoE'' model. This scale
    is inconsistent with the model size described in the caption.'
- id: e1a5d589b0ae
  severity: writing
  text: 'Figure 4: The caption mentions ''Router Retraction'' and ''Power Iteration''
    as key design choices, but the legend labels (''MoE w. MPI'', ''MPI w.o Power-Iter'',
    ''MPI w.o Retraction'') are inconsistent in naming convention and do not clearly
    map to the specific ablation conditions described.'
- id: 4501a0f5943e
  severity: writing
  text: 'Figure 5: The caption contains a placeholder ''\\'' instead of the specific
    method name (e.g., ''MuonH'' or ''MPI'') that the figure legends refer to as ''w.
    MPI'', making the claim ''MoE with \\ achieves...'' unreadable.'
- id: 6d87966221ba
  severity: writing
  text: 'Figure 5: The top subplot legend lists ''AdamW'' and ''AdamW w. MPI'', but
    the caption claims a comparison across ''AdamW, AdamH, Muon''; the top plot should
    likely be labeled ''AdamH'' to match the caption''s description of the three optimizers.'
artifact_hash: 34fabb025335fc2fcf0855d53316dbb275a62eee03c0f1ad1b72c49ea11b1392
artifact_path: projects/PROJ-697-redesign-mixture-of-experts-routers-with/paper/metadata.json
backend: dartmouth
feedback: Vision review of 5 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T10:01:58.623698Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure displays clear convergence curves with error bands, but the caption contains formatting artifacts and the legend fails to explicitly link the plotted lines to the specific 'router design' claim.

### Figure 2

The figure displays loss and accuracy curves but fails to support the 'faster convergence' claim as the x-axis represents tokens rather than time. Additionally, the caption contains a text placeholder error.

### Figure 3

The figure is visually clear but suffers from a critical caption error where the method name is missing, leaving the purple line undefined. Additionally, the y-axis scale is zoomed in significantly, potentially exaggerating the visual impact of the load balancing loss reduction.

### Figure 4

The figure is fundamentally misleading as the data shown (high accuracy for the 'w.o Retraction' condition) directly contradicts the caption's claim of 'pretraining collapses'. Additionally, the token scale on the x-axis appears inconsistent with the 3B model size mentioned in the caption.

### Figure 5

The figure effectively visualizes loss convergence across three optimizers, but the caption contains a broken placeholder ('\\') and the top subplot's legend ('AdamW') contradicts the caption's list of optimizers ('AdamW, AdamH, Muon'), creating confusion about which optimizer is being compared in the top panel.
