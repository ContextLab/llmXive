# Automated-review action items — APPO: Agentic Procedural Policy Optimization

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** Theorem 1 (Variance Reduction) claims a strict inequality Var(g_APPO) <= Var(g_base) - Delta, but the proof in Appendix A.1 only establishes non-strict inequality (<=) and relies on an assumption that sigma_i are not all equal without explicitly stating this condition in the theorem statement. The theorem should clarify the condition for strict reduction or remove the Delta term if equality is possible.
- **[writing]** Table 1 reports APPO outperforming ARPO by '+7.9%' on Llama3.1-8B, but the raw numbers (57.4 vs 55.3) represent an absolute difference of 2.1 points, not a 7.9% relative improvement. The percentage calculation appears inconsistent with the reported absolute scores, potentially misleading readers about the magnitude of gains.
- **[writing]** The paper claims APPO was evaluated on '13 benchmarks' in the abstract and conclusion, but Table 1 lists 10 datasets and Table 2 lists 4 datasets (with WebWalker appearing in both). The total count of unique benchmarks is ambiguous, and the claim of '13' is not explicitly reconciled with the presented tables.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1(c): The legend lists 'Ours' (purple dashed line), but the caption describes the plot as 'pass@$k$' (implying a variable k). However, the y-axis is labeled 'Avg. Pass@1 of Branches' and the x-axis shows dataset sizes (1, 2, 4...), not k values. This contradicts the caption's claim of showing pass@$k$.
- **[science]** Figure 1(c): The radar chart legend includes 'GRPO', 'GIGPO', 'ARPO', and 'Ours (APPO)', but the caption text only mentions 'performance comparison between APPO and others' without specifying these baselines, creating a disconnect between the visual legend and the textual description.
- **[writing]** Figure 1(b.1): The text annotation 'Entropy does not always work ..' is informal and unprofessional for a scientific figure; it should be rephrased to a formal statement or removed.
- **[science]** Figure 2: The 'Dual-Group Advantage Calculation' panel depicts a 'Future' term (purple box) being added to the advantage calculation, but the diagram does not visually link this term to the 'Branching Score' or 'Entropy' components shown in the 'Rollout Branching' panel, making the 'future-aware' mechanism described in the caption opaque.
- **[writing]** Figure 2: The legend at the bottom is incomplete; it defines symbols for 'Query', 'Reasoning Tokens', 'Procedures', 'Tool-calls (Python)', and 'Tool-calls (WebSearch)', but does not define the symbols for 'Entropy', 'Branching Score', or the 'Future' term used in the main diagram.
- **[science]** Figure 3: The legend is cropped and illegible; the text labels for the purple and teal patterns are cut off, making it impossible to verify which color corresponds to ARPO and which to APPO.
- **[writing]** Figure 3: The y-axis of subplot (c) 'WebWalkerQA' has a truncated scale (40-70) that is inconsistent with the other subplots (40-65 or 10-25), which may mislead the reader regarding the relative magnitude of performance differences.
- **[science]** Figure 4: The caption describes 'training dynamics' but does not define the y-axes. The left plots show values 0.0–0.6 (likely entropy or probability) and the right plots show 150–400 (likely token count or cost), yet neither metric is labeled on the axes, making the 'dynamics' uninterpretable.
- **[writing]** Figure 4: The legend is split across the top of the subplots (two separate legends for two model families) rather than being unified or clearly associated with the specific subplots, which creates visual clutter and potential confusion.
- **[science]** Figure 5: The caption claims to show 'alternative designs of the BS metric,' but the sub-captions (a)-(d) do not define which specific metric design corresponds to each panel, making the comparison impossible to interpret.
- **[writing]** Figure 5: Sub-captions (a), (b), and (c) contain mathematical notation ('Weight=(0.5, 0.5)', etc.) that is undefined; the caption fails to explain what these weights represent or which components of the BS metric they modify.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define all acronyms (BS, KL, pass@k, LLM) at their first use.
- **[writing]** Replace or explain jargon like "rollouts," "token entropy," "advantage," "latent," and "spurious" with plainer alternatives or brief explanations.
- **[writing]** Ensure that mathematical terms like "z-score" are explained if they are not common knowledge to the target audience.
- **[writing]** Break down complex phrases like "procedure-level advantage scaling" into simpler components. These changes will make the paper more inclusive and understandable to a wider range of researchers, including those from adjacent fields or with less specialized backgrounds in RL.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Theorem 1 assumes Var(R|D_i) is monotone in BS_i to prove variance reduction, but the paper provides no empirical or theoretical justification for this monotonicity assumption. The proof relies entirely on this unverified premise.
- **[science]** Theorem 2's policy improvement bound uses a state distribution q induced by BS-guided branching, but the proof does not rigorously bound the occupancy mismatch between q and the true policy distribution rho^pi_new, making the constant C undefined.
- **[science]** The dual-group advantage estimation (Eq. 6) claims to avoid bias from mixing policies, but the formula averages advantages from two groups without explaining how this prevents gradient contamination when branches are generated by pi_theta while initial rollouts use pi_old.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that APPO improves performance by 'nearly 4 points' (Abstract) and 'approximately 3 points' (Contributions) is inconsistent with Table 1, which shows a 2.1 point gain on Qwen2.5-7B and a 2.45 point gain on Llama3.1-8B. The 'nearly 4 points' figure appears to conflate the 7.9% relative improvement on Llama3.1-8B with absolute points, or refers to a specific subset not clearly defined. This overstates the generalizable absolute gain.
- **[science]** Theorem 1 claims variance reduction based on the assumption that conditional reward variance is monotone in the Branching Score (BS). The paper provides no empirical evidence or theoretical justification for this monotonicity assumption in the context of LLM reasoning. Without validating this assumption, the theorem's applicability to the proposed method is speculative and overreaches the provided data.
- **[writing]** The abstract states APPO 'consistently improves strong agentic RL baselines by nearly 4 points,' yet Table 2 shows APPO improving over ARPO by only 3.0 points on GAIA (42.7 vs 39.7 implied, though ARPO is 38.8) and 1.4 points on HLE. The 'nearly 4 points' claim is an overgeneralization that does not hold across all reported benchmarks, particularly the DeepSearch tasks where gains are smaller.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper lacks a dedicated 'Broader Impacts' or 'Ethical Considerations' section. Given the focus on autonomous agents with tool-use (search, code execution), a formal discussion of potential misuse (e.g., automated disinformation, unauthorized data scraping) and mitigation strategies is required before acceptance.
- **[writing]** The 'Impact Statement' in Appendix J is generic and does not address specific dual-use risks associated with the proposed 'Branching Score' mechanism, which could theoretically be used to optimize agents for adversarial goal-seeking. A more concrete risk analysis is needed.
- **[writing]** The experiments utilize a 'Bing search engine' and 'sandbox environment' for tool execution. The manuscript must explicitly state whether the search queries and code execution were monitored for safety violations (e.g., generating harmful code, accessing restricted data) and if any safety filters were applied during the RL training loop.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Theorem 1 assumes Var(R|D_i) is monotone in BS_i to prove variance reduction. This is a critical unverified assumption. Provide empirical evidence (e.g., a scatter plot of BS vs. reward variance across datasets) or a sensitivity analysis showing robustness if this monotonicity does not strictly hold.
- **[science]** Table 1 and Table 2 report performance gains (e.g., +7.9% on Llama3.1) without standard deviations or statistical significance tests (e.g., t-tests, confidence intervals). Given the small sample sizes of some benchmarks (e.g., AIME24 has 30 problems), these gains may not be statistically significant. Report variance across multiple seeds or statistical tests.
- **[science]** The ablation study in Table 4 (tab:comp) shows component contributions but lacks error bars or significance testing. With only average scores reported, it is unclear if the observed drops (e.g., 0.9 points for BS->Ent) are robust or within noise. Include variance estimates or multiple runs.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Theorem 1 assumes Var(R|D_i) is monotone in BS_i to prove variance reduction. This is a critical unverified assumption. The authors must provide empirical evidence (e.g., a scatter plot of BS vs. reward variance across decision points) or a theoretical justification for this monotonicity, as it is the linchpin of the variance reduction claim.
- **[science]** Theorem 2 relies on the bound 1-ε' ≤ A^fut(s) ≤ 1+ε'. However, Eq. 7 defines A^fut via a clipped exponential of a sum of log-ratios. The clipping is applied to the final value, but the unclipped sum could theoretically violate the bound if the discount factor γ or the number of steps is large. The authors should explicitly demonstrate that the clipping parameters (ε') are sufficient to guarantee the bound holds for all visited states in their experiments.
- **[science]** Table 1 and Table 2 report mean accuracy scores but omit standard deviations or confidence intervals. Given the stochastic nature of RL training and the small sample sizes of some benchmarks (e.g., AIME24 has only 30 problems), the statistical significance of the reported improvements (e.g., +2.45 points) cannot be assessed. Please report standard deviations over multiple seeds or perform significance tests (e.g., paired t-tests) to validate the gains.
- **[science]** The ablation study in Table 4 compares APPO against variants (e.g., BS→Ent, w/o A^fut) but does not report p-values or confidence intervals for the differences. With multiple comparisons across datasets and backbones, the risk of Type I error increases. Please include statistical significance testing for the ablation results to confirm that the observed drops are not due to random variance.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the Introduction (lines 105-108), the sentence 'We use procedures to denote...' is grammatically awkward. Consider rephrasing to 'We define procedures as...' for better clarity and flow.
- **[writing]** Section 3.1 (lines 230-232) contains a run-on sentence regarding the discount factor gamma. Split into two sentences or use a semicolon to improve readability: '...reduce variance. We then combine...'
- **[writing]** The abstract (line 12) uses 'nearly 4 points' while the contributions (line 135) state 'approximately 3 points'. This inconsistency in reported performance gains should be harmonized to avoid reader confusion.
- **[writing]** In Section 3.2 (line 285), the phrase 'sparse and critical' is used without clear definition or context. Ensure this terminology is either defined earlier or rephrased for immediate clarity.
