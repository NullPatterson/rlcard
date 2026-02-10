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
from .utils.meld_calculator import calculate_meld

class CTPinochleRound:
    @property
    def dealer_id(self) -> int:
        return self.dealer_id
    
    @property
    def roundphase(self):
        if self.is_over():
            return 'game over'
        elif self.trump_suit is None:
            return 'bidding'
        elif not self.meld_shown():
            return 'show meld'
        else:
            return 'play card'
        
    def __init__(self, num_players: int, dealer_id: int, np_random):
        if num_players != 3:
            raise Exception(f'CTPinochleRound: Currently only 3 players supported, got {num_players}')
        
        self.dealer_id = dealer_id
        self.np_random = np_random
        self.dealer: CTPinochleDealer = CTPinochleDealer(self.np_random)

        # Initialize Players
        self.players: List[CTPinochlePlayer] = []
        for player_id in range(num_players):
            self.players.append(CTPinochlePlayer(player_id=player_id, np_random=self.np_random))
        
        # Deal cards (16 to each player in batches of 4)
        dealing = True 
        cards_dealt = 0
        while dealing:
            for player in self.players:
                self.dealer.deal_cards(player, 4)
            cards_dealt += 12 # 3 players dealt 4 cards each
            if cards_dealt == 48: dealing = False

        # Game State
        self.current_player_id: int = (dealer_id + 1) % 3 # Lets player left of dealer bid first
        self.move_sheet: List[CTPinochleMove] = []
        self.move_sheet.append(DealHandMove(dealer=self.players[dealer_id], shuffled_deck=self.dealer.shuffled_deck))

        # Bidding State
        self.current_bid: int = 0
        self.pass_count: int = 0
        self.bid_round: int = 0 # Bidding goes around max of 3 times or if two people have passed
        self.bid_winner_id: int or None = None 
        self.winning_bid_move: MakeBidMove or None = None
        self.player_pass: List[bool] = [False, False, False] 

        # Trump and Meld State
        self.trump_suit: str or None = None 
        self.meld_shown: bool = False 
        self.player_meld_points: List[int] = [0, 0, 0] # Meld Points for each player
        self.player_meld_cards: List[List] = [[], [], []] # What cards have been shown for each player

        # Trick State 
        self.play_card_count: int = 0
        self.trick_points: List[int] = [0, 0, 0]
        self.tricks_won: List[int] = [0, 0, 0] # Number of tricks won by each player. matters as if they win 0 they lose all meld for round

    def is_bidding_over(self) -> bool:
        # Bidding ends when 2 players pass, 3 rounds of bidding
        # If the first 2 players to be able to bid pass the dealer is stuck at 20
        return sum(self.player_pass) == 2 or self.bid_round > 2 # Using 0 index as first index for bid_round count
    
    # Returns whetehr the round is finished
    def is_over(self) -> bool:
        if not self.is_bidding_over():
            return False
        if not self.meld_shown:
            return False
        # Round is over when all cards have been played 
        for player in self.players:
            if len(player.hand) > 0:
                return False
        return True
    
    def get_current_player(self) -> CTPinochlePlayer or None:
        return None if self.current_player_id is None else self.players[self.current_player_id]
    
    def get_trick_moves(self) -> List[PlayCardMove]:
        # Get cards played in current trick 
        trick_moves: List[PlayCardMove] = []
        if self.meld_shown and self.play_card_count > 0:
            trick_size = self.play_card_count % 3
            if trick_size == 0:
                trick_size = 3
            for move in self.move_sheet[-trick_size:]:
                if isinstance(move, PlayCardMove):
                    trick_moves.append(move)
        return trick_moves 
    
    # Hnadle bidding actions 
    def make_call(self, action: CallActionEvent): # FLAG I need to figure out where players get to pass and make sure if they have passed already
                                                  # Then they don't get to bid again they just automatically pass
        current_player = self.players[self.current_player_id]

        if isinstance(action, PassBid):
            if self.players_passed[self.current_player_id]:
                raise Exception(f'Player {self.current_player_id} has already passed and cannot bid')
    
            self.move_sheet.append(MakePassBidMove(current_player))
            self.pass_count += 1

            # Check if dealer is stuck at 20
            # 3 moves should be the first 2 pass and the dealing of cards
            if  len(self.move_sheet) and self.current_bid == 0:
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
            # Maybe reset pass_count but i don't think thats necessary 
            # FLAG I think pass_count may need a reworking we will see how it runs
            make_bid_move = MakeBidMove(current_player, action)
            self.winning_bid_move = make_bid_move
            self.move_sheet.append(make_bid_move)

        # Move to next player who has not already passed if bidding is not over
        if not self.is_bidding_over():
            # Find next active player (skip those who have passed)
            next_player = (self.current_player_id + 1) % 3
            while self.players_passed[next_player]:
                next_player = (next_player + 1) % 3
            self.current_player_id = next_player
        else:
            # Player to lead the first trick is the one who won the bid
            self.current_player_id = self.bid_winner_id
        
    def set_trump(self, trump_suit: str):
        if self.trump_suit is not None:
            raise Exception(f'Trump already set to {self.trump_suit}')
        if trump_suit not in ['C', 'D', 'H', 'S']:
            raise Exception(f'Invalid trump suit: {trump_suit}')
        
        self.trump_suit = trump_suit

        # Calculate meld for all players
        for player in self.players:
            meld_points, _ = calculate_meld(player.hand, self.trump_suit)
            self.player_meld_points[player.player_id] = meld_points
    
    def show_meld(self):
        # Mark that meld has been shown
        if self.trump_suit is None:
            raise Exception('Cannot show meld before trump is set')
        self.meld_shown = True
        # Bid winner leads first trick 
        self.current_player_id = self.bid_winner_id
    
    # Handles playing a card
    def play_card(self, action: PlayCardAction):
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
            
            # Calculate trick points
            trick_points = sum(1 for move in trick_moves if move.card.rank in ['A', '10', 'K'])
            
            # Bonus point for last trick
            if self.play_card_count == 48:
                trick_points += 1
            
            self.trick_points[trick_winner.player_id] += trick_points
        else:
            # Move to next player
            self.current_player_id = (self.current_player_id + 1) % 3
        
    # FLAG where are legal moves checked before this
    def _determine_trick_winner(self, trick_moves: List[PlayCardMove]) -> CTPinochlePlayer:
        lead_suit = trick_moves[0].card.suit 
        winning_card = trick_moves[0].card
        trick_winner = trick_moves[0].player

        rank_order = {'9': 0, 'J': 1, 'Q': 2, 'K': 3, '10': 4, 'A': 5}

        for move in trick_moves[1:]:
            card = move.card
            player = move.player

            # Trump beats non-trump
            if card.suit == self.trump_suit and winning_card.suit != self.trump_suit:
                winning_card = card
                trick_winner = player
            # Both same suit
            elif card.suit == winning_card.suit:
                # If two cards of same rank and suit are played in the same trick
                # Whoever played the first one wins hence this is not >=
                if rank_order[card.rank] > rank_order[winning_card.rank]:
                    winning_card = card 
                    trick_winner = player
            
        return trick_winner 
    
    # Calculate final scores for the round
    def calculate_scores(self) -> List[int]:
        scores = [0, 0, 0]

        for player_id in range(3):
            # Calculate total points(meld + tricks)
            total_points = self.player_meld_points[player_id] + self.trick_points[player_id]
            
            # If they took no tricks they lose meld and have 0 points from tricks
            if self.tricks_won[player_id] == 0:
                total_points = 0
            
            # If the player who did not win the bid does not meet or pass the claimed points
            # They lose all points earned that round and then lose points that they bid from their game total
            if player_id == self.bid_winner_id:
                if total_points >= self.current_bid:
                    scores[player_id] = total_points
                else:
                    scores[player_id] = -self.current_bid
            else:
                # Non bidders score any points they won through tricks or meld at this point
                scores[player_id] = total_points
        
        return scores

    def get_perfect_information(self):
        # Get Complete Game State
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

# FLAG Might need to print the current game state at this point based off print_scene in bridge/round.py