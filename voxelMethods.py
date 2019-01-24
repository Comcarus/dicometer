import numpy as np

# Pixel spacing, Image Position, Image Orientation
def getMatrix(ps, ip, io):
    return np.array([
        [io[0] * ps[0], io[3] * ps[1], 0, ip[0]],
        [io[1] * ps[0], io[4] * ps[1], 0, ip[1]],
        [io[2] * ps[0], io[5] * ps[1], 0, ip[2]],
        [0, 0, 0, 1]
    ]).T

def getVoxelPosition(voxel, ps, ip, io):
    mat = getMatrix(ps, ip, io)
    voxelMatrix = np.array([[voxel[0], voxel[1], 0, 1]])
    coords = np.array(voxelMatrix @ mat)
    return coords[0][0], coords[0][1], coords[0][2]