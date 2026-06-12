# Revision Specification: Paper Science Revision — PROJ-607-https-arxiv-org-abs-2605-19769 round 1

**Generated**: 2026-06-12T11:37:07.629589+00:00
**Kind**: paper_science
**Project**: PROJ-607-https-arxiv-org-abs-2605-19769
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[87fd1a7ee664] (severity: science)** Code repository (verifiers, generators, tests) not included in input. Cannot verify modularity, test coverage, or dependency hygiene.
- **[75cdc0b6687e] (severity: writing)** Add an explicit license declaration for the benchmark dataset and verifier code in the main text or repository README.
- **[08afd595343f] (severity: writing)** Clarify the provenance and licensing of seed files (e.g., piano_sketch.mscz) in the methodology section to ensure redistribution rights.
- **[688b895a9756] (severity: writing)** Include a version tag or commit hash for the released repository to ensure reproducibility and link stability.
- **[71fd509295fe] (severity: writing)** Increase font size in figure/compare_with_llm_as_judge.tex TikZ plot from 7.5pt to at least 9pt to ensure legibility at standard conference print scales.
- **[668509dd01a7] (severity: writing)** Add visual annotations (e.g., arrows or boxes) to image/llm_as_judge_error_1.png to explicitly highlight the cell boundary error, as the caption notes the visual difference is subtle.
- **[65a091541bcd] (severity: writing)** Verify color contrast in figure/compare_with_llm_as_judge.tex for grayscale printing; the black!45 judge bar may be too light compared to the teal verifier bar.
- **[47eb9c99cfda] (severity: writing)** Define all major acronyms at first use: LLM (large language model), CLI (command-line interface), GUI (graphical user interface), API (application programming interface), RL (reinforcement learning), SFT (supervised fine-tuning), JSON (JavaScript Object Notation). These appear throughout without definition.
- **[6bb2d7af13e5] (severity: writing)** Replace jargon-heavy phrases: verifier-grounded framework to framework using programmatic verification, execution-grounded feedback to feedback from actual task execution, calibration executions to test runs, trajectory to sequence of actions.
- **[cbe8c0e59c07] (severity: writing)** Simplify Section 2 Problem Setup mathematical notation. The formal notation tau equals x comma e comma c, s zero tilde e, etc. excludes non-specialist readers without adding clarity.
- **[c268407477f3] (severity: writing)** Define verifier clearly at first use. The term appears approximately 100 times but no explicit definition exists for what a verifier is a program that checks task completion.
- **[d74401762008] (severity: writing)** Replace frontier agents with state-of-the-art agents and partial-credit rewards with partial scores for accessibility.
- **[e85759b7070a] (severity: writing)** Temper the claim in the Abstract and Experiment section that model performance drops expose a 'persistent gap in robust computer automation.' This conflates metric strictness with capability; clarify that stricter verification naturally lowers pass rates compared to looser benchmarks.
- **[aab4cf1d0d16] (severity: writing)** Qualify the Conclusion's claim that the framework preserves 'the diversity and realism of real software workflows.' Acknowledge that visually-grounded workflows (excluded per Appendix/limitations.tex) are part of realistic workflows but omitted for verifiability.
- **[5f9d6f09067a] (severity: writing)** Add explicit IRB approval statement or ethics exemption regarding human annotators mentioned in Section 4.1, including consent and compensation details.
- **[f44c77594806] (severity: writing)** Include a Dual-Use and Responsible Release discussion addressing potential misuse of the agent framework for unauthorized automation or malicious tasks.
- **[fd8d8b6a3407] (severity: writing)** Explicitly confirm that all benchmark data (e.g., zotero.sqlite, commissions.xlsx) is synthetically generated and contains no real user PII in the Data Availability or Limitations section.
- **[0682a0db6707] (severity: science)** Report standard deviations or confidence intervals for success rates in Table 1 (figure/benchmark_result.tex) to account for LLM stochasticity.
- **[7a30b712e88b] (severity: science)** Clarify the number of random seeds used per task in the evaluation harness (Section 4.1) to ensure result reproducibility.
- **[0023a4fb0466] (severity: science)** Perform statistical significance testing (e.g., McNemar's test) for the LLM Judge vs. Verifier human alignment results (Section 4.1).
- **[c745092b0d3b] (severity: science)** Analyze the distribution of the 17 excluded tasks (Appendix/limitations.tex) to assess potential selection bias in the benchmark.
- **[b33ab4c5ba7c] (severity: science)** Add standard deviations or 95% confidence intervals to Table 1 (figure/benchmark_result.tex) for all reported metrics (Success Rate, Avg Reward, Steps, Time).
- **[1742891b1115] (severity: science)** Report variance or multiple-seed results for the CLI vs. GUI timing comparison in Section 4.2 (figure/gui_and_cli.tex) to validate efficiency claims.
- **[d9e0114d110a] (severity: science)** Perform significance testing (e.g., McNemar's test) on the human alignment study (Section 4.1) and ablation results (Section 4.3) to support claims of improvement.
- **[c5f0c0fe1854] (severity: writing)** Remove duplicate color definitions in commands.tex to avoid LaTeX redefinition warnings.
- **[c2f20bffc0dd] (severity: writing)** Consolidate package imports: eliminate redundant subcaption and wrapfig statements.
- **[9c580c12ba1f] (severity: writing)** Standardize figure environments for all floating figures.
- **[fdd649d52346] (severity: writing)** Ensure every caption appears before its corresponding label in all floats.
- **[268f8c078828] (severity: writing)** Check heading hierarchy: all top-level sections use section, subsections use subsection.
- **[81cf061f069b] (severity: writing)** Remove unused macro definitions or replace their usage with standard LaTeX commands.
- **[3b918459c7d5] (severity: writing)** Verify that all cross-references resolve correctly.
- **[158e79d3c77f] (severity: writing)** Align table column specifications with content width consistently.
- **[997aed28ba50] (severity: writing)** Add a newline after begin document before title to improve readability.
- **[a8e57f0bd39b] (severity: writing)** Consider moving the thispagestyle fancy block after maketitle.
- **[ee2fd63673cb] (severity: writing)** In sections/methodology.tex, correct subject-verb agreement: 'The agent treat verifiers' to 'treats', 'the agent implement query endpoints' to 'implements', and 'the agent generate rich synthetic artifacts' to 'generates'.
- **[05e69c513a23] (severity: writing)** In sections/introduction.tex, fix parallelism in paragraph 2: change 'and ensures' to 'ensure' to match 'design' and 'prepare'.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 36 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
