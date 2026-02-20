'''
    File name: envs/ctpinochle.py
    Author: Nol Patterson
    Date created: 2/8/2026
'''

import numpy as np
from collections import OrderedDict

from rlcard.envs import Env

from rlcard.games.ctpinochle import Game

from rlcard.games.ctpinochle.game import CTPinochleGame
from rlcard.games.ctpinochle.utils.action_event import ActionEvent
from rlcard.games.ctpinochle.utils.ctpinochle_card import CTPinochleCard
from rlcard.games.ctpinochle.utils.move import MakeBidMove, MakePassBidMove, PlayCardMove


class CTPinochleEnv(Env):
    ''' Pinochle Environment
    '''
    def __init__(self, config):
        self.name = 'ctpinochle'
        self.game = Game()
        super().__init__(config=config)
        self.pinochlePayoffDelegate = DefaultPinochlePayoffDelegate()
        self.pinochleStateExtractor = DefaultPinochleStateExtractor()
        state_shape_size = self.pinochleStateExtractor.get_state_shape_size()
        self.state_shape = [[1, state_shape_size] for _ in range(self.num_players)]
        self.action_shape = [None for _ in range(self.num_players)]

    def get_payoffs(self):
        ''' Get the payoffs of players.

        Returns:
            (list): A list of payoffs for each player.
        '''
        return self.pinochlePayoffDelegate.get_payoffs(game=self.game)

    def get_perfect_information(self):
        ''' Get the perfect information of the current state

        Returns:
            (dict): A dictionary of all the perfect information of the current state
        '''
        return self.game.round.get_perfect_information()

    def _extract_state(self, state):
        ''' Extract useful information from state for RL.

        Args:
            state (dict): The raw state

        Returns:
            (numpy.array): The extracted state
        '''
        return self.pinochleStateExtractor.extract_state(game=self.game)

    def _decode_action(self, action_id):
        ''' Decode Action id to the action in the game.

        Args:
            action_id (int): The id of the action

        Returns:
            (ActionEvent): The action that will be passed to the game engine.
        '''
        return ActionEvent.from_action_id(action_id=action_id)

    def _get_legal_actions(self):
        ''' Get all legal actions for current state.

        Returns:
            (list): A list of legal actions' id.
        '''
        raise NotImplementedError  # Not needed


class PinochlePayoffDelegate(object):

    def get_payoffs(self, game: CTPinochleGame):
        ''' Get the payoffs of players. Must be implemented in the child class.

        Returns:
            (list): A list of payoffs for each player.

        Note: Must be implemented in the child class.
        '''
        raise NotImplementedError


class DefaultPinochlePayoffDelegate(PinochlePayoffDelegate):
    WIN_BONUS = 50      # Extra reward for winning the game
    LOSS_PENALTY = -50  # Extra penalty for losing the game

    def __init__(self):
        pass

    def get_payoffs(self, game: CTPinochleGame):
        ''' Get the payoffs of players.

        Returns:
            (list): A list of payoffs for each player, using cumulative
                    total_scores plus a win/loss bonus at game end.
        '''
        if game.is_over():
            scores = np.array(game.get_payoffs(), dtype=float)  # cumulative totals

            # Add win bonus / loss penalty
            if game.winner_id is not None:
                scores[game.winner_id] += self.WIN_BONUS
                for player_id in range(game.num_players):
                    if player_id != game.winner_id:
                        scores[player_id] += self.LOSS_PENALTY

            return scores
        else:
            return np.array([0.0, 0.0, 0.0])


class PinochleStateExtractor(object):  # interface

    def get_state_shape_size(self) -> int:
        raise NotImplementedError

    def extract_state(self, game: CTPinochleGame):
        ''' Extract useful information from state for RL. Must be implemented in the child class.

        Args:
            game (CTPinochleGame): The game

        Returns:
            (numpy.array): The extracted state
        '''
        raise NotImplementedError

    @staticmethod
    def get_legal_actions(game: CTPinochleGame):
        ''' Get all legal actions for current state.

        Returns:
            (OrderedDict): A OrderedDict of legal actions' id.
        '''
        legal_actions = game.judger.get_legal_actions()
        legal_actions_ids = {action_event.action_id: None for action_event in legal_actions}
        return OrderedDict(legal_actions_ids)


class DefaultPinochleStateExtractor(PinochleStateExtractor):

    def __init__(self):
        super().__init__()
        self.max_bidding_rep_index = 15  # Max ~15 bidding moves (3 players, up to 5 rounds)
        self.last_bid_rep_size = 1 + 30  # pass + (bid 21-50)

    def get_state_shape_size(self) -> int:
        state_shape_size = 0
        state_shape_size += 3 * 48  # hands_rep_size (3 players, 48 cards)
        state_shape_size += 3 * 48  # trick_rep_size (3 players, 48 cards)
        state_shape_size += 48  # hidden_cards_rep_size
        state_shape_size += 3  # dealer_rep_size
        state_shape_size += 3  # current_player_rep_size
        state_shape_size += 3  # players_passed_rep_size
        state_shape_size += 1  # is_bidding_rep_size
        state_shape_size += self.max_bidding_rep_index  # bidding_rep_size
        state_shape_size += self.last_bid_rep_size  # last_bid_rep_size
        state_shape_size += 30  # current_bid_rep_size (21-50)
        state_shape_size += 4  # trump_suit_rep_size (C, D, H, S)
        state_shape_size += 1  # meld_shown_rep_size
        state_shape_size += 3  # player_melds_rep (normalized meld scores)
        state_shape_size += 3  # tricks_won_rep
        state_shape_size += 3  # trick_points_rep (normalized)
        return state_shape_size

    def extract_state(self, game: CTPinochleGame):
        ''' Extract useful information from state for RL.

        Args:
            game (CTPinochleGame): The game

        Returns:
            (numpy.array): The extracted state
        '''
        extracted_state = {}
        legal_actions: OrderedDict = self.get_legal_actions(game=game)
        raw_legal_actions = list(legal_actions.keys())
        current_player = game.round.get_current_player()
        current_player_id = current_player.player_id

        # construct hands_rep of hands of players (3 players, 48 cards each)
        hands_rep = [np.zeros(48, dtype=int) for _ in range(3)]
        if not game.is_over():
            for card in game.round.players[current_player_id].hand:
                hands_rep[current_player_id][card.card_id] = 1

        # construct trick_pile_rep (current trick being played)
        trick_pile_rep = [np.zeros(48, dtype=int) for _ in range(3)]
        if game.round.meld_shown and not game.is_over():
            trick_moves = game.round.get_trick_moves()
            for move in trick_moves:
                player = move.player
                card = move.card
                trick_pile_rep[player.player_id][card.card_id] = 1

        # construct hidden_card_rep (cards in other players' hands)
        hidden_cards_rep = np.zeros(48, dtype=int)
        if not game.is_over():
            for player in game.round.players:
                if player.player_id != current_player_id:
                    for card in player.hand:
                        hidden_cards_rep[card.card_id] = 1

        # construct dealer_rep
        dealer_rep = np.zeros(3, dtype=int)
        dealer_rep[game.round.dealer_id] = 1

        # construct current_player_rep
        current_player_rep = np.zeros(3, dtype=int)
        current_player_rep[current_player_id] = 1

        # construct players_passed_rep
        players_passed_rep = np.array(game.round.player_pass, dtype=int)

        # construct is_bidding_rep
        is_bidding_rep = np.array([0] if game.round.is_bidding_over() else [1])

        # construct bidding_rep
        bidding_rep = np.zeros(self.max_bidding_rep_index, dtype=int)
        bidding_rep_index = 0
        for move in game.round.move_sheet:
            if bidding_rep_index >= self.max_bidding_rep_index:
                break
            elif isinstance(move, PlayCardMove):
                break
            elif isinstance(move, (MakeBidMove, MakePassBidMove)):
                bidding_rep[bidding_rep_index] = move.action.action_id
                bidding_rep_index += 1

        # last_bid_rep (last bidding action)
        last_bid_rep = np.zeros(self.last_bid_rep_size, dtype=int)
        if not game.round.is_bidding_over():
            last_move = game.round.move_sheet[-1]
            if isinstance(last_move, (MakeBidMove, MakePassBidMove)):
                last_bid_rep[last_move.action.action_id] = 1

        # current_bid_rep (21-50)
        current_bid_rep = np.zeros(30, dtype=int)
        if game.round.current_bid > 0:
            bid_index = game.round.current_bid - 21
            if 0 <= bid_index < 30:
                current_bid_rep[bid_index] = 1

        # trump_suit_rep
        trump_suit_rep = np.zeros(4, dtype=int)
        if game.round.trump_suit:
            trump_suit_index = CTPinochleCard.suits.index(game.round.trump_suit)
            trump_suit_rep[trump_suit_index] = 1

        # meld_shown_rep
        meld_shown_rep = np.array([1] if game.round.meld_shown else [0])

        # player_melds_rep (normalized by dividing by 200)
        player_melds_rep = np.array(game.round.player_meld_points, dtype=float) / 200.0

        # tricks_won_rep
        tricks_won_rep = np.array(game.round.tricks_won, dtype=int)

        # trick_points_rep (normalized by dividing by 25)
        trick_points_rep = np.array(game.round.trick_points, dtype=float) / 25.0

        rep = []
        rep += hands_rep
        rep += trick_pile_rep
        rep.append(hidden_cards_rep)
        rep.append(dealer_rep)
        rep.append(current_player_rep)
        rep.append(players_passed_rep)
        rep.append(is_bidding_rep)
        rep.append(bidding_rep)
        rep.append(last_bid_rep)
        rep.append(current_bid_rep)
        rep.append(trump_suit_rep)
        rep.append(meld_shown_rep)
        rep.append(player_melds_rep)
        rep.append(tricks_won_rep)
        rep.append(trick_points_rep)

        obs = np.concatenate(rep)
        extracted_state['obs'] = obs
        extracted_state['legal_actions'] = legal_actions
        extracted_state['raw_legal_actions'] = raw_legal_actions
        extracted_state['raw_obs'] = obs
        return extracted_state

    def reset(self):
        ''' Start a new game
        
        Returns:
            (tuple): Tuple of (state, player_id)
        '''
        state, player_id = self.game.init_game()
        return self._extract_state(state), player_id