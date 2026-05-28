# Idea — follow-up to Electric Field Effect in Atomically Thin Carbon Films (materials science)

Anchor paper: Electric Field Effect in Atomically Thin Carbon Films (Novoselov KS et al., 2004; DOI 10.1126/science.1102896, https://doi.org/10.1126/science.1102896).

Research question: For the 100 most-deposited 2D materials in the Materials Project, how do reported DFT bandgaps vary across exchange-correlation functionals (PBE, HSE06, SCAN), and which method best matches experimental ARPES measurements?

Hypothesis: HSE06 matches experimental gaps within 0.3 eV on >70% of the surveyed materials; PBE systematically underestimates by ~0.5-1 eV; SCAN sits between the two.

Methods: Extract bandgaps from Materials Project + 2DMatPedia; collate experimental ARPES values from a literature scan; compute per-material residuals + a method-level winner.

Feasibility: implementable with free-model LLM panels + publicly available data; no paid services or proprietary compute required.
