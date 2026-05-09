import pyrealsense2 as rs

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 1920, 1080, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)

profile = pipeline.start(config)

color_stream = profile.get_stream(rs.stream.color)
color_intr = color_stream.as_video_stream_profile().get_intrinsics()

depth_stream = profile.get_stream(rs.stream.depth)
depth_intr = depth_stream.as_video_stream_profile().get_intrinsics()

print("=== Color 内参 ===")
print(f"  fx={color_intr.fx}  fy={color_intr.fy}")
print(f"  cx={color_intr.ppx}  cy={color_intr.ppy}")
print(f"  width={color_intr.width}  height={color_intr.height}")
print(f"  model={color_intr.model}")
print(f"  coeffs={color_intr.coeffs}")

print("\n=== Depth 内参 ===")
print(f"  fx={depth_intr.fx}  fy={depth_intr.fy}")
print(f"  cx={depth_intr.ppx}  cy={depth_intr.ppy}")
print(f"  width={depth_intr.width}  height={depth_intr.height}")
print(f"  model={depth_intr.model}")
print(f"  coeffs={depth_intr.coeffs}")

pipeline.stop()
