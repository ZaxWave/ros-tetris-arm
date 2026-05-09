#这个算出来的结果实际就是hand_eye_calibration的结果

import numpy as np
from math import radians, cos, sin

# 定义欧拉角（以度为单位）
rx = -2.113121  # 旋转角度绕x轴（单位：度）
ry = 0.667186   # 旋转角度绕y轴（单位：度）
rz = -148.614283 # 旋转角度绕z轴（单位：度）

# 转换为弧度
rx_rad = radians(rx)
ry_rad = radians(ry)
rz_rad = radians(rz)

# 绕x轴的旋转矩阵
R_x = np.array([
    [1, 0, 0],
    [0, cos(rx_rad), -sin(rx_rad)],
    [0, sin(rx_rad), cos(rx_rad)]
])

# 绕y轴的旋转矩阵
R_y = np.array([
    [cos(ry_rad), 0, sin(ry_rad)],
    [0, 1, 0],
    [-sin(ry_rad), 0, cos(ry_rad)]
])

# 绕z轴的旋转矩阵
R_z = np.array([
    [cos(rz_rad), -sin(rz_rad), 0],
    [sin(rz_rad), cos(rz_rad), 0],
    [0, 0, 1]
])

# 总旋转矩阵（ZYX顺序）
rotation_matrix = np.dot(R_z, np.dot(R_y, R_x))

# 输出旋转矩阵
print("旋转矩阵:")
print(rotation_matrix)

# 定义平移向量（单位：毫米转为米）
tx = -21.221950  # x方向平移（单位：毫米）
ty = 107.262505  # y方向平移（单位：毫米）
tz = 24.906269   # z方向平移（单位：毫米）

# 平移向量（单位：米）
translation_vector = np.array([tx / 1000, ty / 1000, tz / 1000])

# 输出平移向量
print("平移向量:")
print(translation_vector)
