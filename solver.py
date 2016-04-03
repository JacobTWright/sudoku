import numpy as np
import time, os


#Plan of attack: accept gameboard as numpy array.
#Object will contain gameboard as numpy array, plus dictionary of options
#Index of options dict will be (row,col) index of a given square in the gameboard
#Solved squares set to None.
#Function to add new number (set to current value for square, remove from possiblity in other squares)
#Function to pretty print gameboard for CLI viewing?


class Board(object):
    def __init__(self, grid):
        """
        General object for holding and solving a sudoku puzzle.

        For now pass a numpy array describing the gameboard in the default input (9x9, 0 for unsolved).
        """
        self.__board=np.zeros((9,9),np.uint8)
        self.__poss=np.ones((9,9,9),np.bool) #use 3D array to hold possible numbers 
        self.__batchUpdate(grid)
        self.count=0

    @classmethod
    def load(cls, filename):
        """Method to load a board from previously saved boards, pass path to board."""
        grid=np.load(filename)['board']
        return cls(grid)

    @classmethod
    def fromMaskedStrings(cls, solution, mask):
        """Method to create puzzle from a pair of strings, one for solution and one for mask.

        This is for ripping off online sudoku puzzles.
            solution should be a series of all numbers in sudoku puzzle in a string
            mask should be a string of 1's and 0's, where 0 is visible and 1's are blank.

        I realize that is backwards but I didn't come up with the format.
        """
        assert len(solution)==len(mask), 'Length of solution ({}) and mask ({}) are not the same!'.format(len(solution),len(mask))

        #I can't in place modify the solution string so I am building a new one.
        output=''
        for i in range(len(solution)):
            if mask[i]=='1': output+='.'
            else: output+=solution[i]
        return cls.fromString(output)           

    @classmethod
    def fromString(cls, string):
        """
        Creates board from 81 character string using . to signify unsolved boxes
        """
        board=np.zeros((9,9),np.uint8)
        for row in range(9):
            for col in range(9):
                if not string[row*9+col]=='.':
                    board[row,col]=int(string[row*9+col])
        return cls(board)

    def saveBoard(self,fname):
        """Saves board as np zipped matrix with your filename."""

        #I should probably warn that I am stripping off any incorrect suffixes.  eh.
        if not os.path.splitext(fname)[1].lower()=='.npz':
            fname=os.path.splitext(fname)[0]+'.npz'
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
        """Returns index of allowable values for a given XY location on board grid as numpy array."""
        row, col = location
        return np.nonzero(self.__poss[:,row,col])[0]

    def __checkPossibleCell(self,grid):
        """Returns index of nonzero values in a cell as a list of tuples."""
        y,x=np.nonzero(grid)
        locations=zip(y,x)
        return locations

    def __checkPossibleRC(self,grid):
        """Returns index of nonzero values in a 1D array as a numpy array."""
        return np.nonzero(grid)[0]


    def updateBoard(self, location, value):
        """
        Function to update board and related possibilities after new value is plotted.
        
        Note that this will not prevent you from making illegal moves!
            location is location on board in [row, col] order
            value is number to be placed in a location.
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

        #Finally, leave no other possibilities on current location to mark it as solved.
        self.__poss[:,row,col]=0

    def printBoard(self):
        """
        Prints a 'pretty' view of the board to stdout.


        I'm a engineer, not a programmer damnit.
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
        """Returns a copy of the game board as numpy array.

        Note that this actually returns a copy of the board, not the same object."""
        return np.array(self.__board,np.uint8)

    def getPoss(self):
        """Returns a copy of the 'possibilities matrix' as  a numpy array"""

        #Possibilities matrix sounds like an album name.
        return np.array(self.__poss,np.bool)

    def checkValid(self):
        """Makes sure the solution is valid.
        
        Returns True if valid, False if not."""

        #it better be.
        #make sure every set has one of each val.
        for number in range(1,10):
            for row in range(9):
                if not np.sum(self.__board[row,:]==number)==1:
                    return False
            for col in range(9):
                if not np.sum(self.__board[row,:]==number)==1:
                    return False
            for row in range(0,9,3):
                for col in range(0,9,3):
                    if not np.sum(self.__board[row:row+3,col:col+3]==number)==1:
                        return False
        return True

    def solve(self):
        """Guaranteed to solve the game because it will guess if it can't figure it out!
        
        returns puzzle board if solved, none if unable to solve possible.
        """
        start=time.time()
        solved=self.simpleSolve()
        if not solved:
            #recursive guessing!
            self.__guess(self.__board,self.__poss)
        #whoo! we are solved.
        if self.checkValid():
            return self.getBoard()
        else:
            return None

    def randSolve(self):
        """Generates a random puzzle and solves it."""
        self.__board=np.zeros((9,9),np.uint8)
        self.__poss=np.ones((9,9,9),np.bool)
        return self.solve()

    def __guess(self,board,poss):
        """Doing a depth search guessing algorithm.  Guess, try and solve, guess more.  If impossible, return false.
        
        Guessing isn't totally dumb, it looks for squares with the lowest possible numbers of options and works from there.
        """
        #First, identify lowest risk area.
        board=np.array(board,np.uint8)
        poss=np.array(poss,np.uint8)
        p=np.sum(poss,axis=0)
        if not np.sum(p) == 0: #Make sure there are still options on the board.
            p[p==0]=255 #Mapp 0 (solved) values to 255 so that we can look for mins
            y,x=np.nonzero(p==np.min(p))
            zipped=zip(y,x)
            #This for loop is deceptive.  It should never iterate more than once in a solvable puzzle.
            for option in zipped:
                #For each option find the  possible values
                vals=np.nonzero(self.__poss[:,option[0],option[1]])[0]+1
                #Shuffle (allows for generation of random boards)
                np.random.shuffle(vals)
                for val in vals: 
                    self.updateBoard(option,val) 
                    if self.simpleSolve():
                        return True
                    #if we are here it isn't solved yet
                    #try another guess.
                    if self.__guess(self.__board,self.__poss):
                        return True
                    #if we are here, reset the board and try a new value.
                    self.__board=board
                    self.__poss=poss

                    
        elif np.sum(board) == 405:
            #We get here because there were no options, if the puzzle is solved return blue
            return True
        self.__board=board #return to how we found it!
        self.__poss=poss
        return False


    def __simpleExclusion(self):
        """Simpler form of exclusion testing.  Reduces possibilities for a given number set."""
        #Basic idea: look at cells to see possibilities for a given number.  If they fall in the same row/col
        #Then eliminate the number from possibility for the rest of the rows/cols.
        
        #Second check: if row or col requires a number and all possibilities are in a given cell,
        #remove that possibility from the rest of the cell. (write 0 to whole cell, add back in 1's where 
        #the row/col possibilities were.

        #Noticing a trend here... everything has to be thought of for cell, row, and column.
        reduced=False
        for plane in range(0,9):
            for row in range(0,9,3):
                for col in range(0,9,3):
                    y,x=np.nonzero(self.__poss[plane,row:row+3,col:col+3])
                    if len(x)>0:
                        #If all values are in a single column, the option from the rest of the column
                        if np.all(x==x[0]):
                            if not len(np.nonzero(self.__poss[plane,:,col+x[0]])[0]) == len(x):
                                #if we made it here everything was in the same column.
                                #set all other states to 0 (can't happen)
                                self.__poss[plane,:,col+x[0]]=False
                                self.__poss[plane,row:row+3,col:col+3][y,x]=True #and reset our remaining values
                                reduced=True
                        #Same for rows
                        if np.all(y==y[0]):
                            if not len(np.nonzero(self.__poss[plane,row+y[0],:])[0]) == len(x):
                                #if we made it here everything was in the same row.
                                #set all other states to 0 (can't happen)
                                self.__poss[plane,row+y[0],:]=False
                                self.__poss[plane,row:row+3,col:col+3][y,x]=True #and reset our remaining values
                                reduced=True

        #Do the same thing by rows
        for plane in range(0,9):
            for row in range(9):
                x=np.nonzero(self.__poss[plane,row,:])[0]
                if len(x)>2:
                    if np.all(x<3) or np.all(x>5) or (np.all(x>3) and np.all(x<6)):
                        #now we convert to cell notation
                        cellx=int(x[0]/3)*3
                        celly=int(row/3)*3
                        if len(np.nonzero(self.__poss[plane,celly:celly+3,cellx:cellx+3])[0]) > len(x):
                            self.__poss[plane,celly:celly+3,cellx:cellx+3]=False
                            self.__poss[plane,row,:][x]=True
                            reduced=True

        #Do the same thing by cols
        for plane in range(0,9):
            for col in range(9):
                y=np.nonzero(self.__poss[plane,:,col])[0]
                if len(y)>2:
                    if np.all(y<3) or np.all(y>5) or (np.all(y>2) and np.all(y<6)):
                        #now we convert to cell notation
                        cellx=int(col/3)*3
                        celly=int(y[0]/3)*3
                        if len(np.nonzero(self.__poss[plane,celly:celly+3,cellx:cellx+3])[0]) > len(y):
                            self.__poss[plane,celly:celly+3,cellx:cellx+3]=False
                            self.__poss[plane,:,col][y]=True
                            reduced=True

        #Return if the function was able to reduce the possibility set
        return reduced
                            






    def simpleSolve(self):
        """Simplest solving method, basic elimination and population.  Returns True if solved successfully, false if not.
        
        Good for 'easy' and 'medium' puzzles
        """
        #self.count+=1
        while True:
            updated=False
            for i in range(9):
                for j in range(9):
                    locs=self.__checkPossible((i,j))
                    if len(locs)==1:
                        self.updateBoard((i,j),locs[0]+1)
                        updated=True


            """
            The next 3 blocks look for the same thing: if a group needs a number, and there is only
            one location in the group that can be that number, set the location to that number
            even if it has other possibilities.
            """
            #Check by cell
            for plane in range(9):
                num=plane+1
                for row in range(0,9,3):
                    for col in range(0,9,3):
                        if not num in self.__board[row:row+3,col:col+3]:
                            possible=self.__checkPossibleCell(self.__poss[plane,row:row+3,col:col+3])
                            if len(possible)==1:
                                self.updateBoard((possible[0][0]+row,possible[0][1]+col),num)
                                updated=True
            
            #Check by row 
            for plane in range(9):
                num=plane+1
                for row in range(0,9):
                    if not num in self.__board[row,:]:
                        possible=self.__checkPossibleRC(self.__poss[plane,row,:])
                        if len(possible)==1:
                            self.updateBoard((row,possible[0]),num)
                            updated=True

            #Check by col
            for plane in range(9):
                num=plane+1
                for col in range(0,9):
                    if not num in self.__board[:,col]:
                        possible=self.__checkPossibleRC(self.__poss[plane,:,col])
                        if len(possible)==1:
                            self.updateBoard((possible[0],col),num)
                            updated=True

            if np.sum(self.__board)==405: #return True if solved
                return True
            if not updated:
                if not self.__simpleExclusion():
                    return False #return False if the puzzle is stuck
