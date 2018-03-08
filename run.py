# Date: 2018-02-25
# Author: Robby Costales

# Purpose: Contains all of the main solving algorithms

import sys
import random
import time
import copy
import pickle
from statistics import median
import matplotlib.pyplot as plt
# local
from createWD import *
from misc import *
from heuristics import *
# profiling
import cProfile
# queue stuff
from queue import PriorityQueue
import heapq as hq



def neighbors(state):
    """
    Finds neighbors of an S15 state

    Args:
        state : 1d python list representation of S15
    Returns:
        list : list of neighbors (where each neighbor in given state format)
    """
    neighborhood = []

    # find blank position

    try:
        i = state.index(16)
    except:
        i = state.index(0)
        state[i] = 16

    # move blank left?
    if i % 4 != 0:
        newState = state[:i-1] + [state[i],state[i-1]] + state[i+1:]
        neighborhood.append(newState)

    # move blank right?
    if i % 4 != 3:
        newState = state[:i] + [state[i+1],state[i]] + state[i+2:]
        neighborhood.append(newState)

    # move blank up?
    if i > 3:
        newState = state[:i-4] + [state[i]] + state[i-3:i] + [state[i-4]] + state[i+1:]
        neighborhood.append(newState)

    # move blank down?
    if i < 12:
        newState = state[:i] + [state[i+4]] + state[i+1:i+4] + [state[i]] + state[i+5:]
        neighborhood.append(newState)

    return neighborhood


def print15(state):
    """
    Pretty prints given S15 state

    Args:
        state : 1d python list representation of S15
    """
    for row in range(4):
        for col in range(4):
            if state[4*row+col] < 10:
                    sys.stdout.write(" ")
            sys.stdout.write(str(state[4*row+col]))
            sys.stdout.write("\t")
        print("")
    return


def print15s(path):
    """
    Pretty prints path (or list) of S15 states

    Args:
        state : list of 1d python list representations of S15
    """
    for i, state in enumerate(path):
        print("step " + str(i))
        print15(state)
        print("")


# this function would be in misc except for explicit use of neighbors function
def scrambler(state, n):
    """
    Scrambles an S15 puzzle state (easier to solve than random)

    Args:
        state :  list of 1d python list representations of S15
        n : number of scrambles (actual distance away will vary)
    Returns:
        scrambled state
    """
    sExplored = {}
    try:
        for step in range(n):
            neighborList = neighbors(state)

            # # don't regenerate previously generated states
            newNeighbors = []
            for i in neighborList:
                boo, rank = stateInDict(i, sExplored)
                if not boo:
                    newNeighbors.append(i)
            neighborList = newNeighbors

            num = len(neighborList)
            nextNeighbor = neighborList[random.randint(0, num-1)]
            state = nextNeighbor

            boo, rank = stateInDict(state, sExplored)
            sExplored[rank] = 1
    except:
        scrambler(state, n)
    return state


def AStar(S, neighborhoodFn, goalFn, visitFn, heuristicFn):
    """
    Searches for goal node for S15 given initial set of states
    Uses AStar search

    Args:
        S : list of starting state(s)
        neighborhoodFn : function that finds neighbors of a given state
        goalFn : tests if a state is a goal or not
        visitFn : visits a given path
        heuristicFn : heuristic for AStar search
    Returns:
        runTime, path

        If something goes wrong, returns: -1, None
    """
    global maxTime
    startTime = time.time()

    frontier = PriorityQueue()

    for s in S:
        frontier.put((0, [s]))
        explored[rankPerm(s)] = 1

    while frontier.qsize() > 0:
        (_, path) = frontier.get()
        node = path[-1]

        # check time
        currentTime = time.time()
        if currentTime - startTime > maxTime:
            return [-1, None]

        if goalFn(node):
            visitFn(path)
            currentTime = time.time()
            return [currentTime - startTime, path]
        else:
            neighborhood = neighborhoodFn(node)
            for neighbor in neighborhood:
                boo, rank = stateInDict(neighbor, explored)
                if not boo:
                    explored[rank] = 1
                    newPath = path + [neighbor]
                    pastCost = len(newPath)-1
                    futureCost = heuristicFn(neighbor)
                    totalCost = pastCost + futureCost
                    frontier.put((totalCost, newPath))

    return [-1, None]


# function here because needs dictionaries
def chooseWDDict(state, ori="vert"):
    """
    Given a state, which walking distance type should be used?

    The og goal state has diagonals 4, 4, 4, 3
    However, possible starting states can have all other permuations.

    Type 1: 3, 4, 4, 4
    Type 2: 4, 3, 4, 4
    Type 3: 4, 4, 3, 4
    Type 4: 4, 4, 4, 3

    Args:
        state: S15 puzzle in 1-d python list format
    Returns:
        the dictionary that should be used for the given type
    """
    state = unFlatten(state)
    if ori == "horiz":
        state = transpose(state)
    # no need to transpose, vertical MEANS ROWS!!!! not columns
    # this is confusing af
    # state = fu.transpose(state)
    for i in range(4):
        if 16 in state[i] or 0 in state[i]:
            typ = i+1
            break

    if typ == 1:
        return vertWDRanks1
    elif typ == 2:
        return vertWDRanks2
    elif typ == 3:
        return vertWDRanks3
    elif typ == 4:
        return vertWDRanks4
    else:
        return -1


# function here because we need the dictionaries
def heuristicWD(state, goal=None, typ=4):
    """
    Given a state, what is the walking distance heuristic value?

    Args:
        state : 1-d python representation of S15 state
        goal (optional): if typical goal, let it equal to None
    Returns:
        heuristic (int)
    """

    if goal==None:
        goal = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]

    # try:
    #     vertWDRanks = chooseWDDict(goal, ori="vert")
    #     vertRank = convertWD(state, goal, "vert")
    #     x = vertWDRanks[vertRank]
    # except:
    #     # try other orientation
    #     raise
    #     print("vert error in heuristicWD")
    #     x = 35
    vertWDRanks = chooseWDDict(goal, ori="vert")
    vertRank = convertWD(state, goal, "vert")
    x = vertWDRanks[vertRank]

    # try:
    #     vertWDRanks = chooseWDDict(goal, ori="horiz")
    #     horizRank = convertWD(state, goal, "horiz")
    #     y = vertWDRanks[horizRank]
    # except:
    #     # try other orientation
    #     raise
    #     print("horiz error in heuristicWD")
    #     y = 35

    vertWDRanks = chooseWDDict(goal, ori="horiz")
    horizRank = convertWD(state, goal, "horiz")
    y = vertWDRanks[horizRank]

    return x+y


def bidirectional(S, G, neighborhoodFn, goalFn, visitFn, heuristicFn):
    """
    Searches for goal node for S15 given initial set of states
    Uses bidirectional search

    Args:
        S : list of starting state(s)
        G : list of goal state(s)
        neighborhoodFn : function that finds neighbors of a given state
        goalFn : tests if a state is a goal or not
        visitFn : visits a given path
        heuristicFn : heuristic--should be able to use custom goal state
    Returns:
        runTime, path

        If something goes wrong, returns: -1, None
    """
    global maxTime
    global pastCostConst
    global exploredTo
    global exploredFrom
    global explored

    exploredTo = {}
    explored = {}
    exploredFrom = {}

    startTime = time.time()

    fConst = pastCostConst
    bBound = BRANCH_BOUND

    # # using PQ
    # # paths to goal state
    # frontierTo = PriorityQueue()
    #
    # # paths from goal state
    # frontierFrom = PriorityQueue()

    frontierTo = []

    frontierFrom = []

    # put initial state's path in TO queue
    for s in S:
        # frontierTo.put((0, [s]))
        hq.heappush(frontierTo, (0, [s]))
        exploredTo[rankPerm(s)] = 1

    # put initial state's path in TO queue
    for g in G:
        # frontierFrom.put((0, [g]))
        hq.heappush(frontierFrom, (0, [g]))
        exploredFrom[rankPerm(g)] = 1


    count = 0
    # while frontierFrom.qsize() > 0 and frontierTo.qsize() > 0:
    while len(frontierFrom) > 0 and len(frontierTo) > 0:
        # print(frontierTo.qsize(), frontierFrom.qsize(), end="\r")
        count += 1
        # check time
        currentTime = time.time()
        if currentTime - startTime > maxTime:
            return [-1, None]

        ### TO ------->>>>>
        # pull from TO queue
        # (val, path) = frontierTo.get()
        (val, path) = hq.heappop(frontierTo)


        node = path[-1]

        # check if node in other dictionary
        boo, rank = stateInDict(node, exploredFrom)
        if boo:
            # have our final pathTo
            pathTo = path
            # find the pathFrom that has this overlapping node
            # while frontierFrom.qsize() > 0:
            while len(frontierFrom) > 0:
                # (_, pathCheck) = frontierFrom.get()
                (_, pathCheck) = hq.heappop(frontierFrom)
                for i in range(len(pathCheck)):
                    if rank == rankPerm(pathCheck[i]):
                        # we found our pathFrom
                        pathFrom = pathCheck
                        # need to merge these paths on i (i cant appear in both)
                        finalPath = pathTo + pathFrom[i+1::-1]
                        visitFn(finalPath)
                        currentTime = time.time()
                        return [currentTime - startTime, finalPath]
        else:
            neighborhood = neighborhoodFn(node)
            for neighbor in neighborhood:
                boo, rank = stateInDict(neighbor, exploredTo)
                if not boo:
                    exploredTo[rank] = 1
                    newPath = path + [neighbor]
                    pastCost = (len(newPath)-1)//fConst
                    futureCost = heuristicFn(neighbor, goal=None)
                    totalCost = pastCost + futureCost
                    if len(newPath) < bBound:
                        # frontierTo.put((totalCost, newPath))
                        hq.heappush(frontierTo, (totalCost, newPath))

        ### <<<<<------- FROM
        # pull from FROM queue
        if count % fromConst == 0:
            # (val, path) = frontierFrom.get()
            (val, path) = hq.heappop(frontierFrom)
            node = path[-1]

            # check if node in other dictionary
            boo, rank = stateInDict(node, exploredTo)
            if boo:
                # have our final pathFrom
                pathFrom = path
                # find the pathTo that has this overlapping node
                # while frontierTo.qsize() > 0:
                while len(frontierTo) > 0:
                    # (_, pathCheck) = frontierTo.get()
                    (_, pathCheck) = hq.heappop(frontierTo)
                    for i in range(len(pathCheck)):
                        if rank == rankPerm(pathCheck[i]):
                            # we found our pathTo
                            pathTo = pathCheck
                            # need to merge these paths on i (i cant appear in both)
                            finalPath = pathTo[:i] + pathFrom[::-1]
                            visitFn(finalPath)
                            currentTime = time.time()
                            return [currentTime - startTime, finalPath]
            else:
                neighborhood = neighborhoodFn(node)
                for neighbor in neighborhood:
                    boo, rank = stateInDict(neighbor, exploredFrom)
                    if not boo:
                        exploredFrom[rank] = 1
                        newPath = path + [neighbor]
                        pastCost = (len(newPath)-1)//fConst
                        futureCost = heuristicFn(neighbor, goal=S[0])
                        totalCost = pastCost + futureCost
                        if len(newPath) < bBound:
                            hq.heappush(frontierFrom, (totalCost, newPath))
                            # frontierFrom.put((totalCost, newPath))

    print("function ended error")
    return [-1, None]


if __name__ == "__main__":
    global totalTime
    global maxTime

    # for all 4 tables (look at chooseWDDict for more info)
    global vertWDRanks1
    global vertWDRanks2
    global vertWDRanks3
    global vertWDRanks4

    # for A* search
    global explored
    # for bidirectional search:
    global exploredTo
    global exploredFrom

    # types of tests
    t = ["test", "single", "profile", "sandbox"]

    ###########################################################################
    ###########################################################################
    # NOTE: basic parameters
    RANDOM = True
    numScrambles = 1000 # scrambles
    TYPE = t[0] # type
    numTests = 100 # tests
    maxTime = 100 # seconds
    global BRANCH_BOUND
    global pastCostConst
    global fromConst
    BRANCH_BOUND = 81 # cost
    pastCostConst = 1
    fromConst = 1

    ###########################################################################
    ###########################################################################

    # instantiate other things
    global GOAL_STATE
    GOAL_STATE = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]

    # load tables from pickle
    # print("Loading TABLES from pickle...")
    pic_begin = time.time()
    pickle_in = open("TABLES","rb")
    TABLES = pickle.load(pickle_in)
    pic_end = time.time()
    vertWDRanks1 = TABLES[0]
    vertWDRanks2 = TABLES[1]
    vertWDRanks3 = TABLES[2]
    vertWDRanks4 = TABLES[3]
    # print("Process time: " + str(pic_end-pic_begin) + "\n")


    print("\nConstant with which to divide pastCost: {}\n".format(pastCostConst))
    # how much to divide the past cost by in biD search

    # totalEnd = totalStart is total time for entire program
    totalStart = time.time()
    #######################################################################
    if TYPE=="test":
        # like: 5, 30, 100, failed
        timez = [[], [], [], []]
        # stats for end (only for solved states)
        numCorrect = 0
        solvedTimes = []
        pathLengths = []

        for i in range(numTests):
            if i == 0:
                perc = 100
            else:
                perc = (numCorrect / i)*100
            print("running test {} / {}   ({} / {} found so far... {}%)".format(str(i+1), str(numTests), str(numCorrect), str(i), perc))

            # Make a random state.
            state = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]
            goal = copy.deepcopy(state)

            if RANDOM:
                # print("creating random state")
                random.shuffle(state)
                while not isSolvable(state):
                    random.shuffle(state)
            else:
                state = scrambler(state, numScrambles)
                # print("created "+ str(n) +"-scrambled state")

            print15(state)
            print("has rank " + str(rankPerm(state)))
            # [runTime, path] = AStar([state], neighbors, isGoal, doNothing, heuristicWD)
            [runTime, path] = bidirectional([state], [goal], neighbors, isGoal, doNothing, heuristicWD)
            # add general statistics
            if path != None:
                pathLengths.append(len(path))
                solvedTimes.append(runTime)
                numCorrect += 1
                print("Path Length: {} ".format(len(path)))

            # add things to timez
            if runTime < 0:
                timez[3].append(runTime)
            if 0 < runTime <=5:
                timez[0].append(runTime)
            if 5 < runTime <=30:
                timez[1].append(runTime)
            if 30 < runTime <= maxTime + 20:
                timez[2].append(runTime)
            print("Run Time : {}".format(runTime))

        print("\nNum Unsolved: {}\n".format(len(timez[3])))
        print("Num Under 5 secs: ", len(timez[0]))
        print("Num Under 30 secs: ", len(timez[0]) + len(timez[1]))
        print("Num Under 100 secs: ", len(timez[0]) + len(timez[1]) + len(timez[2]))

        if len(pathLengths) > 0:
            print("\nMedian path length: {}".format(median(pathLengths)))

        totalEnd = time.time()
        print("\nTotal Time: {}".format(totalEnd - totalStart))

        print(solvedTimes)

        n, bins, patches = plt.hist(solvedTimes, 20, color="pink")
        plt.xlabel('Solve Times')
        plt.ylabel('Frequences')
        plt.title('Frequency of Solve Times')
        plt.grid(True)
        plt.show()

        n, bins, patches = plt.hist(pathLengths, 20, color="blue")
        plt.xlabel('Path Lengths')
        plt.ylabel('Frequences')
        plt.title('Frequency of Path Lengths')
        plt.grid(True)
        plt.show()

    #######################################################################
    elif TYPE=="single":
        exploredTo = {}
        explored = {}
        exploredFrom = {}
        # Make a random state.
        state = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]
        goal = copy.deepcopy(state)

        if RANDOM:
            random.shuffle(state)
            while not isSolvable(state):
                random.shuffle(state)
        else:
            state = scrambler(state, numScrambles)

        print15(state)
        print("has rank " + str(rankPerm(state)))

        # [runTime, path] = AStar([state], neighbors, isGoal, doNothing, heuristicWD)
        [runTime, path] = bidirectional([state], [goal], neighbors, isGoal, doNothing, heuristicWD)

        print15s(path)
        print("runTime: ", runTime)

    #######################################################################
    elif TYPE=="profile":
        print("TYPE = Profile")

        exploredTo = {}
        explored = {}
        exploredFrom = {}
        # Make a random state.
        state = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]
        goal = copy.deepcopy(state)

        if RANDOM:
            # print("creating random state")
            random.shuffle(state)
            while not isSolvable(state):
                random.shuffle(state)
        else:
            state = scrambler(state, numScrambles)
            # print("created "+ str(n) +"-scrambled state")

        print("starting profile...")
        cProfile.run("bidirectional([state], [goal], neighbors, isGoal, doNothing, heuristicWD)")

    #######################################################################
    elif TYPE=="sandbox":
        print("TYPE = Sandbox")

        x = [4, 10, 1, 8, 12, 16, 7, 2, 6, 13, 15, 11, 5, 9, 14, 3]
        y = [1, 7, 4, 8, 6, 3, 11, 2, 5, 13, 12, 15, 10, 9, 16, 14]

        z = heuristicWD(x, goal = y)

        print(z)


        z = heuristicWD(y, goal = x)

        print(z)

    else:
        print("RUN TYPE ERROR")
