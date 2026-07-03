# Automated-review action items — ProRL: Effective Reinforcement Learning for Proactive Recommendation via Rectified Policy Gradient Estimation

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Theorem 1 (Section 2.2) claims a convergence rate of O(1/s) for stopping probability. The proof sketch in Appendix A.1 derives p(s) <= K/s, but the text does not explicitly define the variable 's' (e.g., training step, iteration count) or the constant 'K'. This ambiguity prevents verification of the claim's accuracy.
- **[science]** Table 1 (Section 4.2) reports a Coherence score of 0.8422 for ProRL on MovieLens-1M, while Table 2 (Appendix) reports 0.8422 for the same metric on Steam. The text claims 'Pareto dominance' with Coherence > 0.95 on MovieLens-1M (Section 5.1), which contradicts the 0.8422 value in the main results table. Verify the correct value and consistency across tables.
- **[writing]** The claim that 'standard policy gradients degenerate into nearly identical overlong paths' (Section 1) relies on Figure 2. However, the text states 'All components exhibit positive mean' for step rewards, but the specific mean values (e.g., 0.08, 0.45) listed in the critical elements are not explicitly mapped to the specific reward components (CTR, IoI, IoR) in the figure caption or text, making the causal link hard to verify.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 3: The 'IoR' row (second from top) uses a mixed scale where the y-axis includes negative values (e.g., -10^1) alongside a logarithmic scale (10^0, 10^1), which is mathematically invalid for log plots and makes the visualization of negative bars impossible or misleading.
- **[writing]** Figure 3: The x-axis labels ('20%', '40%', '60%', 'Random') are only visible on the bottom row; the top three rows lack these labels, forcing the reader to guess the grouping for the upper metrics.
- **[science]** Figure 4: The caption claims 'ProRL (blue stars)' but the legend and plot show blue squares; the symbol definition is inconsistent.
- **[science]** Figure 4: The orange lines (fixed reward offsets) lack a legend mapping specific colors to specific offset values, making the 'sensitivity analysis' uninterpretable.
- **[writing]** Figure 4: The y-axis label 'Path Length' is ambiguous as it does not specify the unit (e.g., number of items).
- **[writing]** Figure 5: The caption is insufficient as it fails to define the metrics (IoI, IoR) plotted on the y-axes or the specific line styles and markers used for each method, which are only defined in the shared legend at the bottom.
- **[writing]** Figure 5: The subplots are not labeled with letters (A, B, C, D) as referenced in the caption, making it difficult to explicitly map the text description to the specific visual panels.
- **[writing]** Figure 6: The legend at the top defines four methods (RF, RTG, GRPO, ProRL), but the 'Steam' column plots (middle row) display a fifth distinct grey line that is not defined in the legend or caption.
- **[writing]** Figure 6: The 'Amazon-Book' column (right) plots only two lines (blue and green), yet the legend and caption imply four methods should be compared; the missing baselines (RF, GRPO) are not explained.
- **[writing]** Figure 8: The caption contains a malformed mathematical expression for the expected reward accumulation: '$(_t=1^L E[r_t] L)$' is missing the summation symbol and likely intended to be '$\sum_{t=1}^L E[r_t] \propto L$'.
- **[writing]** Figure 8: The caption defines the Stepwise Reward Centering formula as '$r_t = r_t - r$' (using the same symbol for the centered and uncentered reward), whereas the figure itself correctly uses distinct notation '$\tilde{r}_t = r_t - \bar{r}$'.
- **[science]** Figure 9: The top row plots show 'Diversity' on the right y-axis (0.0–1.0), but the green dashed line (Amazon-Book) drops to 0.0 and stays flat, while the red dashed line (MovieLens-1M) remains high. The caption claims 'degenerates into generating nearly identical overlong paths' for standard policy gradient, yet the red dashed line (diversity) does not collapse to zero for MovieLens-1M under CTR/IoI/IoR rewards — contradicting the claim that all methods degenerate. This misrepresents the failur
- **[writing]** Figure 9: Bottom row y-axis label 'E[r_t]' is present, but no units or scale context (e.g., normalized? raw reward?) is given in caption or axis; values range from -0.1 to 100 across subplots without explanation, making cross-comparison ambiguous.
- **[science]** Figure 9: Top row, rightmost subplot (Reward = IoR) shows green dashed line (Amazon-Book diversity) dipping below 0.0 at step 1000 — impossible if diversity is bounded [0,1]. Likely plotting error or mislabeled axis; undermines validity of diversity metric.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific acronyms and coined terms that are not consistently defined at their first point of use, creating barriers for readers outside the immediate niche of reinforcement learning for recommendation systems. In the Abstract and Introduction, the metrics IoI and IoR are introduced as acronyms without their full names (Increment of Interest, Increment of Rank). A general reader cannot understand the contribution without flipping to Section 2 (Preliminaries

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Theoretical Derivation (Theorem 1): Theorem 1 in Section 2.2 asserts that the stopping probability $p(s)$ converges to 0 at a rate of $O(1/s)$ under positive mean rewards. The proof sketch in Appendix A.1 states that $\frac{dJ}{dp} < 0$ and integrates $\frac{dp}{ds} \leq -c p^2$ to yield $p(s) \leq K/s$. The logical gap lies in the derivation of the differential inequality $\frac{dp}{ds} \leq -c p^2$ from the gradient flow of the policy parameters. The paper does not explicitly show how the grad
- **[writing]** Bias in Advantage Estimation: In Section 3.2, the Position-Specific Advantage Estimation (Eq. 5) calculates a baseline $\bar{G}_{i,t}$ conditioned on the subset of trajectories that actually reach step $t$ ($L^{(i,j)} \geq t$). While this reduces variance by using relevant data, the paper does not logically address the potential bias introduced by this conditioning. Trajectories that reach step $t$ are inherently a non-random subset (likely those with higher cumulative rewards or better feasibil
- **[writing]** Causal Interpretation of Ablation: The ablation study (Table 3) demonstrates that removing Stepwise Reward Centering (w/o SRC) results in high CTR but significantly lower IoI and IoR. The authors conclude this confirms SRC prevents the "length shortcut." However, the logical link is slightly tenuous without explicit data on path lengths in the "w/o SRC" condition. The high CTR suggests the model is generating feasible paths, but it does not explicitly prove these paths are *longer* than the opti

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that ProRL achieves 'Pareto dominance' (Section: Supplementary Experiments) is an overstatement. Table 1 shows ProRL has lower CTR (0.8543) than the 'w/o SRC' ablation (0.9731) on MovieLens-1M. The authors must qualify this claim to reflect that ProRL optimizes a specific trade-off, not all metrics simultaneously.
- **[science]** Theorem 1 (Length Collapse Rate) in Section 2.2 and Appendix A claims a convergence rate of O(1/s) for stopping probability. The proof sketch provided is insufficient to justify this specific asymptotic rate without further assumptions on the reward distribution or policy parameterization. The claim should be softened to 'empirical observation' or the proof must be completed.
- **[writing]** The paper claims ProRL eliminates the 'length shortcut' entirely. However, Table 3 (Stability analysis) shows ProRL still generates paths of length ~3.8 on average. The claim should be refined to state that ProRL 'mitigates' or 'controls' the length shortcut to a stable, moderate range, rather than eliminating the phenomenon of path extension.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Impact Statement' is generic and fails to address specific ethical risks of 'proactive' systems, such as manipulation, filter bubbles, or the potential for guiding users toward harmful content. Explicitly discuss safeguards against these dual-use risks.
- **[writing]** The methodology relies on a 'user simulator' (SASRec) to estimate acceptance probabilities. The paper lacks a statement on whether this simulator was validated against real human feedback or if it introduces bias that could lead to unsafe recommendations in deployment.
- **[writing]** The 'Smooth-Guided Data Construction' uses a 'Feasibility Oracle' (KG-based or LLM-based) to mine trajectories. The paper does not disclose the safety alignment or content filtering protocols used for the LLM oracle, raising concerns about the generation of unsafe or biased guidance paths.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The paper claims statistical significance (p < 0.05) for all ProRL improvements in Tables 1, 2, and Appendix tables, but does not specify the statistical test used (e.g., paired t-test, Wilcoxon) or the number of independent runs (seeds) performed. Standard practice for RL requires reporting mean/std over at least 3-5 seeds to establish significance. Without this, the p-values are unverifiable.
- **[science]** The 'Length Collapse' phenomenon (Section 2.2) is a central empirical claim driving the method. While Figure 2 illustrates this, the text lacks quantitative evidence of the variance in path lengths for standard baselines (e.g., REINFORCE) compared to ProRL. Explicitly reporting the standard deviation of path lengths across seeds would strengthen the evidence that the 'shortcut' is a consistent failure mode rather than a training artifact.
- **[science]** The ablation study in Table 3 (w/o SRC) shows a massive drop in IoI/IoR but a spike in CTR. The paper attributes this to the 'length shortcut,' but does not provide the resulting average path lengths for the 'w/o SRC' condition. Showing that the 'w/o SRC' model indeed generates significantly longer paths (e.g., L > 8) compared to ProRL (L ~ 3-4) is necessary to empirically validate the mechanism's specific role.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Table 1 and Table 2 mark improvements with '*' for p<0.05, but the manuscript lacks a 'Statistical Significance' subsection detailing the test used (e.g., paired t-test, Wilcoxon), the number of random seeds (n), and the correction method for multiple comparisons across 3 datasets and 4 metrics. Without this, the significance claims are unverifiable.
- **[science]** The 'Advantage Variance' metric in Table 3 is reported as a relative multiplier (e.g., 0.06x) without defining the baseline denominator or providing the absolute variance values. To validate the claim of reduced variance, report the mean and standard deviation of the advantage estimates over the same number of seeds used for performance metrics.
- **[science]** The ablation study in Table 4 (w/o SRC) shows a massive drop in IoI/IoR but a spike in CTR. The statistical significance of this trade-off is not addressed. Are these differences significant? A formal test comparing the full model against ablated variants is required to support the conclusion that SRC is 'essential' rather than just 'influential'.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The manuscript contains a significant structural error where Section 2 (Experiments) appears twice with conflicting content. The first instance (e002) uses '... N rows omitted ...' placeholders, while the second instance (e000) contains full data. This duplication and inconsistency must be resolved to ensure the final PDF is coherent and complete.
- **[writing]** In the Introduction (e000), the author list includes 'qwen.qwen3.5-122b' as a co-author. This appears to be an artifact of the generation pipeline rather than a human researcher. Please verify the author list and remove any non-human entities to maintain academic integrity.
- **[writing]** In Appendix A2 (e001), the text references 'Eq.~\eqref{eq:gradient_distribution}', but this equation label is not defined in the provided LaTeX source. Ensure all cross-references are valid and point to existing equations.
