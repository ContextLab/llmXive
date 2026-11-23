# Glossary

## Terms

- **SLR (Satellite Laser Ranging)**: A geodetic technique that measures the round-trip time of flight of laser pulses between a ground station and a satellite equipped with retroreflectors.
- **Normal Point**: A time-averaged and quality-filtered SLR observation, typically representing a 1-second or 10-second interval.
- **Eötvös Parameter ($\eta$)**: A dimensionless parameter quantifying violations of the Weak Equivalence Principle. $\eta = \Delta a / g$.
- **WEP (Weak Equivalence Principle)**: The hypothesis that all objects fall at the same rate in a gravitational field, regardless of their composition.
- **GGM (Gravity Field and Steady-State Ocean Circulation Explorer)**: A high-precision Earth gravity field model used in orbit determination.
- **SRP (Solar Radiation Pressure)**: The force exerted by solar photons on a satellite's surface, a significant non-gravitational perturbation.
- **Jacchia Drag**: An atmospheric density model used to calculate atmospheric drag on satellites.
- **Normal Point Schema**: The JSON/YAML schema defining the structure of SLR normal point data (see `contracts/normal_point.schema.yaml`).
- **Orbit Solution**: The result of an orbit determination process, containing orbital elements, non-gravitational accelerations, and residuals.
- **Joint Fit**: An orbit determination method that simultaneously estimates parameters for multiple satellites to directly measure differential acceleration.
- **Separate Fit**: An orbit determination method where each satellite is processed independently, and differential acceleration is derived from the difference in estimated parameters.
- **Feasibility Gap**: A condition where required data (e.g., for a specific satellite) is unavailable, requiring the pipeline to proceed with partial data and flag the result.
- **ILRS (International Laser Ranging Service)**: The international organization that coordinates SLR activities and archives data.
