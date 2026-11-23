# Revision Specification: Paper Science Revision — PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin round 1

**Generated**: 2026-06-28T18:08:59.336302+00:00
**Kind**: paper_science
**Project**: PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[a59824046e09] (severity: science)** Code repository link lacks commit hash/version pinning. Add specific git commit SHA to ensure reproducibility of the exact benchmark version used in experiments.
- **[17ee64b7f58f] (severity: science)** Appendix D describes harness implementations but provides no test coverage metrics. Add unit/integration test counts and coverage percentages for the adapter protocol and each claw.
- **[a8e8a32234e7] (severity: science)** Dependency specifications (UV, Docker images) need exact version pinning. Include requirements.txt, pyproject.toml, or Dockerfile with pinned versions for full reproducibility from scratch.
- **[64843692b793] (severity: science)** Benchmark construction algorithm (Sec 4.2) describes objective function but omits exact coefficient values (cost_alpha, RANK_EPS, lambda). Add these to appendix for reproducibility.
- **[00dfe0aa002d] (severity: writing)** Explicitly state the license of the Claw-SWE-Bench artifact (e.g., MIT) in Appendix I, not just upstream licenses.
- **[9a2d9966df38] (severity: writing)** Add a version tag or commit hash for the code/data release to ensure reproducibility and prevent link rot.
- **[1653b1012d40] (severity: writing)** Document the schema of the benchmark instances (JSON fields) or reference the exact SWE-bench schema version used.
- **[0c3ad5a87a73] (severity: writing)** Reference the specific script or method used for 'Future-commit history is removed' cleaning step in Section 2.3.
- **[b40bb41df8dd] (severity: writing)** Standardize figure file naming convention (e.g., fig_01_pareto.pdf, fig_02_framework.pdf) instead of mixed F1_, C_figure3, F2a_ patterns.
- **[524afb407006] (severity: writing)** Replace PNG figures (C_figure3.png, F_leak_fix_openclaw_multilingual.png) with vector PDFs for print scalability and sharpness.
- **[eab23690664a] (severity: writing)** Add descriptive sub-captions to Figure 3 (fig:dist) panels instead of generic '(a) Per-language parity' labels.
- **[d98474fb59dd] (severity: writing)** Move Figure 1 (pareto_frontier) from Introduction to Results section for better narrative flow.
- **[21891dbd99ab] (severity: writing)** Include accessibility alt-text for all figures using the caption package or arXiv-compliant metadata.
- **[ef9abe9a957a] (severity: writing)** Define 'claw' as 'agent harness' at first use; currently used as internal jargon for frameworks like OpenClaw.
- **[6807fe6cc7a3] (severity: writing)** Define 'pp' as 'percentage points' before using in Abstract and Section 5.
- **[f77d664e1e83] (severity: writing)** Replace 'leak-fix' with 'future-commit cleanup' or define the term explicitly.
- **[8e456c235abd] (severity: writing)** The paper demonstrates strong internal consistency in numerical claims (e.g., 29.4 pp model spread, 27.4 pp claw spread, Lite-80 0.4 pp deviation all match tables). However, several logical gaps weaken causal conclusions: Adapter Diagnostic (Section 5.1): The 19.1%→73.4% improvement is attributed to 'adapter importance,' but Table 1 shows the change involves fundamental patch extraction methodology (direct diff vs. file-edit based). This conflates harness capability with patch extraction mechani
- **[e8235e5349f9] (severity: science)** Clarify whether the adapter is part of the harness or a separate component. The 'bare adapter' vs. 'full adapter' comparison conflates adapter design with harness implementation, overreaching the claim that the adapter alone enables SWE-bench compliance.
- **[ffb0c570aef4] (severity: science)** Validate Lite-80 rankings against full-350 rankings across a wider set of models/claws. The current validation (5-claw × 2-model grid) is insufficient to support the claim that Lite-80 is suitable for 'preliminary model or claw comparisons'.
- **[83fa06f49e73] (severity: writing)** Softening the claim that 'cost-aware Pareto analysis is essential' to 'recommended' or providing evidence that non-Pareto analysis leads to incorrect conclusions. The current claim overreaches the evidence.
- **[83982cbee704] (severity: writing)** Clarify the specific criteria used to exclude security-sensitive issues from the 350-instance benchmark, as claimed in Appendix I. Upstream SWE-bench datasets have historically contained security-related bugs.
- **[226de5d1c64c] (severity: writing)** Add a statement regarding the scrubbing of Personally Identifiable Information (PII) from GitHub issue discussions included in the benchmark dataset.
- **[f57d366d7611] (severity: writing)** Include a Conflict of Interest statement regarding the evaluation of models from companies where authors may have affiliations (e.g., TokenRhythm, Infinigence AI).
- **[333f12222651] (severity: science)** Detail the security measures ensuring Docker containers cannot escape to the host system during agent execution, given the exec tool access granted to agents.
- **[8c0597d9b364] (severity: science)** Report variance (std dev) or confidence intervals for Pass@1 metrics in Tables A2 and B to validate significance of reported differences.
- **[91cef7418417] (severity: science)** Clarify confounding between harness architecture and tool permissions in the claw sweep (Appendix D) to isolate the 'harness' variable.
- **[1af4d61643db] (severity: science)** Add 95% confidence intervals (e.g., Wilson score) to all Pass@1 tables (Table 1, Table 2, Appendix tables).
- **[7c8ad277c314] (severity: science)** Discuss multiple-comparison correction for the 9-model sweep in Section 5.2 to control Type I error.
- **[bec950d41588] (severity: science)** Address single-run variance limitation in Section 7; provide bootstrap estimates or acknowledge conflation of stochasticity.
- **[9e94dd764a37] (severity: science)** Discuss repository-level clustering effects (43 repos) in Section 3.1 assumptions.
- **[b69a96a620bd] (severity: writing)** Abstract uses markdown-style bold (**text**) instead of LaTeX \textbf{} which will cause compilation errors. Replace all **350**, **8**, **43**, **19.1 %**, **73.4 %**, etc. with \textbf{350}, \textbf{8}, \textbf{43}, \textbf{19.1 %}, \textbf{73.4 %}.
- **[b4446b20f250] (severity: writing)** Figure 1 in Introduction (e000) uses \captionof inside a center environment instead of a proper figure environment. Standardize to \begin{figure}...\caption{}...\end{figure} for consistency with other figures in Results section.
- **[4e460389e717] (severity: writing)** Inconsistent caption usage: Introduction uses \captionof while Results section uses \caption within figure environments. Choose one approach and apply consistently across all figures.
- **[79a3e6943a76] (severity: writing)** The abstract effectively summarizes the benchmark's purpose and key results.
- **[e670c4f43fd5] (severity: writing)** Section structure is logical, moving from problem statement to methodology to results.
- **[a07ca6dc8029] (severity: writing)** Most technical descriptions are precise and well-organized. Areas for Improvement:
- **[226fd0ca267b] (severity: writing)** Terminology Definition: The term "claw" is used throughout (e.g., "5 claws × 2 models") without a clear early definition. Readers unfamiliar with the project may be confused. Define "claw = harness" in the Introduction or add a brief glossary.
- **[e8b6452643ed] (severity: writing)** Formatting Consistency: Numerical values use bold formatting inconsistently. Some are bolded (350, 80) while others are not (350, 80). Apply bold only for key results to avoid visual clutter.
- **[6ab2d359c285] (severity: writing)** Figure Captions: Figure captions vary significantly in length. Fig. 1 caption is 3 lines; Fig. 2 caption is 1 line. Standardize to 1–2 sentences for better readability and consistency.
- **[cc104403d2d4] (severity: writing)** Redundancy: Section 3.2 (Lite‑80 Construction Detail) repeats content from Section 3.1. Consolidate these sections to avoid redundancy and improve flow.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 40 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
