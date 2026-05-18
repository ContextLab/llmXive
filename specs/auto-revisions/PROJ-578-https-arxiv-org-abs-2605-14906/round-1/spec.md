# Revision Specification: Paper Science Revision — PROJ-578-https-arxiv-org-abs-2605-14906 round 1

**Generated**: 2026-05-18T15:49:37.626154+00:00
**Kind**: paper_science
**Project**: PROJ-578-https-arxiv-org-abs-2605-14906
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[a46d18f9a8b0] (severity: writing)** Provide verification_status for all citations in state/citations/PROJ-578-https-arxiv-org-abs-2605-14906.yaml to meet accept criteria.
- **[b07b11177f19] (severity: writing)** Ensure full LaTeX source is available for compilation check; current input is truncated.
- **[6d7001908d74] (severity: writing)** Correct the claim that LoCoMo retains visual modalities; the cited work is text-only. Update Section 1 and Section 2 to accurately reflect LoCoMo's text-only nature.
- **[ae329aa3f800] (severity: writing)** Verify that specific model versions (e.g., GPT-5.4, Gemini-3.1-Pro) are explicitly supported by the cited system cards to ensure accurate attribution.
- **[81d2f10c8309] (severity: writing)** Provide the actual source code repository (e.g., evaluation harness, data construction scripts) for review. The current input contains only the manuscript LaTeX and bibliography, preventing assessment of modularity, testing, or dependency hygiene.
- **[96b6f896d1b7] (severity: writing)** Include a requirements.txt or environment specification file to verify dependency hygiene and reproducibility from scratch.
- **[775e28f24d89] (severity: writing)** Explicitly list the frozen version tag names (e.g., v1.0) for the HuggingFace/GitHub releases in the Reproducibility Statement to ensure precise reproducibility.
- **[2626e68c64a9] (severity: science)** Clarify the legal basis for redistributing third-party images under 'original source-site licenses' and provide a mapping of known licenses (e.g., CC-BY, Unsplash) for the 4,695 images to prevent downstream copyright infringement.
- **[dd6a09a52ef8] (severity: writing)** Figure 2 (per_type_heatmap) uses a green colormap. This may be inaccessible to colorblind readers. Replace with a colorblind-safe palette (e.g., Viridis or Cividis) to ensure legibility.
- **[851602e25ca2] (severity: writing)** Appendix Figure (wrong_answer_pie.pdf) uses a pie chart for error distribution. Pie charts are generally less accurate for comparing proportions than bar charts. Consider converting to a grouped or stacked bar chart.
- **[1c436788e78b] (severity: writing)** Figure 1 (pipeline.pdf) caption is minimal ('construction pipeline'). Expand to briefly describe the four visual components (session simulation, question construction, etc.) to improve accessibility and standalone readability.
- **[b35c181f9e48] (severity: writing)** Table 1 embeds a donut chart (composition_donut.pdf). This consumes significant space and may reduce text legibility. Consider moving the distribution data to a bar chart in the main text or appendix to free up table space.
- **[d1453c5c2a75] (severity: writing)** Define acronyms like RAG, LoRA, and RL at their first occurrence in the main text to aid non-specialist readers.
- **[31975288de5e] (severity: writing)** Simplify technical phrases such as "lossy cross-modality compression at storage time" to plain English equivalents.
- **[542eda010dc1] (severity: writing)** Reduce acronym density in Section 4 by spelling out memory ability names (IE, MSR, etc.) in the first paragraph.
- **[1338ec98e2a4] (severity: science)** Temper the claim in the Conclusion that visual-evidence retention is the 'principal bottleneck' to acknowledge the reasoning bottleneck in MSR, which caps system performance below 30%.
- **[569c458879b3] (severity: writing)** Clarify the description of memory agents in Section 5.2 to distinguish between multimodal pipelines (embedding compression) and text-only pipelines (captioning), as the latter do not compress visual information.
- **[20a0f903d938] (severity: science)** In Section 4.2 (Main Results), explicitly qualify the comparison between LVLMs (n=789) and memory agents (n=195). While stratified sampling is used, the smaller agent sample size reduces statistical power for direct performance claims at specific context lengths.
- **[6faacd5259c9] (severity: writing)** In Section 3.4 (Cross-modality Validation), clarify that the image-ablation evidence (Table 2) relies on only two proprietary models (GPT-5.4, Gemini-3.1-Pro). Generalize the claim that 'solving MemLens requires visual evidence' to reflect this model-specific evidence.
- **[690139a8582c] (severity: writing)** Figure 1 caption (Section 4.3) states 'Bands: 95% CI' without specifying the calculation method (e.g., bootstrap, standard error). Explicitly state the method used for the LVLM average bands to ensure reproducibility.
- **[6b29fb06c7be] (severity: writing)** Appendix C, paragraph 'Direct-LVLM overlay on the 195-subset': Report 'p < 10^{-1}' for Spearman correlation. This notation is non-standard and implies weak significance. Verify the exact p-value and report standard notation (e.g., p < 0.05) if significant.
- **[5d2d3c0320b7] (severity: science)** Section 4.2 compares 27 LVLMs and 7 agents across multiple metrics. If claims of 'significant' differences are made, clarify if multiple-comparison corrections (e.g., Bonferroni, FDR) were applied to avoid Type I errors.
- **[ab42d5fa45fa] (severity: writing)** Add \usepackage{tabularray} to preamble or replace 'longtblr' environment with 'longtable'/'tabularx' to prevent compilation errors (Line 850).
- **[36b7026dfac8] (severity: writing)** Verify 'promptbox' environment definition exists in llmxive.cls or define it explicitly in preamble to ensure build stability (Line 1190+).
- **[f0b19b85d85a] (severity: writing)** Standardize citation commands to use \citep consistently for parenthetical citations instead of mixing \cite and \citep (Lines 105-106).
- **[25d28a5efb85] (severity: writing)** Inconsistent number formatting between main text (e.g., '7 memory-augmented agents') and Appendix (e.g., 'seven memory-augmented agent systems').
- **[4eda72a57331] (severity: writing)** Inconsistent hyphenation in compound adjectives (e.g., 'RL-finetuned' vs 'RL-fine-tuned', 'BLIP-2 generated' vs 'BLIP-2-generated').
- **[72142f3c532f] (severity: writing)** Subject-verb agreement error in Reproducibility Statement ('The 789-question benchmark... are publicly released' should be 'is').
- **[7d5df57fa32a] (severity: writing)** Remove editorial LaTeX comments (e.g., '% [motivation + methods]') from the source file for publication readiness.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 29 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
