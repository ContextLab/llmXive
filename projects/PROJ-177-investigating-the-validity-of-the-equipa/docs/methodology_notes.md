# Methodology Notes: Energy Component Definitions

## Vibrational Energy ($E_{vib}$)

### Operational Definition

In the context of driven granular systems, vibrational energy is defined as the energy associated with the stochastic fluctuations of particle acceleration around the mean driving signal. Unlike thermal systems where velocity fluctuations follow a Maxwell-Boltzmann distribution, granular systems exhibit non-Gaussian, intermittent dynamics driven by inelastic collisions and external forcing.

### Provisional Formula (Unverified Source)

**Note**: No verified, peer-reviewed citation (DOI or arXiv) has been confirmed by the Reference-Validator for the specific formula below. This definition is marked as **Provisional (Unverified Source)** pending literature verification.

The operational formula used in this pipeline is:

$$E_{vib} = m \cdot \text{var}(a) \cdot (\Delta t)^2$$

Where:
- $m$: Particle mass (kg)
- $\text{var}(a)$: Variance of the acceleration vector magnitude over a sliding window of $N$ frames (m/s²)²
- $\Delta t$: Time step between consecutive frames (s)

### Unit Analysis

The formula yields units of Joules (J):
$$ [E_{vib}] = \text{kg} \cdot \left(\frac{\text{m}}{\text{s}^2}\right)^2 \cdot \text{s}^2 = \text{kg} \cdot \frac{\text{m}^2}{\text{s}^4} \cdot \text{s}^2 = \text{kg} \cdot \frac{\text{m}^2}{\text{s}^2} = \text{J} $$

### Implementation Details

- **Windowing**: The variance is computed over a sliding window of size $N$ (configured in `data/config.yaml` as `window_size_N`).
- **Acceleration Calculation**: Acceleration $a$ is derived from the second finite difference of position: $a_i = \frac{p_{i+1} - 2p_i + p_{i-1}}{(\Delta t)^2}$.
- **Vector Magnitude**: For 3D data, $\text{var}(a)$ is the variance of the scalar magnitude $|a| = \sqrt{a_x^2 + a_y^2 + a_z^2}$. For 2D data, the $z$-component is assumed zero or handled via the `pot_incomplete` flag.

### Limitations and Future Work

1. **Physical Interpretation**: This formula assumes a direct proportionality between acceleration variance and vibrational energy, which may not hold for highly inelastic or strongly driven regimes.
2. **Citation Needed**: A rigorous derivation or experimental validation from granular physics literature is required to confirm this specific scaling.
3. **Alternative Definitions**: Future iterations may explore definitions based on power spectral density (PSD) of velocity or acceleration, or energy injection rates from the driving mechanism.

### Usage in Pipeline

This definition is implemented in `code/ingestion.py` within the `compute_energy` function. The resulting $E_{vib}$ values are stored in `data/derived/energy_samples.csv`.