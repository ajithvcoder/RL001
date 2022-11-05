from collections import deque
from gym import Env, spaces
import cv2 as cv
import numpy as np
import copy

def birdBody(arr, img):
    cv.rectangle(img, arr, arr, (255,255,255), 5)
    return img

def dtCollisionBoundaries(arr):
    if (arr[0] <= 45):
        return True
    if (arr[1] <= 75) or (arr[1] >= 475):
        return True
    return False

def dtDestination(arr):
    if (arr[0] >= 835):
        return True
    return False

def getDisplay(arr):
    img = np.zeros((512, 900, 3), dtype="uint8")
    img = birdBody(arr, img)
    boundaryPts = np.array([[40, 70], [40, 470],
                    [840, 470], [840, 70]],
                np.int32)
    boundaryPts = boundaryPts.reshape((-1, 1, 2))

    destPts = np.array([[840, 470], [840, 70]],
                np.int32)
    destPts = destPts.reshape((-1, 1, 2))

    hindPts1 = np.array([[194, 474], [194, 304]],
                np.int32)
    hindPts1 = hindPts1.reshape((-1, 1, 2))

    hindPts2 = np.array([[408, 474], [408, 304]],
                np.int32)
    hindPts2 = hindPts2.reshape((-1, 1, 2))

    hindPts3 = np.array([[682, 474], [682, 304]],
                np.int32)
    hindPts3 = hindPts3.reshape((-1, 1, 2))

    hindPts4 = np.array([[281, 69], [281, 231]],
                np.int32)
    hindPts4 = hindPts4.reshape((-1, 1, 2))

    hindPts5 = np.array([[541, 69], [541, 231]],
                np.int32)
    hindPts5 = hindPts5.reshape((-1, 1, 2))

    isClosed = True
    thickness = 8
    img = cv.polylines(img, [boundaryPts],
                        isClosed, (0, 255, 0),
                        thickness)
    img = cv.polylines(img, [destPts],
                        isClosed, (0, 0, 255),
                        thickness)
    img = cv.polylines(img, [hindPts1],
                        isClosed, (120, 120, 0),
                        thickness)
    img = cv.polylines(img, [hindPts2],
                        isClosed, (120, 120, 0),
                        thickness)
    img = cv.polylines(img, [hindPts3],
                        isClosed, (120, 120, 0),
                        thickness)
    img = cv.polylines(img, [hindPts4],
                    isClosed, (120, 120, 0),
                    thickness)
    img = cv.polylines(img, [hindPts5],
                    isClosed, (120, 120, 0),
                    thickness)
    return img

def collisionWithHind(arr):
    #[194, 474], [194, 304]
    if (190 <= arr[0] <= 199) and (304 <= arr[1] <= 474):
        return True

    #[408, 474], [408, 304]
    if ((408-5) <= arr[0] <= (408+5)) and (304 <= arr[1] <= 474):
        return True

    #[682, 474], [682, 304]
    if ((682-5) <= arr[0] <= (682+5)) and (304 <= arr[1] <= 474):
        return True
    #[281, 69], [281, 231]
    if ((281-5) <= arr[0] <= (281+5)) and (69 <= arr[1] <= 231):
        return True

    #[541, 69], [541, 231]
    if ((541-5) <= arr[0] <= (541+5)) and (69 <= arr[1] <= 231):
        return True
    return False
BUFFER_MEMORY = 4
XDIM = 64
YDIM = 64
# TODO: Form a frame as its not able to fetch frames at boundaries
class BirdEnv(Env):
    """Bird Environment that follows gym interface"""

    def __init__(self):
        super(BirdEnv, self).__init__()
        # Define action and observation space
        # Using discrete action
        self.action_space = spaces.Discrete(6)
        self.observation_space = spaces.Box(low=0, high=255, shape=(XDIM,YDIM,3*BUFFER_MEMORY), dtype=np.uint8)

    def step(self, action):
        cv.imshow("The Bird Dot game", self.img)
        self.key = action
        previousArr = copy.deepcopy(self.dot)

        # Actions possible
        if self.key == 0:
            self.dot[0] = self.dot[0] - 10
        elif self.key == 1:
            self.dot[0] = self.dot[0] + 10
        elif self.key == 2:
            self.dot[1] = self.dot[1] - 10
        elif self.key == 3:
            self.dot[1] = self.dot[1] + 10
        elif self.key == 4:
            self.dot[0] = self.dot[0] + 10
            self.dot[1] = self.dot[1] - 10
        elif self.key == 5:
            self.dot[0] = self.dot[0] + 10
            self.dot[1] = self.dot[1] + 10

        # detect collision with boudaries
        if dtCollisionBoundaries(self.dot) == True:
            self.done = True
            print("collision with boundaries")

        collisionHind = False
        if collisionWithHind(self.dot) == True:
            self.done = True
            collisionHind = True
            print("Collided with hinderance")
        # check if dest is reached
        destReached = False
        if dtDestination(self.dot) == True:
            self.score += 1
            destReached = True
            self.done = True
            print("Destination reached")

        self.img = getDisplay(self.dot)
        cv.waitKey(150)

        # Using distance parameters and awarding reward
        # distance between a line and point
        # d = norm(np.cross(p2-p1, p1-p3))/norm(p2-p1)
        currDistToDest = np.linalg.norm(
            np.cross( (self.destPts[1]-self.destPts[0]),(self.destPts[1]-np.array(self.dot) ) )
            )/ np.linalg.norm(self.destPts[1] - self.destPts[0])

        prevDistToDest = np.linalg.norm(
            np.cross( (self.destPts[1]-self.destPts[0]),(self.destPts[1]-np.array(previousArr) ) )
            )/ np.linalg.norm(self.destPts[1] - self.destPts[0])

        if self.done and (destReached==False):
            # For colliding with boundaries
            self.reward -= 40
        elif self.done and destReached:
            # Fetching current food
            self.reward += (self.score * 1000)
        elif currDistToDest < prevDistToDest:
            # staying alive and moving towards from food
            self.reward += 2
        else:
            # staying alive and moving away from food
            self.reward -= 1
        print("#######Reward########", self.reward)
        # head_x, heady_y, dest_delta_x, dest_delta_y, previous_moves
        self.destPts = np.array([[840, 470], [840, 70]],
                np.int32)
        self.previousFrames = self.previousFrames[:, :, 3:] #poping first frame
        currFrame = self.img[(self.dot[1]-32): (self.dot[1]+32), (self.dot[0]-32): (self.dot[0] + 32)]
        # cv.imshow("The frame ", currFrame)
        # cv.waitKey(0)
        self.previousFrames = np.dstack((self.previousFrames, currFrame))
        self.observation = self.previousFrames
        # cv.imshow("The frame ", self.observation[:,:, :3])
        # cv.waitKey(0)
        info = {}
        return self.observation, self.reward, self.done, info

    def reset(self):
        self.done = False
        self.initalize = [[141, 138], [304, 287], [59,268], [655, 289],[516, 356]]
        self.dot =  self.initalize[np.random.randint(5)]
        self.img = getDisplay(self.dot)

        self.score = 0
        self.reward = 0
        self.key = 1 # default key right

        # observation
        self.destPts = np.array([[840, 470], [840, 70]],
                np.int32)
        self.previousFrames = np.zeros((XDIM, YDIM, 3),dtype=np.uint8)
        b = np.zeros((XDIM, YDIM, 3),dtype=np.uint8)

        for _ in range(BUFFER_MEMORY-1):
            self.previousFrames = np.dstack((self.previousFrames, b))
        self.observation = self.previousFrames
        return self.observation