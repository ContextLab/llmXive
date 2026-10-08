# llmXive GitHub issue consolidation — October 8, 2026

## Verified result

The initial census contained **199 open issues**: 185 reviewer-response reports, five provider reports, and nine substantive issues. Two recurring-cause umbrellas (#1474/#1475) were created; two additional reviewer reports (#1476 and #1477) appeared during/following the audit and were included. Of these **203 tracked issues**, **195 are now closed** and **eight remain open**. Final states were verified with a fresh full GitHub issue census.

Closed dispositions: **187 reviewer incidents → #1474**, **five provider incidents → #1475**, and **three historical/overlapping requests** (#216/#314 → #1139; #111 completed backend with deferred scope → #114). The 192 incident closures preserve original report bodies and link to the surviving unresolved cause. Their closure does not change project state or claim that fixes have been deployed.

## Retained work

- [#1475: Recurring: provider availability, model validity, and quota failures](https://github.com/ContextLab/llmXive/issues/1475)
- [#1474: Recurring: malformed reviewer responses block convergence across projects](https://github.com/ContextLab/llmXive/issues/1474)
- [#1285: spec 026: requirement-driven model selection consolidation](https://github.com/ContextLab/llmXive/issues/1285)
- [#1242: Scheduled self-improvement: verified repairs from errors and open platform issues](https://github.com/ContextLab/llmXive/issues/1242)
- [#1241: Real-project storage and compute: streamed datasets and bounded GPU execution](https://github.com/ContextLab/llmXive/issues/1241)
- [#1139: Pipeline quality: verified artifacts, data recovery, and full-study throughput](https://github.com/ContextLab/llmXive/issues/1139)
- [#262: Website usability: mobile navigation, contribution flows, and accurate pipeline status](https://github.com/ContextLab/llmXive/issues/262)
- [#114: Deferred: theorem-statement artifacts for math-theory projects](https://github.com/ContextLab/llmXive/issues/114)

- #1139 owns scientific scope, useful verified artifacts, data/recovery handoffs, and actual full-study throughput. It retains the unchanged-document claim-extraction cache gap, software-feature template overscoping, and possible loss of originating-panel kickback feedback. Causal timing/live-cause claims remain explicitly unproved.
- #1474 owns malformed/truncated reviewer responses and the observed omitted-reviewer-prefix variant. The narrow eight-hex alias fix and shared routing are proposed in draft PR #1472; scientific and production acceptance remain open.
- #1475 keeps capacity, invalid-model, and budget-exhaustion causes distinct. Proposed fallback/routing changes preserve explicit budget errors as hard failures.
- #1242 requires useful, verified scheduled repairs from both recurring errors and open platform issues; one isolated trial is not unattended acceptance.
- #1285 remains the separate requirement-driven model-selection architecture, including migration and budget safeguards.
- #1241 remains real-project large-data/compute capability work; named services are candidates pending suitability checks.
- #262 retains mobile/navigation, contribution-flow, rendering and truthful status work; this audit did not perform fresh browser acceptance.
- #114 remains explicitly deferred until a real math project needs theorem-statement artifacts.

## Historical closures and evidence

- [#111](https://github.com/ContextLab/llmXive/issues/111): paper-discovery backend completed in [merged PR #117](https://github.com/ContextLab/llmXive/pull/117), supported by [the #113 completion record](https://github.com/ContextLab/llmXive/issues/113#issuecomment-4434720834). Theorem-statement scope survives in #114.
- [#216](https://github.com/ContextLab/llmXive/issues/216): quality/execution requirements consolidated into #1139; historical Qwen-default premise superseded by the requested free-model upgrade. Architectural model selection remains #1285.
- [#314](https://github.com/ContextLab/llmXive/issues/314): stale June PROJ-552 rows archived with [prior resolution evidence](https://github.com/ContextLab/llmXive/issues/314#issuecomment-4992331819) and merged [PR #1281](https://github.com/ContextLab/llmXive/pull/1281). Checked-out project state is in_progress with failed_stage/human_escalation_reason null. Current digest code creates a new singleton for future undigested records. Reconciliation/acceptance remains in #1139; this is not a blanket claim that escalation machinery works in production.

## Verification boundary

The final follow-up census at approximately 22:51 UTC again found eight open issues after archiving #1477. Earlier eight-open censuses were valid snapshots; production may emit new duplicate reports until PR #1472 is deployed. The canary subsequently ended naturally with budget_exhausted after 12,242.9 seconds, reaching planned at step 11. It did not establish full acceptance, and the pending concern-ID parser fix was not loaded in that process.

[PR #1472](https://github.com/ContextLab/llmXive/pull/1472) remains draft and undeployed; no accepted full-pipeline scientific canary was established by this cleanup. No project state, source code, user checkout, or PR merge was changed by this consolidation. Six existing substantive issue bodies/titles were clarified; two new umbrella bodies preserve all 192 incident references and current pending acceptance.

The first closure batch had already closed 58 incidents before this resumed pass. A later unapproved-command-prefix prompt stalled issue editing; that prompt was aborted, the old execution cell explicitly terminated, and live state refreshed before resuming. Already-approved GitHub API PATCH calls completed the authorized edits. Subsequent closure batches were small and verified after completion.

## Complete disposition inventory

The machine-readable inventory is `dispositions.json`; original bodies are preserved in `before.json` and final surviving bodies in `after.json`.

| Issue | Final state | Disposition | Continuing work |
|---|---|---|---|
| [#111](https://github.com/ContextLab/llmXive/issues/111) | closed | closed completed parent | [#114](https://github.com/ContextLab/llmXive/issues/114) |
| [#114](https://github.com/ContextLab/llmXive/issues/114) | open | retained and clarified | This issue |
| [#216](https://github.com/ContextLab/llmXive/issues/216) | closed | closed superseded/stale | [#1139](https://github.com/ContextLab/llmXive/issues/1139) |
| [#262](https://github.com/ContextLab/llmXive/issues/262) | open | retained and clarified | This issue |
| [#314](https://github.com/ContextLab/llmXive/issues/314) | closed | closed superseded/stale | [#1139](https://github.com/ContextLab/llmXive/issues/1139) |
| [#1139](https://github.com/ContextLab/llmXive/issues/1139) | open | retained and clarified | This issue |
| [#1241](https://github.com/ContextLab/llmXive/issues/1241) | open | retained and clarified | This issue |
| [#1242](https://github.com/ContextLab/llmXive/issues/1242) | open | retained and clarified | This issue |
| [#1282](https://github.com/ContextLab/llmXive/issues/1282) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1283](https://github.com/ContextLab/llmXive/issues/1283) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1284](https://github.com/ContextLab/llmXive/issues/1284) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1285](https://github.com/ContextLab/llmXive/issues/1285) | open | retained and clarified | This issue |
| [#1286](https://github.com/ContextLab/llmXive/issues/1286) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1287](https://github.com/ContextLab/llmXive/issues/1287) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1288](https://github.com/ContextLab/llmXive/issues/1288) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1289](https://github.com/ContextLab/llmXive/issues/1289) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1290](https://github.com/ContextLab/llmXive/issues/1290) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1291](https://github.com/ContextLab/llmXive/issues/1291) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1292](https://github.com/ContextLab/llmXive/issues/1292) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1293](https://github.com/ContextLab/llmXive/issues/1293) | closed | closed duplicate incident | [#1475](https://github.com/ContextLab/llmXive/issues/1475) |
| [#1294](https://github.com/ContextLab/llmXive/issues/1294) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1295](https://github.com/ContextLab/llmXive/issues/1295) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1296](https://github.com/ContextLab/llmXive/issues/1296) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1297](https://github.com/ContextLab/llmXive/issues/1297) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1298](https://github.com/ContextLab/llmXive/issues/1298) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1299](https://github.com/ContextLab/llmXive/issues/1299) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1300](https://github.com/ContextLab/llmXive/issues/1300) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1301](https://github.com/ContextLab/llmXive/issues/1301) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1302](https://github.com/ContextLab/llmXive/issues/1302) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1303](https://github.com/ContextLab/llmXive/issues/1303) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1304](https://github.com/ContextLab/llmXive/issues/1304) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1305](https://github.com/ContextLab/llmXive/issues/1305) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1306](https://github.com/ContextLab/llmXive/issues/1306) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1307](https://github.com/ContextLab/llmXive/issues/1307) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1308](https://github.com/ContextLab/llmXive/issues/1308) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1309](https://github.com/ContextLab/llmXive/issues/1309) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1310](https://github.com/ContextLab/llmXive/issues/1310) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1311](https://github.com/ContextLab/llmXive/issues/1311) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1312](https://github.com/ContextLab/llmXive/issues/1312) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1313](https://github.com/ContextLab/llmXive/issues/1313) | closed | closed duplicate incident | [#1475](https://github.com/ContextLab/llmXive/issues/1475) |
| [#1314](https://github.com/ContextLab/llmXive/issues/1314) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1315](https://github.com/ContextLab/llmXive/issues/1315) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1316](https://github.com/ContextLab/llmXive/issues/1316) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1317](https://github.com/ContextLab/llmXive/issues/1317) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1318](https://github.com/ContextLab/llmXive/issues/1318) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1319](https://github.com/ContextLab/llmXive/issues/1319) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1320](https://github.com/ContextLab/llmXive/issues/1320) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1321](https://github.com/ContextLab/llmXive/issues/1321) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1322](https://github.com/ContextLab/llmXive/issues/1322) | closed | closed duplicate incident | [#1475](https://github.com/ContextLab/llmXive/issues/1475) |
| [#1323](https://github.com/ContextLab/llmXive/issues/1323) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1324](https://github.com/ContextLab/llmXive/issues/1324) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1325](https://github.com/ContextLab/llmXive/issues/1325) | closed | closed duplicate incident | [#1475](https://github.com/ContextLab/llmXive/issues/1475) |
| [#1326](https://github.com/ContextLab/llmXive/issues/1326) | closed | closed duplicate incident | [#1475](https://github.com/ContextLab/llmXive/issues/1475) |
| [#1327](https://github.com/ContextLab/llmXive/issues/1327) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1328](https://github.com/ContextLab/llmXive/issues/1328) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1329](https://github.com/ContextLab/llmXive/issues/1329) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1330](https://github.com/ContextLab/llmXive/issues/1330) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1331](https://github.com/ContextLab/llmXive/issues/1331) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1332](https://github.com/ContextLab/llmXive/issues/1332) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1333](https://github.com/ContextLab/llmXive/issues/1333) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1334](https://github.com/ContextLab/llmXive/issues/1334) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1335](https://github.com/ContextLab/llmXive/issues/1335) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1336](https://github.com/ContextLab/llmXive/issues/1336) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1337](https://github.com/ContextLab/llmXive/issues/1337) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1338](https://github.com/ContextLab/llmXive/issues/1338) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1339](https://github.com/ContextLab/llmXive/issues/1339) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1340](https://github.com/ContextLab/llmXive/issues/1340) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1341](https://github.com/ContextLab/llmXive/issues/1341) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1342](https://github.com/ContextLab/llmXive/issues/1342) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1343](https://github.com/ContextLab/llmXive/issues/1343) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1344](https://github.com/ContextLab/llmXive/issues/1344) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1345](https://github.com/ContextLab/llmXive/issues/1345) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1346](https://github.com/ContextLab/llmXive/issues/1346) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1347](https://github.com/ContextLab/llmXive/issues/1347) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1348](https://github.com/ContextLab/llmXive/issues/1348) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1349](https://github.com/ContextLab/llmXive/issues/1349) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1350](https://github.com/ContextLab/llmXive/issues/1350) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1351](https://github.com/ContextLab/llmXive/issues/1351) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1352](https://github.com/ContextLab/llmXive/issues/1352) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1353](https://github.com/ContextLab/llmXive/issues/1353) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1354](https://github.com/ContextLab/llmXive/issues/1354) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1355](https://github.com/ContextLab/llmXive/issues/1355) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1356](https://github.com/ContextLab/llmXive/issues/1356) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1357](https://github.com/ContextLab/llmXive/issues/1357) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1358](https://github.com/ContextLab/llmXive/issues/1358) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1359](https://github.com/ContextLab/llmXive/issues/1359) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1360](https://github.com/ContextLab/llmXive/issues/1360) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1361](https://github.com/ContextLab/llmXive/issues/1361) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1362](https://github.com/ContextLab/llmXive/issues/1362) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1363](https://github.com/ContextLab/llmXive/issues/1363) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1364](https://github.com/ContextLab/llmXive/issues/1364) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1365](https://github.com/ContextLab/llmXive/issues/1365) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1366](https://github.com/ContextLab/llmXive/issues/1366) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1367](https://github.com/ContextLab/llmXive/issues/1367) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1368](https://github.com/ContextLab/llmXive/issues/1368) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1369](https://github.com/ContextLab/llmXive/issues/1369) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1370](https://github.com/ContextLab/llmXive/issues/1370) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1371](https://github.com/ContextLab/llmXive/issues/1371) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1372](https://github.com/ContextLab/llmXive/issues/1372) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1373](https://github.com/ContextLab/llmXive/issues/1373) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1374](https://github.com/ContextLab/llmXive/issues/1374) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1375](https://github.com/ContextLab/llmXive/issues/1375) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1376](https://github.com/ContextLab/llmXive/issues/1376) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1377](https://github.com/ContextLab/llmXive/issues/1377) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1378](https://github.com/ContextLab/llmXive/issues/1378) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1379](https://github.com/ContextLab/llmXive/issues/1379) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1380](https://github.com/ContextLab/llmXive/issues/1380) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1381](https://github.com/ContextLab/llmXive/issues/1381) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1382](https://github.com/ContextLab/llmXive/issues/1382) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1383](https://github.com/ContextLab/llmXive/issues/1383) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1384](https://github.com/ContextLab/llmXive/issues/1384) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1385](https://github.com/ContextLab/llmXive/issues/1385) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1386](https://github.com/ContextLab/llmXive/issues/1386) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1387](https://github.com/ContextLab/llmXive/issues/1387) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1388](https://github.com/ContextLab/llmXive/issues/1388) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1389](https://github.com/ContextLab/llmXive/issues/1389) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1390](https://github.com/ContextLab/llmXive/issues/1390) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1391](https://github.com/ContextLab/llmXive/issues/1391) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1392](https://github.com/ContextLab/llmXive/issues/1392) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1393](https://github.com/ContextLab/llmXive/issues/1393) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1394](https://github.com/ContextLab/llmXive/issues/1394) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1395](https://github.com/ContextLab/llmXive/issues/1395) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1396](https://github.com/ContextLab/llmXive/issues/1396) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1397](https://github.com/ContextLab/llmXive/issues/1397) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1398](https://github.com/ContextLab/llmXive/issues/1398) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1399](https://github.com/ContextLab/llmXive/issues/1399) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1400](https://github.com/ContextLab/llmXive/issues/1400) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1401](https://github.com/ContextLab/llmXive/issues/1401) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1402](https://github.com/ContextLab/llmXive/issues/1402) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1403](https://github.com/ContextLab/llmXive/issues/1403) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1404](https://github.com/ContextLab/llmXive/issues/1404) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1405](https://github.com/ContextLab/llmXive/issues/1405) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1406](https://github.com/ContextLab/llmXive/issues/1406) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1407](https://github.com/ContextLab/llmXive/issues/1407) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1408](https://github.com/ContextLab/llmXive/issues/1408) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1409](https://github.com/ContextLab/llmXive/issues/1409) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1410](https://github.com/ContextLab/llmXive/issues/1410) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1411](https://github.com/ContextLab/llmXive/issues/1411) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1412](https://github.com/ContextLab/llmXive/issues/1412) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1413](https://github.com/ContextLab/llmXive/issues/1413) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1414](https://github.com/ContextLab/llmXive/issues/1414) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1415](https://github.com/ContextLab/llmXive/issues/1415) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1416](https://github.com/ContextLab/llmXive/issues/1416) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1417](https://github.com/ContextLab/llmXive/issues/1417) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1418](https://github.com/ContextLab/llmXive/issues/1418) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1419](https://github.com/ContextLab/llmXive/issues/1419) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1420](https://github.com/ContextLab/llmXive/issues/1420) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1421](https://github.com/ContextLab/llmXive/issues/1421) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1422](https://github.com/ContextLab/llmXive/issues/1422) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1423](https://github.com/ContextLab/llmXive/issues/1423) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1424](https://github.com/ContextLab/llmXive/issues/1424) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1425](https://github.com/ContextLab/llmXive/issues/1425) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1426](https://github.com/ContextLab/llmXive/issues/1426) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1427](https://github.com/ContextLab/llmXive/issues/1427) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1428](https://github.com/ContextLab/llmXive/issues/1428) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1429](https://github.com/ContextLab/llmXive/issues/1429) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1430](https://github.com/ContextLab/llmXive/issues/1430) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1431](https://github.com/ContextLab/llmXive/issues/1431) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1432](https://github.com/ContextLab/llmXive/issues/1432) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1433](https://github.com/ContextLab/llmXive/issues/1433) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1434](https://github.com/ContextLab/llmXive/issues/1434) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1435](https://github.com/ContextLab/llmXive/issues/1435) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1436](https://github.com/ContextLab/llmXive/issues/1436) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1437](https://github.com/ContextLab/llmXive/issues/1437) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1438](https://github.com/ContextLab/llmXive/issues/1438) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1439](https://github.com/ContextLab/llmXive/issues/1439) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1440](https://github.com/ContextLab/llmXive/issues/1440) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1441](https://github.com/ContextLab/llmXive/issues/1441) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1442](https://github.com/ContextLab/llmXive/issues/1442) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1443](https://github.com/ContextLab/llmXive/issues/1443) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1444](https://github.com/ContextLab/llmXive/issues/1444) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1445](https://github.com/ContextLab/llmXive/issues/1445) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1446](https://github.com/ContextLab/llmXive/issues/1446) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1447](https://github.com/ContextLab/llmXive/issues/1447) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1448](https://github.com/ContextLab/llmXive/issues/1448) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1449](https://github.com/ContextLab/llmXive/issues/1449) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1450](https://github.com/ContextLab/llmXive/issues/1450) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1451](https://github.com/ContextLab/llmXive/issues/1451) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1452](https://github.com/ContextLab/llmXive/issues/1452) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1453](https://github.com/ContextLab/llmXive/issues/1453) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1454](https://github.com/ContextLab/llmXive/issues/1454) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1455](https://github.com/ContextLab/llmXive/issues/1455) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1456](https://github.com/ContextLab/llmXive/issues/1456) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1457](https://github.com/ContextLab/llmXive/issues/1457) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1458](https://github.com/ContextLab/llmXive/issues/1458) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1459](https://github.com/ContextLab/llmXive/issues/1459) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1460](https://github.com/ContextLab/llmXive/issues/1460) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1461](https://github.com/ContextLab/llmXive/issues/1461) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1462](https://github.com/ContextLab/llmXive/issues/1462) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1463](https://github.com/ContextLab/llmXive/issues/1463) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1464](https://github.com/ContextLab/llmXive/issues/1464) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1465](https://github.com/ContextLab/llmXive/issues/1465) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1466](https://github.com/ContextLab/llmXive/issues/1466) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1467](https://github.com/ContextLab/llmXive/issues/1467) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1468](https://github.com/ContextLab/llmXive/issues/1468) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1469](https://github.com/ContextLab/llmXive/issues/1469) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1470](https://github.com/ContextLab/llmXive/issues/1470) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1471](https://github.com/ContextLab/llmXive/issues/1471) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1473](https://github.com/ContextLab/llmXive/issues/1473) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1474](https://github.com/ContextLab/llmXive/issues/1474) | open | created umbrella | This issue |
| [#1475](https://github.com/ContextLab/llmXive/issues/1475) | open | created umbrella | This issue |
| [#1476](https://github.com/ContextLab/llmXive/issues/1476) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |
| [#1477](https://github.com/ContextLab/llmXive/issues/1477) | closed | closed duplicate incident | [#1474](https://github.com/ContextLab/llmXive/issues/1474) |

