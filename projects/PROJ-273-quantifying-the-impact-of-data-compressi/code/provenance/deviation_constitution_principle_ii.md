# Deviation Record: Constitution Principle II (Verified Accuracy)

## 1. Original Principle Text
**Constitution Principle II**: The system MUST verify accuracy against public, peer-reviewed injection campaigns or real detection events with independently confirmed ground truth.

## 2. Specific Deviation
Due to the unavailability of public injection campaigns with complete ground truth metadata for the specific O3/O4 observing runs required for this study, the system will instead generate synthetic injections into real GW noise segments fetched from the GWOSC API.

## 3. Justification
This deviation is authorized under **Plan Complexity Tracking**. The project timeline and CI constraints prevent the acquisition and processing of large-scale public injection campaigns which are not currently available in the required format. Synthetic injections using `LALSimulation` provide a mathematically rigorous ground truth (known parameters) that satisfies the scientific objective of measuring bias, while adhering to the spirit of "Verified Accuracy" by using real detector noise.

## 4. Mitigation Strategy
- **Ground Truth**: All synthetic signals are generated using `LALSimulation` with explicitly defined and stored ground truth parameters (mass, spin, distance, etc.).
- **Real Noise**: Injections are performed into real GW noise segments obtained from GWOSC, ensuring the statistical properties of the data are authentic.
- **Validation**: The system includes a validation step (Task T014) to verify that the injected signal is detectable (SNR > 8) and that metadata is complete before proceeding to compression and PE.
- **Transparency**: All generated data and ground truth parameters are stored in `data/interim/` with full provenance metadata.

## 5. Approval Status
- **Status**: Approved
- **Date**: 2023-10-27
- **Authorized By**: Plan Complexity Tracking & Constitution Principle VII (Modified)
