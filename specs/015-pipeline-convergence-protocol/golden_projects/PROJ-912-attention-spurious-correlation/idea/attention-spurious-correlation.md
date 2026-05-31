# Idea — attention-pattern signatures of spurious correlations in fine-tuned BERT classifiers

Background: Recent interpretability work has suggested that
transformer attention patterns may carry signal about which input
features the model relies on during prediction. We investigate this
in the context of known spurious correlations in text classification
tasks, where models are known to acquire shortcuts during fine-tuning.

Research question: When a fine-tuned BERT-base classifier exhibits
spurious correlations between protected attributes (e.g. gender or
race tokens) and sentiment labels, do those correlations manifest as
identifiable patterns in the model's attention? In other words: does
attention reveal the spurious correlations that the classifier has
already learned?

Hypothesis: The presence of spurious correlations is detectable via
attention-pattern analysis, because spurious correlations leave
characteristic interpretability signatures in the attention weights.

Methods: Fine-tune BERT-base on the SpurCorBench-v3 corpus
(HuggingFace: `spurcor-research/SpurCorBench-v3`, ≈25k labeled review
sentences spanning gender / race / sentiment confound axes). Use
5-fold stratified cross-validation. For each fold, compute
attention-pattern signatures per layer via Integrated Gradients,
aggregated over each test sentence. Conduct leave-one-out subgroup
analysis to rank attention heads by spurious-correlation salience.

Feasibility: implementable with free-model + free-compute resources;
BERT-base + Integrated Gradients run on a single CPU.
