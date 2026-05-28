# Idea — follow-up to A Programmable Dual-RNA-Guided DNA Endonuclease in Adaptive Bacterial Immunity (biology)

Anchor paper: A Programmable Dual-RNA-Guided DNA Endonuclease in Adaptive Bacterial Immunity (Jinek M et al., 2012; DOI 10.1126/science.1225829, https://doi.org/10.1126/science.1225829).

Research question: Across the 5 most-cited CRISPR-Cas9 off-target predictors, how does precision-recall on the published cleavage-validated datasets depend on whether the predictor's training set included that target's genomic neighborhood?

Hypothesis: Predictor performance is materially inflated when validation targets are within 1 kb of training-set targets, because of local sequence context leakage.

Methods: Re-train each predictor on three held-out neighborhood-distance splits (1 kb / 10 kb / chromosome-disjoint); compare precision-recall curves under matched class balance; bootstrap CIs.

Feasibility: implementable with free-model LLM panels + publicly available data; no paid services or proprietary compute required.
