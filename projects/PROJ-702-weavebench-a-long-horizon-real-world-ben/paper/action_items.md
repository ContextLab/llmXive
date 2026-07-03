# Automated-review action items — WeaveBench: A Long-Horizon, Real-World Benchmark for Computer-Use Agents with Hybrid Interfaces

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 4.2 claims a '+31.6pp' hybrid gain for WeaveBench generally, but this figure is specific to Claude Opus 4.7 (35.1% vs 3.5%). GPT-5.5 shows ~30.7pp. Clarify if this is a model-specific or average gain to avoid overgeneralization.
- **[writing]** Section 4.3 states the judge removes '10.3 to 20.2' points across four GPT backbones. While 20.2pp for GPT-5.5 is shown, the text lacks the specific inflated scores for the other three backbones needed to verify the 10.3pp lower bound. List these scores.
- **[writing]** Appendix C claims CLI and Vision are 'on par' (79.1% vs 77.3%) and CLI takes 'half the steps' (14.3 vs 29.0). Qualify 'on par' as 'statistically comparable' and 'half' as 'approximately half' to maintain numerical precision.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The right-side summary boxes contain text that is significantly smaller and lower contrast than the main workflow labels, making the 'Only CLI' vs 'Only GUI' distinctions difficult to read.
- **[science]** Figure 1: The 'DAV' workflow Step 1 shows a Jaeger trace with a red leaf span, but the specific 'payments.fx-rate.http' span is not clearly highlighted or labeled in the screenshot to match the text description.
- **[writing]** Figure 1: The 'GAME' workflow Step 2 terminal output lists '3 issues' but the text is blurry and the specific file paths (e.g., 'scenes/main.tscn') are hard to verify against the step description.
- **[writing]** Figure 2: The caption contains a typo 'stress-tested by $$3 pilot agents' with a stray dollar sign.
- **[writing]** Figure 2: The caption text 'Task: 114 tasks across 8 domains' is repeated verbatim in the figure's 'Pilot Runs' section, creating redundancy.
- **[writing]** Figure 3 caption: contains a typo 'GUI $$ CLI' instead of 'GUI / CLI' or 'GUI and CLI'.
- **[science]** Figure 3(b): the y-axis label 'Switches' is ambiguous; it should explicitly state 'Number of tasks' to match the x-axis label and clarify that bars represent task counts per switch range.
- **[science]** Figure 4: The caption describes panel (a) as showing 'Overall error distribution across the three frontier backbones', but the rendered sunburst chart displays a single aggregated distribution (n=1,735) without distinguishing the three backbones (Opus 4.7, GPT-5.5, GPT-5.4) which are only shown in panel (b).
- **[writing]** Figure 4: The legend at the top of panel (a) uses color blocks for categories (E1 Reasoning, E2 Tool/Exec, etc.) that are not explicitly labeled in the chart's inner ring, requiring the reader to infer the mapping between the legend colors and the inner ring segments.
- **[writing]** Figure 5: The y-axis label '# tasks' is truncated to '# tasks' in panels (a) and (b), and the decimal point in the y-axis tick labels (e.g., '10.0', '12.5') is barely legible due to low resolution.
- **[science]** Figure 5: Panel (b) displays a histogram of 'GUI <-> CLI channel switches per task' with a median of 16, yet the x-axis extends to 70 with sparse bars; the caption claims 'every task has at least one switch' but the first bin (0-5) appears to contain significant counts, creating a potential visual contradiction regarding the minimum value.
- **[science]** Figure 6: The caption states dotted lines mark the P2 threshold at 20 calls, but the dotted line in panel (a) is positioned near y=25, contradicting the stated value.
- **[science]** Figure 6: The caption states dotted lines mark the P3 threshold at 3 apps, but the dotted line in panel (c) is positioned near y=3.5, contradicting the stated value.
- **[writing]** Figure 7: The caption contains a grammatical error and missing noun in the first sentence: 'Task source distribution of .'.
- **[science]** Figure 7: The legend lists 'GitLab issue' (orange) and 'GitHub issue/PR' (purple), but the stacked bars for 'GAM Games' and 'SPA Spatial' contain a dark blue segment that is not defined in the legend.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific jargon and undefined acronyms that create barriers for non-specialist readers. The most critical issue is the use of "CUA" (Computer-Use Agent) in the very first sentence of the Introduction without expansion. Similarly, "MCP" (Model Context Protocol) is used in Section 1 and Table 1 without definition, assuming the reader is already familiar with this specific protocol. The term "rollouts" is used frequently (e.g., Section 1, Section 3.4) to desc

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The claim that CLI-only scores 'stay at or below 3.5%' implies a hard bound, yet the non-zero score contradicts the strict P1 definition of 'non-substitutability' for all tasks. Clarify if P1 enforcement has a margin of error or if the CLI agent found workarounds.
- **[science]** The conclusion that outcome-only grading 'overestimates' performance relies on the trajectory-aware judge being ground truth. However, the judge is an LLM with a confidence threshold, and no false-positive rate is provided. The magnitude of overestimation is logically unanchored without external audit.
- **[writing]** Section 4.2 attributes the entire +31.6pp hybrid gain to orchestration. However, the 3.5% CLI baseline implies some tasks are solvable by CLI alone, contradicting P1. Reconcile the non-zero CLI score with the claim of strict channel non-substitutability.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that 'GUI-only and CLI-only settings stay at or below 3.5%' (Sec 4.3) overstates the evidence. Table 4 shows CLI-only scores of 3.5% for Opus 4.7 but 2.6% for GPT-5.5. The text implies a universal ceiling for all models, whereas the data shows model-specific variance. Qualify the statement to reflect the specific model tested or provide the max across all models.
- **[writing]** The assertion that 'outcome-only grading substantially overestimates agent performance' (Abstract) is supported by a single data point (GPT-5.5 dropping from 53.5% to 33.3%). While significant, generalizing this to 'agents' broadly without showing the variance across the other 4 GPT backbones or the Opus model in the ablation (Fig 5) is an overreach. Explicitly state the range of inflation observed across all tested backbones.
- **[science]** The claim that tasks 'cannot be solved by an equivalent single-channel rewrite' (P1, Sec 3.1) is a strong theoretical assertion. The paper demonstrates that single-channel *agents* fail, but does not provide a formal proof or exhaustive search that *no* single-channel solution exists (e.g., a CLI-only script that parses logs to infer GUI state). The text should clarify that this is an empirical observation of current agent capabilities, not a mathematical impossibility.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper details a 'trajectory-aware judge' that actively scans for and penalizes 'reward hacking' (e.g., fake screenshots, hardcoded metrics). However, the manuscript lacks a dedicated 'Safety and Ethics' section explicitly discussing the dual-use risks of training agents to detect and bypass these specific anti-fabrication measures. Authors must add a discussion on how this benchmark could be misused to develop more sophisticated deception techniques.
- **[writing]** The benchmark tasks involve real-world interactions (e.g., insurance quotes, system config, code execution) within a sandbox. The manuscript does not explicitly state whether the 'real user requests' and 'public artifacts' used to construct the 114 tasks were anonymized or if they contain any PII (Personally Identifiable Information) that might be exposed during the agent's execution or in the released dataset. A statement on data privacy and consent is required.
- **[writing]** The 'Anti-fabrication Prompt' (Appendix D) explicitly instructs agents on how to avoid detection (e.g., 'do NOT generate placeholder PNG files'). While intended to prevent cheating, this prompt effectively teaches agents the specific signatures of the evaluation system. The authors should discuss the ethical implications of releasing these specific 'jailbreak' or 'evasion' patterns alongside the benchmark, as they could be repurposed to evade safety filters in other contexts.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The interface ablation (Table 3) claims GUI-only/CLI-only settings collapse to <3.5% PassRate, but the text does not explicitly state the sample size (N) for these specific ablation runs. Given the high variance in agent performance, confirm if N=114 (full benchmark) was used for ablation or a subset, and report confidence intervals or standard errors for these low-probability events.
- **[science]** The 'trajectory-aware judge' reduces PassRate by ~20pp (Fig 4), but the judge itself is an LLM (GPT-5.5). The paper lacks a validation study of the judge's own precision/recall against human annotations. Without a human-in-the-loop audit of the judge's 'shortcut' flags (e.g., false positives on legitimate tool use), the corrected PassRate of 33.3% is not fully robust.
- **[science]** The claim that tasks satisfy 'Channel Non-Substitutability' (P1) relies on a static analysis of atomic operations (Table A1). The paper should provide empirical evidence that no single-channel agent (even with infinite retries) could solve these tasks, rather than just asserting the design intent. A 'failure mode' analysis showing single-channel agents hitting hard walls would strengthen this.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Section 5.2 and Table 1 report PassRate and Overall scores for 10 models but omit standard errors or confidence intervals. Given the N=114 tasks, calculate 95% CIs (e.g., Wilson score interval) to determine if differences (e.g., 35.1% vs 33.3%) are statistically significant.
- **[science]** The interface ablation in Section 5.3 compares Hybrid (35.1%) against CLI-only (3.5%) and GUI-only (1.8%). The text claims a '+31.6pp' gain but does not report a statistical test (e.g., McNemar's test or paired t-test) to confirm this difference is not due to random variance across the 114 tasks.
- **[science]** The trajectory-aware judge ablation (Section 5.4) claims a reduction from 53.5% to 33.3% for GPT-5.5. The paper must clarify if these are paired results (same 114 tasks) and provide a significance test for the 20.2pp drop to support the claim that shortcuts are a 'first-order failure mode'.
- **[science]** Appendix D (Table A.4) presents a 'think-budget sweep' with PassRate values (e.g., 10.5% to 33.3%) but lacks standard deviations or confidence intervals. Without error bars, the monotonic improvement claim is descriptive rather than statistically validated.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The manuscript contains significant structural duplication. Section 5 (Experiments) and its subsections (5.1-5.6) appear to be repeated or heavily fragmented in the provided source (e.g., 'e002' contains a second 'Main Results' and 'Interface Ablation' with slightly different text and table formatting). This creates a disjointed reading experience and suggests the LaTeX source is not in a final, coherent state. The authors must consolidate these sections into a single, linear narrative.
- **[writing]** In the Appendix, the 'Hybrid Trajectory Walkthroughs' section (e001/e003) uses custom environments like \begin{climode} and \begin{trajactGUI} which are not defined in the preamble. While this may be a local macro issue, the text within these blocks is presented as raw code mixed with prose, breaking the flow of the narrative. Ensure these are either properly rendered as figures/tables or integrated into the text with standard formatting.
- **[writing]** There are inconsistent formatting choices for numerical data and percentages. For instance, some tables use bolding for the best result (e.g., Table 2), while others do not. Additionally, the use of 'highlight' commands (e.g., \highlight{114}) is inconsistent; some numbers are highlighted in the text while others are not. Standardize the emphasis on key metrics throughout the document.
