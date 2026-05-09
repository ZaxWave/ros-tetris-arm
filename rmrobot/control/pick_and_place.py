#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
from rm_msgs.msg import MoveJ_P, Plan_State
import tf
import subprocess
import math

# 用户可修改参数


_move_result = None

def planStateCallback(msg):
    global _move_result
    _move_result = msg.state
    if msg.state:
        rospy.loginfo("Plan State OK")
    else:
        rospy.loginfo("Plan State Fail")

def wait_for_move(timeout=10.0):
    global _move_result
    rate = rospy.Rate(50)
    start = rospy.Time.now()
    while _move_result is None:
        if (rospy.Time.now() - start).to_sec() > timeout:
            rospy.logwarn("wait_for_move timeout")
            return False
        rate.sleep()
    ok = _move_result
    _move_result = None
    return ok

def rpy_to_quaternion(roll, pitch, yaw):
    return tf.transformations.quaternion_from_euler(roll, pitch, yaw, axes='sxyz')

def move(pub, x, y, z, yaw_deg, speed=0.3):
    global _move_result
    yaw_rad = math.radians(yaw_deg)
    quat = rpy_to_quaternion(3.1410000324249268, 0.004999999888241291, yaw_rad)

    msg = MoveJ_P()
    msg.Pose.position.x = x
    msg.Pose.position.y = y
    msg.Pose.position.z = z
    msg.Pose.orientation.x = quat[0]
    msg.Pose.orientation.y = quat[1]
    msg.Pose.orientation.z = quat[2]
    msg.Pose.orientation.w = quat[3]
    msg.speed = speed

    _move_result = None
    pub.publish(msg)
    ok = wait_for_move()
    if ok:
        rospy.loginfo("move done: ({:.4f}, {:.4f}, {:.4f}) yaw={}".format(x, y, z, yaw_deg))
    else:
        rospy.logwarn("move may have failed: ({:.4f}, {:.4f}, {:.4f})".format(x, y, z))

def suck():
    rospy.loginfo("******* 吸取 *******")
    subprocess.run(["python3", "/home/zhy/rmrobot/xipan/suck.py"])

def place():
    rospy.loginfo("******* 放置 *******")
    subprocess.run(["python3", "/home/zhy/rmrobot/xipan/place.py"])

def main():
    rospy.init_node('pick_and_place', anonymous=True)
    pub = rospy.Publisher('/rm_driver/MoveJ_P_Cmd', MoveJ_P, queue_size=10)
    rospy.Subscriber('/rm_driver/Plan_State', Plan_State, planStateCallback)
    rospy.sleep(2.0)

    # ===== 点1（吸取）参数 =====
    x1 = -0.316331 + 0.005
    y1 = 0.127351
    z1_approach = 0.15
    z1_pick = 0.125
    yaw1 = 0.0

    # ===== 点2（放置）参数 =====
    x2 = 0.01
    y2 = -0.24
    z2_approach = 0.15
    z2_place = 0.13
    
    alpha_0 = 86.0
    alpha_1 = 0.0
    
    yaw2 = alpha_0 - alpha_1

    speed = 0.3

    # ---- 吸取流程 ----
    move(pub, x1, y1, z1_approach, yaw1, speed)   # 运行到点1上方
    move(pub, x1, y1, z1_pick, yaw1, speed)        # 下降
    suck()
    rospy.sleep(1.5)
    move(pub, x1, y1, z1_approach, yaw1, speed)   # 上升

    # ---- 放置流程 ----
    move(pub, x2, y2, z2_approach, yaw2, speed)   # 运行到点2上方
    move(pub, x2, y2, z2_place, yaw2, speed)       # 下降
    place()
    rospy.sleep(0.5)
    move(pub, x2, y2, z2_approach, yaw2, speed)   # 上升

    rospy.loginfo("******* 完成 *******")

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
