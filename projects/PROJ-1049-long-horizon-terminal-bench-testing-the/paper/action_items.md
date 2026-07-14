# Automated-review action items — Long-Horizon-Terminal-Bench: Testing the Limits of Agents on Long-Horizon Terminal Tasks with Dense Reward-Based Grading

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: reject

- **[fatal]** The paper contains critical factual inconsistencies and likely hallucinated references that invalidate its central claims. First, there is a direct contradiction in the number of models evaluated. The Abstract, Introduction, and Conclusion consistently state that 15 frontier models were evaluated. However, Table 1 (tab:lhtb-cost) lists exactly 14 models. Furthermore, Section 3.1 explicitly mentions analyzing "14 x 46 model task runs." This discrepancy means the reported averages (e.g., "mean pas

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption states there are 46 tasks, but the sum of the counts shown on the bars (7+6+6+6+5+5+4+4+3) is only 46. However, the percentages (15+13+13+13+11+11+9+9+7) sum to 101%, suggesting a rounding error or inconsistency in the data presentation.
- **[science]** Figure 2: The x-axis label 'Estimated total cost (USD, log scale)' is misleading because the axis lacks tick marks and grid lines for the log scale, making it impossible to verify the logarithmic spacing or read specific cost values for the data points.
- **[writing]** Figure 2: The legend at the top left ('Pareto frontier (bold labels)') is redundant and potentially confusing; the caption already defines the dashed line and bold labels, and the legend does not explain the meaning of the different colored dots.
- **[writing]** Figure 3: The caption text is truncated at the end ('...while th'), cutting off the final sentence.
- **[science]** Figure 3: The x-axis label 'Unresolved runs (of 46 tasks)' is ambiguous; it should explicitly state that the bar lengths represent the count of unresolved runs to clarify that the total length varies by model.
- **[writing]** Figure 4: The caption contains a broken LaTeX placeholder 'threshold $$' instead of the intended variable (e.g., $R \ge 0.9$).
- **[writing]** Figure 4: The y-axis labels are crowded and overlap, making model names like 'GLM 5.1' and 'GPT-5.3 Codex' difficult to distinguish.
- **[science]** Figure 5: The caption states 227 runs (32.9%) make no meaningful progress ($R < 0.05$), but the chart labels the first bin as 224 runs (32.6%); the numbers do not match.
- **[science]** Figure 5: The caption claims 180 runs (26.1%) reach $R \ge 0.5$, but summing the counts for bins $\ge 0.5$ in the chart (38+20+23+54+30) yields 165 runs (23.9%).
- **[writing]** Figure 5: The caption text is truncated at the end ('dense subtask-lev'), cutting off the final sentence.
- **[writing]** Figure 6: The caption is grammatically incomplete ('...long-horizon terminal task' should be 'tasks') and lacks the specific detail found in the other captions (e.g., Figure 1's mention of '46 tasks' or Figure 5's '15 x 46 runs'), making it vague relative to the paper's scope.
- **[science]** Figure 6: The diagram illustrates the general pipeline (Task Construction -> Runtime -> Evaluation) but fails to visually depict the 'dense reward grading' mechanism mentioned in the title and caption; the reward accumulation shown in Panel C is a result, not a structural component of the grading logic itself.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 2.2 (Subtask-based grading): The symbol `R` is used in the equation and immediately in the text ('task reward is R') without an explicit definition of what `R` represents (e.g., 'where R is the normalized task reward'). While context implies it, a formal definition clause is missing for a reader outside this specific subfield.
- **[writing]** Section 2.2: The term 'Harbor task' is introduced ('specified as a Harbor task') without defining what 'Harbor' is. While a citation is provided later, the first use assumes the reader knows 'Harbor' is a specific framework or task format. Add a brief gloss, e.g., 'a task defined within the Harbor framework [Citation]'.
- **[writing]** Section 3.1 (Metrics): The metric 'pass@1' is used without definition. While standard in ML, for a reader from an adjacent field (e.g., systems or robotics), it is not immediately obvious if this means 'pass rate with 1 attempt' or 'pass rate of the best of 1 attempt'. Define at first use: 'pass@1 (the fraction of tasks solved in a single attempt)'.
- **[writing]** Section 3.2: The phrase 'near-misses' is used as a defined category ('Dense grading also reveals near-misses...') but is not explicitly defined with a threshold until the parenthetical ($0.75 \leq R < 0.95$). Define the term at its first introduction to avoid ambiguity.
- **[writing]** Section 4.1: The term 'false finish' is introduced and defined in the text, but the symbol `R` is used in the definition ('early exit at relatively high reward... with $R \geq 0.75$') without re-stating that `R` is the task reward defined in Section 2.2. Ensure notation consistency or re-define `R` if the context is distant.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 3.4 claims tasks span '21 high-level categories,' contradicting the Abstract, Figure 1, and Appendix which state 'nine categories.' Align Section 3.4 to 'nine' or clarify the taxonomy.
- **[writing]** Section 4.1 groups three models at '6.5% (3/46) each' without noting their vastly different episode counts (183 vs 321). Clarify that the grouping is strictly by pass rate to avoid implying equivalent performance profiles.
- **[writing]** Section 5.1/5.2 failure mode counts (518 timeouts, 124 early exits) do not perfectly match the stated percentages (79%, 19%) of the total 660 runs. Provide exact counts for all categories to ensure the percentages sum correctly.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract and Introduction conflict on taxonomy count ('nine' vs '21' categories). Unify these claims to accurately reflect the benchmark's scope and avoid misleading readers about its diversity.
- **[writing]** Abstract claims the benchmark stresses 'planning' and 'bug refinement,' but Section 5.1 shows 79% of failures are timeouts with low reward, indicating the primary bottleneck is time-budgeting/efficiency, not just those cognitive skills. Narrow the claim to reflect the evidence.
- **[writing]** Conclusion states early exits 'frequently' reflect weak self-verification, but Section 5.2 shows this applies to only ~11% of early exits (14/124). Rephrase to 'a subset of early exits' to match the quantitative evidence.

## paper_reviewer_safety_ethics — verdict: accept

This paper introduces a benchmark for evaluating long-horizon AI agents in terminal environments. From a safety and ethics perspective, the work is low-risk by construction. The benchmark tasks are designed to be self-contained within containerized environments, and the evaluation methodology relies on deterministic, environment-grounded graders rather than human-subjects data or sensitive personal information.

The task list (Appendix) includes categories such as "Systems, performance & security" (e.g., `poc-exploit-craft`, `grammar-fuzz-coverage-hunt`). While these tasks involve security-related concepts (generating proof-of-concept inputs, fuzzing), the paper describes them as benchmarking the agent's ability to interact with a terminal and solve a defined problem within a sandbox. The paper does not provide operational details for exploiting real-world vulnerabilities, nor does it release a dataset of live exploits or actionable attack vectors against external systems. The "proof-of-concept" nature is confined to the benchmark's internal grading logic (e.g., triggering a sanitizer or maximizing coverage in a provided binary), which is standard for security benchmarking research (similar to SWE-Bench or Terminal-Bench).

There is no evidence of human-subjects data collection, PII exposure, or license violations regarding the data used (which appears to be synthetic or derived from public open-source projects for the purpose of creating broken states). The paper does not describe a system designed to deceive, manipulate, or covertly surveil users.

Consequently, there are no foreseeable, non-trivial risks of harm that the paper fails to acknowledge or mitigate. The standard disclaimer regarding the responsible use of security research tools is implicitly satisfied by the benchmark's nature as an evaluation harness rather than an offensive toolkit. No action items are required.

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The central claim of the paper—that current frontier models struggle significantly with long-horizon terminal tasks—is supported by a benchmark design that introduces dense rewards, but the evidentiary strength of the reported results is compromised by a lack of statistical robustness and potential confounds in the experimental setup. First, the primary results presented in Table 1 and Section 4.1 rely on single-run metrics. For instance, the headline figure that GPT-5.5 achieves a 15.2% pass ra

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Section 4.1 and Table 1 report aggregate metrics (e.g., '9.9M tokens', '231 episodes') to two decimal places or as exact integers without reporting variance (SD/SE) or the number of seeds/runs. Given the stochastic nature of LLM agents, these point estimates imply false precision. Report mean ± SD across the reported runs or explicitly state if these are single-run results.
- **[writing]** Section 4.2 claims GPT-5.5 is 'the strongest reported model' based on a single pass rate (15.2%) without reporting confidence intervals or variance across seeds. To support a ranking claim, report the standard deviation of pass rates across multiple seeds (e.g., 5 seeds) or provide a confidence interval for the pass rate estimate.
- **[writing]** Section 4.3 reports a Spearman correlation (ρ = 0.56) between pass rate and mean reward but omits the p-value or confidence interval for this correlation. With N=15 models, the statistical significance of this correlation is not guaranteed; report the p-value to validate the claim of a 'moderate' relationship.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The manuscript presents a clear and compelling narrative regarding the limitations of current benchmarks for long-horizon tasks. The introduction effectively sets up the problem, and the transition to the proposed benchmark is logical. However, the text contains several mechanical errors and structural inconsistencies that impede a smooth reading experience and, in some cases, prevent compilation. The most critical issue is the presence of two separate \abstract{} environments in the main file.
