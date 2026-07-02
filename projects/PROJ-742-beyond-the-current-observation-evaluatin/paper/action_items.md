# Automated-review action items — Beyond the Current Observation: Evaluating Multimodal Large Language Models in Controllable Non-Markov Games

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 1 (Introduction) claims 'Gemini-3.1-Pro wins all 16 head-to-head duels,' but Table 2 (tab:match_dual_image_poker_rank) lists GPT-5.4 and Qwen3.5-397B with 7 and 7 wins respectively in a 16-game set, which is mathematically impossible if Gemini won all 16. The text contradicts the table data.
- **[writing]** Section 1 states 'GPT-5.4 matches 69.5% of pairs on 8x10,' but Table 1 (tab:main_results) only reports results for the 10x10 configuration (62.3%). The 8x10 data point is cited in the text but not present in the provided tables, making the claim unverifiable from the current evidence.
- **[writing]** Section 5 (Training) claims fine-tuning 'transfers to existing benchmarks without regression,' citing EMemBench and VGRPBench. However, the paper provides no tables or specific numerical results for these external benchmarks to substantiate the 'no regression' claim, only a qualitative summary.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains a grammatical error and missing subject in the first sentence: 'while is non-Markov' should read 'while [games] are non-Markov'.
- **[writing]** Figure 1: The 'Non-Markov' section contains a typo 'Filp Back' instead of 'Flip Back'.
- **[writing]** Figure 3: x-axis labels are illegible and appear as a dense, overlapping block of text (e.g., '4x4, 6x6...') rather than distinct tick labels, making the specific board/maze sizes unreadable.
- **[science]** Figure 3: The right panel plots 'Game Score' and 'Explore %' on the same axes but lacks a legend to distinguish the two data series (solid vs. dashed lines).
- **[fatal]** Figure 4: The rendered image displays a qualitative case study of 3D Maze trajectories (Seed-2.0 vs. Kimi-K2.5) with minimaps, but the caption describes a quantitative 'Success rate with minimap across maze sizes' plot; the visual content does not match the caption.
- **[science]** Figure 4: The caption references 'Tab. .' with a missing table number, making the cross-reference unusable.
- **[writing]** Figure 5: The caption states the Kimi-K2.5 model 'exhausts the 96-step budget,' but the right panel's title reads 'Steps: 96 / 96 (failed, Eff: 0.00)' and the trajectory visualization shows a path ending at step 73, creating ambiguity about whether the agent stopped early or the visualization is truncated.
- **[writing]** Figure 5: The text boxes for the Kimi-K2.5 model (right) contain a contradiction; Step 25 states the agent is at '(6,4)' and needs to get to '(6,6)', yet the trajectory map shows the agent moving away from the goal area (bottom-right) into a dead-end loop.
- **[writing]** Figure 6: The caption states the model navigates a '$77$ maze', but the visual grid is clearly 7x7; the caption should read '$7 \times 7$' to match the image.
- **[writing]** Figure 6: The text inside the small 'Step' snapshot images (e.g., 'Step 1', 'Step 16') is illegible due to low resolution.
- **[writing]** Figure 7: The caption contains a typo '$1010$ noise board' which should be '$10 \times 10$' to match the figure title and visual grid.
- **[writing]** Figure 7: The legend text 'GPT-5.4 (31/50)' and 'Gemini-3.1-Pro (16/50)' is ambiguous; it is unclear if these numbers represent the final score, a ratio, or a specific metric without further definition.
- **[science]** Figure 8: The caption states the board is 8x10 (80 pairs), but the 'GPT-5.4 Goes First' panel shows a cumulative total of 18 pairs, which is mathematically impossible for a single-player game on an 80-pair board (max 80) or a duel (max 40). The data appears inconsistent with the stated board size.
- **[writing]** Figure 8: The y-axis label 'Cumulative Matched Pairs' is present, but the axis ticks (0.0, 2.5, 5.0...) and the step-function nature of the data suggest discrete integer events; the decimal formatting is slightly misleading though not fatal.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific terminology that creates unnecessary barriers for non-specialist readers, particularly those in general AI or cognitive science. In Section 3.1 (Problem Formulation), the authors introduce POMDPs (Partially Observable Markov Decision Processes) without defining the acronym. While standard in reinforcement learning, this is a critical concept for the paper's premise and should be spelled out and briefly explained for a general audience. Similarly,

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a compelling benchmark for non-Markov games, but several logical inconsistencies in the presentation of metrics and results undermine the clarity of the conclusions. First, the Game Score (GS) formula in Equation 1 is mathematically inconsistent with the values reported in Table 1. The formula $GS = \frac{SR + SR \times Eff + (1-SR) \times Explore}{2}$ produces a value between 0 and 1. For Gemini-3.1-Pro in the 3D Maze ($13 \times 13$), the table reports $SR=50.0\%$, $Eff=62.5

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The abstract claims fine-tuning transfers to benchmarks 'without regression,' but Section 5 only reports gains on EMemBench/VGRPBench. No data is shown for general multimodal tasks to verify the 'no regression' claim, making this an over-claim of scope.
- **[science]** The abstract states errors are 'mostly forgetting' based on Memory Gap. However, the metric only measures the gap to an oracle, conflating forgetting with reasoning failure. The paper lacks ablation to isolate retention from planning, so this causal attribution is unsupported.
- **[writing]** The introduction claims Gemini-3.1-Pro 'wins all 16 head-to-head duels,' but Table 2 aggregates results against multiple opponents. The phrasing implies a specific sweep that may mislead readers about the exact matchup distribution; precise qualification is needed.

## paper_reviewer_safety_ethics — verdict: accept

The manuscript presents a benchmark for evaluating Multimodal Large Language Models (MLLMs) in controllable non-Markov games, specifically focusing on memory and belief-state reconstruction. From a safety and ethics perspective, the work is sound and poses no immediate risks.

The authors explicitly address ethical considerations in the "Ethics Statement" (Section 7) and "Potential Risks" (Section 8). They correctly identify that the visual observations are synthetically generated, eliminating concerns regarding human-subject data, privacy violations, or the need for IRB/IACUC approval. The environments (Matching Pairs and 3D Maze) are abstract and do not simulate real-world harmful scenarios, reducing the risk of dual-use for malicious training or social engineering.

The "Potential Risks" section appropriately frames the benchmark as a diagnostic tool for research evaluation rather than a metric for deployment in safety-critical applications, mitigating the risk of over-interpretation. The fine-tuning experiments utilize optimal rollouts from a simulator, which are synthetic and do not introduce biased or harmful human data.

No conflicts of interest are apparent in the provided text. The data and code availability are handled via external links, which is standard practice and does not raise privacy concerns. The paper does not contain any content that could be interpreted as promoting harm, hate speech, or dangerous activities. The scope of the research is strictly limited to evaluating model capabilities in a controlled, synthetic environment.

Therefore, the paper meets the safety and ethics criteria for acceptance.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The 'Duel Protocol' results (Tab. 2) claim Gemini-3.1-Pro won all 16 matchups against GPT-5.4 and Qwen3.5-397B. However, the table lists GPT-5.4 with 7 wins and 7 losses (50% win rate) and Qwen3.5-397B with 7 wins and 8 losses. This is a direct contradiction between the narrative text and the data table that must be resolved to validate the claim of total dominance.
- **[science]** The Memory Gap metric (Eq. 2) relies on an oracle score $S^*(m)$. The paper states the oracle injects 'true hidden state,' but does not specify if the oracle is a perfect solver (100% success) or a model with perfect memory but limited reasoning. If the oracle is not perfect, the denominator $S^*(m)$ is ambiguous, making the 'gap' a measure of both memory and reasoning deficits rather than pure forgetting.
- **[science]** The fine-tuning study (Sec. 5, Tab. 4) reports a single run for Qwen3.5-9B with 'rmix32k' data. No standard deviation or confidence intervals are provided for the 29.5% score or the 10.0% success rate. Given the stochastic nature of RLHF/SFT and the small sample size of the evaluation (implied by the integer success counts in other tables), the statistical significance of the transfer claim is unverified.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The 'Duel Protocol' results (Table 2) report 16 total matchups with a 100% win rate for Gemini-3.1-Pro. However, the text states 'GPT-5.4 and Qwen3.5-397B tie at ~47-50% win rate' in the same section, which is mathematically inconsistent with a 16-game sample where one model won all games. Clarify the sample size and aggregation method for the duel statistics.
- **[science]** The 'Memory Gap' metric (Eq. 2) is defined as a percentage difference from an oracle score. The paper reports specific MemGap values (e.g., 51.3%, 40.8%) but does not provide confidence intervals or standard errors for these derived metrics, despite the high variance observed in the raw success rates (e.g., 1/5 vs 4/5 in Table 5). Statistical significance of these gaps is not established.
- **[science]** In the fine-tuning section (Table 4), the improvement of Qwen3.5-9B from 0.0% to 29.5% on Matching Pairs is reported. The text mentions evaluation over '5 environment seeds' in the appendix, but the main table presents single-point estimates without error bars or standard deviations. Given the stochastic nature of the game and the small sample size implied by the 1/5 success rates elsewhere, the statistical robustness of the 29.5% figure is unclear.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 5 (Experiments), the text states 'GPT-5.4 and Qwen3.5-397B tie at ~47-50% win rate' in the Duel setting. However, Table 2 shows GPT-5.4 at 50.0% and Qwen3.5-397B at 46.7%. The text should clarify that these are distinct values or adjust the phrasing to avoid implying a statistical tie where the data shows a difference.
- **[writing]** In Section 5.2 (Diagnostic Analysis), the sentence 'Text-only solves Matching Pairs (100%) and 3D Maze (GS ~70%)' is ambiguous. It is unclear if 'solves' implies perfect performance or merely high performance. Given the context of '100%', it likely means perfect, but 'GS ~70%' is not a 'solution' in the same sense. Rephrase for precision, e.g., 'Text-only inputs achieve 100% on Matching Pairs and ~70% GS on 3D Maze.'
- **[writing]** In the Appendix (More Analysis), the phrase 'Tabs.~\ref{tab:rq1_board_size_match} and~\ref{tab:rq1_board_size_maze} report the per-size numbers' uses 'Tabs.' as an abbreviation for 'Tables'. While common in some contexts, standard academic prose usually spells out 'Tables' or uses 'Table' if referring to a single one. Ensure consistency with the main text style, which spells out 'Table' in captions and text.
