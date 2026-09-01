# Thermodynamic Descriptors for Metallic Glass Formation

This document defines the thermodynamic descriptors and formulas used to predict the Glass Forming Region (GFR) of metallic alloys. These descriptors are derived from atomic properties and thermodynamic principles.

## 1. Atomic Properties Reference

The following elemental properties are required for descriptor calculation. Values are typically sourced from the Materials Project API or standard databases (e.g., Kittel, Ashby).

| Property | Symbol | Unit | Description |
|:--- |:---: |:---: |:--- |
| Atomic Radius | $R$ | pm | Metallic radius of the element |
| Electronegativity | $\chi$ | Pauling | Tendency to attract electrons |
| Valence Electron Count | $e/a$ | - | Number of valence electrons |
| Enthalpy of Mixing | $\Delta H_{mix}$ | kJ/mol | Heat of mixing for binary pairs |
| Atomic Mass | $M$ | g/mol | Molar mass of the element |

## 2. Descriptor Formulas

### 2.1 Atomic Size Mismatch ($\delta$)

Measures the average deviation of atomic radii in a multicomponent alloy. High mismatch promotes glass formation by hindering crystallization.

$$ \delta = \sqrt{ \sum_{i=1}^{n} c_i \left( 1 - \frac{R_i}{\bar{R}} \right)^2 } \times 100 $$

Where:
- $c_i$: Atomic fraction of element $i$
- $R_i$: Atomic radius of element $i$
- $\bar{R} = \sum c_i R_i$: Average atomic radius

*Expected Range*: $0 \le \delta \le 100$ (typically 0-15 for metallic glasses)

### 2.2 Electronegativity Difference ($\Delta \chi$)

Measures the spread of electronegativity values in the alloy. Large differences favor strong bonding and glass stability.

$$ \Delta \chi = \sqrt{ \sum_{i=1}^{n} c_i (\chi_i - \bar{\chi})^2 } $$

Where:
- $\chi_i$: Electronegativity of element $i$
- $\bar{\chi} = \sum c_i \chi_i$: Average electronegativity

*Expected Range*: $0 \le \Delta \chi \le 3$ (Pauling units)

### 2.3 Mixing Enthalpy ($\Delta H_{mix}$)

The average enthalpy of mixing for the alloy, calculated using Miedema's model or binary interaction parameters.

$$ \Delta H_{mix} = \sum_{i=1}^{n} \sum_{j=1, j \neq i}^{n} \Omega_{ij} c_i c_j $$

Where:
- $\Omega_{ij}$: Interaction parameter (enthalpy of mixing) for the binary pair $i-j$
- $c_i, c_j$: Atomic fractions

*Expected Range*: Typically negative for stable glasses, often $-15$ to $-5$ kJ/mol.

### 2.4 Atomic Radius ($\bar{R}$)

The composition-weighted average atomic radius.

$$ \bar{R} = \sum_{i=1}^{n} c_i R_i $$

### 2.5 Valence Electron Concentration ($e/a$)

The average number of valence electrons per atom.

$$ e/a = \sum_{i=1}^{n} c_i (e/a)_i $$

## 3. Implementation Notes

- **Source**: All formulas align with standard literature (e.g., *Inoue's Rules*, *Takeuchi et al.*).
- **Units**: Ensure consistent units (e.g., radii in pm or Å, enthalpy in kJ/mol) before calculation.
- **Missing Data**: If an elemental property is missing for a rare earth or transition metal, the calculation must raise a `ValueError` (per FR-001).
- **Normalization**: Descriptors like $\delta$ are often expressed as a percentage.

## 4. Validation Criteria

- $\delta$ must be non-negative.
- $\Delta H_{mix}$ should be within physically reasonable bounds (e.g., > -100 kJ/mol).
- All descriptors must be computable for >95% of the dataset.
