---
field: linguistics
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/285
paper_authors:
  - Soyeong Jeong
  - Jinheon Baek
  - Minki Kang
  - Sung Ju Hwang
---

# TIDE: Proactive Multi-Problem Discovery via Template-Guided Iteration

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.04743
Paper authors (from arXiv): Soyeong Jeong, Jinheon Baek, Minki Kang, Sung Ju Hwang

Submitted by: github-actions[bot]

(Intake from human-submission issue #285.)

## Rejection rationale (2026-06-10)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[091c53acca8a]** Multiple citations reference 2025-2026 publication dates (e.g., GPT-5 mini, Gemini 3.5 Flash, probe arXiv:2510.19771, FingerTip20K, RoT, DiscoverLLM). These future-dated citations cannot be verified as real publications and undermine the factual accuracy of all claims built upon them. Authors must replace with actual published sources or clarify the timeline.
- **[7fe509e47229]** The arXiv URL (2606.04743) indicates June 2026, a future date inconsistent with current submission. This raises concerns about the paper's provenance and the verifiability of all factual claims.
- **[9a381bb922c2]** Claims about baseline performance (Table~\ref{tab:main}) state specific F1 scores (e.g., 70.46 for GPT TIDE Retrieval). Without access to the experimental code/data, these numerical claims cannot be independently verified. Authors should ensure reproducibility information is complete.
- **[157c03aeabcc]** The claim that templates transfer across backbones (Section 6, Table~\ref{tab:transfer}) shows ~1-2 point differences between self vs. transferred templates. The paper states they "perform comparably" but does not report statistical significance testing to support this claim.
- **[0a1efe293c7b]** Section 5 claims "150 problems across 30 multi-problem workspaces" and "146 problems across 20 multi-bug test instances." These exact counts should be verifiable in the appendix or data release, but no explicit link to data availability is provided in the main text.
- **[44771875df38]** Add code availability statement with GitHub repository link for reproducibility
- **[a4c7ec266f98]** Document dependency versions (Python, LLM SDKs) and environment setup for experiments
- **[9f4cede21b17]** Include instructions for template construction and iterative discovery reproduction in appendix
- **[cc6c4f182982]** Section 5.1 describes constructing 150 workspace and 146 repository problems but provides no URL or DOI for releasing these derived datasets. A data repository link is required for reproducibility.
- **[6fd96249dffc]** The license for the constructed datasets (workspace and repository splits) is not specified. Clarify the license terms for the derived data to ensure legal compliance for reuse.
- **[91fbb7bb8030]** Section 5.1 mentions using 'common anchor commit' for repository instances but does not list specific commit hashes or a manifest table. Provide a link to a manifest file detailing repository names and commit IDs.
- **[9eb3a3c19833]** Add alt text to all figures for accessibility compliance. Currently none of the 10 figures include alt attributes or screen-reader descriptions.
- **[1c22474cea27]** Prompt figures (fig_prompt_inference_code, fig_prompt_inference_workspace, fig_prompt_template_construction_*) use \small font in tcolorbox; verify legibility at print scale or consider splitting across appendix pages.
- **[e232bb1ca8f9]** fig_budget_scaling and fig_template_count_scaling captions reference F1 but do not specify which F1 component (retrieval/identification/resolution) in axis labels; add explicit axis labels with metric names.
- **[cb3d56305428]** fig_multi_bottleneck_scaling combines two subfigures with shared_legend.pdf; ensure the legend is visible and positioned where both subpanels can reference it without ambiguity.
- **[f7867cc3dc5f]** Replace 'thought templates' with 'reasoning patterns' in Abstract and Introduction for broader clarity.
- **[1177a03546b8]** Replace 'backbones' with 'models' in Section 5 (Experimental Setup) and Section 6 (Results).
- **[01adf2aa6344]** Replace 'ablate' with 'disable' or 'remove' in Section 6 (Results) for non-technical readers.
- **[ef3392c452fe]** Replace 'gold' with 'reference' or 'ground truth' in Section 5 and Tables to avoid gaming terminology.
- **[ae06c62911b5]** Clarify the instance size discrepancy between Section 5 and Section 6. Section 5 states Repository instances have 2-41 problems, but Section 6 claims 'every instance contains four to six gold problems' when referencing Figure 4. Explicitly limit the 'four to six' claim to the Workspace subset shown in Figure 4 to avoid contradicting the Repository dataset definition.
- **[b6f457b7b58b]** The Ethics Statement (Section 10) is generic and lacks specific safeguards for workspace data privacy. The paper uses personal workspace data (emails, documents, calendar entries) without detailing consent mechanisms, data anonymization procedures, or how users can opt-out of proactive scanning.
- **[2c99c7731381]** Dual-use concerns are unaddressed. The system could enable workplace surveillance or unauthorized scanning of private documents. The code-discovery capability could surface security vulnerabilities that may be misused. These risks need explicit discussion and mitigation strategies.
- **[1c78daedb6d0]** The limitations section (Section 9) omits ethical limitations entirely. Given the privacy-sensitive nature of workspace scanning, potential harms from false positives (e.g., escalating non-issues), and deployment risks in sensitive contexts should be discussed.
- **[66eb3c4e4d1b]** Report statistical significance testing (p-values, confidence intervals) for all main results in Table 1. Three independent runs are mentioned but no uncertainty bounds are provided.
- **[a0102bc6d6e9]** Validate the LLM judge (GPT-5 mini) used for Identification/Resolution scoring with human annotations on a held-out subset to establish inter-rater reliability.
- **[0da9bb486389]** Apply multiple comparison correction (e.g., Bonferroni or FDR) given the 48+ comparisons across metrics, models, and settings reported without adjustment.
- **[e75486df7298]** Provide cost analysis comparing iterative TIDE vs parallel baselines in terms of total tokens/compute, not just iteration count matching.
- **[48228e810ff8]** Report standard deviations or 95% confidence intervals for all metrics in Table 1 (Section 6.1) to quantify variance over the three independent runs mentioned in the caption.
- **[4a796f027136]** Include statistical significance tests (e.g., bootstrap or paired t-test) for comparisons between TIDE and baselines to support claims of 'consistent outperformance'.
- **[e5edb64c74d6]** Clarify the random seeds and temperature settings for the LLM judge (GPT-5 mini) to ensure reproducibility of the evaluation scores.
- **[b185f6170bc8]** Reorder section inputs in acl_latex.tex: Sections/3_related_work.tex is currently input after Section 6 (Results), causing heading hierarchy to render incorrectly (Section 3 appearing after Section 6). Move it before Section 4 (Method).
- **[86fe7b116347]** Remove redundant \appendix command in Sections/8_appendix.tex; the main file already invokes \appendix before inputting this section.
- **[01a3cc9b4938]** Introduction, Section 2, paragraph 4: The sentence beginning 'Meeting this task requires two complementary capabilities...' exceeds 50 words and contains multiple clauses. Split into 2-3 shorter sentences for improved readability.
- **[f1951beb3ebd]** Results, Section 6: Several analysis paragraphs (e.g., 'Discovery on Multi-Problem Instances') combine multiple analytical claims in single paragraphs. Consider breaking into separate paragraphs by claim type (coverage vs. precision vs. budget scaling).
- **[23834b134cb2]** Throughout: The terms 'bottleneck' and 'hidden problem' are used interchangeably in Method and Results sections. Add a brief definitional note in Section 4.1 to ensure terminological consistency for readers.
- **[8cb9349a91ba]** Figure captions (e.g., Figure~ef{fig:multi_bottleneck_scaling}): Some captions exceed 2 lines of dense text. Consider splitting caption into two parts: (1) what the figure shows, (2) the key takeaway.
