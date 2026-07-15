"""
Text Executor for llmXive pipeline.

Executes queries against the MS MARCO subset using standard string matching
and SQLite logic. Measures real wall-clock time and scales operations
based on the query's `complexity_level`.
"""
import os
import time
import sqlite3
import random
from typing import Dict, Any, List, Optional
from pathlib import Path

# Import config for paths and dataset URLs
# Note: We assume config.py is in the same package structure as defined in API surface
try:
    from ..config import DATASET_URLS, DATA_PATH, EXIT_CODE_THROTTLING_FAILURE
except ImportError:
    # Fallback for direct execution or different import context
    from config import DATASET_URLS, DATA_PATH, EXIT_CODE_THROTTLING_FAILURE

# Import throttling context
try:
    from ..utils.cpu_throttle import throttled_context, ThrottleError
except ImportError:
    from utils.cpu_throttle import throttled_context, ThrottleError

from .base import BaseExecutor

class TextExecutor(BaseExecutor):
    """
    Executor for text-based queries using MS MARCO subset.
    
    Implements logic proportional to `complexity_level` to simulate
    varying computational loads without using time.sleep.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.db_path: Optional[str] = None
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self._load_dataset()
    
    def _load_dataset(self) -> None:
        """
        Loads the MS MARCO subset into an in-memory SQLite database.
        Uses the URL defined in config.py.
        """
        dataset_url = DATASET_URLS.get("ms_marco_subset")
        if not dataset_url:
            raise ValueError("MS MARCO subset URL not found in config.")
        
        # Ensure data directory exists
        data_dir = Path(DATA_PATH)
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # In a real scenario, we would fetch the file if missing.
        # For this executor, we assume the data_fetcher (T016c) has populated
        # the local file or we fetch it here if strictly necessary.
        # To keep this executor self-contained for the task requirement:
        # We will fetch the dataset using the datasets library if not present.
        
        db_file = data_dir / "ms_marco_sample.db"
        
        if not db_file.exists():
            self._fetch_and_init_db(dataset_url, str(db_file))
        
        self.db_path = str(db_file)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
    
    def _fetch_and_init_db(self, url: str, db_path: str) -> None:
        """
        Fetches the dataset using HuggingFace datasets and initializes SQLite.
        """
        try:
            from datasets import load_dataset
        except ImportError:
            raise ImportError("The 'datasets' package is required. Install via pip.")
        
        # Load a small subset of MS MARCO v1.1 for demonstration
        # We use a specific configuration or filter to keep it small
        print(f"Loading MS MARCO subset from {url}...")
        try:
            # Using a public subset or loading the full set and sampling
            # MS MARCO is large, so we load a subset or sample immediately
            dataset = load_dataset("ms_marco", "v1.1", split="train", streaming=True)
            
            # Create SQLite DB
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS passages (
                    pid INTEGER PRIMARY KEY,
                    text TEXT,
                    title TEXT
                )
            ''')
            
            # Insert a sample of 10,000 rows to ensure meaningful execution time
            # without taking forever.
            count = 0
            batch = []
            for row in dataset:
                if count >= 10000:
                    break
                batch.append((row['pid'], row['text'], row['title']))
                if len(batch) >= 500:
                    c.executemany('INSERT INTO passages VALUES (?,?,?)', batch)
                    conn.commit()
                    batch = []
                count += 1
            
            if batch:
                c.executemany('INSERT INTO passages VALUES (?,?,?)', batch)
                conn.commit()
            
            conn.close()
            print(f"Database initialized with {count} rows.")
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch and initialize MS MARCO dataset: {e}")

    def _execute_complexity_logic(self, complexity_level: int, query_text: str) -> Dict[str, Any]:
        """
        Executes logic proportional to complexity_level.
        
        Complexity mapping:
        1: Simple lookup (1 row)
        2: Lookup + simple aggregation (COUNT)
        3: Lookup + Join simulation (self-join or multiple lookups)
        4+: Complex aggregation + multiple iterations
        
        This does NOT use time.sleep. It performs real I/O and CPU work.
        """
        results = []
        start_time = time.perf_counter()
        
        # Base operation: Simple search
        # We simulate a search by looking for keywords in the text column
        # Using LIKE is efficient enough for this sample size but real work
        cursor = self.conn.cursor()
        
        if complexity_level == 1:
            # Level 1: Simple retrieval
            cursor.execute("SELECT text FROM passages WHERE text LIKE ? LIMIT 10", (f"%{query_text}%",))
            results = cursor.fetchall()
            # Add a tiny bit of CPU work to ensure non-zero time even for fast queries
            _ = sum([x for x in range(100)])
            
        elif complexity_level == 2:
            # Level 2: Aggregation
            cursor.execute("SELECT COUNT(*) FROM passages WHERE text LIKE ?", (f"%{query_text}%",))
            count = cursor.fetchone()[0]
            results = [("Count", count)]
            # Simulate more work
            for _ in range(500):
                cursor.execute("SELECT text FROM passages LIMIT 1")
                _ = cursor.fetchone()
                
        elif complexity_level == 3:
            # Level 3: Multiple lookups (simulating a join or multi-step retrieval)
            # Fetch a set of IDs, then fetch details for each
            cursor.execute("SELECT pid FROM passages WHERE text LIKE ? LIMIT 20", (f"%{query_text}%",))
            pids = [row[0] for row in cursor.fetchall()]
            
            for pid in pids:
                cursor.execute("SELECT text, title FROM passages WHERE pid = ?", (pid,))
                row = cursor.fetchone()
                if row:
                    results.append(row)
            
            # Add computational load
            _ = sum([i*i for i in range(2000)])
            
        elif complexity_level >= 4:
            # Level 4+: Complex aggregation and multiple passes
            # Pass 1: Get a subset
            cursor.execute("SELECT pid, text FROM passages WHERE text LIKE ? LIMIT 50", (f"%{query_text}%",))
            subset = cursor.fetchall()
            
            # Pass 2: Aggregation on the subset (simulating in-memory processing)
            total_length = 0
            for pid, text in subset:
                total_length += len(text)
                # Simulate text processing
                words = text.split()
                _ = [w.upper() for w in words]
            
            # Pass 3: Heavy CPU load
            for _ in range(5):
                _ = sum([i**2 for i in range(10000)])
            
            results = [("Total Length", total_length), ("Items Processed", len(subset))]
        else:
            # Fallback for unexpected levels
            cursor.execute("SELECT text FROM passages LIMIT 1")
            results = cursor.fetchall()
        
        end_time = time.perf_counter()
        return {
            "results": results,
            "duration_ms": (end_time - start_time) * 1000,
            "complexity_level": complexity_level
        }

    def execute(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a query dictionary.
        
        Args:
            query: A dictionary containing at least 'text' and 'complexity_level'.
        
        Returns:
            A dictionary containing execution metrics and results.
        """
        if not self.conn:
            raise RuntimeError("Database connection not established.")
        
        query_text = query.get("text", "")
        complexity = query.get("complexity_level", 1)
        
        if not isinstance(complexity, int) or complexity < 1:
            complexity = 1
        
        try:
            # We do not wrap in throttled_context here because the main.py
            # orchestration (T012) is expected to handle the global context.
            # However, we ensure we measure real time.
            execution_result = self._execute_complexity_logic(complexity, query_text)
            
            return {
                "success": True,
                "latency_ms": execution_result["duration_ms"],
                "results": execution_result["results"],
                "query_id": query.get("id", "unknown"),
                "source_type": "text",
                "complexity_level": complexity
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query_id": query.get("id", "unknown"),
                "source_type": "text"
            }

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

def main():
    """
    Standalone test runner for TextExecutor.
    """
    # Mock config
    config = {
        "timeout_limit": 300,
        "seed": 42
    }
    
    executor = TextExecutor(config)
    
    # Test queries with different complexity levels
    test_queries = [
        {"id": "q1", "text": "what is", "complexity_level": 1},
        {"id": "q2", "text": "how to", "complexity_level": 2},
        {"id": "q3", "text": "python", "complexity_level": 3},
        {"id": "q4", "text": "machine learning", "complexity_level": 4},
    ]
    
    print("Running TextExecutor tests...")
    for q in test_queries:
        result = executor.execute(q)
        print(f"Query {q['id']} (Level {q['complexity_level']}): "
              f"Success={result['success']}, Latency={result.get('latency_ms', 0):.2f}ms")
    
    executor.close()
    print("TextExecutor tests completed.")

if __name__ == "__main__":
    main()
