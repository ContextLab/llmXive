---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/272
paper_authors:
  - Xingrun Xing
  - Haoqing Wang
  - Boyan Gao
  - Ziheng Li
  - Yehui Tang
---

# Trust Region On-Policy Distillation

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.01249
Paper authors (from arXiv): Xingrun Xing, Haoqing Wang, Boyan Gao, Ziheng Li, Yehui Tang

Submitted by: github-actions[bot]

(Intake from human-submission issue #272.)

## Rejection rationale (2026-06-10)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[285200b47aa8]** Add verification_status field to all bibliography entries in state/citations/PROJ-659-trust-region-on-policy-distillation.yaml; many citations show future dates (2025-2026) requiring verification.
- **[f3b4dc4a1b78]** Provide compiled figures (f1-1.pdf, f2.pdf, actor_entropy_comparison.pdf, actor_grad_norm_comparison.pdf) in projects/PROJ-659-trust-region-on-policy-distillation/paper/figures/ for reproducibility.
- **[4727d9b04bf3]** Verify LaTeX compiles without errors and proofreader_flags.yaml is empty before final submission.
- **[00d24f87eed9]** Add missing bibliography entries for all cited keys (e.g., ko2026scaling, lu2025onpolicy, wang2026mix) to custom.bib or colm2026_conference.bib to support factual claims.
- **[d1cb5962b1c6]** Verify that every \cite{} command in main.tex has a corresponding entry in the provided bibliography files.
- **[78f25c63759f]** Code repository is referenced (GitHub) but no implementation artifacts are provided. For code quality review, the full source code, dependency specifications (requirements.txt/pyproject.toml), test suite, and reproducibility scripts must be included in the submission.
- **[45d7b4f7714c]** No training scripts, model checkpoints, or evaluation code are accessible. Add a CODE_OF_CONDUCT or REPRODUCIBILITY.md file documenting how to reproduce experiments from scratch.
- **[20cf64c7dd6b]** The paper claims memory-efficient implementations (O(n) vs O(nk)) but provides no benchmarking code or profiling results. Include performance measurement scripts to validate complexity claims.
- **[6ec7eada3936]** Critical dataset citations (e.g., OpenThoughts3, Skywork-OR1, LiveCodeBench) are missing from the provided bibliography. Ensure all data sources have complete bib entries with URLs/DOIs for provenance.
- **[c24b91f0017f]** No license information is provided for any of the datasets or models used (Qwen3, DeepSeek, Skywork). Add license details to ensure compliance and reproducibility.
- **[cb1a162c22c9]** Dataset versions are vague (e.g., 'OpenThoughts3'). Specify exact release versions, commit hashes, or HuggingFace dataset IDs to prevent link rot and ensure reproducibility.
- **[b81db47e7c3d]** Appendix mentions data filtering ('Entries without messages field removed') but lacks a formal schema definition. Include a data schema or data card in the Appendix.
- **[24966d7db3c2]** Define the '$K_1$ estimator' explicitly upon first use (Abstract, line 12) or provide a one-sentence mathematical intuition for non-specialists.
- **[2601025345c5]** Replace 'teacher of generations (ToGs)' and 'student of generations (SoGs)' with plain English (e.g., 'teacher-generated trajectories') in Section 3.1 (line 135).
- **[8457bea6e6cb]** Expand all benchmark acronyms (AIME, AMC, GPQA, LiveCodeBench) at first mention in Section 5 (line 250+) to clarify their domains.
- **[fc454a8733a3]** Replace 'SoTA' with 'state-of-the-art' in the Abstract (line 15) and Related Works (line 90) for formal consistency.
- **[99068159efb4]** Section 3.2 claims FKL KL(πT||πS) → 0 when student probability approaches 0 on teacher top-k tokens. This is mathematically incorrect—FKL would explode to infinity, not approach 0. This fundamental error undermines the outlier estimation mechanism.
- **[b04b1effbf4c]** Section 3.3 defines off-policy guidance as forward KL but Equation 10 shows β log(πT/πS), which is reverse KL form. The mathematical formulation contradicts the stated mechanism.
- **[3714806554d0]** The trust region definition (Eq. 6) creates circular logic: we only train where teacher agrees with student, but the goal is to improve student capability. This avoids rather than addresses the distribution mismatch problem stated in the Introduction.
- **[6645e665d86b]** Table 2 claims Off-Policy Guidance has O(n) memory with forward KL, but forward KL typically requires full vocabulary support. Memory complexity claim needs justification or correction.
- **[4e1c30a34b8c]** Introduction claims specific improvements (+3.34, +4.00, +5.11, +6.18 points) that do not match any single table. Table t1 shows +3.06 avg gain, Table main shows +3.44, Table tab:opd_results shows +3.52. These discrepancies overstate precision and must be clarified or corrected.
- **[7a3a5d4b47f6]** Claims of "unified training settings" are contradicted by varying teacher models (Skywork-OR1-Math-7B vs Qwen3-Nemotron-4B) across experiments. This overstates benchmark consistency and limits comparability claims.
- **[8bc6954be022]** The adaptive trust region definition using min(π_T(x)/π_S(x), 1) is essentially speculative decoding acceptance probability, a well-established concept. The paper does not sufficiently acknowledge this prior work, overclaiming novelty.
- **[b39f45b1b805]** Abstract claims TrOPD works "across mathematical reasoning, code generation, and general-domain benchmarks" but code results are limited to only LiveCodeBench v6 with sparse reporting. This overstates generalization evidence.
- **[abb4b1341824]** Performance attribution to TrOPD alone is incomplete. Table tab:aopd_comparison shows TrOPD + AOPD outperforms TrOPD alone (41.67 vs 40.63), suggesting gains may stem from multiple factors. The paper does not adequately disentangle these contributions.
- **[dbb6d826f796]** Add a dedicated subsection in the Limitations or Conclusion discussing dual-use risks, specifically regarding code generation and automated agent capabilities described in the Abstract and Section 1.
- **[bd3d7aea4327]** Include a statement confirming compliance with the licenses of teacher models (e.g., DeepSeek-R1, Skywork-OR1) used for distillation, as referenced in Table 1 and Table 2.
- **[13b1cd7c362a]** Discuss the potential for safety degradation when improving reasoning capabilities without explicit safety alignment, as benchmarks focus solely on capability (Table 1, Table 2).
- **[9da7ea587bed]** Add standard deviations or confidence intervals to all performance tables (e.g., Table 1, Table 2) to establish statistical significance of reported gains.
- **[2414c1bd71dd]** Provide convergence curves or justify the 200-step training limit in Section 'Benchmark Training' to ensure results reflect stable performance rather than transient speed.
- **[6943196ba9f8]** Clarify whether baseline methods (e.g., REOPOLD) used tuned hyperparameters (e.g., clipping thresholds) or fixed defaults to ensure fair comparison.
- **[9d40e75b6275]** Report training variance across multiple random seeds (N>=3) for all main results. Current '32 times evaluation' refers to inference sampling, not training stability, undermining claims of consistent improvement.
- **[60e37e7a1a16]** Include standard deviations or 95% confidence intervals in Tables t1, tab:opd_results, and main. Point estimates alone do not support statistical significance of reported gains (e.g., +3.06 points).
- **[e32f434ff565]** Justify the fixed learning rate (5e-6) and step count (200) for all baselines. Uniform hyperparameters may introduce optimization bias against methods requiring different tuning schedules.
- **[85be5a3a7d05]** Standardize figure/table label naming conventions (e.g., use 'fig:*' and 'tab:*' consistently instead of mixing 'f1'/'t1' with 'main').
- **[627189dfb2d2]** Unify cross-reference text capitalization (use 'Fig.' or 'Figure' consistently throughout the manuscript).
- **[22bb550c644d]** Verify bibliography completeness; the provided custom.bib snippet appears truncated and may miss cited entries (e.g., open_science_reasoning_2_2025).
- **[3cc5fb0dde08]** Avoid \resizebox for tables; use \small or adjust column widths to preserve font consistency and accessibility.
