---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/342
paper_authors:
  - Haowen Liu
  - Xirui Li
  - Shaoxiong Yao
  - Peng Shi
  - Tianyi Zhou
  - Jia-Bin Huang
  - Furong Huang
  - Jiayuan Mao
---

# Guava: An Effective and Universal Harness for Embodied Manipulation

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.18363
Paper authors (from arXiv): Haowen Liu, Xirui Li, Shaoxiong Yao, Peng Shi, Tianyi Zhou, Jia-Bin Huang, Furong Huang, Jiayuan Mao

Submitted by: github-actions[bot]

(Intake from human-submission issue #342.)

## Rejection rationale (2026-06-21)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[65f53db3de8e]** The manuscript cites a non‑existent “GPT‑5.4” model (citekey openai2026gpt54) multiple times as a frontier proprietary baseline, but this reference is absent from the bibliography and no public record of such a model exists. Replace this placeholder with a real, verifiable baseline (e.g., GPT‑4, Gemini‑Pro, or another published VLM) and provide the appropriate citation.
- **[2d7fe9e8532f]** Several claims about “performance comparable to frontier proprietary models” rely on the unsupported GPT‑5.4 baseline. After fixing the baseline, re‑evaluate the comparative results and update Table 1 and related discussion to reflect verifiable evidence.
- **[95b6c18b7c95]** The citation to “openai2026gpt54” is missing from the bibliography; add a proper entry if the work exists, or remove the reference entirely.
- **[48c9169ac5a6]** The statement that the harness “enables strong generalization to unseen objects, novel instructions, and long‑horizon tasks” is only supported by the authors’ own experimental tables. Provide statistical significance testing (e.g., confidence intervals) or additional ablations to substantiate the generalization claim.
- **[a6b8ddac430b]** Provide a public code repository containing the full implementation of the Guava harness, tool APIs, data generation engine, and training pipelines.
- **[0deb700d4154]** Add a detailed README with step‑by‑step instructions to reproduce the data collection (2K trajectories), supervised fine‑tuning, and GRPO reinforcement learning, including exact command‑line invocations.
- **[1876bb017b8b]** Specify all software dependencies (Python version, libraries, CUDA/cuDNN versions) in a requirements.txt or environment.yml file; consider providing a Dockerfile for containerised reproducibility.
- **[68681832eb29]** Modularise the codebase: separate modules for (a) tool definitions, (b) harness loop logic, (c) model inference wrappers, (d) training scripts, and (e) evaluation scripts. Each module should be <200 LOC and have a clear API.
- **[8ddc78d6a239]** Include unit tests for each tool (e.g., grasp, move, align) and for the ReAct‑style loop to verify correct request/response handling and error‑recovery pathways.
- **[5f4e2c6a9e3c]** Remove duplicate LaTeX package imports (e.g., multiple \usepackage{tcolorbox} and \usepackage{wrapfig}) and consolidate style definitions to improve maintainability of the manuscript source.
- **[09476c669b46]** Document random seeds and any stochastic components (scene randomisation, perturbation generation) used during data collection so that exact trajectories can be regenerated.
- **[cf19397bc05a]** Provide scripts to automatically generate the evaluation tables and figures (e.g., success‑rate CSV → LaTeX table, plot generation) to avoid manual transcription errors.
- **[83ea223aeb9a]** Add a dedicated Data and Code Availability statement that includes explicit URLs (with DOIs when possible) for the simulation dataset, the generated trajectory files, and any code repositories (e.g., the Guava harness, data‑generation engine, and training scripts).
- **[c6e7d8176ed2]** Specify the licensing terms for all released assets (simulation trajectories, model checkpoints, and source code). If the dataset is derived from RoboSuite, cite RoboSuite’s license and clarify whether any modifications are redistributed under a compatible license.
- **[73ee0c9d89e8]** Provide a schema description for the trajectory files (e.g., JSON fields for observations, tool calls, reasoning traces, and success flags) and document how missing or corrupted entries are detected and filtered during preprocessing.
- **[6566df316c47]** Include version identifiers (e.g., Git commit hashes or release tags) for the codebase used to generate the data and train the 4B model, so that reviewers can reproduce the exact experimental setup.
- **[b852ddf8e488]** Verify that all external URLs (project page, image assets, referenced tool implementations such as SAM3) are persistent; consider archiving them via Zenodo or adding DOI references to mitigate link‑rot.
- **[06602e6405e4]** Clarify the provenance of the 2K simulation trajectories: describe the random seeds, scene randomization parameters, and any post‑processing steps that could affect reproducibility.
- **[5d773fe8aff3]** State the data‑handling policy for privacy or safety‑critical information (e.g., real‑world RGB‑D recordings) and confirm that no personally identifiable information is included.
- **[ac2d6757a6af]** Add descriptive alt‑text for every figure (e.g., using the \includegraphics[alt=...] option or a surrounding \caption) to improve accessibility for screen‑reader users.
- **[aa64cb292e59]** Ensure that all quantitative plots (e.g., the three sub‑figures in Fig. 2 and the bar charts in Fig. 3, Fig. 4, Fig. 5) include clear axis labels, units, and tick marks; the current LaTeX source only supplies a caption without explicit axis titles.
- **[1a389a19de29]** Verify that the color palettes used in the plots are color‑blind friendly (e.g., avoid red/green pairs) and provide sufficient contrast when printed in grayscale; consider adding patterned fills or distinct line styles for critical series.
- **[cd681b8608a7]** For multi‑panel figures (e.g., Fig. 2, Fig. 3, Fig. 5), add panel labels (a), (b), (c) directly on the sub‑figures and reference them consistently in the caption to aid readers when the figure is reproduced at smaller scales.
- **[affdb7cfbc19]** Check that the resolution of raster images (e.g., realworld_qualitative.pdf, push_example.pdf) is high enough for print; low‑resolution PDFs can become blurry when the paper is printed in journal format.
- **[be72c0d6769a]** Include a brief description of the data shown in each plot within the caption (e.g., number of trials, confidence intervals) so that the figure can stand alone without requiring the reader to search the main text.
- **[241864830035]** Define all acronyms at first use (e.g., VLM, RL, GRPO, SFT, API, SAM3).
- **[0adb71c33c12]** Replace overly technical phrases with simpler alternatives (e.g., “large‑scale vision‑language data” → “large vision‑language datasets”).
- **[21dc416e1453]** Clarify the meaning of “frontier models” and replace with a more common term such as “state‑of‑the‑art proprietary models”.
- **[e35e5dd3231c]** Simplify compound nouns like “iterative perception‑reasoning‑action loops” to “repeated perception‑reasoning‑action cycles”.
- **[4ef8365c15d4]** Explain “semantic action abstractions” in plain language (e.g., “high‑level action abstractions”).
- **[18788a14f061]** Replace “multimodal observations” with “multiple sensor inputs” or “visual and textual observations”.
- **[6edb4e4608b8]** Avoid repetitive use of the term “harness” when a simpler phrase such as “framework” or “interface” would suffice.
- **[4b02b5eea89f]** In Section 3 (sec/03_method.tex), the paragraph introducing GRPO and RL does not define these terms; add brief definitions or references.
- **[581dde9d5cba]** In the abstract (sec/00_abstract.tex), the phrase “embodied tool‑use capabilities” can be rewritten as “robotic tool‑use abilities” for clarity.
- **[1473bfbee935]** The term “sim2real” appears without explanation; replace with “simulation‑to‑real transfer” or define the abbreviation.
- **[66891539ee05]** Clarify the description of the training pipeline: the paper calls it an “end‑to‑end training pipeline” while the vision encoder and aligner are frozen during fine‑tuning (see Sec. 4, paragraph “Training pipeline”). This creates a logical inconsistency between the claimed end‑to‑end nature and the actual training procedure.
- **[92a60f585662]** Correct the typo “Gauva” to “Guava” in Sec. 3 (first line) to avoid confusion about the system name.
- **[77f44effe5ae]** Provide a precise count of the number of tasks used for the ablation study in Sec. 3 (the text mentions six long‑horizon tasks, but Fig. 2 appears to evaluate more). Ensure the description matches the experimental setup.
- **[9afbd163fa21]** Temper the claim that Guava is a “universal” harness; the paper only evaluates a limited set of models (GPT‑5.4, Qwen‑3.5‑4B, Gemini‑3.1‑Pro, Claude‑Sonnet‑4.6, and a 2B variant). Add a discussion of this scope and avoid language suggesting applicability to all future models.
- **[5c363801ef45]** Provide a more balanced assessment of generalization. The manuscript highlights strong OOD performance, yet tasks such as *shell game* and *place all red objects in basket* show very low success (≤ 6.7 %). Include these failure cases in the discussion and refrain from stating “strong generalization” without qualifying the limitations.
- **[b2dc32dc6181]** Report statistical significance (e.g., confidence intervals or hypothesis tests) for the success‑rate comparisons in Tables 1 and 2. This will substantiate the claim that the 4B model matches or exceeds proprietary baselines rather than relying on point estimates from only 15 episodes per task.
- **[f0aaffd68ef3]** The manuscript lacks any discussion of safety measures, failure‑mode analysis, or mitigation strategies for the embodied robot when executing tool calls (e.g., grasp failures, unintended collisions). Add a dedicated safety section that outlines hardware‑level safeguards, software‑level verification of tool arguments, and emergency stop procedures.
- **[3b776c6620c9]** The paper does not address dual‑use risks of a model‑agnostic manipulation harness that could be repurposed for harmful or malicious tasks (e.g., weapon assembly, property damage). Include a risk‑assessment paragraph describing potential misuse scenarios and proposed access‑control or licensing mitigations.
- **[98cb95c53964]** No ethical review or IRB considerations are mentioned, but the system is intended for real‑world deployment with a physical robot. Clarify whether any human‑subject interaction (e.g., data collection from users, observation of humans) occurs and, if so, provide the appropriate consent/IRB statements.
- **[50b10af03d95]** The dataset used for fine‑tuning consists of simulated trajectories only, yet the paper reports real‑world experiments. Explain how the simulation‑to‑real transfer was validated for safety (e.g., collision‑checking, domain randomization) and whether any real‑world data containing personal information was collected.
- **[cfa2bf7be1e6]** Tool APIs such as `move(x,y,z)` and `rotate(angle, axis)` can generate unsafe robot motions if supplied with out‑of‑range parameters. Provide validation checks or bounded parameter ranges in the API description to prevent dangerous commands.
- **[86728fceab6f]** Provide per‑task confidence intervals or standard errors for the reported success rates (e.g., Table 1) and describe the random seed / episode selection procedure to allow assessment of statistical significance.
- **[55211c0595a9]** Include an ablation that controls for the number of trajectories used in the data‑generation engine (e.g., 1 K vs 2 K vs 5 K) to demonstrate that performance gains are not solely due to over‑fitting on a small dataset.
- **[77ed8664cd32]** Report the variance across runs for the RL fine‑tuning stage (e.g., multiple seeds for GRPO) to show that the observed improvements on long‑horizon tasks are reproducible and not a result of favorable random initialization.
- **[ede71c775e08]** Add statistical tests (e.g., paired bootstrap or permutation tests) when comparing Guava‑Agent‑4B against baselines to quantify the significance of the reported 5‑10 % improvements.
- **[969d05a283ec]** Clarify how failure cases were selected for the ‘recovery’ analysis and ensure that they are not cherry‑picked examples that overstate the model’s robustness.
- **[4780954ad3be]** Report variability (e.g., standard deviation or confidence intervals) for all success‑rate numbers in Tables 1 and 2; the current percentages lack any measure of statistical uncertainty.
- **[2efd0d8018ca]** Perform statistical significance testing (e.g., paired t‑test or non‑parametric test) when comparing Guava‑Agent‑4B against baselines, and report p‑values with appropriate multiple‑comparison correction (e.g., Bonferroni or Holm).
- **[949f7287e285]** Provide a power analysis or justification for the chosen number of evaluation episodes (15 per task) to ensure the reported differences are not due to sampling noise.
- **[ce0be9ffc921]** Specify random seeds and any stochasticity controls used during data generation, training (SFT and GRPO), and evaluation to enable exact reproducibility.
- **[78cd444624b9]** Include a description of how the sparse task‑success reward is defined and scaled in the GRPO stage; without this, the RL optimisation procedure cannot be independently verified.
- **[787e9e4ace35]** Remove duplicate package imports (e.g., `\usepackage{subcaption}`, `\usepackage{wrapfig}`, and multiple `\usepackage[most]{tcolorbox}`) to avoid compilation warnings and keep the preamble tidy.
- **[83e4b6f02f4d]** Correct the typo in the method section title (`\section{Gauva: Harnessing VLM for Embodied Manipulation}`) to match the paper title "Guava" for consistency.
- **[a30a24de6af7]** Ensure all figure environments place the `\caption{...}` command *after* the `\includegraphics` and *before* any `\label{...}` to follow standard LaTeX conventions.
- **[545bf0a0d029]** Standardize citation commands: use either `\citet`/`\citep` consistently throughout the manuscript instead of mixing with raw `\cite` or manual brackets.
- **[140b36f756a0]** In tables, replace manual `\thickhline` definitions with the `booktabs` commands (`\toprule`, `\midrule`, `\bottomrule`) and remove the custom `\thickhline` to improve visual consistency.
- **[89e526c6a2ed]** Wrap long paragraphs (e.g., the abstract and introduction) with explicit line breaks or `\par` to avoid overfull hboxes; consider using the `microtype` package for better justification.
- **[abac26282ce0]** Add missing `\centering` inside `figure*` and `table*` environments to guarantee proper horizontal alignment of wide figures/tables.
- **[32f61b7c53d1]** Verify that all cross‑reference macros (`\figref`, `\tabref`, `\secref`, etc.) are defined only once and used consistently; currently both `\def\figref` and `\newcommand{\figref}` coexist.
- **[01ffb8557db8]** Place the `\appendix` command before the appendix sections (currently `\beginappendix` is used, which is non‑standard). Replace with `\appendix` and ensure sections are numbered as A, B, …
- **[77d1df8f777a]** Remove stray spaces and empty lines inside macro definitions (e.g., extra spaces after `\newcommand{\promptplaceholder}[1]{\texttt{\{#1\}}}`) to keep the source clean.
- **[4fe861e194e5]** Remove duplicate package imports (e.g., tcolorbox, wrapfig) and consolidate them for cleaner preamble (see lines 5‑9 of main.tex).
- **[0c5f5cde5a4d]** Correct typographical errors such as "Gauva" (should be "Guava") in the Method section title (line 1 of sec/03_method.tex) and "sec:realted_word" (should be "sec:related_work") in the Related Work label.
- **[012fc7cbf7f7]** Standardize terminology: consistently use "Guava" throughout the manuscript; avoid mixed references like "Gauva" or "Guava" with different capitalizations.
- **[a82d72bc9cc8]** Improve sentence flow and reduce redundancy in the abstract and introduction (e.g., the phrase "strong potential for embodied agents" appears twice within two sentences; see sec/00_abstract.tex lines 1‑4).
- **[ac467cd7af47]** Fix grammatical issues such as missing articles, subject‑verb agreement, and misplaced commas (e.g., "Our method identifies three key ingredients for effective manipulation" – add "the" before "three"; see sec/01_introduction.tex line 23).
- **[0ce26c935619]** Revise figure captions for clarity and completeness; some captions lack context (e.g., Fig. 1 caption does not explain what the teal arrows represent).
- **[cf94444df3f4]** Ensure consistent citation style and spacing (e.g., missing space before year in some citations, inconsistent use of "~\citep" vs "\citep").
- **[d63b3c8a90fe]** Check and correct LaTeX macro definitions that are unused or duplicated (e.g., multiple definitions of \figref, \secref). Remove or consolidate to avoid confusion.
- **[6c0be3086b67]** Proofread the entire manuscript for punctuation errors, especially in lists and enumerations (e.g., missing commas after "e.g.," in several places).
- **[d56cfb366469]** Add a brief paragraph in the conclusion summarizing the main quantitative results to improve closure and readability.
