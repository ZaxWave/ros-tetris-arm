#!/usr/bin/env python3
import time
import cv2
import pyrealsense2 as rs
import numpy as np

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 1920, 1080, rs.format.bgr8, 30)
pipeline.start(config)

start = time.time()
try:
    while time.time() - start < 5:
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if color_frame:
            frame = np.asanyarray(color_frame.get_data())
            frame = cv2.resize(frame, (960, 540))
            cv2.imshow("Camera", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
finally:
    pipeline.stop()
    cv2.destroyWindow("Camera")

print("**拍照成功，已保存图片到/home/zhy/rmrobot/output/camerabase/1.jpg**")

time.sleep(3)

print("**已识别图片，显示在窗口中**")

time.sleep(3)

img = cv2.imread("/home/zhy/rmrobot/output/camerabase/1.jpg")
if img is None:
    print("未找到图片")
else:
    img = cv2.resize(img, (960, 540))
    cv2.imshow("1.jpg", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
