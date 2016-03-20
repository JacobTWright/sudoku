import numpy as np


#Plan of attack: accept gameboard as numpy array.
#Object will contain gameboard as numpy array, plus dictionary of options
#Index of options dict will be (row,col) index of a given square in the gameboard
#Solved squares set to None.
#Function to add new number (set to current value for square, remove from possiblity in other squares)
#Function to pretty print gameboard for CLI viewing?


class Board(object):
    def __init__(self, grid):
        """
        For now pass a numpy array describing the gameboard in the default input (9x9).
        In the future make the default have no board data, but give the option to generate a random board,
        generate from a string (123...48......2.), you get the idea.
        """
        if type(grid)==str:
            grid=np.load(grid)['board']
        self.__board=np.zeros((9,9),np.uint8)
        self.__poss=np.ones((9,9,9),np.bool) #use 3D array to hold possible numbers 
        self.__batchUpdate(grid)

    def saveBoard(self,fname):
        np.savez(fname,board=self.__board)

    def __batchUpdate(self,grid):
        """
        Function to update the game board with a series of values.  Accepts numpy arrays as inputs.
        """
        y,x=np.nonzero(grid)
        locations=zip(y,x)
        for location in locations:
            self.updateBoard(location,grid[location])
        pass

    def __checkPossible(self,location):
        row, col = location
        return np.nonzero(self.__poss[:,row,col])[0]

    def updateBoard(self, location, value):
        """
        Internal function to update board and related possibilities after new value is plotted.
        """
        #First and foremost, plot the number requested in the appropriate value
        row, col = location
        self.__board[row,col]=value

        #Now the easy part: update the row/column possibilities
        self.__poss[value-1,row,:]=0
        self.__poss[value-1,:,col]=0

        #Now for the slightly more tedious part, updating squares
        cellrow=int(row/3)*3
        cellcol=int(col/3)*3
        self.__poss[value-1,cellrow:cellrow+3,cellcol:cellcol+3]=0

        #Finally, leave no other possibilities on current location.
        self.__poss[:,row,col]=0

    def printBoard(self):
        """
        Prints a pretty view of the board to stdout.
        """
        for row in range(9):
            if not row%3: print '#'*22
            string=''
            for col in range(9):
                if not col%3: string+='#'
                string+=str(self.__board[row,col])+' '
            string+='#'
            print string
        print '#'*22

    def getBoard(self):
        return np.array(self.__board,np.uint8)

    def simpleSolve(self):
        """Simplest solving method, brute force.  Returns True if solved successfully, false if not."""
        #this will always return false.  this is a terrible strategy.
        #TODO: add 'by cell' checks. Currently there is no deductive reasoning strategy.
        while True:
            updated=False
            for i in range(9):
                for j in range(9):
                    locs=self.__checkPossible((i,j))
                    if len(locs)==1:
                        self.updateBoard((i,j),locs[0]+1)
                        updated=True
            if np.sum(self.__board)==405:
                return True
            if not updated:
                return False




if __name__=='__main__':
    print 'this is example code to add to get repo.'
