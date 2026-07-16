import re
import random
import json
import ast
from typing import Tuple, List, Dict, Any, Optional, Set
from collections import Counter

# Python keywords that should NOT be perturbed
KEYWORDS = set([
    "False", "None", "True", "and", "as", "assert", "break", "class", "continue",
    "def", "del", "elif", "else", "except", "finally", "for", "from", "global",
    "if", "import", "in", "is", "lambda", "nonlocal", "not", "or", "pass",
    "raise", "return", "try", "while", "with", "yield", "async", "await"
])

# Common synonyms for variable names and basic operations
# Note: This is a small subset for demonstration; a full implementation would use a larger dictionary
SYNONYMS = {
    "calculate": ["compute", "derive", "determine"],
    "process": ["handle", "manage", "treat"],
    "data": ["info", "information", "dataset"],
    "result": ["output", "outcome", "answer"],
    "value": ["val", "datum", "amount"],
    "list": ["array", "sequence", "collection"],
    "string": ["text", "str", "character"],
    "number": ["num", "integer", "digit"],
    "count": ["total", "sum", "quantity"],
    "find": ["locate", "search", "detect"],
    "create": ["make", "generate", "build"],
    "update": ["modify", "change", "edit"],
    "delete": ["remove", "erase", "clear"],
    "add": ["append", "insert", "include"],
    "remove": ["delete", "exclude", "discard"],
    "get": ["fetch", "retrieve", "obtain"],
    "set": ["assign", "define", "establish"],
    "check": ["verify", "validate", "confirm"],
    "start": ["begin", "initiate", "commence"],
    "end": ["finish", "complete", "terminate"],
    "loop": ["iterate", "cycle", "repeat"],
    "run": ["execute", "perform", "operate"],
    "load": ["read", "import", "fetch"],
    "save": ["write", "store", "record"],
    "open": ["launch", "start", "initiate"],
    "close": ["terminate", "end", "finish"],
    "print": ["display", "output", "show"],
    "input": ["read", "receive", "accept"],
    "return": ["yield", "output", "give"],
    "if": ["when", "assuming"],  # Careful with these
    "for": ["each", "every"],    # Careful with these
    "while": ["as_long_as", "during"],
}

# Typo patterns
TYPO_PATTERNS = [
    ("i", "1"), ("l", "1"), ("o", "0"), ("s", "5"), ("e", "3"), ("a", "4"),
    ("t", "7"), ("b", "8"), ("g", "9"), ("z", "2"),
    ("ss", "z"), ("ph", "f"), ("th", "th"), ("ck", "k"),
    ("e", "ie"), ("i", "ei"), ("a", "e"), ("o", "a"),
]

def _is_valid_identifier(name: str) -> bool:
    """Check if a string is a valid Python identifier."""
    return name.isidentifier() and name not in KEYWORDS

def _parse_code_to_tokens(code: str) -> List[Tuple[str, int, int]]:
    """
    Parse code into tokens with their positions.
    Returns list of (token_type, token_value, start_pos, end_pos)
    """
    tokens = []
    try:
        # Simple tokenization using regex for identifiers and keywords
        token_pattern = re.compile(r'\b(\w+)\b|\W+')
        for match in token_pattern.finditer(code):
            token = match.group(0)
            if token.strip():  # Non-whitespace
                tokens.append((token, match.start(), match.end()))
    except Exception:
        # Fallback: character by character
        for i, char in enumerate(code):
            tokens.append((char, i, i+1))
    return tokens

def _is_keyword(token: str) -> bool:
    """Check if a token is a Python keyword."""
    return token in KEYWORDS

def substitute_synonyms(code: str, seed: Optional[int] = None) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Substitute synonyms in variable names and comments while preserving syntax.
    
    Args:
        code: The original code string
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (perturbed_code, list of substitution details)
    """
    if seed is not None:
        random.seed(seed)
    
    substitutions = []
    tokens = _parse_code_to_tokens(code)
    result = list(code)
    
    # Process tokens in reverse order to maintain positions
    for token, start, end in reversed(tokens):
        # Skip if it's a keyword or not a valid identifier
        if _is_keyword(token) or not _is_valid_identifier(token):
            continue
        
        # Check if this token has synonyms
        lower_token = token.lower()
        if lower_token in SYNONYMS:
            synonyms = SYNONYMS[lower_token]
            if synonyms:
                new_token = random.choice(synonyms)
                # Ensure the new token is a valid identifier
                if _is_valid_identifier(new_token):
                    # Replace in result
                    result[start:end] = list(new_token)
                    substitutions.append({
                        "original": token,
                        "substituted": new_token,
                        "position": start,
                        "type": "synonym"
                    })
    
    return "".join(result), substitutions

def inject_typos(code: str, seed: Optional[int] = None) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Inject random typos into the code while preserving syntax structure.
    
    Args:
        code: The original code string
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (perturbed_code, list of typo details)
    """
    if seed is not None:
        random.seed(seed)
    
    typos = []
    result = list(code)
    
    # Find positions of identifiers and strings (not keywords or operators)
    token_pattern = re.compile(r'\b([a-zA-Z_]\w*)\b')
    matches = list(token_pattern.finditer(code))
    
    # Only perturb a subset of tokens (e.g., 30%)
    num_typos = max(1, int(len(matches) * 0.3))
    indices_to_perturb = random.sample(range(len(matches)), min(num_typos, len(matches)))
    
    for idx in sorted(indices_to_perturb, reverse=True):
        match = matches[idx]
        token = match.group(1)
        start, end = match.start(), match.end()
        
        # Skip keywords
        if _is_keyword(token):
            continue
        
        # Apply a random typo pattern
        typo_pattern = random.choice(TYPO_PATTERNS)
        original, replacement = typo_pattern
        
        if original in token:
            # Apply the typo
            new_token = token.replace(original, replacement, 1)
            result[start:end] = list(new_token)
            typos.append({
                "original": token,
                "typo": new_token,
                "pattern": f"{original}->{replacement}",
                "position": start,
                "type": "typo"
            })
    
    return "".join(result), typos

def rephrase_syntax(code: str, seed: Optional[int] = None) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Syntactically rephrase the code while preserving functionality.
    
    This function applies transformations such as:
    - Converting for loops to while loops (and vice versa)
    - Changing list comprehensions to explicit loops
    - Reordering independent statements
    - Converting between equivalent syntax forms
    
    Args:
        code: The original code string
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (perturbed_code, list of rephrasing details)
    """
    if seed is not None:
        random.seed(seed)
    
    rephrasings = []
    
    try:
        # Parse the code to AST to ensure validity
        tree = ast.parse(code)
        
        # Apply transformations
        transformed_tree = _apply_syntax_rephrasing(tree, rephrasings)
        
        # Convert back to code
        new_code = ast.unparse(transformed_tree)
        
        return new_code, rephrasings
        
    except SyntaxError:
        # If parsing fails, return original code
        return code, []

def _apply_syntax_rephrasing(node: ast.AST, rephrasings: List[Dict[str, Any]]) -> ast.AST:
    """
    Apply syntax rephrasing transformations to an AST node.
    """
    # Convert for loops to while loops
    if isinstance(node, ast.For):
        # Create equivalent while loop
        loop_var = node.target
        iter_expr = node.iter
        
        # Create a temporary variable for the iterator
        temp_var = ast.Name(id='__iterator__', ctx=ast.Load())
        
        # Build the while loop condition and body
        # This is a simplified transformation
        while_loop = ast.While(
            test=ast.Constant(value=True),  # Always true, break inside
            body=node.body + node.orelse,
            orelse=[]
        )
        
        # Add iterator initialization
        init_assign = ast.Assign(
            targets=[temp_var],
            value=iter_expr
        )
        
        # Add next() call and break condition
        next_call = ast.Call(
            func=ast.Name(id='next', ctx=ast.Load()),
            args=[temp_var],
            keywords=[]
        )
        
        # Create assignment from next() result
        assign_next = ast.Assign(
            targets=[loop_var],
            value=next_call
        )
        
        # Add try-except for StopIteration
        try_block = ast.Try(
            body=[assign_next] + node.body,
            handlers=[ast.ExceptHandler(
                type=ast.Name(id='StopIteration', ctx=ast.Load()),
                name=None,
                body=[ast.Break()]
            )],
            orelse=[],
            finalbody=[]
        )
        
        while_loop.body = [init_assign, try_block]
        
        rephrasings.append({
            "original_type": "For",
            "new_type": "While",
            "description": "Converted for loop to while loop"
        })
        
        return ast.copy_location(while_loop, node)
    
    # Convert list comprehensions to explicit loops
    elif isinstance(node, ast.ListComp):
        # Create explicit loop
        result_var = ast.Name(id='__result__', ctx=ast.Store())
        result_list = ast.List(elists=[], ctx=ast.Load())
        
        # This is a simplified transformation
        # In practice, we'd need to handle nested comprehensions
        explicit_loop = ast.For(
            target=node.generators[0].target,
            iter=node.generators[0].iter,
            body=[
                ast.Assign(
                    targets=[result_var],
                    value=ast.Call(
                        func=ast.Attribute(
                            value=result_list,
                            attr='append',
                            ctx=ast.Load()
                        ),
                        args=[node.elt],
                        keywords=[]
                    )
                )
            ],
            orelse=[]
        )
        
        rephrasings.append({
            "original_type": "ListComp",
            "new_type": "For",
            "description": "Converted list comprehension to explicit loop"
        })
        
        return ast.copy_location(explicit_loop, node)
    
    # Recursively process child nodes
    else:
        for field, old_value in ast.iter_fields(node):
            if isinstance(old_value, list):
                new_values = []
                for item in old_value:
                    if isinstance(item, ast.AST):
                        new_values.append(_apply_syntax_rephrasing(item, rephrasings))
                    else:
                        new_values.append(item)
                setattr(node, field, new_values)
            elif isinstance(old_value, ast.AST):
                setattr(node, field, _apply_syntax_rephrasing(old_value, rephrasings))
        
        return node

def generate_perturbation_variants(
    code: str,
    num_variants: int = 3,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Generate multiple perturbation variants of the given code.
    
    Args:
        code: The original code string
        num_variants: Number of variants to generate (up to 3)
        seed: Random seed for reproducibility
        
    Returns:
        List of perturbation dictionaries with type, code, and details
    """
    if seed is not None:
        random.seed(seed)
    
    variants = []
    perturbation_types = ["synonym", "typo", "rephrase"]
    
    # Generate up to num_variants different types of perturbations
    for i in range(min(num_variants, len(perturbation_types))):
        p_type = perturbation_types[i]
        
        if p_type == "synonym":
            perturbed_code, details = substitute_synonyms(code, seed=seed+i)
        elif p_type == "typo":
            perturbed_code, details = inject_typos(code, seed=seed+i)
        elif p_type == "rephrase":
            perturbed_code, details = rephrase_syntax(code, seed=seed+i)
        else:
            continue
        
        variants.append({
            "type": p_type,
            "code": perturbed_code,
            "details": details,
            "original_code": code
        })
    
    return variants