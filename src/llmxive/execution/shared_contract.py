"""Shared-module API-contract analysis for the execution-fix loop.

The auto-fix loop works one task at a time, and the implementer rewrites a
module to suit the SINGLE caller it is fixing — which breaks the OTHER callers
of a shared symbol. Observed on PROJ-552's ``logs.py``: ``log_operation`` /
``get_logger`` / ``ReproducibilityLogger.debug`` are called ~6 incompatible ways
across ~9 scripts, so each round the implementer "fixes" one and re-breaks the
rest → the loop oscillates forever and never converges.

This module turns that un-converging class of bug into a fixable one. From the
run-book failures it detects API-CONTRACT errors (``TypeError`` / ``AttributeError``)
on a symbol the PROJECT'S OWN code defines, locates that symbol's defining file
and EVERY call site, and produces:

* :func:`render_contract_feedback` — a feedback block telling the implementer to
  fix the DEFINITION once, tolerant of all call sites (not the callers);
* :func:`defining_files` — the files whose tasks should be re-opened, so the
  implementer works on the shared ROOT, not the failing callers.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Contract errors on a plain function/decorator: symbol is group 1.
_FUNC_PATTERNS = [
    re.compile(r"TypeError: (\w+)\(\) got an unexpected keyword argument"),
    re.compile(r"TypeError: (\w+)\(\) takes \d+ positional arguments? but"),
    re.compile(r"TypeError: (\w+)\(\) missing \d+ required positional"),
    re.compile(r"TypeError: (\w+)\(\) takes no arguments"),
]
# Contract errors on a method / missing attribute: owner=group 1, symbol=group 2.
_METHOD_PATTERNS = [
    re.compile(r"TypeError: (\w+)\.(\w+)\(\) takes"),
    re.compile(r"TypeError: (\w+)\.(\w+)\(\) got an unexpected keyword"),
    re.compile(r"TypeError: (\w+)\.(\w+)\(\) missing"),
    re.compile(r"AttributeError: '(\w+)' object has no attribute '(\w+)'"),
]


@dataclass
class ContractIssue:
    symbol: str                 # function name OR method/attribute name
    owner: str | None           # class name for a method/attribute, else None
    defining_file: str | None = None      # repo-relative, e.g. code/reproducibility/logs.py
    call_sites: list[str] = field(default_factory=list)


def _code_files(code: Path) -> list[Path]:
    return [p for p in code.rglob("*.py") if "/.venv/" not in str(p)]


def _find_defining_file(code: Path, name: str) -> str | None:
    target = re.compile(rf"^\s*(?:async\s+)?(?:def|class)\s+{re.escape(name)}\b")
    for p in _code_files(code):
        try:
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                if target.match(line):
                    return str(p.relative_to(code.parent))
        except OSError:
            continue
    return None


def _find_call_sites(code: Path, symbol: str, owner: str | None) -> list[str]:
    pats = [re.compile(rf"@\s*{re.escape(symbol)}\b"), re.compile(rf"\b{re.escape(symbol)}\s*\(")]
    if owner:  # method / attribute access
        pats.append(re.compile(rf"\.{re.escape(symbol)}\s*\("))
    seen: set[str] = set()
    out: list[str] = []
    for p in _code_files(code):
        rel = str(p.relative_to(code.parent))
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in lines:
            s = line.strip()
            if s.startswith(("def ", "class ", "async def ")):
                continue  # the definition itself, not a call
            if any(pat.search(line) for pat in pats):
                entry = f"{rel}: {s[:140]}"
                if entry not in seen:
                    seen.add(entry)
                    out.append(entry)
    return out[:25]


def find_contract_issues(project_dir: Path, failures: list[str]) -> list[ContractIssue]:
    """Detect contract errors on PROJECT-DEFINED symbols in the run-book failures.

    Returns one issue per (symbol, owner) whose defining file is found under
    ``code/`` (a third-party symbol — no local definition — is out of scope: that
    is a misuse to fix at the call site, not a shared-contract problem).
    """
    code = Path(project_dir) / "code"
    if not code.is_dir():
        return []
    blob = "\n".join(failures)
    found: dict[tuple[str, str | None], ContractIssue] = {}
    for pat in _FUNC_PATTERNS:
        for m in pat.finditer(blob):
            found.setdefault((m.group(1), None), ContractIssue(m.group(1), None))
    for pat in _METHOD_PATTERNS:
        for m in pat.finditer(blob):
            found.setdefault((m.group(2), m.group(1)), ContractIssue(m.group(2), m.group(1)))

    issues: list[ContractIssue] = []
    for issue in found.values():
        # For a method/attribute issue, the defining file is where the CLASS is.
        issue.defining_file = _find_defining_file(code, issue.owner or issue.symbol)
        if not issue.defining_file:
            continue
        issue.call_sites = _find_call_sites(code, issue.symbol, issue.owner)
        issues.append(issue)
    return issues


def defining_files(issues: list[ContractIssue]) -> set[str]:
    """Re-open targets: the shared modules whose definitions need fixing."""
    out: set[str] = set()
    for i in issues:
        if i.defining_file:
            out.add(i.defining_file)
            out.add(Path(i.defining_file).stem)
    return out


def render_contract_feedback(issues: list[ContractIssue]) -> str:
    if not issues:
        return ""
    lines = [
        "",
        "## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers",
        "",
        "One or more failures are API-CONTRACT errors on a symbol YOUR OWN code "
        "defines and that MANY scripts call in DIFFERENT ways. Rewriting the "
        "definition to match one caller breaks the others — that is why this keeps "
        "failing. Fix the DEFINITION **once** so it is compatible with EVERY call "
        "site listed below: accept ``*args, **kwargs``, branch on what was actually "
        "passed, and NEVER raise on an unexpected call shape. For an auxiliary "
        "utility (e.g. logging), doing nothing on an unrecognized shape is fine. "
        "Do NOT edit the call sites — edit only the defining module.",
        "",
        "**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: "
        "ADD the missing methods/parameters and PRESERVE every function, method, "
        "and attribute that already exists. Do NOT rewrite the file from scratch "
        "and do NOT delete a definition to make room for another. Each round that "
        "deletes a previously-working symbol just moves the failure to that symbol "
        "next round — an infinite loop. The fix is cumulative: the module must "
        "satisfy ALL callers from ALL rounds simultaneously.",
    ]

    # Group method/attribute issues by their owning class so the implementer gets
    # one cumulative instruction per class (not one-method-at-a-time, which is
    # exactly what makes the failure rotate ``.log`` -> ``.info`` -> ``.debug``).
    by_class: dict[str, list[ContractIssue]] = {}
    funcs: list[ContractIssue] = []
    for i in issues:
        if i.owner:
            by_class.setdefault(i.owner, []).append(i)
        else:
            funcs.append(i)

    for i in funcs:
        lines += [
            "",
            f"### `{i.symbol}` — defined in `{i.defining_file}`; "
            f"called {len(i.call_sites)} way(s):",
            "",
        ]
        lines += [f"- {s}" for s in i.call_sites]
        lines += ["", f"Make `{i.symbol}` in `{i.defining_file}` accept ALL of the above."]

    for owner, owner_issues in by_class.items():
        defining = owner_issues[0].defining_file
        method_names = sorted({iss.symbol for iss in owner_issues})
        lines += [
            "",
            f"### class `{owner}` (in `{defining}`) — accessed via method/attribute "
            f"names this round: {', '.join('`' + m + '`' for m in method_names)}",
            "",
            f"`{owner}` is used like a logger: different scripts call DIFFERENT "
            "method names on it, and the set grows every round. Adding only the "
            "name(s) above will fail next round on the NEXT name. Make the class "
            "tolerant of ANY method name **without removing the ones it already "
            "has**, by either:",
            f"  1. defining the full method set explicitly (keep existing methods "
            f"like the ones already in `{defining}` AND add the missing ones), or",
            "  2. adding a permissive fallback so unknown attributes resolve to a "
            "no-op callable, e.g.:",
            "",
            "     ```python",
            "     def __getattr__(self, name):",
            "         # any logger-style call (.info/.debug/.warning/.error/...) "
            "becomes a tolerant no-op",
            "         def _noop(*args, **kwargs):",
            "             return None",
            "         return _noop",
            "     ```",
            "",
            f"Whichever you choose, every call site of `{owner}` across the "
            "codebase must stop raising `AttributeError`/`TypeError`.",
        ]
        for iss in owner_issues:
            lines += [
                "",
                f"`{owner}.{iss.symbol}` call sites ({len(iss.call_sites)}):",
            ]
            lines += [f"- {s}" for s in iss.call_sites]
    return "\n".join(lines)


__all__ = [
    "ContractIssue",
    "defining_files",
    "find_contract_issues",
    "render_contract_feedback",
]
