'''
    File Name: ctpinochle/utils/move.py
    Author: Nol Patterson
    Date Created 2/8/2026
'''
from .action_event import ActionEvent, BidAction, PassBid, PlayCardAction
from .ctpinochle_card import CTPinochleCard
from ..player import CTPinochlePlayer

# Used to keep a move_sheet history of the moves in a round 

class CTPinochleMove(object):
    pass 

class PlayerMove(CTPinochleMove):
    def __init__(self, player: CTPinochlePlayer, action: ActionEvent):
        super().__init__()
        self.player = player 
        self.action = action 

class CallMove(PlayerMove):
    def __init__(self, player: CTPinochlePlayer, action: ActionEvent):
        super().__init__(player=player, action=action)

class DealHandMove(CTPinochleMove):
    def __init__(self, dealer: CTPinochlePlayer, shuffled_deck: [CTPinochleCard]):
        super().__init__()
        self.dealer = dealer
        self.shuffled_deck = shuffled_deck
    
    def __str__(self):
        shuffled_deck_text = " ".join([str(card) for card in self.shuffled_deck])
        return f'{self.dealer} deal shuffled_deck=[{shuffled_deck_text}]'

class MakePassBidMove(CallMove):
    def __init__(self, player: CTPinochlePlayer):
        super().__init__(player=player, action=PassBid())

    def __str__(self):
        return f'{self.player} {self.action}'
    
class MakeBidMove(CallMove):
    def __init__(self, player: CTPinochlePlayer, bid_action: BidAction):
        super().__init__(player=player, action=bid_action)
        self.action = bid_action # Note from bridge/util/move.py keep type as bid action rather than ActionEvent
    
    def __str__(self):
        return f'{self.player} bids {self.action}'
    
class PlayCardMove(PlayerMove):
    def __init__(self, player: CTPinochlePlayer, action: PlayCardAction):
        super().__init__(player=player, action=action)
        self.action = action 
    
    @property
    def card(self):
        return self.action.card 
    
    def __str__(self):
        return f'{self.player} plays {self.action}'


