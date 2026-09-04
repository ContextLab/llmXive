import os
import re
import ast
import sys
import hashlib
from typing import Optional, Iterator, Dict, Any, List, Set, Tuple
from dataclasses import dataclass, field
import json
import logging

from datasets import load_dataset
import pyarrow.parquet as pq
from io import BytesIO

from config import get_data_dir

@dataclass
class ParsedIssue:
    issue_id: str
    description: str
    extracted_files: List[str] = field(default_factory=list)

class ClawSweBenchLoader:
    def __init__(self, dataset_name: str = "princeton-nlp/Claw-SWE-Bench"):
        self.dataset_name = dataset_name
        self.dataset = None
        self.logger = logging.getLogger(__name__)

    def load_streaming(self) -> Iterator[Dict[str, Any]]:
        """Load dataset with streaming. Fails loudly if fetch fails."""
        try:
            self.dataset = load_dataset(
                self.dataset_name,
                split="train",
                streaming=True
            )
            return iter(self.dataset)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch real dataset '{self.dataset_name}': {e}")

    def extract_starting_files(self, issue_text: str) -> List[str]:
        """
        Extract file paths mentioned in the issue text.
        Method: Regex and AST-based extraction (simplified for text).
        """
        # Simple regex for common file patterns (e.g., src/file.py, tests/test_*.py)
        pattern = r'(?:^|[\s/])(src/|tests/|lib/|app/)[a-zA-Z0-9_/\.-]+\.(py|js|ts|java)'
        matches = re.findall(pattern, issue_text)
        # Reconstruct paths
        paths = ["".join(m) for m in matches]
        return list(set(paths))

    def parse_issue(self, record: Dict[str, Any]) -> ParsedIssue:
        issue_id = record.get("issue_id", "unknown")
        description = record.get("text", "")
        extracted_files = self.extract_starting_files(description)
        return ParsedIssue(
            issue_id=issue_id,
            description=description,
            extracted_files=extracted_files
        )

    def validate_issue_sufficiency(self, parsed: ParsedIssue) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate if issue text is sufficient to reconstruct dependency graph.
        Returns (is_sufficient, metrics).
        """
        extracted_n_files = len(parsed.extracted_files)
        is_sufficient = extracted_n_files > 0
        metrics = {
            "extracted_n_files": extracted_n_files,
            "threshold": 1,
            "issue_id": parsed.issue_id
        }
        return is_sufficient, metrics

    def generate_validation_report(self, output_path: str) -> None:
        """
        Iterate through dataset, validate each issue, and write a report.
        """
        loader = self.load_streaming()
        report_data = {
            "total_issues": 0,
            "sufficient_issues": 0,
            "insufficient_issues": 0,
            "details": []
        }

        for record in loader:
            parsed = self.parse_issue(record)
            is_suff, metrics = self.validate_issue_sufficiency(parsed)
            report_data["total_issues"] += 1
            if is_suff:
                report_data["sufficient_issues"] += 1
            else:
                report_data["insufficient_issues"] += 1
            
            # Limit details to first 100 for report size, or full if small
            if len(report_data["details"]) < 100:
                report_data["details"].append({
                    "issue_id": parsed.issue_id,
                    "is_sufficient": is_suff,
                    "metrics": metrics
                })

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

    def _count_lines_in_repo_state(self, repo_state: Optional[Dict[str, Any]], extracted_files: List[str]) -> int:
        """
        Calculate total lines in the relevant file history based on repo_state.
        This implementation assumes repo_state contains a 'files' dict mapping
        file paths to their content strings.
        """
        if not repo_state or "files" not in repo_state:
            return 0
        
        files_dict = repo_state["files"]
        total_lines = 0
        
        for file_path in extracted_files:
            if file_path in files_dict:
                content = files_dict[file_path]
                if isinstance(content, str):
                    total_lines += content.count('\n') + (1 if content and not content.endswith('\n') else 0)
                elif isinstance(content, list):
                    total_lines += len(content)
        
        return total_lines

    def filter_high_complexity(self, min_lines: int = 500) -> Iterator[Dict[str, Any]]:
        """
        Filter instances where relevant file history > min_lines.
        Iterates through the streaming dataset, calculates line counts,
        and yields only those exceeding the threshold.
        """
        self.logger.info(f"Starting filter for instances with > {min_lines} lines of relevant file history.")
        count_passed = 0
        count_total = 0

        for record in self.load_streaming():
            count_total += 1
            parsed = self.parse_issue(record)
            lines = self._count_lines_in_repo_state(record.get("repo_state"), parsed.extracted_files)
            
            if lines > min_lines:
                count_passed += 1
                yield record
            
            if count_total % 100 == 0:
                self.logger.info(f"Processed {count_total} records, {count_passed} passed filter.")

        self.logger.info(f"Filter complete. Total: {count_total}, Passed: {count_passed}")

    def write_filtered_dataset(self, output_path: str, min_lines: int = 500) -> str:
        """
        Filter the dataset, write to a versioned Parquet file, and record the checksum.
        Returns the checksum string.
        """
        import tempfile
        from pathlib import Path

        data_dir = Path(get_data_dir())
        output_dir = data_dir / "intermediate"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Use the provided output_path or construct a default versioned path
        if not output_path:
            output_path = str(output_dir / "filtered_swe_bench_v1.parquet")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Filtering dataset and writing to {output_path}...")
        
        # Collect filtered records into a list (or batch write if memory is a concern)
        # For this implementation, we collect to list assuming the filtered set fits in memory.
        # If the dataset is too large, we would stream to parquet directly.
        filtered_records = []
        for record in self.filter_high_complexity(min_lines):
            filtered_records.append(record)

        if not filtered_records:
            raise RuntimeError(f"No instances passed the filter (>{min_lines} lines). Check data source.")

        # Write to Parquet
        table = pq.Table.from_pylist(filtered_records)
        pq.write_table(table, output_path)
        
        self.logger.info(f"Wrote {len(filtered_records)} records to {output_path}")

        # Calculate checksum
        checksum = self._calculate_file_checksum(output_path)
        
        # Record checksum in state
        state_dir = Path("state")
        state_dir.mkdir(parents=True, exist_ok=True)
        checksum_file = state_dir / "filtered_dataset_checksums.json"
        
        checksum_data = {}
        if checksum_file.exists():
            with open(checksum_file, "r") as f:
                checksum_data = json.load(f)
        
        checksum_data["filtered_swe_bench_v1.parquet"] = {
            "path": str(output_path),
            "checksum": checksum,
            "record_count": len(filtered_records),
            "min_lines_threshold": min_lines
        }
        
        with open(checksum_file, "w") as f:
            json.dump(checksum_data, f, indent=2)
        
        self.logger.info(f"Checksum recorded in {checksum_file}")
        return checksum

    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

def main():
    loader = ClawSweBenchLoader()
    output_path = "projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/data/intermediate/filtered_swe_bench_v1.parquet"
    print(f"Filtering dataset and writing to {output_path}...")
    checksum = loader.write_filtered_dataset(output_path, min_lines=500)
    print(f"Done. Checksum: {checksum}")

if __name__ == "__main__":
    main()
