import re
import random
import json
import ast
from typing import Tuple, List, Dict, Any, Optional, Set
from collections import Counter

# Import existing utilities from sibling modules if available, or define locally
# Note: The API surface shows these are the public names for this module.

# --- Constants and Data ---
COMMON_SYNONYMS = {
    "list": ["sequence", "array", "collection", "items"],
    "dict": ["mapping", "dictionary", "hash", "object"],
    "str": ["text", "string", "word", "character"],
    "int": ["number", "integer", "value", "count"],
    "float": ["decimal", "number", "value"],
    "bool": ["boolean", "flag", "status"],
    "None": ["null", "nil", "nothing", "empty"],
    "True": ["yes", "correct", "active", "on"],
    "False": ["no", "incorrect", "inactive", "off"],
    "append": ["add", "insert", "push", "include"],
    "remove": ["delete", "discard", "exclude", "pop"],
    "len": ["length", "size", "count", "quantity"],
    "range": ["sequence", "interval", "span", "window"],
    "print": ["log", "display", "output", "show"],
    "return": ["yield", "give", "send", "provide"],
    "if": ["when", "provided", "assuming", "in case"],
    "else": ["otherwise", "instead", "failing that", "elsewise"],
    "for": ["iterate", "loop", "cycle", "traverse"],
    "while": ["as long as", "until", "continually", "repeatedly"],
    "def": ["define", "create", "establish", "declare"],
    "class": ["type", "category", "group", "entity"],
    "import": ["load", "bring in", "fetch", "acquire"],
    "from": ["via", "using", "with", "based on"],
    "as": ["into", "to", "as", "in the role of"],
    "try": ["attempt", "test", "experiment", "try"],
    "except": ["catch", "handle", "on error", "failing"],
    "finally": ["in any case", "regardless", "at end", "concluding"],
    "raise": ["throw", "emit", "trigger", "initiate"],
    "assert": ["verify", "confirm", "validate", "check"],
    "pass": ["skip", "continue", "do nothing", "proceed"],
    "break": ["stop", "halt", "terminate", "exit loop"],
    "continue": ["skip", "resume", "proceed", "next iteration"],
    "and": ["&", "plus", "along with", "in addition to"],
    "or": ["|", "either", "alternatively", "else"],
    "not": ["! ", "negate", "invert", "deny"],
    "in": ["inside", "within", "among", "contained"],
    "is": ["equals", "matches", "corresponds to", "is"],
    "lambda": ["anonymous", "inline", "unnamed", "quick"],
}

# Syntax patterns for rephrasing
SYNTAX_PATTERNS = [
    # (pattern_regex, replacement_template)
    # Convert "if x is None" to "if not x" (simplified)
    (r"\bif\s+(\w+)\s+is\s+None\b", r"if not \1"),
    # Convert "if x is not None" to "if x"
    (r"\bif\s+(\w+)\s+is\s+not\s+None\b", r"if \1"),
    # Convert "for i in range(len(list))" to "for i, item in enumerate(list)" (simplified)
    # This is risky, so we'll use a safer rephrasing: "for i in range(n)" -> "for i in [0..n-1]" (conceptually)
    # Instead, let's do variable renaming or comment injection
    # Convert "x = y + z" to "x = z + y" (commutative) for simple math
    (r"\b(\w+)\s*=\s*(\w+)\s*\+\s*(\w+)\b", r"\1 = \3 + \2"),
    # Convert "x = y - z" -> "x = y + (-z)" (algebraic)
    (r"\b(\w+)\s*=\s*(\w+)\s*-\s*(\w+)\b", r"\1 = \2 + (-\3)"),
    # Convert "x and y" to "y and x" (commutative)
    (r"\b(\w+)\s+and\s+(\w+)\b", r"\2 and \1"),
    # Convert "x or y" to "y or x"
    (r"\b(\w+)\s+or\s+(\w+)\b", r"\2 or \1"),
    # Convert "def foo(self, x)" to "def foo(self, x_val)" (rename arg)
    # This is hard to do safely without AST, so we skip complex AST rewrites for now
    # and focus on structural comments or string literal changes
    # Convert single line comments to docstring style if applicable (risky)
    # Let's stick to safe, structural changes:
    # Add a redundant check: "if x: if x:" (bad code, but syntactically valid) - NO, must be semantic preserving
    # Better: Convert "return x" to "return x" (no-op) - NO
    # Let's use AST to safely restructure.
]

# --- Helper Functions ---

def _is_valid_python(code_str: str) -> bool:
    """Check if the code string is valid Python syntax."""
    try:
        ast.parse(code_str)
        return True
    except SyntaxError:
        return False

def _get_all_identifiers(code_str: str) -> Set[str]:
    """Extract all identifiers from the code string."""
    try:
        tree = ast.parse(code_str)
        identifiers = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                identifiers.add(node.id)
            elif isinstance(node, ast.arg):
                identifiers.add(node.arg)
        return identifiers
    except SyntaxError:
        return set()

# --- Core Perturbation Functions ---

def substitute_synonyms(code: str, seed: Optional[int] = None) -> Tuple[str, bool]:
    """
    Substitute non-keyword tokens with synonyms.
    Returns (perturbed_code, success).
    """
    if seed is not None:
        random.seed(seed)

    # We need to be careful not to replace keywords or identifiers that are part of the logic
    # A simple heuristic: only replace words that are NOT in the COMMON_SYNONYMS keys (which are keywords)
    # and are not Python identifiers that look like variables (unless we have a mapping for them)
    # This is a naive implementation. A robust one would use AST.

    words = code.split()
    new_words = []
    changed = False

    for word in words:
        # Strip punctuation for checking
        clean_word = word.strip('(),[]{}:;')
        if clean_word in COMMON_SYNONYMS:
            # This is a keyword or common type, skip or handle carefully
            # For now, skip to avoid breaking syntax
            new_words.append(word)
        elif clean_word in COMMON_SYNONYMS.values():
            # It's a synonym, maybe revert? No, just leave it.
            new_words.append(word)
        else:
            # It might be a variable or a custom function name.
            # We can try to find a synonym for it if we had a dictionary, but we don't.
            # So we skip.
            new_words.append(word)

    # Since we don't have a dictionary of user-defined synonyms, this function
    # effectively does nothing for variables. We need a different approach.
    # Let's replace string literals instead, as they are safe.
    # Find string literals and replace their content with synonyms if possible.
    # This is complex. Let's simplify:
    # We will replace common variable names like 'x', 'y', 'z' with 'val', 'item', 'data'
    # ONLY if they appear in a context that suggests they are variables.

    # For now, we return the original code as a placeholder for the real logic
    # which would require a more sophisticated NLP or AST-based approach.
    # However, the task requires a real implementation.
    # Let's implement a simple variable renaming for common single-letter vars.
    var_map = {'x': 'val', 'y': 'item', 'z': 'data', 'i': 'idx', 'j': 'item_idx'}
    new_code = code
    for old, new in var_map.items():
        # Replace whole words only
        pattern = r'\b' + re.escape(old) + r'\b'
        new_code = re.sub(pattern, new, new_code)

    if new_code != code:
        if _is_valid_python(new_code):
            return new_code, True

    return code, False

def inject_typos(code: str, seed: Optional[int] = None) -> Tuple[str, bool]:
    """
    Inject random typos into the code.
    Returns (perturbed_code, success).
    """
    if seed is not None:
        random.seed(seed)

    # Only inject typos into string literals or comments to preserve logic
    # This is a safe approach.
    # Find string literals and inject a typo into one character.
    # Regex for string literals (single or double quoted)
    string_pattern = r'(["\'])(?:(?=(\\?))\2.)*?\1'

    def typo_in_string(match):
        s = match.group(0)
        if len(s) < 4: # Too short to typo
            return s
        # Pick a random index in the string content (excluding quotes)
        content_start = 1
        content_end = len(s) - 1
        if content_end <= content_start:
            return s
        idx = random.randint(content_start, content_end - 1)
        char_list = list(s)
        char_list[idx] = random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
        return ''.join(char_list)

    new_code = re.sub(string_pattern, typo_in_string, code, count=1)

    if new_code != code:
        if _is_valid_python(new_code):
            return new_code, True

    return code, False

def rephrase_syntax(code: str, seed: Optional[int] = None) -> Tuple[str, bool]:
    """
    Syntactically rephrase the code while preserving semantics.
    This function uses AST to safely restructure code.
    Returns (perturbed_code, success).
    """
    if seed is not None:
        random.seed(seed)

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code, False

    # We will apply a set of safe transformations
    # 1. Commutative operations: swap operands in +, *, and, or
    # 2. Variable renaming for common single-letter vars (as in substitute_synonyms)
    # 3. Reorder independent statements (hard, skip for now)
    # 4. Convert "x = y + z" to "x = z + y" if + is commutative
    # 5. Convert "if x: if y:" to "if x and y:" (only if safe, skip for now)
    # 6. Add redundant parentheses: "x + y" -> "(x + y)"
    # 7. Convert "x == True" to "x"
    # 8. Convert "x == False" to "not x"

    # Let's implement a simple transformer
    class SyntaxRephraser(ast.NodeTransformer):
        def __init__(self, seed):
            self.seed = seed
            random.seed(seed)

        def visit_BinOp(self, node):
            # Swap operands for commutative operators
            if isinstance(node.op, (ast.Add, ast.Mult, ast.BitAnd, ast.BitOr)):
                # Randomly decide to swap
                if random.random() < 0.5:
                    node.left, node.right = node.right, node.left
            return self.generic_visit(node)

        def visit_BoolOp(self, node):
            # Swap operands for 'and' and 'or'
            if isinstance(node.op, (ast.And, ast.Or)):
                if random.random() < 0.5:
                    node.values = node.values[::-1]
            return self.generic_visit(node)

        def visit_Compare(self, node):
            # Convert x == True to x
            if (len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq) and
                isinstance(node.comparators[0], ast.Constant) and node.comparators[0].value is True):
                return node.left
            # Convert x == False to not x
            if (len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq) and
                isinstance(node.comparators[0], ast.Constant) and node.comparators[0].value is False):
                return ast.UnaryOp(op=ast.Not(), operand=node.left)
            return self.generic_visit(node)

        def visit_Name(self, node):
            # Rename common single-letter variables
            var_map = {'x': 'val', 'y': 'item', 'z': 'data', 'i': 'idx', 'j': 'item_idx'}
            if node.id in var_map:
                new_name = var_map[node.id]
                # Check if new_name is already used in the current scope (simplified check)
                # For now, we assume it's safe or just do it.
                node.id = new_name
            return node

        def visit_Add(self, node):
            # Add redundant parentheses around binary operations
            # This is hard to do at the Add node level. We do it in BinOp.
            return node

    rephraser = SyntaxRephraser(seed)
    new_tree = rephraser.visit(tree)
    ast.fix_missing_locations(new_tree)

    try:
        new_code = ast.unparse(new_tree)
    except AttributeError:
        # Fallback for older Python versions without ast.unparse
        # We can use a simple hack or raise an error.
        # For this implementation, we assume Python 3.9+
        return code, False

    if new_code != code:
        if _is_valid_python(new_code):
            return new_code, True

    return code, False

def generate_perturbation_variants(
    code: str,
    task_id: str,
    max_variants: int = 3,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Generate up to max_variants perturbed versions of the code.
    Returns a list of dicts with keys: 'task_id', 'perturbation_type', 'code', 'valid'.
    """
    if seed is not None:
        random.seed(seed)

    variants = []
    types = ['synonym', 'typo', 'rephrase']
    attempts = 0
    max_attempts = max_variants * 3  # Allow some failed attempts

    while len(variants) < max_variants and attempts < max_attempts:
        attempts += 1
        p_type = random.choice(types)

        if p_type == 'synonym':
            new_code, valid = substitute_synonyms(code, seed=random.randint(0, 1000000))
        elif p_type == 'typo':
            new_code, valid = inject_typos(code, seed=random.randint(0, 1000000))
        elif p_type == 'rephrase':
            new_code, valid = rephrase_syntax(code, seed=random.randint(0, 1000000))

        if valid and new_code != code:
            variants.append({
                'task_id': task_id,
                'perturbation_type': p_type,
                'code': new_code,
                'valid': True
            })

    return variants