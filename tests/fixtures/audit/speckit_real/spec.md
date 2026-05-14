# Feature Specification: Add Two-Factor Authentication

**Feature Branch**: `042-two-factor-auth`
**Created**: 2026-05-14
**Status**: Active

## User Scenarios & Testing

### User Story 1 — User enables TOTP-based 2FA on their account (Priority: P1)

A signed-in user navigates to Security Settings and enrolls a TOTP authenticator (e.g. Authy, Google Authenticator). On enrollment, the system displays a QR code containing a TOTP secret URI. The user scans it with their authenticator app, types in the current 6-digit code to confirm setup, and then sees a list of 10 single-use recovery codes that they must download or print. Subsequent logins require the user to enter the current TOTP code after their password.

**Why this priority**: Account-takeover attacks via stolen/reused passwords are the single largest credential-compromise vector for this product. TOTP eliminates that attack surface for users who opt in. Recovery codes prevent permanent lockout if the device is lost.

**Independent Test**: Enroll a fresh user, scan the QR with a real TOTP app, log out, log back in. Verify (a) login is blocked until the 6-digit code is entered, (b) the code must be from the current 30-second window, (c) recovery codes work exactly once each, (d) the user can disable 2FA from a logged-in session by entering a current code.

**Acceptance Scenarios**:

1. **Given** an enrolled user with a valid TOTP code, **When** they submit it within the 30-second window, **Then** login succeeds and the session cookie is issued.
2. **Given** an enrolled user, **When** they submit a code from a previous window, **Then** login fails with "expired code" and the failure is logged.
3. **Given** an enrolled user who has lost their device, **When** they enter one of their unused recovery codes, **Then** login succeeds and that recovery code is marked used.

### Edge Cases

- **Clock drift**: TOTP windows must accept ±1 step (±30 seconds) to tolerate normal client clock drift.
- **Brute force**: failed TOTP attempts must be rate-limited to ≤5 per minute per account; after 10 consecutive failures the account is temporarily locked.
- **Recovery code reuse**: any attempt to reuse an already-used recovery code is logged as a security event and locks the account pending email confirmation.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST generate a per-user TOTP secret using HMAC-SHA1 with a 160-bit random secret per RFC 6238.
- **FR-002**: The system MUST display the TOTP secret as both a QR code (otpauth:// URI format) and a manually-typeable Base32 string.
- **FR-003**: The system MUST issue 10 single-use recovery codes on enrollment, each 8 alphanumeric characters, salted-hashed at rest.
- **FR-004**: The system MUST require the user to confirm TOTP setup by submitting a current 6-digit code before persisting the secret.
- **FR-005**: The system MUST rate-limit TOTP attempts to ≤5 per minute per account.

### Key Entities

- **TotpEnrollment**: per-user record holding the active TOTP secret (encrypted-at-rest), enrollment timestamp, and last-used timestamp.
- **RecoveryCode**: ten per enrollment; each carries a salted hash, a single-use flag, and the timestamp at which it was consumed (if ever).

## Success Criteria

- **SC-001**: 100% of users who enroll in 2FA and pass the confirmation step can log in with a fresh TOTP code on the next session.
- **SC-002**: Failed TOTP rate-limiting kicks in within 1 second of the fifth failed attempt in a 60-second window.
- **SC-003**: 0 recovery codes can be reused (each is single-use).
