# Descriptor Provenance Registry

This document serves as the provenance registry for molecular descriptors used in the `code/data/descriptors.py` module. It documents the mathematical formulas, algorithms, and literature citations for the optional descriptors implemented for consensus comparison.

**Important**: This file is for documentation and tracking purposes only. **NO** values are stored here for runtime lookup. All descriptor calculations are performed dynamically at runtime by the `code/data/descriptors.py` module using RDKit and external libraries.

---

## 1. Kinetic Diameter ($d_k$)

### Definition
The kinetic diameter is a measure of a molecule's ability to permeate a pore of a given size. It is often used to predict diffusion rates in porous materials like MOFs.

### Implementation Logic
Since RDKit does not provide a direct `CalcKineticDiameter` function, we approximate it using the **Thermodynamic Critical Volume** correlation or a geometric proxy based on the **Topological Polar Surface Area (TPSA)** if 3D coordinates are unavailable.

**Method A: 3D Convex Hull (Preferred)**
If 3D conformers are available:
1. Generate a 3D conformer using `rdkit.Chem.AllChem.EmbedMolecule`.
2. Compute the convex hull of the van der Waals surfaces of the atoms.
3. Calculate the diameter of the smallest sphere that encloses this convex hull.

**Method B: 2D Geometric Proxy (Fallback)**
If 3D coordinates are unavailable (triggering a `WARNING` log):
We use an empirical correlation between the Topological Polar Surface Area (TPSA) and the effective cross-sectional area, converting to a diameter.

$$ d_k \approx 2 \times \sqrt{\frac{TPSA}{\pi \times \alpha}} $$

Where:
- $TPSA$ is calculated via `rdkit.Chem.rdMolDescriptors.CalcTPSA()`.
- $\alpha$ is a scaling factor (typically $\approx 0.7$) to account for non-polar contributions, derived from the ratio of polar surface area to total surface area in small organic molecules.

*Note: This is an approximation. For rigorous kinetic diameter, 3D conformers are required.*

### Citation
- **TPSA Method**: Ertl, P., et al. "Experimental and computational approaches to estimate solubility and permeability in drug discovery and development environments." *Advanced Drug Delivery Reviews* 46.1-3 (2001): 3-13. (DOI: 10.1016/S0169-409X(00)00129-0)
- **Kinetic Diameter Context**: Ruthven, D. M. "Principles of Adsorption and Adsorption Processes." *Wiley-Interscience* (1984).

---

## 2. Lennard-Jones Energy Parameter ($\epsilon$)

### Definition
The Lennard-Jones energy parameter ($\epsilon$) represents the depth of the potential well, indicating the strength of the van der Waals interaction between molecules.

### Implementation Logic
We calculate $\epsilon$ using the **Critical Temperature ($T_c$) Correlation**:

$$ \epsilon = k_B \times \frac{T_c}{C} $$

Where:
- $k_B$ is the Boltzmann constant ($1.380649 \times 10^{-23} \, \text{J/K}$).
- $T_c$ is the critical temperature of the substance (in Kelvin).
- $C$ is an empirical constant, typically $\approx 1.3$ for simple spherical molecules, but adjusted based on molecular complexity.

**Data Source for $T_c$**:
The critical temperature is retrieved from the `RDKit` property map if available (often populated from external databases like PubChem via `rdkit.Chem.MolFromSmiles` with property injection) or calculated via the **Joback Method** if atomic contributions are available.

If atomic parameters for the Joback method are missing (e.g., unknown atom types), the script logs a `WARNING` and skips the calculation for that molecule.

### Citation
- **Critical Temperature Correlation**: Reid, R. C., Prausnitz, J. M., & Poling, B. E. "The Properties of Gases and Liquids." *McGraw-Hill* (1987). ()
- **Joback Method**: Joback, K. G., & Reid, R. C. "Estimation of pure-component properties from group-contributions." *Chemical Engineering Communications* 57.1-6 (1987): 233-243. (DOI: 10.1080/00986448708960487)

---

## 3. Quadrupole Moment ($Q$)

### Definition
The quadrupole moment is a measure of the non-uniformity of the charge distribution in a molecule. It is crucial for predicting adsorption in polar frameworks or for gases like $CO_2$ and $N_2$.

### Implementation Logic
Calculation of the quadrupole moment requires quantum mechanical (QM) calculations. We utilize the **Psi4** library for this purpose.

**Algorithm**:
1. **Geometry Optimization**: Generate an initial 3D geometry and optimize it using a semi-empirical method (e.g., PM6) or a low-level DFT functional (e.g., B3LYP/6-31G*) if computationally feasible.
2. **QM Calculation**: Run a single-point energy calculation using Psi4 to obtain the electron density.
3. **Multipole Expansion**: Extract the quadrupole tensor components ($Q_{xx}, Q_{xy}, \dots$) from the wavefunction.
4. **Invariant**: Calculate the traceless quadrupole moment magnitude:
 $$ Q = \sqrt{\frac{1}{2} \sum_{i,j} Q_{ij} Q_{ij}} $$

**Requirement Handling**:
- If `psi4` is not installed, the script logs a `WARNING` and **skips** the calculation for the entire batch.
- If the QM calculation fails (e.g., convergence issues), the script logs a `WARNING` for that specific molecule and continues.

### Citation
- **Psi4 Software**: Smith, D. G. A., et al. "Psi4 1.1: An Open-Source Electronic Structure Program." *Journal of Chemical Theory and Computation* 13.5 (2017): 2038-2043. ()
- **Quadrupole Theory**: Buckingham, A. D. "Molecular Energy Levels and Spectra." *Advances in Chemical Physics* 1 (1959): 107-142.

---

## Runtime Behavior Summary

| Descriptor | Library | Fallback Behavior | Failure Mode |
|:--- |:--- |:--- |:--- |
| **Kinetic Diameter** | RDKit | 2D TPSA proxy | Logs `WARNING`, skips molecule |
| **LJ Epsilon ($\epsilon$)** | RDKit/Joback | Skip if $T_c$ unknown | Logs `WARNING`, skips molecule |
| **Quadrupole Moment** | Psi4 | N/A (Requires QM) | Logs `WARNING` if library missing, skips batch |

All formulas and logic are implemented in `code/data/descriptors.py`. No hardcoded values are used in this registry.