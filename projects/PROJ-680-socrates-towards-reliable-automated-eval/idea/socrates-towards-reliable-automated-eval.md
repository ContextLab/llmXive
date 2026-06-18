---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/292
paper_authors:
  - Taewon Yun
  - Hyeonseong Park
  - Jeonghwan Choi
  - Hayoon Park
  - Yeeun Choi
  - Hwanjun Song
---

# SoCRATES: Towards Reliable Automated Evaluation of Proactive LLM Mediation across Domains and Socio-cognitive Variations

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.05563
Paper authors (from arXiv): Taewon Yun, Hyeonseong Park, Jeonghwan Choi, Hayoon Park, Yeeun Choi, Hwanjun Song

Submitted by: github-actions[bot]

(Intake from human-submission issue #292.)

## Rejection rationale (2026-06-18)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[03ed75dc407c]** Verify that every citation listed in the bibliography has a corresponding entry with verification_status: verified; add missing references or correct any mismatches.
- **[20519fbe4e15]** Provide a concise description of how the topic‑localized evaluator’s prompts are constructed (e.g., exact prompt text) and include a small example dialogue with annotated scores to improve reproducibility.
- **[4086927374aa]** Clarify the statistical significance of the reported Pearson correlations (e.g., confidence intervals, p‑values) and include a brief discussion of potential variance across runs.
- **[9597906fbfa0]** Add a short paragraph in the Limitations section discussing the impact of evaluating only English‑language dialogues on cultural bias findings.
- **[6669696d8100]** Include a publicly accessible code repository (e.g., GitHub) containing all scripts used for scenario generation, simulation, mediator prompting, and the topic‑localized evaluator. The repository should have a clear README, dependency list (requirements.txt or environment.yml), and instructions to reproduce the full benchmark from scratch.
- **[259a140cfc4d]** Structure the code into logical modules (e.g., `scenario_curation/`, `simulation/`, `evaluation/`, `metrics/`) rather than monolithic scripts. Each module should expose a clean API and be documented with docstrings.
- **[eb97bcb1635c]** Add unit and integration tests for core components such as the scenario‑curation pipeline, the persona‑intensity scaler, and the evaluator scoring function. Tests should be runnable via a standard framework (e.g., pytest) and be included in CI.
- **[a4170734dbdd]** Provide version‑pinned dependencies and a reproducibility script (e.g., `run_all.sh` or a Makefile) that automates the end‑to‑end pipeline, including model checkpoint downloads, prompt execution, and metric aggregation.
- **[e8a8fe862ee4]** Add a clear Data Availability statement that includes a persistent URL (e.g., Zenodo DOI) for the generated scenarios, prompt templates, and evaluation scripts.
- **[8597abc3e967]** Specify an open-source license (e.g., CC‑BY‑4.0 for data, MIT for code) for all artifacts and include the license text in the repository.
- **[19d808b86b6d]** Provide a formal schema (e.g., JSON Schema) for the scenario objects (background, parties, topics, weights) and publish it alongside the data.
- **[e6de92714327]** Document versioning practices (git tag/commit hash) for the benchmark release and ensure future updates are backward‑compatible.
- **[e94425ccdc12]** Archive all external URLs (e.g., the project page https://disl-lab.github.io/SoCRATES) using a web archiving service (Internet Archive) and include the archived links to prevent link rot.
- **[bbaadfe6a340]** Add descriptive alt‑text for every figure (e.g., via \caption[Alt‑text]{...}) to improve accessibility for screen‑readers.
- **[8edba8e9be73]** Ensure all quantitative figures (radar chart, component shift, intervention comparison, trend comparison) have clearly labeled axes with units where applicable (e.g., “Consensus Gain (%)”, “Turn Index”, “Intervention Effectiveness (%)”).
- **[6b2eff1fa3ce]** Replace or adjust color schemes in the radar and component‑shift figures to be color‑blind friendly (e.g., avoid red/green pairs, use patterns or distinct hues).
- **[1b5e6dae635a]** Increase line widths and marker sizes in the multi‑panel plots so they remain legible when printed at journal column width.
- **[bde5bf106f2d]** Move the annotation‑template figures (figure_simulation_fidelity.pdf, figure_agreement_score.pdf) to an appendix or supplemental material, as they are not primary experimental results.
- **[219b4f2ade9a]** Check that all figure captions fully explain the content, including what each sub‑panel (a‑c) represents and the meaning of any shaded regions or error bars.
- **[2460e73fa1f1]** Define every acronym (e.g., LLM, GPT‑5.4, DeepSeek‑V3.2, Qwen3‑235B) at first appearance; currently many appear without definition (e.g., line 12 in the abstract, line 45 in Section 3).
- **[63d704e32dbc]** Replace or explain dense jargon such as “topic‑localized evaluator”, “socio‑cognitive axes”, “strategic posture”, and “intervention timeliness” with plain‑language equivalents or brief parenthetical definitions (e.g., Section 1, lines 30‑35).
- **[8675be7ec3c7]** Introduce a concise glossary of specialized terms and abbreviations (e.g., “Proactive mediator”, “Consensus Gain”, “Intervention Effectiveness”) to aid non‑specialist readers.
- **[22ef3cf02efc]** Avoid overuse of capitalised buzzwords (e.g., “Proactive LLM Mediation”, “Agentic Scenario Curation”) that do not add technical meaning; rephrase to simpler language (see Section 3.2, lines 78‑85).
- **[5a56074db213]** When referring to model names, consider adding a short description of their nature (open‑source vs. proprietary) the first time they are mentioned, rather than assuming the reader knows each model’s provenance (Section 4, lines 110‑120).
- **[2cd9624979e7]** Clarify the provenance and anonymization procedures for the real‑world conflict seeds used in the agentic scenario curation pipeline (Section 3.2). Provide evidence that no personally identifiable information (PII) or copyrighted text remains, and obtain IRB/ethics board approval if the source material involved human subjects.
- **[ba8576730bf9]** Add a systematic bias analysis of the topic‑localized evaluator and mediator performance across the three cultural identities (US, KR, CN). Report whether the reported cultural bias (e.g., performance drop for non‑US cultures) is statistically significant and discuss mitigation strategies.
- **[d5001d044b84]** Document the informed consent process for crowdworkers and graduate annotators, including the compensation rates, the nature of the annotation tasks, and any de‑identification steps applied to the data they labeled (Sections 5 and 6).
- **[95b13bca7af6]** Discuss potential dual‑use risks of releasing a benchmark that enables rapid development of proactive LLM mediators, especially the possibility of malicious actors deploying such mediators to steer negotiations or exploit cultural biases.
- **[193f4e593a99]** Provide a clear statement on the intended deployment scope of the benchmark (research‑only vs. real‑world use) and outline safeguards (e.g., licensing restrictions, usage guidelines) to prevent harmful applications.
- **[961bea97f6c9]** The scenario curation pipeline relies on LLM‑generated recasts (GPT‑5.4) of web‑sourced seeds. This may introduce a systematic bias toward conflict structures that LLMs find easy to model, limiting the ecological validity of the benchmark. Add a human‑verified subset of scenarios (or a fully human‑authored baseline) and report comparative performance to demonstrate that results are not an artifact of the generation process.
- **[b668e351a3f1]** The Consensus Gain metric divides by (1 − S_unmed), which can become unstable when the unmediated baseline approaches 1. Provide a sensitivity analysis (e.g., reporting variance or confidence intervals for gains in high‑baseline cases) and consider alternative normalizations to ensure the metric does not artificially inflate differences.
- **[a70a02590359]** All reported performance numbers are means without accompanying confidence intervals or statistical tests for differences across mediators, axes, or domains. Include standard errors, bootstrap confidence intervals, or appropriate hypothesis tests to allow assessment of the robustness of observed gaps.
- **[ba34e20f79d8]** Provide confidence intervals (e.g., 95% CI) for all reported Pearson correlations (r=0.823, 0.801, etc.) and for mean consensus‑gain values across mediators and conditions.
- **[f8f156ee9384]** Clarify the statistical testing framework used to compare mediators (e.g., ANOVA, mixed‑effects models) and report corresponding p‑values, effect sizes, and multiple‑comparison corrections (e.g., Bonferroni, Holm).
- **[f544eaa9c337]** Specify the assumptions underlying Pearson correlation (linearity, normality) and, if violated, present alternative non‑parametric analyses (Spearman’s ρ) or transform the data.
- **[7a23e1eab332]** Report the variance (standard deviation or standard error) for consensus‑gain, intervention timeliness, and effectiveness for each mediator; include statistical tests for differences between proprietary and open‑source models.
- **[6eb4c8f9a87e]** Detail the random seeds, temperature settings, and any stochastic sampling procedures used in scenario generation, simulation, and evaluation to enable exact replication.
- **[0cc877592085]** Address the handling of edge cases in the Consensus Gain formula (division by zero when S_unmed=1) and justify the alternative reporting method.
- **[6ec253b6c945]** Explain how Krippendorff’s α values were computed (e.g., number of annotators, bootstrap CI) and provide confidence intervals for these reliability metrics.
- **[880e1fcd37ab]** Consider evaluating inter‑rater reliability for the automatic evaluator by using multiple LLM backbones and reporting agreement statistics across them.
- **[837263601044]** The manuscript contains duplicate top‑level sections (e.g., two separate \section{Introduction} blocks with the same label sec:introduction). Merge or rename them to maintain a clear hierarchical structure.
- **[8b568fe27199]** Several custom column types (L, X) are used in tables (e.g., \begin{tabular}{|L{1.7cm}|X{2cm}|X{1.9cm}|}) without loading the required packages (tabularx, array). Add \usepackage{tabularx,array} or replace with standard column specifiers.
- **[adc8f32aa1d0]** Citation commands \citep and \citet appear throughout, but the preamble does not load a citation package such as natbib or biblatex. Include \usepackage{natbib} (or appropriate biblatex setup) to avoid undefined‑command errors.
- **[5aa968e4fb25]** The symbols \cmark and \xmark are used in tables but no package (e.g., pifont or dingbat) defines them. Add \usepackage{pifont} and define \newcommand{\cmark}{\ding{51}} and \newcommand{\xmark}{\ding{55}} or replace with textual markers.
- **[353ab17486a5]** Environments like \begin{promptbox}{...} and \begin{wraptable}{r}{0.5\textwidth} are employed without being defined in the preamble or via a package. Either define these environments or replace them with standard LaTeX constructs (e.g., \begin{figure}, \begin{table}).
- **[a9b1e93dc41f]** The document uses \url, \href, and colored links but does not load the hyperref package. Insert \usepackage{hyperref} (preferably after all other packages) to ensure proper link handling.
- **[72c0491fe9db]** Tables that rely on \toprule, \midrule, \bottomrule (e.g., tabular inside table* environments) require the booktabs package, which is not currently imported. Add \usepackage{booktabs}.
- **[c8203e3c00b7]** The tcolorbox environment is used for the title block, but the required package (tcolorbox) and color definitions (absgray, metablue) are not declared. Include \usepackage{tcolorbox,xcolor} and define the colors or replace with standard box formatting.
- **[24ce7b6eecf5]** Figure captions are correctly placed after \includegraphics, but some figures (e.g., Figure~\ref{fig:trend}) are referenced before the figure environment appears, which can cause LaTeX warnings. Reorder or use \FloatBarrier from the placeins package to control placement.
- **[1de71d24ad7b]** Line wrapping in the source code shows excessively long lines (e.g., long author blocks and paragraph texts). Consider breaking lines at ~80 characters for readability and to avoid overfull \hbox warnings.
- **[2880d684010d]** Simplify overly long sentences in the Introduction (e.g., the first paragraph of Sec 1 mixes multiple clauses without commas, making it hard to follow).
- **[6ac5a8c5b916]** Ensure consistent terminology for the benchmark name; both “\algname{}” and “SoCRATES” appear interchangeably without clear definition, leading to confusion.
- **[7d2a5dfd7798]** Correct grammatical errors such as missing articles and subject‑verb agreement (e.g., “The evaluator attains Pearson $r=0.82$ with human experts, more than doubling the per‑turn baseline.” – add “the” before “per‑turn baseline”).
- **[2208c58e2518]** Improve figure caption clarity; many captions (e.g., Fig. 2, Fig. 3) repeat the overview description without highlighting what the specific visual conveys.
- **[d713143aa9c2]** Standardize citation style; the manuscript mixes “\citep{...}” and “\citet{...}” inconsistently, and some citations lack proper spacing.
- **[3ae4478844b0]** Remove redundant sections – the paper contains two almost identical “Introduction” blocks (Sec 1 and e002) which should be merged.
