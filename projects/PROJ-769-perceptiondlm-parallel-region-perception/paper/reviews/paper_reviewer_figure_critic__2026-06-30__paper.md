---
action_items:
- id: f52f11c91265
  severity: writing
  text: In Figure 1 (teaser2.pdf), sub-captions (b) and (c) lack explicit axis labels
    and units. Panel (b) needs Y-axis 'Tokens Per Second (TPS)' and X-axis 'Number
    of Region Masks'. Panel (c) needs similar definitions. Without these, quantitative
    claims are not visually verifiable.
- id: bf494cd6094e
  severity: writing
  text: Figure 1 (teaser2.pdf) and Figure 2 (arch4.pdf) use color coding for components
    but lack a legend. The text mentions 'different color' highlighting, but no key
    exists. Add a legend or direct labels to ensure legibility for print and accessibility.
- id: d4bfab7f9b9a
  severity: writing
  text: Figure 4 (statics.pdf) in the appendix lacks clear axis labels for mask area/count
    distributions. Ensure all appendix figures have explicit titles, axis labels,
    and units consistent with main figures to support the statistical claims.
- id: 3a0e2111f33b
  severity: writing
  text: Failure case figures (failure_case_*.png) lack specific sub-captions describing
    the error type (e.g., 'Cross-region entanglement'). Add specific captions for
    each sub-figure (a-d) to clearly link visual evidence to the textual analysis.
artifact_hash: c2fe12c2ed011a24b223e04bd3ecaeef100189d2028034fd68b96cae705b806b
artifact_path: projects/PROJ-769-perceptiondlm-parallel-region-perception/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T17:22:26.436900Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The figure presentation in this manuscript requires minor revisions to meet standard scientific visualization practices, specifically regarding axis labeling, legend clarity, and caption specificity.

**Figure 1 (teaser2.pdf):** This is the primary efficiency claim figure. While the visual trend is clear, the sub-panels (b) and (c) are missing explicit axis labels and units. Panel (b) plots "Throughput vs. Region Quantity," but the Y-axis unit (e.g., Tokens Per Second) is not explicitly labeled on the axis line, relying solely on the caption. Panel (c) similarly lacks axis definitions. For a paper claiming "near-linear TPS growth," the Y-axis must explicitly state "TPS" and the X-axis "Number of Masks." Without these, the quantitative comparison is ambiguous.

**Figure 2 (arch4.pdf):** The caption states, "we highlight each component in a different color within the dashed boxes." However, the figure lacks a legend or a color key explaining which color corresponds to "region prompting," "RoI-aligned feature replay," or "structured attention masking." This forces the reader to cross-reference the text constantly. A small legend or direct labeling on the diagram components is necessary for immediate comprehension.

**Appendix Figures (benchmark.pdf, statics.pdf, failure cases):** Figure 4 (statics.pdf) appears to show data distributions but lacks clear axis labels in the provided context. The failure case figures (failure_case_*.png) are grouped under a single generic caption. To effectively support the "Failure Case Analysis" section, each sub-figure (a-d) should have a specific, descriptive caption (e.g., "(a) Cross-region attribute entanglement") rather than relying on the reader to infer the specific error from the image alone.

**General Legibility:** Ensure that all text within the figures (especially in the architecture diagram and failure cases) is large enough to be legible when printed at standard conference paper size. The current reliance on color without a legend is a significant accessibility and clarity issue.
