from typing import TypedDict

class GameRecord(TypedDict):
    """
    TypedDict defining the schema for a single parsed chess game record.
    Matches the contract in specs/contracts/game_record.schema.yaml.
    
    All fields are non-nullable. 
    - game_id: Unique identifier for the game.
    - white_rating: ELO rating of the white player.
    - black_rating: ELO rating of the black player.
    - eco_code: Opening code (string), defaults to "Unknown" if missing.
    - avg_move_time_white: Average move time in seconds for white (float).
    - avg_move_time_black: Average move time in seconds for black (float).
    - material_imbalance_move10: Material difference at move 10 (float).
    - material_imbalance_move5: Material difference at move 5 (float).
    - outcome: Game result mapped to float (1.0=White win, 0.5=Draw, 0.0=Black win).
    - elo_expected_prob: Expected win probability for white based on ratings (float).
    - outcome_deviation: Actual outcome minus expected probability (float).
    """
    game_id: str
    white_rating: float
    black_rating: float
    eco_code: str
    avg_move_time_white: float
    avg_move_time_black: float
    material_imbalance_move10: float
    material_imbalance_move5: float
    outcome: float
    elo_expected_prob: float
    outcome_deviation: float