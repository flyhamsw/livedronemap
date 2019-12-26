import numpy as np
import math



def calibrate(yaw, pitch, roll, R_CB, type):
    # R_rpy = A2R_RPY(roll, pitch, yaw)
    # R_opk = R_rpy.dot(R_CB)
    R_ypr = A2R_Multi(yaw, pitch, roll, type)
    R_opk = R_ypr.dot(R_CB)


    return R2A_OPK(R_opk)


# def A2R_RPY(r, p, y):
#     om, ph, kp = p, r, -y
#
#     Rot_x = np.array([[1., 0., 0.], [0., math.cos(om), -math.sin(om)], [0., math.sin(om), math.cos(om)]], dtype=float)
#     Rot_y = np.array([[math.cos(ph), 0, math.sin(ph)], [0, 1, 0], [-math.sin(ph), 0, math.cos(ph)]], dtype=float)
#     Rot_z = np.array([[math.cos(kp), -math.sin(kp), 0], [math.sin(kp), math.cos(kp), 0], [0, 0, 1]], dtype=float)
#
#     Rot_rpy = np.linalg.multi_dot([Rot_y, Rot_z, Rot_x])
#     return Rot_rpy

def A2R_Multi(y, p, r, type):

    #clockwise or counterclockwise
    tmp = type[0]-1
    option = np.zeros(3)
    for n in [0, 1, 2]:
        option[n] = np.mod(tmp, 2) #get a remainder
        tmp = np.fix(tmp/2)        #Round Toward Zero
    if option[2] != 0:
        y = -y
    if option[1] != 0:
        p = -p
    if option[0] != 0:
        r = -r

    #angle combination
    if type[1]-1 == 0:
        om = y, ph = p, kp = r
    elif type[1]-1 == 1:
        om = y, ph = r, kp = p
    elif type[1]-1 == 2:
        om = p, ph = y, kp = r
    elif type[1]-1 == 3:
        om = p, ph = r, kp = y
    elif type[1]-1 == 4:
        om = r, ph = y, kp = p
    elif type[1]-1 == 5:
        om = r, ph = p, kp = y

    #matrix combination
    Rx = np.array([[1, 0, 0],
                   [0, math.cos(om), -math.sin(om)],
                   [0, math.sin(om), math.cos(om)]], dtype=float)
    Ry = np.array([[math.cos(ph), 0, math.sin(ph)],
                   [0, 1, 0],
                   [-math.sin(ph), 0, math.cos(ph)]], dtype=float)
    Rz = np.array([[math.cos(kp), -math.sin(kp), 0],
                   [math.sin(kp), math.cos(kp), 0],
                   [0, 0, 1]], dtype=float)

    if type[2]-1 == 0:
        Rot_ypr = np.linalg.multi_dot([Rx, Ry, Rz])
    elif type[2]-1 == 1:
        Rot_ypr = np.linalg.multi_dot([Rx, Rz, Ry])
    elif type[2]-1 == 2:
        Rot_ypr = np.linalg.multi_dot([Ry, Rx, Rz])
    elif type[2]-1 == 3:
        Rot_ypr = np.linalg.multi_dot([Ry, Rz, Rx])
    elif type[2]-1 == 4:
        Rot_ypr = np.linalg.multi_dot([Rz, Rx, Ry])
    elif type[2]-1 == 5:
        Rot_ypr = np.linalg.multi_dot([Rz, Ry, Rx])

    return Rot_ypr

def R2A_OPK(Rot_opk):
    s_ph = Rot_opk[0, 2]
    temp = (1 + s_ph) * (1 - s_ph)
    c_ph1 = math.sqrt(temp)
    c_ph2 = -math.sqrt(temp)

    omega = math.atan2(-Rot_opk[1, 2], Rot_opk[2, 2])
    phi = math.atan2(s_ph, c_ph1)
    kappa = math.atan2(-Rot_opk[0, 1], Rot_opk[0, 0])

    return omega, phi, kappa

