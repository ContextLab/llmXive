# Retain model outage history across agent calls

The canary recorded successive GPT-OSS fallback completions after 399.7, 384.4,
and 404.2 seconds. Each agent constructed a fresh Dartmouth backend, discarding
its per-model circuit breaker. The default GLM reasoning deadline is 360 seconds,
so fallback success did not prevent the next agent repeating the unavailable
primary's full deadline. Simply retaining the old breaker would also be wrong:
its open state never allowed a recovery probe.

The router now retains Dartmouth backends in a bounded process-local cache,
keyed by a digest of endpoint and authentication context. Other registered
backends retain their existing construction behavior. GLM remains the default;
free peer models still follow the existing fallback policy and paid guards.

A hard model-down/deadline failure immediately opens that model's circuit.
Ordinary transient failures retain the existing sustained-failure thresholds.
After a configurable cooldown (default 15 minutes), one request probes recovery;
concurrent callers continue to fall back. Failure restarts the cooldown; success
restores normal preferred-model use. State is not shared across runner processes.

Validation exercises the real router and backend with an injected transport:
first-call outage, subsequent immediate peer fallback, failed recovery and a
later healthy primary. Separate checks cover auth/endpoint isolation and a real
threaded single-probe race. Fifty backend/deadline/breaker tests pass. No live
latency improvement is claimed until a resumed canary uses this source.
