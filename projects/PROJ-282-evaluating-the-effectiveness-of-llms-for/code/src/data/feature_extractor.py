import os
import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# Imports from existing project surface
from src.utils.logger import get_logger
from src.models.feature_vector import FeatureVector, create_feature_vector

# Tree-sitter imports (dependency listed in T002 requirements.txt)
try:
    from tree_sitter import Language, Parser
    import tree_sitter_c
    import tree_sitter_python
    import tree_sitter_javascript
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    logging.warning("tree-sitter libraries not installed. Structural metrics will be 0.")

# Logger setup
logger = get_logger(__name__)

# --- Semantic Metrics Configuration ---

# Taint Source APIs (Common entry points for untrusted data)
# C/C++
TAINT_APIS_C = {
    'gets', 'scanf', 'fscanf', 'sscanf', 'fgets', 'getenv',
    'memcpy', 'memmove', 'strcpy', 'strncpy', 'strcat', 'strncat',
    'sprintf', 'vsprintf', 'snprintf', 'vsnprintf',
    'read', 'recv', 'recvfrom', 'readv', 'pread',
    'fopen', 'freopen', 'fdopen',
    'system', 'popen', 'execl', 'execle', 'execlp', 'execv', 'execve', 'execvp',
    'shell_exec', 'system', 'popen' # PHP aliases often found in C contexts or mixed
}

# Python
TAINT_APIS_PY = {
    'input', 'raw_input', 'open', 'file',
    'eval', 'exec', 'execfile',
    'pickle.loads', 'marshal.loads', 'yaml.load',
    'os.system', 'os.popen', 'os.spawn', 'os.execl', 'os.execlp', 'os.execle', 'os.execv', 'os.execvp', 'os.execve',
    'subprocess.call', 'subprocess.run', 'subprocess.Popen',
    'socket.recv', 'socket.recvfrom', 'socket.recvfrom_into',
    'cgi.FieldStorage',
    'flask.request.form', 'flask.request.args', 'flask.request.json', 'flask.request.data',
    'django.http.request.POST', 'django.http.request.GET', 'django.http.request.FILES',
    'sqlite3.connect', 'MySQLdb.connect', 'psycopg2.connect' # DB connections often sources if not parameterized
}

# JavaScript
TAINT_APIS_JS = {
    'eval', 'setTimeout', 'setInterval', 'Function',
    'document.write', 'document.writeln',
    'innerHTML', 'outerHTML',
    'location.href', 'location.search', 'location.hash',
    'request.body', 'request.query', 'request.params', 'request.headers',
    'fs.readFileSync', 'fs.readFile',
    'child_process.exec', 'child_process.execFile', 'child_process.spawn',
    'XMLHttpRequest', 'fetch',
    'require' # Potential RCE if dynamic
}

# Sanitization Functions (Escaping, Validation, Filtering)
# C/C++
SANITIZERS_C = {
    'snprintf', 'strncpy', 'strncat', 'memcpy_s', 'memmove_s',
    'strcpy_s', 'strcat_s', 'strtok_s',
    'sscanf', 'fscanf', 'vsscanf', 'vfscanf', 'vfwscanf', 'vswscanf',
    'gets_s',
    'setenv', 'unsetenv',
    'filter_input', 'filter_var', # PHP functions often seen in C-like syntax contexts
    'htmlentities', 'htmlspecialchars', 'mysql_real_escape_string', 'mysqli_real_escape_string'
}

# Python
SANITIZERS_PY = {
    'escape', 'html.escape', 'cgi.escape',
    'quote', 'quote_plus', 'urlencode',
    'sanitize', 'validate',
    'json.dumps', # Safe serialization
    're.sub', # Filtering
    'strip', 'lstrip', 'rstrip',
    'mysql_real_escape_string', 'sqlite3.escape_string', # DB specific
    'werkzeug.security.generate_password_hash',
    'paramiko' # SSH handling
}

# JavaScript
SANITIZERS_JS = {
    'escape', 'encodeURI', 'encodeURIComponent',
    'html.escape', 'he.encode', # 'he' library
    'DOMPurify.sanitize',
    'escapeHtml', 'escapeHtml2', 'escapeHtml3',
    'sanitize', 'filter',
    'replace', 'replaceAll',
    'mysql_real_escape_string', # Node.js mysql lib
    'escapeRegExp',
    'JSON.stringify'
}

def _count_api_occurrences(code: str, apis: set) -> int:
    """
    Count occurrences of known taint APIs or sanitizers in code.
    Uses regex word boundaries to avoid partial matches (e.g., 'input' vs 'inputs').
    """
    count = 0
    for api in apis:
        # Escape special regex characters in API names
        escaped_api = re.escape(api)
        # Match word boundaries or common separators (dot, space, start/end)
        # We look for the API name followed by a non-identifier char or end of string
        pattern = r'\b' + escaped_api + r'\b'
        matches = re.findall(pattern, code, re.IGNORECASE)
        count += len(matches)
    return count

def _detect_sanitization_present(code: str, language: str) -> bool:
    """
    Detect presence of sanitization functions using regex.
    Returns True if at least one sanitizer is found.
    """
    if language.lower() in ['c', 'cpp', 'c++']:
        apis = SANITIZERS_C
    elif language.lower() in ['python', 'py']:
        apis = SANITIZERS_PY
    elif language.lower() in ['javascript', 'js', 'ts']:
        apis = SANITIZERS_JS
    else:
        # Fallback to union if language unknown, or empty
        apis = SANITIZERS_C.union(SANITIZERS_PY).union(SANITIZERS_JS)

    for api in apis:
        escaped_api = re.escape(api)
        pattern = r'\b' + escaped_api + r'\b'
        if re.search(pattern, code, re.IGNORECASE):
            return True
    return False

def extract_semantic_features(code: str, language: str) -> Tuple[int, bool]:
    """
    Extract semantic metrics for a code snippet.

    Args:
        code (str): The source code string.
        language (str): The programming language (C, Python, JavaScript).

    Returns:
        Tuple[int, bool]: (taint_api_count, sanitization_present)
    """
    if not code:
        return 0, False

    # 1. Taint Source Count
    if language.lower() in ['c', 'cpp', 'c++']:
        taint_apis = TAINT_APIS_C
    elif language.lower() in ['python', 'py']:
        taint_apis = TAINT_APIS_PY
    elif language.lower() in ['javascript', 'js', 'ts']:
        taint_apis = TAINT_APIS_JS
    else:
        # Default to empty set if language unknown to avoid false positives
        taint_apis = set()

    taint_count = _count_api_occurrences(code, taint_apis)

    # 2. Sanitization Presence
    sanitization_present = _detect_sanitization_present(code, language)

    logger.debug(f"Semantic features for {language}: taint_count={taint_count}, sanitization={sanitization_present}")

    return taint_count, sanitization_present

def extract_features_for_snippet(
    snippet_id: str,
    code: str,
    language: str,
    structural_features: Optional[Dict[str, int]] = None,
    embedding_score: Optional[float] = None
) -> FeatureVector:
    """
    Extract all features (structural + semantic + embedding) for a single snippet.

    Args:
        snippet_id: Unique ID for the snippet.
        code: Source code.
        language: Programming language.
        structural_features: Pre-computed structural metrics (optional).
        embedding_score: Pre-computed embedding similarity (optional).

    Returns:
        FeatureVector object.
    """
    # If structural features not provided, calculate them (or default to 0 if tree-sitter missing)
    if structural_features is None:
        if TREE_SITTER_AVAILABLE:
            # Placeholder: In a real pipeline, we'd call extract_structural_features here
            # For this specific task T018b, we assume structural features might be passed or calculated elsewhere.
            # To ensure this function is self-contained for the semantic part, we default to 0 if not passed.
            ast_depth = 0
            node_count = 0
            cyclomatic_complexity = 0
        else:
            ast_depth = 0
            node_count = 0
            cyclomatic_complexity = 0
    else:
        ast_depth = structural_features.get('ast_depth', 0)
        node_count = structural_features.get('node_count', 0)
        cyclomatic_complexity = structural_features.get('cyclomatic_complexity', 0)

    # Extract Semantic Features (The core of T018b)
    taint_api_count, sanitization_present = extract_semantic_features(code, language)

    # Embedding score (default to 0 if not provided)
    if embedding_score is None:
        embedding_score = 0.0

    return create_feature_vector(
        snippet_id=snippet_id,
        ast_depth=ast_depth,
        cyclomatic_complexity=cyclomatic_complexity,
        node_count=node_count,
        taint_api_count=taint_api_count,
        sanitization_present=sanitization_present,
        embedding_similarity_score=embedding_score
    )

def batch_extract_features(
    snippets: List[Dict[str, Any]],
    structural_features_map: Optional[Dict[str, Dict[str, int]]] = None,
    embedding_scores_map: Optional[Dict[str, float]] = None
) -> List[FeatureVector]:
    """
    Batch extract features for a list of snippets.

    Args:
        snippets: List of dicts with 'id', 'code', 'language'.
        structural_features_map: Map of snippet_id -> structural features.
        embedding_scores_map: Map of snippet_id -> embedding score.

    Returns:
        List of FeatureVector objects.
    """
    results = []
    for snippet in snippets:
        sid = snippet['id']
        code = snippet['code']
        lang = snippet['language']

        s_feat = None
        if structural_features_map:
            s_feat = structural_features_map.get(sid)

        e_score = None
        if embedding_scores_map:
            e_score = embedding_scores_map.get(sid)

        feat_vec = extract_features_for_snippet(
            snippet_id=sid,
            code=code,
            language=lang,
            structural_features=s_feat,
            embedding_score=e_score
        )
        results.append(feat_vec)

    return results

def main():
    """
    Main entry point for testing feature extraction.
    """
    logger.info("Starting Feature Extractor (Semantic Metrics) Test")

    # Test cases
    test_snippets = [
        {
            "id": "test_py_1",
            "code": "user_input = input('Enter name: ')\nsql = 'SELECT * FROM users WHERE name = ' + user_input\nexec(sql)",
            "language": "python"
        },
        {
            "id": "test_c_1",
            "code": "char buffer[100];\ngets(buffer);\nsprintf(buffer, \"Hello %s\", buffer);",
            "language": "c"
        },
        {
            "id": "test_js_1",
            "code": "var user = req.query.id;\ndocument.write('<h1>' + user + '</h1>');",
            "language": "javascript"
        },
        {
            "id": "test_safe_py",
            "code": "import sqlite3\nconn = sqlite3.connect('db.sqlite')\ncursor = conn.cursor()\nuser = input('Enter name')\ncursor.execute('SELECT * FROM users WHERE name = ?', (user,))",
            "language": "python"
        }
    ]

    for snippet in test_snippets:
        feat = extract_features_for_snippet(
            snippet_id=snippet['id'],
            code=snippet['code'],
            language=snippet['language']
        )
        logger.info(f"Snippet {snippet['id']} ({snippet['language']}): "
                    f"Taint={feat.taint_api_count}, Sanitized={feat.sanitization_present}")

    logger.info("Feature Extractor Test Complete")

if __name__ == "__main__":
    main()
