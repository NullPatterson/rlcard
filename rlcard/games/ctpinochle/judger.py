''' 
    File Name: ctpinochle/judger.py
    Author: Nol Patterson
    Date created: 2/8/2026
'''

from typing import List 
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game import CTPinochleGame

from .utils.action_event import PlayCardAction
from .utils.action_event import ActionEvent, BidAction, PassBid
from .utils.move import MakeBidMove
from .utils.ctpinochle_card import CTPinochleCard

class CTPinochleJudger:
    '''
        Judger decides legal actions for current player
    '''
    def __init__(self, game: 'CTPinochleGame'):
        self.game: CTPinochleGame = game

    def get_legal_actions(self) -> List[ActionEvent]:
        legal_actions: List[ActionEvent] = []
        if not self.game.is_over():
            current_player = self.game.round.get_current_player()
            
            # During bidding phase
            if not self.game.round.is_bidding_over():
                # Player can only pass if they haven't already passed
                if not self.game.round.player_passed[current_player.player_id]:
                    legal_actions.append(PassBid())
                
                # Find the last bid to determine minimum next bid
                last_make_bid_move: MakeBidMove or None = None
                for move in reversed(self.game.round.move_sheet):
                    if isinstance(move, MakeBidMove):
                        last_make_bid_move = move
                        break
                
                # Determine the next valid bid amount
                if last_make_bid_move:
                    # Must bid higher than current bid
                    next_bid_amount = last_make_bid_move.action.bid_amount + 1
                else:
                    # First bid must be at least min_bid (21)
                    next_bid_amount = ActionEvent.min_bid
                
                # Add all valid bid actions from next_bid_amount to max_bid
                for bid_amount in range(next_bid_amount, ActionEvent.max_bid + 1):
                    action = BidAction(bid_amount)
                    legal_actions.append(action)
            
            # During card play phase
            else:
                trick_moves = self.game.round.get_trick_moves()
                hand = self.game.round.players[current_player.player_id].hand
                legal_cards = []
                
                # First card of trick - can play anything
                if not trick_moves:
                    legal_cards = hand
                else:
                    # Must follow suit if possible
                    led_card: CTPinochleCard = trick_moves[0].card
                    cards_of_led_suit = [card for card in hand if card.suit == led_card.suit]
                    
                    if cards_of_led_suit:
                        # Must follow suit
                        legal_cards = cards_of_led_suit
                    else:
                        # Cannot follow suit - must play trump if have it
                        trump_suit = self.game.round.trump_suit
                        trump_cards = [card for card in hand if card.suit == trump_suit]
                        
                        if trump_cards:
                            # Must play trump
                            legal_cards = trump_cards
                        else:
                            # No suit and no trump - can play anything
                            legal_cards = hand
                
                # Create PlayCardAction for each legal card
                for card in legal_cards:
                    action = PlayCardAction(card=card)
                    legal_actions.append(action)
        
        return legal_actions