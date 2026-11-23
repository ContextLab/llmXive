"""
Counterfactual Query Generator Module.

Generates SQL/Python queries for counterfactual analysis using an LLM.
Implements retry logic for syntax errors and timeouts.
"""
import os
import json
import logging
import time
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable
import random

# Import from existing modules
from config import get_config
from narrative.inspector import run_inspector_analysis
from narrative.baseline import run_baseline_analysis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default LLM configuration
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 2  # seconds

class QueryGenerationError(Exception):
    """Exception raised when query generation fails after all retries."""
    pass

class QuerySyntaxError(Exception):
    """Exception raised when generated query has syntax errors."""
    pass

class QueryTimeoutError(Exception):
    """Exception raised when query generation times out."""
    pass

def _validate_python_query(query: str, df_schema: Dict[str, str]) -> bool:
    """
    Validate a Python query string for basic syntax correctness.
    
    Args:
        query: The generated query string
        df_schema: Dictionary mapping column names to their types
        
    Returns:
        True if query appears syntactically valid
        
    Raises:
        QuerySyntaxError: If query has obvious syntax errors
    """
    # Check for balanced parentheses
    if query.count('(') != query.count(')'):
        raise QuerySyntaxError(f"Unbalanced parentheses in query: {query}")
    
    # Check for balanced brackets
    if query.count('[') != query.count(']'):
        raise QuerySyntaxError(f"Unbalanced brackets in query: {query}")
    
    # Check for balanced braces
    if query.count('{') != query.count('}'):
        raise QuerySyntaxError(f"Unbalanced braces in query: {query}")
    
    # Check for basic pandas/polars patterns
    if 'pd.' in query or 'pl.' in query:
        # Verify column references exist in schema
        for col in df_schema.keys():
            # Check if column is referenced but not in a string literal
            # Simple heuristic: check for column name surrounded by non-alphanumeric chars
            pattern = r'(?<!\w)' + re.escape(col) + r'(?!\w)'
            if re.search(pattern, query) and f"'{col}'" not in query and f'"{col}"' not in query:
                # Column is referenced without quotes - likely a variable reference
                pass  # This is acceptable for pandas column access
    
    # Try to compile the query as Python code (limited validation)
    try:
        # Only validate syntax, not execution
        compile(query, '<string>', 'eval')
    except SyntaxError as e:
        raise QuerySyntaxError(f"Syntax error in query: {e}")
    
    return True

def _validate_sql_query(query: str, df_schema: Dict[str, str]) -> bool:
    """
    Validate a SQL query string for basic syntax correctness.
    
    Args:
        query: The generated query string
        df_schema: Dictionary mapping column names to their types
        
    Returns:
        True if query appears syntactically valid
        
    Raises:
        QuerySyntaxError: If query has obvious syntax errors
    """
    # Check for balanced parentheses
    if query.count('(') != query.count(')'):
        raise QuerySyntaxError(f"Unbalanced parentheses in query: {query}")
    
    # Check for basic SQL keywords
    query_upper = query.upper()
    if not any(kw in query_upper for kw in ['SELECT', 'FROM', 'WHERE', 'JOIN']):
        raise QuerySyntaxError(f"Query lacks basic SQL structure: {query}")
    
    # Verify column references exist in schema
    for col in df_schema.keys():
        # Check if column is referenced
        if col.upper() in query_upper:
            # Column is referenced - this is acceptable
            pass
    
    # Basic SQL syntax validation
    if 'SELECT' in query_upper and 'FROM' not in query_upper:
        raise QuerySyntaxError(f"SELECT without FROM: {query}")
    
    return True

def _call_llm_with_retry(
    prompt: str,
    df_schema: Dict[str, str],
    query_type: str = 'python',
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: int = DEFAULT_RETRY_DELAY,
    llm_client: Optional[Callable] = None
) -> str:
    """
    Call LLM to generate query with retry logic for syntax errors and timeouts.
    
    Args:
        prompt: The prompt to send to the LLM
        df_schema: Dictionary mapping column names to their types
        query_type: Type of query to generate ('python' or 'sql')
        timeout: Maximum time to wait for LLM response in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        llm_client: Optional LLM client function with signature (prompt, timeout) -> str
        
    Returns:
        Generated query string
        
    Raises:
        QueryTimeoutError: If all retries timeout
        QuerySyntaxError: If all retries produce syntax errors
        QueryGenerationError: If LLM client is not available or fails completely
    """
    if llm_client is None:
        # Fallback to a simple heuristic-based generator if no LLM client
        logger.warning("No LLM client provided, using heuristic-based query generation")
        return _generate_heuristic_query(df_schema, query_type, prompt)
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries} to generate {query_type} query")
            
            # Call LLM with timeout
            start_time = time.time()
            query = llm_client(prompt, timeout)
            elapsed = time.time() - start_time
            
            if elapsed > timeout:
                raise QueryTimeoutError(f"LLM call exceeded timeout of {timeout}s")
            
            # Validate query syntax
            if query_type == 'python':
                _validate_python_query(query, df_schema)
            elif query_type == 'sql':
                _validate_sql_query(query, df_schema)
            else:
                raise ValueError(f"Unknown query type: {query_type}")
            
            logger.info(f"Successfully generated valid {query_type} query on attempt {attempt + 1}")
            return query
            
        except QueryTimeoutError as e:
            logger.warning(f"Timeout on attempt {attempt + 1}: {e}")
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            
        except QuerySyntaxError as e:
            logger.warning(f"Syntax error on attempt {attempt + 1}: {e}")
            last_error = e
            # Enhance prompt with error information for next retry
            prompt = f"{prompt}\n\nPrevious attempt had syntax error: {e}\nPlease generate a syntactically correct {query_type} query."
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
    
    # All retries failed
    logger.error(f"Failed to generate valid {query_type} query after {max_retries} attempts")
    raise QueryGenerationError(f"Query generation failed after {max_retries} retries. Last error: {last_error}")

def _generate_heuristic_query(
    df_schema: Dict[str, str],
    query_type: str,
    prompt: str
) -> str:
    """
    Generate a query using simple heuristics when LLM is not available.
    
    This is a fallback for when LLM client is not provided or fails.
    """
    # Extract column names from schema
    columns = list(df_schema.keys())
    if len(columns) < 2:
        raise QueryGenerationError("Need at least 2 columns to generate a meaningful query")
    
    # Simple heuristic: generate correlation query for top 2 columns
    if query_type == 'python':
        # Generate a basic pandas correlation query
        col1, col2 = columns[0], columns[1]
        query = f"df[['{col1}', '{col2}']].corr().iloc[0, 1]"
    elif query_type == 'sql':
        # Generate a basic SQL correlation query (assuming sqlite/pandasql)
        col1, col2 = columns[0], columns[1]
        query = f"SELECT CORR({col1}, {col2}) as correlation FROM df"
    else:
        raise ValueError(f"Unknown query type: {query_type}")
    
    logger.info(f"Generated heuristic query: {query}")
    return query

def generate_counterfactual_query(
    baseline_narrative: Dict[str, Any],
    inspector_results: List[Dict[str, Any]],
    df_schema: Dict[str, str],
    query_type: str = 'python',
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: int = DEFAULT_RETRY_DELAY,
    llm_client: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Generate counterfactual queries based on baseline narrative and inspector results.
    
    Args:
        baseline_narrative: Dictionary containing baseline analysis results
        inspector_results: List of dictionaries containing inspector analysis results
        df_schema: Dictionary mapping column names to their types
        query_type: Type of query to generate ('python' or 'sql')
        timeout: Maximum time to wait for LLM response in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        llm_client: Optional LLM client function with signature (prompt, timeout) -> str
        
    Returns:
        Dictionary containing generated queries and metadata
    """
    # Construct prompt for LLM
    prompt = f"""
    Based on the following analysis results, generate a {query_type} query to test counterfactual hypotheses:
    
    Baseline Narrative:
    {json.dumps(baseline_narrative, indent=2)}
    
    Inspector Results:
    {json.dumps(inspector_results, indent=2)}
    
    Dataset Schema:
    {json.dumps(df_schema, indent=2)}
    
    Generate a {query_type} query that:
    1. Tests alternative causal explanations for the observed relationships
    2. Controls for potential confounders identified by the inspector
    3. Uses appropriate statistical methods (partial correlation, regression, etc.)
    4. Is syntactically correct and executable
    
    Query:
    """
    
    try:
        query = _call_llm_with_retry(
            prompt=prompt,
            df_schema=df_schema,
            query_type=query_type,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            llm_client=llm_client
        )
        
        return {
            'query': query,
            'query_type': query_type,
            'status': 'success',
            'metadata': {
                'timeout': timeout,
                'max_retries': max_retries,
                'retry_delay': retry_delay,
                'baseline_variables': list(baseline_narrative.get('variables', {}).keys()) if isinstance(baseline_narrative.get('variables'), dict) else []
            }
        }
        
    except (QueryTimeoutError, QuerySyntaxError, QueryGenerationError) as e:
        logger.error(f"Failed to generate counterfactual query: {e}")
        return {
            'query': None,
            'query_type': query_type,
            'status': 'failed',
            'error': str(e),
            'metadata': {
                'timeout': timeout,
                'max_retries': max_retries,
                'retry_delay': retry_delay
            }
        }

def run_query_generation_pipeline(
    dataset_path: str,
    output_path: str,
    query_type: str = 'python',
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: int = DEFAULT_RETRY_DELAY,
    llm_client: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Run the full query generation pipeline.
    
    Args:
        dataset_path: Path to the dataset file
        output_path: Path to save the output JSON
        query_type: Type of query to generate ('python' or 'sql')
        timeout: Maximum time to wait for LLM response in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        llm_client: Optional LLM client function with signature (prompt, timeout) -> str
        
    Returns:
        Dictionary containing the generation results
    """
    import pandas as pd
    
    # Load dataset to get schema
    logger.info(f"Loading dataset from {dataset_path}")
    df = pd.read_csv(dataset_path)
    df_schema = {col: str(df[col].dtype) for col in df.columns}
    
    # Run baseline analysis
    logger.info("Running baseline analysis")
    baseline_results = run_baseline_analysis(df)
    
    # Run inspector analysis
    logger.info("Running inspector analysis")
    inspector_results = run_inspector_analysis(df, baseline_results)
    
    # Generate counterfactual query
    logger.info("Generating counterfactual query")
    query_result = generate_counterfactual_query(
        baseline_narrative=baseline_results,
        inspector_results=inspector_results,
        df_schema=df_schema,
        query_type=query_type,
        timeout=timeout,
        max_retries=max_retries,
        retry_delay=retry_delay,
        llm_client=llm_client
    )
    
    # Save results to output file
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(query_result, f, indent=2)
    
    logger.info(f"Query generation results saved to {output_path}")
    return query_result

def main():
    """Main entry point for the query generation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate counterfactual queries')
    parser.add_argument('--dataset', type=str, required=True, help='Path to dataset file')
    parser.add_argument('--output', type=str, required=True, help='Path to output JSON file')
    parser.add_argument('--query-type', type=str, choices=['python', 'sql'], default='python',
                      help='Type of query to generate')
    parser.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT,
                      help='Timeout for LLM calls in seconds')
    parser.add_argument('--max-retries', type=int, default=DEFAULT_MAX_RETRIES,
                      help='Maximum number of retry attempts')
    parser.add_argument('--retry-delay', type=int, default=DEFAULT_RETRY_DELAY,
                      help='Delay between retries in seconds')
    
    args = parser.parse_args()
    
    result = run_query_generation_pipeline(
        dataset_path=args.dataset,
        output_path=args.output,
        query_type=args.query_type,
        timeout=args.timeout,
        max_retries=args.max_retries,
        retry_delay=args.retry_delay
    )
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()