# Automated-review action items — Agents' Last Exam

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Abstract claims 2.6% average pass rate across configurations, but Table 1 shows lowest overall rate is 4.4%. Clarify if 2.6% refers only to the Last-Exam tier.
- **[writing]** Section 3.1 cites 82% Terminal-Bench score for Codex/GPT-5.5. Verify `merrill2026terminalbench` explicitly reports this exact figure and configuration.
- **[writing]** Section 3.1 claims ALE-CLI is 'substantially harder' based on a drop from 82% to 25.2%. Ensure the 82% baseline is directly comparable in protocol and difficulty.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption references 'Table' without a number, making it impossible to verify the harness-backbone configurations shown in the bubbles.
- **[science]** Figure 1: The legend defines bubble area as proportional to 'Total tokens' (100M–1000M), but the caption states 'bubble area is proportional to total token consumption' without specifying units or scale, creating ambiguity in interpretation.
- **[writing]** Figure 1: Panel (a) x-axis label 'Total API Cost (USD)' lacks currency symbol formatting consistency with scientific convention; consider '$' prefix or explicit note.
- **[writing]** Figure 2: The caption contains a typo 'Point size $$ total task instances per cluster' where a verb (e.g., 'indicates') is missing between the subject and the definition.
- **[writing]** Figure 2: The legend is missing from the rendered image; the caption defines point size but does not define the color mapping for the taxonomy clusters shown in the plot.
- **[science]** Figure 3: The 'Vary Harness (GPT-5.5 fixed)' group contains 'Codex', 'OpenClaw', 'ALE-Claw', 'Cursor', and 'Droid'. However, the caption states the spread is 5.3--6.0pp, while the visual range for this group is ~19% to ~25% (a 6pp spread). The 'Vary Harness (Opus 4.7 fixed)' group shows 'Cursor', 'ALE-Claw', 'Claude Code' with a range of ~14.5% to ~19% (a 4.5pp spread). The caption claims 5.3-6.0pp for the latter, but the visual data suggests a smaller spread. The text '5.3pp' and '6.0pp' are pl
- **[writing]** Figure 3: The legend distinguishes 'Harness effect' (orange) and 'Model effect' (blue), but the x-axis labels are 'Vary Harness (GPT-5.5 fixed)', 'Vary Harness (Opus 4.7 fixed)', and 'Vary Model (OpenClaw fixed)'. The first two groups are both 'Vary Harness' but use different fixed models, which is not reflected in the legend. The legend should clarify that orange represents varying harnesses (with different fixed models) and blue represents varying models (with a fixed harness).
- **[writing]** Figure 4: The caption contains a placeholder error: 'Near-Term tier ( task instances)' is missing the count (likely 59, matching the plot title).
- **[writing]** Figure 4: The x-axis labels (model/harness names) are rotated and densely packed, making them difficult to read without zooming.
- **[writing]** Figure 5: The caption contains a placeholder error, reading 'Full-Spectrum tier ( task instances)' with a missing integer count for the number of instances.
- **[writing]** Figure 5: The x-axis labels (model/harness combinations) are rotated and densely packed, making them difficult to read without significant zooming.
- **[writing]** Figure 6: The caption contains a placeholder error: 'Last-Exam tier ( task instances)' is missing the specific count of instances.
- **[writing]** Figure 6: The x-axis labels are rotated and densely packed, making model names (e.g., 'OpenClaw / Grok 4.3') difficult to read.
- **[science]** Figure 6: The y-axis lists task instance names but lacks the color-coded domain indicators shown in the legend, forcing reliance on text color which is hard to distinguish.
- **[writing]** Figure 7: The caption contains a broken cross-reference ('appear in Figure .') where the figure number is missing.
- **[science]** Figure 7: The 'Visual & Media Arts' label is positioned in a central overlap region, but the associated icons (e.g., Unity, Blender) are scattered across the center and right, making the domain boundary ambiguous.
- **[writing]** Figure 8: The caption describes a linear pipeline, but the diagram includes a feedback loop from 'QC Committee Review' back to 'Expert Task' (Submission/Editing) without a legend or label explaining the iteration logic.
- **[writing]** Figure 8: The text 'Website Display' and 'Backend Trigger & Email Notified' are positioned ambiguously between the pipeline steps and the UI screenshots, lacking clear arrows or connectors to indicate their specific role in the workflow.
- **[science]** Figure 9: The 'Hands' (Tools) row for CLI-Agents is marked 'Full', but CLI agents typically lack GUI tool interaction; the diagram implies CLI agents have full tool capabilities which contradicts the standard definition of CLI vs GUI agents.
- **[writing]** Figure 9: The legend at the bottom right is incomplete; it defines 'Full', 'Limited', and 'N/A' symbols, but the 'Limited' symbol (half-filled circle) is not explicitly defined in the text, relying on visual inference.
- **[fatal]** Figure 10: The caption describes four panels (a, b, c, d), but the rendered image displays only a single panel (domain-level mean scores). The figure is incomplete.
- **[science]** Figure 10: The x-axis label 'Mean score (%)' is present, but the axis lacks tick marks and grid lines, making it difficult to accurately read the specific values for each domain.
- **[science]** Figure 12: The legend defines orange as 'Unverified' (expert submissions awaiting QC), but the caption states 'All subdomains receive non-zero coverage.' The 'Transport. & Safety' subdomain 'Maritime & Port Operations' shows only a blue bar (13) and no orange bar, contradicting the claim that all subdomains have unverified submissions.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'CUA' (Computer-Use Agent) at first use in Section 2.2. The text currently uses 'CUA' and 'GCUA' without explicitly spelling out the acronym 'Computer-Use Agent' in the main body, relying on the reader to infer it from context or the appendix.
- **[writing]** Replace the acronym 'GCUA' with 'Generalist Computer-Use Agent' or 'generalist agent' throughout the text. The term 'GCUA' is introduced but then used repeatedly as a standalone noun (e.g., 'evaluate all agent systems in GCUA configuration'), which is non-standard and excludes non-specialist readers.
- **[writing]** Define 'MCP' (Model Context Protocol) at first use in Section 2.2 and Appendix A.1. The text mentions 'CUA MCP bridge' and 'MCP server' without defining the protocol, assuming reader familiarity with a specific industry standard.
- **[writing]** Replace 'harness' with 'orchestration framework' or 'agent framework' in the main text. While 'harness' is common in testing, its use to describe the entire agent loop (e.g., 'mainstream harness implementations') is jargon-heavy and less accessible than 'framework' or 'system'.
- **[writing]** Define 'SOC' (Standard Occupational Classification) at first use in the Abstract and Section 2.2. The text references 'SOC 2018' immediately without spelling out the classification system, which is not universally known outside labor economics or specific US government contexts.
- **[writing]** Replace 'backbone' with 'foundation model' or 'base model' in the main text. The term 'backbone' (e.g., 'backbone configurations', 'fixed backbone') is technical jargon from deep learning architecture that may confuse readers from other domains.
- **[writing]** Define 'QC' (Quality Control) at first use in Figure 2 caption. The caption mentions 'Quality Control (QC) Process' but the acronym 'QC' is used later in the text without re-definition or context for non-industry readers.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 2.3 claims the public set includes the 'full Last-Exam tier' while the private pool has 'more Near-Term tasks.' This implies the private pool is easier, contradicting standard benchmark design where hard tasks are often kept private. Clarify the distribution logic to resolve this apparent contradiction with the 'Last-Exam' difficulty definition.
- **[writing]** Appendix A.4 states timeout cases are 'excluded from this breakdown' (the taxonomy), yet Table A.3 explicitly reports timeout rates and scores. Clarify that timeouts are excluded from the *taxonomy analysis* but included in *performance metrics* to avoid confusion about whether they are counted as failures.
- **[science]** The Abstract and Section 3.1 cite an 'average full pass rate is 2.6%' for the hardest tier. Table 1 shows top models achieving 8.6% on Last-Exam. Verify this statistic against the table data or specify the exact subset of configurations used to derive 2.6% to ensure consistency.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Claiming ALE covers 'all 55 SOC/O*NET industries' (Table 1) overreaches; Appendix A.1 notes 4 subdomains are 'frontier extensions' not in SOC 2018. Clarify that coverage applies to the paper's extended taxonomy, not the federal standard itself.
- **[writing]** The claim that ALE will 'close the gap' to GDP impact (Abstract/Intro) lacks empirical support linking scores to economic output. Temper this to state ALE is a 'proxy instrument intended' to measure such impact, not a proven mechanism.
- **[writing]** Stating ALE-CLI tasks are 'substantially harder' than Terminal-Bench (Sec 3.1) relies on a single performance gap without difficulty distribution analysis. Qualify as 'observed lower performance' rather than an intrinsic hardness claim.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The manuscript lacks an explicit statement regarding IRB approval or ethics committee oversight for collecting workflows from 250+ industry experts. Add a formal ethics statement or exemption justification in Section 3.3 or Appendix B.
- **[writing]** The 'GUI-as-Tool' mode grants agents full desktop control. The paper must explicitly detail sandboxing measures beyond standard VM isolation to prevent host escape, external network access, or modification of systems outside the task scope.
- **[writing]** Tasks in radiology and cybersecurity raise dual-use and privacy risks. Clarify HIPAA/GDPR compliance for patient data in radiology tasks and confirm cybersecurity tasks use synthetic/public data to prevent generating real exploits.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim that the public subset is representative of the full pool relies on a single correlation (r=0.89) for one agent configuration (Appendix~ef{app:fullpool}). Validate this across multiple models or explicitly discuss the limitation.
- **[science]** The failure taxonomy relies on an LLM classifier without reported inter-rater reliability or human validation (Appendix~ef{app:failure-taxonomy}). Add reliability metrics to support the conclusion that 'Understanding' errors dominate.
- **[science]** Table~ef{tab:main-results} reports standard deviations from repeated runs of single instances but lacks variance across the 150 diverse tasks. Report standard error of the mean across tasks to assess statistical significance of harness differences.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Table 1 reports standard deviations (±) for a subset of configurations based on 'three independent runs' but does not specify the unit of aggregation (e.g., mean of 3 runs per task vs. 3 runs per task instance). Clarify the statistical unit and aggregation method to ensure reproducibility of the error bars.
- **[science]** The paper claims a 'strong correlation' (r=0.89, p<0.001) in Appendix Fig. 1 regarding public vs. full-pool representativeness. However, the sample size (n=13 clusters) is small for a robust Pearson correlation. Report the 95% confidence interval for the correlation coefficient and consider discussing the stability of this estimate given the low degrees of freedom.
- **[writing]** In the failure taxonomy analysis (Appendix), percentages sum to 100% of 'classifiable failures' (47% + 31% + 22%). Explicitly state the total number of failed runs analyzed and the percentage of total failures that were excluded (e.g., due to timeout or infrastructure issues) to avoid selection bias in the reported distribution.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 2.1 (Benchmark Design Principles), the examples contrasting 'Undesired' and 'Better' tasks use inline color commands (\colorbox) that are visually distracting and non-standard for academic prose. Rephrase these as standard text or use a formal table to improve readability and flow.
- **[writing]** In Section 3.2 (Agent Architecture), the sentence 'The rare appearance single 'task' refers to the runnable instance level' contains a grammatical error and is unclear. It should be revised to 'The rare appearance of the single word 'task' refers to the runnable instance level' or similar for clarity.
- **[writing]** In Appendix A.1 (Taxonomy Definition), the phrase '1{,}016 entries' uses a LaTeX-specific number formatting command that may not render correctly in all viewers. Ensure consistent number formatting (e.g., 1,016) throughout the text for better readability.
- **[writing]** In Appendix A.4 (Task Construction Pipeline), the sentence 'If the engineer discovers gaps... the system triggers an automatic email notification, routing the task log back to the expert to unblock development' is slightly wordy. Consider tightening to '...the system triggers an automatic notification to the expert to unblock development'.
