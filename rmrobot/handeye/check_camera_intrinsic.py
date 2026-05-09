import pyrealsense2 as rs
import json

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 1920, 1080, rs.format.bgr8, 30)

profile = pipeline.start(config)
color_stream = profile.get_stream(rs.stream.color)
intrinsics = color_stream.as_video_stream_profile().get_intrinsics()

print("当前 RealSense 彩色相机内参:")
print(f"  fx = {intrinsics.fx}")
print(f"  fy = {intrinsics.fy}")
print(f"  cx = {intrinsics.ppx}")
print(f"  cy = {intrinsics.ppy}")
print(f"  width  = {intrinsics.width}")
print(f"  height = {intrinsics.height}")
print(f"  model  = {intrinsics.model}")
print(f"  coeffs = {intrinsics.coeffs}")

# 对比 0507good 标定结果
print("\n0507good 标定结果 (camera_intrinsic.json):")
with open('0507good/camera_intrinsic.json') as f:
    calib = json.load(f)
cm = calib['camera_matrix']
print(f"  fx = {cm[0][0]}")
print(f"  fy = {cm[1][1]}")
print(f"  cx = {cm[0][2]}")
print(f"  cy = {cm[1][2]}")
print(f"  dist = {calib['dist_coeffs'][0]}")

print("\n差值 (当前 - 标定):")
print(f"  Δfx = {intrinsics.fx - cm[0][0]:.3f}")
print(f"  Δfy = {intrinsics.fy - cm[1][1]:.3f}")
print(f"  Δcx = {intrinsics.ppx - cm[0][2]:.3f}")
print(f"  Δcy = {intrinsics.ppy - cm[1][2]:.3f}")

pipeline.stop()
