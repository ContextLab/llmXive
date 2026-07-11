"""
Contract test for data/processed/ schema.
Verifies that the processed corpus directory structure and file contents
adhere to the defined schema for User Story 1.

Schema Requirements:
1. Directory `data/processed/` must exist.
2. Must contain exactly 20 subdirectories (one per author).
3. Each author subdirectory must contain >= 10 text files.
4. Each text file must be a valid UTF-8 text file.
5. File naming convention: `abstract_{id}.txt` (or similar consistent pattern).
6. Content must be preprocessed (lowercase, no punctuation, tokenized/char-level).
"""

import json
import os
import re
import string
from pathlib import Path
from typing import List, Dict, Any

import pytest

# Project root relative to tests/contract/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SUMMARY_LOG = PROJECT_ROOT / "data" / "processed" / "summary_log.json"


def get_author_dirs() -> List[Path]:
    """Returns list of author directories in data/processed/."""
    if not PROCESSED_DIR.exists():
        return []
    return [d for d in PROCESSED_DIR.iterdir() if d.is_dir()]


def get_text_files(author_dir: Path) -> List[Path]:
    """Returns list of text files in an author directory."""
    return [f for f in author_dir.iterdir() if f.suffix == ".txt" and f.is_file()]


def is_valid_preprocessed_text(content: str) -> bool:
    """
    Validates that the text content adheres to preprocessing rules:
    - Lowercase only (no uppercase letters).
    - No punctuation (except spaces and newlines which are separators).
    - Contains only alphanumeric characters and whitespace.
    """
    if not content:
        return False

    # Check for uppercase
    if any(c.isupper() for c in content):
        return False

    # Check for punctuation
    # Allowed: alphanumeric, space, newline, tab
    allowed_pattern = re.compile(r'^[a-z0-9\s\n\t]*$')
    if not allowed_pattern.match(content):
        return False

    return True


class TestCorpusSchema:
    """Contract tests for the processed corpus schema."""

    def test_processed_directory_exists(self):
        """Contract: data/processed/ directory must exist."""
        assert PROCESSED_DIR.exists(), "Processed directory 'data/processed/' does not exist."
        assert PROCESSED_DIR.is_dir(), "Path 'data/processed/' is not a directory."

    def test_exact_author_count(self):
        """Contract: Must have exactly 20 distinct author directories."""
        authors = get_author_dirs()
        assert len(authors) == 20, f"Expected exactly 20 author directories, found {len(authors)}."

    def test_minimum_files_per_author(self):
        """Contract: Each author must have at least 10 text files."""
        authors = get_author_dirs()
        for author_dir in authors:
            files = get_text_files(author_dir)
            assert len(files) >= 10, (
                f"Author directory '{author_dir.name}' has only {len(files)} files. "
                "Minimum required is 10."
            )

    def test_file_naming_convention(self):
        """Contract: Files should follow a consistent naming convention (e.g., abstract_*.txt)."""
        authors = get_author_dirs()
        pattern = re.compile(r'abstract_\d+\.txt')
        
        for author_dir in authors:
            files = get_text_files(author_dir)
            if not files:
                continue
            
            # Check the first file to establish the pattern for this author
            first_file = files[0]
            if not pattern.match(first_file.name):
                # If the first file doesn't match, check if others do to give a better error
                matches = [f for f in files if pattern.match(f.name)]
                assert len(matches) > 0, (
                    f"Files in '{author_dir.name}' do not match expected naming convention "
                    f"(e.g., 'abstract_*.txt'). Found: {files[0].name}"
                )

    def test_content_preprocessing_validity(self):
        """Contract: All text files must be valid preprocessed text (lowercase, no punctuation)."""
        authors = get_author_dirs()
        invalid_files = []

        for author_dir in authors:
            files = get_text_files(author_dir)
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if not is_valid_preprocessed_text(content):
                        invalid_files.append(file_path)
                except Exception as e:
                    invalid_files.append(f"{file_path} (Error reading: {e})")

        assert len(invalid_files) == 0, (
            f"Found {len(invalid_files)} files that do not meet preprocessing criteria "
            f"(lowercase, no punctuation). Examples: {invalid_files[:5]}"
        )

    def test_summary_log_exists_and_valid(self):
        """Contract: A summary log (summary_log.json) should exist and be valid JSON."""
        if not SUMMARY_LOG.exists():
            # If the log doesn't exist, it's a warning but maybe not a hard fail depending on strictness.
            # However, the task description says "summary log confirms the total count".
            # We enforce it as a contract for completeness.
            pytest.fail("Summary log 'data/processed/summary_log.json' does not exist.")
        
        try:
            with open(SUMMARY_LOG, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Verify expected keys
            expected_keys = {'total_authors', 'total_files', 'author_distribution'}
            if not expected_keys.issubset(set(data.keys())):
                pytest.fail(f"Summary log missing expected keys. Found: {list(data.keys())}")
            
            assert data['total_authors'] == 20, "Summary log reports incorrect total authors."
        except json.JSONDecodeError:
            pytest.fail("Summary log is not valid JSON.")

    def test_author_directory_names_valid(self):
        """Contract: Author directory names should be valid identifiers or hashes."""
        authors = get_author_dirs()
        valid_name_pattern = re.compile(r'^[a-z0-9_-]+$')
        
        invalid_names = []
        for author_dir in authors:
            if not valid_name_pattern.match(author_dir.name):
                invalid_names.append(author_dir.name)
        
        assert len(invalid_names) == 0, (
            f"Author directory names contain invalid characters. Invalid names: {invalid_names}"
        )

    def test_no_empty_files(self):
        """Contract: No text files should be empty (0 bytes)."""
        authors = get_author_dirs()
        empty_files = []
        
        for author_dir in authors:
            files = get_text_files(author_dir)
            for file_path in files:
                if file_path.stat().st_size == 0:
                    empty_files.append(file_path)
        
        assert len(empty_files) == 0, f"Found {len(empty_files)} empty text files."

    def test_consistent_encoding(self):
        """Contract: All files must be readable as UTF-8."""
        authors = get_author_dirs()
        encoding_errors = []
        
        for author_dir in authors:
            files = get_text_files(author_dir)
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        f.read()
                except UnicodeDecodeError:
                    encoding_errors.append(file_path)
        
        assert len(encoding_errors) == 0, (
            f"Found {len(encoding_errors)} files with invalid UTF-8 encoding."
        )

    def test_author_distribution_balance(self):
        """Contract: Check if distribution is reasonably balanced (optional but good practice)."""
        # This is a soft check to ensure no single author dominates the dataset disproportionately
        # if the ingestion logic was supposed to balance it.
        authors = get_author_dirs()
        if not authors:
            return

        counts = [len(get_text_files(d)) for d in authors]
        min_count = min(counts)
        max_count = max(counts)
        
        # Allow some variance, but flag if max is > 2x min (heuristic)
        if min_count > 0 and max_count > (2 * min_count):
            # This is a warning/assertion depending on strictness. 
            # For a contract test, we might just assert it's not 10x.
            # Let's assert it's not extremely unbalanced.
            assert max_count <= (5 * min_count), (
                f"Author distribution is highly unbalanced. Min: {min_count}, Max: {max_count}. "
                "This might indicate a sampling issue."
            )

    def test_no_subdirectories_in_author_folders(self):
        """Contract: Author folders should contain only files, no subdirectories."""
        authors = get_author_dirs()
        for author_dir in authors:
            subdirs = [d for d in author_dir.iterdir() if d.is_dir()]
            assert len(subdirs) == 0, (
                f"Author directory '{author_dir.name}' contains subdirectories: {subdirs}. "
                "Only text files are expected."
            )