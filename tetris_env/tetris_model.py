
from tetrisAI import *

class State:
    def __init__(self, board, falling_piece, next_piece, score, level, lines_cleared):
        self.board = board
        self.falling_piece = falling_piece
        self.next_piece = next_piece
        self.score = score
        self.level = level
        self.fall_freq = 0.27
        self.lines_cleared = lines_cleared
        self.last_fall_time = time.time()
        self.brain = brain=[1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0]
        self.gh = gameHandler(self.falling_piece, self.board, self.brain)

    def observation(self):
         return {
            "board": self.board,
            "falling_piece": self.falling_piece,
            "next_piece": self.next_piece,
            "score": self.score,
            "level": self.level,
            "lines_cleared": self.lines_cleared,
             "fall_freq": self.fall_freq
         }

    def flatten_observation(self):
        # Flatten the board into a 1D array
        observation = self.observation()
        flat_board = [cell for row in observation["board"] for cell in row]

        # Combine numeric attributes and other relevant info
        flat_obs = flat_board + [
            observation["falling_piece"],  # Add falling piece representation
            observation["next_piece"],  # Add next piece representation
            observation["score"],
            observation["level"],
            observation["lines_cleared"],
            observation["fall_freq"]
        ]
        return flat_obs

    def is_terminal(self):
        """
        Check if the game is over (no valid moves for the falling piece).

        Returns:
            bool: True if the game is over, otherwise False.
        """
        #return (self.falling_piece is None) and (not isValidPosition(self.board, self.falling_piece))
        return not isValidPosition(self.board, self.falling_piece)

    def rotate_piece(self, direction):
        # Rotate the falling piece
        original_rotation = self.falling_piece['rotation']
        self.falling_piece['rotation'] = (original_rotation + direction) % len(
            PIECES[self.falling_piece['shape']]
        )
        if not isValidPosition(self.board, self.falling_piece):
            self.falling_piece['rotation'] = original_rotation



class TetrisModel:
    def __init__(self, state):
        self.state = state
    # ACTION keys
    # 0: Left
    # 1: Right
    # 2: Rotate clockwise
    # 3: Rotate counter clockwise
    # 4: Drop

    def ACTIONS(self):
        """
        Defines the set of valid actions based on the current game state.

        Returns:
            list: A list of valid action numbers that can be taken at the current state.
        """

        valid_actions = []

        # Check if moving left is valid (only if there is space to the left)
        if isValidPosition(self.state.board, self.state.falling_piece, adjX=-1):
            valid_actions.append(0)  # 0 corresponds to "left"

        # Check if moving right is valid (only if there is space to the right)
        if isValidPosition(self.state.board, self.state.falling_piece, adjX=1):
            valid_actions.append(1)  # 1 corresponds to "right"

        # Check if rotating is valid (only if the rotation doesn't cause collision)
        rotated_piece = self.state.falling_piece.copy()
        rotated_piece['rotation'] = (rotated_piece['rotation'] + 1) % len(PIECES[rotated_piece['shape']])
        if isValidPosition(self.state.board, rotated_piece):
            valid_actions.append(3)  # 2 corresponds to "rotate"

        # Check if dropping is valid (always valid as long as the piece can fall)
        if isValidPosition(self.state.board, self.state.falling_piece, adjY=1):
            valid_actions.append(4)  # 3 corresponds to "drop"

        #print("valid actions: ", valid_actions)

        return valid_actions

    def advance_game_state(self):
        # Move the piece down
        if isValidPosition(self.state.board, self.state.falling_piece, adjY=1):
            self.state.falling_piece['y'] += 1
        else:
            # Piece has landed
            addToBoard(self.state.board, self.state.falling_piece)
            self.state.lines_cleared += removeCompleteLines(self.state.board)
            self.state.level, self.state.fall_freq = calculateLevelAndFallFreq(self.state.lines_cleared)
            self.state.score += self.state.lines_cleared * (self.state.level + 1) * 10
            self.state.falling_piece = self.state.next_piece
            self.state.next_piece = getNewPiece()

    def RESULT(self, action):
        #print("getting result")
        """
        Applies an action to the current state and returns the resulting state, reward, and done flag.

        Args:
            action (int): The action to apply, one of ['left', 'right', 'rotate', 'drop'].

        Returns:
            tuple: (new_state, reward, done)
                - new_state (State): The updated game state.
                - reward (float): The reward for performing the action.
                - done (bool): True if the game is over, False otherwise.
        """
        # Backup current state (to revert if needed)
        original_falling_piece = self.state.falling_piece.copy()

        # Apply the action
        if action == 0:  # Move left
            if isValidPosition(self.state.board, self.state.falling_piece, adjX=-1):
                self.state.falling_piece['x'] -= 1
        elif action == 1:  # Move right
            if isValidPosition(self.state.board, self.state.falling_piece, adjX=1):
                self.state.falling_piece['x'] += 1
        elif action == 2:  # Rotate clockwise
            self.state.rotate_piece(1)
        elif action == 3:  # Rotate counterclockwise
            self.state.rotate_piece(-1)
        elif action == 4:  # Hard drop
            while isValidPosition(self.state.board, self.state.falling_piece, adjY=1):
                self.state.falling_piece['y'] += 1
        elif action == 5:  # Do nothing
            pass


        # Update the board state
        self.advance_game_state()

        # Create new state object
        new_state = State(self.state.board, self.state.falling_piece, self.state.next_piece, self.state.score, self.state.level, self.state.lines_cleared)

        return new_state

    def GOAL_TEST(self):
        """
        Tests if the game is over by checking if a new piece can be placed on the board.

        Returns:
            bool: True if the game is over (board is full), False otherwise.
        """

        return not isValidPosition(self.state.board, self.state.falling_piece)

    def STEP_COST(self):

        print("valid actions: ", self.ACTIONS())
        """
        Calculates the reward for the current step:
        - Penalty (-1) for placing a block.
        - Reward (10) for each line cleared.
        """
        lines_cleared = removeCompleteLines(self.state.board)
        # print("lines cleared: ", lines_cleared)
        reward = -1  # Penalty for placing a block
        if lines_cleared > 0:
            reward += lines_cleared * 10  # Reward for clearing lines
        return reward
