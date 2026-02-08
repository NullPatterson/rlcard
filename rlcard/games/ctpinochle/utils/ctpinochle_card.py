'''
    File name: bridge/utils/ctpinochle_card.py 
    Author: William Hale 
    Date created: 11/25/2021 
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
    
    def __init__(self, suit:str, rank:str):
        super().__init__(suit=suit, rank=rank)
        suit_index = CTPinochleCard.suits.index(self.suit)
        rank_index = CTPinochleCard.ranks.index(self.rank)
        self.card_id = 12 * suit_index + rank_index
        # FLAG not sure if this is needed for scoring or not but for now 
        # a way to show if the card is worth a point or not
        self.card_vale = 1 if suit_index > 2 else 0

    def __str__(self):
        return f'{self.rank}{self.suit}'
    
    def __repr__(self):
        return f'{self.rank}{self.suit}'


# Preps the deck in order with the duplicates conescutively
# 9C, 9C, 10C 10C..., KS, KS, AS, AS
_deck = [CTPinochleCard(suit=suit, rank=rank) for suit in CTPinochleCard.suits for rank in CTPinochleCard.ranks for _ in range(2)]


##values = [0, 1] # Flag IDK best way to show counters or not so setting this for now
