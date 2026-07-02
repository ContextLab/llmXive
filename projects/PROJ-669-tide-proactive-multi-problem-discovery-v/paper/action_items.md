# Automated-review action items — TIDE: Proactive Multi-Problem Discovery via Template-Guided Iteration

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Clarify in Section 6 whether the per-iteration coverage/precision curves in Figure 1 (fig_iteration_recall_precision) apply only to the GPT backbone or are averaged across all backbones, as the caption restricts the scope to GPT.
- **[science]** In Section 5, clarify if the template counts (40 for workspace, 108 for repo) represent the total pool size or the output per LLM, as the phrasing 'constructed by each LLM' creates ambiguity about the final pool size used in experiments.
- **[writing]** In Section 6, qualify the claim that 'Multi-Agent at k=10 falls below TIDE at k=2' by explicitly noting this specific budget comparison is limited to the GPT backbone and Workspace setting shown in Figure 2, rather than a general property.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[fatal]** Figure 4: The figure contains only a legend with no actual data visualization (axes, plots, or charts) to display.
- **[fatal]** Figure 4: The caption is explicitly '(no caption)', providing no context for the legend's categories or the figure's purpose.
- **[fatal]** Figure 5: The figure has no caption, making it impossible to understand what the data represents, the meaning of the axes, or the context of the comparison.
- **[science]** Figure 5: The x-axis is completely unlabeled and lacks tick marks or values, preventing any interpretation of the distribution or the specific categories being compared.
- **[science]** Figure 5: The legend uses colored dots to represent 'GPT' and 'Gemini', but the plot consists of bar charts; the legend markers do not match the data visualization style.
- **[science]** Figure 6: The legend defines a 'Single-Agent' baseline (red line), but the y-axis scales (16-22, 12-17, 14-18) are truncated and do not show the baseline's actual value, making it impossible to visually verify the claimed performance gap.
- **[writing]** Figure 6: The y-axis labels ('Retrieval F1', 'Identification F1', 'Resolution F1') are rotated 90 degrees, which is unconventional and reduces readability compared to horizontal labels.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The term 'bottleneck' is used extensively (e.g., Sections 4, 5, 6, and Figures 4-7) to describe 'hidden problems' or 'bugs.' While defined in the prompt figures, the prose often uses 'bottleneck' without clarifying it means 'unarticulated problem.' Replace with 'hidden problem' or 'issue' in the main text to avoid confusion with performance bottlenecks.
- **[writing]** The acronym 'LLM' is used frequently but is not explicitly defined at its first occurrence in the Abstract or Introduction. It appears in the first sentence of the Introduction as 'Large language model (LLM) agents,' which is acceptable, but the Abstract uses 'LLM-based agents' (implied) or just 'agents' without the expansion. Ensure 'Large language model' is explicitly defined before the first use of 'LLM' in the Abstract or Introduction.
- **[writing]** The term 'qualnames' appears in the prompt figure captions (e.g., Figure 4, line 34) and the case study table (Table 2, line 12) without definition. While common in Python, it is jargon for non-specialists. Replace with 'fully qualified function names' or 'function identifiers' in the text.
- **[writing]** The phrase 'World Model' is capitalized and used as a specific input field in the Workspace setting (Figure 5, Section 5) but is not defined as a standard term in the text. It risks confusion with the broader AI concept of a 'world model.' Clarify that this refers to the 'user context profile' or 'state description' in the main text.
- **[writing]** The term 'gold' is used repeatedly as an adjective (e.g., 'gold problems,' 'gold resolution,' 'gold count') to mean 'ground truth' or 'annotated reference.' This is standard in ML but opaque to general readers. Replace with 'reference' or 'annotated' in the main text (e.g., 'reference problems,' 'reference resolution').

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 4 claims templates anchor 'each prediction' in a problem class, yet Figure 5 allows 'template-novel' issues (empty ID). Clarify how the fidelity claim holds for non-template predictions or if the 'template-guided' label is misleading for those cases.
- **[science]** Section 6 attributes Multi-Agent failure to 're-anchoring' on salient signals. The paper assumes this convergence is inevitable for parallel agents without stating controls (e.g., identical seeds/temps) to isolate state-sharing as the sole variable. Explicitly confirm baseline configuration.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Temper the claim of 'substantial gains' in the Repository setting (Abstract, Sec 2). Table 1 shows low absolute Resolution F1 scores (e.g., Qwen: 5.76 vs 9.70). Clarify that gains are relative, not necessarily substantial in absolute terms.
- **[writing]** Qualify the claim that 'scaling parallel agents is no substitute' (Sec 6). The baseline uses independent agents. Specify that independent parallelism fails, rather than implying all parallel scaling is inferior to iteration.
- **[writing]** Restrict the 'templates transfer across backbones' claim (Abstract, Sec 6). Table 2 only shows GPT-Gemini transfer. Do not imply transfer to Claude/Qwen without data.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The Ethics Statement (Section 10) and Limitations (Section 9) recommend generic safeguards (content filtering, human-in-the-loop) but lack specific protocols for the 'proactive' nature of TIDE. Explicitly address how the system prevents 'false positive' interventions where the agent might flag non-issues as critical bottlenecks, potentially causing user alarm or unnecessary workflow disruption.
- **[writing]** The Personal Workspace setting (Section 5.1) involves analyzing 'personal pain points,' 'relationships,' and 'organizational roles.' The paper does not detail the IRB approval process, consent mechanisms, or data anonymization strategies used to construct the 30 multi-problem workspaces. Clarify if these are synthetic or real user data and how privacy was preserved.
- **[writing]** The Software Repository setting (Section 5.1) uses real GitHub issues and code. While open-source, the 'proactive' generation of patches (Figure 4) carries a risk of introducing subtle bugs or security vulnerabilities if deployed without rigorous verification. The paper should explicitly state the safety guardrails preventing the agent from executing or suggesting patches that could compromise repository integrity.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The evaluation of 'identification' and 'resolution' relies on an LLM judge (GPT-5 mini) with a Likert-style rubric. The manuscript lacks a human-in-the-loop validation study (e.g., inter-annotator agreement or correlation with human ratings) to verify that the LLM judge's scores align with human judgment, which is critical for claims about 'fidelity' and 'resolution' quality.
- **[science]** The 'Software Repository' dataset construction groups issues from SWE-bench and TestExplora at a common anchor commit. The paper does not report the distribution of problem complexity or the correlation between the number of coexisting bugs and the difficulty of discovery, raising concerns about potential confounding variables in the multi-problem scaling analysis.
- **[science]** The 'Multi-Agent' baseline is described as running independent agents in parallel. The paper does not explicitly state whether these agents share the same random seed or temperature settings as the iterative TIDE rounds, nor does it clarify if the 'budget' $k$ implies $k$ total calls or $k$ calls per agent, which is essential for a fair comparison of the 'scaling' claims in Figure 5.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Section 5.3 states metrics are 'macro-averaged across instances' but does not report confidence intervals or standard errors for the main results in Table 1. Given the small sample size in the Repository setting (20 instances), statistical significance testing (e.g., paired t-tests or Wilcoxon signed-rank) is required to validate the claimed gains over baselines.
- **[science]** The LLM judge (GPT-5 mini) is used for Identification and Resolution scoring (Section 5.3). The paper lacks an inter-rater reliability analysis (e.g., Cohen's Kappa) or a human-in-the-loop validation study to establish the validity and consistency of these automated metrics, which are central to the paper's conclusions.
- **[science]** Figure 3 (budget_scaling) and Figure 5 (template_count_scaling) show performance trends but lack error bars or confidence intervals. Without these, it is impossible to determine if the observed scaling effects are statistically significant or within the noise of the evaluation process.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 2 (Introduction), the sentence 'These otherwise different issues share a common structure that extends beyond the workspace setting above' is slightly ambiguous. Clarify that the 'structure' refers to the multi-problem coexistence pattern described in the preceding paragraph, not the issues themselves.
- **[writing]** In Section 4 (Method), the phrase 'where none of which is articulated' in the task formulation paragraph contains a grammatical error. It should be corrected to 'none of which are articulated' or 'where no problem is articulated' to ensure subject-verb agreement and clarity.
- **[writing]** In Section 6 (Results), the sentence 'Interestingly, Multi-Agent at k=10 still falls below TIDE at k=2' uses a mathematical notation style that interrupts the prose flow. Consider rephrasing to 'Interestingly, the Multi-Agent baseline with a budget of 10 still underperforms TIDE with a budget of 2' for better readability.
