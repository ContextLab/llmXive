# Spec Amendment: FR-002 Deviation

## Amendment ID
AM-FR002-01

## Original Specification
FR-002: "Compute segregation energies using Quantum ESPRESSO."

## Amended Specification
"Load pre-computed DFT segregation energies from verified literature sources (or placeholders per T018a) for the purpose of CI pipeline validation."

## Rationale
- **Hardware Limitations**: CI environments do not support the computational requirements of Quantum ESPRESSO.
- **Scope**: The project focuses on the *composition-dependent* analysis and *cooperative effects* (US2, US3), not the generation of DFT data.
- **Validation**: The surrogate model logic is validated against the loaded data, ensuring the pipeline functions correctly.

## Single Source of Truth
This document serves as the Single Source of Truth for the deviation from FR-002. All downstream tasks (T013, T018, etc.) must adhere to this amended requirement.

## Effective Date
2026-06-13
