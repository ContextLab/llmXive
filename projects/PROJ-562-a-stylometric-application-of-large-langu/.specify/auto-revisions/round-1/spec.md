# Revision Specification: Paper Science Revision — PROJ-562-a-stylometric-application-of-large-langu round 1

**Generated**: 2026-06-11T16:41:00.601197+00:00
**Kind**: paper_science
**Project**: PROJ-562-a-stylometric-application-of-large-langu
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[b37264814fb6] (severity: writing)** Section 3.4 claims '6 of the 8 authors' showed significant patterns for content-word-only models, but Supp. Tab. 1 shows 7 significant p-values (Melville is the only non-significant). Align text with data.
- **[c6f1341c5887] (severity: writing)** Section 3.4 claims '5 of the 8 authors' for function-word-only models, but Supp. Tab. 2 shows 6 significant p-values (Austen and Melville non-significant at p<0.05). Align text with data.
- **[607cb4a0673c] (severity: writing)** Section 3.4 claims '3 of the 8 authors' for POS-only models, but Supp. Tab. 3 shows 4 significant p-values (Austen, Dickens, Twain, Wells). Align text with data.
- **[212c33ef9124] (severity: writing)** Code repository not provided for review. The paper claims code availability at https://github.com/ContextLab/llm-stylometry but actual training scripts, data preprocessing code, and evaluation pipelines are not accessible.
- **[930658d7217b] (severity: writing)** No test files or unit tests visible in provided artifacts. Reproducibility cannot be verified without access to training scripts with hyperparameters, random seed handling, and evaluation code.
- **[eab63c047100] (severity: writing)** Dependency specifications (requirements.txt, environment.yml, or setup.py) not provided. Cannot verify dependency hygiene or reproducibility from scratch.
- **[bbbe0e117906] (severity: writing)** Project Gutenberg corpus version and download date not specified (Sec. 2.1). Texts may change over time, affecting reproducibility.
- **[882dde832071] (severity: writing)** External GitHub repository link should include archive identifier or DOI for permanence against link rot.
- **[1a15cdf99f6e] (severity: writing)** GPT-2 tokenizer version and Hugging Face Transformers library version not documented in Methods section.
- **[2483247a8ad1] (severity: science)** Supplementary Figure fig:t-stats-pos references the wrong image file: figs/t_stats_content_only.pdf is used for both the content-words and POS ablation plots (supplement.tex, lines 257-263). This appears to be a copy-paste error; verify the correct file path for the POS variant.
- **[6169eb6c26df] (severity: writing)** No alt text is provided for any of the 5 main figures or 8 supplementary figures. Modern accessibility standards require descriptive alt text for screen readers. Add alt text to each includegraphics command or provide figure descriptions in the caption.
- **[e80e6975a132] (severity: writing)** Figure captions mention color-coded author models (e.g., Each color denotes a model trained on a single authors work) but do not specify if the color scheme is colorblind-accessible. Verify the palette meets WCAG 2.1 contrast requirements or add a grayscale-printable alternative.
- **[1d6048608f5c] (severity: writing)** Figure fig:mds and fig:confusion-matrix are referenced as 3D MDS projection and heatmap but do not include a colorbar/legend in the caption describing the loss scale. Add explicit unit labels (cross-entropy loss, nats or bits) to the axis or colorbar.
- **[aaa313725afe] (severity: writing)** Define 'df' in Table 1 caption as 'degrees of freedom' for non-statisticians.
- **[9b6cdcac5c52] (severity: writing)** Replace 'causal language modeling objective' with 'next-word prediction' in Methods.
- **[136883f9dd3c] (severity: writing)** Define 'ablation' in Section 2.3 (e.g., 'controlled removal experiments').
- **[7bb1fb6f358a] (severity: writing)** Simplify 'open-set attribution' and 'parameter-efficient fine-tuning' in Discussion.
- **[fcf3a7915f4b] (severity: science)** In the Results section (Ablation Studies), the text claims specific counts of authors showing significant patterns (e.g., '6 of the 8' for content words, '5 of the 8' for function words, '3 of the 8' for POS). However, the Supplement Tables (tab:t-tests-content, tab:t-tests-function, tab:t-tests-pos) show different counts based on standard p < 0.05 thresholds (7, 6, and 4 respectively). The textual conclusions do not strictly follow from the provided tabular evidence.
- **[84e32c28005a] (severity: writing)** The Methods section (Sec. 2.1) identifies the author as 'Rosemary Plumly Thompson', while the Abstract, Introduction, and Oz attribution section refer to 'R. P. Thompson' (commonly known as Ruth Plumly Thompson). This internal inconsistency in entity naming undermines the precise identification of the data source.
- **[1ab84e21622c] (severity: writing)** Abstract claims to 'confirm' Oz book authorship (line 57). This is a settled case. Reframe as validating against known attribution, not confirming contested work.
- **[5fd06e06cc28] (severity: science)** Define 'stylometric distance' (lines 357-362) more cautiously. Verify metric properties or label as 'similarity measure' to avoid overclaiming theoretical rigor.
- **[76d169071691] (severity: writing)** Align Abstract/Results generalizations (e.g., 'embodies unique writing style', line 54) with Limitations section (lines 630+). Avoid implying broader validity than the 8-author dataset supports.
- **[5340f8172ebd] (severity: writing)** Add a brief statement in the Discussion or Conclusion section explicitly distinguishing the ethical implications of applying this method to historical texts versus living individuals, noting potential risks regarding anonymity and misattribution for contemporary works.
- **[25d29374f3f8] (severity: science)** Report effect sizes (e.g., Cohen's d) for all t-tests in Table 1 and Supplementary Tables to quantify stylistic separation magnitude.
- **[b7f510296d4e] (severity: science)** Clarify sample sizes and independence assumptions for the ablation study statistical comparisons (Sec. 3.4).
- **[4e15f2e069f5] (severity: science)** Discuss potential genre/period confounds given all 8 authors are classic English literature (Methods, Sec. 2.1).
- **[75800142aec6] (severity: science)** Clarify sample sizes for t-tests in Table 1; reported degrees of freedom (e.g., df=11.27 for Twain) are inconsistent with pooling all 7 other authors' seeds (n=70) and suggest averaging per seed (n=10), but the text implies pooling.
- **[b4fd6f78c17e] (severity: writing)** Address multiple comparisons correction for the 8 author tests and ablation comparisons. While p-values are small, methodological rigor requires acknowledging family-wise error rate control.
- **[38b97b1ac3c4] (severity: writing)** Report effect sizes (e.g., Cohen's d) alongside p-values for key t-tests to quantify the magnitude of stylometric separation beyond statistical significance.
- **[8f98c5ec1070] (severity: writing)** Standardize table styling: Main text tables (e.g., line 315) use \hline while Appendix (line 650) uses booktabs. Align to booktabs for consistency.
- **[2539657117dc] (severity: writing)** Fix cross-reference macros: Main text uses \crossentropyContent (expands to '1'), but Supplement labels are descriptive (e.g., \label{fig:all-losses-content}). Ensure refs resolve correctly.
- **[b2cc2b54e0b6] (severity: writing)** Remove manual page breaks: Appendix tables in main-llmxive.tex (lines 730, 750, 770) contain hardcoded \newpage commands. Allow LaTeX to manage flow.
- **[af29fcd9a47c] (severity: writing)** Unify figure placement: Main text uses [t] (line 220), Supplement uses [h] (supplement-llmxive.tex line 45). Prefer [t] or [p] for wide figures to avoid layout breaks.
- **[09fb3c51fa8a] (severity: writing)** Correct the repeated word 'the' in the caption of Figure 2 (Section 3) and Figure 3 (Supplement).
- **[d74ac4f447c9] (severity: writing)** Standardize the capitalization of 'i.e.' in Figure 5 caption to match journal style.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 35 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
