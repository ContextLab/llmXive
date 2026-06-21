# Revision Specification: Paper Science Revision — PROJ-563-many-shot-cot-icl-making-in-context-lear round 1

**Generated**: 2026-06-21T04:34:12.631985+00:00
**Kind**: paper_science
**Project**: PROJ-563-many-shot-cot-icl-making-in-context-lear
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[eeafbe123105] (severity: science)** The evaluation results for 'gpt-5.2' in Table 1 (section/curvature.tex) lack a citation and the model version is not publicly verified. Add a reference or remove this model from the experimental claims to ensure factual accuracy.
- **[794f5d0d2525] (severity: writing)** Citations \\cite{tsp} (Section 6) and \\cite{vllm} (Appendix) are referenced in the text but missing from example_paper.bib. Add these entries to support the methodological claims.
- **[4ea0291cbc92] (severity: writing)** The citation \\cite{qwen2025qwen25technicalreport} is used for both Qwen2.5 and QwQ models. Verify if QwQ requires a distinct technical report citation to accurately attribute the model architecture.
- **[23bfdb7f1933] (severity: writing)** Algorithm 1 in the Appendix contains a syntax error: `\mathbf{m}[j] \leftarrow \mathbf{m}[j] + \times \mathrm{score}^{(j)}_{M}`. The `+ \times` operator combination is invalid LaTeX/math syntax and logically nonsensical.
- **[ca1f4333e194] (severity: science)** Experimental code artifacts (scripts, configs, tests) are not included in the submission. For reproducibility, please provide a link to the code repository and a `requirements.txt` or environment file.
- **[007f0bb6e8f1] (severity: writing)** Dataset citations lack version numbers and license information. Add explicit dataset versions and licenses for reproducibility.
- **[374a9e137af4] (severity: writing)** No data availability statement: processed demonstration data and embedding vectors are not publicly accessible. Provide a data repository link or commit hash.
- **[80d0416fb053] (severity: writing)** Bibliography contains truncated entries and missing URLs. Complete all references with DOIs or stable URLs.
- **[41c24675ae5d] (severity: writing)** Embedding models lack version/commit specification. Add exact model versions for reproducibility.
- **[06f08f733011] (severity: writing)** Experimental seeds are mentioned but exact seed values are not documented. Provide seed values for full reproducibility.
- **[7575c3add0c8] (severity: writing)** Add accessible alt text to all \includegraphics commands (e.g., using the alt package) to comply with accessibility standards.
- **[7adc086e552d] (severity: writing)** Clarify axis labels in Figure 2 (overview) caption; current description (x=accuracy, y=shots) contradicts standard scaling plot conventions and may confuse readers.
- **[9389558a326f] (severity: writing)** Include dataset names (e.g., BANKING77) directly in Figure 5 caption to ensure standalone interpretability without relying on main text.
- **[b257d5c6a510] (severity: writing)** Verify colorblind accessibility for Figures 2 and 6; add hatching or markers to distinguish 'warm' vs 'cool' tasks for grayscale printing.
- **[8923986d2140] (severity: writing)** Define acronyms RAG, PCA, UMAP, RoPE, TSP, 2-opt, vLLM, and BGE at first use.
- **[24140924f376] (severity: writing)** Simplify technical terms like 'embedding trajectory' and 'in-context test-time learning' for broader accessibility.
- **[93581c3ecfd3] (severity: writing)** Briefly explain 'zone of proximal development' when introduced in Section 5.1.
- **[fab4854cbd15] (severity: writing)** Clarify the model identity for the '5.42 percentage-point gain' claim in the Abstract. This gain corresponds to gpt-5.2 in Table 3, but gpt-5.2 is not defined in the 'LLMs Studied' section (Section 3.2).
- **[526e1cfacc90] (severity: writing)** Correct the demonstration count inconsistency in Table 3 (Section 6). The column header reads '124', while the text and other tables (e.g., Table 4) consistently use '128'.
- **[6400bc5ec700] (severity: writing)** Clarify the source of the 5.42% gain in the abstract; it comes from gpt-5.2 (Table 5), not the primary open models (Qwen3). Ensure the headline number reflects the generalizable contribution or specifies the model.
- **[2ba41f7df937] (severity: science)** Temper the claim of 'causal factor' in Section 5.2. While the ablation supports the hypothesis, embedding curvature is a proxy; use 'suggests a causal link' or 'supports the hypothesis' instead of definitive causality.
- **[75a59ea09dab] (severity: writing)** Review the title and abstract phrasing 'Truly Learn'. Since weights are fixed, 'functional learning' or 'test-time adaptation' is more precise than implying cognitive learning occurs.
- **[19185ebc7346] (severity: writing)** Revise Impact Statement to explicitly discuss dual-use risks of enhanced reasoning capabilities, such as automated generation of complex disinformation or adversarial planning.
- **[71f060d1f2cf] (severity: writing)** Add a statement clarifying copyright/licensing compliance for datasets containing copyrighted narratives (e.g., DetectiveQA) used in the few-shot demonstrations.
- **[c54fa3804f74] (severity: science)** Report standard deviation or confidence intervals for CDS results in Tables 3 and 4 to establish statistical significance of reported gains.
- **[a8696b97ce33] (severity: science)** Increase the number of random seeds for variance analysis beyond 5, or provide statistical justification for the current sample size given observed variance.
- **[d1ad89a71ed0] (severity: science)** Clarify potential circularity in embedding model selection (Qwen3 target vs. Qwen3-Embedding) for the primary curvature analysis.
- **[50fc13771b84] (severity: science)** Report confidence intervals or standard errors for all performance gains in Tables 4, 5, 6 (e.g., CDS vs origin comparisons). Point estimates alone cannot establish statistical significance.
- **[ea0fe2e5c287] (severity: science)** Provide p-values for reported Pearson correlations (r=-0.547 overall). With ~5 orderings sampled, test whether correlations differ significantly from zero.
- **[ee0fadfda8fc] (severity: science)** Apply multiple-comparisons correction (e.g., Bonferroni or FDR) given 3 tasks × 4 shot levels × 3 models × 3 methods = 36+ hypothesis tests.
- **[cca1ece6784a] (severity: science)** Increase random ordering seeds from 5 to at least 10-20 for variance estimates. Five samples yield high uncertainty on standard deviation estimates themselves.
- **[b889ca99184a] (severity: writing)** Fix Algorithm 1 line 15 syntax error ("m[j] ← m[j] + × score_M") and specify how PCA/UMAP scores are weighted/combined statistically.
- **[4e0987b45be4] (severity: science)** Report statistical test results (t-test, ANOVA) comparing CDS vs high-curvature ablation in Table 5, not just point estimates.
- **[59682ceae4f0] (severity: writing)** Remove duplicate package imports (e.g., amsmath, amssymb) to avoid redundancy and potential compilation warnings.
- **[fb8504bcfd94] (severity: writing)** Eliminate or replace negative vertical spacing commands (e.g., \vspace{-5mm}, \vspace{-2mm}) with proper spacing adjustments via LaTeX lengths or class options.
- **[22d3f16f77f2] (severity: writing)** Ensure consistent line wrapping in source files (e.g., keep lines under 80 characters) to improve readability and version‑control diffs.
- **[52af378231c9] (severity: writing)** Add a clear \clearpage before the \appendix to guarantee that figures/tables do not float into the appendix section.
- **[770281ec647f] (severity: writing)** Verify that all algorithm environments include the required \usepackage{algorithmic} (or use the algorithmicx package) to avoid undefined commands.
- **[0e1895f50637] (severity: writing)** Several sentences are overly long and contain multiple clauses, which hampers readability. Break them into shorter sentences and use clearer punctuation.
- **[5d8762edea04] (severity: writing)** Inconsistent use of hyphenation (e.g., "many-shot" vs. "many shot") and capitalization (e.g., "Non-reasoning" vs. "non‑reasoning") throughout the manuscript. Standardize terminology.
- **[0583400b9cd9] (severity: writing)** Figure captions (e.g., Fig. 1, Fig. 2) are sometimes vague or repeat information from the main text. Make captions self‑contained and concise.
- **[34af54da63cb] (severity: writing)** The abstract contains a run‑on sentence with several parenthetical clauses. Rewrite for clarity and to highlight the main contributions more directly.
- **[f3f021de4820] (severity: writing)** Section transitions are abrupt; for example, the jump from "Related Works" to "Settings" lacks a bridging sentence that explains why the experimental setup follows.
- **[5ee8d77c6eae] (severity: writing)** Some LaTeX commands (e.g., \vspace{-5mm}) are used to manually tweak spacing, which can lead to inconsistent layout across versions. Consider relying on standard formatting or package options.
- **[becafd868468] (severity: writing)** The use of "we" throughout the paper is appropriate, but occasional passive constructions (e.g., "is presented") could be replaced with active voice for stronger prose.
- **[b9ccb1176f25] (severity: writing)** Typographical errors such as missing commas before conjunctions (e.g., "...demonstrations, and the query") and inconsistent spacing around mathematical symbols should be corrected.
- **[23ea8d179435] (severity: writing)** The "Impact Statement" section is extremely brief and does not follow the journal's recommended structure. Expand it to address potential societal impacts more substantively.
- **[8c076df15521] (severity: writing)** References in the text sometimes lack proper punctuation (e.g., missing periods after citations). Ensure all citations follow the style guide.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 48 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
