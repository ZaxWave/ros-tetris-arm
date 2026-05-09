#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
from rm_msgs.msg import MoveJ_P, Plan_State
import tf
import subprocess
import math

_move_result = None  # True=成功, False=失败, None=等待中

def planStateCallback(msg):
    global _move_result
    _move_result = msg.state
    if msg.state:
        rospy.loginfo("Plan State OK")
    else:
        rospy.loginfo("Plan State Fail")

def wait_for_move(timeout=10.0):
    """轮询 Plan_State，返回 True=成功 / False=超时或失败"""
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

def move(pub, x, y, z, yaw_deg):
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
    msg.speed = 0.4

    _move_result = None
    pub.publish(msg)
    ok = wait_for_move()
    if ok:
        rospy.loginfo(f"move done: ({x:.3f}, {y:.3f}, {z:.3f}) yaw={yaw_deg}")
    else:
        rospy.logwarn(f"move may have failed: ({x:.3f}, {y:.3f}, {z:.3f})")

def suck():
    rospy.loginfo("*******吸盘启动*******")
    subprocess.run(["python3", "/home/zhy/rmrobot/xipan/suck.py"])

def place():    
    rospy.loginfo("*******放置启动*******")
    subprocess.run(["python3", "/home/zhy/rmrobot/xipan/place.py"])

# def convert_target_coordinates(x_grid, y_grid):
#     x_real = -0.18 + 0.02 * x_grid
#     y_real = -0.028 + 0.02 * y_grid
#     return x_real, y_real

# def convert_target_coordinates(x_real, y_real):
#     # 定义固定参数
#     x0 = -0.39632429214108167
#     y0 = -0.22349956478452163
#     angle_deg = -23.0
#
#     # 转换为弧度（顺时针旋转所以角度取负）
#     angle_rad = math.radians(-angle_deg)
#
#     # 计算旋转后的坐标
#     cos_theta = math.cos(angle_rad)
#     sin_theta = math.sin(angle_rad)
#     x2 = x_real/100 * cos_theta - y_real/100 * sin_theta
#     y2 = x_real/100 * sin_theta + y_real/100 * cos_theta
#
#     x_real = x0 + x2
#     y_real = y0 + y2
#     return x_real, y_real

def main():
    rospy.init_node('moveJ_P', anonymous=True)
    pub = rospy.Publisher('/rm_driver/MoveJ_P_Cmd', MoveJ_P, queue_size=10)
    rospy.Subscriber('/rm_driver/Plan_State', Plan_State, planStateCallback)
    rospy.sleep(2.0)

    # 读取吸取坐标（基座坐标系，含相机检测角度）
    pickup_file = "/home/zhy/rmrobot/output/realfinal/transformed_result.txt"
    with open(pickup_file, 'r') as f:
        pickup_lines = [l for l in f if l.strip()]

    # 读取放置坐标（棋盘格目标格子 + 目标角度）
    place_file = "/home/zhy/rmrobot/output/xx.txt"
    with open(place_file, 'r') as f:
        place_lines = [l for l in f if l.strip()]

    # 解析 transform.txt: class_name -> [(x, y, z, cam_angle), ...]（同名可能多行）
    pickup_data = {}
    for line in pickup_lines:
        parts = line.strip().split()
        if len(parts) != 5:
            rospy.logwarn(f"吸取文件行格式错误：{line}")
            continue
        cls = parts[0]
        x, y, z, cam_angle = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
        pickup_data.setdefault(cls, []).append((x, y, z, cam_angle))
    used = {}  # class_name -> 已用掉的索引

    seq = 0
    for g_line in place_lines:
        g_parts = g_line.strip().split()
        if len(g_parts) != 4:
            rospy.logwarn(f"放置文件行格式错误：{g_line}")
            continue
        shape, grid_x, grid_y, grid_angle = g_parts[0], float(g_parts[1]), float(g_parts[2]), float(g_parts[3])

        if shape not in pickup_data:
            rospy.logwarn(f"吸取文件中找不到方块 {shape}，跳过")
            continue
        idx = used.get(shape, 0)
        if idx >= len(pickup_data[shape]):
            rospy.logwarn(f"方块 {shape} 已用完，跳过")
            continue
        px, py, pz, cam_angle = pickup_data[shape][idx]
        used[shape] = idx + 1

        rot = cam_angle - grid_angle
        place_x, place_y = grid_x, grid_y
        seq += 1

        rospy.loginfo(f"==== 第{seq}个方块：{shape} cam_angle={cam_angle} grid_angle={grid_angle} rot={rot} ====")
        rospy.loginfo(f"吸取: ({px:.4f}, {py:.4f})  放置: ({place_x:.4f}, {place_y:.4f})")

        # 放置过程
        move(pub, place_x, place_y, 0.15, rot)
        move(pub, place_x, place_y, 0.125, rot)       
        suck()        
        rospy.sleep(0.25)
        move(pub, place_x, place_y, 0.15, rot) 



        # 吸取过程
        move(pub, px + 0.005, py, 0.15, 0.0)
        move(pub, px + 0.005, py, 0.13, 0.0)
        place()
        rospy.sleep(1.5)
        move(pub, px, py, 0.15, 0.0)




        # move(pub, place_x, place_y, 0.16, rot)

    rospy.loginfo("******* 所有方块已放置完成 *******")
    rospy.spin()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass