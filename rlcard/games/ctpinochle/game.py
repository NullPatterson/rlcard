'''
    File Name: ctpinochle/game.py
    Author: Nol Patterson
    Date Created: 2/8/2026
'''
from typing import List 
import numpy as np 

from .judger import CTPinochleJudger
from .round import CTPinochleRound
from .utils.action_event import ActionEvent, CallActionEvent, PlayCardAction

class CTPinochleGame:
    # The class to interact with outer environment
    def __init__(self, allow_step_back = False)
        self.allow_step_back: bool = allow_step_back
        self.np_random = np.random.RandomState()
        self.judger: CTPinochleJudger = CTPinochleJudger(game=self)
        self.actions: [ActionEvent] = []
        self.round: CTPinochleRound or None = None
        self.num_players: int = 3 # Only 3 is currently supported

    def init_game(self):
        dealer_id = self.np_random.choice([0, 1, 2]) # FLAG IDK what this is doin
        self.actions: List[ActionEvent] = []
        self.round = CTPinochleRound(num_players=self.num_players, dealer_id=dealer_id, np_random=self.np_random)
        
        # FLAG I thought round will deal cards bridge has it in both i think tho
        # come back if issues
        # Deal out cards in sets of 4
        dealt_cards = 0
        while dealt_cards < 48:
            for player_id in range(self.num_players):
                player = self.round.players[player_id]
                self.round.dealer.deal_cards(player=player)
                dealt_cards += 4
        current_player_id = self.round.current_player_id
        state = self.get_state(player_id=current_player_id)
        return state, current_player_id
    
    def step(self, action: ActionEvent):
        # Perform game action and return next player number and the state for next palyer
        if isinstance(action, CallActionEvent):
            self.round.make_call(action=action)
        elif isinstance(action, PlayCardAction):
            self.round.play_card(action=action)
        # FLAG Bidding event?
        else:
            raise Exception(f'Unknown step action={action}')
        self.actions.append(action)
        next_player_id = self.round.current_player_id
        next_state = self.get_state(player_id=next_player_id)
        return next_state, next_player_id
    
    def get_num_players(self) -> int:
        return self.num_players

    # Return number of possible actions in the game
    @staticmethod
    def get_num_actions() -> int:
        return ActionEvent.get_num_actions()
    
    # Return current player that wiill take actions soon
    def get_player_id(self):
        return self.round.current_player_id

    # Determine wheter roundis over
    def is_over(self) -> bool:
        return self.round.is_over()
    
    def get_state(self, player_id: int):
        state = {}
        if not self.is_over():
            state['player_id'] = player_id
            state['current_player_id'] = self.round.current_player_id
            state['hand'] = self.round.players[player_id].hand
        else:
            state['player_id'] = player_id
            state['current_player_id'] = self.round.current_player_id
            state['hand'] = self.round.players[player_id].hand
        return state
    