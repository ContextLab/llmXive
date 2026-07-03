# Automated-review action items — Code as Agent Harness

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 4.1.1 claims LingmaAgent resolves 16.9% of issues autonomously and 43.3% with intervention, citing ma2025alibaba and li2026advances. Verify these specific percentages in the cited sources, as the text does not explicitly state these exact figures in the provided snippets.
- **[writing]** Section 4.1.4 states El Agente Q exceeds 87% success and Virtual Lab designed 92 nanobodies with 2 validated, citing Zou_2025 and swanson2025virtual. Confirm these specific numbers are present in the cited works, as the provided bibliography entries lack abstracts or results sections.
- **[writing]** Section 4.1.5 claims AIDE achieves 16.9% bronze medal rate on MLE-bench, citing huang2024mlagentbenchevaluatinglanguageagents and chan2025mlebenchevaluatingmachinelearning. Ensure the 16.9% figure is explicitly attributed to AIDE in these sources and not a general benchmark statistic.
- **[writing]** Section 4.2.1 claims QualityFlow uses 'Imagined Execution' with 98%+ precision, citing Hu2025QualityFlow. Verify that the cited paper explicitly reports this precision metric for the imagined execution component.
- **[writing]** Section 4.2.1 states ChatDev terminates after 10 rounds or fixed phases. Verify this specific iteration limit (10) is a hard constraint defined in Qian2023ChatDev, as the provided text does not confirm the exact number.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 3: 'MapCoder' appears in both the 'Planning' and 'Tool Use' rows, but the figure provides no visual distinction (e.g., color, icon, or label) to indicate if it is the same work or different variants, creating ambiguity.
- **[science]** Figure 3: 'AgentCoder' appears in both the 'Tool Use' and 'Control' rows with the same logo and year (2023), yet the figure lacks a mechanism to clarify if this is a single work spanning categories or a duplicate entry.
- **[science]** Figure 3: 'OpenHands' appears in both the 'Tool Use' and 'Optimization' rows with the same logo and year (2025), but the figure does not visually distinguish between these instances or explain the relationship.
- **[science]** Figure 3: 'SWE-Agent' appears in both the 'Memory' and 'Control' rows with the same logo and year (2024), but the figure lacks a legend or visual cue to clarify if this is the same work or distinct variants.
- **[writing]** Figure 3: The timeline at the top uses colored dots (2023-2026) but lacks a legend defining what the colors represent or how they map to the specific years listed below.
- **[science]** Figure 8: The timeline includes publication years 2025 and 2026 (e.g., 'CodePRM (2025)', 'ExecVerify (2026)') for works that have not yet been published, which is factually impossible for a scientific roadmap of existing literature.
- **[writing]** Figure 8: The logos for various institutions and companies (e.g., Google, NVIDIA, TUM) are used to identify the authors of the works but are not defined in a legend or caption, requiring external knowledge to interpret.
- **[writing]** Figure 10: The top-right text '(▷§Sec. 3.5)' is a raw LaTeX cross-reference command that was not rendered into a clean section link or title, indicating a compilation or formatting oversight.
- **[writing]** Figure 12: The caption lists 'adaptive coordination' as the fourth category, but the figure's y-axis label reads 'Adaptive Orchestration'; align the text to match the visual label.
- **[writing]** Figure 12: Several logos (e.g., 'sea | AI lab', 'aws') are used as markers without a legend or explicit definition in the caption explaining their role as institutional affiliations.

## paper_reviewer_jargon_police — verdict: full_revision

- **[science]** The manuscript suffers from significant jargon overuse, particularly in the introduction and the "Open Problems" sections, where the authors coin or repurpose terms without sufficient definition for a general audience. The central term "harness" is used as a proper noun ("Code as Agent Harness") throughout, yet the text never explicitly defines it as the "runtime infrastructure and execution environment" distinct from the model itself. This forces the reader to infer the meaning from context, wh

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim that 'LLM-simulated execution achieves 98%+ precision/recall' (Section 4.1, Patterns and Trends) is presented as a general fact without a specific citation or scope definition. This risks over-generalizing results from a single method (QualityFlow) to the entire field of simulated execution. Please clarify the source and limit the claim to the specific system studied.
- **[writing]** The statement that 'No system fully unifies both' repository-based and execution-based representations (Section 4.1, Patterns and Trends) is a strong negative claim. Given the breadth of the survey, the authors should either provide a definitive list of excluded systems or soften the language to 'No major system surveyed fully unifies...' to avoid over-claiming completeness.
- **[writing]** The paper cites 'GPT-5-Codex' and 'GPT-5.1-Codex-Max' (Section 5.1) as existing systems trained on long-horizon interactions. As these refer to unreleased or hypothetical model versions (given the 2026 date context), the authors must explicitly state these are projections or future work, rather than presenting them as established empirical facts to avoid over-claiming current capabilities.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper discusses 'Human-in-the-Loop Safety' and 'Sandboxed Execution' extensively (Sec 3.4, 4.3) but lacks a dedicated Ethics/Safety section detailing specific mitigation strategies for dual-use risks (e.g., autonomous code generation for malware, supply chain attacks). Explicitly address how the proposed harness prevents or detects malicious intent in generated code.
- **[writing]** In Section 4.1 (Code Assistants), the paper cites 'solution leakage' in benchmarks (e.g., SWE-bench). The review must clarify the ethical implications of training agents on data that may contain private or proprietary code, and whether the survey addresses data provenance and consent for the training corpora of the cited systems.
- **[writing]** Section 4.3 mentions 'Self-Driving Labs' and 'Scientific Discovery' where agents execute physical experiments. The manuscript needs to explicitly discuss safety protocols for physical harm (e.g., chemical synthesis, robotics) and the ethical boundaries of autonomous experimentation, rather than treating safety only as a software sandboxing issue.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The manuscript cites specific quantitative performance metrics (e.g., '98%+ precision' for QualityFlow, '16.9% bronze' for AIDE, '41 of 58' compounds for A-Lab) without providing the underlying sample sizes, confidence intervals, or statistical significance tests. For a survey paper, these claims require explicit citation to the primary source's statistical analysis or a summary of the experimental design (N, controls) to verify robustness.
- **[science]** Several claims regarding 'state-of-the-art' performance or 'best accuracy' (e.g., failure attribution accuracy of 14-53%) lack a clear definition of the evaluation protocol or the specific benchmark versions used. Without specifying the test sets and baseline comparisons, these ranges are difficult to interpret as robust scientific evidence rather than anecdotal observations.
- **[science]** The paper discusses 'simulated execution' achieving high precision but does not quantify the divergence between simulated and real-world execution in terms of error rates or specific failure modes. A brief quantitative comparison or a citation to a study that explicitly measures this gap is needed to support the claim that simulation is a sufficient proxy for verification.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The manuscript cites specific performance metrics (e.g., LingmaAgent 16.9%/43.3% in §5.1, AIDE 16.9% bronze in §5.1, 98%+ precision for Imagined Execution in §4.2) without providing confidence intervals, sample sizes (N), or statistical significance tests. As a survey, it must clarify if these are point estimates from single runs or aggregated results with variance.
- **[science]** Section 4.2 claims '98%+ precision' for QualityFlow's Imagined Execution. The review requires the specific dataset size, the definition of the ground truth used for this calculation, and whether this figure represents a mean over multiple seeds or a single experimental run to assess reproducibility.
- **[science]** In §5.1, the claim that 'best step-level attribution accuracies' are in the '14–53% range' aggregates results from multiple studies (cemri2025whymas, zhang2025whoandwhen, etc.). The text should explicitly state the sample sizes and experimental conditions for each cited study to ensure the range is statistically comparable across different benchmarks.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The manuscript contains significant structural duplication. Section 3 ('Harness Mechanisms') and Section 4 ('Scaling the Harness') appear twice in the source (e.g., e000 vs e004/e005), with conflicting table definitions and figure references. This must be consolidated into a single, linear narrative flow before publication.
- **[writing]** Several tables are truncated in the source with '(... N rows omitted ...)' or '(... 10 rows omitted ...)' placeholders (e.g., Table 2 in e001, Table 4 in e005). These must be fully expanded or the text must explicitly state that the table is illustrative, as incomplete tables disrupt readability and data integrity.
- **[writing]** Inconsistent citation formatting exists between \cite{} and \citep{} commands throughout the text (e.g., Section 5.1.1 uses \citep while Section 5.1.2 uses \cite). Standardize to the target venue's required style (likely \citep for parenthetical) to ensure professional consistency.
- **[writing]** The 'Open Problems' section (Section 5.2) is split across multiple chunks (e002, e003, e004) with disjointed subheadings. Ensure the final compilation presents a unified, logically ordered list of open problems without redundant introductions or broken transitions.
