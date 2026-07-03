# Automated-review action items — TUA-Bench: A Benchmark for General-Purpose Terminal-Use Agents

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** Section 4.1 claims tasks were selected for 'lowest solvability' across specific models, yet results show ~60% success for frontier models. Clarify if 'lowest' is relative to a larger pool or if the selection criteria description is inaccurate regarding the resulting difficulty.
- **[writing]** Task distribution percentages in Section 4.3 (Office 38.3%, Web 18.3%, Multimedia 13.3%) sum to 69.9%, leaving 30.1% for two categories. However, the text states only 20 professional tasks exist (16.7%). The math for the remaining categories is inconsistent with the stated 100/20 split.
- **[writing]** The bibliography cites 'anthropic2026opus47' but the results table and text highlight 'Claude Opus 4.8' as the top performer. Add a specific citation for the Opus 4.8 model to support the claim that it was evaluated and achieved 65.8%.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The 'Cost Efficiency' chart (bottom right) contains illegible text labels for data points (e.g., model names like 'Terminus-2', 'Codex', 'Claude Code') and axis values due to low resolution and small font size.
- **[writing]** Figure 1: The 'Success Rate by Task Category' bar chart (middle right) lacks a Y-axis label and scale, making the percentage values (e.g., 61%, 52%) the only reference for magnitude.
- **[science]** Figure 3: The caption claims the connected line marks the Pareto frontier, but the dotted line connects points that are not Pareto-optimal (e.g., the 'Terminus-2 MiniMax-M3' point at ~$12 is connected to 'Terminus-2 GLM-5.1' at ~$23, yet there are other points with higher success rates at similar or lower costs, such as the orange square at ~$30 with ~41% success). A true Pareto frontier should only connect points where no other point has both higher success rate and lower cost.
- **[writing]** Figure 3: The x-axis label 'Cost per run (USD)' is clear, but the axis scale is logarithmic without explicit indication (e.g., no log-scale notation or tick labels like 10^1, 10^2), which may mislead readers about the spacing of cost values.
- **[writing]** Figure 3: The legend defines 'Agent' shapes and 'Model' colors, but some points (e.g., the red triangle labeled 'Claude Code') use a shape (triangle) that corresponds to 'Claude Code' in the Agent legend, yet the color (red) corresponds to 'Claude Opus 4.8' in the Model legend — this dual encoding is not explicitly explained in the caption, potentially causing confusion about which attribute (agent or model) is being emphasized for each point.
- **[writing]** Figure 4 caption contains a broken cross-reference: 'A more detailed, task-level breakdown of success rates is provided in .' The target figure name or number is missing.
- **[writing]** Figure 4 legend labels include version numbers (e.g., 'GPT-5.5', 'Claude Opus 4.8') that do not match the model names in the paper title or other figure captions (e.g., 'GPT-4', 'Claude 3.5'), creating potential confusion about which models are evaluated.
- **[writing]** Figure 5: The x-axis labels (task names) are rotated 45 degrees and overlap significantly, making them illegible and cluttered.
- **[writing]** Figure 5: The caption states 'grouped by category and subcategory' and mentions 'n' (number of tasks) below groups, but the rendered image lacks the vertical separator lines and the 'n' counts shown in the related Figure 4.
- **[writing]** Figure 6: The x-axis labels (agent + model + effort) are extremely dense, rotated, and illegible, making it impossible to distinguish specific configurations without zooming in significantly.
- **[writing]** Figure 6: The y-axis task labels are similarly dense and rotated, causing overlap and rendering many task names unreadable.
- **[science]** Figure 6: The colorbar legend is missing from the rendered image; while the caption defines the red-to-green scale, the visual key is absent from the figure itself.
- **[writing]** Figure 7: The x-axis labels for the reasoning effort settings (none, low, medium, high, xhigh, max) are rotated 90 degrees and rendered at a font size that is illegible in the provided image, making it impossible to distinguish the specific effort level for each column.
- **[writing]** Figure 7: The task identifiers and names on the y-axis are extremely small and densely packed, rendering them illegible without significant zooming, which contradicts the caption's instruction to 'zoom in' to view details.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript generally avoids excessive jargon, but several terms and acronyms are used without definition, potentially excluding non-specialist readers. First, in Table 1 (line 108), the column header MM is used to denote "Multimodal" requirements. This abbreviation is not defined in the table caption or the surrounding text. While common in computer vision circles, it is opaque to a general audience. The authors should spell out "Multimodal" or define "MM" at first use. Second, the term Scaf

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 3.3 lists five task families but only provides percentages for three (summing to 70%). The missing percentages for 'System & Software Operations' and 'Scientific & Engineering' break the logical link to the claimed total of 120 tasks.
- **[science]** Section 4.2 text claims GPT-5.5 has All-5 of 42.5% and Opus 4.8 has 31.7%, but Table 1(a) shows the reverse (Opus 4.8: 42.5%, GPT-5.5: 31.7%). The text contradicts the table data it cites.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that tasks are 'co-designed with PhD-level domain experts' (Abstract, Sec 1) is over-claimed given the lack of methodological detail. The paper does not specify the number of experts, their specific qualifications, the iterative design process, or how their input was validated. Without this, the 'expert' label is a marketing term rather than a scientific claim. Add a subsection detailing the expert curation protocol.
- **[science]** The statement that tasks were 'converted to CLI' from OSWorld (Sec 3.2.1) implies a direct mapping that may not exist. Many OSWorld tasks rely heavily on visual GUI cues (e.g., specific button locations, drag-and-drop) that do not have direct CLI equivalents. The paper over-reaches by suggesting these are 'real-world' terminal tasks without explaining how the semantic gap between GUI intent and CLI execution was bridged or if the tasks were fundamentally altered.
- **[writing]** The benchmark claims to evaluate 'general-purpose' agents (Title, Abstract), yet the task distribution is heavily skewed toward Office/Productivity (38.3%) and System Ops, with only 20/120 tasks in Scientific/Engineering domains. The term 'general-purpose' suggests broad coverage across all computing domains, but the data does not support a claim of generalization beyond office automation and basic system administration. Temper the 'general-purpose' claim or expand the scientific task set.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** Task 107 (073-force-quit-frozen-doc) and Task 107 (106-create-charles-ssh-user) involve creating system users and modifying OS configurations. The paper must explicitly state that these tasks are executed in isolated, disposable containers (Harbor framework) and that no persistent system changes or real user accounts are created on host machines to prevent privilege escalation risks.
- **[writing]** Several tasks (e.g., 027-add-dota-dlc-cart, 037-electric-cars-under-50k) involve interacting with live commercial websites (Steam, Cars.com). The manuscript should clarify the protocol for rate limiting, bot detection avoidance, and ensuring that automated agents do not violate Terms of Service or incur unintended financial charges during benchmark execution.
- **[writing]** Task 044 (044-etsy-saved-passwords) and Task 099 (098-extract-email-doc-image) involve accessing sensitive user data (passwords, emails). The authors must confirm that all test data used in the benchmark is synthetic or anonymized, and that the evaluation protocol explicitly forbids agents from exfiltrating or logging real credentials.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Clarify the statistical significance of the reported performance gaps. Table 1 reports means with standard deviations (e.g., 65.8 ± 0.7 vs 64.7 ± 0.7), but no hypothesis tests (e.g., paired t-tests or bootstrap confidence intervals) are provided to confirm these differences are not due to random variance across the 5 trials.
- **[science]** Address potential selection bias in the 'Everyday Digital Tasks' subset. The text states 100 tasks were retained based on 'lowest solvability' across three specific models. This curation method risks overfitting the benchmark to the failure modes of those specific models, potentially inflating the difficulty for other architectures or under-representing tasks where those models happen to succeed.
- **[science]** Provide a detailed breakdown of the 'Professional Scientific Tasks' validation. While the paper mentions co-design with PhD experts, it lacks quantitative inter-rater reliability metrics or a description of the validation protocol used to ensure the 20 tasks are solvable and unambiguous, which is critical for the reliability of the benchmark's 'depth' claim.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Section 4.1 and Table 1 report success rates with standard deviations (e.g., 65.8 ± 0.7) derived from 5 trials. The manuscript must explicitly state the statistical test used to determine if the difference between the top two agents (65.8% vs 64.7%) is significant, or provide confidence intervals. Without this, the claim of 'highest score' is not statistically supported given the small sample size (n=5).
- **[science]** The ablation study on 'Thinking-effort scaling' (Section 4.2) reports monotonic gains (36.5% to 60.1%) but lacks error bars or significance testing. Given the high variance often seen in LLM benchmarks, the authors must verify if the gain from 'high' to 'xhigh' is statistically distinguishable from noise before claiming 'diminishing returns'.
- **[science]** The task selection process for the 'Everyday Digital Tasks' (Section 3.2.1) states tasks were retained based on 'lowest solvability' across three models. The authors must clarify if this selection introduced bias (e.g., selecting only tasks where models failed consistently) and if the resulting distribution of difficulty is representative of the broader domain, or if it artificially inflates the benchmark's difficulty.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.1 (Task Curation), the sentence 'Rigorous human verification removes input-gold mismatches' is vague. Specify the verification protocol (e.g., 'Two independent annotators verified...') to improve clarity and reproducibility.
- **[writing]** Section 4.2 (Main results) contains inconsistent phrasing: 'GPT-5.5 (60.1%) and Claude Opus 4.8 (59.7%) are close on Terminus-2, but reliability differs'. Clarify that the reliability difference refers to the 'All-5' metric explicitly in the same sentence to avoid ambiguity.
- **[writing]** The Appendix task descriptions (e.g., Task 082, 098, 106) contain placeholder text like '{path}' instead of specific file paths. Replace these with concrete examples or a consistent notation (e.g., '<input_path>') to ensure the text is self-contained and readable.
