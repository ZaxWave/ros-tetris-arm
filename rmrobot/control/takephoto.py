import pyrealsense2 as rs
import numpy as np
import cv2
import os

counter = 1
base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
color_dir = os.path.join(base_dir, "color")
depth_dir = os.path.join(base_dir, "depth")
os.makedirs(color_dir, exist_ok=True)
os.makedirs(depth_dir, exist_ok=True)

def shot(color_frame, depth_frame):
    global counter
    color_path = os.path.join(color_dir, f"{counter}.png")
    depth_path = os.path.join(depth_dir, f"{counter}.png")
    cv2.imwrite(color_path, color_frame)
    cv2.imwrite(depth_path, depth_frame)
    print(f"已保存: {color_path}")
    print(f"已保存: {depth_path}")

pipeline = rs.pipeline()
config = rs.config()

config.enable_stream(rs.stream.color, 1920, 1080, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)

profile = pipeline.start(config)

align_to = rs.stream.color
align = rs.align(align_to)

try:
    while True:
        frames = pipeline.wait_for_frames()
        aligned_frames = align.process(frames)

        color_frame = aligned_frames.get_color_frame()
        depth_frame = aligned_frames.get_depth_frame()
        if not color_frame or not depth_frame:
            continue

        color_image = np.asanyarray(color_frame.get_data())
        depth_image = np.asanyarray(depth_frame.get_data())

        color_show = cv2.resize(color_image, (960, 540))
        cv2.imshow('D435 (t=save, ESC=quit)', color_show)

        key = cv2.waitKey(1)
        if key == 27:
            cv2.destroyAllWindows()
            break
        elif key == ord('t'):
            shot(color_image, depth_image)
            counter += 1

finally:
    pipeline.stop()
