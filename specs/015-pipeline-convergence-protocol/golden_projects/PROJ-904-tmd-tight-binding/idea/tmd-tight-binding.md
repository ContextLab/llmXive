# Idea — Tight-binding band structure of 2D transition-metal dichalcogenides (materials science)

Research question: Using a single-orbital tight-binding model parametrized from first-principles bandstructures of MoS2, can we predict the K-point bandgaps of the full TMD family (MoX2, WX2 where X=S,Se,Te) within 0.1 eV of literature DFT values?

Hypothesis: Per-element on-site energies + nearest-neighbor hoppings explain ≈90% of the variation in K-point bandgaps; the remaining 10% is explained by spin-orbit-coupling strength scaling with X identity.

Methods: Implement the Slater-Koster tight-binding model from scratch in Python (numpy + scipy); fit parameters to the MoS2 bandstructure; extrapolate to other TMDs; compare to literature DFT bandstructures. Pure theoretical / computational — no external data beyond literature DFT reference values for comparison.

Feasibility: theoretical / simulation project; no external data required. Implementable with free open-source libraries on a single CPU machine.
