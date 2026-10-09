# Revision Specification: Paper Science Revision — PROJ-776-planbench-xl-evaluating-long-horizon-pla round 1

**Generated**: 2026-06-28T21:49:10.111709+00:00
**Kind**: paper_science
**Project**: PROJ-776-planbench-xl-evaluating-long-horizon-pla
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[5c9361ab5177] (severity: science)** Add missing bibliography entries for all cited keys (e.g., vllm, GPT-5.4, likert1932technique, justus2024bootstrap, ToolLLM, LiveAPIBench). Currently, many citations in the text (Abstract, Sec 3.1, Appendix) have no corresponding entry in custom.bib, making claims unverifiable.
- **[f6bf3985b55c] (severity: science)** Verify the existence and citation of proprietary models (e.g., GPT-5.4, DeepSeek-V4). If these are future/internal models, provide technical reports or API documentation references. Currently, no bibliography entries exist for these model keys.
- **[f3769890addf] (severity: writing)** Ensure all numerical claims (e.g., 51.90% accuracy, 11.36% under blocking) are explicitly linked to the correct tables/figures in the text. Some claims in the Abstract lack direct figure/table references.
- **[1b6fc898233f] (severity: science)** Code repository not accessible for review. Authors should provide public GitHub link with complete implementation, test suite, and dependency specifications for reproducibility.
- **[f283a2f2e803] (severity: science)** No evidence of modular code structure or test coverage metrics in manuscript. Add Appendix section documenting code organization, test strategy, and CI/CD pipeline.
- **[76f1ea4ed36a] (severity: writing)** Specify the exact Creative Commons license version (e.g., CC-BY 4.0) for the benchmark dataset in the Ethics Statements.
- **[7ef02bebf2df] (severity: writing)** Provide a permanent version identifier (Git tag or commit hash) for the GitHub repository and Hugging Face dataset to ensure reproducibility.
- **[5d1658926f98] (severity: writing)** Report inter-annotator agreement metrics (e.g., Krippendorff's alpha) for the human annotation data beyond mean Likert scores.
- **[8bd7ea078ae6] (severity: writing)** Link to the explicit data schema definition (e.g., JSON Schema) used for the 1,665 tools to clarify structure and constraints.
- **[c938bba2208d] (severity: writing)** Resolve label mismatch between Figure~\ref{fig:task_step} in text and file Figures/task_steps_pdf.pdf. Ensure \label{fig:task_step} is defined.
- **[f53f3b87ea25] (severity: writing)** Add alt text to all figures for accessibility compliance (e.g., \alttext or equivalent).
- **[efff0d14f617] (severity: writing)** Ensure color palettes in Figure~\ref{fig:noisy_tool_type_mix} are distinguishable in grayscale print.
- **[597d0d5c1753] (severity: writing)** Verify font legibility in tcolorbox listings (e.g., Figure~\ref{fig:case_irrecoverable_drift_wrong_tool_value}) at print scale.
- **[8801b5c7aac0] (severity: writing)** Define acronyms (LLM, API, MCP, EGT, ITCR, UIRR) at first use in main text.
- **[7e8dca128831] (severity: writing)** Expand 'pp' to 'percentage points' in Section 3.1 and 3.2.
- **[57cb1c0536ee] (severity: writing)** Replace 'datatypes' with 'data types' throughout the manuscript.
- **[4ad62b77c51e] (severity: writing)** Simplify 'retrieval-time blockers' to 'blocked tools' for clarity.
- **[9dc673953557] (severity: writing)** Standardize hyphenation for 'ground truth' and 'tool use'.
- **[4941de716856] (severity: writing)** Qualify generalizations in Abstract and Conclusion regarding 'massive-tool environments' to reflect the retail domain constraint.
- **[fb7e479de87f] (severity: writing)** Acknowledge related retrieval benchmarks (e.g., ToolRet, LiveMCPBench) when claiming novelty on 'retrieval-limited tool visibility'.
- **[c4f3158ebd10] (severity: writing)** Appendix H (Human Annotation) describes five annotators rating tools but lacks IRB approval or informed consent documentation. Add a statement confirming ethical guidelines followed.
- **[a16b9298cc01] (severity: writing)** The dataset release (HuggingFace) requires an explicit statement confirming no Personally Identifiable Information (PII) is included, given the 'retail domain' context.
- **[463374be273d] (severity: science)** Safety claims rely on models like 'GPT-5.4' which appear non-existent. Clarify if these are placeholders; otherwise, safety evaluations are invalid.
- **[3adfbec2682e] (severity: science)** Resolve contradiction between text claiming 'highly consistent' seed results and Figure 12 caption stating 'variation 20 pp'. 20pp variance undermines benchmark reliability.
- **[863a93bfd19f] (severity: science)** Clarify potential bias from using GPT-5.2 for data construction when evaluating GPT-5.4. Provide ablation or justification.
- **[27f6d4162d07] (severity: science)** Justify 327-task sample size for statistical power across 10 models and multiple blocking conditions.
- **[aa9febb46db4] (severity: science)** Multiple comparisons across 10 models × multiple blocking conditions lack correction (e.g., Bonferroni, FDR). Report adjusted p-values or confidence intervals to control Type I error inflation.
- **[2ee103f27d40] (severity: science)** Seed variability shows 20 pp accuracy swings (Figure seed_acc, Appendix E002). This exceeds reported CI widths (~2.94 pp). Re-run with more seeds or report seed-dependent variance explicitly.
- **[365f2dab97e0] (severity: science)** No explicit hypothesis tests reported for model comparisons. Confidence intervals alone are insufficient; add paired tests (e.g., McNemar, bootstrap t-tests) with effect sizes.
- **[860620e06d17] (severity: science)** Sample size (327 tasks) lacks power analysis justification. Explain why this size detects meaningful differences given observed variance.
- **[2a098887eee6] (severity: writing)** Replace the undefined macros \BENCH{}, \bench{}, and \linkblock with either proper definitions or explicit text; undefined commands cause LaTeX compilation failures.
- **[02397e8bbdeb] (severity: writing)** Convert the unnumbered sections \section*{Limitations} and \section*{Ethics Statements} to numbered sections (\section{Limitations} etc.) to maintain a consistent heading hierarchy throughout the document.
- **[bbafb4eb1748] (severity: writing)** Ensure that all tables are wrapped in a proper table environment (e.g., \begin{table}...\end{table}) rather than being inserted via \input{Tables/...} alone; otherwise they will not be floated or captioned correctly.
- **[59abaa4edd13] (severity: writing)** Add the required package imports for tcolorbox, listings, and any custom commands used (e.g., \usepackage{tcolorbox, listings}) in the preamble to avoid missing-package errors.
- **[7b57afaf4baa] (severity: writing)** Standardize citation commands: use either \citep{...} or \citet{...} consistently throughout the manuscript; mixing styles can lead to inconsistent bibliography formatting.
- **[ef0f902cfaac] (severity: writing)** Check figure placement: figure* environments span two columns and should appear at the top of a page; verify that the intended layout matches the journal's guidelines, and replace with regular figure if single-column width is desired.
- **[1c0505d831f4] (severity: writing)** Wrap the itemize environments that include custom spacing options inside a \begin{itemize}[...]\end{itemize} block that loads the enumitem package; otherwise LaTeX will raise an undefined option error.
- **[f712d7270624] (severity: writing)** Verify that all \label{...} commands are placed after the corresponding \caption{...} within figures/tables to ensure correct cross-reference linking.
- **[01b535929cb5] (severity: writing)** Several sentences contain run‑on structures and missing commas, reducing readability (e.g., abstract first sentence, §4.1 description of blocking). Insert appropriate punctuation and consider splitting long sentences.
- **[39ffae018d9d] (severity: writing)** Inconsistent use of the benchmark name: sometimes "\BENCH{}", sometimes "\bench{}". Standardize to a single macro (e.g., \bench) throughout the manuscript.
- **[f7431724cb98] (severity: writing)** Figure captions often start with lower‑case letters and lack sufficient description of what is being shown (e.g., Fig 2, Fig 3). Capitalize the first word and add a brief explanatory clause.
- **[426dad8b280e] (severity: writing)** The LaTeX macro for the benchmark name (\BENCH{}) is defined but never used consistently; also the macro name appears in the source as "\BENCH{}" and "\bench{}". Define a single macro and replace all occurrences.
- **[86bb1623172c] (severity: writing)** The “Limitations” and “Ethics Statements” sections are placed before the main body and lack proper section numbering. Move them to after the conclusion and use \section*{} for unnumbered sections.
- **[d63568286de0] (severity: writing)** Some tables and figures are referenced without a preceding “Fig.” or “Table” (e.g., "see Figure~\ref{fig:task_step}"). Ensure consistent referencing style.
- **[ed7ba2ab2306] (severity: writing)** The bibliography entries contain inconsistent capitalization and missing periods (e.g., "arXiv preprint arXiv:2603.03202"). Apply a uniform bibliography style (e.g., ACL style).
- **[8b7eb46d07af] (severity: writing)** The abstract contains a stray footnote marker ("\footnote{*Equal contribution.}") that appears outside the abstract environment. Relocate the footnote to the author block.
- **[d0f093200764] (severity: writing)** Multiple instances of "\textbf{...}" are used inside section headings, which is unnecessary and can cause formatting issues. Remove bold formatting from headings.
- **[f52cec2c484d] (severity: writing)** The “Takeaway” environment is used without a preceding definition; ensure the custom environment is defined in the preamble or replace with a standard \paragraph{}.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 48 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
