# Automated-review action items — Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The review focuses on the accuracy of factual claims and the validity of the mathematical derivations supporting the paper's central hypotheses. Mathematical Validity of the "Average Token" Derivation (Section 3.2.2): The paper claims to reverse-engineer an "average" token embedding $\hat{\vh}$ using the formula $\hat{\vh} = \log(\hat{\vp}) \, \mW_{\mathcal{U}}^+$ (Eq. 4). This derivation is mathematically flawed. The starting point is the logit equation $\vh \, \mW_\mathcal{U}^\top = \log(\vq)

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The word clouds contain raw escape sequences (e.g., '\n\n', '\n') and punctuation artifacts (e.g., '80', '[', ']') that are not present in the input text provided in the caption; the visualization should either clean these tokens or the caption should explain their presence.
- **[writing]** Figure 1: The word clouds are cluttered with overlapping text and inconsistent font sizes, making it difficult to distinguish the relative importance of tokens or read smaller words clearly.
- **[fatal]** Figure 2: The y-axis label is the symbol '$\Delta\pi$' but the caption text is missing the symbol entirely (rendered as 'Figure 2: ( ) distribution...'), making the figure's subject undefined.
- **[science]** Figure 2: The y-axis uses a logarithmic scale (0.16% to 20.0%) but lacks grid lines or tick marks between the labeled decades, making it impossible to estimate intermediate values.
- **[writing]** Figure 2: The x-axis tick labels (e.g., 112, 224, 336) are non-standard and lack a clear unit or definition (e.g., 'dimension index' or 'tokens'), which is not explained in the caption.
- **[fatal]** Figure 3: The caption contains critical missing information, specifically the name of the method or variable represented by the backslash symbol (\) in 'refined by .' and '\ suppresses...'. This makes the figure's context and claims unintelligible.
- **[science]** Figure 3: The caption claims to display 'Top-6 tokens', but the word clouds show dozens of tokens of varying sizes without a clear legend or scale defining the top 6, making the specific claim unverifiable.
- **[science]** Figure 3: The caption states 'colored entries indicate tokens that have literal connections', but the word clouds use a multi-color palette for all words without a legend or visual distinction to identify which specific tokens are 'colored entries' versus others.
- **[fatal]** Figure 4: The y-axis label is the symbol '$\Delta\pi$' without defining what this metric represents (e.g., change in probability, divergence). The caption refers to '$\Delta\pi$ distribution' but does not define the variable, making the scientific content unintelligible.
- **[fatal]** Figure 4: The figure contains three subplots but lacks a legend or any labels to distinguish the three conditions mentioned in the caption ('high-frequency', 'low-frequency', and 'randomly sampled tokens'). It is impossible to determine which subplot corresponds to which token category.
- **[science]** Figure 4: The y-axis uses a logarithmic scale (0.16% to 20.0%) but lacks grid lines or tick marks at intermediate powers of 10, making it difficult to accurately compare the magnitude of values across the different subplots.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized terminology from mechanistic interpretability and linear algebra without providing sufficient scaffolding for a general audience. While the core concepts are sound, the density of jargon creates a barrier to entry. Specifically, the terms "Logit Lens" and "Logit Spectroscopy" are introduced in the Introduction (Section 1) with a footnote directing readers to Section 2 for details. This is insufficient for a general paper; these tools should be briefly

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[fatal]** The proof in Appendix sec:proof claims V_tau * V_tau^T is the identity matrix, which is false for a truncated projection. This invalidates the step ||z * V_tau * V_tau^T|| = ||z||. The proof must be corrected to show norm preservation via orthogonality of V_tau in the reduced space.
- **[science]** The derivation of the 'average' token (h_hat = log(p_hat) * W_U^+) ignores the non-linearity of Softmax and the log-sum-exp normalization term. The linear inversion used is mathematically unsound, making the 'reverse-engineering' claim speculative rather than derived.
- **[science]** The ablation study shows filtering only the 'Secondary' subspace (Config 4) performs nearly as well as the full method, while filtering 'Dominant' (Config 3) hurts performance. The logic for including the 'Dominant' subspace in the filter is not justified by these results.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim that the transformation is 'distance-preserving' (Section 4.2, Eq. 1) is mathematically incorrect for dimensionality reduction. The proof in Appendix B incorrectly assumes V_tau * V_tau^T is the identity matrix; it is a projection matrix. Consequently, the claim that reducing dimensions to 1/tau 'causes no theoretical difference in similarity measurement' is an overreach not supported by the provided proof.
- **[writing]** The abstract and introduction claim the method enables 'inherent dimensionality reduction... while fully preserving the refined embedding quality.' The results in Table 1 show performance drops (e.g., Qwen ECHO Avg drops from 52.55 to 49.43 at tau=8). The claim of 'fully preserving' quality is an overstatement given the observed trade-offs in the data.
- **[science]** The paper asserts that the 'edge spectrum' is 'primarily responsible for encoding high-frequency tokens' based on Logit Spectroscopy of a reverse-engineered 'average' token. However, the paper does not provide evidence that this specific subspace is the *sole* or *dominant* cause of anisotropy in actual text embeddings versus the synthetic average token, potentially over-extrapolating from a proxy analysis.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The Acknowledgments section (lines 1045-1050) explicitly states the work is supported by Lenovo Group and lists authors from Lenovo. The manuscript must include a formal Conflict of Interest (COI) statement clarifying the nature of this funding and any potential influence on the research design or results, as required by most academic venues.
- **[writing]** The paper proposes a method to filter 'edge spectrum' subspaces to remove high-frequency tokens. While intended to improve semantic quality, this mechanism could be misused to systematically suppress specific topics, political viewpoints, or safety-critical keywords if the 'frequent token' definition is manipulated. The authors should add a discussion on the potential for dual-use in censorship or bias amplification and propose mitigation strategies.
- **[writing]** The methodology relies on approximating training corpus word frequencies using the RedPajama dataset (Section 3.2.1, lines 430-435) because the actual pretraining data is undisclosed. The authors should explicitly discuss the ethical implications of using a proxy dataset for reverse-engineering model internals, particularly if the proxy distribution differs significantly from the actual training data, potentially leading to unintended filtering of legitimate semantic content.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The proof in Appendix~ef{sec:proof} claims V_tau * V_tau^T is identity, which is false for dimensionality reduction (tau > 1). This invalidates the 'distance-preserving' claim. Correct the proof to reflect the projection geometry.
- **[science]** The 'average' token reverse-engineering assumes the unembedding matrix pseudo-inverse recovers a hidden state from log-probs, ignoring bias effects. Provide stronger justification or empirical validation for this heuristic across model architectures.
- **[science]** The ablation study shows 'Bulk' filtering fails but lacks a theoretical explanation for why edge spectra specifically encode high-frequency tokens. Add mechanistic analysis to rule out overfitting to specific model spectral properties.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[fatal]** The proof in Appendix~\ref{sec:proof} contains a fatal algebraic error. The authors claim V_tau * V_tau^T is the identity matrix, which is false for a truncated projection matrix (it is a projection, not identity). Consequently, the claim that ||z * Phi^T||_2 = ||z||_2 is incorrect; the transformation reduces the norm. The dimensionality reduction claim relies on this flawed identity.
- **[science]** The ablation study in Table~\ref{tab:ablation} lacks statistical significance testing. With 49 datasets, reporting single-point averages without standard deviations, confidence intervals, or paired t-tests makes it impossible to determine if the observed gains (e.g., +9.0%) are robust or due to random variance.
- **[science]** The reverse-engineering of the "average" token in Section~\ref{sec:interpret} uses log(frequency) as a proxy for logits without accounting for the temperature scaling or the bias term (vb) omitted in Equation 5. This approximation may introduce systematic bias in the identification of the edge spectrum subspace.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the Abstract, the phrase 'By filtering out this subspace, \name\ suppress the influence' contains a subject-verb agreement error. Since \name\ is singular, it should be 'suppresses'. This error appears in the Abstract and Section 1.
- **[writing]** In Section 1 (Introduction), the sentence 'We provide an mechanism interpretation' uses the incorrect article 'an' before a consonant sound. It should be 'a mechanism interpretation'.
- **[writing]** In Section 1, the sentence ending '...providing a detailed account of its identification' is a fragment lacking a period. Additionally, the phrase 'preliminaries analyses' in Section 3.1 should be 'preliminary analyses'.
- **[writing]** In Section 5.2, the phrase '...prompt-engineering methods exhibits performance fluctuations' has a subject-verb agreement error. 'Methods' is plural, so it should be 'exhibit'.
- **[writing]** In Section 5.3, the word 'acorss' is a typo and should be corrected to 'across'.
- **[writing]** In the Appendix (Section A.2), the proof concludes with 'this completes the proof...', which should be capitalized as 'This completes the proof...' to start a new sentence.
