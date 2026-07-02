# Automated-review action items — Self-Distilled Agentic Reinforcement Learning

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer — verdict: major_revision_writing

- **[writing]** Resolve LaTeX compilation failure: The document imports 'colm2026_conference' which is missing from the source tree, causing a fatal error. Additionally, 'graphicx' and 'booktabs' are imported multiple times. Remove duplicates and provide the missing class file or switch to a standard conference template (e.g., NeurIPS/ICLR) to ensure the PDF compiles.
- **[writing]** Clean up the Abstract: The abstract currently contains two nearly identical paragraphs describing the method and results. Merge these into a single, cohesive paragraph to meet standard conference length and readability requirements.
- **[writing]** Complete Bibliography Verification: The citation list shows 'arxiv: 2605.15155' as 'unreachable' (likely a self-reference or placeholder error) and several other entries lack verification status. Ensure all citations are valid, accessible, and marked as 'verified' before resubmission.
- **[writing]** Fix Figure References: The text references 'Figure 1' (teaser) and 'Figure 2' (instability) but the LaTeX code uses 'figure' environments that may not render correctly without the missing template or proper float placement. Ensure all figures are correctly included and captions are distinct.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Abstract claims +10.2% WebShop-Acc gain for 7B. Table 1 confirms Qwen2.5-7B gain is +10.2 (82.8 vs 72.6). However, Qwen3-1.7B gain is +20.3. Clarify if +10.2% applies only to 7B or if the text implies uniform gains.
- **[science]** Section 3.1 attributes GRPO+OPSD degradation on Qwen3-1.7B to 'unbounded distillation gradients'. While the performance drop (32.0 vs 46.1) is correct, no gradient norm evidence is provided. Soften to 'likely due to' or add gradient analysis.
- **[fatal]** Section 3.1 claims Skill-GRPO shows a 'massive performance drop when tested without skills (60.2 vs 80.5)'. Table 1 shows Skill-GRPO (with skills) is 60.2 and Skill-GRPO* (without) is 80.5. The text implies 60.2 is the 'without' score, which is false. Performance actually improves without skills. This contradicts the 'internalization' argument and misrepresents the data.
- **[writing]** Section 3.3 claims Random Retrieval yields 'notable gains' of +1.0 on WebShop-Acc. Table 2 confirms +1.0 (73.6 vs 72.6). While numerically correct, 'notable' is subjective for such a small margin. Ensure consistency in describing small gains.

## paper_reviewer_code_quality_paper — verdict: minor_revision

- **[writing]** The LaTeX source contains duplicate package imports (e.g., \usepackage{booktabs} and \usepackage{graphicx} appear twice). While not fatal, this indicates poor dependency hygiene and should be cleaned to ensure reproducibility and reduce compilation warnings.
- **[writing]** The file includes a commented-out geometry package warning and manual margin adjustments (\addtolength) that conflict with the conference template. This risks template violation and should be resolved by strictly adhering to the colm2026_conference class without manual geometry overrides.
- **[writing]** The code quality of the LaTeX source is compromised by the presence of multiple \usepackage{graphicx} and \usepackage{booktabs} declarations. Consolidate these into a single preamble block to improve readability and maintainability.

## paper_reviewer_data_quality_paper — verdict: full_revision

- **[science]** The paper claims to use real benchmarks (ALFWorld, WebShop, Search-QA) but provides no provenance for the specific data splits, seed lists, or retrieval corpora (SkillBank). Section 'Implementation Details' cites external papers for splits but does not explicitly state the version or commit hash of the datasets used. Without this, the results cannot be reproduced or verified against link rot.
- **[science]** The 'SkillBank' source is cited as 'SkillRL' but no direct link, version, or license is provided for the skill library itself. If the skill files are not publicly available or have changed since the cited paper, the 'Random Retrieval' and 'UCB Retrieval' experiments become irreproducible. The paper must include a manifest or hash of the exact skill files used.
- **[fatal]** The paper references 'Qwen3' models (e.g., Qwen3-1.7B, Qwen3-Instruct) which do not currently exist in public repositories (as of the current date). If these are internal or future models, the data provenance is opaque. If they are placeholders for Qwen2.5, this is a critical data fabrication/misrepresentation issue. The specific model weights and their public availability must be clarified.
- **[science]** The 'Random Retrieval' baseline relies on a specific skill library structure. The paper does not define the schema of the skill files (e.g., JSON, text, specific fields) or how 'random' selection is implemented (uniform over files? over tasks?). This ambiguity prevents the reproduction of the robustness analysis in Table 2.

## paper_reviewer_figure_critic — verdict: minor_revision

- **[writing]** The paper contains a rich set of figures that effectively visualize the proposed SDAR framework and its training dynamics. However, several figures suffer from legibility issues and missing metadata that hinder immediate comprehension, particularly in a print context. Clarity and Labeling: Figure 1 (sdar_teaser.pdf) is the primary visual hook but its caption is confusing. It references "(a)" and "(b)" without clear visual demarcation in the provided source context. If the figure is a single comp

## paper_reviewer_jargon_police — verdict: full_revision

- **[science]** The paper is heavily laden with domain-specific jargon that significantly raises the barrier to entry for non-specialist readers, particularly those in adjacent fields like general NLP or software engineering. The Abstract and Introduction are dense with acronyms and technical phrases that are not defined upon first use. Specifically, the term "OPSD" is introduced in the Abstract but "OPD" appears in the Introduction without a clear link or definition, confusing the reader about whether these ar

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a logically coherent framework for combining RL and distillation, but several specific claims suffer from internal inconsistencies or insufficient causal justification. First, there is a direct numerical contradiction in the Abstract versus the Main Results section. The Abstract states: "+10.2% on WebShop-Acc". However, the "Main Results" text explicitly attributes a "+4.7%" gain to the 7B model (82.8 vs 72.6 is +10.2, but 68.0 vs 63.3 is +4.7). The table confirms the 7B gain

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The paper makes several strong claims regarding the consistency and robustness of the proposed SDAR method that slightly exceed the granularity of the provided evidence. First, the abstract and introduction assert that SDAR "consistently outperforms hybrid RL–OPSD baselines across all model scales." While the aggregate averages in Table 1 support a general improvement, the claim of "consistent" outperformance is contradicted by specific sub-task results. For instance, on the Qwen2.5-7B model in

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper relies on a 'SkillBank' for privileged context (Sec 2.1) but does not disclose the data provenance, licensing, or safety audit of its contents. If the bank contains toxic or biased data, the distillation process may encode these harms. A statement on data provenance and safety filtering is required.
- **[writing]** The gating mechanism attenuates gradients when the teacher-student gap is negative (Sec 2.2). This could inadvertently suppress learning signals when the teacher correctly identifies a harmful action as suboptimal, potentially shielding the model from safety corrections. Analyze this risk.
- **[writing]** The method internalizes agentic skills for inference without retrieval (Sec 4.1). The paper lacks a discussion on the dual-use risk of these internalized behaviors being repurposed for malicious automation (e.g., phishing, social engineering) in real-world deployments.

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The paper claims 'extensive experiments' across Qwen2.5/3 families but provides no statistical significance testing (e.g., t-tests, confidence intervals) for the reported gains (e.g., +9.4% on ALFWorld). Without variance estimates or multiple seeds, these point estimates are insufficient to rule out random fluctuation, especially given the small number of reported runs (implied single run per setting).
- **[science]** The robustness analysis (Table 2) claims 'graceful degradation' with random retrieval, yet the baseline 'w/o OPSD' is a single point. The paper fails to report the variance of the baseline or the proposed method across different random seeds for the retrieval noise experiment, making the 'robustness' claim statistically unsupported.
- **[science]** The ablation study on hyperparameters (Figures 4-6) sweeps $\lambda$ and $eta$ but does not report the standard deviation of performance across seeds for these ablations. Given the sensitivity of RL training, a single run per hyperparameter setting is insufficient to validate the claimed 'optimal' values.
- **[science]** The claim that 'naive GRPO+OPSD degrades severely' (Section 4.1) is supported by a single data point (32.0 vs 46.1). The paper must provide error bars or results from multiple independent training runs to confirm this instability is systematic and not an artifact of a specific random seed or initialization.

## paper_reviewer_statistical_analysis — verdict: full_revision

- **[science]** The paper reports point estimates (e.g., +9.4% on ALFWorld) without any measure of statistical uncertainty. For all main results in Table 1 and ablation studies, report standard deviations or 95% confidence intervals derived from multiple independent runs (e.g., 3-5 seeds) to distinguish signal from noise.
- **[science]** The robustness analysis in Table 2 (retrieval strategies) presents single-run results. Given the high variance inherent in RL training, a single run is insufficient to claim "graceful degradation." Re-run experiments with multiple seeds and report mean ± std dev to validate the statistical significance of the differences between retrieval methods.
- **[science]** The ablation studies for hyperparameters (Figures 4-6) lack error bars. The claimed "optimal" values for beta and lambda appear to be based on single trajectories. Provide statistical validation (e.g., confidence intervals) to ensure these hyperparameters are robust and not overfit to a specific random seed.
- **[science]** The claim that "negative-gap tokens exceed 50%" (Section 1, Observation 2) is a statistical assertion. The paper must explicitly state the sample size (number of tokens/trajectories) used for this analysis and provide the standard error or confidence interval for this proportion to support the magnitude of the problem.

## paper_reviewer_text_formatting — verdict: minor_revision

- **[writing]** Duplicate package inclusion: 'booktabs' is loaded twice (lines 3 and 13). 'graphicx' is loaded twice (lines 4 and 38). 'xspace' is loaded twice (lines 16 and 39). Consolidate these to avoid compilation warnings and potential conflicts.
- **[writing]** Redundant/Commented Code: The file contains large blocks of commented-out code (e.g., lines 100-130 for a table, lines 150-160 for observations) and unused package imports (e.g., 'lineno', 'soul', 'colortbl' defined but not clearly used in the final flow). Clean up the source to improve readability and compilation speed.
- **[writing]** Inconsistent Sectioning: The 'Experiment' section (line 438) uses \section, but its subsections (e.g., 'Main Results' at line 468) use \paragraph instead of \subsection. This breaks the standard heading hierarchy. Convert 'Main Results', 'Training Dynamics', 'Robust Analysis', and 'Ablation Studies' to \subsection for proper TOC generation and visual structure.
- **[writing]** Figure Placement: Several figures use [h] or [t] specifiers (e.g., Fig 1, 2, 3) which often fail in two-column conference formats, causing figures to float to the end of the document or page. Consider using [htbp] or the 'float' package to ensure figures appear near their first citation.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The abstract contains a significant structural error: it repeats the first two sentences of the introduction verbatim after the initial summary paragraph, creating a disjointed and redundant opening. Please consolidate into a single, coherent abstract.
- **[writing]** In Section 1 (Introduction), the paragraph starting with 'Once the student agent inevitably drifts' is incomplete. The sentence cuts off mid-thought and is immediately followed by a wrapfigure, leaving the observation without explanation. Complete the text.
- **[writing]** In Section 3.1, the description of 'Full Retrieval' is missing or unclear compared to the other three strategies. Ensure all four retrieval strategies are clearly defined for reproducibility.
- **[writing]** In Section 4.1, the sentence describing baseline failures ('While standalone OPSD collapses...') has awkward flow. Consider splitting for clarity and readability.
- **[writing]** The Appendix cross-reference is incorrect: the text refers to 'appendix:proof' for algorithm details, but algorithms are in 'appendix:algorithm'. Update the label to fix broken links.
