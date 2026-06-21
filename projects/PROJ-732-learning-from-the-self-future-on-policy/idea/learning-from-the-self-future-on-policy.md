---
field: linguistics
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/336
paper_authors:
  - Yifu Luo
  - Zeyu Chen
  - Haoyu Wang
  - Xinhao Hu
  - Yuxuan Zhang
  - Zhizhou Sha
  - Shiwei Liu
---

# Learning from the Self-future: On-policy Self-distillation for dLLMs

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.18195
Paper authors (from arXiv): Yifu Luo, Zeyu Chen, Haoyu Wang, Xinhao Hu, Yuxuan Zhang, Zhizhou Sha, Shiwei Liu

Submitted by: github-actions[bot]

(Intake from human-submission issue #336.)

## Rejection rationale (2026-06-21)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[8c19ecb209f3]** Replace the citation of Yang2025qwen3 in the statement about On‑policy Distillation (OPD) with a source that actually discusses OPD; Yang2025qwen3 is a model technical report and does not cover OPD methodology.
- **[71dbc515193c]** Verify that Li2026rethinking indeed addresses on‑policy distillation of LLMs; if it does not, substitute with a more appropriate reference.
- **[3ed16094b1a2]** The submission lacks any source code, build scripts, or environment specifications required to reproduce the experiments. Provide a complete code repository (e.g., on GitHub) containing the training, inference, and evaluation pipelines.
- **[e844d41f4fa5]** Include a `requirements.txt` or `environment.yml` that pins exact versions of all Python packages (e.g., torch, transformers, trl, flash-attention, accelerate, etc.) used in the experiments.
- **[dbc1873468bf]** Add a detailed README with step‑by‑step instructions to reproduce each experiment (data download, preprocessing, training hyper‑parameters, random seeds, hardware requirements, and evaluation commands).
- **[88bbad387b4f]** Structure the code into modular components (e.g., `models/`, `training/`, `evaluation/`, `utils/`) rather than a monolithic script, and ensure each module has clear docstrings and type hints.
- **[f1e686ad1809]** Provide unit tests (e.g., using pytest) for critical functions such as the self‑teacher construction, step‑level KL computation, and the input concatenation trick to catch regressions.
- **[5951cde1f71c]** Document the data preprocessing pipeline for each benchmark (GSM8K, MATH500, Countdown, Sudoku) and include scripts to generate the exact splits used in the paper.
- **[ea713cdc687c]** Expose configuration files (e.g., YAML or JSON) for all hyper‑parameters (learning rate, LoRA rank, retaining ratio, top‑k selection, pass@k, clipping threshold) so that experiments can be rerun without modifying code.
- **[cd6587e90c2d]** Add an explicit Data Availability and Licensing statement that lists the exact versions of all external datasets used (GSM8K, MATH500, Sudoku, Countdown) together with their licenses (e.g., CC‑BY‑4.0 for GSM8K). This should include URLs to the dataset releases and any required citation details.
- **[be8c7314e13e]** Specify the license under which the released code (https://github.com/xingzhejun/d-OPSD) is distributed (e.g., MIT, Apache‑2.0). Include a LICENSE file in the repository and reference it in the paper.
- **[0ced52756c4c]** Provide a precise version identifier (commit hash or release tag) for the code snapshot used in the experiments, and cite it in the manuscript to ensure reproducibility.
- **[526d6378e0a0]** Clarify how missing or incorrect generations are handled during training and evaluation (e.g., the threshold for Sudoku scores, the ‘correct only’ loss computation). Include a brief description of any data filtering or preprocessing steps applied to the raw datasets.
- **[98f2f496c7da]** Add persistent identifiers (DOI or arXiv IDs) for all external resources referenced (datasets, baseline codebases, RLVR implementations) to mitigate link‑rot risk. Where possible, archive the resources in a long‑term repository (e.g., Zenodo) and provide the archive URLs.
- **[d1218431b69c]** Include a reproducibility checklist that details the exact data splits (train/validation/test) and any random seeds used for sampling trajectories, especially for the pass@k strategy.
- **[8a71f5f8f253]** Add clear axis labels, units, and legends to all quantitative plots (Fig 1, Fig 2, Fig 3, Fig 4). Currently the captions mention performance or sample‑efficiency but the figures themselves lack any axis titles or tick‑mark explanations, making it impossible for readers to interpret the curves without consulting the text.
- **[0ae4102b59eb]** Provide descriptive alt‑text for each figure (e.g., via \caption[short]{...} or \includegraphics[alt=...]) to improve accessibility and to satisfy the paper‑submission guidelines.
- **[0353d842ced6]** Replace the current color palette with a color‑blind‑friendly scheme (e.g., use color‑blind safe palettes or add distinct line styles) and ensure that the colors used in the plots are distinguishable when printed in grayscale.
- **[947419c32c81]** Resize the wrap‑figure (Fig 1, Fig 2) so that the graphics fit comfortably within the column width and remain legible at the final print size; the current width of 0.6 \textwidth for a wrapfigure can cause the image to be squeezed and text to become unreadable.
- **[8bbdc3b46402]** Include a brief description of what each subplot or bar in the tables‑turned‑figures (e.g., Fig 2’s framework diagram) represents directly in the caption, rather than relying on the reader to infer from the surrounding paragraph.
- **[03a8dea60f40]** Verify that all figure references are correct (e.g., \Cref{fig1} appears before the figure is defined, and the label matches the caption). Some figures (e.g., Fig 4) are introduced in the text but the corresponding \label may be missing or mismatched.
- **[d67f6ab054e3]** Consider adding a high‑resolution version of the large PNGs (e.g., try1.png is >1 MB) or converting them to vector graphics (PDF/PGF) for sharper rendering in the final PDF.
- **[8478bcd7657f]** Replace repeatedly used abbreviations such as “OPSD”, “dLLM”, “RLVR”, “AR”, and “KL” with plain language on first mention or add brief parenthetical explanations.
- **[816631e9aa84]** Define “KL” (Kullback‑Leibler divergence) at its first appearance; many readers unfamiliar with information‑theoretic terms will be lost.
- **[298c3ed3a5e6]** Substitute “privileged information” with a clearer phrase like “extra context” or “additional guidance” throughout Sections 1‑3.
- **[8865f49dcda6]** Rephrase “dense token‑level supervision” and “dense step‑level supervision” to “rich token‑level guidance” and “stepwise guidance” to improve readability.
- **[4cf476504d2b]** The phrase “self‑future‑experience” (Section 3.1) is opaque; replace with “future self” or “future answer” for clarity.
- **[a84f50b3c8b1]** Avoid the jargon‑heavy term “policy collapse” (Section 4.5); use “training collapse” or “performance degradation” and briefly explain the phenomenon.
- **[66d3f3431da6]** The term “on‑policy nature” appears multiple times (e.g., Sections 1, 3.1, 3.3); simplify to “using its own generated data”.
- **[632d930e58e0]** Clarify “step‑level KL divergence” by adding a short description of what the KL is measuring at each denoising step.
- **[9d64e53e38a8]** The acronym “SFT” is introduced without a clear definition of the underlying method; add a brief description of “supervised fine‑tuning” when first used.
- **[39693c446195]** In Table 3 and related discussion, replace “sample efficiency” with “training efficiency” and explain why fewer optimization steps matter.
- **[b687e6f7028d]** The phrase “teacher‑specific privileged information” (Section 2) is redundant; simplify to “teacher’s extra context”.
- **[17298db0d8c8]** Throughout the manuscript, replace “autoregressive‑centric” with “focused on left‑to‑right models”.
- **[3f051b25d2ed]** The term “step‑level divergence supervision” is repeated; consider a single term like “stepwise divergence loss” and use it consistently.
- **[f13527889737]** Explain the abbreviation “LoRA” (Low‑Rank Adaptation) at its first mention in Appendix A.3.
- **[236262cd8bcb]** The phrase “model‑seeking behavior” vs. “model‑covering behavior” (Section 4.4) is jargon‑heavy; replace with “focuses on high‑probability predictions” and “covers a broader distribution”, respectively.
- **[539be4588aa2]** Revise the statement that d-OPSD “consistently outperforms” RLVR and SFT baselines to accurately reflect the results (e.g., d-OPSD underperforms RLVR on Math500 at sequence length 512).
- **[e50807e722d7]** Include statistical significance testing (e.g., confidence intervals or p‑values) for the reported performance gains to substantiate claims of superiority.
- **[2c726d7012e4]** Clarify the sample‑efficiency comparison methodology, ensuring that the reported 10 % step reduction accounts for identical compute budgets and rollout strategies across methods.
- **[8d4a28e18a11]** Add a dedicated discussion of dual‑use risks, explicitly acknowledging that improving reasoning and sample‑efficiency of diffusion LLMs may enable more capable malicious agents (e.g., automated phishing, disinformation, or code generation).
- **[57e43c1805dc]** Include concrete mitigation strategies (e.g., safety‑aligned fine‑tuning, refusal training, monitoring of harmful outputs) and outline any planned safety evaluations beyond the reasoning benchmarks.
- **[017828f22b5c]** Clarify data handling and privacy: confirm that all training data (GSM8K, MATH500, Sudoku, Countdown) are publicly available and contain no personally identifiable information; if any private data were used, provide IRB/IACUC approval details.
- **[bf74c3266115]** Discuss the observed policy‑collapse failure mode (Section 4.5) from a safety perspective, describing potential risks of sudden degradation in behavior and proposing safeguards (e.g., early‑stop criteria, checkpoint validation).
- **[076ddd8da210]** Provide an ethical statement regarding the intended use cases of d‑OPSD and any limitations on deployment, especially concerning high‑stakes applications.
- **[349fdf26692f]** The paper reports single-point performance numbers for each benchmark without any measure of variance (e.g., standard deviation across random seeds) or statistical significance testing. Add multiple training runs with different seeds and report mean ± std or confidence intervals to demonstrate that improvements are robust and not due to random chance.
- **[74e840c7c69a]** The experimental setup lacks a clear description of the size of the validation and test sets used for each reasoning task, as well as the number of examples sampled for the toy verification. Provide exact sample counts and ensure that the same splits are used across baselines to avoid data leakage.
- **[720c3c38ca6a]** Hyperparameter selection (e.g., retaining ratio ρ_teacher, top‑k selection, clipping threshold) appears to be tuned on the test set, and the best checkpoint is chosen based on a single evaluation point. Adopt a held‑out validation set and report performance on an untouched test set to prevent over‑fitting to the evaluation metric.
- **[9be81d107c38]** The comparison to RLVR baselines uses optimization‑step counts from the original papers, but does not control for differences in compute (e.g., batch size, GPU count) or training duration per step. Include a fair compute‑budget comparison (e.g., total FLOPs or wall‑clock time) to substantiate the claim of superior sample efficiency.
- **[b4eac29d28cc]** The failure‑mode analysis (policy collapse) is presented qualitatively with a single figure. Quantify the frequency and severity of collapse across runs, and explore mitigation strategies (e.g., regularization, early stopping) to assess the stability of d‑OPSD.
- **[f4976b52f57f]** The toy verification experiment reports Pass@k improvements but does not include statistical tests to confirm that the observed gains are significant. Add appropriate significance testing (e.g., paired t‑test) for these comparisons.
- **[430b0a00076e]** Provide measures of variability (e.g., standard deviation, confidence intervals) for all reported performance numbers in Tables 1–3 and the toy verification (Table 1). Without these, it is impossible to assess whether observed gains are statistically significant.
- **[26e3447b6ab4]** Report the number of random seeds or independent runs used for each experiment, and include the seed values or a statement that the same seed was used across baselines. This is essential for reproducibility of the statistical results.
- **[72d8d99f5325]** Conduct appropriate statistical significance tests (e.g., paired t‑test or bootstrap) when comparing d‑OPSD against RLVR and SFT baselines across the four reasoning tasks, and report p‑values. Adjust for multiple comparisons (e.g., Bonferroni or Holm) given the six metrics (four tasks × two sequence lengths).
- **[938d127ce4f6]** Clarify the sampling strategy for the pass@k experiments (Section 4.4.4). Report the variance of the pass@k estimates (e.g., using the standard error of a binomial proportion) to show the reliability of the reported improvements.
- **[823914dbdb93]** In the toy verification (Section 4.1, Table 1), include confidence intervals for the Pass@1 and Pass@8 scores at each retaining ratio, and describe the statistical test used to claim that the self‑teacher is ‘significantly better’ than the student.
- **[1369c5881bf0]** Document any data preprocessing steps that could affect the distribution of the evaluation metrics (e.g., filtering of incorrect answers, thresholding for Sudoku scores). Provide justification that these steps do not bias the statistical comparison.
- **[82d5095900b9]** Table labels (`\label{...}`) are placed inside the `tabular` environment (e.g., lines around 310‑320 for Table 2 and similar for other tables). Move each `\label` command to immediately follow the `\caption` (outside the `tabular`) to ensure proper referencing.
- **[789163437efe]** Duplicate package imports (`\usepackage{wrapfig}` and `\usepackage{booktabs}` appear twice). Remove the redundant `\usepackage` lines to keep the preamble clean.
- **[e2a4e091d34d]** In several `wraptable` environments, the `\caption` appears before the `\begin{tabular}` but the corresponding `\label` is placed after `\bottomrule` inside the `tabular`. Relocate the `\label` to directly follow the `\caption` (outside the `tabular`).
- **[1d455cf06145]** Consistent figure/table placement: some figures use `wrapfigure` with negative `\vspace` adjustments that may cause layout issues. Consider using standard `figure` environments with `[htbp]` placement and let LaTeX handle spacing.
- **[d1c48c7845a3]** The custom `\question`, `\twoquestion`, and `\multiquestion` tcolorbox definitions lack explicit `\label` handling. If you intend to reference these boxes, add `\label` after the `\end{tcolorbox}` and use `\ref` accordingly.
- **[9ae4535e2bb7]** The abstract contains several long, complex sentences that hinder readability (e.g., lines 31‑38). Break them into shorter sentences and clarify the main contribution early.
- **[d735cae44ef8]** In Section 1, the use of "On-policy distillation (OPD) \citep{...}, where a student model samples its own trajectories while a stronger teacher model provides dense token-level supervision, has recently emerged..." is a run‑on sentence. Re‑write for clearer subject‑verb structure.
- **[999d5d89a5d6]** Figure captions (e.g., Fig 1 and Fig 2) repeat information already described in the main text and contain informal phrasing like "our approach". Make captions self‑contained and more formal.
- **[39fc7a916658]** The LaTeX source includes duplicated package imports (e.g., `wrapfig`, `booktabs`, `xcolor` are loaded multiple times). Remove redundancies to improve maintainability.
- **[bfa1942ab1e9]** Several sections contain inconsistent terminology: "self‑future" vs. "self‑future‑experience" vs. "self‑future". Choose a single term and use it consistently throughout.
- **[d70a064ffddb]** The use of custom tcolorbox commands (`\question`, `\twoquestion`, `\multiquestion`) adds visual clutter in the PDF and interrupts the narrative flow. Consider moving these Q&A blocks to an appendix or simplifying their presentation.
- **[bd651a48b869]** Tables (e.g., Table 2, Table 3) have inconsistent formatting: some cells are highlighted with `\cellcolor{lightblue}` while others are not, and the caption style varies. Standardize table styling for a professional look.
- **[a7d495b10cbc]** The bibliography style `unsrtnat` is used but the reference list is not sorted by appearance in the text, leading to mismatches between citations and bibliography order.
- **[13f65e3959ef]** There are several typographical errors and missing spaces, such as "dLLMs" sometimes written as "dLLMs" without a space after a period, and "AR" sometimes written as "AR" without proper spacing. Run a spell‑check and proofread for such issues.
- **[ad26f2748d4b]** The conclusion section repeats earlier points verbatim (e.g., lines 720‑730). Summarize key findings concisely and avoid redundancy.
