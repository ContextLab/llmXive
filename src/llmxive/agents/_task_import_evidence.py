"""Bounded static Python dependency context; never import project code."""
from __future__ import annotations

import ast
import hashlib
from collections import deque
from pathlib import Path

MAX_DEPENDENCY_FILES = 8
MAX_IMPORT_CANDIDATES = 256
MAX_PARSE_BYTES = 200_000
MAX_CONTENT_BYTES = 12_000


def _candidates(source: Path, tree: ast.AST, root: Path):
    """Yield plausible local files, without claiming Python would select them."""
    roots = [source.parent]
    roots.extend(p for p in source.parents if p != source.parent and p.is_relative_to(root))
    roots.extend((root / "code", root / "src"))
    roots = list(dict.fromkeys(roots))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
            search = roots
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            modules = ([module] if module else []) + [
                ".".join(filter(None, (module, alias.name)))
                for alias in node.names if alias.name != "*"
            ]
            if node.level:
                base = source.parent
                for _ in range(node.level - 1):
                    base = base.parent
                search = [base] if base.is_relative_to(root) else []
            else:
                search = roots
        else:
            continue
        for module in modules:
            parts = module.split(".")
            for base in search:
                yield base.joinpath(*parts).with_suffix(".py")
                # Package initializers can themselves import relevant code.
                for end in range(1, len(parts) + 1):
                    yield base.joinpath(*parts[:end], "__init__.py")


def local_import_evidence(project_dir: Path, sources: list[Path]) -> str:
    """Expose bounded local import candidates and their bytes/hashes.

    Candidate enumeration is static and may include multiple layouts. In
    particular, a local io.py does not override Python's built-in/frozen io.
    Successful execution must still be evidenced by actual task run records.
    """
    root = project_dir.resolve()
    queue = deque(dict.fromkeys(
        path.resolve() for path in sources if path.resolve().is_relative_to(root)
    ))
    seen = set(queue)
    checked: set[Path] = set()
    chunks: list[str] = []
    discovered = 0
    while queue:
        source = queue.popleft()
        try:
            with source.open("rb") as stream:
                raw = stream.read(MAX_PARSE_BYTES + 1)
            if len(raw) > MAX_PARSE_BYTES:
                chunks.append(f"- `{source.relative_to(root)}`: dependency scan NOT INSPECTED (source size limit)")
                continue
            tree = ast.parse(raw)
        except (OSError, SyntaxError, ValueError):
            chunks.append(f"- `{source.relative_to(root)}`: dependency scan NOT INSPECTED (unreadable/invalid Python)")
            continue
        for candidate in _candidates(source, tree, root):
            if candidate in checked:
                continue
            if len(checked) >= MAX_IMPORT_CANDIDATES:
                chunks.append("Dependency scan NOT INSPECTED beyond the candidate limit; context is incomplete.")
                queue.clear()
                break
            checked.add(candidate)
            try:
                resolved = candidate.resolve()
                if not resolved.is_relative_to(root) or not resolved.is_file() or resolved in seen:
                    continue
                seen.add(resolved)
                if discovered >= MAX_DEPENDENCY_FILES:
                    chunks.append("Dependency scan NOT INSPECTED beyond the file limit; context is incomplete.")
                    queue.clear()
                    break
                with resolved.open("rb") as stream:
                    digest = hashlib.file_digest(stream, "sha256").hexdigest()
                    stream.seek(0)
                    content = stream.read(MAX_CONTENT_BYTES).decode("utf-8", errors="replace")
                size = resolved.stat().st_size
            except (OSError, ValueError, RuntimeError):
                chunks.append(f"- `{candidate.relative_to(root)}`: dependency NOT INSPECTED (unreadable path)")
                continue
            discovered += 1
            chunks.append(
                f"- Local import candidate `{candidate.relative_to(root)}` "
                f"(referenced from `{source.relative_to(root)}`, resolved: `{resolved.relative_to(root)}`, "
                f"{size} bytes, sha256={digest}):\n```\n{content}\n```"
                + ("\n…(truncated)" if size > MAX_CONTENT_BYTES else "")
            )
            queue.append(resolved)
    if not chunks:
        return ""
    return ("# Static project-local Python import context\n"
            "These are candidate source files, NOT proof of import resolution or successful execution. "
            "Multiple candidates can exist; standard-library/built-in modules and the actual runtime "
            "search path may take precedence. Unlisted imports may be installed dependencies or missing; "
            "absence from this bounded packet alone does not prove a module is absent.\n"
            + "\n".join(chunks))
