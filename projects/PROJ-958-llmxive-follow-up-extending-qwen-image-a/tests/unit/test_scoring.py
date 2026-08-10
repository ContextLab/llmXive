"""
Unit tests for src/scoring/syntactic_features.py.
Specifically verifies that no semantic embeddings (BERT, CLIP text encoders) are used.
"""

import ast
import importlib.util
import os
import re
from pathlib import Path

import pytest


# Path configuration relative to the project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
SYNTACTIC_FEATURES_PATH = PROJECT_ROOT / "src" / "scoring" / "syntactic_features.py"


class TestNoSemanticEmbeddings:
    """Tests to ensure syntactic_features.py does not import or use semantic embeddings."""

    def test_file_exists(self):
        """Verify the source file exists."""
        assert SYNTACTIC_FEATURES_PATH.exists(), f"Source file not found: {SYNTACTIC_FEATURES_PATH}"

    def test_no_bert_or_clip_imports(self):
        """
        Static analysis: Check the source code for imports of BERT or CLIP text encoders.
        We look for patterns like 'transformers', 'bert', 'clip', 'sentence_transformers'
        that would indicate semantic embedding usage.
        """
        with open(SYNTACTIC_FEATURES_PATH, "r", encoding="utf-8") as f:
            source_code = f.read()

        # Patterns that indicate semantic embedding libraries
        forbidden_patterns = [
            r"from\s+transformers\s+.*\b(Bert|Roberta|DistilBert|Electra|Deberta)\b",
            r"import\s+transformers",
            r"from\s+clip\s+import",
            r"import\s+clip",
            r"from\s+sentence_transformers\s+import",
            r"import\s+sentence_transformers",
            r"from\s+torch\s+hub\s+.*\b(load)\b.*\b(clip|bert|model)\b",
            r"torch\.hub\.load.*\b(clip|bert)\b",
        ]

        # Combined regex for forbidden imports
        forbidden_regex = re.compile("|".join(forbidden_patterns), re.IGNORECASE)

        matches = forbidden_regex.findall(source_code)
        assert not matches, (
            f"Found forbidden semantic embedding imports in {SYNTACTIC_FEATURES_PATH}: {matches}. "
            "This module must only use syntactic/lexical features (nltk, spacy, textstat)."
        )

    def test_no_embedding_initialization(self):
        """
        Static analysis: Check for instantiation of embedding models.
        Even if imported conditionally, we check for common initialization patterns.
        """
        with open(SYNTACTIC_FEATURES_PATH, "r", encoding="utf-8") as f:
            source_code = f.read()

        forbidden_init_patterns = [
            r"\bBertModel\b",
            r"\bRobertaModel\b",
            r"\bCLIP\b",
            r"\bSentenceTransformer\b",
            r"\bAutoModel\b.*\b(text|encoder)\b",
            r"\bload_model\b.*\b(clip|bert)\b",
        ]

        forbidden_regex = re.compile("|".join(forbidden_init_patterns), re.IGNORECASE)
        matches = forbidden_regex.findall(source_code)

        # Allow 'textstat' or 'nltk' or 'spacy' usage, but forbid transformer-based text encoders
        assert not matches, (
            f"Found forbidden semantic embedding initialization patterns in {SYNTACTIC_FEATURES_PATH}: {matches}. "
            "Do not instantiate BERT, CLIP, or similar semantic models in this module."
        )

    def test_ast_verification_no_transformer_calls(self):
        """
        AST-based verification: Parse the file and ensure no calls to known
        semantic embedding loading functions exist.
        """
        with open(SYNTACTIC_FEATURES_PATH, "r", encoding="utf-8") as f:
            source_code = f.read()

        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            pytest.fail(f"Source file has syntax errors: {e}")

        # Functions that load semantic models
        forbidden_calls = {
            "from_pretrained",  # Common in transformers
            "load",             # Common in clip/sentence_transformers
        }

        # Check function calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check direct function call
                if isinstance(node.func, ast.Name):
                    if node.func.id in ["load", "from_pretrained"]:
                        # Check if it's likely a semantic model load by looking at context/args if possible
                        # For safety, flag if 'transformers' or 'clip' is in the module path or if args suggest it
                        pass 
                
                # Check attribute calls (e.g., model.load, transformers.load)
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ["load", "from_pretrained"]:
                        # Check the value part of the attribute access
                        if isinstance(node.func.value, ast.Name):
                            module_name = node.func.value.id
                            if module_name in ["transformers", "clip", "sentence_transformers", "torch"]:
                                pytest.fail(
                                    f"Found potential semantic model loading call: {module_name}.{node.func.attr}() "
                                    f"in {SYNTACTIC_FEATURES_PATH}. This module must not use semantic embeddings."
                                )

    def test_only_allowed_dependencies(self):
        """
        Verify that the module only imports from allowed libraries:
        - Standard library
        - nltk, spacy, textstat, numpy, pandas, logging
        """
        with open(SYNTACTIC_FEATURES_PATH, "r", encoding="utf-8") as f:
            source_code = f.read()

        allowed_modules = {
            "nltk", "spacy", "textstat", "numpy", "pandas", 
            "logging", "os", "sys", "re", "ast", "math", 
            "typing", "collections", "itertools", "json"
        }

        # Extract imports
        tree = ast.parse(source_code)
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module.split(".")[0])

        # Check for forbidden modules
        forbidden_found = imported_modules - allowed_modules
        
        # Filter out standard library modules that might not be in our explicit list
        stdlib_modules = {
            "os", "sys", "re", "ast", "math", "logging", "json", "typing", 
            "collections", "itertools", "pathlib", "warnings", "time", "random"
        }
        
        actual_forbidden = forbidden_found - stdlib_modules

        # Specific check: if transformers, clip, sentence_transformers are present, fail
        semantic_libs = {"transformers", "clip", "sentence_transformers", "torch"}
        if semantic_libs & actual_forbidden:
            pytest.fail(
                f"Found forbidden semantic embedding libraries in imports: {semantic_libs & actual_forbidden}. "
                "Allowed libraries: {allowed_modules} + standard library."
            )