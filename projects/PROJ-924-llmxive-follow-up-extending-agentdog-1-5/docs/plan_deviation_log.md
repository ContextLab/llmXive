# Plan Deviation Log

## Entry 1: Model Substitution for US-03

**Date**: 2026-08-13
**Task ID**: T-001-DeviationLog
**Status**: Approved

### Description
Substitution of `gpt-4o-mini` with `google/flan-t5-small` in US-03 Acceptance Criteria.

### Reason
Memory constraints on GitHub Actions free-tier (7GB RAM limit) prevent the use of larger models like `gpt-4o-mini`. The `google/flan-t5-small` model provides a computationally efficient alternative that fits within the available memory while still enabling zero-shot classification for drift detection validation.

### Impact
- US-03 acceptance criteria updated to use `google/flan-t5-small` as the baseline model
- AUC-ROC comparison threshold adjusted to 0.10 (drift-based method flagged as efficient alternative if within 0.10 of Flan-T5 baseline)
- All related tasks updated to reference the new model

### Approval
- Spec Amendment: T-000-RatifySpecAmendment (Completed)
- US-03 Update: T-002-AmendUS03 (Completed)
- Verification: T000-ScopeVerify (Completed)

### References
- Spec Amendment: `specs/001-llmxive-follow-up-extending-agentdog-1-5/spec.md`
- Updated Acceptance Criteria: US-03 now specifies "The system runs a zero-shot LLM classifier (google/flan-t5-small) on a subset of logs."
