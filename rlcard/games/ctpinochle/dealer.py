'''
    File Name: ctpinohcle/dealer.py
    Author: Nol Patterson
    Date created: 2/8/2026
'''

from typing import List # FLAG Unsure if needed

from .player import CTPinochlePlayer
from .utils.ctpinochle_card import CTPinochleCard

class CTPinochleDealer:
    def __init__(self, np_random):
        self.np_random = np_random 
        self.shuffled_deck: List[CTPinochleCard] = CTPinochleCard.get_deck() 
        self.np_random.shuffle(self.shuffled_deck)
        # Stock pile is used for other games such as bridge but i don't think its the best term
        # As a stock pile normally represents the remaing cards that are drawn from during the cours of the game
        self.to_be_dealt: List[CTPinochleCard] = self.shuffled_deck.copy()
    
    '''
        Deal some cards from the remaining deck to one player
        
        player: The current CTPinochlePlayer object to recieve cards
        num: The number of cards to be dealt. 
            for cutthroat pinochle cards are normally dealt to players in sets of 4 accroding to wikipedia
    '''
    def deal_cards(self, player: CTPinochlePlayer, num: int = 4):
        for __ in range(num):
            player.hand.append(self.to_be_dealt.pop())

