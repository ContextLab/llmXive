# Automated-review action items — UniClawBench: A Universal Benchmark for Proactive Agents on Real-World Tasks

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: accept

The paper presents a well-structured benchmark for proactive agents, and the factual claims made are consistently supported by the provided evidence, including internal tables, figures, and citations.

Specifically:
1.  **Benchmark Composition:** The claim of "400 bilingual real-world tasks" (Abstract, Section 1, Section 3) is consistent with the stated design of 5 capabilities with 40 English and 40 Chinese tasks each (5 * 40 * 2 = 400).
2.  **Experimental Results:** The performance metrics (Pass Rate and Average Score) reported in the text (Section 4.2, 4.3) align precisely with the data presented in Tables 1, 2, 3, 4, 5, and 6. For instance, the claim that "absolute success rates remain strictly below 50%" is supported by the highest overall Pass Rate of 0.475 (Claude Opus-4.8 in Table 5) and 0.480 (Claude Opus-4.6 in Table 3).
3.  **Citation Accuracy:** The citations used to support claims about existing benchmarks (e.g., WebArena, OSWorld) and agent frameworks (OpenClaw, Nanobot, EDICT) point to relevant works. While some cited works (e.g., "GPT-5.4", "Gemini-3.1-pro") are dated 2026, this is consistent with the paper's own timeline (NeurIPS 2026 submission) and the bibliography entries provided. There is no evidence of hallucinated references within the context of the paper's internal logic.
4.  **Methodology Claims:** The description of the "three-role closed-loop evaluation" and the "information firewall" mechanism is detailed in Section 3.2 and Appendix C, and the case study in Appendix D provides concrete evidence that the system functions as described (e.g., the user simulator receiving only a high-level status signal).

No unsupported claims, citation mismatches, or numerical inconsistencies were found that would undermine the paper's factual accuracy. The claims are appropriately qualified and backed by the presented data.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption ends abruptly with 'returned to the executor f', which appears to be a typo or incomplete sentence.
- **[writing]** Figure 1: The legend at the bottom left is labeled 'Legend' but the text is extremely small and difficult to read.
- **[writing]** Figure 1: The text 'Metric 1' at the bottom right is unexplained and appears to be a stray label not connected to the diagram.
- **[science]** Figure 2: The heatmaps display 'within-category percentage' values (e.g., 45% for Media/Entertainment in Multimodal), but the column headers (Multimodal, Long Context, etc.) represent the benchmark's core capabilities. The caption fails to clarify if these percentages represent the proportion of tasks within a domain that use a specific capability, or the proportion of a capability's tasks that fall into a domain. Without this definition, the 'diversity' claim is ambiguous and the data interpret
- **[writing]** Figure 2: The colorbar on the right is labeled 'Share (%)', but the individual cells contain specific percentage values (e.g., '0%', '15%'). The term 'Share' is slightly imprecise for 'Percentage of tasks' or 'Distribution', though acceptable. However, the colorbar scale (0-100) matches the cell values, which is good, but the lack of a clear title for the colorbar (e.g., 'Percentage of Tasks') makes the visualization slightly less self-explanatory.
- **[science]** Figure 3: The x-axis labels in subplots (a) and (b) are rotated at a steep angle, causing significant overlap and illegibility for model names (e.g., 'Claude Sonnet 4 6', 'Gemini 3.1 Pro') and task dimensions.
- **[science]** Figure 3: Subplot (a) displays 'Avg Input Tokens (M)' and 'Avg Output Tokens (K)' on dual y-axes, but the x-axis labels (model names) are crowded and partially illegible due to rotation.
- **[writing]** Figure 3: The caption states the data is from the 'OpenClaw system,' but the figure itself lacks a title or label explicitly identifying the system name, relying solely on the caption for context.
- **[writing]** Figure 4: The radar chart legend lists nine model/framework combinations, but the chart contains ten distinct colored lines, making it impossible to map one line to a specific entry.
- **[science]** Figure 4: The radar chart lacks a unit or scale definition for the 'Normalized Pass Rate' axis (0.0–1.0), leaving the magnitude of performance differences ambiguous.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 4.1 (Environmental Setup) uses 'Codex agents' without defining the term. While 'Codex' is a known model name, the phrase 'Codex agents' implies a specific system or role not previously defined. Clarify if this refers to agents powered by the Codex model or a specific agent framework named Codex, e.g., 'agents based on the Codex model'.
- **[writing]** Section 4.1 (Environmental Setup) introduces 'Advanced Packaging Tool (apt)' as a skill name. While 'apt' is standard Linux terminology, the phrasing 'self-written Advanced Packaging Tool (apt) skill' is slightly ambiguous. Ensure the reader understands 'apt' is the standard Linux package manager being wrapped as a skill, not a novel tool invented by the authors.
- **[writing]** Section 4.3 (Cross-Framework Benchmark Results) uses the term 'coordination friction' without a formal definition or operational metric. While the context explains the phenomenon (stalled pipelines), a brief gloss or citation to a standard definition would help an adjacent-field reader understand if this is a specific technical term or a descriptive phrase.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** In Table 5, the model 'Claude Opus-4.8' cites 'claude-opus-4.6'. Correct the citation key to match the bibliography entry for version 4.8 to ensure the table label and reference align.
- **[writing]** Section 4.1 defines distinct timeouts for long-context tasks (45/30 min) vs standard (30/20 min). Section 4.2 reports 'Overall' metrics without clarifying if these aggregate results use the extended limits for the long-context subset. Explicitly state whether the reported Overall metrics reflect the specific timeout rules per task type to ensure the conclusion follows from the setup.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Title/Abstract claim 'Universal Benchmark' but Section 3 limits scope to 400 tasks in only 2 languages (English/Chinese) and 3 frameworks. Replace 'Universal' with 'Comprehensive' or 'Capability-Driven' and qualify 'Real-World' to reflect the specific tested domains.
- **[writing]** Abstract claims 'first capability-driven benchmark... in dynamic, real-world settings' (Abstract). Section 2 cites ClawMark and LiveClawBench which also use dynamic real-world settings. Qualify the claim to 'first with a three-role closed-loop evaluation strategy' to avoid overclaiming novelty of the setting itself.
- **[writing]** Conclusion states the benchmark 'successfully pinpoints the root causes of agent failures' (Section 5). Results show very low pass rates in some categories but do not ablate framework vs. model vs. task difficulty to prove root causes. Soften to 'provides diagnostic evidence for failure modes' or 'helps identify potential root causes'.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a benchmark for evaluating proactive AI agents in real-world environments. The methodology involves running agents in isolated Docker containers with injected tasks, using a "hidden supervisor" to grade performance against private rubrics, and a "user simulator" to provide feedback.

From a safety and ethics perspective, the work is low-risk. The benchmark tasks (e.g., license audits, trip planning, code refactoring) are benign and do not involve generating harmful content, exploiting vulnerabilities, or targeting real individuals. The "real-world" aspect is carefully contained within Docker containers with specific, non-sensitive fixtures (e.g., local files, mock APIs, or public web pages like The Met or Library of Congress), avoiding the risk of agents interacting with live, sensitive production systems or private user data.

The paper explicitly addresses the risk of evaluation leakage via a "three-role" architecture with an information firewall, ensuring the grading criteria remain hidden from the agent and the user simulator. This is a robust design choice that mitigates the risk of the benchmark itself being used to train agents to game evaluations.

There are no human subjects involved; the "user simulator" is an automated agent, and the tasks do not require collecting or processing personal data from real people. The datasets and code are intended for public release, but the task descriptions and examples provided in the appendix do not contain PII or sensitive information.

No dual-use capabilities are introduced that would lower the barrier to harm (e.g., automated vulnerability discovery or disinformation generation). The research focuses on evaluation methodology, not on creating new offensive capabilities. Consequently, there are no missing disclosures or unmitigated risks requiring action.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a comprehensive benchmark for proactive agents, but the experimental design supporting the central claims regarding model and framework rankings lacks sufficient statistical rigor to rule out noise or confounding variables. First, the primary results in Tables 1, 2, 5, and 6 report single-point estimates (Pass Rate and Average Score) for 400 tasks without any measure of variance. The benchmark splits tasks into five categories with only 40 tasks each (20 English, 20 Chinese).

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Section 4.2 reports '92.0% agreement' and correlation coefficients (r=0.71, ρ=0.68) for the reliability study based on N=50 trajectories. No confidence intervals, standard errors, or p-values are provided for these statistics. Given the small sample size (N=50), the precision of these estimates is unknown. Report 95% CIs for the agreement proportion and the correlation coefficients, or state the standard error, to allow readers to assess the stability of the reliability claim.
- **[writing]** Tables 1-6 report Pass Rates and Average Scores to three decimal places (e.g., 0.438, 0.834) for 40 tasks per category. With N=40, the standard error for a proportion near 0.5 is ~0.08, making the third decimal place statistically meaningless (false precision). Round all reported metrics to two decimal places (e.g., 0.44, 0.83) to match the resolution supported by the sample size.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** Section 1, Paragraph 1: 'assist user by directly control' contains a subject-verb agreement error and missing article. Rewrite as: 'assist users by directly controlling'.
- **[writing]** Section 1, Paragraph 2: The sentence 'Finally, and most critically, existing benchmarks organize tasks by application scenario... This approach conflates fundamentally different abilities' splits a single logical point into two sentences. Merge them for better flow: 'Finally, and most critically, existing benchmarks organize tasks by application scenario (e.g., office, research), an approach that conflates fundamentally different abilities.'
- **[writing]** Section 3, Paragraph 1: The phrase 'All tasks run inside Docker containers equipped with real software, live browsers and local file systems' lacks a serial comma before 'and', creating a slight ambiguity in the list. Add a comma: '...live browsers, and local file systems'.
- **[writing]** Section 4, Paragraph 1: 'installing and preparing each frameworks' has a number agreement error. Change to 'installing and preparing each framework' or 'installing and preparing the frameworks'.
- **[writing]** Section 4, Paragraph 3: 'EDICT consume a huge amount of token' has subject-verb agreement and number errors. Rewrite as: 'EDICT consumes a huge amount of tokens'.
- **[writing]** Section 4, Paragraph 3: 'resulting in a notably lower overall pass rates' has a number agreement error. Change to 'resulting in notably lower overall pass rates' or 'a notably lower overall pass rate'.
- **[writing]** Section 4, Paragraph 4: 'categorised by model' uses British spelling ('categorised') while the rest of the paper uses American spelling ('categorized' is implied by 'realized' elsewhere, though 'categorized' is not explicitly used, 'behavior' is used in Appendix C). For consistency with 'behavior' in Appendix C and standard NeurIPS style, ensure consistent spelling. If the paper aims for US English, change 'categorised' to 'categorized'.
