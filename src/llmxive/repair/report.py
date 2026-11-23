"""Render retained repair evidence into the GitHub Actions run summary."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _read(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def render(output: Path) -> str:
    result = _read(output / "result.json")
    lines = ["## Platform repair", "", f"Result: {result.get('status', 'incomplete or interrupted')}"]
    if result.get("reason"):
        lines.extend(["", str(result["reason"])[:2000]])
    for attempt in sorted(output.glob("attempt-*")):
        if not attempt.is_dir():
            continue
        progress = _read(attempt / "progress.json")
        selection = _read(attempt / "selection.json")
        outcome = _read(attempt / "result.json")
        context = _read(attempt / "source-context.json")
        responses = sorted(attempt.glob("proposal-response-revision-*.json"))
        proposal = _read(responses[-1] if responses else attempt / "proposal-response.json")
        lines.extend(["", f"### {attempt.name}", "",
                      f"Last phase: {progress.get('phase', 'unknown')}"])
        anchor = _read(attempt / "failure-anchor.json")
        if anchor:
            lines.append("Original failure anchor: " + str(anchor.get("project_id"))
                         + " / " + str(anchor.get("project_relative_path")) + "; "
                         + str(anchor.get("exception")) + " (errno "
                         + str(anchor.get("os_errno")) + ")")
        if selection.get("problem"):
            lines.append("Selected problem: " + str(selection["problem"])[:2000])
        routes = _read(attempt / "dispatch-context.json").get("routes", [])
        if isinstance(routes, list):
            for route in routes:
                if isinstance(route, dict):
                    lines.append("Observed stage default: " + str(route.get("stage"))
                                 + " → " + str(route.get("default_agent")) + " ("
                                 + str(route.get("agent_source", route.get("source"))) + ")")
        bindings = _read(attempt / "import-bindings.json")
        for source, imports in bindings.items():
            if isinstance(imports, list):
                lookups = [str(item.get("imported_from")) + " → " + str(item.get("used_as"))
                           for item in imports if isinstance(item, dict)]
                if lookups:
                    lines.append(f"Dependency lookup bindings ({source}): " + "; ".join(lookups[:20]))
        for diagnostic in sorted(attempt.glob("proposal-validation*.json")):
            lines.append("Proposal correction: " + str(_read(diagnostic).get("error", ""))[:2000])
        if context:
            lines.append("Complete source inspected: " + ", ".join(
                f"`{name}` ({len(text.encode())} bytes)"
                for name, text in context.items() if isinstance(text, str)))
        if proposal:
            for field, label in (("edits", "Exact-edit targets"), ("files", "File proposals")):
                paths = proposal.get(field)
                if isinstance(paths, dict) and paths:
                    lines.append(label + ": " + ", ".join(f"`{name}`" for name in paths))
        if outcome.get("reason"):
            lines.append("Outcome: " + str(outcome["reason"])[:2000])
        for name in ("before.log", "after.log", "safety.log"):
            log = attempt / name
            if log.is_file():
                lines.extend(["", f"{name} (tail):", "```text",
                              log.read_text()[-2000:].replace("```", "'''"), "```"])
    lines.extend(["", "Detailed inputs, responses and test logs are in the repair-evidence artifact."])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print(render(Path(sys.argv[1])), end="")
