# Automated-review action items — Redesign Mixture-of-Experts Routers with Manifold Power Iteration

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Section 1 (Introduction), the claim that the method 'provides a theoretical analysis yielding tighter bounds on expert utilization' is unsupported. The paper derives an optimization interpretation (Eq. 10) and convergence intuition but presents no formal bounds on utilization metrics (e.g., load variance or collision rates) compared to baselines. This overstates the theoretical contribution.
- **[writing]** In Section 3.2 (Eq. 10) and Appendix A, the derivation claims the update rule is an 'approximation' of steepest ascent. However, the text asserts 'striking structural alignment' and 'equivalence' without quantifying the error term or proving the approximation holds under the specific non-stationary conditions of online training. The claim of equivalence is too strong given the lack of error bounds.
- **[writing]** In Section 4.1, the claim that the method is 'agnostic to shifts in model features across optimizers' is based on 1B parameter experiments. Extrapolating this to claim fundamental agnosticism for 11B+ models without explicit theoretical justification or larger-scale ablation is an overgeneralization of the evidence provided.
- **[writing]** In Section 4.2, the claim that the 0.2% slowdown is 'negligible' and 'does not exceed that of N extra tokens' lacks a rigorous breakdown. The power iteration involves matrix-matrix multiplications ($R 	imes W 	imes W^T$) which are computationally heavier than simple token additions. The specific arithmetic justification for this claim is missing from the text.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains a placeholder artifact 'with ,' and the model name 'grayMuonH-1B' appears to be a raw filename or variable name rather than a clean description.
- **[science]** Figure 1: The legend labels 'MuonH' and 'MuonH w. MPI' do not explicitly identify which line corresponds to the 'router design' mentioned in the caption, making the claimed 0.013 reduction difficult to verify visually.
- **[science]** Figure 2: The caption claims the method facilitates 'faster convergence,' but the x-axis is 'Tokens' (compute budget), not 'Wall-clock time' or 'Steps.' Since the curves overlap significantly in the loss plot (a), the claim of faster convergence is not supported by the provided axes.
- **[writing]** Figure 2: The caption contains a missing variable placeholder (a backslash '\') before 'facilitates,' likely referring to the specific router design or method name which is absent from the text.
- **[fatal]** Figure 3: The caption states 'Load balancing loss for 3B MoE with [missing method]', but the rendered plot shows two distinct lines ('MoE' and 'MoE w. MPI') without defining what the purple line represents in the text. The caption is incomplete and fails to describe the comparison shown.
- **[science]** Figure 3: The y-axis scale is extremely narrow (0.016 to 0.017), which visually exaggerates the difference between the two curves. While the absolute difference is small, the visual presentation may mislead readers regarding the magnitude of the improvement in load balancing loss.
- **[fatal]** Figure 4: The caption claims to show 'pretraining collapses' without Router Retraction, but the plot displays 'Accuracy (%)' on the y-axis, not pretraining loss. Furthermore, the 'MPI w.o Retraction' line (pink) shows high accuracy (~53%) and does not collapse, directly contradicting the caption's claim of instability.
- **[science]** Figure 4: The x-axis labels (100B, 125B, 150B, 175B, 200B) imply a 200B token training run, but the caption specifies this is for a '3B MoE' model. This scale is inconsistent with the model size described in the caption.
- **[writing]** Figure 4: The caption mentions 'Router Retraction' and 'Power Iteration' as key design choices, but the legend labels ('MoE w. MPI', 'MPI w.o Power-Iter', 'MPI w.o Retraction') are inconsistent in naming convention and do not clearly map to the specific ablation conditions described.
- **[writing]** Figure 5: The caption contains a placeholder '\\' instead of the specific method name (e.g., 'MuonH' or 'MPI') that the figure legends refer to as 'w. MPI', making the claim 'MoE with \\ achieves...' unreadable.
- **[writing]** Figure 5: The top subplot legend lists 'AdamW' and 'AdamW w. MPI', but the caption claims a comparison across 'AdamW, AdamH, Muon'; the top plot should likely be labeled 'AdamH' to match the caption's description of the three optimizers.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The acronym 'MPI' is defined in the preamble as 'Message Passing Interface' (line 42), conflicting with the paper's usage for 'Manifold Power Iteration'. Remove the conflicting preamble definition and define 'Manifold Power Iteration' clearly at first use in the abstract or introduction.
- **[writing]** Replace the industry slang 'midtrain' (Section 5.2) with 'continued pretraining' to ensure clarity for non-specialist readers unfamiliar with this specific training phase terminology.
- **[writing]** Define the metric 'MaxVio' (Section 5.2, Table 4) at first use. The text mentions it reflects load balance but does not define the acronym (e.g., Maximum Violation) or its calculation.
- **[writing]** Correct the typo 'Opimization' to 'Optimization' in Section 5.1 and briefly explain 'Hyperball Optimization' (e.g., constraining weights to a hypersphere) for readers unfamiliar with the cited work.
- **[writing]** Correct the grammatical error 'Principle Singular direction' to 'Principal Singular direction' in Section 6.1 to align with standard linear algebra terminology and avoid confusion.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The claim that MPI is 'equivalent to a steepest ascent optimization' (Sec 3.3) is unsupported. Eq. 10 shows structural similarity, not equivalence. The adaptive step-size is not proven to match the optimal step-size for steepest ascent on the manifold, weakening the theoretical claim.
- **[science]** The argument that 'aggressive alignment disrupts stability' (Sec 4.1) with 10 iterations contradicts standard power iteration convergence. The paper lacks a mechanism (e.g., gradient variance analysis) to explain why tighter alignment to the principal direction would destabilize the optimizer.
- **[science]** The load balancing improvement is attributed to 'retraction design' (Sec 4.1), yet the ablation (Fig 4) shows the 'Retraction-only' baseline achieves similar balance. This suggests normalization, not the power iteration interaction, drives the benefit, weakening the causal claim for the full method.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The Introduction claims the method provides 'tighter bounds on expert utilization' (Section 1, Contributions), yet the paper presents no formal bounds, theorems, or proofs regarding utilization rates. This is an unsupported theoretical claim that must be removed or substantiated with actual derivations.
- **[science]** The Abstract and Introduction state that the method 'matches or exceeds' recent alternatives like Switch Transformer, but the Experiments section (Section 5) explicitly states: 'We forgo comparisons with other baselines since our design conforms to the standard router form.' The claim of superiority over specific named baselines is unsupported by the provided data.
- **[writing]** The paper claims 'zero inference overhead' (Section 5, Efficiency Analysis) because weights are pre-computed. However, the 'Power-then-Retract' step requires matrix-vector products with expert weights ($W_g W_g^T$) during the forward pass (Eq. 2) or at load time. If computed at load time, this adds a non-trivial initialization cost proportional to expert size, which contradicts the 'zero overhead' absolute claim. If computed online, it adds FLOPs. The claim needs qualification.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Ethical Considerations' section (lines 13-24) and 'Broader Impact' section (lines 1085-1093) acknowledge dual-use risks but lack concrete mitigation strategies. Explicitly detail proposed technical safeguards (e.g., specific watermarking techniques, access control protocols) or policy frameworks the authors intend to support, rather than generic calls for 'usage policies.'
- **[writing]** The 'Reproducibility' section (lines 1065-1072) and code availability statement (line 1067) cite a placeholder GitHub URL ('https://github.com/yourorg/mixture-of-experts-routers') and a generic commit hash. For a paper claiming efficiency gains in large-scale training, the absence of a verifiable, functional code repository prevents independent safety auditing of the implementation for potential instability or unintended behaviors.
- **[writing]** The manuscript states training data (FineWeb-Edu) contains no PII (lines 1078-1080). However, it does not address the potential for the model to memorize and regurgitate sensitive information present in the broader pretraining corpus or the specific 'Math' and 'Code' datasets used for evaluation. A brief discussion on memorization risks or privacy-preserving training techniques would strengthen the safety profile.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim of 'faster convergence' and 'superior performance' lacks statistical significance testing. Table 1 (tab:opt-agnostic) and Table 3 (tab:midtrain) report single-point averages without standard deviations, confidence intervals, or p-values. Given the stochastic nature of LLM pretraining, single-run comparisons are insufficient to rule out random variance as the cause of observed gains.
- **[science]** The ablation study in Section 5.2.1 (lines 630-650) compares the full method against a 'normalization-only' baseline but fails to include a 'power-iteration-only' (no retraction) baseline in the final performance tables. While the text mentions instability for the latter, quantitative data on its performance (if stable runs were possible) or a clear explanation of why it cannot be compared fairly is needed to isolate the specific contribution of the retraction step versus the power iteration.
- **[science]** The efficiency claim of '0.2% slowdown' (Section 4.3, line 560) is presented as a definitive metric but lacks the necessary context of variance or measurement methodology. Was this measured over a single step or an average over the entire training run? Without error bars or a description of the measurement protocol, this precise figure is not robustly supported.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The paper reports downstream performance improvements (e.g., Table 1, Table 3) and loss reductions (e.g., Figure 1, Table 2) as deterministic facts without reporting statistical significance. Given the stochastic nature of deep learning training, the authors must report standard deviations or confidence intervals across multiple random seeds (e.g., 3-5 runs) to confirm that the observed gains are not due to random variance.
- **[science]** In Section 5.1 (Ablation Studies), the claim that 10 power iterations 'provides no further convergence advantage' is based on a single run comparison (0.002-0.003 loss increase). Without error bars or variance estimates, it is impossible to distinguish a genuine performance drop from noise. The authors should re-run these ablations with multiple seeds to validate the stability of the single-iteration choice.
- **[science]** The sensitivity analysis of hyperparameter C' (Table 4) presents a single validation perplexity value for each setting. To support the claim of 'insensitivity,' the authors should report the variance of these metrics across different random seeds or data shuffles, as small fluctuations in PPL could otherwise be misinterpreted as robustness.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.2, fix the dangling modifier in 'while designed to avoid instability, this retraction provides...' by rephrasing to 'While designed to avoid instability, the retraction step also provides...'.
- **[writing]** In Section 3.2, remove the duplicate word in 'to to prevent explosion'.
- **[writing]** In Section 4.2, correct the subject-verb agreement error: change 'aggressive alignment disrupt the stability' to 'disrupts'.
- **[writing]** In Section 4.2, change 'more challenge tasks' to 'more challenging tasks'.
- **[writing]** In Section 4.2, fix 'it impose no constaint' to 'it imposes no constraint'.
- **[writing]** In Section 4.2, correct 'downstream performance stills improves' to 'still improves'.
- **[writing]** In Section 5, change 'Extensive experiments validates MPI' to 'validate'.
- **[writing]** In the Abstract, clarify 'rows of the router matrix compute their similarity' to 'the router matrix computes similarity scores between its rows and inputs'.
