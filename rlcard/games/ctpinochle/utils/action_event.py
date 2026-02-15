'''
    File Name: ctpinochle/action_event.py
    Author: Nol Patterson
    Date Created: 2/8/2026
'''

from .ctpinochle_card import CTPinochleCard

# =========================================
# Action_ids:
#       0 -> pass_bid_action_id 
#       min_bid = 21 for normal meanas but if dealer gets stuck its 20
#       max_bid = 50 (should cover most games)
#       1-30 -> bid_action_id (bid amount of 21-50)
#       31-78 -> play_card_action_id
#       79 -> Select Club as Trump
#       80 -> Select Diamond as Trump
#       81 -> Select Heart as Trump
#       82 -> Select Spades as Trump
# =========================================

class ActionEvent(object): 
    min_bid = 21 # If the non dealing players pass the dealer is stuck with the bid at 20
    max_bid = 50
    pass_bid_action_id = 0
    first_bid_action_id = 1
    first_play_card_action_id = 31
    min_trump = 79
    max_trump = 82
    trump_suits = ['C', 'D', 'H', 'S']

    def __init__(self, action_id: int):
        self.action_id = action_id 
    
    # Can be used for checking valid action or if somehow two people took the same action (shouldn't be possible)
    def __eq__(self, other):
        result = False 
        if isinstance(other, ActionEvent):
            result = self.action_id == other.action_id 
        return result
    
    @staticmethod 
    def from_action_id(action_id: int):
        if action_id == ActionEvent.pass_bid_action_id:
            return PassBid()
        elif ActionEvent.first_bid_action_id <= action_id <= 30:
            bid_amount = ActionEvent.min_bid + (action_id - ActionEvent.first_bid_action_id)
            return BidAction(bid_amount)
        elif ActionEvent.first_play_card_action_id <= action_id < ActionEvent.first_play_card_action_id + 48:
            card_id = action_id - ActionEvent.first_play_card_action_id
            card = CTPinochleCard.card(card_id=card_id)
            return PlayCardAction(card=card)
        elif ActionEvent.min_trump <= action_id <= ActionEvent.max_trump:
            trump_suit = ActionEvent.trump_suits[action_id-79]
            
        else:
            raise Exception(f'ActionEvent form_action_id: invalid action_id={action_id}')

    @staticmethod 
    def get_num_actions():
        return 1 + 30 + 48 # Pass on bid, 30 bids, 48 cards

class CallActionEvent(ActionEvent):
    pass
        
class PassBid(CallActionEvent):
    def __init__(self):
        super().__init__(action_id=ActionEvent.pass_bid_action_id)
    
    def __str__(self):
        return "pass"
    
    def __repr__(self):
        return "pass"
    
class BidAction(CallActionEvent):
    def __init__(self, bid_amount: int):
        if bid_amount < ActionEvent.min_bid-1 or bid_amount > ActionEvent.max_bid:
            raise Exception(f'BidAction has invalid bid_amount: {bid_amount}')
        bid_action_id = bid_amount - ActionEvent.min_bid + ActionEvent.first_bid_action_id
        super().__init__(action_id=bid_action_id)
        self.bid_amount = bid_amount

    def __str__(self):
        return f'{self.bid_amount}'

    def __repr__(self):
        return self.__str__()
    
class PlayCardAction(ActionEvent):
    def __init__(self, card: CTPinochleCard):
        play_card_action_id = ActionEvent.first_play_card_action_id + card.card_id 
        super().__init__(action_id=play_card_action_id)
        self.card: CTPinochleCard = card 

    def __str__(self):
        return f"{self.card}"
    
    def __repr__(self):
        return f"{self.card}"
    
class SelectTrumpAction(ActionEvent):
    def __init__(self, trump_suit: str):
        if trump_suit not in ['C', 'H', 'D', 'S']:
            raise Exception(f'SelectTrumpAction has invalid trump suit: {trump_suit}')
        trump_suit_id = ActionEvent.trump_suits.index(trump_suit) + 79
        super().__init__(action_id=trump_suit_id)
        self.trump_suit = trump_suit
    
    def __str__(self):
        return f'{self.trump_suit}'
    
    def __repr__(self):
        return f'{self.trump_suit}'