# Automated-review action items — OpenThoughts-Agent: Data Recipes for Agentic Models

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper presents a rigorous ablation study on data curation for agentic models, with most numerical claims aligning well with the provided tables. However, there are specific instances where the textual claims rely on unsupported or potentially hallucinated external facts, and one instance of ambiguous comparative logic. First, the Introduction and Section 3.5 repeatedly reference "GPT-5.3-Codex" as a benchmark model and a teacher model. As of the current date, GPT-5 has not been publicly rele

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption references 'Table .' with a missing table number, making the 'All Average' benchmark definition unresolvable.
- **[writing]** Figure 1: The legend includes 'SERA Qwen3-32B (best harness)' (dotted purple), but the caption states 'Additional notes on SERA below' without providing them, leaving the method undefined.
- **[science]** Figure 1: The 'All Average' plot shows a dotted purple line for 'SERA Qwen3-32B (best harness)' that is not present in the other two subplots, creating an inconsistent comparison set across the figure.
- **[writing]** Figure 2: The caption states 'Each stage is ablated independently in Sections --', but the section numbers are missing (likely a placeholder). Replace '--' with the correct section numbers.
- **[science]** Figure 3: The caption states 'Error bars are standard error across three stochastic re-runs,' but the rendered plot contains no visible error bars on any data points.
- **[science]** Figure 3: The caption claims Method 1 'plateaus from 31.6K to 100K,' yet the 'SWE-bench Verified' and 'Terminal-Bench 2.0' subplots show a visible increase in accuracy for Method 1 between these points, contradicting the description.
- **[science]** Figure 4: The Sankey diagram shows a total output of 94,334 (sum of Final Mix values), but the caption claims the final dataset is 100k agentic traces. The visual data does not support the specific number in the caption.
- **[writing]** Figure 4: The 'StackExchange Tezos' label is split across three lines, making it difficult to read and visually disjointed compared to other labels.
- **[science]** Figure 5: The legend labels the blue line as 'OT-Agent Qwen3-8B' and the pink line as 'Nemotron-Terminal-Corpus Qwen3-8B', but the caption states the experiment compares 'OpenThoughts-Agent-v2' against the 'Nemotron-Terminal-Corpus baseline'. The legend fails to explicitly name the 'OpenThoughts-Agent-v2' method, creating ambiguity about whether the blue line represents the specific v2 recipe or a generic agent.
- **[writing]** Figure 5: The x-axis labels ('316', '1K', '3.16K', etc.) are not formatted as a standard logarithmic scale (e.g., 10^2, 10^3) nor as a linear scale, which may confuse readers regarding the exact spacing of data points between 10K and 100K.
- **[science]** Figure 6: The caption states the deployed checkpoint reward is 0.33, but the 'post-RL eval' diamond marker is plotted at approximately 0.325, creating a minor inconsistency between the text and the visual data.
- **[writing]** Figure 6: The x-axis tick labels (e.g., '05-05 00') lack the year, which is ambiguous for a scientific record; full ISO 8601 format (YYYY-MM-DD HH) is recommended.
- **[science]** Figure 7: The legend entry for the orange diamond ('post-RL') is partially cut off by the plot border, making the label illegible.
- **[science]** Figure 7: The caption claims the blue line rises from 0.54 to 0.73, but the visual data points start near 0.54 and end near 0.73; however, the orange diamond (post-RL eval) is plotted at ~0.22, which contradicts the caption's implication that the policy improves to 0.73 without collapse (the diamond should likely be higher if it represents the final eval reward).
- **[writing]** Figure 7: The legend text 'post-RL eval' is partially obscured by the plot frame on the right side.
- **[science]** Figure 8: The 'Premature stop rate' panel shows a constant value of 1.0 across all bins, which contradicts the caption's claim that the agent 'times out' (implying a variable rate) and suggests a potential data logging error or mislabeled metric.
- **[writing]** Figure 8: The x-axis tick labels are rotated 45 degrees and overlap significantly, making the timestamps (e.g., '2026-05-05 00:00') difficult to read.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 3.1 (Sourcing Tasks) and Table 1 use 'pp' (e.g., '~30 pp') without defining it as 'percentage points'. While common in economics/stats, an adjacent-field PhD in NLP/ML might momentarily confuse this with 'parts per' or 'pages'. Define at first use: 'percentage points (pp)'.
- **[writing]** Section 3.2 (Mixing Tasks) and Table 1 introduce 'Raw' and 'Normalized' columns without defining the normalization metric. The text mentions 'average z-score' in Section 3, but the table header does not explicitly link 'Normalized' to 'z-score', forcing the reader to cross-reference. Add '(z-score)' to the 'Normalized' column header or define it in the table caption.
- **[writing]** Section 3.5 (Teacher Model) and Table 5 reference 'GLM-4.7-AWQ' and 'GPT-5.3-Codex'. These specific versioned model names (especially the hypothetical/future '5.3' and '4.7') are used without a brief gloss of their architecture or origin (e.g., 'GLM-4.7-AWQ, a quantized variant of the GLM-4.7 model'). While model names are proper nouns, the specific versioning implies a specific capability set not obvious to an outsider.
- **[writing]** Section 4.1 (Sourcing Tasks in RL) introduces the data source name '	exttt{pymethods2test}' without explaining the transformation. The text says it is 'competitive programming recast as contracts', but the name itself is opaque. Add a brief parenthetical on first use: '	exttt{pymethods2test} (a dataset converting competitive programming problems into function-level contract verification tasks)'.
- **[writing]** Section 3.6 (Filtering Agent Rollouts) and Appendix A.3 use the term 'turns' (e.g., 'fewer than 5 turns') without explicitly defining it as 'agent-environment interaction steps' or 'model response cycles'. In multi-turn dialogue, 'turn' is standard, but in agentic loops involving tool use, it can be ambiguous (does a tool call count as a turn?). Define 'turn' as 'one complete cycle of model generation and tool execution' at first use.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Section 4.3 claims filtering for <5 turns yields the "largest improvement," but Table 2 (e002) shows "Response Length (GPT-5, longest)" as the top strategy (+1.38 normalized) with no row for the min-turns filter. The text's superlative claim is not entailed by the visible table data.
- **[science]** Section 3.2 states mixing Top 4/8 "outperforms" Top 1, but Table 1 (e000) shows Top 1 (30.67%) beats Top 4 (29.33%) on SWE-Bench Verified. The unqualified claim contradicts the primary metric column; qualify as "outperforms on average" or "normalized score."
- **[writing]** Section 5 conflates "Upsampling" (Method 1) plateauing with "Adding sources" (Method 4) hurting performance. The text implies a single narrative for both, but the data (Fig 2 vs Table 3) supports them as distinct phenomena. Clarify the distinction to avoid causal ambiguity.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Conclusion claims 'strongest... across seven benchmarks' despite losing on MedAgentBench (47.8% vs 62.6%). Narrow to 'strongest on average' or specify the subset of benchmarks where it leads to avoid implying universal dominance.
- **[writing]** Introduction claims outperformance on listed OOD benchmarks but omits the MedAgentBench failure. Add a limitation acknowledging the model does not dominate every single OOD benchmark to prevent a cherry-picked impression of robustness.
- **[writing]** Conclusion admits 'no ablation of base model choice' but presents findings as a general 'data recipe.' Explicitly state that the recipe is validated only on Qwen3 and generalization to other families (e.g., Llama) is unproven.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a data curation pipeline for training agentic language models on software engineering and terminal tasks. The work involves supervised fine-tuning (SFT) and reinforcement learning (RL) using synthetic and public benchmark data (e.g., SWE-Bench, Terminal-Bench).

From a safety and ethics perspective, the research is low-risk by construction. The primary artifacts are data recipes and model weights trained on public or synthetic datasets. The paper explicitly acknowledges the dual-use nature of agentic models in the "Broader Impacts" section (Section 6), noting that these models are "capable of unauthorized actions" and recommending "sandboxing and human oversight." This disclosure is appropriate for the field and the specific capabilities described.

There are no indications of:
- **Human subjects data:** The data sources are synthetic (generated by other models) or derived from public benchmarks (SWE-Bench, Terminal-Bench) which do not involve private human data or require IRB approval in this context.
- **PII exposure:** The paper does not release raw scraped data containing personal information; it releases processed trajectories and model weights.
- **Dual-use operationalization:** While the models can perform coding tasks, the paper does not provide operational details for generating exploits, malware, or specific cyber-attacks. The focus is on general software engineering capabilities (fixing bugs, implementing features).
- **License violations:** The paper cites the sources of its data (e.g., SWE-Smith, StackExchange) and releases its own artifacts under open licenses, with no evidence of ToS violations in the text provided.

The paper does not require additional safety disclosures or mitigations beyond what is already present. The risk profile is consistent with standard ML research on agentic systems.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents an extensive ablation study on data curation for agentic models, but several central claims rely on experimental designs that do not fully rule out confounding variables or sampling noise. First, the stability of the reported gains is unclear. Tables 1, 2, and 3 report standard errors (e.g., ±1.63) but do not state the number of random seeds (n) used to generate these statistics. In agentic benchmarks, run-to-run variance can be high; a 1.3 percentage point difference (e.g., T

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Table 1 (mixing_strategies) and Table 2 (task_gen_full) report means with subscripts (e.g., 29.33 ± 1.63) but do not define the subscript as Standard Error (SE) or Standard Deviation (SD). Section 4.2 mentions 'three stochastic re-runs' for scaling plots, but the ablation tables (95 strategies) lack explicit confirmation of N. Report 'N' and the specific metric (SE vs SD) in table captions to allow readers to judge precision and perform meta-analysis.
- **[writing]** The paper claims 'significant' improvements (e.g., +3 pp avg in filtering, +5.4 pp on SWE-Bench) without reporting p-values or confidence intervals for these specific pairwise comparisons. With N=3 runs, a paired t-test or Wilcoxon signed-rank test is feasible. Either report the test statistic and p-value for the key ablation comparisons or rephrase claims to 'observed improvement' to avoid implying statistical significance without evidence.
- **[science]** Section 4.2 and Table 3 present results from 95 task generation strategies and multiple mixing strategies. The 'best' performers are highlighted without correction for multiple comparisons (e.g., Bonferroni or FDR). With ~100+ tests, false positives are expected. Apply a multiple-comparison correction to the ablation results or explicitly state that the reported 'best' strategies are uncorrected and subject to selection bias.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** Section 3.5 (Teacher Model) states: 'Despite GPT-5.3-Codex being the best-performing model, GLM-4.7-AWQ is the best teacher, representing a ~5% decrease in performance when using GPT-5.3-Codex.' The phrase 'representing a ~5% decrease' is ambiguous: does it mean a 5 percentage point drop or a 5% relative drop? Rewrite to specify the metric (e.g., 'a 5 percentage point drop on Terminal-Bench 2.0').
- **[writing]** Section 3.6 (Filtering Agent Rollouts) claims: 'Filtering traces with fewer than 5 turns yields the largest improvement.' This contradicts the logic of Section 3.4 (Filtering Tasks), which found that filtering for *more* tokens (implying longer traces) improved performance. The phrasing 'fewer than 5 turns' likely contains a typo (should be 'more than' or 'at least'). Verify and correct the direction of the filter to match the reported results.
- **[writing]** The Introduction lists four key findings in a bulleted list, but the second bullet ('The strongest model by benchmark performance does not necessarily make the best teacher') is not explicitly supported by a specific result summary in the abstract or intro text. Ensure the intro explicitly names the teacher model comparison (GLM vs. GPT) to ground the claim before the reader reaches Section 3.5.
- **[writing]** Section 4 (Scaling Up SFT Data) contains a paragraph labeled 'OpenThoughts-Agent-v2' that abruptly lists final metrics without a transition sentence explaining how these results relate to the preceding discussion on scaling methods. Add a lead-in sentence (e.g., 'Applying these scaling strategies to the full 100K dataset yields the following final performance:') to improve flow.
