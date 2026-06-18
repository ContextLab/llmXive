---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/319
paper_authors:
  - Xin Jin
  - Huanqia Cai
  - Zhen Li
  - Zechao Zhan
  - Dengyang Jiang
  - Aiming Hao
  - Yuming Jiang
  - Chunle Guo
  - Peng Gao
  - Ming-Ming Cheng
  - Steven C. H. Hoi
---

# Beyond Scalar Rewards by Internalizing Reasoning into Score Distributions

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.09076
Paper authors (from arXiv): Xin Jin, Huanqia Cai, Zhen Li, Zechao Zhan, Dengyang Jiang, Aiming Hao, Yuming Jiang, Chunle Guo, Peng Gao, Ming-Ming Cheng, Steven C. H. Hoi

Submitted by: github-actions[bot]

(Intake from human-submission issue #319.)

## Rejection rationale (2026-06-18)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[b328babc936b]** Verify all cited references and ensure they are marked as verified in the bibliography.
- **[2c9f1365276d]** Provide explicit details of hyperparameters, training schedules, and data preprocessing steps to enable reproducibility.
- **[a4b66a2c2448]** Clarify the exact procedure for decoding score distributions from the model outputs and how expectations are computed.
- **[7b76e85190e9]** Add a brief discussion of potential limitations, failure modes, and ethical considerations of the teacher‑student reward modeling framework.
- **[fabf34e06063]** Remove or replace the non‑existent package `duckuments` (line ~30 in main.tex) which causes compilation failure on a standard LaTeX installation.
- **[1c2158435793]** Provide the missing custom class file `llmxive.cls` referenced in the preamble of `main-llmxive.tex`; without it the document cannot be compiled.
- **[165e3b1e6b23]** Consolidate the massive block of macro definitions (lines 70‑400 in main-llmxive.tex and lines 80‑350 in math_commands.tex) into a separate, well‑documented style file to improve readability and maintainability.
- **[8270efab8182]** Add a minimal build script (e.g., a Makefile or a `requirements.txt`/`environment.yml`) that lists all required LaTeX packages and any custom dependencies, ensuring reproducibility from scratch.
- **[c108d5dd013f]** Introduce unit tests or compilation sanity checks (e.g., using `latexmk -pdf -interaction=nonstopmode`) that verify the document builds successfully on a fresh environment.
- **[d33e80eb027b]** Document the data preprocessing and model training pipelines (e.g., Python scripts, configuration files) that generated the results reported in the paper; currently no code is provided, making the experimental claims non‑reproducible.
- **[8dfb3c9e6ffa]** Provide a clear provenance statement for the annotation dataset (e.g., source of prompts, collection pipeline, date of collection) and include a data sheet describing its composition and intended use.
- **[68e64f071e8c]** Specify the licensing terms under which the annotation data and any derived evaluation set are released (or explicitly state that they are proprietary and unavailable), and include a link to the license text.
- **[9398bba5e2e7]** Describe the schema of the annotation records (fields such as prompt, image ID, dimension, rubric score, annotator ID, confidence) and any validation checks applied during collection.
- **[31fc359e568c]** Detail how missing or ambiguous annotations are handled beyond the simple drop‑the‑highest/lowest‑score rule (e.g., annotator disagreement thresholds, imputation strategies, or exclusion criteria).
- **[a60a14e879c4]** Introduce version control metadata for the dataset (e.g., version number, changelog, date of last update) and provide a persistent identifier (DOI or URL) to enable reproducibility.
- **[3fffe338139f]** Audit all external URLs (e.g., arXiv links, code repositories) for long‑term accessibility; consider archiving them via services like Zenodo or Internet Archive to mitigate link rot.
- **[f3d0ca1ff0f7]** Add explicit axis labels (including units) to all plots, e.g., training steps (iterations) on the x‑axis and human‑preference accuracy or reward score on the y‑axis.
- **[65cae8df26ae]** Replace or augment the current color scheme with a color‑blind‑friendly palette and ensure sufficient contrast between lines/curves and the background.
- **[8bc273dea404]** Provide concise alt‑text descriptions for each figure (e.g., using \caption* or \texorpdfstring) so that the visual content is accessible to screen readers.
- **[814cb99f1dde]** Increase the font size of tick labels and legends in multi‑subplot figures (Fig. 4, Fig. 5) to guarantee legibility when printed at 2‑column size.
- **[cad959a4e4c3]** In Fig. 4, include a legend that clearly differentiates “Parsing Text” vs “Score‑Distribution” reward computation methods; the current caption does not specify which curve corresponds to which method.
- **[016c4923d50a]** For the qualitative comparison figure (Fig. 6), ensure that the displayed images are of sufficient resolution for print and consider adding a small identifier (e.g., prompt number) underneath each pair.
- **[a0bcac23684b]** Verify that all figure references (e.g., \figref{fig:teaser}) point to the correct figure numbers after any reordering; inconsistencies can confuse readers.
- **[0f1a55cb7ceb]** Define every acronym at its first occurrence. Currently terms like VLM (vision‑language model), RL (reinforcement learning), OPD (on‑policy distillation), GRPO (Group‑Relative Policy Optimization), GDSO, RISD, SFT, and others appear without an explicit definition.
- **[3d3d2f38a122]** Replace or explain domain‑specific jargon such as “rubric‑aligned”, “score‑distribution”, “reasoning‑internalized”, “teacher‑student framework”, and “policy‑gradient” with clearer language or brief explanations for readers unfamiliar with reward‑modeling literature.
- **[f59cfdfe2c82]** In the abstract and introduction, avoid long compound sentences that pack multiple technical concepts. Split sentences to improve readability for non‑specialists.
- **[63375799a413]** The phrase “high‑quality scoring requires reasoning and uncertainty awareness” (Section 1) is vague; clarify what is meant by “reasoning” and “uncertainty awareness” or replace with concrete descriptions.
- **[38cf4e51c70b]** Explain abbreviations like “OPD” and “GRPO” when they are first introduced in Section 4.2 and 4.3; the current first mention assumes prior knowledge.
- **[10a4d5691feb]** The term “teacher” and “student” are used metaphorically throughout the paper. Add a short parenthetical clarification (e.g., “large model (teacher)” and “compact model (student)”) at first use.
- **[0f4010d1f98b]** Avoid using symbols such as “	abyes” and “	abno” in tables without caption explanations; these symbols are not self‑explanatory for a general audience.
- **[0d59e3df4bed]** The discussion of “score‑gap supervision” and the Bradley‑Terry model (Eq. 13) is dense. Provide a brief intuitive description of why matching score gaps matters, or move the technical details to an appendix.
- **[48b4bb284cc7]** In Section 5.2, the sentence “RewardDance shows a useful contrast on 9B…” assumes readers know the baseline; briefly restate what RewardDance is.
- **[5de56b29841b]** The “Good‑Same‑Bad (GSB)” metric (Eq. 23) is introduced without context. Add a short sentence describing its purpose before the formula.
- **[55ce30ec312d]** Replace the phrase “latent, reasoning‑conditioned distribution” (Section 3) with a clearer alternative such as “hidden distribution that depends on the model’s reasoning steps.”
- **[067b0678995e]** The term “policy‑gradient reward” appears multiple times; consider simplifying to “gradient‑based reward signal” or adding a footnote explaining the term.
- **[eaa82faff802]** Figures 1 and 2 contain dense captions with multiple references (e.g., “Left: accuracy curves… Right: final accuracy comparison…”). Break captions into bullet points or separate sentences for clarity.
- **[15cd344e3968]** The abstract uses the phrase “internalizing reasoning into score distributions.” This could be rephrased as “incorporating reasoning steps into the model’s predicted scores.”
- **[037366e55226]** The training objective does not explicitly tie the reasoning trace ρ to the predicted score distribution q(s|·,ρ). Consequently, it is unclear whether the teacher truly leverages reasoning to produce calibrated distributions, or if reasoning is merely generated but ignored. Add an ablation or analysis that measures the impact of the reasoning component on the final distribution.
- **[68ecca60e01a]** Equation (9) applies a cross‑entropy loss with a one‑hot target (the annotated bin), which contradicts the stated goal of modeling uncertainty via soft, neighboring‑bin probabilities. Clarify whether the loss should use a soft target distribution (e.g., label smoothing) and adjust the formulation accordingly.
- **[23c4a655bc26]** Table 1 lists the teacher’s inference efficiency as “Low” while also stating that the teacher uses reasoning. The paper should define what ‘Low’ means (e.g., latency, token count) and reconcile this with the claim that the teacher is deployed only for training, not inference.
- **[01329cf1155e]** The OPD baseline is described as requiring ~750 output tokens, yet the student model is said to output a single token. Explain how the student encodes a full score distribution with a single token (e.g., via token‑wise logits) to avoid confusion.
- **[5fb1fda3da17]** The manuscript claims that the teacher’s reasoning‑conditioned score distribution can be “effectively internalized” into a 9B student without providing a direct ablation that isolates the contribution of reasoning versus the KL distillation loss. Add an experiment that trains the student with only KL loss on the teacher’s scalar expectations (no distribution) or with a non‑reasoning teacher to substantiate the claim.
- **[3f7bc77f694c]** The paper states that the proposed framework “generalizes to all sequence‑to‑score tasks” (Section 7) despite only evaluating on text‑to‑image generation. This is an over‑generalization; either remove the claim or provide evidence on at least one additional modality (e.g., video or captioning).
- **[869497645444]** The authors report a “41.3 % net human‑preference improvement” (GSB) over the SFT baseline, yet the GSB metric is defined relative to a baseline that already includes human‑aligned fine‑tuning. The evaluation set (400 prompts) is small and may not reflect broader distributions. Clarify the statistical significance, confidence intervals, and whether the improvement holds across diverse datasets.
- **[b7ff0e4303bf]** The manuscript suggests that score‑distribution supervision “accelerates score‑scale calibration” without presenting a baseline where only pointwise scalar supervision is used. Include a comparison where the teacher is trained with only scalar rewards to verify that the distributional loss is responsible for the reported gains.
- **[885d08285c4e]** Section 4.2 claims that the teacher’s reasoning “helps decompose visual evidence, apply rubric criteria, and allocate probability mass across neighboring score bins,” yet no analysis of the reasoning traces is provided (e.g., qualitative examples, correlation with performance). Provide evidence that the reasoning actually influences the distribution rather than being ignored.
- **[156b4df24d66]** The manuscript does not describe any Institutional Review Board (IRB) or equivalent ethical review for the human annotation process (Section 2, lines 70‑95). Add a statement confirming that the annotation protocol was reviewed and approved by an IRB or ethics committee, and detail how annotator consent and compensation were handled.
- **[545e2b1b3624]** Potential dual‑use risks are not discussed. The reward model can be used to steer image generators toward higher aesthetic quality, which could be exploited to create more persuasive disinformation or deep‑fakes. Include a brief risk assessment and mitigation strategy (e.g., usage policies, watermarking, or model‑level safety filters).
- **[c7aae62704c8]** The data used for training and evaluation appear to be internally generated prompts and images, but the source of the underlying images (e.g., copyrighted datasets) is not disclosed. Clarify the provenance of the image data and ensure that any copyrighted material is used under appropriate licenses or fair‑use justification.
- **[6aca3f4280c3]** No analysis of bias or fairness is presented. Since visual preferences are subjective and culturally dependent, the rubric‑based scoring may reflect annotator bias. Add an evaluation of demographic diversity among annotators and discuss steps taken to mitigate systematic bias in the reward model.
- **[689703eda567]** The paper proposes deploying a compact student model for large‑scale scoring (Section 4). However, there is no discussion of privacy safeguards when the model is applied to user‑generated content. Include a statement on how personally identifiable information (PII) in images is handled, and whether any data retention or anonymization measures are in place.
- **[2bdb24b01bcb]** The reward‑guided fine‑tuning of diffusion models (Section 5) could amplify unsafe generation (e.g., violent or adult content) if the reward model does not penalize such content. Provide details on how the reward signal is constrained to avoid encouraging prohibited content.
- **[5de275ba83e9]** Provide explicit details on the size of the annotated dataset (number of prompts, images, and annotations per sample) and the split between training/validation/test sets to assess statistical power.
- **[7b70ad73e409]** Report inter‑annotator agreement metrics (e.g., Krippendorff’s α or Cohen’s κ) for the rubric‑based scores to demonstrate annotation reliability.
- **[ea952f681bce]** Include statistical significance testing (e.g., confidence intervals or hypothesis tests) for the reported gains in PLCC, SRCC, and human‑preference accuracy over baselines.
- **[1f40e4c70df2]** Clarify hyperparameter selection procedures for GDSO (group size G, λ_pt, λ_pw, α_pt, α_pw) and conduct sensitivity analyses to rule out over‑tuning or p‑hacking.
- **[460750d7bc3a]** Describe any data‑augmentation or filtering steps applied to the training data, and justify that the test set remains fully held‑out.
- **[58defb115369]** Provide variance or standard error estimates for the human‑preference accuracy and margin HPA metrics (e.g., bootstrap confidence intervals) to gauge result robustness.
- **[4e1468137e91]** Explain how the student model’s performance was evaluated across multiple random seeds or runs to ensure reproducibility of the reported improvements.
- **[7cb12f9445d8]** Supply details on the computational budget and training duration for both teacher (27 B) and student (9 B) models to contextualize the scalability claims.
- **[b48978213bcd]** Report confidence intervals or standard errors for each evaluation metric (PLCC, SRCC, HPA, margin HPA) to quantify uncertainty and enable statistical significance testing.
- **[56fd8c06dae8]** Conduct appropriate statistical significance tests (e.g., paired bootstrap, permutation tests) when comparing methods and clearly state p‑values or effect sizes.
- **[61ddb8ed315d]** Apply a multiple‑comparison correction (e.g., Bonferroni, Holm‑Šidák, or FDR) across the many pairwise method comparisons reported in Table 2 to control Type I error.
- **[c30f9b9442ff]** Provide details on random seeds, data splits, and any stochastic training procedures (e.g., group size G, number of iterations) to ensure reproducibility of the reported results.
- **[3947f953d7ca]** Include a brief discussion of the variance observed across multiple runs (if any) and justify the choice of a single best‑performing run per model size.
- **[5c5f9f715506]** Remove duplicated package imports (e.g., enumitem, colortbl, tabularx, algorithm, algpseudocode appear twice) and clean up unused packages such as `duckuments` which is a typo.
- **[ceb917bdc93a]** Standardize figure placement options: replace the mixture of `[!htbp]`, `[H]`, and `[t]` with a consistent style (e.g., `[htbp]` for all figures) and ensure figures are placed after their first reference.
- **[5f9552a8ba52]** Move all `\caption{...}` commands to appear before `\label{...}` for tables and figures to follow the usual LaTeX convention (caption then label).
- **[9330987f2cca]** Break overly long lines (especially in the abstract, section headings, and long equations) to stay within an 80‑character limit, improving readability and version‑control diffs.
- **[0a6b6edb1a80]** Add missing `\centering` before tables (e.g., Table 1) to ensure consistent horizontal alignment; currently the table relies on manual `\resizebox` without explicit centering.
- **[8b7150b0e35a]** Consolidate duplicate `\makeatletter` / `\makeatother` blocks (they appear in both the wrapper and the original preamble) to avoid redefinition warnings.
- **[25c0e3d7a7bd]** Correct the typo `\usepackage{duckuments}` (likely intended to be `\usepackage{document}` or should be removed) to prevent compilation errors.
- **[eadc3e31d139]** Ensure consistent citation style: add a space after commas in `\cite{...}` commands and use `natbib`’s author‑year format consistently throughout.
- **[6625b658b8f5]** Place all math definitions (e.g., `\newcommand{\figref}[1]{figure~\ref{#1}}`) in a separate style file or before `\begin{document}` to keep the main body clean and avoid accidental redefinition.
- **[1f0c5d93a4c9]** Remove the redundant `main.tex` file from the submission bundle or clearly indicate which file is the primary entry point; having two `\documentclass` declarations can cause confusion.
- **[84c4477cac69]** Add a newline after each `\section{}` command to separate it from the following paragraph, improving LaTeX source readability.
- **[635a1d0337e3]** Check that all figure files referenced (e.g., `images/annotation.pdf`) exist in the repository and that their extensions match the actual files (PDF vs. PNG) to avoid missing‑figure warnings.
- **[4fa5885d76ae]** Several sentences are overly long and contain multiple clauses, making them hard to follow (e.g., the first paragraph of the Introduction and the description of Group-wise Direct Score Optimization). Consider breaking them into shorter, clearer sentences.
- **[6ce11d237add]** Inconsistent terminology for the teacher and student models (e.g., sometimes referred to as "teacher", "large VLM", or "reasoning-based teacher") leads to ambiguity. Standardize the naming throughout.
- **[81b1788e3a62]** Figure and table references are sometimes mismatched or missing (e.g., "Figref{fig:annotation}" appears before the figure is introduced, and some tables lack proper captions). Ensure all cross-references are correct and captions are complete.
- **[fd5861b0658a]** The use of LaTeX macros (e.g., \tabyes, \tabno) in the main text creates visual clutter and can be confusing for readers unfamiliar with the definitions. Replace them with plain text equivalents where appropriate.
- **[9bdeb3923a0a]** Repeated paragraphs appear in both the llmxive wrapper and the original main.tex (e.g., the abstract and introduction are duplicated). Remove redundancy to avoid confusing the reader.
- **[aa36a081ae3a]** There are several grammatical errors and missing articles (e.g., "Reward models are a key component of post‑training, where they provide the preference signals used for model selection" should be "Reward models are a key component of post‑training, providing the preference signals used for model selection"). Proofread for subject‑verb agreement and article usage.
- **[65d0c69771ef]** Inconsistent citation formatting (some citations appear as "~\cite{...}" while others are embedded in text with "\citep{...}") disrupts the flow. Adopt a single citation style.
- **[52317d0384e7]** The notation for distributions and expectations (e.g., \mu_\theta, q_\theta) is introduced without sufficient explanation, and the same symbols are reused for different concepts in later sections, causing potential confusion.
- **[0b76c0321b2c]** The abstract contains a long list of contributions separated by commas; reformat into a bullet list or separate sentences for better readability.
- **[7e340df2e629]** The tables use \resizebox and \textcolor commands that may not render correctly in all formats; consider simplifying the table layout for clarity.
- **[6863e9668c25]** The method section mixes algorithmic pseudocode with dense mathematical formulas without intermediate explanations, which can be hard for readers not familiar with the specific RL terminology. Add brief intuitive descriptions for each equation.
- **[5ec750b58745]** Some sections contain placeholder text (e.g., "\lipsum") that should be removed before final submission.
- **[5d40b78adcac]** The conclusion repeats earlier points verbatim; condense and focus on future directions instead of restating results.
