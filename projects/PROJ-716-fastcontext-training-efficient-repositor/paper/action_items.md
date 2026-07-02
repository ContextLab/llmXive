# Automated-review action items — FastContext: Training Efficient Repository Explorer for Coding Agents

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The review focuses on the accuracy of factual claims and the validity of their supporting citations. Citation Mismatch in Baselines: In the "Standalone Exploration Evaluation Protocol" section (e000), the authors list "OpenHands-Bash" as a baseline and cite it with \cite{openhands,codescout}. While \cite{openhands} correctly references the OpenHands framework, \cite{codescout} refers to "CodeScout: An Effective Recipe for Reinforcement Learning of Code Search Agents." There is no logical connect

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains a grammatical error ('where shifts coding agents') and omits the subject (likely 'FastContext'), making the claim unclear.
- **[science]** Figure 1: The x-axis uses a non-linear, irregular scale (e.g., 200k to 300k is wider than 1M to 1.5M) which visually distorts the slope of the tradeoff lines and misrepresents the magnitude of token savings.
- **[writing]** Figure 1: The legend is split into two separate blocks ('Main Model' and 'FastContext Model') with inconsistent formatting, making it difficult to map the combined symbols (e.g., circle with square) to their specific components.
- **[science]** Figure 2: The y-axis label 'Estimated API cost (USD)' and the bar values ($282.47, $208.92) imply a total cost per benchmark run, but the caption describes these as 'provider-recorded GPT-5.4 API cost' without specifying if this is a mean, median, or total across the SWE-bench Multilingual suite. Without a sample size (N) or error bars, the magnitude of these costs is ambiguous and difficult to interpret as a standard metric.
- **[writing]** Figure 2: The x-axis label '4B-RL subagent' is visually crowded and the text is split across three lines, reducing readability. Additionally, the annotation '2.2% of augmented main cost' is placed directly above the bar but lacks a clear visual connector (like a bracket) to the 'augmented main cost' bar, requiring the reader to infer the comparison.
- **[science]** Figure 3: The caption claims the figure shows 'reading and searching dominate... prompt-token usage', but the bottom panel ('Total tokens') displays percentages (32.4%, 14.1%, etc.) that sum to ~93% with the 'Other' category unlabelled. It is unclear if these are shares of total tokens or just the visible categories, and the 'Other' slice is not quantified, making the claim of dominance difficult to verify.
- **[writing]** Figure 3: The caption refers to 'Left' and 'Right' panels, but the figure displays two stacked horizontal bar charts ('Turns' and 'Total tokens') without clear left/right separation or labels indicating which part corresponds to which claim in the caption.
- **[fatal]** Figure 4 caption contains multiple grammatical errors and missing nouns (e.g., 'Overview of .', 'delegates repository exploration to and receives'), making it impossible to identify the subject of the figure.
- **[science]** Figure 4: The 'Fast Context Agent' box contains a specific example ('Query(hugo-12204)') and code snippets that are not explained in the caption, making the specific workflow difficult to interpret without external context.
- **[science]** Figure 5: The red downward arrows and percentage values (e.g., '↓ 17.1%') are not defined in the caption or legend. It is unclear if these represent the shift in mean, median, or a specific quantile, making the quantitative claim ambiguous.
- **[writing]** Figure 5: The y-axis label 'Frequency' is present only on the first subplot; the remaining three subplots lack y-axis labels, which is inconsistent formatting.
- **[science]** Figure 6: The Sankey diagram labels 'File Reading' (43%) and 'Code Search' (19%) on the left side sum to 62%, but the total token count is 818k. The right side labels 'File Reading' (40%) and 'Code Search' (18%) sum to 58% of 701k. The percentages do not align with the absolute token counts shown below the bars, and the 'FastContext' category (purple in legend) is missing from the breakdown labels on the right side despite being part of the total.
- **[writing]** Figure 6: The caption contains a grammatical error and missing subject: 'substantially reduces main-agent context consumption' lacks the subject 'FastContext' or 'FC-4B-RL'.
- **[science]** Figure 7: The caption describes a two-panel figure ('Left: ... Right: ...'), but the rendered image shows only a single plot titled 'SFT Loss'. The 'Right' panel showing reinforcement-learning reward is missing.
- **[writing]** Figure 7: The x-axis label 'train/step' is placed directly on top of the data lines near x=130, making it illegible and obscuring the plot area.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript exhibits significant jargon overuse, particularly in the Introduction and Method sections, which hinders accessibility for non-specialist readers. The most critical issue is the undefined macro \approach (e.g., in the Introduction: "\approach is a read-only explorer"), which appears to be a placeholder for the system name "FastContext" but is never defined, rendering the text unintelligible. Additionally, acronyms such as SFT, RL, GRPO, SWE-bench, F1, API, CLI, JSONL, and LLM are

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** "The logical consistency of the paper is generally sound, with clear causal links between the proposed method (decoupled exploration) and the observed outcomes (token reduction). However, there are minor ambiguities in the presentation of cost accounting and the evaluation protocol that require clarification to ensure the conclusions follow strictly from the premises.\n\nFirst, in the 'Runtime Integration and Token Accounting' section, the paper presents a cost breakdown where the total system c

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that the explorer 'accounts for 2.1% and the system saves $69.03' (Section: Runtime Integration) relies on a counterfactual API pricing model ($0.20/M tokens) for the 4B-RL explorer. Since the paper states the explorer runs locally in deployment, extrapolating a specific dollar savings based on serverless API costs is an over-claim of economic impact. Clarify that the savings are relative to a hypothetical API-based baseline, not a realized deployment cost reduction.
- **[writing]** The conclusion states the method improves success 'up to 5.5%' and cuts tokens 'up to 60%'. The text cites 'GPT-5.4 on SWE-bench Pro' for the former and 'GPT-5.4 on SWE-QA' for the latter. Ensure these specific maximums are explicitly highlighted in the main text or abstract to prevent readers from inferring these gains apply universally across all benchmarks and agents.
- **[writing]** The paper claims the 4B-RL explorer 'often matches or exceeds 30B-SFT' (Section: Experiments). While Table 1 shows high performance, the text does not explicitly qualify that this comparison holds primarily for file-level F1 or specific benchmarks. Broaden the claim to specify the granularity (e.g., 'matches 30B-SFT on file-level F1') to avoid over-generalizing performance across all metrics.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Potential Risks' section (e001/e002) acknowledges that the tool may enable agents to introduce bugs or insecure changes but lacks specific mitigation strategies for the 'over-reliance' risk. Explicitly state how the system prevents the main agent from blindly executing code based solely on the explorer's citations without verification steps.
- **[writing]** The paper mentions using 'Sonnet 4.6' traces for SFT data construction (e000, e001). Clarify the data provenance and licensing status of these traces to ensure no proprietary or non-public code was inadvertently included in the training set, which could pose legal or privacy risks.
- **[writing]** While the paper states no new human-subject data was collected, the evaluation uses SWE-bench instances derived from real GitHub issues. Add a brief statement confirming that the specific 200-instance subset of SWE-bench Pro (listed in e002/e003) does not contain sensitive PII or offensive content that was not already publicly visible, or describe the filtering process used.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The RL training set is extremely small (400 prompts, 395 repos). The paper must report variance metrics (e.g., standard deviation or confidence intervals) across multiple random seeds or bootstrap resampling to rule out that the reported gains are due to favorable sampling of easy instances.
- **[science]** The SFT data (2,954 examples) is entirely distilled from Sonnet 4.6 traces. The authors must provide evidence that the 4B model learns a generalizable exploration strategy rather than simply overfitting to the specific trajectory patterns of the teacher model, especially given the small dataset size.
- **[science]** The end-to-end evaluation relies on a single main agent configuration (GPT-5.4) for the primary cost/success claims. To support the claim of a general 'efficient repository explorer,' the authors should demonstrate that the subagent's benefits hold across at least one other distinct main agent architecture or model family.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report variance measures (standard deviation or standard error) for all aggregate metrics (F1, Precision, Recall, Token counts) in Tables 1 and 2. Currently, only point estimates are provided, preventing assessment of statistical significance or effect stability across the 200+ instance benchmarks.
- **[science]** Clarify the statistical aggregation method for the 'Standalone Exploration Evaluation' (Appendix e000). The text states 'Scoring & Compute per-instance precision... then report instance-wise averages.' Confirm if the reported F1 is the mean of per-instance F1 scores or the F1 computed from aggregated true/false positives across all instances, as these yield different results for imbalanced data.
- **[writing]** The RL reward function (Eq 1 & 2, Appendix e000) includes a hard penalty for format violations. Specify if the reported 'RL reward' curves in Figure 1 are normalized or raw, and whether the KL coefficient (0.0) implies no KL-divergence penalty was applied during the reported runs, which may affect the stability of the policy updates.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 'Standalone Exploration Evaluation Protocol' (e001), the text references 'Table~\ref{tab:explore-protocol}' but the subsequent table environment is labeled 'tab:explore-protocol' in the source (e003) yet the caption in e003 is missing the table environment start, creating a broken reference chain. Ensure the label and reference match the actual table structure.
- **[writing]** The 'SWE-bench Pro Subset' appendix (e002/e003) lists 200 instance IDs in a single enumerated list. This creates a massive wall of text that disrupts readability. Consider moving this list to a separate supplementary file or a compressed table format in the main text to improve flow.
- **[writing]** In the 'Prompt Templates' section (e001), the text states 'Below is a representative example (full texts are included in the original source).' Since this is the full manuscript, this phrasing is confusing. Clarify if the full texts are in the appendix or if the examples provided are the full texts.
