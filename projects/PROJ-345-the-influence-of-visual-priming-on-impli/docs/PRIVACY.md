# Privacy and Data Security

This document outlines the privacy and data security practices of the Visual Priming Research Project.

## Data Collection

- Data is sourced from public, verified repositories (OSF, Hugging Face).
- No personally identifiable information (PII) is collected or stored.
- All data is anonymized before processing.

## PII Scanning

- The pipeline includes a PII scanner (`code/security/pii_scanner.py`) to detect and prevent PII leakage.
- If PII is detected, the pipeline halts and generates a security report.
- Security reports are stored in `data/security_report.json`.

## Data Storage

- Raw data is stored in `data/raw/`.
- Processed data is stored in `data/processed/`.
- All data is encrypted at rest and in transit.

## Access Control

- Access to data is restricted to authorized personnel.
- Credentials are managed securely and never hard-coded.

## Compliance

- The project complies with relevant data protection regulations.
- Regular audits are conducted to ensure compliance.

## Contact

For privacy-related inquiries, please contact the project maintainers.
