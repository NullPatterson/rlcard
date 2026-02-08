'''
    File Name: ctpinochle/round.py
    Author: Nol Patterson
    Date Created: 2/8/2026
'''
from typing import List 
from .dealer import CTPinochleDealer
from .player import CTPinochlePlayer

from .utils.action_event import CallActionEvent, PassBid, BidAction, PlayCardAction 
from .utils.move import CTPinochleMove, DealHandMove, PlayCardMove, MakeBidMove, MakePassBidMove, CallMove
from .utils.tray import Tray

class CTPinochleRound:
    @property
    def dealer_id(self) -> int:
        return self.tray.dealer_id
    
    @property
    def board_id(self) -> int:
        return self.tray.board_id
    
    @property
    def roundphase(self):
        if self.is_over():
            result = 'game over'
        elif self.is_bidding_over() and self.is_meld_over():
            result = 'play card'
        elif self.is_bidd_over():
            result = 'calculate meld'
        else:
            result = 'make bid'
        return result 

    def __init__(self, num_players: int, board_id: int, np_random):
        tray = Tray(board_id=board_id)
        dealer_id = tray.dealer_id
        self.tray = tray
        self.np_random = np_random
        self.dealer: CTPinochleDealer = CTPinochleDealer(self.np_random)
        self.players: List[CTPinochlePlayer] = []
        for player_id in range(num_players):
            self.players.append(CTPinochlePlayer(player_id=player_id, np_random=self.np_random))
        self.current_player_id: int = dealer_id
        self.play_card_count: int = 0
        