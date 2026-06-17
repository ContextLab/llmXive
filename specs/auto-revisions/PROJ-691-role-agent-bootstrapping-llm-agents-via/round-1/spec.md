# Revision Specification: Paper Science Revision — PROJ-691-role-agent-bootstrapping-llm-agents-via round 1

**Generated**: 2026-06-17T00:46:38.760422+00:00
**Kind**: paper_science
**Project**: PROJ-691-role-agent-bootstrapping-llm-agents-via
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[9d308455885e] (severity: writing)** Clarify the definition and computation of the Longest Matching Subsequence (LMS) metric used for predictive rewards, including any preprocessing of state texts and handling of ties.
- **[655581be152b] (severity: science)** Provide a more detailed discussion of potential reward hacking where the predictive reward could dominate the task reward, and describe any safeguards implemented.
- **[5435e536b6e0] (severity: writing)** Include quantitative analysis (e.g., ablation of predictive horizon H) in the main paper rather than only in the appendix, to better justify the chosen hyper‑parameter settings.
- **[ab3383a070b1] (severity: writing)** Discuss the limitations of using a single LLM as both agent and environment in multi‑modal or real‑time embodied settings, and outline concrete future work directions.
- **[ca2e28f291fa] (severity: writing)** Verify that all cited references in the bibliography have been checked and marked as verified; add missing citations for any statements that currently lack support.
- **[169c8435e925] (severity: writing)** Add a brief comparison of computational overhead introduced by the predictive reward and AIW components relative to baseline methods, with runtime numbers on a standard hardware configuration.
- **[24465725727a] (severity: writing)** The abstract and main text claim an “average gain of over 4 % over strong baselines.” Table 1 shows a +4.2 % gain over GiGPO for the 1.5 B model, but for the 7 B model the gain over GiGPO is only +3.0 %. Revise this claim to accurately reflect the observed improvements for each backbone size (e.g., specify the gain for each model or report the overall average gain across all experiments).
- **[564c68c90ac6] (severity: writing)** In Table 2 the method “R1‑Instruct” is listed under the “RL Training” category, but R1‑Instruct is a search‑augmented model, not an RL‑trained agent. Either move it to the appropriate category or clarify the categorisation to avoid misleading statements.
- **[040b7cf01725] (severity: writing)** Provide the full source code (training loop, model definitions, data loaders, reward computation, and failure‑mode analysis) in a public repository with a clear directory layout (e.g., src/, scripts/, configs/, tests/).
- **[2e573d099ad5] (severity: writing)** Modularize the implementation: separate the World‑In‑Agent (state prediction) and Agent‑In‑World (failure analysis & retrieval) logic into distinct modules (e.g., wia.py, aiw.py) and expose clean APIs. This improves readability and reuse.
- **[a04d5996a307] (severity: writing)** Add a requirements.txt or environment.yml that pins all Python dependencies (transformers, torch, tcolorbox, etc.) and specify the exact versions used for the experiments.
- **[972a0c900415] (severity: writing)** Include unit tests for each module (e.g., test_wia.py verifying LMS computation and predictive reward scaling; test_aiw.py checking failure‑mode parsing and retrieval query generation). Tests should be runnable with pytest.
- **[dfa7db8b1acf] (severity: writing)** Document the training pipeline with a README that explains how to reproduce each benchmark (ALFWorld, WebShop, search‑augmented QA), including data download commands, hyper‑parameter files, random seed settings, and expected hardware requirements.
- **[bca386ff637e] (severity: writing)** Ensure that all random seeds (numpy, torch, transformers) are fixed and logged in the training script to guarantee deterministic runs where possible.
- **[8814547a27f5] (severity: writing)** Provide a small end‑to‑end script (e.g., run_role_agent.sh) that launches the training from start to finish, invoking the appropriate configuration files. This script should handle logging and checkpoint saving.
- **[bf088af73bab] (severity: writing)** If any custom utilities (e.g., Longest Matching Subsequence, state hashing) are implemented, place them in a utils/ package with docstrings and type hints.
- **[b3d549fbdbeb] (severity: writing)** Add CI configuration (e.g., GitHub Actions) that runs linting (flake8/black) and the test suite on each push to catch regressions.
- **[f09ed2afa34b] (severity: writing)** Add an explicit software license (e.g., MIT, Apache 2.0) to the GitHub repository and cite it in the paper so readers know the reuse terms for the code.
- **[46b96ffed470] (severity: writing)** Provide clear licensing information for all external datasets (ALFWorld, WebShop, NQ, HotpotQA, etc.) and include any required attribution or usage restrictions in the manuscript.
- **[ca3332c19216] (severity: writing)** Specify the exact commit hash or release tag of the code used for experiments (e.g., `git checkout <sha>`), and reference this version in the appendix to improve reproducibility.
- **[9a0cdab0f45a] (severity: writing)** Replace raw URLs (e.g., https://github.com/AMAP-ML/roleagent) with persistent identifiers (DOI via Zenodo or archive.org snapshots) to mitigate link rot.
- **[8afd172ce2dc] (severity: science)** Describe how missing or malformed states during rollouts are handled (e.g., default fallback, error logging) and whether such cases are filtered out before computing rewards.
- **[5cd48b94de14] (severity: writing)** Include a data‑schema description for the failure‑mode records (fields, types, allowed values) and provide a JSON/YAML example in the supplementary material.
- **[39b5e5858eef] (severity: science)** Document any preprocessing steps applied to the benchmark datasets (tokenization, truncation, temperature settings) and explain how they affect dataset integrity.
- **[9b20f1806afb] (severity: writing)** Add a version‑controlled citation for the external benchmarks (e.g., cite the specific arXiv version or dataset release) to avoid ambiguity over which data split was used.
- **[49832a230aac] (severity: writing)** Add explicit axis labels and units to all quantitative plots (e.g., Fig 4 [dyna.pdf] and Fig 7 [eff.pdf]) so readers can understand what is being measured without referring to the caption.
- **[79eb8e5850bc] (severity: writing)** Provide concise alt‑text descriptions for each figure (including schematic diagrams like Fig 1 [main.pdf] and case studies) to improve accessibility and ensure the figures convey their purpose when printed in grayscale.
- **[f9b24cff7242] (severity: writing)** Increase the font size of tick labels and legends in the plots to guarantee legibility at typical conference print scales; current default sizes may become unreadable after scaling.
- **[ff96ac6ea9e3] (severity: writing)** Include a legend or annotate the different curves in Fig 4 [dyna.pdf] (left and right panels) to clarify which line corresponds to Role‑Agent vs. GiGPO, as the caption alone does not identify them.
- **[81737d652537] (severity: writing)** Consider reducing the width of wide figures (e.g., set width to 0.9\linewidth) or splitting multi‑panel figures into separate sub‑figures to avoid overcrowding and improve layout consistency.
- **[f561a566bdd7] (severity: writing)** Replace or explain dense technical terms such as “bootstrapped co‑evolution”, “state‑level advantage”, “trajectory‑level advantage”, and “process reward” with simpler language or add brief parenthetical definitions.
- **[55c5f8a703fb] (severity: writing)** Introduce a short glossary for all domain‑specific acronyms (e.g., ARL, GRPO, GiGPO, WIA, AIW) and ensure each acronym is defined at its first appearance in the manuscript.
- **[24f5f170d7d9] (severity: writing)** Reduce repetitive use of the phrase “LLM agents” by alternating with synonyms like “language‑model agents” or simply “agents” where context is clear.
- **[2fadc4fdd5d9] (severity: writing)** Clarify the meaning of “predictive reward”, “advantage scaling coefficient α”, and “state grouping mechanism” in plain terms, possibly with a one‑sentence lay summary.
- **[91111d120ed6] (severity: writing)** Simplify the description of the “Longest Matching Subsequence (LMS)” metric; consider describing it as a “text similarity score” and avoid the technical abbreviation unless essential.
- **[db76ddf69479] (severity: writing)** In sections describing the experimental setup, replace jargon‑heavy sentences (e.g., “the environment fails to expose the agent's hidden weaknesses”) with more straightforward statements.
- **[22713242e029] (severity: writing)** Add brief, non‑technical explanations for specialized concepts such as “process‑level rewards” and “state‑grouped advantage estimation” to aid readers unfamiliar with reinforcement‑learning terminology.
- **[483eade6ff7e] (severity: writing)** Temper the blanket claim that Role-Agent “consistently outperforms existing approaches” by acknowledging the observed under‑performance on the NQ single‑hop QA benchmark (Table 2) and any other cases where baselines are competitive.
- **[c8daa077163d] (severity: science)** Provide a more rigorous analysis of the predictive reward formulation (multiplicative modulation). Discuss whether this design could still introduce bias or enable reward‑hacking, especially in trajectories with low task reward but high predictive alignment.
- **[7cc23bae108d] (severity: science)** Justify the choice of the state‑similarity threshold (0.9) used for state grouping. Include an ablation or sensitivity study showing the impact of varying this threshold on performance and generalisation across tasks.
- **[6b04f8543271] (severity: writing)** Add a dedicated discussion section on dual‑use and safety implications of using a single LLM as both agent and environment, including potential for uncontrolled self‑evolution and misuse in real‑world or high‑risk domains.
- **[62d3f0915ea6] (severity: writing)** Clarify that all training data (ALFWorld, WebShop, QA datasets) are publicly available and contain no personally identifiable information; explicitly state that no private user data are collected or stored.
- **[c3adbc2a5022] (severity: science)** Provide details on any safeguards or alignment techniques employed to prevent the LLM‑environment component from generating harmful or unsafe actions during training (e.g., content filters, reward shaping limits).
- **[8973cca74c89] (severity: writing)** Discuss the ethical considerations of storing failure‑mode reflections and trajectories, ensuring they cannot be reverse‑engineered to expose sensitive environment details or proprietary information.
- **[d346eb0b64f4] (severity: writing)** If the framework were to be extended to multimodal or embodied settings, include a brief risk assessment outlining required safety evaluations (e.g., IRB/IACUC, simulation‑to‑real transfer safety checks).
- **[956b7af51615] (severity: science)** Report the number of evaluation episodes per benchmark (e.g., ALFWorld, WebShop) and provide confidence intervals or statistical significance tests for the reported gains (Table 1, Table 2).
- **[58d441f6c1a4] (severity: science)** Increase the number of independent runs (beyond three) for the main experiments to reduce variance and strengthen reproducibility claims (see Table 3 and Table 4).
- **[9d9980f014ec] (severity: science)** Clarify how the predictive reward horizon H was selected and provide an analysis to rule out reward‑hacking or over‑fitting to the LMS metric (see Section 3.1 and sensitivity analysis Table 5).
- **[8c7457b1e98f] (severity: writing)** Include a discussion of potential bias introduced by using the same LLM for both agent and environment roles, especially regarding the fairness of comparisons with baselines that use frozen backbones (see Limitations §6).
- **[27ef6139b4a3] (severity: science)** Provide statistical significance testing (e.g., paired t‑tests or bootstrap confidence intervals) for the reported improvements over baselines in Tables 1‑4, and report corresponding p‑values or confidence intervals.
- **[14aaa9595f13] (severity: science)** Address the multiple‑comparisons problem arising from evaluating many task categories (Pick, Look, Clean, etc.) by applying a correction method (e.g., Bonferroni or Holm) or clearly stating that each metric is considered independently.
- **[eb9faa496a4f] (severity: writing)** Include a more detailed description of the random seed handling and the exact number of runs for each experiment; the current statement of “three runs” (Table 9) should be accompanied by variance estimates and reproducibility instructions.
- **[6e14d05d4d17] (severity: science)** Report effect sizes (e.g., Cohen’s d) for key comparisons such as Role‑Agent vs. GiGPO to quantify the practical magnitude of gains beyond raw percentages.
- **[ce710aee326d] (severity: science)** Clarify the computation of the predictive reward correlation (point‑biserial r = 0.41) by providing the sample size, confidence interval, and a hypothesis test to assess whether this relationship is statistically robust.
- **[41d1a89e9105] (severity: writing)** Remove duplicate package imports (e.g., \usepackage{listings} appears twice in acl_latex.tex lines 23‑24) to avoid redundancy.
- **[f43216b7ef57] (severity: writing)** Eliminate unnecessary \vspace commands inside the itemize environment (see lines 94‑96) which can cause inconsistent spacing.
- **[e500834af4d6] (severity: writing)** Standardize figure captions: avoid embedding \textcolor{black}{\textbf{...}} inside \caption (e.g., Figure 1 caption lines 61‑64) and place the caption directly after \includegraphics.
- **[57fbba4a1cc6] (severity: writing)** Ensure consistent heading hierarchy: the "Related Work" section uses \paragraph{} for sub‑headings, but later sections use \subsection{}. Convert all sub‑sections to \subsection{} for uniformity.
- **[75eadc1aadd8] (severity: writing)** Replace manual line‑breaks (\\) in the author block with proper \author formatting to improve readability and avoid excessive vertical spacing.
- **[2edb33411ed9] (severity: writing)** In tables, avoid using both \resizebox and \setlength\tabcolsep together; choose one method to control column width (see Table 1 lines 210‑225).
- **[d256a2af09b3] (severity: writing)** The abstract (lines 1‑5) contains a run‑on sentence and inconsistent use of commas. Rewrite to separate the description of WIA and AIW into two concise sentences.
- **[552c095950e7] (severity: writing)** In the Introduction (lines 10‑15), the phrase “critical and have therefore been widely explored” is awkward; replace with a clearer construction such as “which are critical and thus widely explored.”
- **[8b4a06efd173] (severity: writing)** Figure 1 caption (lines 28‑30) mixes bold and plain text inconsistently and includes unnecessary line‑break commands; simplify the caption and ensure consistent formatting.
- **[e556bada3039] (severity: writing)** Throughout the Methodology section (lines 45‑55), there are several overly long mathematical sentences that hinder readability (e.g., the definition of 𝑅𝑡). Break them into shorter statements and add punctuation where needed.
- **[09a0c23e0e73] (severity: writing)** The use of ‘	extcolor{black}{…}’ to force black text appears repeatedly (e.g., lines 22, 34, 47). Remove these commands unless they serve a specific purpose.
- **[ca1af3422c7b] (severity: writing)** The tables (e.g., Table 1 starting at line 70) suffer from cramped column headings and inconsistent capitalization (“Pick” vs. “pick”). Standardize heading style and add spacing for readability.
- **[c029b5c0b2de] (severity: writing)** The “Limitations” section (lines 120‑124) contains a dangling comma after “multi‑modal or real‑time embodied settings may require vision‑language state descriptions or latent‑state matching and remain important future work.” Rewrite for grammatical completeness.
- **[fd37cff91915] (severity: writing)** Several instances of redundant wording appear, such as “bootstrapped co‑evolution” and “bootstrapped agent‑environment co‑evolution” (lines 8‑9, 55‑56). Choose one term and use it consistently.
- **[fa6d609c3531] (severity: writing)** In the Appendix (lines 150‑155), the bullet list mixes punctuation styles (some items end with periods, others do not). Adopt a uniform style.
- **[28c0cb0d9777] (severity: writing)** The algorithm block (Algorithm 1, lines 180‑210) uses inconsistent notation (e.g., sometimes πθ, other times π_θ). Standardize variable notation throughout.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 70 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
