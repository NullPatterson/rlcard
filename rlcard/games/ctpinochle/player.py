'''
    File name: ctpinochle/player.py 
    Author: Nol Patterson 
    Date Created: 2/8/2026
'''

from typing import List
from .utils.ctpinochle_card import CTPinochleCard

class CTPinochlePlayer:
    # FLAG idk what np_random is
    def __init__(self, player_id: int, np_random):
        if player_id < 0 or player_id > 2:
            raise Exception(f'CTPinochlePLayer has invalid player_id: {player_id}')
        self.np_ranodm = np_random 
        self.player_id: int = player_id 
        self.hand: List[CTPinochleCard] = []

    def remove_card_from_hand(self, card: CTPinochleCard):
        self.hand.remove(card)
    
    def get_player_id(self):
        return self.player_id

        