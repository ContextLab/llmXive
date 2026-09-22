from typing import List, Dict, Any, Set

def is_valid_category(category: Any, valid_categories: Set[str]) -> bool:
    """
    Check if a category string is in the set of valid categories.
    
    Args:
        category: The category string from the record.
        valid_categories: Set of allowed category names.
        
    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(category, str):
        return False
    return category.strip() in valid_categories

def filter_by_categories(records: List[Dict[str, Any]], valid_categories: Set[str]) -> List[Dict[str, Any]]:
    """
    Filter a list of records based on their category field.
    
    Args:
        records: List of task records.
        valid_categories: Set of allowed category names.
        
    Returns:
        List of records where category is in valid_categories.
    """
    return [r for r in records if is_valid_category(r.get("category"), valid_categories)]
