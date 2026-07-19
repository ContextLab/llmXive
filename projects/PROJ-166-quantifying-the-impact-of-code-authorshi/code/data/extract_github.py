import os
import sys
import subprocess
import tempfile
import shutil
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from sibling modules as per API surface
from config import ensure_directories
from data.schemas import get_schema, validate_dataframe

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/extract_github.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
CLOC_TIMEOUT = 300  # 5 minutes per repo
MEMORY_WARNING_THRESHOLD = 6 * 1024 * 1024 * 1024  # 6 GB

def check_memory_usage() -> bool:
    """Check if current memory usage exceeds threshold. Returns True if safe to continue."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_usage = process.memory_info().rss
        if mem_usage > MEMORY_WARNING_THRESHOLD:
            logger.warning(f"Memory usage {mem_usage / 1e9:.2f}GB exceeds threshold. Aborting.")
            return False
        return True
    except ImportError:
        logger.warning("psutil not installed, skipping memory check.")
        return True
    except Exception as e:
        logger.error(f"Error checking memory: {e}")
        return True

def shallow_clone(repo_url: str, target_dir: Path) -> bool:
    """Perform a shallow clone of the repository since 2015-01-01."""
    try:
        # Ensure target_dir exists
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Run git clone with shallow-since
        cmd = [
            'git', 'clone', 
            '--depth', '1',
            '--shallow-since', '2015-01-01',
            repo_url,
            str(target_dir)
        ]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=300,
            env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'}
        )
        
        if result.returncode != 0:
            logger.warning(f"Shallow clone failed for {repo_url}: {result.stderr}")
            return False
        
        return True
    except subprocess.TimeoutExpired:
        logger.warning(f"Clone timeout for {repo_url}")
        return False
    except Exception as e:
        logger.warning(f"Clone error for {repo_url}: {e}")
        return False

def parse_git_log_and_count_authors(clone_path: Path) -> int:
    """Parse git log and count unique authors with at least 1 line of code."""
    try:
        # Get git log with author names
        cmd = ['git', '-C', str(clone_path), 'log', '--format=%aN', '--numstat']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            logger.warning(f"Git log failed for {clone_path}: {result.stderr}")
            return 0
        
        lines = result.stdout.split('\n')
        authors = set()
        current_author = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('Author:'):
                # Extract author name from "Author: Name"
                current_author = line.split(':', 1)[1].strip()
            elif line and not line.startswith('#') and '\t' in line:
                # This is a numstat line, indicating code changes
                # If we have a current author, they committed code
                if current_author:
                    authors.add(current_author)
                    current_author = None  # Reset to avoid double counting
        
        return len(authors)
    except Exception as e:
        logger.warning(f"Git log parse error for {clone_path}: {e}")
        return 0

def run_cloc_on_clone(clone_path: Path) -> Tuple[int, int]:
    """Run cloc --by-file and return (raw_line_count, kloc)."""
    try:
        # Run cloc --by-file
        cmd = ['cloc', '--by-file', '--quiet', '--exclude-dir=.git', str(clone_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=CLOC_TIMEOUT)
        
        if result.returncode != 0:
            logger.warning(f"cloc failed for {clone_path}: {result.stderr}")
            return 0, 0.0
        
        # Parse cloc output
        # Format: file|blank|comment|code
        lines = result.stdout.split('\n')
        total_code_lines = 0
        
        for line in lines:
            if '|' in line and not line.startswith('SUM'):
                parts = line.split('|')
                if len(parts) >= 4:
                    try:
                        code_lines = int(parts[3].strip())
                        total_code_lines += code_lines
                    except ValueError:
                        continue
        
        raw_line_count = total_code_lines
        kloc = total_code_lines / 1000.0
        
        return raw_line_count, kloc
    except subprocess.TimeoutExpired:
        logger.warning(f"cloc timeout for {clone_path}")
        return 0, 0.0
    except Exception as e:
        logger.warning(f"cloc error for {clone_path}: {e}")
        return 0, 0.0

def process_repo(repo_info: Dict[str, Any], clone_base: Path) -> Optional[Dict[str, Any]]:
    """Process a single repository: clone, parse authors, run cloc."""
    url = repo_info['url']
    repo_name = url.split('/')[-1].replace('.git', '')
    clone_path = clone_base / repo_name
    
    # Check memory before processing
    if not check_memory_usage():
        raise MemoryError("Memory threshold exceeded")
    
    # Step 1: Shallow clone
    logger.info(f"Cloning {url}")
    if not shallow_clone(url, clone_path):
        logger.warning(f"Skipping {url} due to clone failure")
        return None
    
    # Step 2: Parse git log for unique authors
    logger.info(f"Parsing authors for {url}")
    unique_authors = parse_git_log_and_count_authors(clone_path)
    if unique_authors == 0:
        logger.warning(f"No authors found for {url}")
        # Clean up and return None
        shutil.rmtree(clone_path, ignore_errors=True)
        return None
    
    # Step 3: Run cloc
    logger.info(f"Running cloc for {url}")
    raw_line_count, kloc = run_cloc_on_clone(clone_path)
    
    # Clean up clone directory
    shutil.rmtree(clone_path, ignore_errors=True)
    
    return {
        'url': url,
        'primary_language': repo_info.get('primary_language', 'Unknown'),
        'unique_authors': unique_authors,
        'raw_line_count': raw_line_count,
        'kloc': kloc
    }

def main():
    """Main entry point for Part 3: cloc & Merge."""
    ensure_directories()
    
    # Paths
    target_list_path = Path('data/raw/target_list.csv')
    authors_temp_path = Path('data/processed/authors_temp.csv')
    output_path = Path('data/processed/github_raw_metrics.csv')
    clone_base = Path('data/raw/clones')
    
    # Load target list
    logger.info(f"Loading target list from {target_list_path}")
    if not target_list_path.exists():
        raise FileNotFoundError(f"Target list not found: {target_list_path}")
    
    target_df = pd.read_csv(target_list_path)
    
    # Validate required columns
    required_cols = ['url', 'primary_language']
    missing_cols = [col for col in required_cols if col not in target_df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns in target list: {missing_cols}")
    
    # Load authors temp data (from T008b)
    if authors_temp_path.exists():
        authors_df = pd.read_csv(authors_temp_path)
        logger.info(f"Loaded {len(authors_df)} author counts from temp file")
    else:
        logger.warning(f"Authors temp file not found: {authors_temp_path}")
        logger.warning("Proceeding without author counts (will be filled with 0)")
        authors_df = pd.DataFrame(columns=['url', 'unique_authors'])
    
    # Ensure clone directory exists
    clone_base.mkdir(parents=True, exist_ok=True)
    
    # Process each repo
    results = []
    successful_clones = 0
    failed_clones = 0
    
    for idx, row in target_df.iterrows():
        try:
            repo_info = row.to_dict()
            result = process_repo(repo_info, clone_base)
            
            if result:
                results.append(result)
                successful_clones += 1
            else:
                failed_clones += 1
                
        except MemoryError as e:
            logger.critical(f"Memory error at {idx}/{len(target_df)}: {e}")
            break
        except Exception as e:
            logger.error(f"Error processing {row['url']}: {e}")
            failed_clones += 1
            continue
    
    logger.info(f"Processing complete: {successful_clones} successful, {failed_clones} failed")
    
    if not results:
        logger.warning("No successful results. Creating empty output file.")
        results_df = pd.DataFrame(columns=['url', 'primary_language', 'unique_authors', 'raw_line_count', 'kloc'])
    else:
        results_df = pd.DataFrame(results)
    
    # Merge with authors temp data if available
    if len(authors_df) > 0:
        # Merge on 'url'
        results_df = results_df.merge(authors_df, on='url', how='left')
        
        # Fill missing unique_authors with 0 (shouldn't happen if T008b ran correctly)
        results_df['unique_authors'] = results_df['unique_authors'].fillna(0).astype(int)
        
        # Drop duplicate columns if any
        results_df = results_df.drop_duplicates(subset=['url'])
    
    # Ensure all required columns exist
    output_schema = ['url', 'primary_language', 'unique_authors', 'raw_line_count', 'kloc']
    for col in output_schema:
        if col not in results_df.columns:
            if col == 'unique_authors':
                results_df[col] = 0
            else:
                results_df[col] = ''
    
    # Select and order columns
    results_df = results_df[output_schema]
    
    # Sort by URL
    results_df = results_df.sort_values('url').reset_index(drop=True)
    
    # Validate output schema
    schema = get_schema('github_raw_metrics')
    validate_dataframe(results_df, schema)
    
    # Write output
    logger.info(f"Writing output to {output_path}")
    results_df.to_csv(output_path, index=False)
    
    # Verification
    assert output_path.exists(), "Output file was not created"
    output_df = pd.read_csv(output_path)
    assert len(output_df) == len(results_df), "Output row count mismatch"
    assert list(output_df.columns) == output_schema, f"Column mismatch: {list(output_df.columns)} vs {output_schema}"
    
    logger.info(f"Successfully wrote {len(output_df)} rows to {output_path}")
    return output_path

if __name__ == '__main__':
    main()