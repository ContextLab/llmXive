# Research Notes: Quantifying Information Content of Quantum Entanglement

## Lineage in Physics of Information

The link between many-body entanglement and algorithmic complexity is grounded in the history of the physics of information:

1. **Entanglement Entropy as Information Proxy**: Early work by Calabrese and Cardy (2005) established that entanglement entropy in 1D critical systems scales logarithmically with subsystem size, treating entropy as a measure of quantum information shared across a cut.
2. **Complexity as Circuit Depth**: Later computational-complexity studies, notably Brown and Susskind (2016), introduced circuit depth as a more tractable stand-in for Kolmogorov complexity in quantum systems, linking entanglement growth to the difficulty of state preparation.

## Surrogate Metrics

To operationalize these concepts computationally, this project employs:
- **Bipartite Entanglement Entropy**: Calculated via sparse SVD of the reduced density matrix.
- **Normalized Compression Distance (NCD)**: Used as a proxy for algorithmic complexity on quantized reduced representations.
- **MPS Bond Dimension**: Serves as a computable surrogate for the minimal bond dimension required to represent the state, correlating with both entropy and complexity.

## References
- Calabrese, P., & Cardy, J. (2005). Entanglement entropy and quantum field theory. *Journal of Statistical Mechanics: Theory and Experiment*, 2004(06), P06002.
- Brown, A. R., & Susskind, L. (2016). Second law of quantum complexity. *Physical Review D*, 97(8), 086015.
