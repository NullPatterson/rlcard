'''
    File Name: ctpinochle/game.py
    Author: Nol Patterson
    Date Created: 2/8/2026
'''
from typing import List, Optional
import numpy as np

from .judger import CTPinochleJudger
from .round import CTPinochleRound
from .utils.action_event import ActionEvent, CallActionEvent, PlayCardAction, SelectTrumpAction

WIN_SCORE = 100  # First player to reach this wins the game

class CTPinochleGame:
    '''
    Manages the full multi-round game. A game ends when at least one player
    reaches WIN_SCORE (100) at the end of a completed round AND that player
    is the highest scorer. The dealer rotates left each round.
    '''

    def __init__(self, allow_step_back: bool = False):
        self.allow_step_back: bool = allow_step_back
        self.np_random = np.random.RandomState()
        self.judger: CTPinochleJudger = CTPinochleJudger(game=self)
        self.num_players: int = 3  # Only 3 is currently supported

        # Per-game state (reset in init_game)
        self.actions: List[ActionEvent] = []
        self.round: Optional[CTPinochleRound] = None
        self.round_number: int = 0

        # Cumulative scores across all rounds — these persist until init_game is called
        self.total_scores: List[int] = [0, 0, 0]

        # The dealer_id for the *current* round. Rotates left each round.
        self._current_dealer_id: int = 0

        # Set once the game is over so callers can inspect who won
        self.winner_id: Optional[int] = None

    def init_game(self):
        # Start a new game
        self.actions = []
        self.round_number = 0
        self.total_scores = [0, 0, 0]
        self.winner_id = None

        # Pick a random starting dealer
        self._current_dealer_id = int(self.np_random.choice([0, 1, 2]))

        self._start_new_round()

        current_player_id = self.round.current_player_id
        state = self.get_state(player_id=current_player_id)
        return state, current_player_id

    def step(self, action: ActionEvent):
        '''
        Apply one action to the current round. If the round ends, scores are
        tallied and — unless someone has won the game — a new round begins
        automatically. Returns (next_state, next_player_id).
        '''
        if isinstance(action, CallActionEvent):
            self.round.make_call(action=action)
        elif isinstance(action, SelectTrumpAction):
            self.round.set_trump(action.trump_suit)
            self.round.show_meld()
        elif isinstance(action, PlayCardAction):
            self.round.play_card(action=action)
        else:
            raise Exception(f'CTPinochleGame.step: unknown action type={action}')

        self.actions.append(action)

        # If the round just finished, score it and potentially start a new one
        if self.round.is_over():
            self._tally_round_scores()

            if not self.is_over():
                # Rotate the dealer and begin next round
                self._current_dealer_id = (self._current_dealer_id + 1) % 3
                self._start_new_round()

        next_player_id = self.round.current_player_id
        next_state = self.get_state(player_id=next_player_id)
        return next_state, next_player_id

    def is_over(self) -> bool:
        '''
        The game is over when:
          1. The current round has finished, AND
          2. At least one player is at or above WIN_SCORE.

        We only check after a round completes so that every player has a fair
        chance to respond in the same round (standard pinochle convention).
        '''
        if self.round is None or not self.round.is_over():
            return False
        return any(score >= WIN_SCORE for score in self.total_scores)

    def get_payoffs(self) -> List[int]:
        '''Return cumulative scores as payoffs. Call after is_over() is True.'''
        return list(self.total_scores)

    # ------------------------------------------------------------------
    # Standard RLCard helpers
    # ------------------------------------------------------------------

    def get_num_players(self) -> int:
        return self.num_players

    @staticmethod
    def get_num_actions() -> int:
        return ActionEvent.get_num_actions()

    def get_player_id(self) -> int:
        return self.round.current_player_id

    def get_state(self, player_id: int) -> dict:
        state = {
            'player_id': player_id,
            'current_player_id': self.round.current_player_id,
            'hand': self.round.players[player_id].hand,
            'total_scores': list(self.total_scores),
            'round_number': self.round_number,
        }
        return state

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _start_new_round(self):
        '''Create and initialise a fresh Round. Cards are dealt inside Round.__init__.'''
        self.round_number += 1
        self.round = CTPinochleRound(
            num_players=self.num_players,
            dealer_id=self._current_dealer_id,
            np_random=self.np_random,
        )
        # Note: CTPinochleRound.__init__ already deals all 48 cards in batches of 4.
        # Do NOT deal again here — that was the source of the double-deal bug.

    def _tally_round_scores(self):
        '''Add this round's scores to the running totals and record the winner if done.'''
        round_scores = self.round.calculate_scores()
        for player_id in range(self.num_players):
            self.total_scores[player_id] += round_scores[player_id]

        # Determine winner if game is now over
        if any(score >= WIN_SCORE for score in self.total_scores):
            if self.total_scores[self.round.bid_winner_id] >= 100: 
                self.winner_id = self.round.bid_winner_id
            else: 
                self.winner_id = int(np.argmax(self.total_scores))