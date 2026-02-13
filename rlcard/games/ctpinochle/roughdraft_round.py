'''
    File name: ctpinochle/round.py
    Author: Nol Patterson
    Date created: 2/8/2026
'''

from typing import List

from .dealer import CTPinochleDealer
from .player import CTPinochlePlayer
from .utils.action_event import CallActionEvent, PassBid, BidAction, PlayCardAction
from .utils.move import CTPinochleMove, DealHandMove, PlayCardMove, MakeBidMove, MakePassMove
from .utils.meld_calculator import calculate_meld

class CTPinochleRound:

    @property
    def dealer_id(self) -> int:
        return self._dealer_id

    @property
    def round_phase(self):
        if self.is_over():
            return 'game over'
        elif self.trump_suit is None:
            return 'bidding'
        elif not self.meld_shown:
            return 'show meld'
        else:
            return 'play card'

    def __init__(self, num_players: int, dealer_id: int, np_random):
        ''' Initialize the round class

        Args:
            num_players: int (should be 3 for this variant)
            dealer_id: int (0, 1, or 2)
            np_random: numpy random generator
        '''
        if num_players != 3:
            raise Exception(f'CTPinochleRound: only 3 players supported, got {num_players}')
        
        self._dealer_id = dealer_id
        self.np_random = np_random
        self.dealer: CTPinochleDealer = CTPinochleDealer(self.np_random)
        
        # Initialize players
        self.players: List[CTPinochlePlayer] = []
        for player_id in range(num_players):
            self.players.append(CTPinochlePlayer(player_id=player_id, np_random=self.np_random))
        
        # Deal cards (16 to each player)
        for player in self.players:
            self.dealer.deal_cards(player, 16)
        
        # Game state
        self.current_player_id: int = (dealer_id + 1) % 3  # Player to left of dealer bids first
        self.move_sheet: List[CTPinochleMove] = []
        self.move_sheet.append(DealHandMove(dealer=self.players[dealer_id], shuffled_deck=self.dealer.shuffled_deck))
        
        # Bidding state
        self.current_bid: int = 0
        self.pass_count: int = 0
        self.bid_winner_id: int or None = None
        self.winning_bid_move: MakeBidMove or None = None
        
        # Trump and meld state
        self.trump_suit: str or None = None
        self.meld_shown: bool = False
        self.player_meld_points: List[int] = [0, 0, 0]  # Meld points for each player
        
        # Trick state
        self.play_card_count: int = 0
        self.trick_points: List[int] = [0, 0, 0]  # Points from tricks for each player
        self.tricks_won: List[int] = [0, 0, 0]  # Number of tricks won by each player

    def is_bidding_over(self) -> bool:
        ''' Return whether bidding is over '''
        # Bidding ends when 2 players pass (or all 3 pass and dealer stuck at 20)
        return self.pass_count >= 2 or (self.pass_count == 3 and self.bid_winner_id is not None)

    def is_over(self) -> bool:
        ''' Return whether the game is over '''
        if not self.is_bidding_over():
            return False
        if not self.meld_shown:
            return False
        # Game is over when all cards have been played
        for player in self.players:
            if len(player.hand) > 0:
                return False
        return True

    def get_current_player(self) -> CTPinochlePlayer or None:
        return None if self.current_player_id is None else self.players[self.current_player_id]

    def get_trick_moves(self) -> List[PlayCardMove]:
        ''' Get the cards played in the current trick '''
        trick_moves: List[PlayCardMove] = []
        if self.meld_shown and self.play_card_count > 0:
            trick_size = self.play_card_count % 3
            if trick_size == 0:
                trick_size = 3
            for move in self.move_sheet[-trick_size:]:
                if isinstance(move, PlayCardMove):
                    trick_moves.append(move)
        return trick_moves

    def make_call(self, action: CallActionEvent):
        ''' Handle bidding actions '''
        current_player = self.players[self.current_player_id]
        
        if isinstance(action, PassBid):
            self.move_sheet.append(MakePassMove(current_player))
            self.pass_count += 1
            
            # Check if dealer is stuck at 20
            if self.pass_count == 3 and self.current_bid == 0:
                # Dealer must take bid at 20
                self.bid_winner_id = self.dealer_id
                self.current_bid = 20
                # Create implicit bid move for dealer
                dealer_bid = BidAction(20)
                self.winning_bid_move = MakeBidMove(self.players[self.dealer_id], dealer_bid)
                self.move_sheet.append(self.winning_bid_move)
                self.current_player_id = self.dealer_id
                return
                
        elif isinstance(action, BidAction):
            if action.bid_amount <= self.current_bid:
                raise Exception(f'Bid {action.bid_amount} must be higher than current bid {self.current_bid}')
            
            self.current_bid = action.bid_amount
            self.bid_winner_id = self.current_player_id
            self.pass_count = 0  # Reset pass count
            make_bid_move = MakeBidMove(current_player, action)
            self.winning_bid_move = make_bid_move
            self.move_sheet.append(make_bid_move)
        
        # Move to next player if bidding not over
        if not self.is_bidding_over():
            self.current_player_id = (self.current_player_id + 1) % 3
        else:
            # Bidding over, bid winner chooses trump
            self.current_player_id = self.bid_winner_id

    def set_trump(self, trump_suit: str):
        ''' Bid winner sets trump suit '''
        if self.trump_suit is not None:
            raise Exception('Trump already set')
        if trump_suit not in ['C', 'D', 'H', 'S']:
            raise Exception(f'Invalid trump suit: {trump_suit}')
        
        self.trump_suit = trump_suit
        
        # Calculate meld for all players
        for player in self.players:
            meld_points, _ = calculate_meld(player.hand, self.trump_suit)
            self.player_meld_points[player.player_id] = meld_points

    def show_meld(self):
        ''' Mark that meld has been shown '''
        if self.trump_suit is None:
            raise Exception('Cannot show meld before trump is set')
        self.meld_shown = True
        # Bid winner leads first trick
        self.current_player_id = self.bid_winner_id

    def play_card(self, action: PlayCardAction):
        ''' Handle playing a card '''
        current_player = self.players[self.current_player_id]
        self.move_sheet.append(PlayCardMove(current_player, action))
        
        card = action.card
        current_player.remove_card_from_hand(card=card)
        self.play_card_count += 1
        
        # Check if trick is complete
        trick_moves = self.get_trick_moves()
        if len(trick_moves) == 3:
            # Determine trick winner
            trick_winner = self._determine_trick_winner(trick_moves)
            self.current_player_id = trick_winner.player_id
            self.tricks_won[trick_winner.player_id] += 1
            
            # Calculate trick points (A=1, 10=1, K=1, others=0)
            trick_points = sum(1 for move in trick_moves if move.card.rank in ['A', '10', 'K'])
            
            # Add bonus point for last trick
            if self.play_card_count == 48:  # All cards played
                trick_points += 1
            
            self.trick_points[trick_winner.player_id] += trick_points
        else:
            # Move to next player
            self.current_player_id = (self.current_player_id + 1) % 3

    def _determine_trick_winner(self, trick_moves: List[PlayCardMove]) -> CTPinochlePlayer:
        ''' Determine who won the trick '''
        lead_suit = trick_moves[0].card.suit
        winning_card = trick_moves[0].card
        trick_winner = trick_moves[0].player
        
        # Card rank order: 9 < J < Q < K < 10 < A
        rank_order = {'9': 0, 'J': 1, 'Q': 2, 'K': 3, '10': 4, 'A': 5}
        
        for move in trick_moves[1:]:
            card = move.card
            player = move.player
            
            # Trump beats non-trump
            if card.suit == self.trump_suit and winning_card.suit != self.trump_suit:
                winning_card = card
                trick_winner = player
            # Both same suit (trump or lead)
            elif card.suit == winning_card.suit:
                if rank_order[card.rank] > rank_order[winning_card.rank]:
                    winning_card = card
                    trick_winner = player
        
        return trick_winner

    def calculate_scores(self) -> List[int]:
        ''' Calculate final scores for the round '''
        scores = [0, 0, 0]
        
        for player_id in range(3):
            # Calculate total points (meld + tricks)
            total_points = self.player_meld_points[player_id] + self.trick_points[player_id]
            
            # Check if player took at least one trick (required to keep meld)
            if self.tricks_won[player_id] == 0:
                total_points = self.trick_points[player_id]  # Lose meld
            
            # Special case: bid winner
            if player_id == self.bid_winner_id:
                if total_points >= self.current_bid:
                    scores[player_id] = total_points
                else:
                    # Failed to make bid - lose all points including meld
                    scores[player_id] = -self.current_bid
            else:
                # Non-bidders always score their points (if they took a trick)
                scores[player_id] = total_points
        
        return scores

    def get_perfect_information(self):
        ''' Get complete game state '''
        state = {}
        state['move_count'] = len(self.move_sheet)
        state['dealer_id'] = self.dealer_id
        state['current_player_id'] = self.current_player_id
        state['round_phase'] = self.round_phase
        state['current_bid'] = self.current_bid
        state['bid_winner_id'] = self.bid_winner_id
        state['trump_suit'] = self.trump_suit
        state['meld_shown'] = self.meld_shown
        state['player_meld_points'] = self.player_meld_points
        state['hands'] = [player.hand for player in self.players]
        state['trick_moves'] = self.get_trick_moves()
        state['trick_points'] = self.trick_points
        state['tricks_won'] = self.tricks_won
        return state