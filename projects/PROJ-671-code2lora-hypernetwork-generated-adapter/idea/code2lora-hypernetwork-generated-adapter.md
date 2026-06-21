---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/283
paper_authors:
  - Liliana Hotsko
  - Yinxi Li
  - Yuntian Deng
  - Pengyu Nie
---

# Code2LoRA: Hypernetwork-Generated Adapters for Code Language Models under Software Evolution

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.06492
Paper authors (from arXiv): Liliana Hotsko, Yinxi Li, Yuntian Deng, Pengyu Nie

Submitted by: github-actions[bot]

(Intake from human-submission issue #283.)

## Rejection rationale (2026-06-21)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[3c5e0049a3f9]** The manuscript contains numerous citation commands (e.g., \cite{hu2022lora}, \cite{jain2025livecodebench}) but the bibliography section is empty. Verify that all cited works are present in the .bib file and that each citation actually supports the associated claim.
- **[dcd044366751]** The paper states that the static hypernetwork has ≈720 M trainable parameters and the evolutionary version adds ≈25 M (total ≈745 M). Given the described architecture (input dim 2048, hidden 512, LoRA rank 16, 7 projection types across 28 layers), this parameter count is implausibly high. Re‑calculate and correct the reported model sizes, and ensure the claim matches the actual implementation.
- **[1a1a0f9d2d9e]** In the abstract and results sections, the authors claim that \codelorastatic{} matches the per‑repo LoRA upper bound (64.0 % IR EM) and that \codeloraevo{} exceeds the next‑best fine‑tuned adapter by ~1.8 pp EM on OOD data. Verify that the numbers in Tables \ref{tab:main_results}, \ref{tab:per_commit_results}, and \ref{tab:ood_results} indeed correspond to these statements; any discrepancy should be corrected.
- **[fcf0b51bb13e]** The statement that the method incurs “zero inference‑time token overhead” is supported by Table \ref{tab:efficiency}, which lists 0 extra tokens. Ensure that the table includes all evaluated baselines and that the measurement methodology (e.g., token counting) is clearly described.
- **[cb060ddfacf4]** Several macro placeholders (e.g., \UseMacro{cr-em-codelorastatic}, \UseMacro{num-repos-total}) appear in the text without being expanded in the compiled PDF. Replace these with concrete values to avoid ambiguity and to allow readers to verify the reported statistics.
- **[282bf6391f03]** The submission does not include any source code, build scripts, dependency specifications (e.g., requirements.txt, environment.yml), or test suites required to reproduce the experiments. Provide a complete, version‑controlled code repository (or a zip archive) containing the hypernetwork implementation, repository encoder, training loops, evaluation scripts, and any data preprocessing pipelines.
- **[5e7e1d21909f]** Add a clear README that documents the required hardware (GPU model, memory), software stack (Python version, CUDA/cuDNN versions), and step‑by‑step instructions to download the released dataset, install dependencies, and run the training and evaluation pipelines from scratch.
- **[d157bca8f3b0]** Include unit and integration tests for all major modules (e.g., encoder, hypernetwork, GRU recurrence, LoRA generation) and expose them via a standard test runner (pytest). Tests should be runnable on a minimal subset of the data to verify correctness without requiring the full benchmark.
- **[c7d4a8f1f16d]** Provide a reproducibility script (e.g., run_experiments.sh) that automates the full end‑to‑end pipeline: data download → preprocessing → training → evaluation → result aggregation. The script should log random seeds, hyperparameter values, and output the exact tables/figures reported in the paper.
- **[09db03fde074]** Ensure that all external resources (e.g., the Qwen3‑Embedding‑0.6B model, Qwen2.5‑Coder‑1.5B checkpoint) are referenced with precise version identifiers or URLs, and include code to download them programmatically with checksum verification.
- **[6c5d81a3c7c6]** Provide an explicit data‑license statement for the epopeftbench{} dataset (e.g., a CC‑BY‑4.0 or MIT license) and include a LICENSE file in the repository.
- **[c7a0df62794f]** Document the exact version (commit SHA) of each GitHub repository used in the benchmark and archive a snapshot (e.g., via Zenodo or the 4open.science link) to prevent link‑rot.
- **[84de6beaea3e]** Describe how missing or malformed files (e.g., repositories that lack a test suite or have non‑Python files) were filtered or imputed; currently the paper only mentions a star‑count filter.
- **[b7e1df3bebec]** Include a schema definition (e.g., JSON schema) for the benchmark entries (repo ID, commit hash, prefix tokens, target assertion) and verify that all entries conform to it.
- **[456d16d5b9ee]** Clarify the handling of duplicate or near‑duplicate repositories (e.g., forks) to avoid data leakage between train/val/test splits.
- **[88f2a8a3e6fc]** Provide persistent URLs for the released dataset and code (the current URLs point to anonymous.4open.science and HuggingFace without version tags); use versioned releases or DOI links.
- **[f17236b43608]** State the process for updating the benchmark as new repositories appear (e.g., a changelog or versioning policy) to ensure reproducibility over time.
- **[dc7e5f58d55a]** Figure 1 (architecture_overview) lacks clear axis‑like labels for the three sub‑panels (a‑c). Add concise titles (e.g., “(a) Overall pipeline”, “(b) Static hypernetwork”, “(c) Evolutionary hypernetwork”) and annotate the flow arrows with brief verb phrases so readers can follow the data flow without referring to the caption.
- **[82cb55c81ef8]** The color palette used in Figure 2 (commit_pct_trend) relies on two shades of blue that are hard to distinguish for color‑blind readers. Replace one line with a distinct hue (e.g., orange) or use different line styles (solid vs. dashed) and include a legend.
- **[82df1265c451]** Figure 3 (dataset_construction) presents a schematic of the benchmark splits but omits axis units (e.g., “# repos”, “# commits”). Add axis labels and numeric tick marks to make the quantitative relationships explicit.
- **[af0c3d548577]** Figure 4 (error_reclassification) shows a stacked bar chart without a legend explaining the color mapping to error categories. Provide a legend and ensure the colors are color‑blind safe.
- **[0cfddb632a10]** Figure 5 (input_length_distribution) displays two histograms side‑by‑side but the x‑axis is unlabeled (token count) and the y‑axis lacks a unit (frequency). Add both axis labels and indicate whether the y‑axis is absolute count or proportion.
- **[c1eca65fedc8]** Figure 6 (lora_comparison_heatmap) uses a heatmap with a single sequential colormap. Consider a diverging colormap centered at zero to highlight positive vs. negative weight norms, and add a color bar with numeric tick labels.
- **[4611c078208e]** Figure 7 (lora_tsne) omits axis ticks and labels (t‑SNE dimensions are arbitrary). Include a brief note in the caption that axes are t‑SNE components and add a small legend indicating the color scale (EM %).
- **[7ab105d0e951]** Figure 8 (per_repo_violin) shows violin plots but the y‑axis (Exact‑Match %) lacks a range label (0–100 %). Add axis limits and tick marks for better readability at print scale.
- **[672f52eb8091]** Figure 9 (plora_data_sparsity) presents a scatter plot without axis titles (training‑set size, EM %). Add clear axis labels and consider using larger markers for print legibility.
- **[ed26b9c8e6be]** Figure 10 (scaling_law) displays a log‑linear curve but does not indicate the scale (log‑x axis). Annotate the x‑axis as “Number of training repositories (log scale)” and include error bars if available.
- **[84df67be9c87]** Define all acronyms on first use (e.g., LoRA, GRU, RAG, DRC, FFT, QnA, EM, CodeBLEU).
- **[4f10dbe96492]** Replace or explain domain‑specific jargon that may be opaque to non‑specialist readers (e.g., “hypernetwork‑generated adapters”, “parameter‑efficient fine‑tuning”, “repository‑specific LoRA”, “rank $r$”, “$lpha$ scaling”, “truncated BPTT”).
- **[3cf771702fa8]** Add brief plain‑language explanations for technical concepts such as hypernetworks, LoRA adapters, and the role of the repository encoder, preferably in the Introduction or a dedicated “Background” paragraph.
- **[71ad4643e6a5]** Introduce a glossary or inline parenthetical definitions for recurring technical terms (e.g., “GRU (gated recurrent unit)”, “RAG (retrieval‑augmented generation)”, “DRC (dependency‑resolved context)”).
- **[609ce79cf8fa]** Avoid overuse of shorthand symbols in equations without accompanying textual description (e.g., symbols $\mathbf{e}$, $\mathbf{h}$, $\mathbf{z}_t$). Provide a short sentence explaining what each represents.
- **[5a7511d91e5d]** Clarify the meaning of “static” vs. “evolution” scenarios in plain terms early in the paper, rather than relying on the symbols \codelorastatic{} and \codeloraevo{} alone.
- **[a999f4424927]** In the Method section, replace the phrase “zero inference‑time token overhead” with a more accessible description such as “adds no extra tokens to the model’s input during inference”.
- **[9d51f261bb1a]** When referring to datasets, replace macro placeholders like \UseMacro{num-repos-total} with the actual numbers or a clear statement (e.g., “we collected 623 Python repositories”).
- **[70f2f357e5a4]** Explain abbreviations in table captions (e.g., “EM” = Exact Match, “CR” = cross‑repo, “IR” = in‑repo) so readers can interpret results without consulting the text.
- **[5411a6fc8bba]** Provide a short, non‑technical summary of the benchmark construction (Section 4) for readers unfamiliar with software‑evolution terminology.
- **[3f3ddc393628]** The manuscript states that LoRA matrices are shared across all 28 layers yet reports ~720 M trainable parameters for the static hypernetwork. This contradicts the parameter count implied by sharing. Re‑calculate and report the correct number of trainable parameters, and ensure the description of sharing matches the actual architecture.
- **[65ff4d569b31]** In the Results section, the claim that codelorastatic “matches the per‑repo LoRA upper bound” is inconsistent with Table \ref{tab:main_results}, where codelorastatic’s IR EM (66.2 %) exceeds the reported per‑repo LoRA IR EM (64.0 %). Clarify whether per‑repo LoRA is truly an upper bound or adjust the claim accordingly.
- **[3763a5cee5d7]** The Deployment Efficiency table lists extra storage for codelorastatic as +679 MB, but a hypernetwork with ~720 M parameters (even in bf16) would require >1.4 GB. Reconcile the storage figure with the actual size of the hypernetwork and any adapter storage.
- **[7b57d4c1d343]** Table \ref{tab:ablation_data} shows a dip in CR‑test EM when training on 500 repositories (61.2 %) compared to 409 repositories (63.8 %). This contradicts the narrative of a log‑linear improvement that plateaus. Provide an explanation or correct the table if it contains an error.
- **[5b55c5a0e209]** The OOD evaluation caveats acknowledge that shorter target lengths inflate Exact Match scores, yet the paper still reports absolute EM improvements. Include a normalized metric (e.g., EM adjusted for target length) or discuss how this inflation might affect the claimed superiority.
- **[06eca977cad4]** The manuscript repeatedly refers to per‑repo LoRA as an “upper bound”. Since per‑repo LoRA is itself a learned baseline and not provably optimal, this phrasing overstates its status. Re‑word to describe it as a strong baseline rather than an upper bound.
- **[eb1e0f67be1d]** The OOD evaluation (Table 5) shows higher exact‑match scores, but the authors note that OOD targets are shorter, which can inflate EM. Provide a controlled analysis (e.g., normalize target length or report length‑adjusted metrics) to substantiate the claim of “strong generalization”.
- **[cd5e1d0f7be6]** The claim that Code2LoRA “consistently gains over context‑injection and fine‑tuning baselines” should be qualified to reflect the modest OOD margin (≈1.8 pp) and the fact that some baselines (e.g., FFT‑RAG) close the gap on certain splits. Adjust the language to avoid overstating superiority.
- **[586bc04fac4a]** Add a dedicated discussion of dual‑use risks, explicitly acknowledging that the hypernetwork‑generated adapters could be employed to more efficiently produce malicious or vulnerable code, and outline mitigation strategies (e.g., usage policies, model‑level safety filters).
- **[c52a769e776b]** Clarify the licensing compliance of the dataset: confirm that all harvested repositories are truly under permissive licenses (MIT/Apache‑2.0) and that no copyrighted code is redistributed beyond what the licenses permit.
- **[bd3e011194ea]** Address potential privacy or leakage concerns if the method is applied to private repositories: discuss whether the generated LoRA adapters could unintentionally encode proprietary code snippets and propose safeguards (e.g., encryption, access controls).
- **[5bdd3f0106af]** Provide an ethical statement on the intended use cases and any safeguards implemented during training or inference to prevent the generation of harmful code (e.g., filtering of dangerous APIs, monitoring of generated outputs).
- **[415e3f821a45]** Report variance (e.g., standard deviation or confidence intervals) for all primary metrics (EM, EditSim, CodeBLEU) across multiple random seeds or data splits to assess statistical significance of reported gains.
- **[1bf20e76927a]** Include statistical hypothesis testing (e.g., paired t‑tests or bootstrap) comparing Code2LoRA variants against each baseline, and report p‑values to guard against chance improvements.
- **[7e6f9760492c]** Clarify the random seed handling and whether experiments were repeated; if only a single run was performed, add at least three runs with different seeds for each method.
- **[a2710eca0411]** Provide a more detailed ablation of key hyperparameters (e.g., LoRA rank, GRU hidden size, number of training epochs) to demonstrate robustness of the central claims to these design choices.
- **[438a13540cb2]** Discuss potential overfitting to the specific benchmark (RepoPEFTBench) and evaluate on an additional, independently sourced code‑completion benchmark to strengthen external validity.
- **[c574f1656d5c]** Report the total number of trainable parameters for each baseline (including per‑repo LoRA) and the memory/computation overhead during inference to contextualize the claimed efficiency gains.
- **[9dbcec06b733]** Provide statistical significance testing (e.g., paired t‑tests or bootstrap) for all reported performance differences in Tables 1–3, and report p‑values or confidence intervals.
- **[4098276978af]** Report variance measures (standard deviation, standard error) across multiple training runs for each method; currently only point estimates are shown.
- **[b9ad242ee5aa]** Address multiple‑comparison correction (e.g., Bonferroni or Holm) given the large number of baselines and metrics evaluated.
- **[e18144116771]** Specify random seeds, data‑split randomness, and any nondeterministic training settings to enable exact reproducibility of the results.
- **[0c8510996094]** Include effect‑size metrics (e.g., Cohen’s d) alongside raw EM/CodeBLEU improvements to contextualize practical significance.
- **[90a3cddb1204]** Replace all custom macro calls such as \codelora{}, \codelorastatic{}, \codeloraevo{}, \URLRepo{}, \URLData{}, and \UseMacro{...} with either defined macros or plain text. Undefined macros cause LaTeX compilation failures.
- **[80659d94924c]** Ensure every \cite, \citet, and \citep command references a valid entry in the bibliography. The current source has no \bibitem entries, leading to missing references.
- **[1134428e4da4]** Standardize heading hierarchy: use \section, \subsection, \subsubsection consistently. The current document jumps from \section to \paragraph without intermediate levels in some places.
- **[c46847321001]** Reformat all tables to use the booktabs package consistently (\toprule, \midrule, \bottomrule) and align numeric columns on the decimal point for readability.
- **[766f5c1b70ad]** Place figure captions immediately after \includegraphics and before \label, and ensure the \label is prefixed with the appropriate prefix (e.g., \label{fig:architecture}). Currently some figures have the label after the caption, which is acceptable, but verify consistency.
- **[0b5d51377006]** Wrap long lines (especially in tables and itemized lists) to stay within 80 characters for source readability. Many lines exceed this limit, making version control diffs noisy.
- **[ee8f32d23c16]** Replace en‑dashes (–) and em‑dashes (—) with proper LaTeX commands (\textendash, \textemdash) or use ``--'' and ``---'' to avoid encoding issues.
- **[92d9d0bca5b4]** Add a \bibliographystyle{plainnat} and a corresponding \bibliography{bib} file with proper entries; the current bibliography block is empty, causing compilation warnings.
- **[fc1da14479c6]** Check that all \label commands have matching \ref or \cref calls. Several labels (e.g., \label{sec:method}) are defined but never referenced.
- **[6ae03ce577a6]** Ensure that all list environments (itemize, enumerate) have consistent indentation and that each \item starts on a new line.
- **[61af2944cbcd]** Replace all placeholder macros (e.g., \UseMacro{...}) with their actual values; the current manuscript contains many unreplaced macros that break readability.
- **[6d5121f779e6]** Break up overly long sentences, especially in the Introduction and Method sections, to improve flow and comprehension.
- **[e1cbb7cb2a74]** Standardize punctuation and spacing (e.g., ensure a space after commas, use en‑dashes consistently, and avoid stray hyphens like “‑04”).
- **[74783e17aacd]** Check for missing articles or prepositions (e.g., “We propose … supporting …” could be “… supporting …”) and correct minor grammatical errors throughout.
- **[80350c0fb394]** Ensure all tables and figures have complete, self‑contained captions and that references (e.g., Fig. 1) are correctly linked; some captions lack context for readers.
- **[dcbc80118f06]** Proofread the abstract and conclusion for redundant phrasing (e.g., “zero inference‑time token overhead” could be simplified) and tighten wording.
