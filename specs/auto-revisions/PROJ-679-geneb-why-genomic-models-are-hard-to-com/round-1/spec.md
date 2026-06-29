# Revision Specification: Paper Science Revision — PROJ-679-geneb-why-genomic-models-are-hard-to-com round 1

**Generated**: 2026-06-29T02:55:26.653113+00:00
**Kind**: paper_science
**Project**: PROJ-679-geneb-why-genomic-models-are-hard-to-com
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[fe0a240b8f3f] (severity: writing)** Add a Code and Data Availability section with a link to the GENEB evaluation repository to enable reproducibility.
- **[04522704c0ba] (severity: science)** Include a requirements.txt or environment.yml file in the repository to ensure dependency hygiene.
- **[57325591d8c0] (severity: writing)** The manuscript does not specify a license for the GENEB benchmark data or code (Section: Limitations/Appendix). Please add a license statement (e.g., MIT, CC-BY) to ensure reuse.
- **[2c9a323da90f] (severity: writing)** The arXiv ID `2606.04525` in the metadata corresponds to a future date (June 2026). Please verify and correct the submission ID for provenance accuracy.
- **[83f402c6fb80] (severity: science)** Appendix `app:excluded_models` notes 25% of models excluded due to 'Private weights' or 'Broken code'. Please discuss how this selection bias impacts the benchmark's representativeness of the field.
- **[8229a08b0268] (severity: writing)** Task sources (NT, GUE, GB) are cited by name but lack specific versioned URLs or DOIs in `tab:task_groups`. Please provide persistent links to the exact dataset versions used.
- **[5acec32c2436] (severity: writing)** Figure 1 (chaotic_models.png) lacks a legend explaining what node colors or edge styles represent; add a concise legend and ensure the caption explicitly defines nodes = models and edges = explicit baselines.
- **[cb5a9c99ab80] (severity: writing)** Several heatmaps (e.g., Fig 3 main_hitmap.png, Fig 4 category_summary.png, Fig 6 high‑variance tasks) use a red‑to‑green color map without a color‑blind‑safe palette; switch to a palette such as viridis or cividis and include a color bar with numeric MCC values.
- **[cedd1dc62fa4] (severity: writing)** Axis labels and units are missing or ambiguous on many plots (e.g., Fig 2 image_per_size_v2.png lacks a label for the x‑axis ‘Parameter count (M)’ and y‑axis ‘Macro‑MCC’); add clear axis titles with units where applicable.
- **[54db47fd86bb] (severity: writing)** Font sizes in heatmaps and line plots are too small to be legible when printed (e.g., model names and task labels in Fig 3 and Fig 5 are cramped); increase label font size and consider rotating tick labels for readability.
- **[400597a47fb8] (severity: writing)** Captions for multi‑panel figures (e.g., Fig 6 high‑variance tasks) do not describe each panel (A) and (B) in sufficient detail; expand captions to serve as alt text for accessibility.
- **[03068ba1bc21] (severity: writing)** Figure 5 (few‑shot performance degradation) plots MCC values for 40 models but does not include a legend indicating which line corresponds to which model; add a legend or annotate key models directly on the plot.
- **[8d95ab84a1cb] (severity: writing)** Some figures are stored as compressed PNGs with noticeable artifacts (e.g., heatmap images in the zip archive); provide high‑resolution vector PDFs for all figures to avoid loss of detail.
- **[6e582c460272] (severity: writing)** Define all acronyms (MCC, SSM, BPE, k-mer, TF, lncRNA, MoE, T2T) at first use in Abstract or Introduction.
- **[0b1dd7d161df] (severity: writing)** Replace technical shorthand (T-dec, T-enc, SN) with full terms in Appendix tables or define in caption.
- **[1dfa52f6ae6b] (severity: writing)** Clarify 'shot' regimes (1-shot, 10-shot) as 'examples per class' for non-ML readers.
- **[d532821b6e19] (severity: writing)** Expand benchmark acronyms (GUE, GB, NT, iDHS) in Appendix Task Taxonomy.
- **[667b043a0d80] (severity: writing)** The manuscript claims that GENEB provides a comprehensive evaluation of genomic foundation models, yet it explicitly excludes long‑range regulatory tasks (>10 kb) which are central to many state‑of‑the‑art models (e.g., Enformer, Caduceus). This limitation should be acknowledged more prominently, and any statements suggesting that GENEB “covers the full spectrum of genomic modeling” must be qualified.
- **[300e52be2ab7] (severity: science)** Rank stability analyses (probe vs. MLP, regularization sweeps) are performed on a small subset of 11 models and 13 tasks. The paper extrapolates these results to all 40 models and 100 tasks, which is an over‑generalization. Include a discussion of this limitation or expand the stability checks to a broader sample.
- **[120c542716be] (severity: writing)** The impact statement asserts that GENEB “reduces risk of selecting models based on aggregate leaderboards masking heterogeneity.” While the benchmark shows category‑wise differences, the claim implies that GENEB fully resolves this issue. Temper the language to reflect that the benchmark mitigates but does not eliminate the problem, especially given the limited task diversity in certain domains (e.g., virus/phage, plant lncRNA).
- **[b8b5d5bdac1e] (severity: science)** Add a dedicated discussion of dual‑use risks associated with large genomic foundation models, including potential misuse for pathogenic genome design or harmful gene drives, and outline concrete mitigation strategies (e.g., model access controls, responsible release policies).
- **[0b276211193a] (severity: writing)** Provide a statement on data privacy and security measures taken to protect any personally identifiable genetic information that may be present in the benchmark datasets.
- **[b434423c2fc5] (severity: writing)** Disclose any potential conflicts of interest related to funding sources (e.g., Ministry of Economic Development of the Russian Federation) that could influence the presentation or interpretation of safety‑related findings.
- **[af51528904c7] (severity: science)** Include recommendations for downstream users on responsible application of the benchmark results, emphasizing the need for ethical review before deploying models in clinical or ecological contexts.
- **[f3485f5bb1bc] (severity: science)** Report confidence intervals or standard errors for MCC scores across the 5 seeds (Methodology) to quantify uncertainty in main results.
- **[a377b89dc37c] (severity: science)** Address multiple-comparisons issue for the 13 category-level scaling correlations (Table 1) using FDR or Bonferroni correction.
- **[ffa73680eadd] (severity: science)** Provide statistical significance tests (e.g., paired t-tests or bootstrap CIs) for the 30 controlled-pair differences (Appendix) rather than point estimates alone.
- **[85661a2021de] (severity: writing)** Duplicate LaTeX labels cause cross‑reference collisions (e.g., \label{tab:stability_tasks} appears twice, and \label{fig:high-var} is defined in two separate locations). Rename one of each duplicate to a unique identifier and update all \ref calls accordingly.
- **[1167b83c8385] (severity: writing)** Several tables lack a \label command after the \caption (e.g., the table introduced in Section 2.1 after the "Representative task subset used for probe stability" paragraph). Add a \label for each table to enable reliable referencing.
- **[df3060fe3d4c] (severity: writing)** The document uses \cite and \citep inconsistently; choose a single citation command style (preferably \citep for parenthetical citations) and apply it uniformly throughout the manuscript.
- **[ff92b1fe38ce] (severity: writing)** The manuscript relies on the booktabs commands (\toprule, \midrule, \bottomrule) but does not include \usepackage{booktabs} in the preamble. Insert the package to avoid compilation warnings.
- **[7b09aae214fd] (severity: writing)** Long lines in the source (e.g., the abstract and several table rows) exceed typical 80‑character limits, making the .tex file hard to read. Wrap lines at a reasonable length without breaking LaTeX commands.
- **[e68a7e1c239a] (severity: writing)** Some tables use \small without a surrounding \centering or \begin{center} environment, which can lead to misaligned tables. Ensure each table is centered (e.g., add \centering before \small).
- **[fdd5c68a1404] (severity: writing)** The hierarchy of headings is mostly correct, but the "Related Work" section appears both as a top‑level \section and later as a \section* in the appendix. Consolidate to a single heading level (e.g., use \section for the main body and \section* only for unnumbered appendix sections).
- **[589691a86ca2] (severity: writing)** In the "Methodology" section, the description of the probing protocol is a paragraph without a subheading, while later subsections (e.g., "Scale–Performance Correlation") are introduced. Consider adding a \subsection{Probing Protocol} for consistency.
- **[b111e41f5bd3] (severity: writing)** Abstract is dense; break the long sentence into two and clarify the meaning of “full‑shot, 10‑shot, 1‑shot”.
- **[8812fd382658] (severity: writing)** In the Introduction, the phrase “models are benchmarked disjointly, hindering direct comparison” is vague – replace with a more precise description of the fragmentation problem.
- **[f46446251ed5] (severity: writing)** Figure captions (e.g., Fig. 1, Fig. 2) start with bold text but lack a period after the closing brace; add a period for consistency.
- **[420470c1c1a7] (severity: writing)** Section 3 (Methodology) contains a run‑on sentence: “GENEB probes frozen embeddings with logistic regression (max_iter=1000) in 1‑shot, 10‑shot, and full‑data regimes (5 seeds: 13, 17, 42, 123, 997).” Split into two sentences for readability.
- **[a2f01abcec7c] (severity: writing)** Throughout the manuscript, commas are sometimes missing after introductory clauses (e.g., “After removing the prokaryotic outlier … raises ρ to 0.685”). Insert commas to improve flow.
- **[3f6085f587fe] (severity: writing)** The use of “≥” and “≤” symbols in the text (e.g., “31/36 models show a ≥5× smaller model outperforming…”) should be spelled out or placed in math mode for consistency.
- **[5b075f6532e7] (severity: writing)** In Table 1 and Table 2 captions, the term “macro‑MCC” is introduced without definition; add a brief explanation of the metric on first use.
- **[8e677709b656] (severity: writing)** The “Practitioner Recommendations” bullet list mixes model names with performance numbers without clear separators; reformat as “Model (size, tokenization): performance metric”.
- **[3d51a7d3ed53] (severity: writing)** Section 4.2 (Architecture Effects) uses the phrase “Transformer‑decoder $+$0.149 macro‑MCC vs. Mamba” – clarify that this is a performance gain and not a mathematical addition.
- **[2d6ee980a7a4] (severity: writing)** The conclusion repeats several points from the abstract verbatim; condense to avoid redundancy.
- **[155719efc5f5] (severity: writing)** Several abbreviations (e.g., “MCC”, “SSM”, “BPE”) are not defined at first appearance; add definitions.
- **[449ef15bc9af] (severity: writing)** In the Limitations section, the bullet points lack parallel structure; rewrite so each starts with a gerund (e.g., “Excluding long‑range tasks limits…”, “Task curation may contain noisy labels…”).
- **[b07940929c21] (severity: writing)** The bibliography entries have inconsistent formatting (some use ‘arXiv’, others ‘bioRxiv’); standardize according to the journal’s style.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 48 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
