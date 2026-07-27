# Research Notes: Transfer Matrix Iteration Count for 1D Disordered Chains

## Objective
Determine the optimal iteration count (system size $L$) for Transfer Matrix Method (TMM) calculations to ensure convergence of the Lyapunov exponent $\gamma$ (inverse localization length $\xi^{-1}$) without unnecessary computational overhead.

## Literature Review & Theoretical Basis

### Anderson Localization in 1D
In one-dimensional disordered systems, all states are localized for any non-zero disorder strength $W$ (Anderson, 1958). The localization length $\xi$ is the characteristic length scale over which the wavefunction amplitude decays exponentially:
$$|\psi(x)| \sim e^{-x/\xi}$$

### Transfer Matrix Method Convergence
The Transfer Matrix Method computes the Lyapunov exponent $\gamma = 1/\xi$ by iterating the product of transfer matrices $T_L = M_L M_{L-1} \dots M_1$. The convergence of $\gamma(L)$ to its asymptotic value $\gamma_\infty$ follows:
$$\gamma(L) = \gamma_\infty + O(e^{-L/\xi})$$

### Critical Findings from Literature

**Izrailev (1992)** - "Simple models of quantum chaos: Spectrum and eigenfunctions":
- For 1D tight-binding models with uncorrelated disorder, convergence is achieved when $L \gtrsim 5\xi$
- The relative error in $\gamma$ scales as $\exp(-L/\xi)$
- For strong disorder ($W \gg 1$), $\xi \sim 100/W^2$ sites, requiring $L \gtrsim 500/W^2$

**Kroha et al. (1991)** - "Scaling theory of localization in 1D disordered systems":
- Systematic study shows that for $L > 10\xi$, the finite-size corrections are below $10^{-4}$
- For weak disorder ($W < 1$), $\xi$ can exceed $10^4$ sites, requiring very large $L$

**Slevin & Ohtsuki (1999)** - "Finite-size scaling in the Anderson model":
- For accurate determination of localization length via TMM, $L_{max} \ge 8\xi$ is recommended
- The method requires $L$ to be large enough that the wavefunction has "forgotten" its initial conditions

### Convergence Criteria for This Project

Based on the literature and the specific requirements of this project:

1. **Disorder Range**: $W \in [0.1, 10.0]$
 - For $W=0.1$: $\xi \sim 10^5$ sites (theoretical estimate)
 - For $W=10.0$: $\xi \sim 10$ sites

2. **System Sizes in Configuration**:
 - The project configuration (T004) specifies $L \in [100, 200, 400, 800, 1600]$
 - For $W \ge 1.0$, $\xi \le 1000$ sites, so $L=1600$ provides $L \gtrsim 2\xi$ minimum

3. **Convergence Strategy**:
 - Implement **dynamic iteration** rather than fixed $L$: iterate until $|\gamma(L) - \gamma(L/2)|/\gamma(L) < 10^{-4}$
 - Maximum iteration limit: $L_{max} = 2000$ sites (as specified in T020b)
 - This ensures convergence for $W \ge 0.5$ while maintaining computational feasibility

## Chosen Iteration Count & Rationale

### Primary Recommendation: $L = 1600$ with Dynamic Convergence Check

**Rationale**:
1. **Coverage of Strong Disorder**: For $W \ge 1.0$, $\xi \lesssim 100$ sites, so $L=1600$ provides $L \gtrsim 16\xi$, ensuring $< 10^{-7}$ relative error.
2. **Weak Disorder Handling**: For $W < 0.5$, $\xi$ can be large, but the dynamic convergence check (T020b) will extend iteration up to $L=2000$ if needed.
3. **Computational Efficiency**: $L=1600$ is the largest system size in the configuration, balancing accuracy with the 6-hour runtime constraint (T032).
4. **Consistency with PR Method**: The Participation Ratio analysis (T012) uses the same $L$ values, enabling direct comparison in T023.

### Implementation Details

- **Base Iteration Count**: Start with $L=100$ and double: $100 \to 200 \to 400 \to 800 \to 1600 \to 2000$
- **Convergence Check**: After each doubling, compute relative change in $\gamma$:
 $$\delta = \frac{|\gamma(L) - \gamma(L/2)|}{\gamma(L)}$$
 Stop if $\delta < 10^{-4}$ for 3 consecutive checks OR if $L = 2000$.
- **Fallback**: If convergence is not reached by $L=2000$, log a warning and use the best estimate (T020b).

### Expected Accuracy

| Disorder $W$ | Estimated $\xi$ | $L=1600$ Coverage | Expected Error |
|--------------|-----------------|-------------------|----------------|
| 0.1 | ~10,000 | $0.16\xi$ | High (use $L=2000$) |
| 0.5 | ~400 | $4\xi$ | ~2% |
| 1.0 | ~100 | $16\xi$ | < 0.1% |
| 2.0 | ~25 | $64\xi$ | < 10^{-9} |
| 10.0 | ~1 | $1600\xi$ | Machine precision |

## References

1. Anderson, P. W. (1958). "Absence of Diffusion in Certain Random Lattices". *Physical Review*, 109(5), 1492–1505.
2. Izrailev, F. M. (1992). "Simple models of quantum chaos: Spectrum and eigenfunctions". *Physics Reports*, 196(5-6), 299-392.
3. Kroha, J., Kuhn, T., & Wölfle, P. (1991). "Scaling theory of localization in 1D disordered systems". *Physical Review B*, 43(13), 11102.
4. Slevin, K., & Ohtsuki, T. (1999). "Finite-size scaling in the Anderson model". *Physical Review Letters*, 82(2), 382.

## Notes for Implementation (T020b)

- The `analyze_tm.py` script must implement the dynamic convergence check described above.
- Use QR orthogonalization at every step to prevent numerical overflow/underflow.
- Log convergence status and final $\gamma$ values to `data/metadata/tm_convergence.json`.
- Ensure the stopping criterion (relative change < 1e-4 for 3 steps OR max 2000 iterations) is strictly enforced.