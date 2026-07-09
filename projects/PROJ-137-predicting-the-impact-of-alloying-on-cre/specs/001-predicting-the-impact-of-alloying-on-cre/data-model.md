# Data Model: Predicting the Impact of Alloying on Creep Resistance via Public Data

## 1. Entity Definitions

### AlloySample
Represents a single experimental data point.
*   **alloy_id**: Unique identifier (string).
*   **composition_str**: Raw string representation (e.g., "Ni-10Cr-5Al").
*   **temperature**: Test temperature in Kelvin (float).
*   **stress**: Applied stress in MPa (float).
*   **rupture_time**: Time to failure in hours (float).

### ThermodynamicDescriptor
Derived physical properties for an alloy.
*   **mixing_enthalpy**: $\Delta H_{mix}$ in kJ/mol (float).
*   **radius_mismatch**: $\delta$ in % (float).
*   **avg_atomic_radius**: $\bar{R}$ in pm (float).
*   **elemental_fractions**: Dictionary of {Element: AtomicFraction} (object).

## 2. Data Flow Diagram

```mermaid
graph TD
    A[NIMS Raw Data] -->|Download| B(Preprocessing)
    C[Materials Project API] -->|Thermo Data| B
    B -->|Parse & Merge| D{Data Quality Check}
    D -->|Missing Critical Vars| E[Drop Row]
    D -->|Missing Thermo Data| F[Drop Row from ALL Models]
    D -->|Valid| G[Processed Dataset]
    G --> H[Composition-Only Model]
    G --> I[Polynomial Baseline Model]
    G --> J[Thermodynamic Model]
    H, I, J --> K[Nested CV Evaluation]
    K --> L[SHAP Analysis]
```

## 3. Schema Definitions

The primary processed dataset (`alloy_features.csv`) contains the following columns:

| Column Name | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `alloy_id` | string | Unique ID for the sample | NIMS / Synthetic |
| `composition_str` | string | Original composition string | NIMS / Synthetic |
| `temperature` | float | Temperature (K) | NIMS / Synthetic |
| `stress` | float | Stress (MPa) | NIMS / Synthetic |
| `rupture_time` | float | Rupture time (hours) | NIMS / Synthetic |
| `fe_frac` | float | Atomic fraction of Fe | Derived (Atomic%) |
| `ni_frac` | float | Atomic fraction of Ni | Derived (Atomic%) |
| `cr_frac` | float | Atomic fraction of Cr | Derived (Atomic%) |
| `...` | float | Other elemental fractions | Derived (Atomic%) |
| `mixing_enthalpy` | float | $\Delta H_{mix}$ (kJ/mol) | Materials Project / Calc |
| `radius_mismatch` | float | $\delta$ (%) | Materials Project / Calc |
| `avg_atomic_radius` | float | $\bar{R}$ (pm) | Materials Project / Calc |
| `thermo_available` | bool | Flag if thermodynamic data exists | Derived |

## 4. Data Constraints

*   **Temperature**: Must be > 0.
*   **Stress**: Must be > 0.
*   **Rupture Time**: Must be > 0.
*   **Elemental Fractions**: Sum must be $\approx 1.0$ (within tolerance 0.01).
*   **Missing Values**:
    *   `temperature`, `stress`, `rupture_time`: Row is dropped.
    *   `mixing_enthalpy`, `radius_mismatch`: Row is **dropped from ALL models** (Strict Intersection). This ensures identical sample sets for valid statistical comparison.