import time

import gym
import numpy as np
import pygame
from gym import spaces

from gameLogic import getBlankBoard, getNewPiece, isValidPosition, removeCompleteLines
from tetris_model import *


class TetrisEnv(gym.Env):
    def __init__(self):
        """
        Initializes the Tetris environment for Gymnasium.
        - Initializes the Tetris model (board, pieces, etc.)
        - Sets up the action and observation spaces for the agent.
        """
        super(TetrisEnv, self).__init__()

        # Initialize the Tetris game model
        self.clock = None

        # Define action space: 4 possible actions (left, right, rotate, drop)
        # Mapping actions to discrete values:
        # 0: left, 1: right, 2: rotate, 3: drop
        self.action_space = spaces.Discrete(6)
        self.board = getBlankBoard()
        self.falling_piece = getNewPiece()
        self.next_piece = getNewPiece()
        self.level = 0
        self.score = 0
        self.lines = 0
        self.reward = 0
        # Define observation space: The observation consists of the board and related game state
        self.observation_space = spaces.Dict({
            "board": spaces.Box(low=0, high=1, shape=(10, 20), dtype=np.int8),  # 10x20 grid for the board
            "falling_piece": spaces.Dict({
                "shape": spaces.Discrete(7),  # 7 possible shapes
                "rotation": spaces.Discrete(4),  # 4 possible rotations
                "x": spaces.Discrete(10),  # X position on the board
                "y": spaces.Discrete(20),  # Y position on the board
            }),
            "next_piece": spaces.Dict({
                "shape": spaces.Discrete(7),
                "rotation": spaces.Discrete(4),
                "x": spaces.Discrete(10),
                "y": spaces.Discrete(20),
            }),
            "score": spaces.Discrete(10000),  # Arbitrary large number to handle scores
            "level": spaces.Discrete(10),  # Arbitrary max level
            "lines": spaces.Discrete(100),  # Arbitrary max lines cleared
        })
        self.last_fall_time = time.time()
        # Initialize state with the model
        self.state = State(self.board, self.falling_piece, self.next_piece, self.score, self.level, self.lines)
        # Re-initialize the Tetris game model (this resets the game state)
        self.model = TetrisModel(self.state)

    def reset(self, seed=None, options=None):
        """
        Resets the game environment to the starting state by re-initializing the model.

        Args:
            seed (int, optional): Seed for the random number generator.
            options (dict, optional): Additional options for resetting the environment.

        Returns:
            tuple: The initial observation and an info dictionary.
        """
        # Set the random seed for reproducibility if provided
        super().reset(seed=seed)
        self.state = State(self.board, self.falling_piece, self.next_piece, self.score, self.level, self.lines)
        # Re-initialize the Tetris game model (this resets the game state)
        self.model = TetrisModel(self.state)

        # Get the initial observation from the model's state
        observation = self.state.observation()

        # Info dictionary (can be expanded for additional metadata)
        info = {}

        return observation, info

    def step(self, action):
        """
        Applies the given action to the environment, updates the state, and returns the new state.

        Args:
            action (int): The action to apply, corresponding to one of the actions in action_space.

        Returns:
            tuple: A tuple containing:
                - observation (dict): The new state of the game after the action.
                - reward (float): The reward for the action taken.
                - terminated (bool): Whether the game is over (True if the game is over, False otherwise).
                - truncated (bool): Always False (used for environments that may truncate episodes based on other criteria).
                - info (dict): Additional information about the current step.
        """
        # Get the current state
        state = self.state

        # Apply the action to get the new state using the model's RESULT function
        state1 = self.model.RESULT(action)

        # Update the environment's state with the new state
        self.state = state1

        # Get the observation (new state of the game)
        observation = self.state.observation()

        # Calculate the reward for the action taken
        self.reward = self.model.STEP_COST()

        # Check if the game is over (terminated)
        terminated = self.model.GOAL_TEST()

        # Additional information (can be expanded as needed)
        info = {}

        # Render the game if render_mode is "human"
        if self.render_mode == "human":
            self.render()
        #print (" observation: ", observation, " reward: ", reward, " terminated: ", terminated, " info: ", info)
        # Return the updated observation, reward, termination status, truncated flag, and info
        return observation, self.reward, terminated, info

    def render(self, mode='human'):
        """
        Renders the environment. Currently, it prints the board state to the console.
        :param mode: The rendering mode.
        """
        if mode == 'human':
            board = self.state.observation()
            # print("\n".join("".join(str(cell) for cell in row) for row in board.T))
            if self.state.falling_piece is None:
                # No falling piece in play, so start a new piece at the top
                self.state.falling_piece = self.state.next_piece
                self.state.next_piece = getNewPiece()
                while self.state.next_piece == self.state.falling_piece:
                    self.state.next_piece = getNewPiece()
                self.last_fall_time = time.time()  # reset lastFallTime

                if not isValidPosition(self.state.board, self.state.falling_piece):
                    # pygame.quit()
                    #("should be done now lol")
                    return [self.state.score, self.state.lines_cleared]  # can't fit a new piece on the board, so game over
                self.state.gh.newPiece(self.state.falling_piece, self.state.board)

            checkForQuit()

            self.state.movingDown = False
            self.state.movingLeft = False
            self.state.movingRight = False

            # drawing everything on the screen
            fillBG()
            drawBoard(self.state.board)
            drawStatus(self.state.score, self.state.lines_cleared, self.state.level, self.state.brain)
            drawNextPiece(self.state.next_piece)
            if self.state.falling_piece is not None:
                drawPiece(self.state.falling_piece)
            updateDisplay()
        else:
            super().render()  # Raise an exception for unsupported modes

    def close(self):
        """Closes the environment."""
        pass
