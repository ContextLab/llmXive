---
action_items:
- id: caab11c7cd4c
  severity: fatal
  text: "Figure category_distribution.pdf has placeholder caption 'Enter Caption'\
    \ \u2014 must be replaced with descriptive text explaining the taxonomy and data\
    \ distribution."
- id: 30e77073cd96
  severity: writing
  text: "Case study figures (scenario1_home-4.pdf, scenario2_office-2.pdf) have minimal\
    \ captions that do not explain what is shown or why it matters \u2014 expand to\
    \ include key observations."
- id: dc80de8e9247
  severity: writing
  text: Heatmap figure (fig3_cross_task_heatmaps.pdf) and continuity ratio figure
    (cross_task_continuity.pdf) must include explicit axis labels and color legends
    for print legibility.
- id: 14c8cc30eb93
  severity: writing
  text: "Figure numbering is inconsistent (fig3_cross_task_heatmaps.pdf labeled as\
    \ 'fig3' but appears as Figure 7 in paper) \u2014 ensure all captions match their\
    \ in-text reference numbers."
- id: 604c8ce110c1
  severity: writing
  text: "PNG figure dataset.png (5.3MB) may have resolution issues at print scale\
    \ \u2014 verify 300+ DPI or convert to vector format."
artifact_hash: d722b827ffcc42ef33cad3308518a181a01c5d135cbbac51efaf0289e64033d0
artifact_path: projects/PROJ-666-https-arxiv-org-abs-2606-05121/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-12T11:07:11.381795Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: full_revision
---

The paper contains 13 figures spanning overview diagrams, framework schematics, dataset statistics, analysis plots, and case studies. Several critical figure quality issues must be addressed before publication.

**Fatal Issue — Figure 12 (category_distribution.pdf):** The caption literally reads "Enter Caption" — this placeholder text was never replaced. This figure appears in Appendix B (Proactive-Sound-Bench) and must have a proper caption describing the taxonomy rationale and category coverage.

**Caption Quality:** Case study figures (scenario1_home-4.pdf, scenario2_office-2.pdf) have minimal captions ("Case study: Home" / "Case study: Office") that fail to explain what the visual shows, what key insight it demonstrates, or why it supports the paper's claims. Expand these to 2-3 sentences minimum.

**Axis Labels and Legends:** The continuity ratio figure (cross_task_continuity.pdf) and head importance heatmaps (fig3_cross_task_heatmaps.pdf) should include explicit axis labels (layer/head indices, task names) and color legends. Without these, the figures are not interpretable at print scale.

**Figure Numbering Consistency:** Multiple figures reference internal file names that don't match their paper numbering (e.g., "fig3_cross_task_heatmaps" appears as Figure 7 in the manuscript). Ensure all in-text figure references match their actual caption numbers.

**Resolution Concerns:** The dataset.png figure (5.3MB PNG) may have resolution issues when printed in double-column format. Verify 300+ DPI or convert to vector format (PDF/SVG) for scalability.

**Accessibility:** LaTeX figures lack alt text. Consider adding descriptive alt text for screen readers where figures convey critical information (especially the framework diagram and taxonomy figure).

**Redundancy:** Three case study figures (figure-casestudy.pdf, scenario1_home-4.pdf, scenario2_office-2.pdf) could be consolidated into a single multi-panel figure with unified captions to reduce page count and improve coherence.
