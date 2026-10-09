# One owner for Dartmouth retries

Inspection of the installed ChatDartmouth/OpenAI client on 2026-10-09 found
`root_client.max_retries == 2` despite llmXive owning its own retry loop and
hard model deadlines. The SDK can issue up to three HTTP requests per outer
attempt. A worker abandoned at the outer deadline can still perform SDK retries,
adding hidden provider traffic after the router has fallen back to another model.

Pass `max_retries: 0` through ChatDartmouth's model kwargs (promoted by
ChatOpenAI to the client configuration). llmXive's existing bounded transient
retry, fallback and circuit-breaker behavior remains responsible for recovery.
No deadline, model or reasoning-effort default changes.

Validation uses the actual installed SDK against a credential-free localhost
HTTP server. Both HTTP 503 and a real read timeout yield one observed request
after the fix, versus three before it. Both regressions fail on the old platform;
38 SDK/retry/thinking/circuit-breaker tests pass. This proves request-count
control, not recovery of the externally hosted models or improved scientific
quality. The current SDK also correctly promotes the existing timeout field;
the outer hard deadline remains protection against other hangs.
