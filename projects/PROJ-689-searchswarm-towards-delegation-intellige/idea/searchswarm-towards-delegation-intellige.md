---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/313
paper_authors:
  - Pu Ning
  - Quan Chen
  - Kun Tao
  - Xinyu Tang
  - Tianshu Wang
  - Qianggang Cao
  - Xinyu Kong
  - Zujie Wen
  - Zhiqiang Zhang
  - Jun Zhou
---

# SearchSwarm: Towards Delegation Intelligence in Agentic LLMs for Long-Horizon Deep Research

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.09730
Paper authors (from arXiv): Pu Ning, Quan Chen, Kun Tao, Xinyu Tang, Tianshu Wang, Qianggang Cao, Xinyu Kong, Zujie Wen, Zhiqiang Zhang, Jun Zhou

Submitted by: github-actions[bot]

(Intake from human-submission issue #313.)

## Rejection rationale (2026-06-21)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[bf9e78114376]** The claim that “Large language models face finite context windows” is supported by citations to SWE‑Bench, RepoZero, and ProgramBench, which do not discuss context‑window limitations. Replace these citations with appropriate references on context‑window constraints or rephrase the statement to avoid unsupported citation.
- **[c38279dcdfe8]** The paper reports Qwen3‑30B‑A3B‑Thinking fine‑tuning results (66.5 on BrowseComp, 64.0 on BrowseComp‑ZH) but provides no table, figure, or citation for these numbers. Add the missing experimental details (e.g., a table analogous to Table 1) or cite a source that documents these results.
- **[38200220becc]** The statement that SearchSwarm improves over its base by +14.2 average points on open‑ended deep‑research benchmarks lacks a clear baseline for comparison. Include the baseline scores (e.g., the performance of the un‑fine‑tuned base model) to substantiate the claimed improvement.
- **[efed8a04d1bc]** The submission does not include any source code, build scripts, or a public repository link for the SearchSwarm implementation, making reproducibility impossible.
- **[aa0680842b68]** No dependency manifest (e.g., requirements.txt, environment.yml, or Dockerfile) is provided; reviewers cannot verify that the model fine‑tuning pipeline can be re‑run from scratch.
- **[4c604d78f829]** The paper lacks a detailed description of the software architecture (module boundaries, class responsibilities, and data flow) beyond high‑level figures, preventing assessment of modularity and readability.
- **[66d5510f02cf]** There is no test suite or evaluation script included; without unit/integration tests the correctness of data filtering, harness enforcement, and training loops cannot be validated.
- **[469abc1ab742]** The appendix only contains prompt snippets; the actual code that implements the harness, sub‑agent spawning, and context‑window management is omitted, hindering code‑quality review.
- **[cf8fb296dce2]** Add an explicit open‑source license (e.g., Apache‑2.0 or MIT) for the released dataset, code, and model weights; include the license text in the repository and a clear statement in the paper.
- **[9b44eb59ca4d]** Provide a persistent identifier (DOI or Zenodo archive) for the SFT dataset and the model checkpoint, and reference the exact version (commit hash or tag) in the manuscript.
- **[0febb8ff60d4]** Audit all external URLs in the bibliography and appendix; replace any future‑dated or potentially transient links with archived versions (e.g., via archive.org) or include a note that the resource is expected to be released post‑publication.
- **[e09370779d70]** Describe the dataset schema (fields, data types, citation format) and detail how missing or malformed entries (e.g., hallucinated citations, incomplete tool‑call logs) are detected and handled during filtering.
- **[30ca783397c3]** Document the full provenance of the synthetic SFT data: random seeds, harness version, tool versions, and timestamps for each trajectory collection run, ideally in a reproducible script or notebook.
- **[8aa49da31068]** Add explicit axis labels (including units where appropriate) to all quantitative plots (e.g., Fig 1 sub‑figures, Fig 4 distribution plots) so readers can interpret the numbers without consulting the caption.
- **[d24a1e7f936f]** Replace or supplement the current color palette in pie charts (Fig 3) and bar charts with a color‑blind‑friendly scheme; include a legend that maps colors to benchmark names or tool categories.
- **[d7d37e606ab8]** Provide descriptive alt‑text for each \includegraphics command (e.g., using the \\caption* or \\pdfstringdefDisableCommands) to improve accessibility for screen‑reader users.
- **[dc8105ae3cfd]** Ensure that sub‑figure sizes are large enough to remain legible when printed at 1‑column width; consider increasing the width of the sub‑figures in Fig 1 and Fig 4 or providing a separate high‑resolution version.
- **[f22df00ca5ee]** Verify that every figure is explicitly referenced in the main text (e.g., Fig 4 is only mentioned in the Appendix; consider moving the most informative plots into the main body or summarising their key take‑aways).
- **[daa50388764c]** Define every acronym at first use (e.g., SFT, LR, ReAct, LLM, etc.) and replace obscure abbreviations like “A3B” with a plain description of the model size or architecture.
- **[43414132cc86]** Replace overloaded buzzwords such as “delegation intelligence”, “harness”, “core judgment retained”, and “citation‑grounded reporting” with clearer, more concrete phrasing (e.g., “system that decides when to delegate tasks”); avoid using the same term repeatedly across sections.
- **[f07c12a2f706]** Simplify tool‑name jargon (e.g., `call_sub_agent`, `search`, `visit`, `google_scholar`, `python`) by providing a brief plain‑language description the first time each appears, and consider using more intuitive names like “delegate task” or “web search”.
- **[2fb78fdea36a]** Reduce the density of technical shorthand in tables and figure captions (e.g., replace “30B‑A3B” with “30‑billion‑parameter model with architecture A3B”) to improve readability for non‑specialist readers.
- **[c7293c0174ba]** Avoid excessive use of the term “benchmark” without context; specify what each benchmark measures (e.g., “BrowseComp evaluates web‑browsing ability”) the first time it is mentioned.
- **[4f650628f737]** Clarify the meaning of symbols and notation in equations (e.g., define τ_t, a_t, o_t, H_T) in plain language before presenting the formal notation.
- **[88807d57322e]** Temper the claim that SearchSwarm achieves “state‑of‑the‑art” performance on open‑ended deep‑research benchmarks; the results in Table 5 show Dr Tulu outperforming SearchSwarm on two of four metrics.
- **[9008ed0dada7]** Provide a clear provenance for all baseline numbers (e.g., GPT‑5.2, Claude‑4.5, Gemini‑3.0) – many are from future‑dated announcements and lack publicly‑available evaluation data, which makes the comparative claims unverifiable.
- **[6684f2ac1ccd]** Add explicit limitation statements regarding the reliance on synthetic SFT data generated by the harness, and discuss how this may affect generalization to truly unseen domains.
- **[4139f280139e]** Report statistical significance (e.g., confidence intervals or p‑values) for the reported gains (e.g., the +10.0 improvement from the full harness in §4.2) to avoid overstating marginal differences.
- **[21b0fd7f759e]** Include a concrete URL or repository reference for the released code, data, and model weights mentioned in the Conclusion; the current manuscript provides no such link.
- **[475f01bd62ab]** Add a dedicated discussion of dual‑use risks, including how the released SearchSwarm model could be misused for large‑scale misinformation or automated generation of deceptive scientific claims, and outline concrete mitigation strategies (e.g., usage licenses, rate limits, monitoring).
- **[8902eafb149c]** Implement or at least describe a verification step for the inline citations generated by sub‑agents, ensuring that cited URLs actually contain the claimed information and are not fabricated or outdated.
- **[c53dfd8d7aab]** Provide a privacy and data‑handling statement clarifying how the system treats personal or copyrighted information encountered during web browsing, and describe safeguards (e.g., filtering of PII, respect for robots.txt) to prevent inadvertent data leakage.
- **[5b6dd254ef0b]** Provide statistical significance testing (e.g., confidence intervals or p‑values) for all reported benchmark scores in Table 1 (Sec 4.2) and Table 2 (Sec 4.6) to demonstrate that observed gains are not due to random variation.
- **[50a746961cd7]** Report the number of random seeds, training runs, and any variance (standard deviation or inter‑quartile range) for the main results; currently only a single point estimate is shown, which hampers assessment of reproducibility.
- **[355ba936d133]** Clarify the exact size of the SFT dataset (number of trajectories, total token count) and the proportion retained after filtering; without this, the claim of “high‑quality” data lacks quantitative backing.
- **[f79911f93722]** Explain how baseline models were evaluated under comparable conditions (e.g., whether context‑management was enabled for all baselines); the asterisk notation in Table 1 suggests inconsistent settings.
- **[4134f0683afd]** Include an ablation that controls for the effect of the harness versus simply increasing model capacity (e.g., fine‑tune a different 30B model without the harness on the same data) and report statistical differences.
- **[856a782b9d09]** Add a replication study or cross‑validation on a held‑out subset of the benchmarks to demonstrate that the reported improvements generalize beyond the specific test sets used.
- **[24ff9eca610f]** The manuscript reports point estimates (e.g., 68.1 on BrowseComp) without any measure of variability (standard deviation, confidence interval, or error bars). This makes it impossible to assess whether observed differences between SearchSwarm and baselines are statistically significant.
- **[a4d719e63818]** No statistical hypothesis tests (e.g., paired t‑test, Wilcoxon signed‑rank) are performed to support claims of superiority over other models, despite multiple benchmark comparisons. The risk of Type I error due to multiple comparisons is not addressed.
- **[82708f07009f]** The experimental setup lacks details on random seed handling, number of training runs, and whether results are averaged over multiple fine‑tuning runs. Reproducibility of the reported scores cannot be verified.
- **[baf181e69bb9]** The paper does not disclose the size of the evaluation sets (e.g., number of questions per benchmark) for each metric, nor does it provide per‑question score distributions. This omission hampers assessment of statistical power.
- **[aa3ae2333638]** Hyper‑parameter choices (learning rate schedule, batch size, temperature, top‑p) are listed, but there is no justification or sensitivity analysis to show robustness of the results to these settings.
- **[109038f7294b]** When reporting ablation results (e.g., +10.0 gain from full harness), the authors present a single aggregate number without indicating variance or statistical testing, making the claim of a ‘gain’ ambiguous.
- **[236f72ea5cc8]** The paper uses a single judge model (DeepSeek‑V4‑Flash) for all benchmark evaluations without discussing inter‑judge agreement or potential bias, and does not provide inter‑rater reliability metrics.
- **[7675425e7858]** Wrap the two tabular environments (e.g., the feature comparison table in Appendix e002) inside a proper \begin{table} … \end{table} block, add a descriptive \caption, and provide a \label for cross‑referencing.
- **[d5e8cb3cff1e]** Add the missing LaTeX packages required for the current markup: \usepackage{booktabs} for \toprule/\midrule, \usepackage{subcaption} for the subfigure environment, and \usepackage{amsmath,amssymb} for the displayed equations. Ensure these are loaded in the preamble.
- **[c36d0c4d4905]** Standardise citation commands: the manuscript mixes \citep, \citet, and bare \cite. Choose a single natbib style (e.g., author‑year) and apply it uniformly; replace any stray \cite{#1} with the appropriate command.
- **[7fa4c43fc96e]** For all tables (including Table 1 and Table 2), ensure column alignment is consistent and avoid overly wide columns that cause line‑overflow. Consider using the tabularx package with X columns or adjusting column widths.
- **[5cd941a64ceb]** Check figure placement specifiers: some figures use [t] while others have no specifier. Use a consistent placement option (e.g., [htbp]) and add \centering before \includegraphics for uniformity.
- **[c02d73ff5938]** In the Introduction (Sec 1, lines 1‑4), the opening sentence is overly long and contains a dangling modifier; split into two sentences and clarify the relationship between context windows and delegation.
- **[193720862b8c]** Throughout the manuscript, citations are attached without preceding space (e.g., "context windows\citep{jimenez2024swe}" in Sec 1); add a space before each citation for readability.
- **[cc791373661f]** The phrase "delegation intelligence" is introduced without definition; add a concise definition the first time it appears (Sec 1, line 9).
- **[234ce831ec38]** In Table 1 caption (Fig. ef{tab:main-results}), the asterisk notation (*) is not explained; include a footnote or legend describing what the asterisk denotes.
- **[023c4869ae7b]** Several sentences contain missing articles or plural‑singular mismatches, e.g., "SearchSwarm follows a main‑distributes, sub‑executes paradigm" (Sec 2, line 2). Revise to "SearchSwarm follows a main‑distribute, sub‑execute paradigm" or similar.
- **[4fa8464ceb06]** The use of hyphens and en‑dashes is inconsistent (e.g., "30B‑A3B" vs. "30B‑A3B"); standardize to en‑dash for ranges and hyphen for compound adjectives.
- **[9c6c5a9946d0]** In the Results section, the term "context‑management enabled" appears in a table footnote without explanation; add a brief description of what this setting entails.
- **[e48fd61295d2]** The appendix sections contain duplicated reference entries (e.g., multiple “[4]” entries) and inconsistent formatting; clean up duplicate IDs and ensure uniform bibliography style.
- **[2967edf709df]** Some figure captions are overly verbose (Fig. ef{fig:tool-usage}); consider shortening while retaining essential information.
- **[a32fdeb2e95a]** The conclusion (Sec 6) repeats phrases from the introduction; rephrase to provide a concise summary and future‑work outlook.
