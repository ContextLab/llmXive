# Revision Specification: Paper Science Revision — PROJ-796-in-context-world-modeling-for-robotic-co round 1

**Generated**: 2026-06-28T06:00:34.640716+00:00
**Kind**: paper_science
**Project**: PROJ-796-in-context-world-modeling-for-robotic-co
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[b46427abb4a9] (severity: writing)** Correct performance improvement percentages in Simulation Results (e.g., 13.0% vs 5.2% in Tab. unseen) to match table data.
- **[f5933e231d5b] (severity: writing)** Resolve viewpoint count discrepancy: Text claims 15 viewpoints, Appendix lists 14 angles (8 ID + 6 OOD).
- **[86e82b7acdd4] (severity: writing)** Clarify morphological generalization margin claim (+60%) which contradicts specific data points (5.6 vs 14.4).
- **[375bad1d4939] (severity: writing)** The \checkdata metadata in paper.tex points to 'MOSS-Transcribe-Diarize' (a different project). Update these links to point to the ICWM code repository or remove them if code is not yet public.
- **[f40289c52672] (severity: writing)** Add a direct link to the ICWM code repository (e.g., GitHub/HuggingFace) in the Abstract or Introduction to ensure reproducibility of the method.
- **[ddce66379a85] (severity: writing)** Clarify the technical implementation of context prepending in Section 4.1 (e.g., tokenization of interaction clips, KV cache usage) to aid reproduction.
- **[8df90fc8e308] (severity: science)** Provide a repository link or data release statement for the custom real-robot dataset collected in Appendix app:real to enable reproducibility.
- **[5b4b3ec01348] (severity: writing)** Add explicit license information for all datasets (LIBERO, real-robot) and pretrained models (Qwen2.5-VL, FAST) used in the pipeline.
- **[61b27dcfc07a] (severity: writing)** Correct the invalid arXiv ID (2606.26025) in the paper metadata to ensure valid provenance tracking.
- **[5e845f2d3151] (severity: writing)** Remove template residue (e.g., commented-out MOSS demo links) from the preamble to maintain manuscript hygiene.
- **[d61656784e2b] (severity: writing)** Resolution and File Size (Critical) Several quantitative result figures have suspiciously small file sizes, indicating potential quality issues:
- **[77563b225e74] (severity: writing)** imgs/libero2.pdf (Fig. 4, Simulation Results): 26KB.
- **[67389468a3ef] (severity: writing)** imgs/real.pdf (Fig. 5, Real-world Results): 20KB.
- **[9f0bfd60b6eb] (severity: writing)** imgs/time.pdf (Fig. 10, Latency): 15KB. These sizes suggest the figures may be low-resolution raster images embedded as PDFs or contain minimal vector data. For a paper submitted to a venue requiring print quality, axis labels, tick marks, and legend text in these plots must be crisp. I recommend regenerating these plots as high-resolution vector graphics (PDF or EPS) to ensure all text remains legible when scaled.
- **[9700acd7102c] (severity: writing)** Labeling and Naming Conventions
- **[26026a8fd9dd] (severity: writing)** Placeholder Label: The figure imgs/robot2.pdf (Sec. Experiments) uses the label \label{fig:placeholder}. This is unprofessional for a final manuscript. Please rename to a descriptive identifier (e.g., \label{fig:real_tasks}).
- **[83ba0840f993] (severity: writing)** Consistency: Most figures use descriptive labels (fig:intro, fig:methods, fig:tsne), which is good practice.
- **[a576e01100e5] (severity: writing)** imgs/set2.png (Fig. 7, t-SNE) is provided as a PNG. While acceptable for raster images, line plots and scatter plots (like t-SNE) should ideally be vector-based (PDF/EPS) to prevent pixelation during printing or zooming.
- **[8fa5a50d60e8] (severity: writing)** None of the \includegraphics commands include alt text attributes. For accessibility compliance (e.g., screen readers), please add descriptive alt text to all figures (e.g., alt="Bar chart comparing success rates of ICWM vs baselines across 6 viewpoints").
- **[6f952f25059a] (severity: writing)** The caption for imgs/time.pdf reads "Comparison of inference time across different setting." This should be corrected to "settings" (plural). Recommendations
- **[7f918522da92] (severity: writing)** Regenerate all quantitative plots (libero2, real, time, gen3-3) as vector graphics.
- **[83bf0e91d735] (severity: writing)** Verify that all axis labels, legends, and tick marks are large enough to be read at 100% zoom and in print.
- **[201128737c25] (severity: writing)** Update the fig:placeholder label.
- **[25ac6a599b7a] (severity: writing)** Add alt text to all figures.
- **[ac0b34f3c2c7] (severity: writing)** Correct the minor grammatical error in the latency figure caption. Addressing these issues will ensure the figures meet the visual standards expected for publication.
- **[8d873494261b] (severity: writing)** Define 'POMDP' at first use in Section 3.1. Spell out 'Partially Observable Markov Decision Process' for non-specialist readers.
- **[4cc98da12203] (severity: writing)** Define 'OOD' (Out-of-Domain) in Section 4.1 before using the acronym. Currently defined only in Appendix A.1.
- **[4f38db3dd9f7] (severity: writing)** Expand 'KV caching' to 'Key-Value caching' in Section 4.4. This is implementation jargon that may confuse readers unfamiliar with Transformer internals.
- **[5451d2a3a66d] (severity: writing)** Simplify or define 'd-separation' and 'collider' in Appendix A.1 proof. These are specific probabilistic graphical model terms not standard in all ML subfields.
- **[fdde98ec29d3] (severity: writing)** Replace 'action chunk' with 'action sequence' or define it in Section 3.1 for clarity.
- **[d7605e1e5191] (severity: science)** In Section 'Simulation Results' (040-exp.tex), the text claims ICWM improves OOD success rate by 13.0% over Multi-View BC. However, Table 'tab: unseen' (appendix.tex) shows MV Avg=19.8% and ICWM Avg=25.0%, a 5.2% absolute difference. This numerical inconsistency undermines the conclusion that the data supports the stated claim. Please align the text with the table data or clarify the metric used.
- **[2115db5e0481] (severity: writing)** The paper makes strong claims about generalization and system identification that are not fully supported by the provided data. Specifically, Section 4.2 claims a 9.5% improvement over Explicit Configuration (EXP), but Table tab: unseen in the Appendix shows an average absolute improvement of only ~3% (33.75% vs 30.8% average). While this may represent a 9.5% *relative* improvement, the phrasing "improving the OOD success rate by 9.5%" is ambiguous and risks misleading readers into expecting a l
- **[583baae9b528] (severity: writing)** Explicitly detail safety mechanisms (e.g., emergency stops, collision detection) for the 'Active Probing Phase' in real-world deployment to prevent physical harm.
- **[7558efe124c6] (severity: writing)** Clarify whether informed consent or IRB approval was obtained for the human teleoperation data collection described in Appendix B.1.
- **[edf8768b253e] (severity: writing)** Discuss safety fallback protocols for scenarios where system identification fails (e.g., 'false context' in Table 2) to avoid unsafe actions.
- **[f789aa6438c7] (severity: science)** Report standard deviations or 95% confidence intervals for all success rate metrics in Tables 1, 2, and 3. Single-point estimates without variance prevent statistical significance assessment.
- **[f9b3763d0ab4] (severity: science)** Specify the number of random seeds used for model training and report mean/std performance across seeds. Single-seed results are insufficient to rule out initialization variance.
- **[1d1a6b09bd1e] (severity: science)** Clarify the total episode count discrepancy in Section 4.1 (500x15x4) versus Appendix A.1 (14 angles). Inconsistent sample size reporting undermines reproducibility.
- **[d3af76d9b3e2] (severity: science)** Report standard deviations or 95% confidence intervals for all success rate metrics in Tables 1-3 and Figures 3-5. Point estimates alone are insufficient to claim 'significant' improvements.
- **[7627ceaa4b6a] (severity: science)** Explicitly state the number of random seeds used for training and evaluation. The current text implies single-run results, which undermines reproducibility and statistical validity.
- **[1b06fbd12871] (severity: science)** Perform and report statistical significance tests (e.g., bootstrap or paired t-tests) for key comparisons (ICWM vs. MV) to substantiate the claim of 'significant outperformance' in the Abstract and Section 4.2.
- **[1cf99003c2de] (severity: writing)** Clarify the total episode count calculation in Section 4.1. The expression '$500 \times 15 \times 4$' is ambiguous (30,000 total? per suite?). Define the denominator for success rates clearly.
- **[f4e3d135f2da] (severity: writing)** The manuscript’s overall structure (sections, subsections, figures, tables) follows a conventional hierarchy, but several formatting details need attention to meet the journal’s style guidelines. Heading hierarchy – The use of \section, \subsection, and \subsubsection is consistent, but the custom \autoref names (e.g., \sectionautorefname) are re‑defined in the preamble. This is acceptable, yet the definitions should be placed *after* loading cleveref to avoid warnings. Figure placement – Most f
- **[396c4a34e60b] (severity: writing)** The abstract contains several long, comma‑spliced sentences that hinder readability (e.g., the first two sentences). Break them into shorter sentences and clarify the role of the context window.
- **[cf7e635c11c3] (severity: writing)** In the Introduction (Section 1), the phrase “the operator’s first instinct is not to attempt the task directly, but to explore” is awkward; rephrase for smoother flow.
- **[00ab15b96fd9] (severity: writing)** Figure 1 caption repeats the term “system configurations” and uses the phrase “standard VLA models often fail … due to fixed observation‑action assumptions.” Consider simplifying to improve clarity.
- **[ee170768b394] (severity: writing)** Throughout the paper, the notation $\psi$ for system configuration is introduced without a concise definition; add a brief explanatory sentence when first used (e.g., “where $\psi$ denotes camera viewpoint, robot morphology, etc.”).
- **[aa0c44610bc6] (severity: writing)** The term “task‑agnostic random movements” appears repeatedly (e.g., Sections 3.2, 4.2). Vary the wording to avoid redundancy and improve readability.
- **[605a6a57826b] (severity: writing)** In the Method section (Section 3), the equation $a_t \sim \pi_	heta\left(a_t \mid  si(\mathcal{T}), o_t, light)$ repeats the variable $a_t$ on both sides; rewrite as $a_t \sim \pi_	hetaigl(\cdotigr)$ or clarify the sampling notation.
- **[ca890a85df5c] (severity: writing)** The tables (e.g., Table 1 and Table 2) contain inconsistent formatting of percentages (some with “%”, some without) and mixed use of bold/colored cells; standardize the style for a professional appearance.
- **[38e9721b1135] (severity: writing)** Several sections contain stray LaTeX commands that render as raw text in the PDF, such as “	extit{system identification}” and “	extit{task‑agnostic}”. Ensure proper compilation or replace with plain italics.
- **[bf158a4f120c] (severity: writing)** The Conclusion (Section 6) repeats the same three‑sentence structure used earlier; vary sentence length and avoid verbatim repetition of earlier phrasing.
- **[7e88e218d1ce] (severity: writing)** The bibliography entries lack consistent punctuation (e.g., missing periods after journal names). Apply a uniform citation style.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 53 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
