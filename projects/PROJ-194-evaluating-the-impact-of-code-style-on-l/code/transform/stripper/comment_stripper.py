"""
Comment and docstring stripper implementation.
Removes comments and docstrings from input code while preserving logic.
Also preserves the original docstring in a separate return value for ground truth verification.
"""
import ast
import re
from typing import Optional, Tuple

class CommentRemover(ast.NodeTransformer):
    """
    AST NodeTransformer that removes comments and docstrings.
    Preserves the first docstring (module, class, or function) in a side attribute
    to allow retrieval of the ground truth.
    """
    def __init__(self):
        self.original_docstring: Optional[str] = None
        self._found_first_docstring = False

    def visit_Expr(self, node: ast.Expr) -> Optional[ast.Expr]:
        # Check if the expression is a docstring or a standalone string literal
        # Docstrings are the first statement in a module, class, or function body
        # and are of type Constant (or Str in older Python) with a string value.
        
        # We need to determine if this Expr is actually a docstring.
        # In the AST, docstrings are just Expr nodes containing a Constant string
        # that appears as the first child of a FunctionDef, ClassDef, or Module.
        # Since we don't have parent context easily here without a custom walker,
        # we rely on the fact that we visit the parent node (FunctionDef etc)
        # and check its body[0].
        
        # However, a simpler heuristic for a "stripper" that removes ALL comments/docstrings
        # except we want to *capture* the first one for ground truth:
        # We will check if this is the first string expression encountered in the tree
        # that acts as a docstring.
        
        # To correctly handle "first docstring" logic, we usually inspect the parent.
        # Since NodeTransformer doesn't pass parent by default, we'll use a different approach:
        # We will visit the node, and if it's a string constant in an Expr, we check
        # if it looks like a docstring (is it the first child of a def/class/module?).
        # But without parent pointers, we can't be 100% sure.
        
        # Alternative: Use the `ast.get_docstring` helper on the parent nodes.
        # But we are transforming the tree.
        
        # Let's refine the strategy:
        # 1. We want to remove ALL comments (handled by ast not preserving them usually, but we need to remove docstrings).
        # 2. We want to capture the FIRST docstring found in the tree (module level or first function/class).
        
        # Actually, `ast.parse` removes comments from the tree entirely.
        # The only "comments" left are docstrings (which are string literals).
        # So we just need to remove string literals that are docstrings.
        # And we need to save the first one.
        
        # How to identify a docstring in the AST?
        # It is an `ast.Expr` containing an `ast.Constant` (str) that is the first element
        # of the `body` list of a `Module`, `FunctionDef`, `AsyncFunctionDef`, `ClassDef`, or `AsyncWith` (rare).
        
        # Since we are in `visit_Expr`, we don't know the parent.
        # Let's change strategy: We will not use `NodeTransformer` to remove them in one pass.
        # Instead, we will walk the tree, identify docstrings, save the first one, and remove them.
        
        # Wait, the prompt asks to "remove comments and docstrings... while preserving the original docstring for ground truth".
        # This implies we need to output two things: the stripped code, and the original docstring.
        
        # Let's implement a custom walker that collects the first docstring and removes all docstrings.
        
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            # This is a string literal. Is it a docstring?
            # We can't be sure without parent context.
            # However, in the context of a "stripper", usually we assume the first string in a body is a docstring.
            # But `ast.unparse` will put it back if we don't remove it.
            # The only way to reliably remove docstrings is to modify the parent's body list.
            # But `NodeTransformer` replaces nodes, it doesn't modify parents directly.
            
            # Correct approach:
            # We need to know if this `node` is the first element of its parent's body.
            # Since we can't easily get the parent in `visit_Expr`, let's try a different method.
            # We can use `ast.fix_missing_locations` or just rely on the fact that
            # we can visit the parent nodes (FunctionDef, etc) and filter their body.
            pass
        
        return node

def _get_first_docstring(tree: ast.AST) -> Optional[str]:
    """
    Recursively find the first docstring in the AST.
    Returns the string content or None.
    """
    if isinstance(tree, ast.Module):
        if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
            return tree.body[0].value.value
        # Check children
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                    return node.body[0].value.value
    elif isinstance(tree, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
            return tree.body[0].value.value
    return None

def _remove_docstrings(tree: ast.AST) -> ast.AST:
    """
    Remove all docstrings (first string literal in body) from the AST.
    Returns the modified tree.
    """
    class DocstringRemover(ast.NodeTransformer):
        def visit_Module(self, node: ast.Module) -> ast.Module:
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                node.body.pop(0)
            self.generic_visit(node)
            return node

        def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                node.body.pop(0)
            self.generic_visit(node)
            return node

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                node.body.pop(0)
            self.generic_visit(node)
            return node

        def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                node.body.pop(0)
            self.generic_visit(node)
            return node

    remover = DocstringRemover()
    return remover.visit(tree)

class CommentRemover:
    """
    High-level class to strip comments and docstrings.
    Since AST does not represent comments (only docstrings as strings),
    we use AST to remove docstrings and regex to remove line comments.
    """
    def __init__(self):
        self.original_docstring: Optional[str] = None

    def strip(self, code: str) -> Tuple[str, Optional[str]]:
        """
        Strip comments and docstrings from code.
        Returns (stripped_code, original_docstring).
        """
        if not code.strip():
            return code, None

        # 1. Extract the first docstring for ground truth
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise SyntaxError(f"Invalid Python syntax in input: {e}")

        self.original_docstring = _get_first_docstring(tree)

        # 2. Remove docstrings from the AST
        tree_no_docstrings = _remove_docstrings(tree)

        # 3. Convert back to code
        try:
            stripped_code = ast.unparse(tree_no_docstrings)
        except AttributeError:
            raise RuntimeError("ast.unparse is not available. Python 3.9+ required.")

        # 4. Remove line comments (# ...) and block comments (if any, though AST doesn't see them)
        # Since we unparsed, the comments are gone (AST doesn't store them).
        # However, if there were comments that were NOT docstrings, they were never in the AST.
        # So `ast.unparse` naturally produces code without comments.
        # We just need to ensure we didn't lose logic.
        
        # The only thing `ast` doesn't capture is comments like `# this is a comment`.
        # So `ast.unparse` effectively strips all comments (docstrings and line comments).
        # The only issue is if we need to preserve the *original* docstring string content
        # which we did in step 1.

        return stripped_code, self.original_docstring

def strip_comments_and_docstrings(code: str) -> str:
    """
    Remove comments and docstrings from the provided code string.
    
    Args:
        code: Python code string.
    
    Returns:
        Code string without comments and docstrings.
        (Note: The original docstring is lost in this return value.
         Use the class method `CommentRemover().strip()` if the original docstring is needed).
    """
    remover = CommentRemover()
    stripped, _ = remover.strip(code)
    return stripped

def main():
    """Test the stripper."""
    sample = '''
    def foo():
        """This is a docstring."""
        # This is a comment
        x = 1
        # Another comment
        return x
    '''
    remover = CommentRemover()
    stripped, original = remover.strip(sample)
    print("Original Docstring:", repr(original))
    print("Stripped Code:")
    print(stripped)

if __name__ == "__main__":
    main()