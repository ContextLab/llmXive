# Revision Specification: Paper Science Revision — PROJ-654-https-arxiv-org-abs-2605-29707 round 2

**Generated**: 2026-06-23T13:04:10.011021+00:00
**Kind**: paper_science
**Project**: PROJ-654-https-arxiv-org-abs-2605-29707
**Round**: 2

## Input

Address the following reviewer-raised action items:

- **[72877de672f7] (severity: science)** Align Introduction performance numbers (EAGLE-3 3.28x, DFlash 3.42x) with Main Results Table 1 (Qwen3-8B GSM8K: EAGLE-3 2.21x, DFlash 5.21x). Current text claims do not match table data.
- **[82e21bda645c] (severity: writing)** Verify Abstract claim of 'up to 5.8x throughput speedup under SGLang'. Table 2 (high_concurrency.tex) shows max 5.1x (Qwen3-8B GSM8K Concurrency 2). Update abstract or table to match.
- **[bbd3c42aca8f] (severity: writing)** Clarify baseline for '+5.3% parameters' claim in Introduction. Specify whether this is relative to the draft model or target model size to ensure accuracy.
- **[d646fc5c5021] (severity: science)** External code repository (GitHub) is referenced but not accessible for review. Ensure the repo is public, pinned to the exact commit used for experiments, and includes a README with reproduction steps, dependency files (requirements.txt/environment.yml), and test suites.
- **[5fe7aca36d3f] (severity: writing)** Explicitly state the software license for the Domino code and model weights in the repository (e.g., MIT, Apache 2.0) to ensure legal reproducibility.
- **[8e07f629fe70] (severity: writing)** Provide specific version tags or commit hashes for external links (GitHub, Hugging Face) to prevent link rot and ensure exact reproducibility of artifacts.
- **[387f2d1f7c10] (severity: writing)** Clarify the discrepancy between training data in Section 6.1 (mlabonne/open-perfectblend) and Section 6.3 (ShareGPT) to ensure consistent data provenance reporting.
- **[efdd930706e1] (severity: writing)** Expand caption for fig:domino_intro (latex/sec/2introduction.tex, line 23) to explicitly list the benchmarks (GSM8K, code, chat) shown, rather than generic representative math, code, and chat.
- **[ee3f77af772f] (severity: writing)** Remove the commented-out figure block in latex/acl_latex.tex (lines 23-33) which duplicates fig:domino_intro with conflicting caption details.
- **[2ca92e8501c0] (severity: writing)** Ensure fig:draft_overhead (latex/sec/2introduction.tex, line 13) includes explicit axis units (e.g., ms, tokens) and panel labels (a, b) matching the caption's Left/Right description.
- **[cd5eee4175c8] (severity: writing)** Add accessibility metadata (alt text or description) to all includegraphics commands to comply with venue accessibility standards.
- **[7fe6c236d22e] (severity: writing)** Define 'SGLang' on first use (Abstract/Intro) as 'SGLang, a language model serving framework' for non-specialist clarity.
- **[e1eba822ca00] (severity: writing)** Expand 'LM-head' to 'Language Model head' at first occurrence in Introduction or Preliminaries.
- **[8d7865796b40] (severity: writing)** Define 'GRU' as 'Gated Recurrent Unit' and 'SiLU' as 'Sigmoid Linear Unit' upon first mention in Methodology.
- **[36704cdfb471] (severity: writing)** Define 'TPS' (Tokens Per Second) in the caption of Table~\ref{tab:high-concurrency-tps}.
- **[b00b22914ccd] (severity: writing)** Clarify 'T=0' and 'T=1' as 'Temperature' in Section 6.1 Experimental Setup to avoid confusion with time.
- **[baf62d57bb40] (severity: science)** The Abstract claims 'up to 5.8x throughput speedup under SGLang serving,' but Table 'high_concurrency' (latex/table/high_concurrency.tex) reports a maximum of 5.1x (Qwen3-8B GSM8K @ concurrency 2). Verify if 5.8x was achieved on a specific benchmark/concurrency not shown, or correct the Abstract to match the provided data.
- **[4614c0c8736c] (severity: writing)** The Introduction states 'Instead of generating draft tokens sequentially,' but Section 5.1.2 and Figure 1 describe the Domino head as 'sequentially updates a causal state.' This creates a logical tension between the 'parallel drafting' claim and the actual sequential correction mechanism. Clarify that the backbone is parallel while the correction is lightweight and sequential.
- **[9aa6559e8ec8] (severity: writing)** Align abstract claim of 'up to 5.8x throughput speedup under SGLang' with provided Table 2 (high_concurrency.tex), which shows a maximum of 5.1x. Either update the text to match the data or provide the missing benchmark configuration.
- **[ac314d7e05fd] (severity: writing)** Qualify the claim 'Domino consistently outperforms... DFlash' in the Introduction (sec/2introduction.tex), as Table 1 (main_result.tex) shows DFlash outperforming Domino on Qwen3-4B T=1 AIME25 (3.79x vs 3.75x).
- **[f47528804feb] (severity: writing)** Add a dedicated Ethics Statement or Broader Impact section discussing the implications of inference acceleration, including potential dual-use risks (e.g., increased throughput for harmful generation) and environmental costs.
- **[6233f74f62ed] (severity: writing)** Explicitly state the license and usage compliance of the `mlabonne/open-perfectblend` dataset in the Appendix or Experimental Setup to ensure data privacy and consent requirements are met.
- **[edab0ff6d74f] (severity: science)** Clarify training data for baseline models in Table 1. Section 6.1 states Domino uses 'mlabonne/open-perfectblend', but Table 1 baselines use public checkpoints (Table 1 Appendix) likely trained on different data. This confounds architectural gains with data quality.
- **[17474253db23] (severity: science)** Report statistical variance (std dev) for latency and speedup metrics. Inference speed varies by system noise; single-point estimates lack robustness evidence.
- **[4280f8ca4bfa] (severity: science)** Align ablation data with main results. Section 6.3 ablation uses ShareGPT, while main results (Section 6.1) use PerfectBlend. Ensure ablation controls match the main experimental setup to validate claims.
- **[20fc3692ba1b] (severity: science)** Report standard deviations or confidence intervals for all speedup and acceptance length metrics in Tables 1 and 2, particularly for sampling decoding (T=1) where variance is high.
- **[c27c50b6a85f] (severity: science)** Clarify the number of independent runs or random seeds used to generate the reported averages, especially for the sampling decoding experiments in Section 6.2.
- **[90cbed7adad8] (severity: science)** Include statistical significance tests (e.g., paired t-tests or bootstrap confidence intervals) to substantiate claims of 'consistent outperformance' over baselines in Section 6.2.
- **[f1467b7983cf] (severity: writing)** Remove duplicate \usepackage{graphicx} and \usepackage[table]{xcolor} declarations in latex/acl_latex.tex (lines 38, 41, 44, 57) to ensure clean compilation.
- **[daf5a289bfa1] (severity: writing)** Move \label{sec:experiments} in latex/sec/6experiment.tex to immediately follow the \subsection{Experimental Setup} command, not before it.
- **[10c6e0a7d27f] (severity: writing)** Relocate \input{latex/table/high_concurrency} from the Ablation section to the Main Results section in latex/sec/6experiment.tex to match its citation context.
- **[828a59036076] (severity: writing)** Remove redundant \centering inside \begin{table*} in latex/table/main_result.tex and standardize comments to English.
- **[e5af595467e6] (severity: writing)** In latex/sec/2introduction.tex, several sentences exceed 35 words and reduce readability. Consider breaking into 2-3 shorter sentences for clarity.
- **[dd9a8e41fc66] (severity: writing)** In latex/sec/5method.tex, the terminology shifts between draft model, drafter, and draft backbone without clear distinction. Standardize to one term throughout for consistency.
- **[b193b9327a53] (severity: writing)** Figure references in latex/sec/2introduction.tex cite fig:draft_overhead and fig:domino_intro but the corresponding figures have inconsistent labeling conventions. Verify all figure labels match their references.
- **[1ce89b42b1b2] (severity: writing)** In latex/acl_latex.tex, the usepackage{graphicx} command appears twice. Remove the duplicate to avoid compilation warnings.
- **[6029e302246a] (severity: writing)** The abstract includes a centered links block with special color formatting. Consider using standard ACL formatting for links to ensure compatibility with all submission systems.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 37 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
