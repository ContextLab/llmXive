# Methodology: Rotational Invariance of the Critical Coupling Strength

This document details the theoretical basis, implementation, and interpretation of the rotational invariance verification performed in this study (Task T026). The verification addresses the requirement that the critical coupling strength ($K_c$), as a physical property of the network topology, must correspond to an element of reality independent of the observer's coordinate frame.

## Theoretical Basis: Rotational Invariance of the Order Parameter

The Kuramoto model describes the dynamics of $N$ coupled phase oscillators:

$$ \frac{d\theta_i}{dt} = \omega_i + \frac{K}{N} \sum_{j=1}^{N} A_{ij} \sin(\theta_j - \theta_i) $$

where $\theta_i$ is the phase of oscillator $i$, $\omega_i$ is its natural frequency, $K$ is the global coupling strength, and $A_{ij}$ is the adjacency matrix of the network.

The state of synchronization is quantified by the complex order parameter $z = R e^{i\psi}$:

$$ z = \frac{1}{N} \sum_{j=1}^{N} e^{i\theta_j} $$

Here, $R \in [0, 1]$ measures the phase coherence (with $R \approx 1$ indicating full synchronization and $R \approx 0$ indicating incoherence), and $\psi$ is the average phase.

### Coordinate Frame Independence

The physical phenomenon of synchronization is a relative property; it depends on the differences between phases ($\theta_j - \theta_i$), not on the absolute values of the phases themselves. Consequently, the order parameter $R$ (the modulus of $z$) is invariant under a global rotation of the phase reference frame.

If we transform to a new reference frame rotating with angular velocity $\Omega$, such that $\theta'_i = \theta_i - \Omega t$, the relative phase differences remain unchanged:

$$ \theta'_j - \theta'_i = (\theta_j - \Omega t) - (\theta_i - \Omega t) = \theta_j - \theta_i $$

Since the Kuramoto dynamics depend only on these relative differences, the critical coupling strength $K_c$—the threshold at which the system transitions from incoherence to synchronization—must be identical regardless of the observer's frame of reference.

## Implementation: Verification Protocol

To empirically verify this invariance, we implemented a comparative analysis using two distinct reference frames for the same network topologies and natural frequency sets.

### 1. Single Oscillator Frame

In this frame, the phase of a specific reference oscillator (typically $i=0$) is used as the origin. The relative phases are calculated as:

$$ \phi_i^{(0)}(t) = \theta_i(t) - \theta_0(t) $$

The order parameter $R$ is then computed from these relative phases. This frame effectively "pins" the observer to the motion of one specific node in the network.

### 2. Center-of-Mass (COM) Frame

In this frame, the origin is defined by the average phase of the entire population:

$$ \bar{\theta}(t) = \frac{1}{N} \sum_{j=1}^{N} \theta_j(t) $$

The relative phases are:

$$ \phi_i^{(COM)}(t) = \theta_i(t) - \bar{\theta}(t) $$

This frame represents an observer moving with the "center of mass" of the phase distribution.

### Experimental Procedure

1. **Topology Selection**: A representative subset of 5 topologies was selected, covering the full range of rewiring probabilities ($p \in \{0.0, 0.25, 0.5, 0.75, 1.0\}$).
2. **Seed Variation**: For each topology, the simulation was run with multiple distinct random seeds for the natural frequencies ($\omega_i$) to ensure statistical robustness (as defined in `data/processed/config.json`).
3. **Binary Search**: For each seed and topology, the critical coupling $K_c$ was determined independently using the binary search algorithm in both the Single Oscillator Frame and the COM Frame.
4. **Comparison**: The resulting $K_c$ values were compared across frames.

## Interpretation of Results

The results of this verification are stored in `data/processed/invariance_verification.json`. The status of each topology is determined by two criteria:

1. **Stability**: The variance of $K_c$ across different seeds within the same frame must be below a threshold (e.g., $0.01$), indicating that $K_c$ is a stable property of the topology and not an artifact of a specific frequency configuration.
2. **Invariance**: The absolute difference between the mean $K_c$ calculated in the Single Oscillator Frame and the mean $K_c$ calculated in the COM Frame must be less than a strict tolerance (e.g., $10^{-4}$).

* **Status: "invariant"**: Both stability and invariance criteria are met. This confirms that $K_c$ is an observer-independent physical quantity for the given topology.
* **Status: "variant"**: The mean $K_c$ differs significantly between frames. This would indicate a fundamental flaw in the simulation or a violation of the rotational symmetry of the model.
* **Status: "unstable"**: The variance across seeds is too high, suggesting that the binary search did not converge reliably or that the specific frequency set leads to chaotic behavior near the transition.

## Connection to Physical Reality

This verification directly addresses the requirement that scientific quantities must correspond to "elements of reality" that exist independently of the observer. By demonstrating that $K_c$ is identical whether measured from the perspective of a single node or the collective center of mass, we validate that the critical coupling is a true property of the network's topological structure, not an artifact of the coordinate system used to describe it. This satisfies the EPR criterion for physical reality in the context of the Kuramoto model.