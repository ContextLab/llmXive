# Automated-review action items — SearchSwarm: Towards Delegation Intelligence in Agentic LLMs for Long-Horizon Deep Research

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The claim that SearchSwarm 'exceeds GPT-5.2-Thinking' on BrowseComp (Sec 3.2) is unsupported by Table 1. The table shows 68.1 vs 65.8, but the text implies a direct comparison without clarifying if metrics or contexts differ. The phrasing 'exceeds' overstates the significance of a 2.3-point margin without statistical validation.
- **[science]** The citation 'openai2025gpt52' refers to a 'GPT-5.2' model with a 2025 release date. Given the paper's future-dated citations (e.g., 2026 for Kimi), verify if 'GPT-5.2' is a real, public model. If hypothetical, the claim of 'exceeding' it is speculative and must be qualified, not stated as an empirical result.
- **[writing]** The claim in Sec 3.2 that the base model 'never' invokes call_sub_agent is an absolute statement lacking evidence. The text does not provide the sample size or test set used to derive this 0% rate. If the evaluation set was small, this is an overgeneralization. Qualify with 'in our evaluation of X samples'.
- **[writing]** The claim of 'SOTA among 30B-A3B models' (Abstract, Sec 3.2) relies on a 0.2-point margin over MiroThinker-1.7-mini (68.1 vs 67.9). Without statistical significance or error bars, claiming SOTA on such a marginal difference is misleading. Clarify if the difference is statistically significant.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption claims a comparison on 'four benchmarks', but the chart displays a single set of scores without specifying which benchmark these results correspond to or showing the other three.
- **[science]** Figure 1: The y-axis lacks a unit or label (e.g., 'Accuracy (%)' or 'Score'), making the numerical values (e.g., 68.1) ambiguous.
- **[science]** Figure 1: The caption mentions 'lightweight models of comparable scale' and 'larger models', but the x-axis labels do not indicate model sizes (e.g., parameter counts), making this comparison impossible to verify visually.
- **[writing]** Figure 2: The caption text is truncated at the end ('...multi-turn t'), cutting off the description of the subagent execution flow.
- **[fatal]** Figure 3: The caption 'Main agent [tool_usage_four_datasets_pies_main.pdf]' is a filename fragment and fails to describe the figure's content (tool usage distribution across four datasets), making the figure unintelligible without external context.
- **[science]** Figure 3: The 'BrowseComp' and 'BrowseComp-zh' charts display a '0.1%' slice for 'Scholar' that is visually indistinguishable from the white background, rendering the data point illegible.
- **[science]** Figure 4: The y-axis is labeled 'Percentage(%)' but the values (0-14) likely represent frequency counts or normalized density rather than a percentage of the total population, as the sum of these values across the x-axis does not equal 100%. This label is misleading for a distribution plot.
- **[writing]** Figure 4: The title 'BrowseComp - Main Calls To Sub-Agents' is redundant and inconsistent with the caption 'Distribution of call_sub_agent invocation counts per question'; the title should be removed or aligned with the caption.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized terminology that creates a barrier for non-specialist readers. The central concept, "delegation intelligence," is introduced in the Abstract and Introduction without a clear, standalone definition, assuming the reader already understands the specific nuance the authors intend. This term should be explicitly defined upon first use. Furthermore, the paper frequently uses acronyms without expansion. "SFT" appears in Section 3.3 without being spelled out

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The claim that SearchSwarm 'exceeds GPT-5.2-Thinking' on BrowseComp (68.1 vs 65.8) is logically unsupported because the baseline result lacks the '*' marker indicating context management, while the proposed method uses it. This creates an unfair comparison of capabilities rather than just model performance.
- **[writing]** The ablation study in Section 4.3 claims the 'Full Harness' yields a +10.0 gain over 'Tool only', but the text does not explicitly state whether the 'Tool only' baseline includes the same context window sizes (128K/64K) as the full harness, leaving the causal mechanism of the gain ambiguous.
- **[writing]** The conclusion states delegation patterns 'generalize to single-agent' settings, yet the single-agent results (52.0) are significantly lower than the multi-agent results (68.1). The paper needs to clarify if 'generalization' implies the *skill* exists (which it does) or if the *performance* is comparable, as the current phrasing risks overclaiming efficacy in the single-agent mode.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim that SearchSwarm 'exceeds GPT-5.2-Thinking' (Section 3.2) is an overreach. Table 1 shows SearchSwarm (68.1) only exceeds GPT-5.2-Thinking (65.8) on BrowseComp, but GPT-5.2-Thinking scores 76.1 on BrowseComp-ZH, where SearchSwarm scores 73.3. The text implies a general superiority that the data does not support across all metrics.
- **[writing]** The statement that SearchSwarm 'remains competitive with models over 10x larger' (Figure 1 caption) is an overgeneralization. While it beats GPT-5.2-Thinking on one metric, it trails significantly on others (e.g., GAIA: 82.5 vs. 76.4 for GPT-5, but GPT-5 is not 10x larger; the comparison to 10x larger models like DeepSeek V3.2 is mixed). The claim needs qualification to reflect specific benchmark performance rather than a blanket statement.
- **[science]** The conclusion states 'Delegation patterns generalize to single-agent and open-ended tasks' (Section 6). However, Section 3.5 shows a significant performance drop in the single-agent setting (52.0 vs 68.1 on BrowseComp). While it improves over the base model, claiming 'generalization' without acknowledging the substantial performance degradation in the absence of subagents overstates the robustness of the learned behavior.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper presents a multi-agent system (SearchSwarm) designed for long-horizon deep research, utilizing web browsing tools and delegated sub-agents. From a safety and ethics perspective, the primary concerns revolve around data privacy, the potential for generating hallucinated citations in a research context, and the dual-use nature of autonomous information gathering. Data Privacy and Consent: In Section 3.3 ("Supervised Fine-tuning"), the authors state that data is sourced from RedSearcher a

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Section 4.2 (Main Results) and Table 1 lack statistical significance testing. The margin between SearchSwarm (68.1) and MiroThinker (67.9) on BrowseComp is 0.2 points. Without reported standard deviations, confidence intervals, or p-values from multiple runs, it is impossible to determine if this is a genuine improvement or noise.
- **[science]** The ablation study in Section 4.3 ('Effectiveness of the Harness') uses a 200-question subset but does not specify if this subset is a random sample or a curated hard/easy set. If not random, the +10.0 gain may be biased. Please clarify the sampling methodology or provide results on the full benchmark.
- **[science]** The claim that SearchSwarm 'exceeds GPT-5.2-Thinking' (Section 4.2) relies on a single-point comparison (68.1 vs 65.8) without error bars. Given the proprietary nature of the baseline, the authors must explicitly state the variance of their own model's performance across seeds to validate the robustness of this claim.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report statistical significance (e.g., p-values, confidence intervals, or standard deviations) for the benchmark comparisons in Table 1. The marginal gains (e.g., 68.1 vs 67.9 on BrowseComp) are too small to claim superiority without variance estimates or significance testing across multiple runs.
- **[science]** Clarify the experimental protocol for the ablation study in Section 4.3. Specify if the 200-question subset was sampled randomly and if the base, tool-only, and full-harness models were evaluated on the exact same seed set to ensure the +10.0 gain is not due to sampling variance.
- **[science]** The 'Generalization to Single-Agent' results (Section 4.5) lack a baseline comparison for the specific single-agent configuration. Clarify if the base model was also evaluated in a single-agent mode to isolate the effect of the fine-tuning versus the architectural change.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 2.1 (Formulation), the trajectory definition 'H_T = (q, (τ_0, a_0, o_0), ..., (τ_T, a_T, o_T), y)' lacks a verb and reads as a fragment. Rewrite as a complete sentence, e.g., 'A trajectory H_T is defined as...'.
- **[writing]** The Introduction lists three bullet points but inconsistently mixes 'We explore' (present tense) with 'We synthesize' and 'We open-source'. Ensure parallel structure and consistent tense across all contribution statements.
- **[writing]** In Section 3.2 (Main Results), the sentence 'Without fine-tuning, the base model never invokes call_sub_agent' appears abruptly. Add a transitional phrase to connect this observation to the preceding performance comparison.
- **[writing]** The Appendix Case Study (Section A.3) uses a mix of narrative paragraphs and bulleted lists for the 'Rejected alternatives' section. Standardize the formatting to ensure visual consistency with the rest of the paper.
