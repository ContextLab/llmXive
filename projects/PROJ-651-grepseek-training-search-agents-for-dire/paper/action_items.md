# Automated-review action items — GrepSeek: Training Search Agents for Direct Corpus Interaction

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper makes several specific factual claims regarding dataset composition, performance metrics, and statistical significance that require tighter alignment with their cited sources or internal consistency. First, the description of the corpus in Section 3 ("Experimental Setup") and the Introduction states: "Corpus: 2018 Wikipedia (21M docs, 14GB)." This claim is attributed to \citep{karpukhin2020dense}. However, the Karpukhin et al. (2020) paper (DPR) describes a corpus of 21M *passages* ext

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 2 caption: The phrase 'Efficiency and cost analysis of compared to' contains a grammatical error (missing subject) and should be corrected to 'Efficiency and cost analysis of GrepSeek compared to'.
- **[science]** Figure 2b: The 'Ours' bar represents 14 GB of RAM, which is significantly lower than the baselines (70 GB and 221 GB). The y-axis scale (0-200+) makes this bar appear negligible; a broken axis or inset would better visualize the magnitude of this improvement.
- **[science]** Figure 2c: The 'Ours' bars are labeled '1m' (1 minute) but are plotted at the zero baseline, making them visually indistinguishable from zero. This obscures the data; the y-axis should be adjusted or the bars highlighted to show they are non-zero.
- **[writing]** Figure 4: The x-axis label '# SFT Trajectory' is ambiguous regarding the 'base (0)' tick; the caption does not clarify if 'base' represents a model with zero SFT trajectories or a pre-trained baseline.
- **[writing]** Figure 4: The x-axis label '# SFT Trajectory' is grammatically incomplete and should be pluralized to '# SFT Trajectories' to match the caption.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific acronyms and technical shorthand that are not defined upon first use, creating a barrier for non-specialist readers. The term "DCI" (Direct Corpus Interaction) is central to the paper's contribution but is never explicitly expanded in the Abstract or Introduction, appearing only as an acronym. Similarly, "GRPO" (Group Relative Policy Optimization) and "SFT" (Supervised Fine-Tuning) are used frequently in Sections 2 and 3 without initial definition

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The logical flow regarding the efficiency gains in Section 2.2 ("Efficient Corpus Interaction") contains a potential conflation of variables. The text states that sharded-parallel execution reduces latency from 5.39s to 0.71s. However, the description of the "Persistent Search Daemon" (which keeps the corpus in memory) is presented as a separate bullet point. It is logically ambiguous whether the 5.39s baseline includes the overhead of process startup for every query (which the daemon eliminates

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The paper makes several strong claims regarding the superiority and practicality of Direct Corpus Interaction (DCI) that slightly overreach the presented evidence, particularly regarding the trade-offs between latency, surface-form robustness, and the definition of "indexing." First, the narrative in Section 3.2 ("Main Findings") claims the method "outperforms all baselines on 4/7 datasets" and frames the performance on PopQA as a "minor degradation." However, Table 1 explicitly marks the PopQA

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper presents a Direct Corpus Interaction (DCI) agent trained via a two-stage process involving a "Tutor" model that is explicitly "answer-aware" (Section 2.1.1, Appendix). From a safety and ethics perspective, the primary concern is the potential for data leakage and the integrity of the evaluation. The authors state that the Tutor decomposes queries and answers to construct retrieval chains in reverse. It is critical to explicitly confirm in the text that the evaluation datasets (NQ, Hotp

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim of statistical significance (p<0.05) for F1 and EM improvements lacks methodological detail. Specify the statistical test used (e.g., McNemar's, bootstrap) and report the number of random seeds or runs used to estimate variance, as single-run results on large datasets can be noisy.
- **[science]** The ablation study (Tables 1 & 2) shows a massive performance drop when removing SFT, but the 'w/o GRPO' variant still outperforms baselines on some metrics. Clarify if the GRPO-only baseline was trained from scratch or initialized from the SFT model, as this affects the interpretation of the 'cold-start' contribution.
- **[science]** The efficiency claim (14GB RAM vs 221GB) compares the agent's runtime memory against the index size of dense retrievers. To support the 'zero offline indexing' claim robustly, explicitly state the time required to load the 14GB corpus into RAM and whether this 'warm-up' cost is included in the reported 8.67s latency.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The paper claims statistical significance (p<0.05) for performance gains in Tables 1 and 2 (F1 and EM) but does not specify the statistical test used (e.g., McNemar's, paired t-test) or the number of independent runs. Without variance estimates or test details, these significance claims are unverifiable.
- **[science]** The RL training protocol specifies only 200 steps with a group size of n=5. The paper reports single-point performance metrics without confidence intervals or standard deviations across multiple random seeds, making it impossible to assess the stability or reproducibility of the reported gains.
- **[science]** The ablation study (Tables 1 & 2) compares the full model against variants without reporting statistical significance for the differences between the ablated models and the baseline. It is unclear if the observed drops are statistically significant or within the noise of the evaluation.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 2.1 (Training DCI Search Agent), the phrase 'answer-aware Tutor' and 'answer-blind Planner' are introduced without defining what 'answer-aware' or 'answer-blind' specifically entails in this context. Clarify these terms or provide a brief parenthetical explanation to ensure reader comprehension.
- **[writing]** In Section 3.2 (Main Findings), the sentence 'It excels at exact entity matching and rare patterns (e.g., chemical formulas) where dense retrievers fail due to semantic conflation' is slightly ambiguous. Specify whether 'semantic conflation' refers to the retriever's inability to distinguish similar entities or its tendency to merge distinct concepts.
- **[writing]** In the Appendix (Section A.3, Reward Function), the formula for $R_{\mathrm{ans}}$ uses $\max_{y\in\mathcal Y}F_1(\hat y,y)$, but the text does not explicitly define $\mathcal Y$ (the set of gold answers) or $\hat y$ (the predicted answer) in this specific context, assuming prior knowledge. Define these variables for clarity.
