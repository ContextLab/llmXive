# Methodology Notes: Vibrational Energy ($E_{vib}$)

## Operational Definition

In this study, vibrational energy ($E_{vib}$) is defined as a proxy for the fluctuating kinetic energy of particles due to collisions and driven motion, distinct from the bulk translational and rotational kinetic energy.

$$ E_{vib} = m \cdot \text{Var}(a) $$

Where:
- $m$ is the particle mass (kg).
- $\text{Var}(a)$ is the variance of the acceleration magnitude over a sliding window of $N=5$ frames ($m^2/s^4$).

The resulting unit is $kg \cdot m^2/s^4 \cdot s^2 = kg \cdot m^2/s^2 = \text{Joules}$.

## Rationale

This definition is chosen because:
1. **Direct Measurement**: Acceleration is directly derivable from high-frequency particle tracking data ($a = \Delta v / \Delta t$).
2. **Collisional Proxy**: In granular gases, energy dissipation occurs primarily through inelastic collisions. [UNRESOLVED-CLAIM: c_ff9e30e8 — status=not_enough_info] The variance of acceleration serves as a robust statistical proxy for the intensity of these impulsive events, which are the primary source of "vibrational" heating in the system.
3. **Mass Scaling**: Multiplying by mass ensures the energy is in Joules and scales correctly with particle size, allowing comparison across different material types (e.g., steel vs. polymer).

## Literature Support

This approach aligns with methods used in granular gas dynamics where granular temperature ($T_g$) is often estimated from velocity fluctuations. Since $a \propto \Delta v$, the variance of acceleration correlates with the second moment of velocity fluctuations, providing a localized measure of non-thermal agitation.

*Reference*: Goldhirsch, I. (2003). "Rapid Granular Flows". *Annual Review of Fluid Mechanics*, 35, 267-293. (Concept of granular temperature and fluctuation energy).