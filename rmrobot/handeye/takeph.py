import pyrealsense2 as rs
import numpy as np
import cv2
import os

counter = 1  # 从1开始计数
# 使用绝对路径确保图片保存到正确位置
script_dir = os.path.dirname(os.path.abspath(__file__))
folder = os.path.join(script_dir, 'calibration_images')  # 绝对路径  # 需提前创建文件夹

def shot(frame):
    """仅保存彩色图，命名为 1.png, 2.png..."""
    global counter
    path = os.path.join(folder, f"{counter}.png")
    cv2.imwrite(path, frame)
    print(f"已保存: {path}")

pipeline = rs.pipeline()
config = rs.config()

# 彩色流配置（最高分辨率）
config.enable_stream(rs.stream.color, 1920, 1080, rs.format.bgr8, 30)
# 深度流仍需启用（用于对齐，但不保存）
config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)

profile = pipeline.start(config)

# 深度对齐到彩色图（关键：保证深度与彩色图空间一致）
align_to = rs.stream.color
align = rs.align(align_to)

try:
    while True:
        frames = pipeline.wait_for_frames()
        aligned_frames = align.process(frames)  # 执行对齐处理

        # 获取对齐后的彩色帧（重点：从对齐帧中提取）
        color_frame = aligned_frames.get_color_frame()
        if not color_frame:
            continue

        # 转换为原始彩色图像（未经过任何颜色加工）
        color_image = np.asanyarray(color_frame.get_data())

        # 缩放显示（方便观察）
        color_show = cv2.resize(color_image, (960, 540))
        cv2.imshow('Color Image (for calibration)', color_show)

        key = cv2.waitKey(1)
        if key == 27:  # ESC退出
            cv2.destroyAllWindows()
            break
        elif key == ord('t'):  # 按t保存彩色图
            shot(color_image)
            counter += 1

finally:
    pipeline.stop()