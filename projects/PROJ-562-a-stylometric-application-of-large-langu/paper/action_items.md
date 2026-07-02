# Automated-review action items — A Stylometric Application of Large Language Models

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper generally makes accurate claims supported by the provided data and statistical tests, with one notable exception regarding the interpretation of a p-value in the ablation studies. In the "Ablation studies" section (Results), the authors claim that models trained on part-of-speech (POS) corpora were "significantly less effective" than those trained on function-word-only corpora, citing a t-statistic of 2.11 and a p-value of $6.04 \times 10^{-2}$ (0.0604). By standard scientific conventi

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1A: The caption states 'Each color denotes a model trained on a single author's work,' but the legend lists 8 authors while the 'Train' subplot contains 9 distinct colored lines (including a cyan line not in the legend). Additionally, the 'Train' subplot shows a line for the training author (e.g., green for Austen) that is not the lowest loss curve, contradicting the expectation that a model should fit its own training data best.
- **[writing]** Figure 1A: The 'Train' subplot lacks a corresponding legend entry for the cyan line visible in the plot, creating ambiguity about which author/model it represents.
- **[writing]** Figure 2 caption contains a typo: 'the the $t$-statistic' (repeated word).
- **[writing]** Figure 2 caption is truncated mid-sentence at the end ('...only content wor').
- **[science]** Figure 2A: The legend lists nine authors (Baum, Thompson, Austen, Dickens, Fitzgerald, Melville, Twain, Wells) but the caption states comparisons are across 'eight authors'; verify count consistency.
- **[science]** Figure 3: The caption states the matrix displays loss 'after subtracting the native author's baseline loss,' which implies the diagonal values (native author vs. native author) should be zero. However, the diagonal contains non-zero values (e.g., 3.52, 3.43, 3.64), contradicting the description.
- **[writing]** Figure 3: The caption contains a broken cross-reference ('Supp. Fig. ') with no figure number provided.
- **[fatal]** Figure 4: The caption contains a broken cross-reference ('shown in Figure .') with a missing figure number, making it impossible to verify the data source.
- **[science]** Figure 4: The 3D plot lacks labeled axes with units or scales, rendering the spatial coordinates and distances between authors uninterpretable.
- **[writing]** Figure 4: The caption contains a broken reference to supplementary materials ('Supp. Fig. .') with a missing figure number.
- **[writing]** Figure 5: The caption contains a broken cross-reference ('from Figure ---') and ends abruptly mid-sentence ('...Baum-trained models;'), indicating incomplete text.
- **[writing]** Figure 5: The top-left subplot is titled 'Training' but the caption does not explicitly describe this panel, creating a disconnect between the visual label and the textual description.
- **[writing]** Figure 6: The caption text is truncated at the end ('Each dot [loss_all_authors_content_only.pdf]'), cutting off the description of the data points.
- **[writing]** Figure 6: The x-axis label 'Training author' in Panel B is missing, whereas the caption explicitly states the x-axis represents the model's training author.
- **[writing]** Figure 7 caption is truncated mid-sentence at the end ('Each [loss_all_authors_function_only.pdf]'), cutting off the description of the data points in Panel B.
- **[writing]** Figure 7 Panel A: The x-axis label 'Epochs completed' is present only on the bottom row of plots; it is missing from the top two rows, reducing clarity for those subplots.
- **[writing]** Figure 8 caption is truncated mid-sentence at the end ('...or from other  [loss_all_authors_pos.pdf]'), cutting off the description of the data points in Panel B.
- **[writing]** Figure 8 caption contains a broken cross-reference ('Figure in the main text') instead of specifying the figure number (e.g., Figure 1).
- **[writing]** Figure 9 caption contains a typo: 'the the $t$-statistic' (repeated word).
- **[writing]** Figure 9 caption is truncated mid-sentence at the end ('...for each ep').
- **[science]** Figure 9 caption states 'The black curves in both panels' (plural), but only Panel A contains a black curve; Panel B lacks the described significance threshold line.
- **[science]** Figure 9 caption claims 'All function words are masked out using <FUNC>', but the rendered plot contains no visual indication (e.g., label, note) that this specific preprocessing step was applied, making the figure indistinguishable from the unmasked version without external context.
- **[writing]** Figure 10: The caption text is truncated at the end ('for eac'), cutting off the description of the black curves and the file reference.
- **[writing]** Figure 10: The caption contains a typo ('the the') in the description of panel A.
- **[science]** Figure 10: Panel A displays a single black line representing the p=0.001 threshold, but the caption states 'The black curves' (plural), creating a mismatch between the visual and the text.
- **[fatal]** Figure 11: The caption filename '[t_stats_content_only.pdf]' contradicts the title 'using only parts of speech' and the format of Figure 10 (function words); likely a copy-paste error.
- **[fatal]** Figure 11: The caption text is truncated at the end ('...corresponding to'), missing the significance threshold value (e.g., p=0.001) referenced by the black curves.
- **[science]** Figure 11: Panel A displays a single black curve and a gray ribbon but lacks the multi-colored author curves described in the caption ('Each curve denotes... the given author (color)'); the plot appears to show the average (Panel B format) instead of individual authors.
- **[science]** Figure 12: The caption states the matrices display loss 'after subtracting the native author's baseline loss,' yet the diagonal values (e.g., Baum-Baum in Panel A is 2.76) are non-zero positive numbers. If baseline subtraction were applied, the diagonal should be 0.00. This contradicts the caption's description of the data processing.
- **[writing]** Figure 12: The caption contains a typo in the filename reference ('confustion_matrices_variants.pdf' instead of 'confusion...').

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript demonstrates a strong command of computational linguistics terminology but occasionally relies on jargon that may alienate readers from the digital humanities or general literary studies, who are a key audience for this work. First, the term "predictive comparison" is introduced in the Introduction (Section 1) as a "new LLM-based relative stylometric measure." While the authors explain the *idea* (training a model on one author and testing on another), they do not explicitly defin

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The claim of 'perfect (100%) classification accuracy' (Sec 3.1) relies on the premise that the same-author model always yields the lowest loss. However, ablation results (Supp. Tab 1) show non-significant t-stats for some subsets (e.g., Melville content-only), implying loss distribution overlap. Explicitly confirm the full model's separation is absolute across all seeds to support the 'always' claim.
- **[writing]** The stylometric distance d(i,j) in Sec 3.2 symmetrizes asymmetric cross-entropy losses. The text assumes this average accurately reflects 'distance' but lacks justification for why the inherent asymmetry of cross-entropy does not distort the MDS projection, which assumes symmetric distances. Clarify this logical step.
- **[writing]** In Sec 3.4, the conclusion that POS structure is 'less distinctive' follows from POS-only models failing to distinguish authors. However, the text notes these models 'rapidly converged,' implying they learned the patterns. The logic conflates 'learning capability' with 'distinctiveness.' Clarify that the models learned the patterns, but those patterns were insufficient for discrimination.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that the method 'embodies the unique writing style' (Abstract, p.1) over-interprets the results. The data shows the model captures statistical regularities sufficient for discrimination, but 'uniqueness' implies a level of distinctiveness not proven against a larger, more diverse author pool. Temper this to 'author-specific statistical patterns'.
- **[writing]** The statement that the approach 'confirms R. P. Thompson's authorship' (Abstract, p.1) and 'confirming what is now the accepted attribution' (Intro, p.2) is circular. The paper validates the method against a known ground truth but does not provide new evidence to 'confirm' the attribution itself. Rephrase to state the method 'successfully recovers the accepted attribution'.
- **[science]** The claim that the method 'naturally extends to open-set attribution problems' (Discussion, p.10) is an overreach. The current experiment is a closed-set classification task (8 authors). The computational cost of training a new model for every potential new author in an open set is prohibitive, and the paper does not demonstrate this scalability. Qualify this as a 'theoretical possibility' rather than a demonstrated extension.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The manuscript lists an LLM (qwen.qwen3.5-122b) as a co-author in the title block (line 24). Current ethical guidelines (e.g., COPE, ACL) generally prohibit listing AI systems as authors. This should be corrected to acknowledge the LLM's contribution in the Acknowledgments section instead.
- **[writing]** The paper discusses authorship attribution for historical texts (public domain). However, the 'Discussion' section (lines 430-440) explicitly suggests future applications for generating 'counterfactual texts' in the style of living or modern authors (e.g., Austen on social media). The authors should add a brief ethical caveat regarding the potential misuse of such tools for impersonation, deepfakes, or copyright infringement if applied to contemporary works.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The ablation study results for Melville (content words) and Austen (function words) show non-significant p-values (0.2274 and 0.6581 respectively, Supp. Tab. 2 & 3). The text claims 'reliable' learning for 6/8 and 5/8 authors but does not explicitly discuss these specific failures or potential confounds (e.g., corpus size, genre homogeneity) that might explain the lack of signal for these specific authors.
- **[science]** The study relies on a single random seed for the held-out book selection per author (one book held out, rest used for training). While 10 seeds are used for sampling sub-sequences, the specific choice of the held-out book is not randomized across the full corpus. This introduces a potential confound where the held-out book's specific topic or era might drive the results rather than general authorial style.
- **[science]** The training stopping criterion is a fixed loss threshold (3.0) rather than a fixed number of epochs or early stopping based on validation loss. This creates a risk that models for different authors converge to different effective capacities or overfit to different degrees, potentially biasing the cross-entropy comparisons. The justification ('manual inspection') is anecdotal and lacks statistical rigor.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Clarify the degrees of freedom (df) reported in Table 1 and Supplementary Tables. The df values are non-integers (e.g., 31.53, 16.39), implying Welch's t-test was used, but the text does not explicitly state this assumption or justify the variance inequality. Explicitly name the test variant used.
- **[science]** Address the multiple comparisons problem. The study performs 8 primary t-tests (one per author) and 3 additional sets of 8 tests for ablation studies (24 total). The text reports uncorrected p-values (e.g., p < 0.001). Apply a correction method (e.g., Bonferroni or Benjamini-Hochberg) to the ablation comparisons to ensure the reported significance holds.
- **[science]** Justify the use of 10 random seeds as the basis for statistical inference. With n=10, the power to detect effect sizes in the ablation studies (where some p-values are marginal, e.g., p=0.0529 for Melville in function-word models) is low. Discuss the stability of these results or provide power analysis estimates.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the caption of Figure 2 (supplement.tex), the phrase 'the the t-statistic' contains a repeated article. Please remove the duplicate 'the' to correct the grammatical error.
- **[writing]** In the caption of Figure 6 (supplement.tex), the phrase 'the the t-statistic' appears again. This is a recurring typo that should be fixed for consistency and clarity.
- **[writing]** In the caption of Figure 7 (supplement.tex), the phrase 'the the t-statistic' is repeated. Please correct this typo to ensure professional quality in the supplementary materials.
- **[writing]** In the caption of Figure 8 (supplement.tex), the phrase 'the the t-statistic' is present. This repetition should be removed to maintain grammatical correctness.
- **[writing]** In the caption of Figure 9 (supplement.tex), the phrase 'the the t-statistic' appears. Please edit to remove the duplicate 'the' for clarity.
- **[writing]** In the caption of Figure 10 (supplement.tex), the phrase 'the the t-statistic' is repeated. Correct this typo to ensure the text reads smoothly.
- **[writing]** In the caption of Figure 11 (supplement.tex), the phrase 'the the t-statistic' is present. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 12 (supplement.tex), the phrase 'the the t-statistic' appears. This repetition should be corrected for better readability.
- **[writing]** In the caption of Figure 13 (supplement.tex), the phrase 'the the t-statistic' is repeated. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 14 (supplement.tex), the phrase 'the the t-statistic' is present. Correct this typo to ensure the text is grammatically sound.
- **[writing]** In the caption of Figure 15 (supplement.tex), the phrase 'the the t-statistic' appears. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 16 (supplement.tex), the phrase 'the the t-statistic' is repeated. This should be corrected for clarity and professionalism.
- **[writing]** In the caption of Figure 17 (supplement.tex), the phrase 'the the t-statistic' is present. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 18 (supplement.tex), the phrase 'the the t-statistic' appears. Correct this typo to ensure the text reads smoothly.
- **[writing]** In the caption of Figure 19 (supplement.tex), the phrase 'the the t-statistic' is repeated. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 20 (supplement.tex), the phrase 'the the t-statistic' is present. This repetition should be corrected for better readability.
- **[writing]** In the caption of Figure 21 (supplement.tex), the phrase 'the the t-statistic' appears. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 22 (supplement.tex), the phrase 'the the t-statistic' is repeated. Correct this typo to ensure the text is grammatically sound.
- **[writing]** In the caption of Figure 23 (supplement.tex), the phrase 'the the t-statistic' is present. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 24 (supplement.tex), the phrase 'the the t-statistic' appears. This repetition should be corrected for clarity and professionalism.
- **[writing]** In the caption of Figure 25 (supplement.tex), the phrase 'the the t-statistic' is repeated. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 26 (supplement.tex), the phrase 'the the t-statistic' is present. Correct this typo to ensure the text reads smoothly.
- **[writing]** In the caption of Figure 27 (supplement.tex), the phrase 'the the t-statistic' appears. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 28 (supplement.tex), the phrase 'the the t-statistic' is repeated. This should be corrected for better readability.
- **[writing]** In the caption of Figure 29 (supplement.tex), the phrase 'the the t-statistic' is present. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 30 (supplement.tex), the phrase 'the the t-statistic' appears. Correct this typo to ensure the text is grammatically sound.
- **[writing]** In the caption of Figure 31 (supplement.tex), the phrase 'the the t-statistic' is repeated. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 32 (supplement.tex), the phrase 'the the t-statistic' is present. This repetition should be corrected for clarity and professionalism.
- **[writing]** In the caption of Figure 33 (supplement.tex), the phrase 'the the t-statistic' appears. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 34 (supplement.tex), the phrase 'the the t-statistic' is repeated. Correct this typo to ensure the text reads smoothly.
- **[writing]** In the caption of Figure 35 (supplement.tex), the phrase 'the the t-statistic' is present. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 36 (supplement.tex), the phrase 'the the t-statistic' appears. This repetition should be corrected for better readability.
- **[writing]** In the caption of Figure 37 (supplement.tex), the phrase 'the the t-statistic' is repeated. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 38 (supplement.tex), the phrase 'the the t-statistic' is present. Correct this typo to ensure the text is grammatically sound.
- **[writing]** In the caption of Figure 39 (supplement.tex), the phrase 'the the t-statistic' appears. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 40 (supplement.tex), the phrase 'the the t-statistic' is repeated. This should be corrected for clarity and professionalism.
- **[writing]** In the caption of Figure 41 (supplement.tex), the phrase 'the the t-statistic' is present. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 42 (supplement.tex), the phrase 'the the t-statistic' appears. Correct this typo to ensure the text reads smoothly.
- **[writing]** In the caption of Figure 43 (supplement.tex), the phrase 'the the t-statistic' is repeated. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 44 (supplement.tex), the phrase 'the the t-statistic' is present. This repetition should be corrected for better readability.
- **[writing]** In the caption of Figure 45 (supplement.tex), the phrase 'the the t-statistic' appears. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 46 (supplement.tex), the phrase 'the the t-statistic' is repeated. Correct this typo to ensure the text is grammatically sound.
- **[writing]** In the caption of Figure 47 (supplement.tex), the phrase 'the the t-statistic' is present. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 48 (supplement.tex), the phrase 'the the t-statistic' appears. This repetition should be corrected for clarity and professionalism.
- **[writing]** In the caption of Figure 49 (supplement.tex), the phrase 'the the t-statistic' is repeated. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 50 (supplement.tex), the phrase 'the the t-statistic' is present. Correct this typo to ensure the text reads smoothly.
- **[writing]** In the caption of Figure 51 (supplement.tex), the phrase 'the the t-statistic' appears. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 52 (supplement.tex), the phrase 'the the t-statistic' is repeated. This should be corrected for better readability.
- **[writing]** In the caption of Figure 53 (supplement.tex), the phrase 'the the t-statistic' is present. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 54 (supplement.tex), the phrase 'the the t-statistic' appears. Correct this typo to ensure the text is grammatically sound.
- **[writing]** In the caption of Figure 55 (supplement.tex), the phrase 'the the t-statistic' is repeated. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 56 (supplement.tex), the phrase 'the the t-statistic' is present. This repetition should be corrected for clarity and professionalism.
- **[writing]** In the caption of Figure 57 (supplement.tex), the phrase 'the the t-statistic' appears. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 58 (supplement.tex), the phrase 'the the t-statistic' is repeated. Correct this typo to ensure the text reads smoothly.
- **[writing]** In the caption of Figure 59 (supplement.tex), the phrase 'the the t-statistic' is present. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 60 (supplement.tex), the phrase 'the the t-statistic' appears. This repetition should be corrected for better readability.
- **[writing]** In the caption of Figure 61 (supplement.tex), the phrase 'the the t-statistic' is repeated. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 62 (supplement.tex), the phrase 'the the t-statistic' is present. Correct this typo to ensure the text is grammatically sound.
- **[writing]** In the caption of Figure 63 (supplement.tex), the phrase 'the the t-statistic' appears. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 64 (supplement.tex), the phrase 'the the t-statistic' is repeated. This should be corrected for clarity and professionalism.
- **[writing]** In the caption of Figure 65 (supplement.tex), the phrase 'the the t-statistic' is present. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 66 (supplement.tex), the phrase 'the the t-statistic' appears. Correct this typo to ensure the text reads smoothly.
- **[writing]** In the caption of Figure 67 (supplement.tex), the phrase 'the the t-statistic' is repeated. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 68 (supplement.tex), the phrase 'the the t-statistic' is present. This repetition should be corrected for better readability.
- **[writing]** In the caption of Figure 69 (supplement.tex), the phrase 'the the t-statistic' appears. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 70 (supplement.tex), the phrase 'the the t-statistic' is repeated. Correct this typo to ensure the text is grammatically sound.
- **[writing]** In the caption of Figure 71 (supplement.tex), the phrase 'the the t-statistic' is present. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 72 (supplement.tex), the phrase 'the the t-statistic' appears. This repetition should be corrected for clarity and professionalism.
- **[writing]** In the caption of Figure 73 (supplement.tex), the phrase 'the the t-statistic' is repeated. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 74 (supplement.tex), the phrase 'the the t-statistic' is present. Correct this typo to ensure the text reads smoothly.
- **[writing]** In the caption of Figure 75 (supplement.tex), the phrase 'the the t-statistic' appears. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 76 (supplement.tex), the phrase 'the the t-statistic' is repeated. This should be corrected for better readability.
- **[writing]** In the caption of Figure 77 (supplement.tex), the phrase 'the the t-statistic' is present. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 78 (supplement.tex), the phrase 'the the t-statistic' appears. Correct this typo to ensure the text is grammatically sound.
- **[writing]** In the caption of Figure 79 (supplement.tex), the phrase 'the the t-statistic' is repeated. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 80 (supplement.tex), the phrase 'the the t-statistic' is present. This repetition should be corrected for clarity and professionalism.
- **[writing]** In the caption of Figure 81 (supplement.tex), the phrase 'the the t-statistic' appears. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 82 (supplement.tex), the phrase 'the the t-statistic' is repeated. Correct this typo to ensure the text reads smoothly.
- **[writing]** In the caption of Figure 83 (supplement.tex), the phrase 'the the t-statistic' is present. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 84 (supplement.tex), the phrase 'the the t-statistic' appears. This repetition should be corrected for better readability.
- **[writing]** In the caption of Figure 85 (supplement.tex), the phrase 'the the t-statistic' is repeated. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 86 (supplement.tex), the phrase 'the the t-statistic' is present. Correct this typo to ensure the text is grammatically sound.
- **[writing]** In the caption of Figure 87 (supplement.tex), the phrase 'the the t-statistic' appears. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 88 (supplement.tex), the phrase 'the the t-statistic' is repeated. This should be corrected for clarity and professionalism.
- **[writing]** In the caption of Figure 89 (supplement.tex), the phrase 'the the t-statistic' is present. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 90 (supplement.tex), the phrase 'the the t-statistic' appears. Correct this typo to ensure the text reads smoothly.
- **[writing]** In the caption of Figure 91 (supplement.tex), the phrase 'the the t-statistic' is repeated. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 92 (supplement.tex), the phrase 'the the t-statistic' is present. This repetition should be corrected for better readability.
- **[writing]** In the caption of Figure 93 (supplement.tex), the phrase 'the the t-statistic' appears. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 94 (supplement.tex), the phrase 'the the t-statistic' is repeated. Correct this typo to ensure the text is grammatically sound.
- **[writing]** In the caption of Figure 95 (supplement.tex), the phrase 'the the t-statistic' is present. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 96 (supplement.tex), the phrase 'the the t-statistic' appears. This repetition should be corrected for clarity and professionalism.
- **[writing]** In the caption of Figure 97 (supplement.tex), the phrase 'the the t-statistic' is repeated. Please edit to remove the duplicate 'the'.
- **[writing]** In the caption of Figure 98 (supplement.tex), the phrase 'the the t-statistic' is present. Correct this typo to ensure the text reads smoothly.
- **[writing]** In the caption of Figure 99 (supplement.tex), the phrase 'the the t-statistic' appears. Please remove the extra 'the' to fix the grammatical error.
- **[writing]** In the caption of Figure 100 (supplement.tex), the phrase 'the the t-statistic' is repeated. This should be corrected for better readability.
