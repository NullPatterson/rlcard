'''
    File name: ctpinochle/utils/meld_calculator.py
    Author: Nol Patterson
    Date created: 2/8/2026
'''

from collections import Counter
from typing import List, Tuple

def calculate_meld(hand: List, trump_suit: str) -> Tuple[int, List[str]]:
    """
    Calculate meld points for a hand given trump suit
    
    Args:
        hand: List of CTPinochleCard objects
        trump_suit: Trump suit ('C', 'D', 'H', 'S')
    
    Returns:
        Tuple of (total_meld_points, list_of_meld_descriptions)
    
    Meld Scoring:
    - Run of trump (A, 10, K, Q, J): 15
    - Double run of trump: 150
    - 9 of trump: 1 (each)
    - Marriage in trump (K, Q): 4
    - Marriage not in trump (K, Q): 2
    - Pinochle (Q♠, J♦): 4
    - Double Pinochle: 30
    - Round of Aces: 10 (one of each suit)
    - Double Round of Aces: 100
    - Round of Kings: 8
    - Double Round of Kings: 80
    - Round of Queens: 6
    - Double Round of Queens: 60
    - Round of Jacks: 4
    - Double Round of Jacks: 40
    
    Rules:
    - Cards can be reused in multiple melds
    - Exception: Cards used in a run cannot also count for marriage points
    - Double marriages have no bonus (just base points for each)
    - Two 9s of trump are worth 1 point each (no bonus)
    """
    
    meld_points = 0
    meld_breakdown = []
    
    # Convert hand to card strings and count them
    # Each card (rank+suit combination) needs to be counted
    card_strings = []
    for card in hand:
        card_strings.append(f'{card.rank}{card.suit}')
    
    # Count cards by rank+suit
    hand_counter = Counter(card_strings)
    
    # Check for double run in trump
    trump_run = [f'A{trump_suit}', f'10{trump_suit}', f'K{trump_suit}', 
                 f'Q{trump_suit}', f'J{trump_suit}']
    
    has_run = False
    double_run = False
    
    if all(hand_counter[card] >= 2 for card in trump_run):
        meld_points += 150
        meld_breakdown.append("Double Run in trump: 150")
        has_run = True
        double_run = True
    elif all(hand_counter[card] >= 1 for card in trump_run):
        meld_points += 15
        meld_breakdown.append("Run in trump: 15")
        has_run = True
    
    # Check for marriages (only count if NOT in a run)
    if not has_run:
        for suit in ['C', 'D', 'H', 'S']:
            king = f'K{suit}'
            queen = f'Q{suit}'
            num_marriages = min(hand_counter[king], hand_counter[queen])
            
            if num_marriages > 0:
                if suit == trump_suit:
                    points = num_marriages * 4
                    meld_points += points
                    if num_marriages == 1:
                        meld_breakdown.append(f"Marriage in {suit}: {points}")
                    else:
                        meld_breakdown.append(f"Marriage in {suit} (×{num_marriages}): {points}")
                else:
                    points = num_marriages * 2
                    meld_points += points
                    if num_marriages == 1:
                        meld_breakdown.append(f"Marriage in {suit}: {points}")
                    else:
                        meld_breakdown.append(f"Marriage in {suit} (×{num_marriages}): {points}")
    
    # Check for 9s of trump
    nine_trump = f'9{trump_suit}'
    if hand_counter[nine_trump] > 0:
        points = hand_counter[nine_trump]
        meld_points += points
        if hand_counter[nine_trump] == 1:
            meld_breakdown.append(f"9 of trump: 1")
        else:
            meld_breakdown.append(f"9 of trump (×{hand_counter[nine_trump]}): {points}")
    
    # Check for double pinochle (both Q♠ and both J♦)
    if hand_counter['QS'] == 2 and hand_counter['JD'] == 2:
        meld_points += 30
        meld_breakdown.append("Double Pinochle: 30")
    # Check for single pinochle
    elif hand_counter['QS'] >= 1 and hand_counter['JD'] >= 1:
        meld_points += 4
        meld_breakdown.append("Pinochle: 4")
    
    # Check for rounds (Aces, Kings, Queens, Jacks)
    round_checks = [
        ('A', 10, "Round of Aces", 100),
        ('K', 8, "Round of Kings", 80),
        ('Q', 6, "Round of Queens", 60),
        ('J', 4, "Round of Jacks", 40)
    ]
    
    for rank, base_points, name, double_points in round_checks:
        round_cards = [f'{rank}{suit}' for suit in ['C', 'D', 'H', 'S']]
        min_count = min(hand_counter[card] for card in round_cards)
        
        if min_count >= 2:
            meld_points += double_points
            meld_breakdown.append(f"Double {name}: {double_points}")
        elif min_count >= 1:
            meld_points += base_points
            meld_breakdown.append(f"{name}: {base_points}")
    
    return meld_points, meld_breakdown


def format_meld_display(hand: List, trump_suit: str) -> str:
    """
    Format meld calculation for display
    
    Args:
        hand: List of CTPinochleCard objects
        trump_suit: Trump suit
    
    Returns:
        Formatted string showing meld breakdown and total
    """
    meld_points, meld_breakdown = calculate_meld(hand, trump_suit)
    
    if not meld_breakdown:
        return "No meld: 0 points"
    
    output = "Meld breakdown:\n"
    for item in meld_breakdown:
        output += f"  - {item}\n"
    output += f"\nTotal Meld: {meld_points} points"
    
    return output