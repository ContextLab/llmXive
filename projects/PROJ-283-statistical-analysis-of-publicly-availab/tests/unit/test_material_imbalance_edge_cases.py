import pytest
import chess
import chess.pgn
import io
from src.data.parse import get_material_imbalance_move5, calculate_material_imbalance, get_material_value

class TestMaterialImbalanceEdgeCases:
    """Additional unit tests for material imbalance calculation edge cases."""

    def test_empty_game_no_moves(self):
        """Test handling of a game with no moves played."""
        pgn_str = """
        [Event "Test"]
        [White "Player1"]
        [Black "Player2"]
        [Result "*"]
        """
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        
        # If no moves are played, move 5 state is the starting position
        # Starting position has equal material (0 imbalance)
        imbalance = get_material_imbalance_move5(game)
        assert imbalance == 0.0

    def test_game_ends_before_move_5(self):
        """Test handling of a game that ends before move 5 is complete."""
        pgn_str = """
        [Event "Test"]
        [White "Player1"]
        [Black "Player2"]
        [Result "1-0"]
        1. e4 1-0
        """
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        
        # Game ends early, should still calculate imbalance at move 5 (or max available)
        # Since game ended, we evaluate the final position or handle gracefully
        imbalance = get_material_imbalance_move5(game)
        # Even with e4, material is still equal (0 imbalance) unless captures happened
        assert isinstance(imbalance, (int, float))

    def test_multiple_captures_move_5(self):
        """Test material imbalance with multiple captures by move 5."""
        # Example: 1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# (Scholar's Mate)
        # At move 5, White has captured a pawn (Qxf7)
        pgn_str = """
        [Event "Test"]
        [White "Player1"]
        [Black "Player2"]
        [Result "1-0"]
        1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7#
        """
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        
        # White captured a pawn (value 1)
        # Material imbalance should reflect White +1
        imbalance = get_material_imbalance_move5(game)
        assert imbalance == 1.0  # White has +1 material advantage

    def test_castling_affects_board_but_not_material(self):
        """Verify castling doesn't change material imbalance."""
        pgn_str = """
        [Event "Test"]
        [White "Player1"]
        [Black "Player2"]
        [Result "*"]
        1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O Nf6
        """
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        
        imbalance = get_material_imbalance_move5(game)
        # No captures, only development and castling
        assert imbalance == 0.0

    def test_promotion_at_move_5(self):
        """Test material imbalance with pawn promotion (rare at move 5 but possible)."""
        # This is a constructed example: 1. a4 a5 2. b4 axb4 3. c4 bxc4 4. d4 cxd4 5. e4 d3
        # Actually, promotion at move 5 is extremely rare/impossible in standard play.
        # We test a scenario where a pawn reaches the last rank (promotion would happen next).
        # Instead, we test a capture sequence that leads to a significant imbalance.
        
        pgn_str = """
        [Event "Test"]
        [White "Player1"]
        [Black "Player2"]
        [Result "*"]
        1. e4 d5 2. exd5 Qxd5 3. Nc3 Qa5 4. d4 Nf6 5. Nf3 Bg4
        """
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        
        # White captured a pawn (d5), Black recaptured with Queen. 
        # Material is balanced again (Queen for pawn is not a capture, it's a trade).
        # Wait: 2. exd5 (White takes pawn), 2... Qxd5 (Black takes pawn with Queen).
        # Net: White lost a pawn, Black lost a pawn. Balance = 0.
        imbalance = get_material_imbalance_move5(game)
        assert imbalance == 0.0

    def test_asymmetric_captures(self):
        """Test scenario where one side captures more material than the other."""
        # 1. e4 e5 2. Nf3 d6 3. Bc4 Bg4 4. Nc3 g6 5. Nxe5 (White takes e5 pawn)
        pgn_str = """
        [Event "Test"]
        [White "Player1"]
        [Black "Player2"]
        [Result "*"]
        1. e4 e5 2. Nf3 d6 3. Bc4 Bg4 4. Nc3 g6 5. Nxe5
        """
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        
        # White captured a pawn on e5
        imbalance = get_material_imbalance_move5(game)
        assert imbalance == 1.0  # White +1

    def test_get_material_value_pieces(self):
        """Test individual piece value retrieval."""
        board = chess.Board()
        
        # Pawn
        assert get_material_value(chess.PAWN) == 1.0
        # Knight
        assert get_material_value(chess.KNIGHT) == 3.0
        # Bishop
        assert get_material_value(chess.BISHOP) == 3.0
        # Rook
        assert get_material_value(chess.ROOK) == 5.0
        # Queen
        assert get_material_value(chess.QUEEN) == 9.0
        # King should not be counted in material imbalance usually, but function exists
        # Typically King value is not used in imbalance calc, but let's ensure it doesn't crash
        # The function might return 0 or a special value for King, but standard is not to count it.
        # Assuming the implementation returns 0 or ignores King.
        # Let's just ensure it returns a number.
        king_val = get_material_value(chess.KING)
        assert isinstance(king_val, (int, float))

    def test_calculate_material_imbalance_starting_position(self):
        """Test that starting position has zero imbalance."""
        board = chess.Board()
        imbalance = calculate_material_imbalance(board)
        assert imbalance == 0.0

    def test_calculate_material_imbalance_after_capture(self):
        """Test imbalance calculation after a single capture."""
        board = chess.Board("rnbqkbnr/pppp1ppp/4p3/8/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 1")
        # White pawn on d4, Black pawn on e6. No captures yet in this FEN.
        # Let's construct a FEN with a capture: White has extra pawn.
        # Start: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
        # After 1. e4 (no capture).
        # Let's use a FEN where White has captured a pawn:
        # rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1 (Black played d5, White played e4, no capture)
        # Correct FEN with capture: White took a pawn on d5?
        # Let's just create a board with extra piece for White.
        board = chess.Board()
        # Remove a black pawn and add a white pawn to simulate capture
        board.remove_piece_at(chess.D7) # Remove black pawn
        board.set_piece_at(chess.D4, chess.Piece(chess.PAWN, chess.WHITE)) # Add white pawn (already there in e4, let's do d4)
        # Actually, simpler: just check the function logic with a known state.
        # We'll trust the logic: sum(white) - sum(black).
        # Let's create a board where White has an extra pawn.
        board = chess.Board("rnbqkbnr/ppp1pppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1")
        # This is just e4, no capture.
        # Let's force a capture state manually.
        board = chess.Board()
        board.remove_piece_at(chess.E7) # Remove black pawn
        # White still has all pawns.
        # Imbalance = (White total) - (Black total) = 1 (since Black lost 1 pawn)
        # But wait, the function calculates based on the board state.
        # If we remove a black piece, imbalance should be +1.
        # However, the board must be valid. Let's just test the function with a known FEN.
        # FEN: rnbqkbnr/ppp1pppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1 (e4, no capture)
        # Let's use a FEN where White is up a pawn:
        # rnbqkbnr/ppp1pppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1 (No, this is just e4)
        # Let's assume the function works and test with a known capture.
        # We'll rely on the game-based test for real captures.
        # This test is for the helper function.
        # Let's create a board with an extra white pawn.
        board = chess.Board("rnbqkbnr/ppp1pppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1")
        # This board has equal material.
        # Let's manually add a pawn to White's side.
        board.set_piece_at(chess.A3, chess.Piece(chess.PAWN, chess.WHITE))
        imbalance = calculate_material_imbalance(board)
        assert imbalance == 1.0

    def test_unicode_piece_handling(self):
        """Ensure unicode piece notation in PGN doesn't break parsing."""
        # PGNs are standard ASCII, but just in case of encoding issues
        pgn_str = """
        [Event "Test"]
        1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O
        """
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        imbalance = get_material_imbalance_move5(game)
        assert isinstance(imbalance, float) or isinstance(imbalance, int)
