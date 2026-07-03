# Automated-review action items — Role-Agent: Bootstrapping LLM Agents via Dual-Role Evolution

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The claim in Section 4.2 that Role-Agent outperforms prompt-based methods by '78.0% on ALFWorld' is mathematically inconsistent with Table 1. The average success rate for Role-Agent (90.9%) vs. the average of ReAct/Reflexion (~17.3%) represents a relative increase of ~424%, or an absolute increase of ~73.6 percentage points. The '78.0%' figure appears to be a calculation error or a mislabeled metric that requires correction to accurately reflect the data.
- **[writing]** The claim in Section 4.2 that Role-Agent outperforms GiGPO with 'relative gains of 4.2% / 6.9%' on ALFWorld/WebShop (Qwen-1.5B) is inconsistent with Table 1. The data shows ALFWorld gains of 4.2% (90.9 vs 86.7) but WebShop gains of 6.9% (71.9 vs 65.0) are actually 6.9 percentage points, which is a ~10.6% relative gain. The text conflates absolute percentage point differences with relative percentage gains, potentially overstating the improvement on WebShop.
- **[writing]** The claim in Section 4.2 that Role-Agent shows a '+13.6% increase on the Pick2 task' (Qwen-7B) is ambiguous and likely inaccurate. Table 1 shows Pick2 scores of 92.8% (Role-Agent) vs 79.2% (GiGPO). This is an absolute difference of 13.6 percentage points, but a relative increase of ~17.2%. The text should explicitly state '13.6 percentage points' to avoid confusion with relative improvement metrics.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 3: The caption contains the artifact 'black' at the beginning, which appears to be a formatting error or leftover LaTeX command.
- **[writing]** Figure 3: The y-axis label on the right plot ('Rollout Probs Diff Mean') is ambiguous; the caption describes it as 'averaged difference', but the label does not explicitly state the units or the specific metric being averaged.
- **[science]** Figure 4: The legend lists 12 failure modes, but the stacked bars only display 10 distinct colors; 'Exhaustive Exploration Failure' and 'Action Format Error' are missing from the visual data.
- **[writing]** Figure 4: The legend is cluttered with 12 items in a dense 3-column layout, making it difficult to map specific colors to failure modes.
- **[science]** Figure 6: The 'Total' bar (519.92) is not the sum of the preceding components (approx. 350s), and the 'Rollout' bar (175.36 + 18.63) does not align with the 'Total' bar's magnitude, making the breakdown mathematically inconsistent and misleading.
- **[writing]** Figure 6: The y-axis contains a break (indicated by the double slash) but lacks a clear visual gap or distinct scale change, making the transition between 30 and 200 visually confusing.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized acronyms and coined terms that are not defined at their first occurrence, creating a barrier for non-specialist readers. Specifically, the term "Agentic Reinforcement Learning (ARL)" appears in the Introduction without expansion. Similarly, the core components "World-In-Agent (WIA)" and "Agent-In-World (AIW)" are introduced as acronyms immediately, forcing the reader to memorize these labels before understanding the mechanisms they represent. In the M

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The claim of "co-evolution" contradicts the static offline library used in AIW (Sec 3.2). The environment re-weights existing tasks rather than generating new adaptive challenges, making "co-evolution" an overstatement of the mechanism.
- **[writing]** The WIA reward formula R_t = R_task * (1 + R_pre) is described as "modulation," but if R_task is 0, the term vanishes entirely. This is a hard gate, not a soft modulation of reliability for failed trajectories as claimed.
- **[science]** The claim that large H causes "reward hacking" via "speculative guesswork" is unsupported. Since R_pre relies on LMS against ground truth, hallucinations cannot increase the score unless they match reality, which is not hacking.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim of 'bootstrapped co-evolution' without human supervision (Introduction, Contribution 1) is overstated. The failure modes (Table in Appendix A) are pre-defined categories (e.g., 'wrong_target_location'), and the retrieval logic relies on these fixed labels rather than emergent, unsupervised discovery. The paper should clarify that the 'evolution' is guided by a fixed taxonomy, not purely bootstrapped.
- **[writing]** The statement that Role-Agent achieves 'substantial improvements' and 'generalization capabilities' (Introduction, Conclusion) is not fully supported by the search-QA results (Table 2). Role-Agent underperforms GiGPO on the NQ dataset (40.1% vs 42.0%). The authors attribute this to 'stronger generalization' rather than overfitting, but this contradicts the standard interpretation of lower in-domain performance. This specific claim needs retraction or stronger evidence.
- **[writing]** The efficiency claim of 'only about 5.2% extra computation' (Efficiency Study) conflicts with the 'Computational Overhead' appendix which reports a ~27% total overhead (109 tokens/sec vs 150 tokens/sec). The 5.2% figure likely refers only to the AIW feedback loop, excluding the predictive rollout cost. The text should be precise to avoid misleading readers about the total inference cost.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'The Use of Large Language Models' section (Appendix) states LLMs were used for grammar and coding assistance but does not explicitly confirm that the LLMs were not used to generate the failure mode analyses, trajectory data, or the core experimental results. Given the method's reliance on LLM-generated feedback, a clearer distinction between human-designed prompts and LLM-generated content is required to ensure reproducibility and transparency.
- **[writing]** The paper describes a self-reinforcing loop where the LLM analyzes its own failures to curate future training data (AIW). There is no discussion of safeguards against 'reward hacking' or the amplification of specific biases (e.g., the model learning to exploit the failure-mode analysis prompt rather than solving the task). A brief discussion on potential failure modes of the co-evolution loop itself is needed.
- **[writing]** The WebShop benchmark involves simulating interactions with a large-scale e-commerce environment (1.18M products). The paper does not address data privacy or the potential for the agent to inadvertently generate or expose sensitive user data (e.g., credit card numbers, addresses) during the 'click' or 'search' actions, even in a simulated setting. A statement on data safety protocols is recommended.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The ablation study in Table 3 lacks standard deviations for the -w/o AIW and -w/o Predictive Reward variants. Re-run these ablations with multiple seeds to confirm the reported gains are statistically significant and not due to random variance.
- **[science]** The predictive reward relies on LMS string matching, which may penalize semantically correct but textually different states. Provide evidence that LMS is robust to semantic equivalence in these benchmarks or analyze the false-negative rate of the state prediction metric.
- **[science]** The AIW retrieval mechanism lacks quantitative validation. Report precision/recall metrics for the retrieved tasks or provide a human evaluation of the failure mode analysis to prove the data distribution shift is actually targeting the identified deficiencies.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** The statistical analysis in the paper is generally sound in its application of standard RL metrics (success rate, score) and ablation studies. However, several areas require stronger statistical rigor to fully support the claims of superiority and stability. First, the reporting of variance is inconsistent. While Table 3 in Appendix B correctly reports mean ± standard deviation over three runs for the proposed method and key baselines, the main results in Table 1 and Table 2 only present point e

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the Introduction, fix the semicolon splice: '...rewards; The environment fails...' should use a period or lowercase 'the' to correct the grammar.
- **[writing]** In Section 3.1, change 'as the following' to 'as follows' and fix inconsistent spacing around math symbols (e.g., '1± ε') to improve readability.
- **[writing]** In Section 3.2, rephrase the dangling modifier 'Instead of employing..., following GiGPO...' to clearly attribute the action to the authors.
- **[writing]** In Section 4.2, clarify if the '78.0%' improvement is an absolute percentage point gain or a relative increase to prevent misinterpretation.
