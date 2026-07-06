"""
Reference Validator for Markdown Artifacts.

This module verifies citations in markdown artifacts by checking both legacy paths
(idea/, technical-design/, implementation-plan/, paper/) and the active project
structure (specs/).
"""

import re
from pathlib import Path
from typing import List, Tuple, Set, Dict, Optional

from .logging import get_logger

logger = get_logger(__name__)

# Legacy documentation directories that may contain cited artifacts
LEGACY_PATHS = [
    "idea",
    "technical-design",
    "implementation-plan",
    "paper"
]

# Active project specification directory
ACTIVE_PATHS = [
    "specs"
]

# Regex pattern to match markdown links: [text](path) or [text](path "title")
# Also captures bare references like (path) or path references in text
MARKDOWN_LINK_PATTERN = re.compile(
    r'\[([^\]]+)\]\(([^)\s]+)(?:\s+"[^"]*")?\)'
)

# Pattern for bare file references in text (e.g., "see idea/design.md")
BARE_REFERENCE_PATTERN = re.compile(
    r'(?:see|refer to|based on|from)\s+([a-zA-Z0-9_/.-]+\.md)',
    re.IGNORECASE
)

def find_markdown_files(root_dir: Path) -> List[Path]:
    """
    Find all markdown files in the project directory.

    Args:
        root_dir: Project root directory

    Returns:
        List of Path objects for all markdown files found
    """
    md_files = []
    if not root_dir.exists():
        logger.warning(f"Root directory does not exist: {root_dir}")
        return md_files

    for path in root_dir.rglob("*.md"):
        md_files.append(path)

    return md_files

def extract_citations(file_path: Path) -> List[str]:
    """
    Extract all potential citations/references from a markdown file.

    Args:
        file_path: Path to the markdown file

    Returns:
        List of citation strings found in the file
    """
    citations = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return citations

    # Extract markdown links
    for match in MARKDOWN_LINK_PATTERN.finditer(content):
        ref = match.group(2).strip()
        if ref:
            citations.append(ref)

    # Extract bare references
    for match in BARE_REFERENCE_PATTERN.finditer(content):
        ref = match.group(1).strip()
        if ref:
            citations.append(ref)

    return citations

def resolve_reference(ref: str, root_dir: Path) -> Optional[Path]:
    """
    Attempt to resolve a reference to an actual file path.

    Checks both legacy paths and active project structure.

    Args:
        ref: The reference string from the markdown file
        root_dir: Project root directory

    Returns:
        Path to the resolved file if found, None otherwise
    """
    # Normalize the reference
    ref = ref.strip()

    # Handle absolute paths within project (starting with /)
    if ref.startswith('/'):
        ref = ref[1:]

    # Try direct path resolution
    candidate = root_dir / ref
    if candidate.exists():
        return candidate

    # Try with legacy prefixes
    for legacy in LEGACY_PATHS:
        candidate = root_dir / legacy / ref
        if candidate.exists():
            return candidate

    # Try with active prefixes
    for active in ACTIVE_PATHS:
        candidate = root_dir / active / ref
        if candidate.exists():
            return candidate

    # Try without extension if reference has .md
    if ref.endswith('.md'):
        base_ref = ref[:-3]
        candidate = root_dir / base_ref
        if candidate.exists():
            return candidate

        for legacy in LEGACY_PATHS:
            candidate = root_dir / legacy / base_ref
            if candidate.exists():
                return candidate

        for active in ACTIVE_PATHS:
            candidate = root_dir / active / base_ref
            if candidate.exists():
                return candidate

    # Try common extensions
    for ext in ['.md', '.txt', '.rst']:
        test_ref = ref if ref.endswith(ext) else ref + ext
        candidate = root_dir / test_ref
        if candidate.exists():
            return candidate

        for legacy in LEGACY_PATHS:
            candidate = root_dir / legacy / test_ref
            if candidate.exists():
                return candidate

        for active in ACTIVE_PATHS:
            candidate = root_dir / active / test_ref
            if candidate.exists():
                return candidate

    return None

def validate_citations(
    root_dir: Path,
    file_paths: Optional[List[Path]] = None
) -> Dict[str, List[Tuple[str, Optional[Path]]]]:
    """
    Validate all citations in markdown files against existing files.

    Args:
        root_dir: Project root directory
        file_paths: Optional list of specific files to check. If None, checks all .md files.

    Returns:
        Dictionary mapping each file path to a list of (citation, resolved_path) tuples.
        resolved_path is None if the citation could not be resolved.
    """
    if file_paths is None:
        file_paths = find_markdown_files(root_dir)

    results = {}
    total_citations = 0
    unresolved_count = 0

    for file_path in file_paths:
        logger.debug(f"Validating citations in: {file_path}")
        citations = extract_citations(file_path)

        if not citations:
            continue

        file_results = []
        for citation in citations:
          total_citations += 1
          resolved = resolve_reference(citation, root_dir)
          file_results.append((citation, resolved))

          if resolved is None:
              unresolved_count += 1
              logger.warning(f"Unresolved citation '{citation}' in {file_path}")
          else:
              logger.debug(f"Resolved citation '{citation}' to {resolved}")

        results[str(file_path)] = file_results

    logger.info(
        f"Validation complete: {total_citations} citations checked, "
        f"{unresolved_count} unresolved"
    )

    return results

def generate_validation_report(
    validation_results: Dict[str, List[Tuple[str, Optional[Path]]]],
    output_path: Optional[Path] = None
) -> str:
    """
    Generate a human-readable validation report.

    Args:
        validation_results: Results from validate_citations
        output_path: Optional path to write the report to

    Returns:
        The report as a string
    """
    lines = []
    lines.append("# Reference Validation Report")
    lines.append("")

    total_citations = 0
    total_unresolved = 0
    unresolved_files: List[str] = []

    for file_path, citations in validation_results.items():
        if not citations:
            continue

        lines.append(f"## {file_path}")
        lines.append("")

        file_unresolved = []
        for citation, resolved in citations:
            total_citations += 1
            status = "✓" if resolved else "✗"
            resolved_str = str(resolved) if resolved else "NOT FOUND"
            lines.append(f"- {status} `{citation}` → {resolved_str}")

            if resolved is None:
                total_unresolved += 1
                file_unresolved.append(citation)

        if file_unresolved:
            unresolved_files.append(file_path)

        lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total Citations**: {total_citations}")
    lines.append(f"- **Resolved**: {total_citations - total_unresolved}")
    lines.append(f"- **Unresolved**: {total_unresolved}")
    lines.append("")

    if unresolved_files:
        lines.append("### Files with Unresolved Citations")
        lines.append("")
        for f in unresolved_files:
            lines.append(f"- {f}")
        lines.append("")
    else:
        lines.append("✅ All citations resolved successfully!")
        lines.append("")

    report = "\n".join(lines)

    if output_path:
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Validation report written to {output_path}")
        except Exception as e:
            logger.error(f"Failed to write report to {output_path}: {e}")

    return report

def main():
    """Main entry point for the reference validator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate citations in markdown artifacts"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Project root directory (default: current directory)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to write the validation report (default: print to stdout)"
    )
    parser.add_argument(
        "--file",
        type=Path,
        action="append",
        help="Specific markdown file to validate (can be repeated)"
    )

    args = parser.parse_args()

    logger.info(f"Starting reference validation for: {args.root}")

    file_paths = args.file if args.file else None
    results = validate_citations(args.root, file_paths)
    report = generate_validation_report(results, args.output)

    if not args.output:
        print(report)

    # Exit with error code if there are unresolved citations
    total_unresolved = sum(
        1 for citations in results.values()
        for _, resolved in citations if resolved is None
    )

    if total_unresolved > 0:
        logger.warning(f"Found {total_unresolved} unresolved citations")
        return 1

    logger.info("All citations resolved successfully")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())