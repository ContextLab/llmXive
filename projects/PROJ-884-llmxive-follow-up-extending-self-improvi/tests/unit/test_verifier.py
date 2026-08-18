"""
Unit tests for the puzzle solution verifier.

Tests verification logic for Sudoku, pathfinding, and arithmetic puzzles.
"""
import pytest
import time
from code.dataset.verifier import verify_solution, ErrorCodes, SolutionResult


class TestSudokuVerification:
    """Tests for Sudoku puzzle verification."""
    
    def test_valid_sudoku_solution(self):
        """Test that a valid Sudoku solution is accepted."""
        puzzle = {
            "id": "test_sudoku_001",
            "type": "sudoku",
            "size": 9,
            "initial_state": [
                [5, 3, 0, 0, 7, 0, 0, 0, 0],
                [6, 0, 0, 1, 9, 5, 0, 0, 0],
                [0, 9, 8, 0, 0, 0, 0, 6, 0],
                [8, 0, 0, 0, 6, 0, 0, 0, 3],
                [4, 0, 0, 8, 0, 3, 0, 0, 1],
                [7, 0, 0, 0, 2, 0, 0, 0, 6],
                [0, 6, 0, 0, 0, 0, 2, 8, 0],
                [0, 0, 0, 4, 1, 9, 0, 0, 5],
                [0, 0, 0, 0, 8, 0, 0, 7, 9]
            ]
        }
        
        solution = {
            "id": "test_sol_001",
            "grid": [
                [5, 3, 4, 6, 7, 8, 9, 1, 2],
                [6, 7, 2, 1, 9, 5, 3, 4, 8],
                [1, 9, 8, 3, 4, 2, 5, 6, 7],
                [8, 5, 9, 7, 6, 1, 4, 2, 3],
                [4, 2, 6, 8, 5, 3, 7, 9, 1],
                [7, 1, 3, 9, 2, 4, 8, 5, 6],
                [9, 6, 1, 5, 3, 7, 2, 8, 4],
                [2, 8, 7, 4, 1, 9, 6, 3, 5],
                [3, 4, 5, 2, 8, 6, 1, 7, 9]
            ]
        }
        
        result = verify_solution(puzzle, solution)
        
        assert result.is_valid is True
        assert result.error_code == ErrorCodes.VALID
        assert result.execution_time_ms < 100.0
    
    def test_rejects_duplicate_row(self):
        """Test that a solution with duplicate row values is rejected."""
        puzzle = {
            "id": "test_sudoku_002",
            "type": "sudoku",
            "size": 9,
            "initial_state": [[0] * 9 for _ in range(9)]
        }
        
        solution = {
            "id": "test_sol_002",
            "grid": [
                [1, 1, 2, 3, 4, 5, 6, 7, 8],  # Duplicate 1
                [2, 3, 4, 5, 6, 7, 8, 9, 1],
                [3, 4, 5, 6, 7, 8, 9, 1, 2],
                [4, 5, 6, 7, 8, 9, 1, 2, 3],
                [5, 6, 7, 8, 9, 1, 2, 3, 4],
                [6, 7, 8, 9, 1, 2, 3, 4, 5],
                [7, 8, 9, 1, 2, 3, 4, 5, 6],
                [8, 9, 1, 2, 3, 4, 5, 6, 7],
                [9, 1, 2, 3, 4, 5, 6, 7, 8]
            ]
        }
        
        result = verify_solution(puzzle, solution)
        
        assert result.is_valid is False
        assert result.error_code == ErrorCodes.DUPLICATE_ROW
    
    def test_rejects_duplicate_column(self):
        """Test that a solution with duplicate column values is rejected."""
        puzzle = {
            "id": "test_sudoku_003",
            "type": "sudoku",
            "size": 9,
            "initial_state": [[0] * 9 for _ in range(9)]
        }
        
        solution = {
            "id": "test_sol_003",
            "grid": [
                [1, 2, 3, 4, 5, 6, 7, 8, 9],
                [1, 3, 4, 5, 6, 7, 8, 9, 1],  # Duplicate 1 in column 0
                [3, 4, 5, 6, 7, 8, 9, 1, 2],
                [4, 5, 6, 7, 8, 9, 1, 2, 3],
                [5, 6, 7, 8, 9, 1, 2, 3, 4],
                [6, 7, 8, 9, 1, 2, 3, 4, 5],
                [7, 8, 9, 1, 2, 3, 4, 5, 6],
                [8, 9, 1, 2, 3, 4, 5, 6, 7],
                [9, 1, 2, 3, 4, 5, 6, 7, 8]
            ]
        }
        
        result = verify_solution(puzzle, solution)
        
        assert result.is_valid is False
        assert result.error_code == ErrorCodes.DUPLICATE_COLUMN
    
    def test_rejects_initial_state_violation(self):
        """Test that a solution violating initial state is rejected."""
        puzzle = {
            "id": "test_sudoku_004",
            "type": "sudoku",
            "size": 9,
            "initial_state": [
                [5, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0]
            ]
        }
        
        solution = {
            "id": "test_sol_004",
            "grid": [
                [6, 3, 4, 6, 7, 8, 9, 1, 2],  # Changed 5 to 6
                [6, 7, 2, 1, 9, 5, 3, 4, 8],
                [1, 9, 8, 3, 4, 2, 5, 6, 7],
                [8, 5, 9, 7, 6, 1, 4, 2, 3],
                [4, 2, 6, 8, 5, 3, 7, 9, 1],
                [7, 1, 3, 9, 2, 4, 8, 5, 6],
                [9, 6, 1, 5, 3, 7, 2, 8, 4],
                [2, 8, 7, 4, 1, 9, 6, 3, 5],
                [3, 4, 5, 2, 8, 6, 1, 7, 9]
            ]
        }
        
        result = verify_solution(puzzle, solution)
        
        assert result.is_valid is False
        assert result.error_code == ErrorCodes.CONSTRAINT_VIOLATION


class TestPathfindingVerification:
    """Tests for pathfinding puzzle verification."""
    
    def test_valid_path(self):
        """Test that a valid path is accepted."""
        puzzle = {
            "id": "test_path_001",
            "type": "pathfinding",
            "grid": [
                [0, 0, 0, 0],
                [0, 1, 1, 0],
                [0, 0, 0, 0],
                [0, 1, 0, 0]
            ],
            "start": [0, 0],
            "target": [3, 3]
        }
        
        solution = {
            "id": "test_path_sol_001",
            "path": [[0, 0], [0, 1], [0, 2], [0, 3], [1, 3], [2, 3], [3, 3]]
        }
        
        result = verify_solution(puzzle, solution)
        
        assert result.is_valid is True
        assert result.error_code == ErrorCodes.VALID
    
    def test_rejects_path_not_starting_at_start(self):
        """Test that a path not starting at the start position is rejected."""
        puzzle = {
            "id": "test_path_002",
            "type": "pathfinding",
            "grid": [
                [0, 0, 0],
                [0, 0, 0],
                [0, 0, 0]
            ],
            "start": [0, 0],
            "target": [2, 2]
        }
        
        solution = {
            "id": "test_path_sol_002",
            "path": [[0, 1], [0, 2], [1, 2], [2, 2]]  # Starts at [0, 1]
        }
        
        result = verify_solution(puzzle, solution)
        
        assert result.is_valid is False
        assert result.error_code == ErrorCodes.INVALID_PATH
    
    def test_rejects_path_not_ending_at_target(self):
        """Test that a path not ending at the target is rejected."""
        puzzle = {
            "id": "test_path_003",
            "type": "pathfinding",
            "grid": [
                [0, 0, 0],
                [0, 0, 0],
                [0, 0, 0]
            ],
            "start": [0, 0],
            "target": [2, 2]
        }
        
        solution = {
            "id": "test_path_sol_003",
            "path": [[0, 0], [0, 1], [0, 2], [1, 2]]  # Ends at [1, 2]
        }
        
        result = verify_solution(puzzle, solution)
        
        assert result.is_valid is False
        assert result.error_code == ErrorCodes.INCORRECT_TARGET
    
    def test_rejects_path_crossing_obstacle(self):
        """Test that a path crossing an obstacle is rejected."""
        puzzle = {
            "id": "test_path_004",
            "type": "pathfinding",
            "grid": [
                [0, 1, 0],
                [0, 0, 0],
                [0, 0, 0]
            ],
            "start": [0, 0],
            "target": [2, 2]
        }
        
        solution = {
            "id": "test_path_sol_004",
            "path": [[0, 0], [0, 1], [0, 2], [1, 2], [2, 2]]  # Crosses obstacle at [0, 1]
        }
        
        result = verify_solution(puzzle, solution)
        
        assert result.is_valid is False
        assert result.error_code == ErrorCodes.INVALID_PATH
    
    def test_rejects_out_of_bounds(self):
        """Test that a path going out of bounds is rejected."""
        puzzle = {
            "id": "test_path_005",
            "type": "pathfinding",
            "grid": [
                [0, 0, 0],
                [0, 0, 0],
                [0, 0, 0]
            ],
            "start": [0, 0],
            "target": [2, 2]
        }
        
        solution = {
            "id": "test_path_sol_005",
            "path": [[0, 0], [0, 1], [0, 2], [-1, 2], [2, 2]]  # Out of bounds
        }
        
        result = verify_solution(puzzle, solution)
        
        assert result.is_valid is False
        assert result.error_code == ErrorCodes.OUT_OF_BOUNDS


class TestArithmeticVerification:
    """Tests for arithmetic puzzle verification."""
    
    def test_valid_expression(self):
        """Test that a valid arithmetic expression is accepted."""
        puzzle = {
            "id": "test_arith_001",
            "type": "arithmetic",
            "numbers": [1, 3, 4, 6],
            "target": 24
        }
        
        solution = {
            "id": "test_arith_sol_001",
            "expression": "6 / (1 - 3 / 4)"
        }
        
        result = verify_solution(puzzle, solution)
        
        assert result.is_valid is True
        assert result.error_code == ErrorCodes.VALID
    
    def test_rejects_wrong_result(self):
        """Test that an expression with wrong result is rejected."""
        puzzle = {
            "id": "test_arith_002",
            "type": "arithmetic",
            "numbers": [1, 2, 3, 4],
            "target": 10
        }
        
        solution = {
            "id": "test_arith_sol_002",
            "expression": "1 + 2 + 3 + 4"  # = 10, but let's make it wrong
        }
        
        # Actually, this is correct. Let's make it wrong.
        solution["expression"] = "1 + 2 + 3"  # = 6, not 10
        
        result = verify_solution(puzzle, solution)
        
        assert result.is_valid is False
        assert result.error_code == ErrorCodes.INCORRECT_TARGET
    
    def test_rejects_invalid_characters(self):
        """Test that an expression with invalid characters is rejected."""
        puzzle = {
            "id": "test_arith_003",
            "type": "arithmetic",
            "numbers": [1, 2, 3],
            "target": 6
        }
        
        solution = {
            "id": "test_arith_sol_003",
            "expression": "1 + 2 + 3 + __import__('os').system('ls')"
        }
        
        result = verify_solution(puzzle, solution)
        
        assert result.is_valid is False
        assert result.error_code == ErrorCodes.SYNTAX_ERROR
    
    def test_rejects_division_by_zero(self):
        """Test that division by zero is rejected."""
        puzzle = {
            "id": "test_arith_004",
            "type": "arithmetic",
            "numbers": [1, 2, 3],
            "target": 10
        }
        
        solution = {
            "id": "test_arith_sol_004",
            "expression": "1 / 0"
        }
        
        result = verify_solution(puzzle, solution)
        
        assert result.is_valid is False
        assert result.error_code == ErrorCodes.CONSTRAINT_VIOLATION


class TestVerifierPerformance:
    """Tests for verifier performance requirements."""
    
    def test_verifier_executes_within_time_limit(self):
        """Test that verification completes within 100ms."""
        puzzle = {
            "id": "perf_test_001",
            "type": "sudoku",
            "size": 9,
            "initial_state": [[0] * 9 for _ in range(9)]
        }
        
        solution = {
            "id": "perf_sol_001",
            "grid": [[i * 9 + j + 1 for j in range(9)] for i in range(9)]
        }
        
        start_time = time.time()
        result = verify_solution(puzzle, solution)
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert elapsed_ms < 100.0
        assert result.execution_time_ms < 100.0


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_missing_puzzle_type(self):
        """Test handling of missing puzzle type."""
        puzzle = {
            "id": "edge_001",
            "initial_state": []
        }
        
        solution = {"id": "edge_sol_001", "grid": []}
        
        result = verify_solution(puzzle, solution)
        
        assert result.is_valid is False
        assert result.error_code == ErrorCodes.SYNTAX_ERROR
    
    def test_missing_solution_data(self):
        """Test handling of missing solution data."""
        puzzle = {
            "id": "edge_002",
            "type": "sudoku",
            "size": 9,
            "initial_state": [[0] * 9 for _ in range(9)]
        }
        
        solution = {"id": "edge_sol_002"}  # Missing grid
        
        result = verify_solution(puzzle, solution)
        
        assert result.is_valid is False
        assert result.error_code == ErrorCodes.INVALID_PATH
    
    def test_unknown_puzzle_type(self):
        """Test handling of unknown puzzle type."""
        puzzle = {
            "id": "edge_003",
            "type": "unknown_type",
            "data": {}
        }
        
        solution = {"id": "edge_sol_003", "data": {}}
        
        result = verify_solution(puzzle, solution)
        
        assert result.is_valid is False
        assert result.error_code == ErrorCodes.SYNTAX_ERROR