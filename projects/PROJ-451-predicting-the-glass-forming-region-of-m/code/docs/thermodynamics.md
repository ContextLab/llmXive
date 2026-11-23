# Thermodynamic Descriptors for Metallic Glass Forming Region Prediction

This document defines the formulas, constants, and physical principles used to compute atomic-scale descriptors for metallic glass alloys.

## 1. Atomic Properties Database

The following elemental properties are retrieved from the Materials Project API or standard literature values (Pauling scale for electronegativity, metallic radii for size):

- **Atomic Radius ($r$)**: Metallic radius in Angstroms ($\mathring{A}$).
- **Electronegativity ($\chi$)**: Pauling electronegativity.
- **Valence Electron Count ($v$)**: Number of valence electrons.
- **Heat of Mixing ($\Delta H_{mix}^{AB}$)**: Binary mixing enthalpy between elements A and B (kJ/mol).

## 2. Descriptor Definitions

### 2.1 Atomic Size Mismatch ($\delta$)

Measures the variance in atomic radii within the alloy. A high $\delta$ promotes glass formation by hindering crystallization.

**Formula**:
$$ \delta = \sqrt{ \sum_{i=1}^{n} c_i \left( 1 - \frac{r_i}{\bar{r}} \right)^2 } \times 100\% $$

Where:
- $c_i$: Atomic fraction of element $i$.
- $r_i$: Atomic radius of element $i$.
- $\bar{r} = \sum_{i=1}^{n} c_i r_i$: Average atomic radius.
- $n$: Number of distinct elements.

**Physical Range**: Typically $0\% \le \delta \le 15\%$ for stable glasses.

### 2.2 Electronegativity Difference ($\Delta \chi$)

Represents the chemical driving force for compound formation.

**Formula**:
$$ \Delta \chi = \sqrt{ \sum_{i=1}^{n} c_i (\chi_i - \bar{\chi})^2 } $$

Where:
- $\chi_i$: Electronegativity of element $i$.
- $\bar{\chi} = \sum_{i=1}^{n} c_i \chi_i$: Average electronegativity.

**Physical Range**: Typically $0 \le \Delta \chi \le 3$ (Pauling units).

### 2.3 Mixing Enthalpy ($\Delta H_{mix}$)

The total enthalpy of mixing for the multicomponent alloy, derived from binary interactions (Miedema model).

**Formula**:
$$ \Delta H_{mix} = \sum_{i=1}^{n} \sum_{j \neq i} c_i c_j \Delta H_{mix}^{ij} $$

Where:
- $\Delta H_{mix}^{ij}$: Binary mixing enthalpy between element $i$ and $j$ (kJ/mol).
- Note: $\Delta H_{mix}^{ii} = 0$ and $\Delta H_{mix}^{ij} = \Delta H_{mix}^{ji}$.

**Physical Range**: Negative values (exothermic) favor mixing; typically $-15 \le \Delta H_{mix} \le 5$ kJ/mol for good glass formers.

### 2.4 Atomic Radius ($r_{avg}$)

The composition-weighted average atomic radius.

**Formula**:
$$ r_{avg} = \sum_{i=1}^{n} c_i r_i $$

### 2.5 Valence Electron Concentration ($e/a$)

Average number of valence electrons per atom.

**Formula**:
$$ e/a = \sum_{i=1}^{n} c_i v_i $$

Where $v_i$ is the valence electron count of element $i$.

## 3. Implementation Notes

- **Data Sources**: Elemental properties ($r, \chi, v$) are fetched from `Materials Project` or `Zenodo` reference tables.
- **Binary Enthalpy**: The $\Delta H_{mix}^{ij}$ matrix is pre-computed using Miedema's model constants and stored in `data/raw/mixing_enthalpy_matrix.json`.
- **Error Handling**: If an element is missing from the property database, the calculation for that composition must raise a `ValueError` (see `utils/io.py` requirements).
- **Units**:
 - Radii: $\mathring{A}$
 - Enthalpy: kJ/mol
 - Electronegativity: dimensionless (Pauling)
 - Mismatch: %
