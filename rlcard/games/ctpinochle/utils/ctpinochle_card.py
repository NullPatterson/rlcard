'''
    File name: ctpinochle/utils/ctpinochle_card.py 
    Author: Nol Patterson
    Date created: 2/8/2026
'''

from rlcard.games.base import Card 

class CTPinochleCard(Card):
    suits = ['C', 'D', 'H', 'S']
    ranks = ['9', 'J', 'Q', 'K', '10', 'A']
    
    @staticmethod
    def card(card_id: int):
        return _deck[card_id]
    
    @staticmethod 
    def get_deck() -> [Card]:
        return _deck.copy()
    
    def __init__(self, suit: str, rank: str):
        super().__init__(suit=suit, rank=rank)
        suit_index = CTPinochleCard.suits.index(self.suit)
        rank_index = CTPinochleCard.ranks.index(self.rank)
        
        # Each card appears twice in the deck
        # card_id ranges from 0-47 (48 total cards)
        # This will be set when building the deck
        self.card_id = None
        
        # Counter value: A, 10, K are worth 1 point in tricks
        # 9, J, Q are worth 0 points
        self.card_value = 1 if rank in ['A', '10', 'K'] else 0

    def __str__(self):
        return f'{self.rank}{self.suit}'
    
    def __repr__(self):
        return f'{self.rank}{self.suit}'


# Prepare the deck in order with duplicates consecutively
# 9C, 9C, JC, JC, ..., AS, AS (48 cards total)
_deck = []
card_id = 0
for suit in CTPinochleCard.suits:
    for rank in CTPinochleCard.ranks:
        for _ in range(2):  # Two of each card
            card = CTPinochleCard(suit=suit, rank=rank)
            card.card_id = card_id
            _deck.append(card)
            card_id += 1