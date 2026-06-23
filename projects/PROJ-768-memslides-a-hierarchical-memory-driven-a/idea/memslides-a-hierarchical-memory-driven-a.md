---
field: linguistics
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/351
paper_authors:
  - Ye Jin
  - Yangyang Xu
  - Jun Zhu
  - Yibo Yang
---

# MemSlides: A Hierarchical Memory Driven Agent Framework for Personalized Slide Generation with Multi-turn Local Revision

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.17162
Paper authors (from arXiv): Ye Jin, Yangyang Xu, Jun Zhu, Yibo Yang

Submitted by: github-actions[bot]

(Intake from human-submission issue #351.)

## Rejection rationale (2026-06-23)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[ea75007f332a]** Add a reproducibility README and automation (e.g., Makefile or scripts) that installs exact LaTeX package versions, pulls the data, runs the evaluation scripts, and produces all tables/figures from raw outputs.
- **[0734102684ee]** Provide the Python (or shell) scripts used to generate the quantitative tables (profile_memory_v6_*.tex) and figures, together with version‑pinned dependencies (requirements.txt) and random seeds for deterministic runs.
- **[072127c48e25]** Separate experimental code from the manuscript: place all data‑processing, model‑calling, and metric‑computation logic in a dedicated `src/` directory with clear module boundaries rather than embedding large code blocks in the LaTeX source.
- **[3d10783082f6]** Introduce a minimal test suite (e.g., pytest) that validates data loading, API‑call wrappers, and metric calculations to catch regressions before paper generation.
- **[ffb8ca980416]** Document how external APIs (GPT‑5, GLM‑5, Gemini) are accessed, including handling of API keys, rate limits, and cost accounting, so that reviewers can reproduce the experiments without hidden credentials.
- **[46729eda15a2]** Ensure all figures are generated from source files (e.g., matplotlib, tikz) rather than static PDFs; include the source code (e.g., .py or .tex) for each figure in the repository.
- **[a08b33387bf4]** Add an explicit license statement for the GitHub repository (https://github.com/huohua325/Memslides) and any other third‑party code or assets used. Prefer an OSI‑approved open‑source license and include the license file in the repository.
- **[4bd651c5fcc8]** Release the constructed user‑profile bank and all evaluation artifacts (prompts, generated decks, judge outputs, trace logs) in a stable, version‑controlled repository (e.g., Zenodo or a GitHub release with a DOI) to enable reproducibility.
- **[45721849f184]** Archive all external URLs (code repo, website, project page, video) using a web‑archiving service (e.g., archive.org) and include the archived URLs in the paper to mitigate link‑rot.
- **[c9b8c3bda925]** Provide a data schema description (e.g., JSON schema) for the profile entries and tool‑memory records, and document how missing fields are handled during the seeded‑completion step.
- **[8a9c0587875e]** Specify version identifiers for the profile bank (e.g., v1.0) and for any model API versions used, and record these in the appendix to improve traceability.
- **[c3bcfaf4bdac]** Add descriptive alt‑text (or a short descriptive caption) for every included figure (e.g., via the \includegraphics[...]{...} optional argument or a surrounding \caption) to improve accessibility for screen‑reader users.
- **[6010d3d4164f]** Check and, if necessary, adjust the colour palette used in all diagrams (Figures 1, 2, 3, 8, 9, 10) to ensure they remain distinguishable when printed in grayscale and for common colour‑blindness types (e.g., replace red/green contrasts with colour‑blind‑safe palettes or add pattern/label cues).
- **[ae20ffb299ce]** Verify that any raster images embedded in the PDF figures (e.g., slide screenshots in Figures 4, 5, 6, 7) have a resolution of at least 300 dpi so that details are legible at typical print sizes.
- **[714257837904]** For any figure that contains axes, data points, or quantitative plots (none are present now, but future additions), ensure that axis labels include units and that legends are clear and not reliant solely on colour.
- **[e57aa3480787]** Replace or simplify overloaded terms such as “hierarchical memory framework”, “personalized presentation agents”, and “multi‑turn localized revision” with clearer, more concrete language.
- **[a6b0403b468d]** Define every acronym at first use (e.g., LLM, API, RAG, etc.) and consider removing those that are not essential to the core argument.
- **[8c7861117ece]** Break up long, dense sentences (e.g., the abstract paragraph and several sentences in the Introduction) to improve readability for non‑specialist readers.
- **[28495eacce2a]** Reduce reliance on field‑specific buzzwords like “scoped slide‑local revision”, “execution contract”, and “guarded patch calls”; replace them with plain descriptions of the process.
- **[db3d34a0ffe9]** Add brief explanatory footnotes or parenthetical remarks for technical concepts such as “tool‑memory injection”, “working memory”, and “profile‑memory routing” to aid readers unfamiliar with agent‑memory literature.
- **[823876a96e0a]** The claim that working memory supports session‑level preference carryover is only backed by qualitative figures (Appendix Fig. 9). Provide a systematic quantitative evaluation (e.g., controlled ablation or statistical analysis) to substantiate this claim.
- **[6e4c3019e121]** Clarify whether the profile‑memory and tool‑memory ablations control for all other variables (e.g., template usage, prompt phrasing). Explicitly state that the only difference between conditions is the memory injection to avoid implicit causal assumptions.
- **[3e5e41718912]** In Section 3, the problem formulation is presented twice with slightly different notation (e.g., $z_t$ vs $U(z_{t-1},f_t)$). Consolidate the formulation to avoid potential confusion about the role of session state.
- **[210d8e4dc7a5]** Temper the causal claim in the abstract and conclusion that “effective personalization … depends on separating persistent user profiles, session-level working memory, and reusable execution experience” – the evidence is limited to controlled persona‑alignment and diagnostic modify settings, not real‑world user studies.
- **[430dd7c6ae9d]** Add a clear statement in the discussion that the presented gains may not generalize to heterogeneous user populations, noisy feedback, or production‑scale slide authoring pipelines.
- **[1397ec877d22]** Provide quantitative analysis of variance or statistical significance for the persona‑alignment scores (e.g., confidence intervals) to avoid implying definitive superiority when differences are modest (e.g., Gemini 3.1 Pro Structure scores).
- **[1bb38e9917bd]** Clarify that the tool‑memory improvements are demonstrated only on a diagnostic matched‑pair benchmark; avoid extrapolating to broader editing scenarios without additional evaluation.
- **[80dae345dfee]** In the limitations section, explicitly acknowledge that the profile bank and edit requests are synthetic proxies and that user privacy, consent, and memory management in real deployments remain untested.
- **[aeeb7d582b44]** The paper stores persistent user‑profile memory that may contain personally identifiable or sensitive preference information. The manuscript lacks concrete mechanisms for user consent, data minimization, and secure deletion of these profiles.
- **[5c045961580e]** Evaluation is performed on synthetic persona‑intent profiles rather than real user data, yet the authors claim broader applicability. An IRB or ethics review is required before deploying with actual users.
- **[ac035287e929]** Potential for misuse: the system can generate highly tailored persuasive slides, which could be weaponized for misinformation or targeted propaganda. No discussion of misuse mitigation or access controls is provided.
- **[f8bb244f1bd0]** The paper does not address bias that may be encoded in the profile bank (e.g., occupational stereotypes) and how the system might amplify such biases in generated decks.
- **[c22311bb0320]** No audit or transparency features are described for the hierarchical memory (e.g., user‑visible logs of what preferences are stored or how they influence output).
- **[b90e05feb08a]** Report variance (e.g., standard deviation or confidence intervals) for all quantitative tables (e.g., Table 1, Table 2, Table 3) and perform appropriate statistical significance tests to support claims of improvement.
- **[bd188e8f0e12]** Clarify the exact number of unique decks evaluated per persona‑intent pair and per model family; the current description (49 runs) conflates runs with distinct evaluation units.
- **[6d5f1fcf493f]** Provide a power analysis or justification that the matched‑pair tool‑memory evaluation (9 pairs) is sufficient to draw reliable conclusions, or increase the number of pairs.
- **[5c766fc00288]** Include effect size measures (e.g., Cohen's d) for the persona‑alignment gains to contextualize practical significance beyond raw score differences.
- **[75cd48e930dc]** Document the randomization procedure for selecting source materials, personas, and modify requests to rule out selection bias.
- **[91ed05f47ea4]** Address potential p‑hacking by pre‑registering evaluation protocols or explicitly stating that all reported metrics were defined a priori.
- **[0b7cbf22b60c]** The paper reports mean scores for persona‑alignment and quality metrics but provides no confidence intervals or standard deviations, making it impossible to assess the statistical reliability of the reported differences.
- **[b49ad7912c31]** No statistical significance testing (e.g., paired t‑tests, Wilcoxon signed‑rank tests) is reported for the comparisons between MemSlides and baselines, despite multiple metrics and model families being evaluated; this raises the risk of false positives due to multiple comparisons.
- **[349d7e274670]** The diagnostic matched‑pair tool‑memory evaluation aggregates results across nine pairs, yet the paper does not correct for the multiple hypothesis tests performed (e.g., Bonferroni or Holm correction), nor does it report effect sizes.
- **[6d7e3a89cb49]** Assumptions underlying the use of arithmetic and geometric means (e.g., normality, independence) are not justified, especially for metrics like Core Tool Time Ratio that are ratios of skewed timing data.
- **[adfdebb6b047]** Reproducibility of the statistical analysis is limited: the code for computing the paired‑robustness sign test, the exact formulas for the geometric mean of time ratios, and the random seed settings are not released.
- **[27ca2f6b2c64]** The paper mixes different scales (0‑10 judges, 1‑5 quality scores, raw seconds) in a single table without normalizing or providing variance estimates, which can mislead readers about the relative magnitude of improvements.
- **[874e9b398f35]** In the author block (main.tex lines 30‑45) the mix of \And and \AND creates inconsistent vertical spacing. Use a single macro (\And) for all author separations and move the manual \vspace{-0.85em} out of the author environment.
- **[db268053483c]** After \maketitle the manual \vspace{-1.55em} and \vspace{0.35em} (lines 53‑55) are non‑standard and can cause layout glitches on different page sizes. Replace them with proper spacing commands (e.g., \setlength{\belowcaptionskip}{...}) or adjust the class options.
- **[dfc45da89f25]** Figure captions should be placed below the \includegraphics command and before the \label. Several figures (e.g., Fig. 1 in sections/01_introduction.tex lines 84‑88) have the \label after the caption, which is correct, but ensure no extra vertical space (\vspace{-3mm}) is inserted between the image and caption as it may break the caption‑figure association.
- **[bdc0fccc6145]** Table environments occasionally lack explicit \centering before the font size change (e.g., tables/profile_memory_v6_bestof_main_table.tex lines 5‑7). Move \centering to the top of the table environment to guarantee consistent horizontal alignment.
- **[301efc50ae65]** Ensure every referenced figure/table has a preceding \label that appears after the \caption. The reference to Fig.~\ref{fig:appendix_working_memory_carryover} (appendix/appendix.tex line 84) is correct, but double‑check all other cross‑references for this ordering.
- **[751b93d7640d]** The bibliography style plainnat is used, but the natbib package is not loaded. Add \usepackage{natbib} in the preamble to guarantee proper citation formatting.
- **[02961ce97f85]** Several sentences in the abstract and introduction are overly long and contain comma splices, making them hard to follow (e.g., abstract lines 4‑6, introduction lines 9‑12). Break them into shorter sentences and use clearer conjunctions.
- **[ca949768a460]** Inconsistent use of hyphenation for terms like “multi‑turn” and “multi‑turn” (sometimes hyphenated, sometimes not). Standardize throughout the manuscript.
- **[7c9a7ebb1d69]** Figure captions (e.g., Figure 1 and Figure 2) lack descriptive detail about what the reader should notice; add brief explanatory sentences.
- **[eac7bd744a25]** The bibliography style mixes plainnat with author‑year citations, leading to mismatched formatting in the reference list. Choose a single citation style and apply it consistently.
- **[b1a0e5fcd5a8]** The conclusion (Section 6) repeats earlier points without summarizing key take‑aways; rewrite to provide a concise synthesis and future‑work outlook.
- **[db454106a22b]** There are several typographical errors such as missing spaces after periods and inconsistent capitalization of section headings (e.g., “Problem Formulation” vs. “Multi‑Turn Localized Modify Execution”). Proofread for these minor issues.
