---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/166
paper_authors:
  - Yujun Wu
  - Dongxu Zhang
  - Xinchen Li
  - Jinhang Xu
  - Yiling Duan
  - Yumou Liu
  - Jiabao Pan
  - Qiyuan Zhu
  - Xuanhe Zhou
  - Jingxuan Wei
  - Siyuan Li
  - Jintao Chen
  - Conghui He
  - Cheng Tan
---

# Intern-Atlas: A Methodological Evolution Graph as Research Infrastructure for AI Scientists

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2604.28158
Paper authors (from arXiv): Yujun Wu, Dongxu Zhang, Xinchen Li, Jinhang Xu, Yiling Duan, Yumou Liu, Jiabao Pan, Qiyuan Zhu, Xuanhe Zhou, Jingxuan Wei, Siyuan Li, Jintao Chen, Conghui He, Cheng Tan

Submitted by: github-actions[bot]

(Intake from human-submission issue #166.)

## Rejection rationale (2026-06-03)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[27cca22eabe3]** Provide quantitative error propagation analysis showing how the 70.4% Phase-1 extraction accuracy impacts downstream idea evaluation scores and lineage reconstruction reliability.
- **[d79ed99fe928]** Confirm verification_status for all bibliography entries in state/citations/PROJ-569-intern-atlas-a-methodological-evolution.yaml or update ref.bib to include DOIs/URLs for all entries.
- **[9803c45caa38]** Source code artifacts (scripts, configs, tests) are missing from the submission package. Please upload the implementation repository or provide a direct link to the public codebase to enable a full code quality assessment.
- **[6453024791ef]** Dependency hygiene is unclear; specific versions for Nougat, GROBID, and LLM APIs (Qwen3.6, Claude-Sonnect) should be pinned in a requirements.txt or environment.yml file.
- **[6b7d11604658]** Reproducibility from scratch requires unit tests for the evaluation metrics (e.g., Novelty, Feasibility signals) and the SGT-MCTS algorithm, which are not visible in the current input.
- **[59fc0087b0b1]** Add an explicit data license (e.g., CC-BY 4.0, ODC-BY) in the Data Availability Statement or Conclusion to clarify usage rights for the released graph.
- **[41276fed0fdc]** Include a dataset version identifier (e.g., v1.0) in the metadata and HuggingFace link to ensure reproducibility and track updates.
- **[6879f0e1d779]** Clarify the specific 'neutral default' value for missing publication years in Appendix A, beyond the temporal coherence score of 0.70.
- **[6d7d3857da15]** Fix subfigure label mismatch in Figure 4 (fig:main_four_results). Labels use 'four_a'/'four_d' but caption enumerates (a)/(b). Standardize to match caption.
- **[6048e74faf82]** Standardize figure file paths. Some are in 'figures/' (e.g., Figure3.pdf) while others are root-level (e.g., intro.pdf). Consolidate under a single directory for maintainability.
- **[fb06e12372fe]** Add explicit accessibility metadata (alt text) to all \includegraphics commands where supported, ensuring screen reader compatibility for complex diagrams.
- **[84e450d53c4f]** Define all acronyms (e.g., SGT‑MCTS, UCT, BM25, LLM) at their first occurrence; otherwise readers must guess their meaning.
- **[9bab769afc2c]** Replace or explain overloaded technical terms such as “causal edge”, “strong‑causal”, “temporal coherence”, and “graph‑grounded” with plain‑language equivalents (e.g., “cause‑and‑effect link”, “high‑confidence link”, “time‑aware”, “graph‑based”).
- **[015d72634558]** Simplify the description of the Monte‑Carlo Tree Search process; the current phrasing (“selection by SGT‑UCT, expansion of the highest‑confidence untried child…”) is dense and inaccessible to readers without a background in AI planning.
- **[0b4d691b064e]** Avoid repeatedly using the term “methodology” in compound forms (e.g., “methodological evolution graph”, “method‑level heterogeneous graph”). A single clear phrase like “method evolution map” would be clearer.
- **[bc5dcbde80b2]** Clarify the meaning of domain‑specific jargon such as “bottleneck”, “mechanism”, and “trade‑off” when they appear in the evidence record; a brief parenthetical definition would help non‑specialist readers.
- **[5b73572569c3]** Introduce a short, non‑technical summary of the three operators (lineage reconstruction, idea evaluation, idea generation) early in the paper, using everyday language (e.g., “tracing how methods changed over time”, “rating new research ideas”, “suggesting new ideas”).
- **[88965af540f2]** Consider replacing the abbreviation “SGT‑MCTS” with a more descriptive name or a brief expansion (e.g., “Self‑Guided Temporal Monte‑Carlo Tree Search”) at first use and then consistently use the short form.
- **[b2451f248b4f]** The phrase “strong‑causal subset” is jargon‑heavy; replace with “high‑confidence cause‑and‑effect links”.
- **[5aec3b7a418b]** The section titles and figure captions use many technical adjectives (“typed evolution edges”, “causal edge labels”, “verb atim bottleneck‑to‑mechanism evidence”). Rewrite them to be more approachable.
- **[ceb24eadc271]** Resolve the corpus size discrepancy between the Abstract/Section 2.2 (1,030,314 papers) and Appendix A.1 (66,431 full texts). Clarify if the larger number refers to references or a different subset.
- **[f38d1b02f6a5]** Correct the edge vocabulary count in Appendix A.1. The text states 'nine-class' while Table 1 and Section 2.2 list seven types.
- **[6e8116354314]** Align the evidence record schema in Eq. 1 with Appendix A.2. Eq. 1 defines four fields, while Appendix A.2 describes an 'impact' object with three sub-fields.
- **[d3f854ff435d]** The paper claims that Intern‑Atlas will become a foundational data layer for AI research agents, but provides only limited empirical validation (survey‑derived benchmarks and a small Strata dataset). Reduce the scope of these claims or add broader, independent evaluations.
- **[b99acde97e4d]** The conclusion states that the graph ‘enables downstream applications in idea evaluation and automated idea generation’ yet the evaluation only covers three specific tasks with narrow baselines. Clarify that these results are preliminary and do not prove general utility.
- **[e96db2883d26]** Assertions such as “methodological evolution graphs can serve as a foundational data layer for the emerging automated scientific discovery” are speculative and not supported by evidence of adoption or impact on actual AI agents. Rephrase to reflect a hypothesis rather than a demonstrated fact.
- **[26233ce59838]** Explicitly state IRB approval or informed consent procedures for the 10 human PhD researchers involved in idea evaluation (Section 4.2, Appendix app:idea-eval-data).
- **[60cfc2fb1015]** Expand the Broader Impact discussion to address dual-use risks of automated scientific idea generation beyond 'no plausible pathway to direct harm' (Appendix app:limitations).
- **[cb2b7096543e]** Disclose the 70.4% production extraction accuracy in the main text to ensure users understand potential error rates in verbatim evidence (Appendix app:extraction).
- **[bfc65d1787a4]** Clarify the circular validation in Sec 4.3. The idea generator is evaluated using the same Intern-Atlas scoring pipeline (Sec 4.2) that relies on the graph used for generation. Quantitative scores in Table 4.3 are tautological. Provide independent metrics or ablation showing generation quality is not an artifact of the shared scoring function.
- **[d014cd907d52]** Report statistical significance for all comparative claims. Correlation differences (0.81 vs 0.58 in Fig 5a) and win rates (88% in Fig 5b) lack confidence intervals or p-values. Perform Fisher's Z tests for correlations and binomial tests for win rates to confirm robustness against sampling variance.
- **[135969a61568]** Address the ground truth construction bias in Sec 4.1. The benchmark uses LLM extraction + manual audit. If the LLM logic mirrors the graph construction model, this risks circular validation. Detail the audit independence and consider a subset of purely human-curated chains for validation.
- **[cf336815a043]** Report confidence intervals or standard errors for all aggregate metrics in Table 1 (lineage search) and Table 3 (idea generation).
- **[40d6f7b3e3ef]** Perform statistical significance tests (e.g., paired t-test, McNemar) for baseline comparisons in Sections 4.1 and 4.3.
- **[208e1a52c3f1]** Report inter-annotator agreement (e.g., Krippendorff's alpha) for the human evaluation study in Section 4.2.
- **[5b2cf429673d]** Address multiple-comparison correction when testing across five evaluation dimensions in Section 4.2.
- **[589e21b45875]** Avoid using negative vertical spacing (e.g., `\vspace{-1.5em}`) around tables and figures; it can cause overlapping content and unpredictable page breaks.
- **[dd0851e7ebe8]** The `\rowcolor{lightblue}` command in Table 1 requires the `colortbl` package. Add `\usepackage{colortbl}` or replace row coloring with `tcolorbox`/`xcolor` compatible syntax.
- **[d7384493bf5e]** In the `wraptable` environment (Table 1), the `\caption` appears before the `tabular`. Move the caption after the `tabular` (or use `\caption*` before) to follow conventional LaTeX practice and ensure proper placement.
- **[12123306941e]** Duplicate color definitions for `promptcolor` and `promptcolorheader` appear in both the main preamble and the author‑defined block. Consolidate these definitions to avoid redundancy.
- **[bf278ee8fa5a]** Some `figure*` environments (e.g., Figure 1) are placed before the first `\section`. While allowed, they may float to unexpected locations. Consider moving them after the relevant section heading to improve logical ordering.
- **[4b9f668f2216]** Ensure all figures and tables are referenced in the text. For instance, verify that Table 2 (`tab:idea-eval-strata-transposed`) and Figure 4 (`fig:main_four_results`) have explicit `\ref{}` calls.
- **[07f3fb85e63c]** The `wraptable` environment can interfere with the two‑column layout flow. If layout issues arise, replace it with a standard `table` environment or adjust the wrap width.
- **[6dbc5e6600ec]** Consistently use `\centering` inside `figure`/`table` environments *before* `\includegraphics` or `\begin{tabular}` to avoid stray indentation.
- **[293c47beeb58]** Add `\usepackage{booktabs}` (already present) but also `\usepackage{colortbl}` for row coloring, and consider using `\toprule`, `\midrule`, `\bottomrule` consistently across all tables.
