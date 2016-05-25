import numpy as np
import cv2
import math
import random
import json

def vector2mat(vector):
    """
    Converts a vector in form x,y,z,axis-angle to a homogenous transformation
    matrix

    Args:
        vector (6 element list): a vector representation form of a
                                 transformation matrix. x,y,z,axis-angle

    Returns: A 4x4 np.ndarry of the homogenous transformation matrix
    """
    transformation_matrix = np.zeros((4,4))
    transformation_matrix[3, 3] = 1
    try:
        transformation_matrix[0:3, 3] = vector[:3,0]
    except:
        transformation_matrix[0:3, 3] = vector[:3]
    # mag = math.sqrt(math.pow(vector[3],2)+math.pow(vector[4],2)+math.pow(vector[5],2))
    # norm = np.divide(np.array([vector[3],vector[4],vector[5]]), mag)
    rotation_matrix, _ = cv2.Rodrigues(vector[3:])
    transformation_matrix[:3,:3] = rotation_matrix
    return transformation_matrix

def mat2vector(mat):
    """
    Converts a transformatiion matrix into a 6 dof vector. x,y,z,axis-angle
    Args:
        mat (4x4 ndarray): the transformation matrix

    Returns: A 6 element list, x,y,z,axis-angle
    """
    vector = [0]*6
    vector[:3] = np.asarray(mat[:3,3])
    axis_angle, _ = cv2.Rodrigues(mat[:3,:3])
    vector[3:] = axis_angle
    return vector

def error(guess, tcp2robot, camera2grid,intrinsic,distortion,test_points):
    """
    Calculates the difference between a guess at robot 2 cam transformations
    compared to gathered data.

    Args:
        guess (1x12 array): Input guess array. Values will range between the bounds
                            passed in the optimize function. 6 dof camera 2 robot
                            (x,y,z,axis-angle), 6 dof tcp 2 target
                            (x,y,z,axis-angle)
        tcp2robot (nx6 array): Array of gathered data for the pose of the robot
                               tool center point wrt. the robot coordinate base
        camera2grid (nx6 array): Array of gathered data for the transformation
                                 from the camera to the target
        intrinsic (3x3 array): Camera intrinsic matrix

        distortion (1x5 array): Camera distortion parameters

    Returns: A float, the average error between the guess and the collected
             data
    """
    total_error = 0
    # global counter
    # print('error function called')
    # counter += 1
    for i in range(len(tcp2robot)):
        guess_cam2rob = vector2mat(guess[:6])
        guess_tcp2target = vector2mat(guess[6:])
        guess_cam2tcp = np.matmul(guess_cam2rob, vector2mat(np.concatenate((1000*np.array(tcp2robot[i][:3]),np.array(tcp2robot[i][3:])))))
        guess_cam2target = np.matmul(guess_cam2tcp, guess_tcp2target)
        image_points, _ = cv2.projectPoints(test_points, np.array(camera2grid[i][3:6]), np.array(camera2grid[i][0:3]),
                                            intrinsic, distortion)
        guess_cam2target = mat2vector(guess_cam2target)
        guess_points, _ = cv2.projectPoints(test_points, np.array(guess_cam2target[3:6]), np.array(guess_cam2target[0:3]),
                                            intrinsic, distortion)
        #Take distance between projected points as error
        for j in range (image_points.shape[0]):
            total_error += math.sqrt(np.power(image_points[j][0][0] - guess_points[j][0][0], 2) +
                                     np.power(image_points[j][0][1] - guess_points[j][0][1], 2))

        # errorvec = np.array(mat2vector(guess_cam2target))-np.array(camera2grid[i])
        # for j in range(0,len(errorvec)):
        #     total_error+=math.pow(errorvec[j],2)
        # total_error=math.sqrt(total_error)

        # total_error += abs(sum(
        #     np.array(mat2vector(guess_cam2target))-np.array(camera2grid[i])
        # ))

    # return total_error/guess.shape[0]
    return total_error
#test_points = np.array([[10.,20.,30.]])
test_points = np.zeros((30, 3))
for i in range(test_points.shape[0]):
    test_points[i][0] = random.randrange(-50, 50)
    test_points[i][1] = random.randrange(-50, 50)
    test_points[i][2] = random.randrange(-50, 50)
intrinsic = np.matrix([[2462.345193638386, 0.0, 1242.6269086495981],[0.0, 2463.6133832534606, 1014.3609261368764],[0, 0, 1]])
distortion = np.array([-0.3954032063765203, 0.20971494160750948, 0.0008056336338866635, 9.237725225524615e-05, -0.06042030845477194])
correspondences = '../examples/correspondences_may10.json'
# cam2rob_guess = mat2vector(np.matrix([[-.7152,.6985,-.0243,178.2],[.0412,.0074,-.9991,724.3],[-.6978,-.7155,-.0341,1515.7],[0.,0.,0.,1.]]))
# tcp2target_guess = mat2vector(np.matrix([[.0189,.9998,.0049,-206.5],[.9998,-.0189,-.0027,-71.1],[-.0026,.005,-1.,2.5],[0.,0.,0.,1.]]))
cam2rob_guess = np.array([1.54349198e+02, 7.47408195e+02, 1.46924939e+03, -1.07703900e+00, -2.49097316e+00, 2.47022147e+00])
tcp2target_guess = np.array([ -1.95790490e+02, 1.10668527e+02, 4.45463951e+00, 3.12965547e+00, -9.51645893e-02, -5.73926109e-03])
guess = np.concatenate((cam2rob_guess, tcp2target_guess))
with open(correspondences, 'r') as correspondences_file:
    correspondences_dictionary = json.load(correspondences_file)
    write_time = correspondences_dictionary['time']
    tcp2robot = correspondences_dictionary['tcp2robot']  # nx6 array x,y,z,axis-angle
    camera2grid = correspondences_dictionary['camera2grid']  # nx6 array x,y,z,axis-angle

result = error(guess,tcp2robot,camera2grid,intrinsic,distortion,test_points)
print(result)