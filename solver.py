import numpy as np
import time


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
        self.__board=np.zeros((9,9),np.uint8)
        self.__poss=np.ones((9,9,9),np.bool) #use 3D array to hold possible numbers 
        self.__batchUpdate(grid)
        self.count=0

    @classmethod
    def load(cls, filename):
        """Method to create board from previously saved boards."""
        grid=np.load(filename)['board']
        return cls(grid)

    @classmethod
    def fromMaskedStrings(cls, solution, mask):
        """Method to create puzzle from a pair of strings, one for solution and one for mask."""
        assert len(solution)==len(mask), 'Length of solution and mask are not the same!'
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

    def __checkPossibleCell(self,grid):
        y,x=np.nonzero(grid)
        locations=zip(y,x)
        return locations

    def __checkPossibleRC(self,grid):
        return np.nonzero(grid)[0]


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

    def getPoss(self):
        return np.array(self.__poss,np.bool)

    def checkValid(self):
        """Make sure the solution is valid."""
        #it better be.
        #make sure every row has one of each val.
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
        """Guaranteed to solve the game because it will guess!"""
        start=time.time()
        solved=self.simpleSolve()
        if not solved:
            #recursive guessing!
            self.__guess(self.__board,self.__poss)
        #whoo! we are solved.
        if self.checkValid():
            print 'Solved in {0:.3f} seconds!'.format(time.time()-start)
            self.printBoard()
        else:
            print 'Aww man!'

    def randSolve(self):
        self.__board=np.zeros((9,9),np.uint8)
        self.__poss=np.ones((9,9,9),np.bool)
        self.solve()

    def __guess(self,board,poss):
        """
        Doing a depth search guessing algorithm.  Guess, try and solve, guess more.  If impossible, return false.
        """
        #First, identify lowest risk area.
        board=np.array(board,np.uint8)
        poss=np.array(poss,np.uint8)
        p=np.sum(poss,axis=0)
        if not np.sum(p) == 0:
            p[p==0]=255
            y,x=np.nonzero(p==np.min(p))
            zipped=zip(y,x)
            for option in zipped:
                vals=np.nonzero(self.__poss[:,option[0],option[1]])[0]+1
                np.random.shuffle(vals)
                for val in vals: 
                    self.updateBoard(option,val) 
                    if self.simpleSolve():
                        return True
                    #if we are here it isn't solved yet
                    #try another guess.
                    if self.__guess(self.__board,self.__poss):
                        return True
                    #if we are here, reset the board.
                    self.__board=board
                    self.__poss=poss

                    
        elif np.sum(board) == 405:
            return True
        self.__board=board #return to how we found it!
        self.__poss=poss
        return False


    def __pairExclusion(self):
        """Method to reduce possibilities by induction.  Expensive, so called only when needed.
        This catches the standard 'swordfish' and 'xwing' solving techniques.
        I'm retiring this in favor of simple exclusion as it catches all cases.
        This is easier for people to find, __simpleExclusion is more efficient.  And shorter.
        """
        
        _='' #keep indentation in correct place.
        #do first by rows.
        #look for rows with two and only two possibilities for a given number.
        for plane in range(9):
            roi={} #rows of interest.  get it? like region of interest?
            for row in range(9):
                possible=self.__checkPossibleRC(self.__poss[plane,row,:])
                if len(possible)==2:
                    roi[row]=possible #store the columns for later.
            #now we have to actually do something with that data...
            #for each value in each row, check to see if they have anything in common with
            #another value from another row.  
            #this is guaranteed to be 2x2, implement a checkCommon function for this?
            for key in roi.keys():
                p1 = (key,roi[key][0])
                p2 = (key,roi[key][1])
                for key2 in roi.keys():
                    if not key==key2:
                        p3=(key2,roi[key2][0])
                        p4=(key2,roi[key2][1])
                        self.__checkCommon([p1,p2],[p3,p4],plane)
                        #TODO: Implement checkCommon.  This should compare the point sets and tell me
                        #if there is any commonality between the two sets and if so, what.
                        #e.g. p1,p3 share column 0, p2,p4 share cell 3.  I guess best case scenario
                        #would be a double share (p2,p4 share cell 3, column 8) then we can reduce the possibility
                        #from every other spot in cell3 and every other spot in column 8.

    def __simpleExclusion(self):
        """Simpler form of exclusion testing.  Reduces possibilities for a given number set."""
        #Basic idea: look at cells to see possibilities for a given number.  If they fall in the same row/col
        #Then elemenate the number from possibility for the rest of the rows/cols.
        
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
                        if np.all(x==x[0]):
                            if not len(np.nonzero(self.__poss[plane,:,col+x[0]])[0]) == len(x):
                                #if we made it here everything was in the same column.
                                #set all other states to 0 (can't happen)
                                self.__poss[plane,:,col+x[0]]=False
                                self.__poss[plane,row:row+3,col:col+3][y,x]=True #and reset our remaining values
                                reduced=True
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
        #e.g. col needs value, all possible locations are in one cell, remove other possibilities in that cell
        return reduced
                            






    def simpleSolve(self):
        """Simplest solving method, brute force.  Returns True if solved successfully, false if not."""
        #this will always return false.  this is a terrible strategy.
        #TODO: add 'by cell' checks. Currently there is no deductive reasoning strategy.
        self.count+=1
        while True:
            updated=False
            for i in range(9):
                for j in range(9):
                    locs=self.__checkPossible((i,j))
                    if len(locs)==1:
                        self.updateBoard((i,j),locs[0]+1)
                        updated=True

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

            if np.sum(self.__board)==405:
                return True
            if not updated:
                if not self.__simpleExclusion():
                    return False

if __name__=='__main__':
    print 'this is example code to add to git repo.'
