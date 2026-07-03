# Automated-review action items — OPID: On-Policy Skill Distillation for Agentic Reinforcement Learning

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** The bibliography uses 'iclr2025_conference' style, implying a 2025 submission, yet cites multiple baselines (e.g., OPSD, Skill-SD, RLSD, SDAR) with 2026 publication years (e.g., zhao2026opsd, wang2026skillsd). These future-dated references cannot be verified as existing baselines for a 2025 paper, invalidating the comparative claims. Verify the actual publication years or replace with existing baselines.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption claims OPID is 'competitive' on Search-based QA, but the chart shows OPID (49.2) is significantly outperformed by multiple baselines (e.g., Skill-GRPO* at 47.5, Skill-SD at 47.8, RLSD at 49.0, SDAR at 49.0) and is not the strongest; the claim contradicts the visual data.
- **[writing]** Figure 1: The y-axis labels (method names) are not explicitly defined in the caption or legend, forcing the reader to infer which bars correspond to which method groups without a clear key.
- **[science]** Figure 4: The caption claims OPID 'approaches full-data GRPO performance using about 60% of the data,' but the chart shows OPID at 60% data (~73%) is still significantly higher than GRPO at 100% data (~76%), and the red arrow annotation points to the gap between OPID at 60% and GRPO at 100% rather than showing convergence. The visual evidence does not support the specific claim of 'approaching' performance at that data fraction.
- **[writing]** Figure 4: The annotation '≈ 40% Data' with a downward arrow is ambiguous; it is unclear if this refers to the data reduction (100% - 60% = 40%) or a specific metric value, and the arrow placement between the curves does not clearly link to the x-axis value of 60%.
- **[science]** Figure 6: The y-axis label 'Avg critical steps' contradicts the caption's claim that the curve reports 'how many timesteps are selected... in each trajectory' (a count per sequence). The y-axis values (~3.0–4.0) are too low to represent a raw count of steps per trajectory if the x-axis is 'Training step' (1–150), suggesting the metric is an average over multiple trajectories per step, but this aggregation is not explained in the caption or axis label.
- **[writing]** Figure 6: The annotation 'avg 3.692' is placed near the end of the plot without clarifying whether it represents the global mean across all training steps or a local average; the caption does not define this value.
- **[science]** Figure 7: The x-axis is labeled 'Training step' with a range of 1–150, but the caption describes 'magnitudes... during OPID training' without specifying the unit of the step (e.g., iterations, epochs, or gradient updates). This ambiguity makes it impossible to assess the training duration or convergence rate.
- **[writing]** Figure 7: The y-axis label for the bottom panel, 'Skill abs advantage(1e-4)', uses scientific notation that implies the plotted values are scaled by 10,000. However, the axis ticks (1.5–4.0) and the caption's description of 'magnitudes' suggest these are raw values. If the values are indeed scaled, the caption should explicitly state this to avoid misinterpretation of the signal's strength relative to the episode advantage.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 3.1 (Problem Formulation): The symbol `ind` is used in the definition of routing masks ($q^{\mathrm{step}}_{	au,t}=\ind[t\in\mathcal{C}_	au]$) without definition. Define it as the indicator function (1 if true, 0 otherwise) at first use.
- **[writing]** Section 3.3 (Critical-First Skill-Conditioned Self-Distillation): The variable `m` in the advantage equation ($A^{\mathrm{skill}} = \dots m_{	au,t,ll}$) is undefined. Specify that $m_{	au,t,ll}$ is a token mask (e.g., excluding padding or non-generation tokens).
- **[writing]** Section 3.4 (Policy Optimization): The term `episode-relative advantage` is used for $A^{\mathrm{ep}}_{	au}$, but the equation shows it is computed per trajectory within a group. Clarify if this is a 'group-relative advantage' or define the 'episode' scope explicitly to avoid confusion with standard episode-level returns.
- **[writing]** Section 3.2 & 3.3: The term 'analyzer' ($\mathcal{A}$) is introduced as an LLM-based component. While the function is clear, explicitly state in the first mention that $\mathcal{A}$ is a separate, frozen LLM instance used for offline trajectory analysis to distinguish it from the policy $\pi_	heta$.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 4.2 (Main Results) claims OPID improves over GRPO by '+26.5 (WebShop)' on Qwen3-1.7B. However, Table 1 shows OPID (85.0) vs GRPO (67.3), a difference of +17.7. The text's number (+26.5) does not follow from the table's data. Verify the calculation or correct the text to match the table.
- **[writing]** Section 4.2 states 'OPID improves over GRPO in most combinations' and cites specific gains. However, Table 1 shows that on Qwen3-1.7B for the 'Pick' task in ALFWorld, OPID (65.9) is lower than GRPO (71.1). The text's generalization 'improves... in most combinations' is technically true but the specific claim of consistent improvement in the paragraph context ignores this clear counter-example in the same table, creating a slight logical tension between the summary and the data presentation.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract claims 'generalizes' broadly, but evidence is only ALFWorld 'unseen' split (Sec 3.4). Scope claim to 'unseen splits within same environment' or add cross-domain tests.
- **[writing]** Conclusion states 'consistent improvements' but Table 1 shows OPID loses on specific tasks (e.g., ALFWorld Clean on 3B, NQ on 1.7B). Qualify 'consistent' to 'generally' and acknowledge variance.
- **[writing]** Qualitative analysis (Fig 3) presents one success case as evidence for 'reduced invalid behaviors' without statistical backing. Clarify this is illustrative, not a quantitative proof of reduced hallucination.

## paper_reviewer_safety_ethics — verdict: accept

The paper presents a reinforcement learning method (OPID) for agentic LLMs using on-policy skill distillation. From a safety and ethics perspective, the work is low-risk. The research utilizes standard, public benchmarks (ALFWorld, WebShop, Search-based QA) and does not involve human subjects, personal data, or sensitive information. The methodology focuses on improving agent efficiency and sample complexity in simulated environments, with no dual-use capabilities identified that would meaningfully lower the barrier to harmful activities (e.g., automated cyberattacks, disinformation generation, or biological synthesis).

The paper does not release any new datasets containing PII or scraped content that would violate terms of service; the training data consists of interactions within the specified benchmark environments. The "analyzer" component described in the method uses an LLM to extract skills from trajectories, but this is an internal training mechanism, not a system designed for deception, surveillance, or manipulation of human users. There are no undisclosed conflicts of interest or operational vulnerabilities disclosed that require responsible disclosure.

As this is a third-party preprint, the absence of a formal "Broader Impacts" statement is noted but does not constitute a safety failure given the benign nature of the research (algorithmic improvement on standard benchmarks). The paper does not require specific safety mitigations or disclosures beyond what is standard for this subfield.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a compelling method (OPID) for enhancing agentic RL via on-policy skill distillation. However, the evidentiary strength of the central claims is currently undermined by a lack of statistical rigor in the experimental design. The primary concern is the absence of variance reporting. Table 1 presents headline performance numbers (e.g., 84.3% vs 75.0% on ALFWorld) derived from what appears to be single training runs. In reinforcement learning, performance is highly sensitive to r

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Table 1 and Section 4.2 report single-point accuracy/success rates without variance (SD/SE/CI) or seed counts. RL results are stochastic; reporting single runs implies false precision. Report mean ± SD over ≥3 seeds for all main results to assess stability.
- **[writing]** Section 4.2 claims OPID 'improves' or is 'better' based on point estimates alone, with no hypothesis test (t-test, Wilcoxon, bootstrap) or p-values reported. Without statistical validation, these are descriptive, not inferential. Run tests on seed data or rephrase to 'observed improvement'.
- **[writing]** Ablation Tables 3 and 4 compare OPID to variants using single-point averages. With multiple comparisons, false positives are possible. Report variance across seeds or acknowledge multiplicity to ensure observed drops (e.g., -10.2 points) are robust and not noise.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-structured, with a logical flow from problem formulation to method, results, and analysis. The abstract effectively sets the stage, though it could be more specific about the quantitative gains. The introduction clearly delineates the gap in current methods and the proposed solution. However, several sections suffer from minor clarity issues that require a second read. In Section 3.1, the transition from the standard RL objective to the group-relative advantage used i
