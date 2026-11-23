# FastContext-Lite API Reference

This module implements a lightweight, CPU-efficient context exploration pipeline for coding agents.
It uses TF-IDF similarity to retrieve relevant code snippets from a repository based on an issue description.

## Classes

### `TfidfIndex`

A wrapper class for managing TF-IDF vectorization and search operations.

**Attributes:**
- `vectorizer`: The `TfidfVectorizer` instance.
- `documents`: List of document strings (code snippets).
- `filenames`: List of file paths corresponding to the documents.

**Methods:**
- `build(documents, filenames)`: Initializes the index with documents and metadata.
- `search(query, top_k)`: Returns the top-k most similar documents for a given query string.

## Functions

### `extract_keywords(text: str) -> List[str]`

Extracts significant keywords from an issue description or query string.

**Parameters:**
- `text` (str): The input text to process.

**Returns:**
- `List[str]`: List of cleaned, lowercased keywords.

### `stream_file_lines(file_path: Path) -> Iterator[str]`

Generator that yields lines from a file, handling large files efficiently.

**Parameters:**
- `file_path` (Path): Path to the file.

**Yields:**
- `str`: Each line from the file.

### `chunk_file_content(file_path: Path, window_size: int = 50, step: int = 25) -> Iterator[Dict[str, str]]`

Sliding window chunking of a file's content to create manageable snippets for indexing.

**Parameters:**
- `file_path` (Path): Path to the file.
- `window_size` (int): Number of lines per chunk.
- `step` (int): Number of lines to shift the window.

**Yields:**
- `Dict[str, str]`: Dictionary containing `content` (str) and `file_path` (str).

### `build_tfidf_index(repo_path: Path) -> TfidfIndex`

Scans a repository, chunks Python files, and builds a TF-IDF index.

**Parameters:**
- `repo_path` (Path): Path to the repository root.

**Returns:**
- `TfidfIndex`: The populated index.

### `search_tfidf(index: TfidfIndex, query: str, top_k: int = 5) -> List[Dict[str, Any]]`

Searches the index for the most relevant snippets.

**Parameters:**
- `index` (TfidfIndex): The built index.
- `query` (str): The search query (issue description).
- `top_k` (int): Number of results to return.

**Returns:**
- `List[Dict[str, Any]]`: List of snippets with metadata (content, score, file_path).

### `filter_files_by_target_dirs(repo_path: Path, target_dirs: List[str]) -> List[Path]`

Filters the file list to only include files within specified target directories (e.g., `src/`, `tests/`).

**Parameters:**
- `repo_path` (Path): Repository root.
- `target_dirs` (List[str]): List of directory names to filter by.

**Returns:**
- `List[Path]`: List of matching file paths.

### `extract_snippets(index: TfidfIndex, query: str, top_k: int = 5) -> Dict[str, Any]`

High-level function to retrieve snippets for a given query.

**Parameters:**
- `index` (TfidfIndex): The index.
- `query` (str): The query string.
- `top_k` (int): Number of snippets.

**Returns:**
- `Dict[str, Any]`: Dictionary containing `retrieved_snippets` and `token_count`.

### `run_fastcontext_lite(repo_path: Path, issue_description: str, top_k: int = 5) -> Dict[str, Any]`

Executes the full FastContext-Lite pipeline on a repository for a given issue.

**Parameters:**
- `repo_path` (Path): Path to the repository.
- `issue_description` (str): The issue text to search for.
- `top_k` (int): Number of snippets to retrieve.

**Returns:**
- `Dict[str, Any]`: Result dictionary containing retrieved snippets and token usage metrics.

### `main()`

CLI entry point for running FastContext-Lite.

**Usage:**
```bash
python -m fastcontext_lite --repo /path/to/repo --issue "Fix bug in parser"
```
