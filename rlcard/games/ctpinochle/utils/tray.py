'''
    File Name: ctpinochle/utils/tray.py
    Author: Nol Patterson
    Date Created: 2/8/2026
'''

class Tray(object):
    def __init__(self, board_id: int):
        if board_id <= 0:
            raise Exception(f'Tray: invalid board_id={board_id}')
        self.board_id = board_id
    
    @property 
    def dealer_id(self):
        return (self.board_id - 1) % 3 # It was originally % 4 i am assumign that was because bridge is 4 players and this pinochle will be 3 player
    
    # FLAG maybe use this class for tracking current scores as well?

    def __str__(self):
        return f'{self.board_id}: dealer_id={self.dealer_id}'