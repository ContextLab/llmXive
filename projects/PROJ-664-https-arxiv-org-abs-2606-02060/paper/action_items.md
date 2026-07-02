# Automated-review action items — Where Do Deep-Research Agents Go Wrong? Span-Level Error Localization in Agent Trajectories

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Abstract claims 'first-error accuracy by up to 30 percentage points' but Table 1 shows max FEA gain is 18.50. The 30 figure matches F1 gains, not FEA. Correct this metric conflation.
- **[writing]** Section 3 states 'downsample it to 200 tasks, resulting in 465 tasks' without clarifying the breakdown of the 465 total across the three cited benchmarks (GAIA, XBench, BrowseComp).
- **[writing]** Section 4 cites 'GPT-5.4' and 'DeepSeek-V3.2' with 2025/2026 dates. Verify these specific version numbers and dates against the cited system cards to ensure they are not hypothetical.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 2 (bottom-left): The x-axis labels 'Failed' and 'Successful' contradict the chart's title 'Error vs. Non-Error Span Composition' and the legend ('Error span'/'Non-error span'). The bars should be labeled by the presence of error spans (e.g., 'Has Error Span' vs 'No Error Span') to match the data being visualized, rather than the final trajectory outcome used in the top-left chart.
- **[science]** Figure 2 (bottom-right): The x-axis labels 'GPT', 'Claude', and 'Gemini' are ambiguous. The caption mentions comparing 'model families', but these labels could refer to specific models or families without a clear definition in the figure or caption, making it difficult to interpret the 'Error-Span Density' comparison accurately.
- **[science]** Figure 3: The 'Retrieve' stage has a labeled error rate of 2.9% but no visible bar, making the data point illegible and the chart inconsistent.
- **[science]** Figure 3: The 'Extract' stage shows a line data label of 3,146 spans, but the corresponding gray circle is plotted near the x-axis (approx. 1k), contradicting the label and the trend.
- **[science]** Figure 4: The legend defines five frameworks (GPT, Claude, Gemini, MiroFlow, OAgent), but the x-axis labels only list three (GPT, Claude, Gemini). The bars for MiroFlow and OAgent are present in the plot but lack corresponding x-axis labels, making it impossible to identify which model family they belong to.
- **[science]** Figure 4: The caption states 'Colors denote model families, while hatching distinguishes frameworks,' but the legend maps colors to specific model names (GPT, Claude, Gemini) and hatching to specific framework names (MiroFlow, OAgent). This contradicts the caption's claim that colors represent broad families and hatching represents frameworks, creating confusion about whether the bars represent models or frameworks.
- **[science]** Figure 5: The legend lists 'Claude-Sonnet-4.6' (triangle marker), but the plot lines for this model are missing from all three subplots (Precision, Recall, F1), making the ablation incomplete.
- **[writing]** Figure 5: The caption 'Ablation of Modules' is vague; it does not define what the x-axis categories ('Bare', '+A', '+A+B', 'DRIFT') represent in terms of specific module additions.
- **[science]** Figure 6: The radar chart lacks a radial axis scale (e.g., 0%, 25%, 50%, 75%, 100%). Without numerical tick marks or a legend indicating the scale, it is impossible to determine the absolute recall values or the magnitude of improvement claimed in the caption.
- **[writing]** Figure 6: The axis labels are abbreviated (e.g., 'Source verif.', 'Constraint semantics', 'Entity disamb.') without defining the full error type names in the caption or figure text, making it difficult to map the data to specific error categories.
- **[science]** Figure 7: The legend defines 'Bare', 'Codex', 'Claude Code', and 'DRIFT' as methods, but the bars are colored by these methods while containing icons for specific models (e.g., GPT-5.4, DeepSeek-V3.2). This conflates the method (framework) with the model, making it impossible to distinguish if a bar represents a specific model's performance or an aggregate of the method.
- **[science]** Figure 7: The x-axis lacks labels. While the bars are sorted by value, there is no indication of which benchmark, model, or configuration each bar represents, rendering the specific data points uninterpretable.
- **[writing]** Figure 7: The legend is split into two disconnected blocks (top row for methods, second row for models) without a clear visual grouping or hierarchy, which is confusing given the bars combine both method colors and model icons.
- **[science]** Figure 8: The caption claims to examine 'robustness across model scale and span complexity' and 'token cost,' but the figure only displays 'Macro F1' and 'FEA' scores for three specific model variants (Qwen3-235B, 32B, 8B) across 'Easy' and 'Hard' splits. There is no data shown regarding span complexity, token cost, or a broader scale analysis beyond these three points.
- **[writing]** Figure 8: The y-axis lacks a unit label (e.g., '%'), and the legend does not specify what the stacked bar segments represent (e.g., confidence intervals, component contributions, or error types).
- **[science]** Figure 9: The radar chart displays 12 error types, but the legend only defines 6 model configurations (DeepSeek Bare, Claude Bare, Qwen Bare, Gemini Bare, GPT Bare, Claude + DRIFT). It is unclear which line corresponds to which model for the non-baseline models, or if the colors map consistently across the 12 types without explicit labeling on the lines.
- **[writing]** Figure 9: The axis labels (e.g., 'Source misuse', 'Constraint semantics') are abbreviated and lack units or scale markers (e.g., 0%, 25%, 50%, 75%, 100%), making it impossible to quantify the 'recall' values mentioned in the caption.
- **[science]** Figure 12 (e): The scatter plot's x-axis ('Traj Error Rate') and y-axis ('Frequency in Error Trials') are not clearly labeled with units or definitions, making it difficult to interpret the relationship between the two metrics.
- **[writing]** Figure 12 (d): The word cloud contains extremely small, illegible text (e.g., 'subtask', 'confirmed', 'year') that cannot be read even at full resolution, reducing its utility as a visual summary.
- **[science]** Figure 12 (g): The x-axis labels ('1' through '10') lack context — it is unclear whether these represent time steps, span indices, or another ordinal metric, and no axis title clarifies this.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'semantic spans' at first use in the Abstract and Introduction. The term is used as a core unit of analysis but lacks a plain-English definition for non-specialists.
- **[writing]** Replace 'backbone models' with 'base models' or 'underlying LLMs' in the Abstract and Introduction. 'Backbone' is jargon that may confuse readers outside the specific architecture sub-field.
- **[writing]** Define 'first-error accuracy' (FEA) upon its first mention in the Abstract or Introduction. Currently, it appears as a metric without explanation of what it measures.
- **[writing]** Replace 'trajectory' with 'sequence of actions' or 'step-by-step process' in the Abstract. While common in agent literature, 'trajectory' is a specific technical term that excludes general readers.
- **[writing]** Define 'claim-centric' in the Abstract. The phrase describes the framework's approach but is not immediately clear to a general audience.
- **[writing]** Replace 'span-level' with 'segment-level' or 'step-level' in the Abstract and Introduction. 'Span' is a technical term from NLP/linguistics that may be opaque to broader audiences.
- **[writing]** Define 'Verified-1K' in the Abstract. The name implies a specific dataset subset but lacks a descriptive explanation of what it contains.
- **[writing]** Replace 'backtraces' with 'traces back' or 'follows the chain of' in the Introduction. 'Backtrace' is a debugging/programming term that may be jargon-heavy.
- **[writing]** Define 'hard constraints' in the Introduction. The term is used without context for what constitutes a 'hard' vs. 'soft' constraint in this specific task.
- **[writing]** Replace 'agentic' with 'agent-based' or 'autonomous agent' in the Introduction. 'Agentic' is a neologism that is not standard English and may confuse readers.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Clarify if Qwen/DeepSeek trajectories are part of the 2,790 corpus or new runs. Section 3.1 claims 3 models were used for collection, but Section 4.1 evaluates 5 models. The logical link between the fixed benchmark and the expanded evaluation set is missing.
- **[writing]** Define the roles of the 'two' vs 'seven' expert annotators in Section 3.1. The text mentions two experts validating LLM candidates and seven experts total spending 300 hours each. The workflow distribution is ambiguous.
- **[writing]** Qualify the claim that baselines 'degrade performance' in Section 4.2. Table 1 shows Codex improves GPT-5.4 slightly, contradicting the blanket statement. Specify that degradation is model-dependent.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The abstract claims DRIFT improves localization by 'up to 30 percentage points.' While true for the Easy split (31.92), the Hard split gain is lower (22.26). Clarify that the 30pp gain applies specifically to the Easy split to avoid over-emphasizing performance on difficult cases.
- **[writing]** The abstract highlights a 30pp F1 gain but downplays the modest First-Error Accuracy (FEA) gains on the Hard split (e.g., only 5.75pp for DeepSeek). Since the paper's core question is 'Where do agents go wrong?', the abstract over-represents success by focusing on aggregate F1 rather than the harder temporal localization metric.
- **[writing]** The introduction generalizes findings to 'deep-research agents' broadly, but the data is limited to three benchmarks (GAIA, XBench, BrowseComp) and two frameworks. Temper the claim to acknowledge the specific scope of the corpus to avoid over-generalizing failure modes to all agent types.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Annotator recruitment' section (Appendix) notes annotators were internal team members. Explicitly address potential bias, confirm if IRB approval was sought, and detail compensation to mitigate coercion.
- **[writing]** The dataset TELBench redistributes outputs from proprietary models (GPT-5, Claude, Gemini). Clarify compliance with model providers' Terms of Service regarding the redistribution of generated trajectories in a public benchmark.
- **[writing]** The term 'harmful' is used broadly. Clarify if this strictly means factual error or includes downstream safety risks (e.g., medical misinformation). If the latter, ensure annotation guidelines explicitly cover safety-specific criteria.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim that 'Each setting is repeated three times' (Experiment Settings) lacks statistical rigor. For a benchmark of 1,000 instances, reporting only the mean of three runs without standard deviation, confidence intervals, or significance testing (e.g., paired t-tests or Wilcoxon signed-rank) makes it impossible to assess if the reported ~30% F1 gains are robust or due to random variance in the LLM's stochastic sampling.
- **[science]** The annotation pipeline relies on 'two independent LLM annotators' followed by 'two expert annotators' (Dataset section). The paper does not report inter-annotator agreement (e.g., Cohen's Kappa or Fleiss' Kappa) for either the LLM stage or the human expert stage. Without these metrics, the reliability of the ground truth labels in TELBench is unverifiable, and the benchmark's validity is questionable.
- **[science]** The ablation study (Figure 1c, Appendix) claims performance gains from specific modules (Claim Keeper, Support Seeker). However, the text does not specify if these ablation results are statistically significant or if the improvements are consistent across the three random seeds. A statistical test comparing the full DRIFT against the ablated variants is required to support the claim that the gains arise from the proposed modules rather than noise.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report confidence intervals or standard deviations for the three repeated runs. Point estimates alone cannot validate the claimed ~30% F1 improvements as statistically significant.
- **[science]** Add statistical significance tests (e.g., paired t-tests) for DRIFT vs. baselines and ablation comparisons to confirm gains are not due to random variance.
- **[science]** Provide 95% confidence intervals for normalized error rates in the appendix (e.g., 60.5% for decision-making) to support claims about stage-specific risk.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the Abstract, there is a non-breaking space before the footnote marker for DRIFT ('DRIFT~\footnote'). Remove the tilde to ensure standard spacing.
- **[writing]** In Section 3 (Dataset), the phrase 'two framewrok' in the contributions list is a typo and should be 'two frameworks'.
- **[writing]** In Section 4.2 (Main Results), the sentence 'Table~\ref{tab:difficulty-split} and Figure~\ref{fig:performance} shows' contains a subject-verb agreement error; 'shows' should be 'show' to agree with the plural subject.
- **[writing]** In Section 4.2, the phrase 'where first goes wrong' is grammatically incomplete. It should be revised to 'where the error first goes wrong' or 'where things first go wrong'.
- **[writing]** In the Appendix, Section 'Detailed Error Analysis for Deep-research Agent Systems', the title uses a period at the end ('Systems.') which is inconsistent with standard section heading conventions and should be removed.
