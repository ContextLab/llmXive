# Calibration adjudication — domain: (unspecified)
<!-- runner_version: 9da4a8f7 -->

**Summary**: 0 of 1 injections caught · 1 missed · 0 extra finding(s) on clean artifacts (each flagged for manual adjudication).

**Runner version**: `9da4a8f7`

Per design SSoT (FR-046): adjustment is DIFFERENTIAL + manual. There is no fixed over-flag % threshold; the maintainer reviews each extra finding below and marks it 'legitimate' (panel correctly noticed real flaw in a supposedly-clean sample → fix the sample) or 'spurious' (prompt over-strict → adjust the prompt).

## 1. Injector: `nonexistent_citation`

- **Expected lens**: `claim_accuracy`
- **Description**: Injector: nonexistent_citation
- **Status**: ❌ MISSED (false negative)
- **Lenses flagged on injected**: (none)

Clean artifact surfaced no concerns. ✅
