# Revision Specification: Paper Science Revision — PROJ-579-https-arxiv-org-abs-2605-15155 round 1

**Generated**: 2026-06-29T02:44:56.493904+00:00
**Kind**: paper_science
**Project**: PROJ-579-https-arxiv-org-abs-2605-15155
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[c6cef9aba447] (severity: science)** Theoretical analysis appendix contains only placeholder comment '% (Proofs retained in full in the appendix.)' without actual proofs. Claim of theoretical support is unsupported.
- **[9d11e0fc7d46] (severity: writing)** Multiple citations have 2026 publication dates (e.g., zhao2026opsd, yang2026rlsd, he2026sdzero). Verify these are not future-dated errors or provide justification.
- **[b8e3980a1cdf] (severity: science)** Performance gain claims (+9.4% ALFWorld, +7.0% Search-QA, +4.7% WebShop) reference baseline values not visible in Table 1 (30 rows omitted). Verify numerical accuracy.
- **[42e7a913293c] (severity: science)** Claim 'OPSD alone collapses (near-zero on Search-QA)' cannot be verified as OPSD row is omitted from Table 1. Include or cite specific evidence.
- **[01214e0c571f] (severity: writing)** Citation '\citep{ye2025mobileagentv3,}' has trailing comma syntax error that will break compilation.
- **[0703a023e60e] (severity: science)** Implementation code artifacts are not provided in the submission. Reproducibility cannot be verified without access to the training/inference scripts.
- **[ce702f410a46] (severity: writing)** GitHub URL in text contains a typo (SDAR}) preventing direct access. Correct to SDAR.
- **[d0ce5e281b0a] (severity: writing)** Specify exact dataset versions (commit hashes or release tags) for ALFWorld, WebShop, and Search-QA to ensure reproducibility.
- **[fc262ca0eaf9] (severity: writing)** Document the schema, file format, and license for the derived 'SkillBank' dataset referenced in Implementation Details.
- **[82572404cb9a] (severity: writing)** Correct the GitHub repository link (remove trailing brace) to prevent link rot and ensure code/data access.
- **[cd02bb0830d5] (severity: writing)** Add a section describing missing-data handling (e.g., failed search queries) in the training pipeline.
- **[f6140e4f9987] (severity: writing)** Expand captions for ablation figures (fig:ablation_tip, fig:ablation_beta, fig:ablation_lambda, fig:ablation_loss) to explicitly state the y-axis metric (e.g., Success Rate %) and x-axis variable.
- **[ba5ac433febe] (severity: writing)** Verify that fig:7b_alfworld_gap_gate contains labeled subplots (a) and (b) as referenced in the text, or update the caption to reflect the single-image structure.
- **[d9827dbd0efa] (severity: writing)** Ensure prompt template figures (fig:prompt_alfworld, etc.) use legible font sizes for print; consider reducing text density or increasing figure height.
- **[c5cb47bf3772] (severity: writing)** Add alt text descriptions to all figure environments for accessibility compliance.
- **[bb0a8f908216] (severity: writing)** Define the acronym GRPO at its first occurrence (e.g., in the Baselines paragraph of the Experiment section).
- **[77ce4558b44b] (severity: writing)** Define the acronym RLSD when it first appears (e.g., in the Baselines list).
- **[8c596f94ddfb] (severity: writing)** Introduce the term LLM (large language model) and RL (reinforcement learning) with brief definitions before using the acronyms.
- **[dcbb96b0eff6] (severity: writing)** Explain “privileged context” the first time it is mentioned in the Related Work section; readers unfamiliar with the concept may be confused.
- **[a488e8a05ecf] (severity: writing)** Replace or clarify technical jargon such as “mode‑seeking advantage”, “unbiased RL”, and “auxiliary signal” with simpler language or brief explanations.
- **[5d153230f7d6] (severity: writing)** Provide a short description of KL (Kullback‑Leibler) divergence when referring to Reverse KL, Forward KL, and Jensen–Shannon losses.
- **[9d51d36357b2] (severity: writing)** Clarify the meaning of “OPSD signal” when it first appears in Section 3.2; a one‑sentence definition would aid non‑specialist readers.
- **[b55263603e81] (severity: writing)** Consider adding a glossary of abbreviations (e.g., OPSD, GRPO, RLSD, Skill‑GRPO, Skill‑SD) at the end of the paper for quick reference.
- **[129c2c3e49c6] (severity: science)** Provide the theoretical analysis in Appendix~\ref{appendix:proof} as claimed in the text.
- **[c6f302a6b56c] (severity: science)** Clarify the gradient flow in the loss definition to ensure teacher log-probs are detached.
- **[cd8591ea7586] (severity: writing)** Include omitted table rows for key baselines (OPSD, GRPO) to verify numerical claims.
- **[a8b09b9fc125] (severity: science)** Theoretical analysis is claimed in Section 'Token-Level Gating' but Appendix contains only a placeholder comment. Provide actual proofs.
- **[d89f8597ff1f] (severity: writing)** Claim that OPSD 'collapses (near-zero)' lacks supporting data in Table 1 (rows omitted). Include full baseline results.
- **[5e1fcc3743f4] (severity: writing)** Conclusion overstates generalization without discussing limitations (e.g., SkillBank dependency, compute cost). Add limitations subsection.
- **[0d1ecb4be3f4] (severity: writing)** Add a dedicated safety and ethics discussion addressing dual-use risks of autonomous agents trained with this method (e.g., automated purchasing, information gathering, reconnaissance).
- **[f1df73315f04] (severity: writing)** Include discussion of potential misuse scenarios and recommended guardrails for deployment of trained agents in real-world environments.
- **[6153d8e245b7] (severity: writing)** Add societal impact statement discussing how improved agentic capabilities could affect users, markets, and information ecosystems.
- **[48415507a69c] (severity: science)** Report standard deviations or confidence intervals for all main results in Table 1 and Table 3. RL training is stochastic; point estimates alone are insufficient to claim statistical significance.
- **[f94eb0689b54] (severity: science)** Specify the number of random seeds used for training and evaluation in the 'Implementation Details' section. Current text does not mention seed count.
- **[8db8b7fcd5c9] (severity: science)** Clarify the '150 steps' training duration mentioned in 'Implementation Details'. Is this total steps, per epoch, or per task? This is unusually low for RL and requires justification.
- **[727fb9bde7ce] (severity: science)** Confirm that hyperparameter tuning (e.g., beta=5, lambda=0.01) was performed on a validation set, not the test set, to avoid data leakage.
- **[574822eca40b] (severity: science)** Report standard deviations or confidence intervals for all main results in Table 1. RL experiments are high-variance; point estimates are insufficient.
- **[72574f6fee18] (severity: science)** Conduct statistical significance tests (e.g., paired t-test or bootstrap) for all reported improvements over baselines (e.g., +9.4% on ALFWorld).
- **[05fdf0d7ff51] (severity: science)** Explicitly state the number of random seeds used for each experiment. Current text implies single runs or unreported aggregation.
- **[0658b3377da6] (severity: science)** Address multiple comparisons correction given the 15+ sub-tasks across ALFWorld, Search-QA, and WebShop to avoid inflated Type I error.
- **[dac6993433ee] (severity: writing)** Remove or comment out all stray section markers such as `e000`, `e001`, `e002`, and any isolated `}` characters that appear outside of LaTeX environments (e.g., the stray brace after the bibliography). These cause compilation errors.
- **[5b8ba0b7754d] (severity: writing)** Define the custom column type `C` used in the large tables (e.g., via `
ewcolumntype{C}{>{\centeringrraybackslash}p{...}}`) or replace it with a standard column specifier (`c`).
- **[e2b993f25386] (severity: writing)** Add the required packages for table styling (`booktabs`, `colortbl`, `xcolor`, `array`) and for figure placement (`float` if `[H]` is desired). Ensure they are loaded in the preamble.
- **[d7146121d439] (severity: writing)** Place `\label{...}` commands *after* the corresponding `\caption{...}` inside figures and tables to guarantee proper cross‑referencing.
- **[e57e25115fff] (severity: writing)** Replace the `[h]` float specifiers with more robust options such as `[htbp]` or use the `float` package’s `[H]` if strict placement is required.
- **[61bf63751404] (severity: writing)** Check line wrapping in the source; very long lines (e.g., the bibliography entries) should be broken at logical points to improve readability and avoid overfull hbox warnings.
- **[84d79ceda5d0] (severity: writing)** Ensure consistent heading hierarchy: all `\subsection` commands appear under a `\section`, and `\subsubsection` (if any) are nested correctly. Verify that the `ppendix` command is followed by `\section` headings for each appendix.
- **[585934aeeb94] (severity: writing)** Remove row placeholders (e.g., “... 30 rows omitted ...”) from Table 1 and Table 2; ensure all data rows are present in the final manuscript.
- **[e3904a71675e] (severity: writing)** Fix the Appendix reference in the “Main Results” section so that it points to the correct label (change \ref{appendix:proof} to \ref{appendix:algorithm}).
- **[8106c51d99b2] (severity: writing)** Standardize spelling (e.g., “destabilises” vs. “stabilizes”) and hyphenation/en‑dash usage (e.g., “Search‑QA” vs. “Search‑QA”) throughout the paper.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 50 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
