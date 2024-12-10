# Tetromino (a Tetris clone)
# By Al Sweigart al@inventwithpython.com
# http://inventwithpython.com/pygame
# Released under a "Simplified BSD" license

import random, time, pygame, sys
from pygame.locals import *
from tetrisAI import *


class Game():
    def runGame(self, brain = [1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0 ], delay = 0.02):
        # setup variables for the start of the game
        delay = 0.5
        self.board = getBlankBoard()
        self.lastMoveDownTime = time.time()
        self.lastMoveSidewaysTime = time.time()
        self.lastFallTime = time.time()
        self.movingDown = False # note: there is no movingUp variable
        self.movingLeft = False
        self.movingRight = False
        self.score = 0
        self.lines = 0
        self.level, self.fallFreq = calculateLevelAndFallFreq(self.lines)

        self.fallingPiece = getNewPiece()
        self.nextPiece = getNewPiece()
        self.gh = gameHandler(self.fallingPiece, self.board, brain)



        while True: # game loop

            time.sleep(delay)
            if self.fallingPiece == None:
                # No falling piece in play, so start a new piece at the top
                self.fallingPiece = self.nextPiece
                self.nextPiece = getNewPiece()
                # et kaks sama juppi jarjest ei tuleks
                while self.nextPiece == self.fallingPiece:
                    self.nextPiece = getNewPiece()
                self.lastFallTime = time.time() # reset lastFallTime

                if not isValidPosition(self.board, self.fallingPiece):
                    #pygame.quit()
                    return [self.score, self.lines] # can't fit a new piece on the board, so game over
                self.gh.newPiece(self.fallingPiece, self.board)

            checkForQuit()
            if self.gh.rotatePiece(self.fallingPiece['rotation'], self.fallingPiece) != 0:
                self.fallingPiece['rotation'] += self.gh.rotatePiece(self.fallingPiece['rotation'], self.fallingPiece)
                if not isValidPosition(self.board, self.fallingPiece): # kui jupp pöörab end mängulaualt välja
                    if self.fallingPiece['x'] < BOARDWIDTH/2: # kui on vasakul pool mängulauda
                        while not isValidPosition(self.board, self.fallingPiece):
                            self.fallingPiece['x'] += 1
                    else: # jupp on paremal pool mängulauda
                        while not isValidPosition(self.board, self.fallingPiece):
                            self.fallingPiece['x'] -= 1
            elif self.gh.movePieceToPosition(self.fallingPiece['x']) == -1:
                self.movingLeft = True
            elif self.gh.movePieceToPosition(self.fallingPiece['x']) == 1:
                self.movingRight = True
            else: # jupp on oiges kohas ja voib alla kukutada
                    self.movingLeft = False
                    self.movingRight = False
                    for i in range(1, BOARDHEIGHT):
                        if not isValidPosition(self.board, self.fallingPiece, adjY=i):
                            break
                    self.fallingPiece['y'] += i - 1
                    if isValidPosition(self.board, self.fallingPiece, adjY=1):
                        self.fallingPiece['y'] += 1
                    addToBoard(self.board, self.fallingPiece)
                    self.scoreChange, self.linesChange = updateScore(self.board, self.level)
                    self.score -= 1
                    self.score += self.scoreChange

                    if(self.scoreChange > 0):
                        print("STEP COST: ", self.scoreChange-1, " => One block (-1) + ", self.linesChange , " Lines cleared (+10 each)")
                    else:
                        print("STEP COST: ", -1, " => One block (-1)")
                    self.lines += self.linesChange
                    self.level, self.fallFreq = calculateLevelAndFallFreq(self.lines)
                    self.fallingPiece = None

            if self.movingRight:
                if isValidPosition(self.board, self.fallingPiece, adjX=1):
                    self.fallingPiece['x'] += 1
                if isValidPosition(self.board, self.fallingPiece, adjY=1):
                    self.fallingPiece['y'] += 1
                else:
                    # falling piece has landed, set it on the board
                    addToBoard(self.board, self.fallingPiece)
                    self.score += removeCompleteLines(self.board)
                    self.level, self.fallFreq = calculateLevelAndFallFreq(self.score)
                    self.fallingPiece = None
            if self.movingLeft:
                if isValidPosition(self.board, self.fallingPiece, adjX=-1):
                    self.fallingPiece['x'] -= 1
                if isValidPosition(self.board, self.fallingPiece, adjY=1):
                    self.fallingPiece['y'] += 1
                else:
                    # falling piece has landed, set it on the board
                    addToBoard(self.board, self.fallingPiece)
                    self.score += removeCompleteLines(self.board)
                    self.level, self.fallFreq = calculateLevelAndFallFreq(self.score)
                    self.fallingPiece = None

            # Manual controls mode
            self.movingDown = False
            self.movingLeft = False
            self.movingRight = False

            # drawing everything on the screen
            fillBG()
            drawBoard(self.board)
            drawStatus(self.score, self.lines, self.level, brain)
            drawNextPiece(self.nextPiece)
            if self.fallingPiece != None:
                drawPiece(self.fallingPiece)
            updateDisplay()


def main():
    initPygame()
    game = Game()
    showTextScreen('Tetromino')
    while True: # game loop
        score = game.runGame()
        #print("Score:",score)
        showTextScreen('Game Over')

if __name__ == '__main__':
    main()
