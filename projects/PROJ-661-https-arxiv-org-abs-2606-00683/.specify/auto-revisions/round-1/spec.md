# Revision Specification: Paper Science Revision — PROJ-661-https-arxiv-org-abs-2606-00683 round 1

**Generated**: 2026-06-16T10:20:01.448823+00:00
**Kind**: paper_science
**Project**: PROJ-661-https-arxiv-org-abs-2606-00683
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[00c0a2939f43] (severity: science)** Resolve logical inconsistencies between textual claims (e.g., performance superiority) and evaluation tables (e.g., Table 1) by re-running benchmarks or clarifying metric definitions.
- **[b9f856faafb5] (severity: science)** Release training and evaluation code artifacts, including model checkpoints and data generation scripts, to ensure reproducibility of the reported results.
- **[ef848b5a0887] (severity: writing)** Complete the bibliography and ensure all cited references have verified metadata; the current input shows truncation in the .bib file.
- **[5c3309dc146b] (severity: writing)** Several citations remain missing from the bibliography (e.g., \citep{pleias}, \citep{qwen3}, \citep{li-etal-2024-teaching}). Add the corresponding bibliography entries or replace citations with existing references.
- **[ecf66ee4f31d] (severity: writing)** The claim that OCC-RAG-1.7B closes the gap with Qwen-3-4B in thinking mode on multi-hop reasoning is not supported by Table 5, where Qwen-3-4B (thinking) achieves 67.1 In-Acc versus OCC-RAG-1.7B's 60.9. Re-phrase or remove this overstated claim.
- **[fbd21c89858a] (severity: writing)** The statement that OCC-RAG-0.6B exceeds Gemma-3-4B and SmolLM-3-3B on each dimension is correct per Table 5, but the manuscript should explicitly reference the table rows to avoid ambiguity.
- **[8a8a707881c7] (severity: writing)** In the evaluation description, the phrase "2–6× larger" is used broadly. While OCC-RAG-1.7B matches Qwen-3-4B on HotpotQA, it falls short on MuSiQue and TAT-QA. Adjust the wording to reflect that OCC-RAG matches or exceeds some, but not all, larger baselines.
- **[56675ca91d43] (severity: writing)** Provide a concrete definition of "thinking mode" for the reader, and cite the source where this mode is described for Qwen3 and SmolLM3 models.
- **[efcf88620350] (severity: writing)** The introduction states memorization reduces from 8.2 (Qwen3-0.6B) to 5.2, but Table 5 shows Qwen3-0.6B M_R is 9.0 (8.2). Verify all performance numbers quoted in the text exactly match Table 5 values and add a note if rounding was applied.
- **[49f2be8d00ef] (severity: science)** Release the actual code repository (training scripts, data pipeline, evaluation harness) to ensure reproducibility from scratch. Currently, only LaTeX descriptions are available.
- **[162248599afe] (severity: science)** Provide configuration files (e.g., YAML/JSON) for hyperparameters and distributed training settings referenced in Appendix~ef{appendix:training-hyperparameters}.
- **[641dab0b5357] (severity: writing)** Specify the exact Wikipedia dump date/version used for corpus construction to ensure reproducibility and content stability.
- **[44b29bb7f9b6] (severity: science)** Clarify the license and public release status of the 3.25M synthetic training corpus to enable independent verification.
- **[f31b1dfa1ad4] (severity: writing)** Provide specific version tags or commit hashes for the Qwen3 base models to ensure exact reproducibility of the mid-training.
- **[3b4e3eaf1ac6] (severity: writing)** Include license information for evaluation datasets (HotpotQA, MuSiQue, ConFiQA) in the benchmark description.
- **[02b87812b022] (severity: writing)** Figure~\ref{fig:radars} is referenced in Section 5 but the file `appendices/radar.tex` is commented out (line 124). Uncomment to include the figure.
- **[d81b4df12c10] (severity: writing)** In `images/main.tex`, the x-axis (Model size) uses a non-linear mapping (0.6->1, 1->2) but appears visually linear. Clarify scaling or use categorical ticks.
- **[bb09e69980a8] (severity: writing)** In `sections/synth.tex` (Figure~\ref{fig:token_budget}), the left plot x-axis labels (0.01B, 0.1B...) correspond to log indices (0, 1, 2, 3). Explicitly label as log-scale or adjust ticks.
- **[78945c99c9dd] (severity: writing)** Color definitions in `appendices/radar.tex` (e.g., clr1=FFD21E) conflict with main preamble (clr1=6200EA). Unify hex codes to ensure visual consistency if the figure is included.
- **[b7ff98182d09] (severity: writing)** Rename `images/youtu_noemoji.pdf` to a descriptive filename (e.g., `occ-output-structure.pdf`) for professionalism and clarity.
- **[5dd665e3f3d0] (severity: writing)** Remove `\resizebox` in `appendices/radar.tex` (Figure~\ref{fig:radars}) to maintain consistent font sizing across the document.
- **[7da837749dfb] (severity: writing)** Define acronyms FSDP, CE, and technical terms bf16, RDF, SPARQL at first use.
- **[04f27393af05] (severity: writing)** Replace 'parametric knowledge' with 'pre-trained memory' for broader accessibility.
- **[d4833ff30d7f] (severity: writing)** Simplify 'ontological constraints' and 'topological properties' in Section 4.1.
- **[baf2c8cf023d] (severity: science)** Item 775fa02551b9 UNADDRESSED: Results section still claims OCC-RAG-1.7B is 'on par with models of 8B parameters or higher' for refusal, but Table results.tex shows Qwen3-8B achieves 90.7% vs OCC-RAG-1.7B's 87.2%. This is a 3.5 point gap that contradicts the 'highest results' language. Correct to 'competitive with' or remove superlative claims.
- **[0d399e0af6b0] (severity: science)** Item e8b904936279 UNADDRESSED: Introduction numerical claims remain inconsistent with Table results.tex. ConFiQA gap stated as 9.5 points (79.9-64.8=15.1 in table); M_R stated as 8.2→5.2 but table shows 12.7→5.0 for Qwen3-1.7B→OCC-RAG-1.7B. Recalculate all numerical claims against Table results.tex.
- **[3ee5facbb2a6] (severity: writing)** Item 139be0dfe1d9 UNADDRESSED: Comparative claims in Introduction (e.g., 'exceeds Qwen3-1.7B by 9.5 points') do not specify whether baselines are in base or thinking mode. Table results.tex shows thinking mode results in parentheses. Clarify mode specification for all baseline comparisons to prevent logical gaps.
- **[50d2b99e119c] (severity: writing)** Abstract claims OCC-RAG models 'match or exceed' general-purpose models 2-6x their size across all benchmarks. Table 1 shows OCC-RAG-0.6B loses to Qwen3-4B on HotpotQA (57.6 vs 60.6) and TAT-QA (75.0 vs 76.9). Revise to reflect partial superiority.
- **[1dfe9bb503e9] (severity: science)** Introduction states OCC-RAG-0.6B exceeds Qwen3-1.7B by '9.5 points on ConFiQA'. Table 1 shows a 15.1 point gap (79.9 vs 64.8). This numerical inconsistency undermines claim precision. Verify and correct.
- **[51d31aa6c524] (severity: writing)** Claim of 'financial reasoning' capability relies on TAT-QA subset excluding arithmetic/counting questions (Section 5.1). This limits generalizability. Qualify the claim or include full benchmark results.
- **[93506d0f4ce7] (severity: writing)** Results attribute gains to 'internalizing the process' of reasoning (Section 4) without mechanistic evidence (e.g., probing, attention analysis). This extrapolates beyond empirical data. Soften to 'training on structured traces improves performance'.
- **[2c4f8a1e9b3d] (severity: writing)** Figure `images/main.tex` uses a non-linear x-axis mapping (e.g., 0.6B at x=1, 4B at x=4) that compresses larger models, visually exaggerating the efficiency advantage of the 0.6B model relative to its actual parameter count.
- **[32c6e698a38e] (severity: writing)** Add a dedicated paragraph discussing the risk of 'faithful' misinformation propagation. As shown in tables/demo.tex, the model will output false claims if the context supports them. Explain how this risk is mitigated in deployment.
- **[8c38e823b237] (severity: writing)** Specify the license and acceptable use policy for the released OCC-RAG checkpoints. Explicitly state if the models are restricted from use in disinformation campaigns or high-stakes decision-making.
- **[2a94ae610a12] (severity: writing)** Acknowledge limitations regarding adversarial robustness. The paper does not evaluate performance against context injection attacks (prompt injection via retrieved documents), which is a critical safety gap for RAG systems.
- **[f8a0e8b10c77] (severity: science)** Figure 1 aggregates incompatible metrics (In-Acc, F1, R-Acc) without normalization. Please normalize per-benchmark scores or replace with a radar chart using consistent scales.
- **[40bf44cd4748] (severity: science)** Baseline sampling parameters vary by model recommendation. Please report results using a uniform decoding strategy (e.g., greedy) to control for inference variance.
- **[4f467090c662] (severity: science)** LLM-as-judge filtering may introduce bias in reasoning traces. Consider evaluating a subset against human-annotated traces to validate reasoning quality.
- **[75ac891bd396] (severity: science)** Report 95% confidence intervals or standard errors for all benchmark scores in Table 2.
- **[9a96f8767eb5] (severity: science)** Perform statistical significance tests (e.g., bootstrap) for pairwise model comparisons.
- **[1025b48b8373] (severity: science)** Specify the number of evaluation seeds/runs averaged and report variance for data filtering.
- **[abf33782681b] (severity: writing)** Remove duplicate \usepackage{booktabs} declaration in colm2024_conference.tex (lines 15-16).
- **[e45a81fe5aff] (severity: writing)** Standardize citation commands to \citep throughout the manuscript; \cite is used inconsistently in sections/into.tex (line 43).
- **[83561b3fe77b] (severity: writing)** Consolidate color definitions (clr1-clr5) to avoid redefinition warnings between colm2024_conference.tex and appendices/radar.tex.
- **[9ac185d579d7] (severity: writing)** Unify label naming conventions (e.g., use fig: prefix for all figures); tables/demo.tex uses \label{figure:demo} while others use \label{fig:...}.
- **[add5c60ae778] (severity: writing)** Inconsistent color definitions for 'airigreen' family across files (colm2024_conference.tex uses airigreenlight, appendices/radar.tex and images/main.tex use airigreen). Define a single master palette.
- **[0ff9ff129321] (severity: writing)** Remove duplicate \usepackage{booktabs} in colm2024_conference.tex (lines 14, 17).
- **[63f9bf39e7ba] (severity: writing)** Standardize 'Context QA' capitalization in sections/into.tex (use lowercase after first definition).
- **[029428e80981] (severity: writing)** Fix parallel structure in sections/synth.tex pipeline list (e.g., 'ingesting and chunking pages').
- **[ea6af7e780f1] (severity: writing)** Resolve color variable inconsistency for OCC-RAG in appendices/radar.tex (clr5 vs airigreen).


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 50 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
