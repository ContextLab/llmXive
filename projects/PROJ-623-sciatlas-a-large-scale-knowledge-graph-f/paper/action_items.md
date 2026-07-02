# Automated-review action items — SciAtlas: A Large-Scale Knowledge Graph for Automated Scientific Research

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Table 1 (e001) lists CITES edges as 1.2B and COAUTHOR as 800M, but Table 1 (e000) and the text (e000) state 213.88M CITES and 2.06B COAUTHOR. These are direct contradictions. The authors must reconcile these numbers and ensure the table matches the text.
- **[writing]** The abstract and introduction claim the KG contains '3B triplets' (edges), but the sum of the specific edge counts provided in the detailed table (e000) is approximately 2.8B. The authors should clarify if '3B' is a rounded estimate or if the detailed counts are incomplete.
- **[writing]** The paper cites 'Qwen3-30B-A3B-Instruct' (e001) and 'Qwen3' (e000). As of the current date, Qwen3 is not a publicly released model family (Qwen2.5 is the latest). The authors must verify the model name/version or provide a citation if this is a pre-release/internal model.
- **[writing]** The bibliography lists the OpenAlex URL (c-001) as 'unreachable'. While external links can change, the authors should verify the stability of the data source link or provide a DOI/Archive link for the specific snapshot used.

## paper_reviewer_figure_critic — verdict: minor_revision

- **[writing]** Figure 1: The caption contains a grammatical error and missing subject ('Discipline Distribution in . is a large-scale...'), likely due to a placeholder variable not being replaced with the system name.
- **[writing]** Figure 1: The legend lists 26 disciplines, but the pie chart labels are crowded and illegible for the smaller slices (e.g., <2%), making it difficult to map specific colors to the legend entries without zooming.
- **[writing]** Figure 2: The caption contains multiple instances of missing text where the system name should appear (e.g., 'Schema of .', 'provides a structured...', 'of can be found in Appx..'). This makes the figure description grammatically incomplete and unclear.
- **[writing]** Figure 2: Several attribute labels in the 'Author' and 'Institution' entity boxes are truncated with ellipses (e.g., 'displ...', 'works_co...', 'cited_by_c...'), reducing readability and preventing verification of the full schema.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on high-level, abstract terminology that obscures the specific technical contributions for a general scientific audience. The most significant issue is the overuse of "neuro-symbolic" (Abstract, Sec 1, Sec 3) without a clear, plain-English definition of how the neural (vector embeddings) and symbolic (graph logic) components interact. While experts in the field may recognize the term, a broader audience requires an explicit explanation of the mechanism. Similarly, p

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Resolve the contradiction in Table 1 (e001) where CITES edges are listed as 1.2B and COAUTHOR as 800M, conflicting with the text and Table 1 (e000) stating 213.88M CITES and 2.06B COAUTHOR. This data swap undermines the statistical validity of the graph description.
- **[writing]** Clarify the 'tri-path' claim. The text describes three matching paths (Sec 3.1) but merges them into a single seed set before a single Random Walk (Sec 3.3). The term implies parallel graph exploration, but the mechanism is sequential filtering. Re-evaluate terminology to match the algorithm.
- **[science]** The claim that the system reduces inference costs (Abstract, Conclusion) lacks support. The pipeline involves multiple LLM calls and graph traversal. Without a comparative analysis of token usage or latency against a baseline, the causal claim of cost reduction is unsupported.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The manuscript makes several claims that extend beyond the evidence provided in the text, particularly regarding the nature of the retrieval algorithm and the comparative benefits of the system. First, the Abstract and Conclusion repeatedly describe the retrieval pipeline as achieving "deterministic association discovery." This is a significant overreach. The core algorithm employed is Random Walk with Restart (RWR), which is inherently a stochastic process. While the implementation yields repro

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The manuscript lacks a dedicated Ethics Statement or Data Privacy section. Given the inclusion of 109.7M author nodes and 195.94M affiliation edges, explicit confirmation of compliance with OpenAlex's Terms of Service and GDPR/CCPA regarding researcher data is required.
- **[writing]** The 'Idea Generation' application (Sec 5.3) proposes using the KG to synthesize novel research concepts. A discussion on the risks of dual-use (e.g., accelerating the discovery of harmful biological agents or cyber-attack vectors) and the system's potential to automate the generation of disinformation or biased scientific claims is missing.
- **[writing]** The 'Researcher Background Review' feature (Sec 5.6) aggregates and summarizes individual academic trajectories. The paper must clarify the consent model for this profiling and address potential biases in the LLM-generated summaries that could unfairly impact researchers' reputations.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The paper claims a 'neuro-symbolic retrieval algorithm' achieves 'deterministic association discovery' but provides no quantitative evaluation (e.g., precision@k, recall, NDCG) against baselines. Without empirical metrics on a held-out test set, the efficacy of the proposed RWR and weighting scheme remains an unverified assertion.
- **[science]** The construction pipeline relies on a single LLM (Qwen3) for keyword extraction without reporting inter-annotator agreement, human validation, or error rates. The quality of the 3.76M keyword nodes is a critical dependency for the graph's utility, yet no evidence of extraction accuracy is provided.
- **[science]** The retrieval algorithm contains multiple tunable hyperparameters (e.g., theta_kw=0.7, lambda_emb=0.3, gamma=0.5). The manuscript does not describe the methodology used to select these values (e.g., grid search, ablation study) or report sensitivity analysis, raising concerns about overfitting to anecdotal examples.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The manuscript defines edge weights (Table 1) and node importance scores (Eq. 6-7) using fixed hyperparameters (e.g., gamma=0.5, beta_cite=1.00) without reporting any sensitivity analysis, ablation studies, or statistical justification for these specific values. The impact of these choices on retrieval performance is unquantified.
- **[science]** The paper claims a 'neuro-symbolic retrieval algorithm' but provides no statistical evaluation metrics (e.g., Precision@K, Recall@K, NDCG, or Mean Average Precision) comparing the proposed method against baselines. Without quantitative results and confidence intervals, the claim of 'seamless transition' and 'reduced inference cost' is unsupported by evidence.
- **[science]** The construction pipeline relies on LLMs (Qwen3) for keyword extraction and scoring. The manuscript fails to report inter-annotator agreement (e.g., Cohen's Kappa) or validation statistics against a human-annotated gold standard to assess the reliability and bias of these extracted features.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** Inconsistent naming: The paper alternates between 'SciAtlas' and 'SciMap' (e.g., Table 1 caption in e001). Standardize to 'SciAtlas' throughout.
- **[writing]** Grammar and flow: The abstract contains a sentence fragment ('...consuming high inference costs') and awkward phrasing ('In this report, we introduce...'). Revise for professional academic tone.
- **[writing]** Table inconsistency: Table 1 in e001 lists 'CITES' as 1.2B and 'COAUTHOR' as 800M, while the text and Table 1 in e000 list different values (213.88M CITES, 2.06B COAUTHOR). Ensure data consistency across all tables.
- **[writing]** LaTeX syntax error: In e001, the table caption for 'Statistics of SciAtlas' contains a typo 'SciMap' instead of 'SciAtlas'. Additionally, the table body uses '...' placeholders which should be replaced with actual data or removed.
