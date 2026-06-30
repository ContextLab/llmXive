# Data Handling Plan

**Project**: PROJ-317 - The Impact of Visual Detail on False Memory Susceptibility
**Version**: 1.0
**Date**: [Current Date]

## 1. Data Types

### 1.1 Collected Data
- **Stimulus Data**: Original and manipulated images (PNG/JPG).
- **Metadata**: YAML files describing image manipulation parameters (complexity scores, object counts).
- **Response Data**: Participant responses to recognition questions (binary: true/false, confidence ratings).
- **Session Data**: Timestamps, session duration, dropout flags.
- **Demographic Data** (Optional): Age range, gender (non-identifying categories).

### 1.2 Excluded Data
- No personally identifiable information (PII) such as names, email addresses, or IP addresses will be collected.
- No audio or video recordings of participants.

## 2. Data Collection Methods

- **Simulated Participants**: Data is generated programmatically using the `code/participants/interface.py` module.
- **Human Participants** (Future): Data will be collected via a secure web interface or local application.
- **Storage**: All data is stored in the `data/` directory structure.

## 3. Data Storage and Security

### 3.1 Storage Location
- **Primary Storage**: `data/responses/`, `data/stimuli/`, `data/stimuli_metadata/`, `data/processed/`.
- **Backup**: Automated backups to [Secure Cloud/Local Server].
- **Encryption**: Data at rest is encrypted using AES-256.

### 3.2 Access Control
- Access is restricted to authorized research team members.
- Credentials are managed via [Authentication System].
- Logs of data access are maintained.

## 4. Data Anonymization

- **Pseudonymization**: Each participant is assigned a unique, random ID.
- **No Linkage**: The mapping between participant IDs and real identities (if any) is stored separately and destroyed after data collection.
- **Aggregation**: Analysis is performed on aggregated data where possible.

## 5. Data Retention and Disposal

- **Retention Period**: Data will be retained for [X] years (e.g., 5 years) after the publication of results.
- **Disposal Method**: Secure deletion using cryptographic shredding.
- **Documentation**: A disposal log will be maintained.

## 6. Data Sharing

- **Internal**: Data is shared within the research team for analysis.
- **External**: De-identified data may be shared in public repositories (e.g., OSF) upon publication, in compliance with open science principles.
- **Third Parties**: No data will be shared with third parties without explicit IRB approval.

## 7. Compliance

- **GDPR**: If EU citizens are involved, data handling complies with GDPR regulations (Right to Access, Right to Erasure).
- **HIPAA**: Not applicable (no health information).
- **Institutional Policies**: Adherence to [Institution] data security policies.

## 8. Incident Response

In the event of a data breach:
1. Immediately isolate affected systems.
2. Notify the Principal Investigator and IRB.
3. Assess the scope of the breach.
4. Notify affected participants if required by law.
5. Document the incident and remediation steps.

## 9. Review and Updates

This plan will be reviewed annually or whenever there is a significant change in the research protocol.

---

**Approvals**:
- Principal Investigator: ___________________ Date: ___________
- Data Protection Officer: ___________________ Date: ___________
