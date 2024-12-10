import random
import sys
import time
import pygame
from typing import DefaultDict
from hashlib import new

from game import Game
from gameLogic import initPygame
from env import TetrisEnv


class Agent:
    def __init__(self, brain, numGames=1):
        initPygame()
        self.brain = brain  # Default brain
        self.game = Game()
        self.fitness = self.returnAverageFitness(numGames)

    def returnAverageFitness(self, numGames):
        totalFitness = 0.0
        for i in range(numGames):
            data = self.game.runGame(self.brain, False)
            if data[1] == 0:
                continue
            else:
                totalFitness += data[0] / data[1]  # fitness is calculated by score/lines cleared
        return totalFitness / numGames

    def evaluate_action(self, action, observation):
        """
        Simulate the outcome of an action and evaluate it using the agent's brain.
        """
        simulated_state = self.simulate_action(action, observation)
        features = self.extract_features(simulated_state)
        return sum(weight * feature for weight, feature in zip(self.brain, features))

    def simulate_action(self, action, observation):
        """
        Simulates the environment's state after taking a given action.
        """
        # Clone the current observation and apply the action to get the new state
        board = observation["board"].copy()
        piece = observation["falling_piece"].copy()
        # Apply the action logic (e.g., move piece, rotate, drop)
        if action == 0:  # Move left
            piece["x"] = max(piece["x"] - 1, 0)
        elif action == 1:  # Move right
            piece["x"] = min(piece["x"] + 1, len(board[0]) - 1)
        elif action == 2:  # Rotate
            piece["rotation"] = (piece["rotation"] + 1) % 4
        elif action == 3:  # Drop
            while self.is_valid_position(board, piece):
                piece["y"] += 1
            piece["y"] -= 1  # Revert to last valid position

        # Simulate adding the piece to the board
        self.add_piece_to_board(board, piece)
        return {"board": board, "falling_piece": piece}

    def extract_features(self, observation):
        """
        Extracts features from the current observation for evaluation.
        """
        board = observation["board"]
        column_heights = self.get_column_heights(board)
        max_height = max(column_heights)
        num_holes = self.count_holes(board)
        bumpiness = self.calculate_bumpiness(column_heights)

        return [max_height, num_holes, bumpiness]

    def get_column_heights(self, board):
        column_heights = []
        for col in zip(*board):
            height = len(board) - next((i for i, cell in enumerate(col) if cell), len(board))
            column_heights.append(height)
        return column_heights

    def count_holes(self, board):
        holes = 0
        for col in zip(*board):
            filled = False
            for cell in col:
                if cell:
                    filled = True
                elif filled:
                    holes += 1
        return holes

    def calculate_bumpiness(self, column_heights):
        return sum(abs(column_heights[i] - column_heights[i + 1]) for i in range(len(column_heights) - 1))

    def add_piece_to_board(self, board, piece):
        """
        Adds the piece to the board at its current position.
        Ensures numerical representation for colors.
        """
        shape_to_color = {'J': 1, 'Z': 2, 'S': 3, 'I': 4, 'O': 5, 'L': 6, 'T': 6}  # Map shapes to colors
        color = shape_to_color.get(piece["shape"], 0)  # Default to 0 if shape is invalid

        for x in range(len(piece["shape"])):
            for y in range(len(piece["shape"][x])):
                if piece["shape"][x][y] != 0:  # Ensure this cell is part of the shape
                    board[piece["x"] + x][piece["y"] + y] = color

    def is_valid_position(self, board, piece):
        """
        Checks if the piece can fit in the current position on the board.
        """
        for x in range(len(piece["shape"])):
            for y in range(len(piece["shape"][x])):
                if piece["shape"][x][y] != 0:
                    if (
                        piece["x"] + x < 0
                        or piece["x"] + x >= len(board[0])
                        or piece["y"] + y >= len(board)
                        or board[piece["x"] + x][piece["y"] + y] != 0
                    ):
                        return False
        return True

    def choose_action(self, observation):
        """
        Chooses the best action based on the agent's brain.
        """
        # print("choose_action")
        action_scores = {}
        for action in range(len(self.brain)):
            score = self.evaluate_action(action, observation)
            action_scores[action] = score
        best_action = max(action_scores, key=action_scores.get)
        return best_action

class Evolution:
    def __init__(self, env, gen_size=15, gen_count=50, elitism=0.2, mutation_rate=0.2):
        self.env = env
        self.gen_size = gen_size
        self.gen_count = gen_count
        self.elitism = elitism
        self.mutation_rate = mutation_rate
        self.total_reward = 0

        # Initialize population
        self.population = [self.random_brain() for _ in range(gen_size)]

    def random_brain(self):
        """Generate a random brain (list of weights)."""
        return [random.uniform(-1, 1) for _ in range(9)]

    def evaluate_fitness(self, brain, num_games=5):
        """Evaluate fitness of a brain by running it in the environment."""
        agent = Agent(brain)
        total_score = 0

        for _ in range(num_games):
            observation, _ = self.env.reset()
            done = False
            while not done:
                action = agent.choose_action(observation)
                observation, reward, done, _ = self.env.step(action)
                # print("current score: ", reward)
                total_score += reward

        print("total_score: ", agent.game.score)

        return total_score / num_games

    def evolve(self):
        """Run the evolutionary process."""
        for gen in range(self.gen_count):
            print(f"Generation {gen + 1}/{self.gen_count}")
            # Evaluate fitness for all agents

            fitness_scores = [
                (brain, self.evaluate_fitness(brain)) for brain in self.population
            ]
            fitness_scores.sort(key=lambda x: x[1], reverse=True)

            # Log the best performance
            print("fitness_scores: ", fitness_scores)
            best_brain, best_score = fitness_scores[0]

            print(f"Best Score: {best_brain}")

            # Select elites
            num_elites = max(1, int(self.gen_size * self.elitism))
            elites = [brain for brain, _ in fitness_scores[:num_elites]]

            # Create new generation
            new_population = elites.copy()
            while len(new_population) < self.gen_size:
                if len(elites) < 2:
                    parent_a = parent_b = random.choice(elites)
                else:
                    parent_a, parent_b = random.sample(elites, 2)
                child = self.crossover(parent_a, parent_b)
                child = self.mutate(child)
                new_population.append(child)

            self.population = new_population

        # Return the best brain after evolution
        return fitness_scores[0][0]

    def crossover(self, parent_a, parent_b):
        """Crossover two parents to produce a child."""
        return [random.choice([a, b]) for a, b in zip(parent_a, parent_b)]

    def mutate(self, brain):
        """Mutate a brain with a given probability."""
        return [
            weight + random.uniform(-0.1, 0.1) if random.random() < self.mutation_rate else weight
            for weight in brain
        ]


def evolve(self):
    for gen in range(self.gen_count):
        fitness_scores = [(brain, self.evaluate_fitness(brain)) for brain in self.population]
        fitness_scores.sort(key=lambda x: x[1], reverse=True)

        # Elites: top brains that are carried over without change
        elites = [brain for brain, _ in fitness_scores[:max(1, int(self.gen_size * self.elitism))]]

        new_population = elites.copy()  # Start with elites
        while len(new_population) < self.gen_size:
            parent_a, parent_b = random.sample(elites, 2)  # Select two elite parents
            child = self.crossover(parent_a, parent_b)  # Generate offspring
            child = self.mutate(child)  # Apply mutation
            new_population.append(child)  # Add the child to the new generation
        self.population = new_population  # Update population

        
def main():
    env = TetrisEnv()

    # Run evolution
    evolver = Evolution(env, gen_count=10, gen_size=10)
    best_brain = evolver.evolve()

    # Test the best brain
    agent = Agent(best_brain)
    observation, _ = env.reset()

    total_reward = 0
    done = False

    while not done:
        action = agent.choose_action(observation)
        observation, reward, done, _ = env.step(action)
        total_reward += reward
        print(f"Step Reward: {reward}, Total Accumulated Reward: {total_reward}")

    print("Total Reward: ", total_reward)
    env.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "evolve":
        evolver = Evolution()
    else:
        main()
