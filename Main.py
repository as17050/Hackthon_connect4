import streamlit as st
import numpy as np
import random
import math
from typing import List, Tuple, Optional
from PIL import Image
import time
import threading

#Opc-UA variable
balldropDone=False
ErrorCode=0
StateMachine=0

# Game Constants
ROW_COUNT = 6
COLUMN_COUNT = 7
WINDOW_LENGTH = 4
EMPTY = 0
PLAYER_PIECE = 1
OPPONENT_PIECE = 2


# Streamlit Page Configuration
st.set_page_config(page_title='Connect 4 AI', page_icon='🔵')
st.image("Festo.png", caption="", width=200)


def difficultyOnChange():
    st.session_state['game'].depth = difficulty_map[difficulty]
    print(f"Level (DEPTH): {st.session_state['game'].depth}")

opponentChoice = st.radio(
    "Who would you like to play against?",
    ["AI", "Another player"],
    captions=[
        "Artificial opponent based on the minimax algorithm. Human against machine!",
        "An opponent of flesh and blood",
    ],
)

opponent_map = {
    "AI": True,
    "Another player": False,
    "hard": 5
}

if 'game' in st.session_state.keys():
    st.session_state['game'].matchVsAi = opponent_map[opponentChoice]
    #st.write(f"Selected Opponent: {opponentChoice}")
difficulty = st.select_slider(
    "Select a difficulty",
    options=["easy", "medium", "hard"],
    disabled=opponentChoice == "Another player"
)

difficulty_map = {
    "easy": 1,
    "medium": 3,
    "hard": 5
}

if 'game' in st.session_state.keys():
    st.session_state['game'].depth = difficulty_map[difficulty]
st.write(f"Selected Difficulty: {difficulty}")

def clearButtonClick():
    #write opc-ua variable
    CPX_Opc_ua_client.writeOPC_UA_NodeValue(nodeID=Cpx_opc_ua_gvl_node_list['gameOver'],value=True,variableType=ua.VariantType.Boolean)
    st.session_state['game'] = Connect4Game()


#clear button
st.button(label="Clear",on_click=clearButtonClick)


if 'game' in st.session_state.keys():
    st.session_state['game'].depth = difficulty_map[difficulty]
# depth = difficulty_map[difficulty]

#*******************************************OPC-UA-Client*********************************************
from opcua import Client
from opcua import ua
#logging.basicConfig(level=logging.DEBUG)
Cpx_opc_ua_gvl_node_list={
    'MatchStarted'      :"ns=4;s=|var|CPX-E-CEC-C1-PN.Application.GVL_OPC_UA.bMatchStarted",
    'bMatchFinished'    :"ns=4;s=|var|CPX-E-CEC-C1-PN.Application.GVL_OPC_UA.bMatchFinished",
    'ErrorCode'        :"ns=4;s=|var|CPX-E-CEC-C1-PN.Application.GVL_OPC_UA.iErrorCode",
    'EmptyBoard'       :"ns=4;s=|var|CPX-E-CEC-C1-PN.Application.GVL_OPC_UA.bEmptyBoard",
    'BallDropColumn'   :"ns=4;s=|var|CPX-E-CEC-C1-PN.Application.GVL_OPC_UA.iBallDropColumn",
    'BallDropDone'     :"ns=4;s=|var|CPX-E-CEC-C1-PN.Application.GVL_OPC_UA.bBallDropDone",
    'StateMachine'      :"ns=4;s=|var|CPX-E-CEC-C1-PN.Application.GVL_OPC_UA.StateMachine",
    'PlayerSet'         :"ns=4;s=|var|CPX-E-CEC-C1-PN.Application.GVL_OPC_UA.Player",
    'test'              :"ns=4;s=|var|CPX-E-CEC-C1-PN.Application.GVL_OPC_UA.iTestvariable_write",
    'gameOver'          :"ns=4;s=|var|CPX-E-CEC-C1-PN.Application.GVL_OPC_UA.bGameOver",
    'iRow'              :"ns=4;s=|var|CPX-E-CEC-C1-PN.Application.GVL_OPC_UA.iRow"
}

#****************************************Connect the opc-ua client********************************************
opc_ua_url = "opc.tcp://192.168.0.10:4840"
print("OPC UA is running")

class UA_Client():
    def __init__(self,url):
        self.url=url
        try:
            self.client=Client(self.url)
            self.client.connect()
            print("OPC-UA connection successful")
        except Exception as e:
            print(f"OPC-UA connection not established {e}")

    def readOPC_UA_NodeValue(self, nodeID):
        refNode=self.client.get_node(nodeID)
        return refNode.get_value()

    def writeOPC_UA_NodeValue(self, nodeID, value, variableType=ua.VariantType.Int16):
        refNode=self.client.get_node(nodeID)
        return refNode.set_value(value=value,varianttype=variableType)
        #confirm if the value is written

CPX_Opc_ua_client=UA_Client(url=opc_ua_url)

class Connect4Game:
    def __init__(self):
        self.board = np.zeros((ROW_COUNT, COLUMN_COUNT), dtype=int)
        self.matchVsAi = True
        self.depth = 1
        self.game_over = False
        self.winner: Optional[int] = None
        self.turn = 0  # 0 = Player's turn, 1 = Opponent's turn

    def drop_piece(self, row: int, col: int, piece: int):
        self.board[row][col] = piece

    def is_valid_location(self, col: int) -> bool:
        return self.board[ROW_COUNT - 1][col] == EMPTY

    def get_next_open_row(self, col: int) -> int:
        for r in range(ROW_COUNT):
            if self.board[r][col] == EMPTY:
                return r
        raise ValueError("Column is full")

    def winning_move(self, piece: int) -> bool:
        # Horizontal check
        for c in range(COLUMN_COUNT - 3):
            for r in range(ROW_COUNT):
                if all(self.board[r][c + i] == piece for i in range(WINDOW_LENGTH)):
                    return True

        # Vertical check
        for c in range(COLUMN_COUNT):
            for r in range(ROW_COUNT - 3):
                if all(self.board[r + i][c] == piece for i in range(WINDOW_LENGTH)):
                    return True

        # Positive diagonal check
        for c in range(COLUMN_COUNT - 3):
            for r in range(ROW_COUNT - 3):
                if all(self.board[r + i][c + i] == piece for i in range(WINDOW_LENGTH)):
                    return True

        # Negative diagonal check
        for c in range(COLUMN_COUNT - 3):
            for r in range(3, ROW_COUNT):
                if all(self.board[r - i][c + i] == piece for i in range(WINDOW_LENGTH)):
                    return True

        return False

    def evaluate_window(self, window: List[int], piece: int) -> int:
        score = 0
        opp_piece = PLAYER_PIECE if piece == OPPONENT_PIECE else OPPONENT_PIECE

        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(EMPTY) == 1:
            score += 10
        elif window.count(piece) == 2 and window.count(EMPTY) == 2:
            score += 5

        if window.count(opp_piece) == 3 and window.count(EMPTY) == 1:
            score -= 80

        return score

    def score_position(self, piece: int) -> int:
        score = 0

        # Center column preference
        center_array = list(self.board[:, COLUMN_COUNT // 2])
        center_count = center_array.count(piece)
        score += center_count * 6

        # Horizontal scoring
        for r in range(ROW_COUNT):
            row_array = list(self.board[r, :])
            for c in range(COLUMN_COUNT - 3):
                window = row_array[c:c + WINDOW_LENGTH]
                score += self.evaluate_window(window, piece)

        # Vertical scoring
        for c in range(COLUMN_COUNT):
            col_array = list(self.board[:, c])
            for r in range(ROW_COUNT - 3):
                window = col_array[r:r + WINDOW_LENGTH]
                score += self.evaluate_window(window, piece)

        # Positive diagonal scoring
        for r in range(ROW_COUNT - 3):
            for c in range(COLUMN_COUNT - 3):
                window = [self.board[r + i][c + i] for i in range(WINDOW_LENGTH)]
                score += self.evaluate_window(window, piece)

        # Negative diagonal scoring
        for r in range(3, ROW_COUNT):
            for c in range(COLUMN_COUNT - 3):
                window = [self.board[r - i][c + i] for i in range(WINDOW_LENGTH)]
                score += self.evaluate_window(window, piece)

        return score

    def is_terminal_node(self) -> bool:
        return (self.winning_move(PLAYER_PIECE) or
                self.winning_move(OPPONENT_PIECE) or
                len(self.get_valid_locations()) == 0)

    def get_valid_locations(self) -> List[int]:
        return [col for col in range(COLUMN_COUNT) if self.is_valid_location(col)]

    def order_moves(self, valid_locations: List[int], piece: int) -> List[int]:
        scores = []
        for col in valid_locations:
            row = self.get_next_open_row(col)
            self.drop_piece(row, col, piece)
            score = self.score_position(piece)
            scores.append((score, col))
            self.board[row][col] = EMPTY  # Undo move
        scores.sort(reverse=True)
        ordered_moves = [col for score, col in scores]
        return ordered_moves

    def minimax(self, depth: int, alpha: float, beta: float, maximizingPlayer: bool) -> Tuple[Optional[int], int]:
        valid_locations = self.get_valid_locations()
        is_terminal = self.is_terminal_node()
        if depth == 0 or is_terminal:
            if is_terminal:
                if self.winning_move(OPPONENT_PIECE):
                    return (None, math.inf)
                elif self.winning_move(PLAYER_PIECE):
                    return (None, -math.inf)
                else:
                    return (None, 0)
            else:
                return (None, self.score_position(OPPONENT_PIECE))

        if maximizingPlayer:
            value = -math.inf
            best_col = random.choice(valid_locations)
            ordered_locations = self.order_moves(valid_locations, OPPONENT_PIECE)
            for col in ordered_locations:
                row = self.get_next_open_row(col)
                self.drop_piece(row, col, OPPONENT_PIECE)
                new_score = self.minimax(depth - 1, alpha, beta, False)[1]
                self.board[row][col] = EMPTY  # Undo move
                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return best_col, value
        else:
            value = math.inf
            best_col = random.choice(valid_locations)
            ordered_locations = self.order_moves(valid_locations, PLAYER_PIECE)
            for col in ordered_locations:
                row = self.get_next_open_row(col)
                self.drop_piece(row, col, PLAYER_PIECE)
                new_score = self.minimax(depth - 1, alpha, beta, True)[1]
                self.board[row][col] = EMPTY  # Undo move
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return best_col, value

    def handle_click(self, col: int):
        if self.is_valid_location(col) and not self.game_over and self.turn == 0:
            row = self.get_next_open_row(col)
            self.drop_piece(row, col, PLAYER_PIECE)
            if self.winning_move(PLAYER_PIECE):
                self.game_over = True
                self.winner = PLAYER_PIECE
            else:
                if len(self.get_valid_locations()) == 0:
                    self.game_over = True
                else:
                    self.turn = 1  # Switch to Opponents's turn
            st.session_state['game'] = self  # Update the game state
            st.rerun()
        if self.is_valid_location(col) and not self.game_over and self.turn == 1:
            row = self.get_next_open_row(col)
            self.drop_piece(row, col, OPPONENT_PIECE)
            if self.winning_move(OPPONENT_PIECE):
                self.game_over = True
                self.winner = OPPONENT_PIECE
            else:
                if len(self.get_valid_locations()) == 0:
                    self.game_over = True
                else:
                    self.turn = 0  # Switch back to player's turn
            st.session_state['game'] = self  # Update the game state
            st.rerun()

    def ai_move(self):
        if not self.game_over and self.turn == 1:
            col, _ = self.minimax(self.depth, -math.inf, math.inf, True)
            CPX_Opc_ua_client.writeOPC_UA_NodeValue(Cpx_opc_ua_gvl_node_list['test'], value=col + 1,variableType=ua.VariantType.Int16)
            if col is not None and self.is_valid_location(col):
                row = self.get_next_open_row(col)
                self.drop_piece(row, col, OPPONENT_PIECE)
                if self.winning_move(OPPONENT_PIECE):
                    self.game_over = True
                    self.winner = OPPONENT_PIECE
                else:
                    if len(self.get_valid_locations()) == 0:
                        self.game_over = True
                    else:
                        self.turn = 0  # Switch back to player's turn
            st.session_state['game'] = self  # Update the game state
            st.rerun()

    def draw_board(self):

        st.write('')  # Spacer

        # Draw the top buttons for dropping pieces, using color based on the turn
        cols = st.columns(COLUMN_COUNT)
        piece_emoji = '⬇️' if self.turn == 0 else '▽'  # Blue for player, Yellow for AI
        for col in range(COLUMN_COUNT):
            disabled = not self.is_valid_location(col) or self.game_over or (self.matchVsAi and self.turn != 0)
            if cols[col].button(piece_emoji, key=f'drop_{col}', use_container_width=True, disabled=disabled):
                #write the column position
                print(col)
                CPX_Opc_ua_client.writeOPC_UA_NodeValue(Cpx_opc_ua_gvl_node_list['test'],value=col+1,variableType=ua.VariantType.Int16)
                self.handle_click(col)

        # Draw the board with emojis representing each cell
        for row in range(ROW_COUNT - 1, -1, -1):
            cols = st.columns(COLUMN_COUNT)
            for col in range(COLUMN_COUNT):
                piece = self.board[row][col]
                cols[col].markdown(self.get_piece_html(piece), unsafe_allow_html=True)

        if self.game_over:
            if self.winner == PLAYER_PIECE:
                if self.matchVsAi:
                    st.success("Congratulations! You won the game! 🎉")
                else:
                    st.success("Player 1 won the game! 🎉")
            elif self.winner == OPPONENT_PIECE:
                if self.matchVsAi:
                    st.error("Game Over. The AI won the game. 🤖")
                else:
                    st.success("Player 2 won the game! 🎉")
            else:
                st.info("It's a tie! 🤝")

    def reinitialise(self):
        self.board = np.zeros((ROW_COUNT, COLUMN_COUNT), dtype=int)
        self.matchVsAi = True
        self.depth = 1
        self.game_over = False
        self.winner: Optional[int] = None
        self.turn = 0  # 0 = Player's turn, 1 = Opponent's turn

    @staticmethod
    def get_piece_html(piece: int) -> str:
        if piece == PLAYER_PIECE:
            emoji = '🔵'
        elif piece == OPPONENT_PIECE:
            emoji = '⚫'
        else:
            emoji = '⚪️'
        return f"<div style='text-align: center; font-size: 50px;'>{emoji}</div>"


def main():
    st.markdown(
        """
        <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;align:center;}
            .css-1v0mbdj, .css-18e3th9 {
                flex: 1 !important;
                max-width: 100% !important;
                min-width: 100% !important;
            }
            
                    /* Cibler tous les sliders dans Streamlit */
        .stSlider input[type='range'] {
            background: #007bff; /* Couleur bleue pour la barre du slider */
            height: 8px; /* Taille de la barre du slider */
        }
        /* Personnaliser le "thumb" (bouton) du slider */
        .stSlider input[type='range']::-webkit-slider-thumb {
            background: #ff5733; /* Couleur orange pour le bouton */
            height: 20px;
            width: 20px;
            border-radius: 50%; /* Bouton circulaire */
            border: 2px solid #333; /* Bordure autour du bouton */
            cursor: pointer; /* Le curseur devient un pointeur */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    if 'game' not in st.session_state:
        st.session_state['game'] = Connect4Game()

    game: Connect4Game = st.session_state['game']

    # If it's AI's turn, make the AI move
    print('test')
    if game.matchVsAi and game.turn == 1 and not game.game_over:
        print("ai_move")
        game.ai_move()

    game.draw_board()


def readOpcUA():
    while True:
        ##real all the opc-ua variables BallDropDone
        #balldropDone=CPX_Opc_ua_client.readOPC_UA_NodeValue(nodeID=Cpx_opc_ua_gvl_node_list['bGameOver'])

        ErrorCode=CPX_Opc_ua_client.readOPC_UA_NodeValue(nodeID=Cpx_opc_ua_gvl_node_list['iRow'])
        #print(ErrorCode)
        #StateMachine=CPX_Opc_ua_client.readOPC_UA_NodeValue(nodeID=Cpx_opc_ua_gvl_node_list['StateMachine'])
        time.sleep(1)

if __name__=="__main__":
    opcUaThread = threading.Thread(target=readOpcUA)
    opcUaThread.start()
    main()




