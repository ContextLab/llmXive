---
action_items:
- id: 0d300bf29054
  severity: science
  text: The ablation study results for Melville (content words) and Austen (function
    words) show non-significant p-values (0.2274 and 0.6581 respectively, Supp. Tab.
    2 & 3). The text claims 'reliable' learning for 6/8 and 5/8 authors but does not
    explicitly discuss these specific failures or potential confounds (e.g., corpus
    size, genre homogeneity) that might explain the lack of signal for these specific
    authors.
- id: 35f9dba4a27a
  severity: science
  text: The study relies on a single random seed for the held-out book selection per
    author (one book held out, rest used for training). While 10 seeds are used for
    sampling sub-sequences, the specific choice of the held-out book is not randomized
    across the full corpus. This introduces a potential confound where the held-out
    book's specific topic or era might drive the results rather than general authorial
    style.
- id: 8851b36d1e63
  severity: science
  text: The training stopping criterion is a fixed loss threshold (3.0) rather than
    a fixed number of epochs or early stopping based on validation loss. This creates
    a risk that models for different authors converge to different effective capacities
    or overfit to different degrees, potentially biasing the cross-entropy comparisons.
    The justification ('manual inspection') is anecdotal and lacks statistical rigor.
artifact_hash: 148021f63314c6cbe2b6159eaaaecc4e6c793ec5541ddbe74681664a10cdde19
artifact_path: projects/PROJ-562-a-stylometric-application-of-large-langu/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:16:14.328808Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling application of LLM cross-entropy loss for stylometry, demonstrating perfect classification accuracy on a small set of eight authors. The experimental design, utilizing 10 random seeds for data sampling and reporting bootstrap confidence intervals, generally supports the robustness of the central claim that LLMs capture author-specific styles. However, several aspects of the evidence require clarification to rule out alternative explanations and ensure statistical rigor.

First, the ablation studies in the Supplementary Materials reveal specific failures that are glossed over in the main text. Table 2 (content words) shows Melville's model fails to distinguish his own text from others ($p=0.2274$), and Table 3 (function words) shows Austen's model fails ($p=0.6581$). The text states models "reliably learned" patterns for 6/8 and 5/8 authors, respectively, but does not analyze *why* these specific authors failed. Given the small sample size (8 authors), these failures could indicate that the stylometric signal for these authors is not robust to the specific ablation method, or that their corpora (e.g., Melville's varied genres) introduce noise that the ablation exacerbates. A discussion of these specific outliers is necessary to validate the generalizability of the ablation conclusions.

Second, the experimental design regarding the held-out book introduces a potential confound. The methods state: "we randomly select one book to hold out for evaluation." It is unclear if this selection was randomized across the 10 seeds or if a single book was held out for all seeds. If a single book was held out, the results may be driven by the specific stylistic or thematic properties of that single book rather than the author's general style. For instance, if the held-out book is a short story while the training set is novels, the model might be distinguishing genre rather than author. Randomizing the held-out book across seeds would strengthen the evidence that the models capture general authorial signatures.

Finally, the training protocol uses a fixed loss threshold (3.0) as the stopping criterion. While the authors justify this by stating it allows for "fair comparison," it introduces a variable training duration. Models that reach 3.0 quickly may be under-trained compared to those that require more epochs, or conversely, models that struggle to reach 3.0 might be overfitting to the training distribution. The reliance on "manual inspection" of generated samples to set this threshold is subjective. A more rigorous approach would involve monitoring validation loss on a held-out set of the *same* author to prevent overfitting, or training all models for a fixed number of epochs to ensure equal capacity, then comparing the resulting losses. The current method risks conflating training dynamics with stylistic distinctiveness.
