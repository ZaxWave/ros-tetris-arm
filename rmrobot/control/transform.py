import rospy
from rm_msgs.msg import Arm_Current_State, GetArmState_Command
import numpy as np
from scipy.spatial.transform import Rotation as R
import os
import glob
import re


rotation_matrix = np.array([
    [0.9986405533536075,
      -0.051061428446026964,
      -0.010477391023150824],
    [0.050894640142830884,
      0.9985819972831655,
      -0.015611864292768118],
    [0.011259698145708923,
      0.015057397750452391,
      0.9998232313617504]
])
translation_vector = np.array([-0.029569421037002655, -0.05337783602682322, 0.023028992213978846])

# rotation_matrix = np.array([
# [0.9998996646082053,-0.011361535638535971,-0.00846027330130278],
# [0.011117734145421521,0.9995368777601313,-0.028327124545211784],
# [0.00877819479563925,0.028230223262710633,0.9995629033686011]])

# translation_vector = np.array([-0.0323337371219584, -0.10766620729062798, 0.024609788267459564])

def convert(x, y, z, x1, y1, z1, rx, ry, rz):
    obj_camera_coordinates = np.array([x, y, z])
    T_camera_to_end = np.eye(4)
    T_camera_to_end[:3, :3] = rotation_matrix
    T_camera_to_end[:3, 3] = translation_vector

    T_base_to_end = np.eye(4)
    T_base_to_end[:3, :3] = R.from_euler('xyz', [rx, ry, rz], degrees=False).as_matrix()
    T_base_to_end[:3, 3] = [x1, y1, z1]

    obj_homo = np.append(obj_camera_coordinates, 1.0)
    obj_end = T_camera_to_end @ obj_homo
    obj_base = T_base_to_end @ obj_end
    return obj_base[:3]

def get_current_pose(timeout=2.0):
    """订阅一次Arm_Current_State消息"""
    received = {}

    def callback(msg):
        received["pose"] = msg.Pose
        rospy.signal_shutdown("Got pose")

    rospy.init_node("get_arm_pose_node", anonymous=True)
    rospy.Subscriber("/rm_driver/Arm_Current_State", Arm_Current_State, callback)

    pub = rospy.Publisher("/rm_driver/GetArmState_Cmd", GetArmState_Command, queue_size=1)
    rospy.sleep(0.5)
    pub.publish(GetArmState_Command(command=""))

    rospy.sleep(timeout)
    if "pose" not in received:
        raise TimeoutError("[ERROR] 超时未获取末端位姿")
    return received["pose"]

if __name__ == "__main__":
    try:
        pose = get_current_pose()
        x1, y1, z1 = pose[0], pose[1], pose[2]
        rx, ry, rz = pose[3], pose[4], pose[5]
        print(f"[INFO] 获取到末端位姿：位置=({x1:.6f}, {y1:.6f}, {z1:.6f})，姿态=({rx:.6f}, {ry:.6f}, {rz:.6f})")

        final_dir = "/home/zhy/rmrobot/output/camerabase"
        output_dir = "/home/zhy/rmrobot/output/realfinal"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "transformed_result.txt")

        all_txt_files = glob.glob(os.path.join(final_dir, "*.txt"))
        txt_files = [f for f in all_txt_files if re.search(r"1.txt$", os.path.basename(f))]
        if not txt_files:
            raise FileNotFoundError(f"[ERROR] 未找到符合格式的1.txt")

        input_path = txt_files[0]
        print(f"[INFO] 使用的输入文件为：{input_path}")

        output_lines = []
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 4:
                    continue
                cls = parts[0]
                angle = float(parts[4]) if len(parts) >= 5 else 0.0
                try:
                    x = float(parts[1])
                    y = float(parts[2])
                    z = float(parts[3])
                except ValueError:
                    continue
                x_base, y_base, z_base = convert(x, y, z, x1, y1, z1, rx, ry, rz)
                output_lines.append(f"{cls} {x_base:.6f} {y_base:.6f} {z_base:.6f} {angle}")

        with open(output_path, 'w', encoding='utf-8') as f:
            for line in output_lines:
                f.write(line + '\n')

        print(f"[INFO] 转换完成，共处理 {len(output_lines)} 个目标")
        print(f"[INFO] 坐标已保存至：{output_path}")

    except Exception as e:
        print(f"[ERROR] {e}")
