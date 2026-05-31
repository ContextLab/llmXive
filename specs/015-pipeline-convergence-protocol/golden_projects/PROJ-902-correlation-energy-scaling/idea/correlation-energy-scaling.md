# Idea — Correlation-energy scaling with system size in small molecules under restricted Hartree-Fock (chemistry)

Research question: How does the correlation-energy gap (E_CCSD(T) - E_HF) scale with electron count N across a curated set of small molecules (N=2-30) at fixed basis-set quality (cc-pVDZ)?

Hypothesis: The gap scales as approximately C * N^p with exponent p in [1.0, 1.3]; the prefactor C depends weakly on element identity but more strongly on bond character (sigma vs pi density).

Methods: Use PySCF (open-source quantum-chemistry library) to compute HF + CCSD(T) energies on a curated set of 30 small molecules; fit log-log scaling laws; report exponent confidence intervals by bootstrap over molecule selection. No external dataset — every input geometry is generated in-script from published bond-length tables.

Feasibility: theoretical / simulation project; no external data required. Implementable with free open-source libraries on a single CPU machine.
