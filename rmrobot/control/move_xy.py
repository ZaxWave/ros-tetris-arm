#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
from rm_msgs.msg import MoveJ_P, Plan_State
import tf
import math

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

def move_to(pub, x, y, z, yaw_deg):
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
    msg.speed = 0.3

    _move_result = None
    pub.publish(msg)
    ok = wait_for_move()
    if ok:
        rospy.loginfo("move done: ({:.6f}, {:.6f}, {:.6f}) yaw={}".format(x, y, z, yaw_deg))
    else:
        rospy.logwarn("move may have failed: ({:.6f}, {:.6f}, {:.6f})".format(x, y, z))

def main():
    rospy.init_node('move_xy', anonymous=True)
    pub = rospy.Publisher('/rm_driver/MoveJ_P_Cmd', MoveJ_P, queue_size=10)
    rospy.Subscriber('/rm_driver/Plan_State', Plan_State, planStateCallback)
    rospy.sleep(2.0)

    rospy.loginfo("===== 机械臂XY控制 =====")
    rospy.loginfo("输入 x y yaw 控制机械臂, z 固定为 0.15")
    rospy.loginfo("输入 q 退出")
    rospy.loginfo("格式: x y yaw  (例如: 0.11 0.32 0)")

    while not rospy.is_shutdown():
        try:
            line = input(">>> ").strip()
        except EOFError:
            break

        if not line:
            continue
        if line.lower() == 'q':
            rospy.loginfo("退出")
            break

        parts = line.split()
        if len(parts) != 3:
            rospy.logwarn("请输入3个值: x y yaw (例如: 0.11 0.32 0)")
            continue

        try:
            x = float(parts[0])
            y = float(parts[1])
            yaw_deg = float(parts[2])
        except ValueError:
            rospy.logwarn("输入格式错误，请输入数字")
            continue
        z = 0.45
        # z = 0.14
        move_to(pub, x  , y , z, yaw_deg)
        # move_to(pub, x + 0.005 , y , z, yaw_deg)

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
