# Specification: Visual Aesthetics and Credibility Study

## Overview
This specification defines the requirements for a web-based study investigating the impact of visual design on perceived credibility.

## User Stories

### US0: Informed Consent Workflow
**As a** participant, **I want to** review and accept an IRB-approved consent form, **so that** I can voluntarily participate in the study with full knowledge of the risks and benefits.
- **Acceptance Criteria**:
 - Consent form is displayed before any study content.
 - Form includes `IRB_PROTOCOL_ID`.
 - "I Agree" logs consent and allows access.
 - "I Do Not Agree" redirects to a withdrawal page.

### US1: Participant Survey Data Collection
**As a** researcher, **I want to** present stimuli in a counterbalanced order and collect ratings, **so that** I can minimize order effects and gather valid data.
- **Acceptance Criteria**:
 - Several stimuli (Professional, Minimalist, Low-Quality, Neutral) are presented.
 - Order follows a pre-defined Latin Square.
 - Participants rate Credibility and Professionalism (1-7 Likert) for each.
 - Demographic data (Age, Education) is collected.
 - Data is exported to CSV with hashed IP and metadata.

### US2: Statistical Analysis Pipeline
**As a** researcher, **I want to** run Repeated-Measures ANOVA and pairwise tests, **so that** I can determine if visual design significantly affects credibility.
- **Acceptance Criteria**:
 - ANOVA is run on the main hypothesis.
 - Post-hoc tests are Bonferroni-corrected.
 - Effect sizes (η², Cohen's d) are calculated.
 - Results are saved in JSON format.

### US3: Robustness and Validation
**As a** researcher, **I want to** control for demographics in a Mixed-Effects model, **so that** I can verify the design effect is independent of participant background.
- **Acceptance Criteria**:
 - Model includes Age and Education as covariates.
 - Random intercepts for participants are used.
 - Results are compared to ANOVA findings.

## Data Model
- **Stimulus**: ID, Type (Professional, Minimalist, etc.), HTML Content.
- **Response**: ParticipantID, StimulusID, CredibilityRating, ProfessionalismRating, Timestamp.
- **Participant**: ParticipantID, Age, EducationLevel, HashedIP.

## Non-Functional Requirements
- **Performance**: Survey must load within 2 seconds on standard broadband.
- **Security**: No PII stored in logs; IP hashing mandatory.
- **Reproducibility**: All analysis scripts must use fixed random seeds.
