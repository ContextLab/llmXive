---
field: other
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/162
---

# https://arxiv.org/abs/2604.27351

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2604.27351

Submitted by: github-actions[bot]

(Intake from human-submission issue #162.)

## Rejection rationale (2026-06-07)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[f7c706321121]** Verify all citation dates are consistent with actual publication years; several references cite 2025-2026 which conflicts with typical arXiv submission timelines and undermines credibility.
- **[60d8effa782d]** Complete all truncated table rows (e.g., "(... N rows omitted ...)" in tables) to ensure full experimental results are visible for reproducibility.
- **[9deafb775b4b]** Provide full theoretical proofs in the appendix; current text references proofs but does not include complete derivations for Theorem 1, Lemma 1, etc.
- **[e09a71c2ab61]** Clarify the relationship between arXiv ID 2604.27351 and the citation metadata; the submission date appears to be April 2026 which requires verification.
- **[5866e6870fbb]** Multiple citations reference arXiv papers with future dates (e.g., 2601.03267, 2604.27351) that cannot be independently verified. Claims about GPT-5/gpt-5-nano availability lack public evidence. Verify all model citations exist and are publicly accessible.
- **[078dd88ae513]** Section 5.3 claims EywaAgent improves utility by ~6.6% and reduces tokens ~30%. Table 1 shows 0.6154→0.6558 utility (6.6%) but token reduction is 4469→3137 (30%). However, baselines include unverified models. Provide reproducible baseline configurations.
- **[1dae86c7eda4]** Theoretical claims (Theorem 1, 2) depend on Assumption 1 (Domain Advantage) which asserts FMs outperform LLMs on domain data without empirical proof in the main text. Either provide empirical validation or qualify claims as conditional on this assumption.
- **[36b3ea44c4ec]** EywaBench claims 200 samples from 67 source datasets (Appendix Sec. B.1) citing DeepPrinciple, MMLU-Pro, fev-bench, TabArena. Verify sample counts match cited sources and provide dataset access information.
- **[12e9926e8f80]** Related Work (Sec. 6) cites domain-specific FMs (Chronos, TabPFN, AlphaFold) as lacking language interfaces. Some (e.g., AlphaFold 3, 2024) have emerging language integration. Update claims with specific versions and interface status.
- **[07a258e1701d]** Code artifacts (implementation scripts, configs, test suites) are not included in the submission package. Add repository link or zip file to enable reproducibility and code quality review.
- **[38796c15e500]** Verify external GitHub link (Violet24K/Eywa) is public and accessible; include DOI or archive link for long-term reproducibility.
- **[fe04090270ba]** Add explicit license declaration for EywaBench and cite source dataset licenses (e.g., MMLU-Pro, TabArena) in Section 'EywaBench Details' to ensure legal compliance and provenance.
- **[2ee8cd712e2f]** Fix truncated URLs in Figure 1 caption (e.g., 'https://en.wikipedia.org/wiki/Avatar_(2009_film') to prevent link rot and ensure referential integrity.
- **[ab41be9de7e7]** Clarify the 'label' column type in Table 1 (tab:eywabench_schema); it is defined as 'string' but time-series/numeric tasks require structured numeric labels for evaluation.
- **[a7ef05d20af3]** Specify version tags or commit hashes for source datasets (DeepPrinciple, MMLU-Pro, fev-bench, TabArena) to enable exact benchmark reproducibility.
- **[829650036547]** Convert figures/fig_sunburst_modality.jpg to vector PDF or high-res PNG to ensure text legibility in print.
- **[82e097ffa612]** Standardize legend placement in tradeoff_plots (Fig.~\ref{fig:tradeoff_per_domain}) instead of manual includegraphics with line breaks.
- **[020a73eeb859]** Verify all axis labels and units are explicitly visible on all tradeoff and benchmark composition figures.
- **[615e7598d0da]** Define FM (Foundation Model) and LLM (Large Language Model) at first use in the Abstract or Introduction. Currently FM appears in Preliminary section without prior definition.
- **[f4e97513a897]** Replace "Agentic" with "AI agent-based" or "systems with autonomous agents" for accessibility. Term appears 20+ times throughout manuscript.
- **[b8a42f77d4fe]** Define sMAPE and MAAPE metrics when first introduced in Appendix Metrics section. Non-specialists cannot understand utility calculation without these definitions.
- **[b486d47e82ad]** Replace "modality-native collaboration" with "direct collaboration using original data formats" in Conclusion. Current phrasing excludes non-specialist readers.
- **[1b9761352ea6]** Explain "population risk," "Data Processing Inequality," and "oracle adaptivity" in plain language in Theoretical Analysis appendix. These terms appear without any explanatory context.
- **[b402e56428a7]** Text claims EywaOrchestra 'matches or exceeds' EywaMAS utility (e000, Section Experiments), but Table 1 reports 0.6746 (Orchestra) vs 0.6761 (MAS). Revise claim to reflect data (e.g., 'approaches' or 'comparable').
- **[c66c779b6902]** Theorem 1 (Improvement of EywaAgent) relies on Assumption 4 (Faithful Interface), which assumes lossless translation by psi. This assumption is critical yet unverified empirically. Clarify this dependency in the main text to ensure logical transparency.
- **[8039f1dcf19b]** Refine Theorem 1 (Section 3) to explicitly state risk improvement is conditional on Assumption 1 (Domain Advantage), rather than implying universal superiority.
- **[1f88b2de86c3]** Correct the Conclusion's claim of 'token/latency reductions' to specify this applies to EywaAgent, as EywaMAS shows increased token usage (Table 1).
- **[d18917263f35]** Qualify the description of EywaBench as 'scalable' given the current N=200 sample size, or provide evidence of scaling beyond the fixed split.
- **[fec85116062f]** Restrict generalization claims in the Conclusion to the tested modalities (time-series, tabular) rather than implying broad scientific applicability.
- **[12783ad91ab4]** Add a dedicated 'Ethics and Broader Impact' section addressing dual-use risks, specifically for Life Science (Drug/Clinic) domains.
- **[3470fb889e4f]** Clarify data privacy and consent procedures for 'Clinic' tasks in EywaBench to ensure compliance with medical data standards.
- **[277bf6d53f51]** Report standard deviations or confidence intervals for utility scores in Table `tab:main_comparison_eywabench` to establish statistical significance.
- **[a96a081cd68e]** Include baseline results (Refine, Debate, MoA, X-MAS) in the main comparison table, not just text descriptions, to verify claims of outperformance.
- **[dd81edeec4b6]** Specify the number of random seeds or runs used to average the reported metrics, given the small sample size (N=200).
- **[ebc65e769042]** Report standard deviation or confidence intervals for all metrics in Table 1 (e000) to quantify variance across runs.
- **[bf927c6f3d3d]** Perform statistical significance testing (e.g., paired t-test or bootstrap) to validate claims of improvement like the ~6.6% gain.
- **[e763d3663857]** Explicitly state the number of random seeds used for averaging results in the Experimental Setup section.
- **[c8996156ec0d]** Remove duplicate section definitions between chunks e000 and e002 (e.g., Introduction, Preliminary, EywaAgent appear in both). This causes LaTeX redefinition errors.
- **[9212fb7447f4]** Standardize citation commands: e000 uses \cite, e002 uses \citep. Choose one style consistent with \bibliographystyle{unsrtnat}.
- **[93b136bb70b3]** Add missing bibliography keys (e.g., hu2025survey, zhang2024comprehensive) to reference.bib. Cited in e002 but absent from provided bib file.
- **[e661d4135995]** Resolve duplicate table definitions. Tables like tab:main_comparison_eywabench are defined inline in e000 and in tables/main_comparison_eywabench.tex.
- **[fe9b2f0b9250]** Fix label formatting: \label{fig: main} contains a space. Use \label{fig:main} to avoid reference issues.
- **[8b850ab54b7b]** In the Abstract (main.tex), add article 'the' before 'language interface'.
- **[7b9bc2c5f540]** In Introduction contributions (e000), fix parallelism in bullet points (e.g., 'show consistent' -> 'and show consistent').
- **[06783fd2b163]** In Conclusion (e002), change tense from 'We introduced' to 'We introduce' to match Abstract.
- **[f5ba4f0b0105]** In Section 3 (e000), add comma after 'skip' in 'When C=skip the agent'.
- **[0010e95ff7fe]** In Section 3 Key Findings (e000), replace informal 'cutting' with 'reducing'.
