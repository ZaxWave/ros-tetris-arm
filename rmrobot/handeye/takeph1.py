import pyrealsense2 as rs
import numpy as np
import cv2
import threading
import subprocess
import time
import os
from datetime import datetime

# 设置ROS环境
def setup_ros_environment():
    """设置ROS工作空间环境"""
    # 检查常见的ROS工作空间路径
    possible_workspaces = [
        os.path.expanduser('~/ws_rmrobot'),
        os.path.expanduser('~/catkin_ws'),
        os.path.expanduser('~/ros_ws'),
        '/opt/ros/noetic',  # 标准ROS安装路径
        '/opt/ros/melodic'
    ]
    
    ros_workspace = None
    setup_file = None
    
    for workspace in possible_workspaces:
        potential_setup = os.path.join(workspace, 'devel/setup.bash')
        if os.path.exists(potential_setup):
            ros_workspace = workspace
            setup_file = potential_setup
            break
    
    if ros_workspace and setup_file:
        print(f"已找到ROS工作空间: {ros_workspace}")
        # 设置环境变量
        os.environ['ROS_WORKSPACE'] = ros_workspace
        return True
    else:
        print("警告: 未找到ROS工作空间")
        print("请确保已正确安装ROS并创建工作空间")
        return False

# 在程序开始时设置ROS环境
ros_available = setup_ros_environment()

counter = 1  # 从1开始计数
script_dir = os.path.dirname(os.path.abspath(__file__))
folder = os.path.join(script_dir, 'calibration_images')  # 需提前创建文件夹
pose_file = os.path.join(os.path.dirname(__file__), 'pose.txt')

# 全局变量用于保存最近一次收到的位姿文本
latest_pose = None
latest_pose_time = 0.0
pose_lock = threading.Lock()
stop_event = threading.Event()

def shot(frame):
    """仅保存彩色图，命名为 1.png, 2.png..."""
    global counter
    path = os.path.join(folder, f"{counter}.png")
    cv2.imwrite(path, frame)
    print(f"已保存: {path}")

def check_ros_topics():
    """检查ROS topic是否可用"""
    if not ros_available:
        return False
        
    try:
        # 检查topic是否存在
        cmd = ['bash', '-c', 'source /opt/ros/noetic/setup.bash && rostopic list | grep rm_driver']
        if os.environ.get('ROS_WORKSPACE'):
            workspace = os.environ['ROS_WORKSPACE']
            cmd = ['bash', '-c', f'source {workspace}/devel/setup.bash && rostopic list | grep rm_driver']
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and '/rm_driver/Arm_Current_State' in result.stdout:
            print("✓ ROS topic /rm_driver/Arm_Current_State 可用")
            return True
        else:
            print("✗ ROS topic /rm_driver/Arm_Current_State 不可用")
            print("请先启动机械臂节点：")
            print("cd ~/ws_rmrobot/ && source devel/setup.bash")
            print("roslaunch rm_control rm_control.launch")
            print("rosrun rm_driver rm_driver")
            return False
    except Exception as e:
        print(f"检查ROS topic失败: {e}")
        return False

def pose_listener():
    """后台运行 rostopic echo，不断更新 latest_pose"""
    global latest_pose, latest_pose_time
    
    if not ros_available:
        print("ROS不可用，跳过位姿监听")
        return
        
    # 检查topic是否可用
    if not check_ros_topics():
        print("位姿监听线程将无法获取数据")
        return
        
    # 使用bash -c来正确执行source命令
    cmd = ['bash', '-c', 'source /opt/ros/noetic/setup.bash && rostopic echo /rm_driver/Arm_Current_State']
    
    # 如果找到了工作空间，使用工作空间的setup文件
    if os.environ.get('ROS_WORKSPACE'):
        workspace = os.environ['ROS_WORKSPACE']
        cmd = ['bash', '-c', f'source {workspace}/devel/setup.bash && rostopic echo /rm_driver/Arm_Current_State']

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, bufsize=1)
        print("位姿监听线程已启动")
    except Exception as e:
        print("无法启动 rostopic echo:", e)
        return

    # 等待机械臂节点初始化（最多等待10秒）
    print("等待机械臂节点初始化...")
    start_time = time.time()
    first_message_received = False
    init_block_lines = []  # 用于收集初始化阶段的数据
    
    while not stop_event.is_set() and time.time() - start_time < 10:
        line = proc.stdout.readline()
        if line == '' and proc.poll() is not None:
            break
        if line:
            print(f"收到机械臂数据: {line.strip()}")
            # 关键修改1：用 --- 触发初始化消息保存（替换原空行判断）
            if '---' in line.strip():
                if init_block_lines:
                    msg = ''.join(init_block_lines).strip()
                    with pose_lock:
                        latest_pose = msg
                        latest_pose_time = time.time()
                        print(f"初始化阶段收到位姿数据，时间戳: {time.time()}")
                    init_block_lines = []
                    first_message_received = True
                    break
            else:
                init_block_lines.append(line)
        time.sleep(0.1)
    
    if not first_message_received:
        print("警告: 10秒内未收到机械臂数据，可能机械臂节点未完全启动")
    
    # 正常处理数据流
    block_lines = []
    error_count = 0
    message_count = 0
    
    while not stop_event.is_set():
        line = proc.stdout.readline()
        if line == '' and proc.poll() is not None:
            break
        if not line:
            time.sleep(0.01)
            continue
            
        # 检查是否有错误输出
        if line.startswith('ERROR') or 'error' in line.lower():
            error_count += 1
            if error_count <= 3:  # 只显示前3个错误
                print(f"位姿监听错误: {line.strip()}")
            continue
            
        # 关键修改2：用 --- 作为消息分隔符（替换原空行判断）
        if '---' in line.strip():
            if block_lines:
                msg = ''.join(block_lines).strip()
                with pose_lock:
                    latest_pose = msg
                    latest_pose_time = time.time()
                    message_count += 1
                    print(f"收到位姿数据 #{message_count}，时间戳: {time.time()}")
                block_lines = []
        else:
            block_lines.append(line)  # 收集消息内容（joint、Pose等行）
            
        # 重置错误计数
        if error_count > 0 and 'error' not in line.lower():
            error_count = 0
            
    try:
        proc.terminate()
    except:
        pass

def request_arm_state_publish():
    """发送一次 GetArmState_Cmd 指令（按用户要求的格式），使用 -1 只发布一次"""
    if not ros_available:
        print("ROS不可用，跳过发送GetArmState_Cmd")
        return
        
    # 使用bash -c来正确执行source命令
    pub_cmd = ['bash', '-c', 'source /opt/ros/noetic/setup.bash && rostopic pub -1 /rm_driver/GetArmState_Cmd rm_msgs/GetArmState_Command "command: \'\'"']
    
    # 如果找到了工作空间，使用工作空间的setup文件
    if os.environ.get('ROS_WORKSPACE'):
        workspace = os.environ['ROS_WORKSPACE']
        pub_cmd = ['bash', '-c', f'source {workspace}/devel/setup.bash && rostopic pub -1 /rm_driver/GetArmState_Cmd rm_msgs/GetArmState_Command "command: \'\'"']

    try:
        subprocess.run(pub_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("成功发送GetArmState_Cmd")
    except subprocess.CalledProcessError as e:
        print(f"发送GetArmState_Cmd失败，退出码: {e.returncode}")
        # 检查是否是命令未找到错误
        if e.returncode == 127:
            print("错误: rostopic命令未找到，请检查ROS安装")
        else:
            print(f"其他错误: {e}")
    except Exception as e:
        print("发送GetArmState_Cmd失败:", e)

def save_pose_for_counter(idx, timeout=5.0):
    """等待 latest_pose 更新并把它追加保存到 pose.txt"""
    start_wait = time.time()
    # 关键修改3：如果基准时间为0，直接用当前时间-1（避免首次采集时判断失效）
    with pose_lock:
        baseline_time = latest_pose_time if latest_pose_time != 0.0 else start_wait - 1.0
        print(f"开始等待位姿数据，基准时间: {baseline_time}")
        
    # 等待新的位姿（发布命令后上位机会更新 latest_pose_time）
    while time.time() - start_wait < timeout:
        with pose_lock:
            if latest_pose_time > baseline_time and latest_pose is not None:
                text = latest_pose
                print(f"成功获取到位姿数据，等待时间: {time.time() - start_wait:.2f}秒")
                break
        time.sleep(0.05)
    else:
        # 超时，仍然尝试保存当前缓冲的位姿（可能为 None）
        with pose_lock:
            text = latest_pose if latest_pose is not None else '<NO_POSE_RECEIVED>'
        print(f"位姿获取超时，保存的数据: {'有数据' if text != '<NO_POSE_RECEIVED>' else '无数据'}")
        
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = f"=== #{idx}  {ts} ===\n{text}\n\n"
    try:
        with open(pose_file, 'a', encoding='utf-8') as f:
            f.write(entry)
        print(f"位姿已保存到 {pose_file}")
    except Exception as e:
        print("写入 pose.txt 失败:", e)

# RealSense相机配置
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

# 启动后台位姿监听线程（仅在ROS可用时）
if ros_available:
    t = threading.Thread(target=pose_listener, daemon=True)
    t.start()
    print("已启动位姿监听线程")
    # 等待更长时间让监听线程完全启动
    time.sleep(2)
else:
    print("ROS不可用，将无法获取机械臂位姿")

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
        elif key == ord('t'):  # 按t保存彩色图并请求/保存位姿
            # 先保存图片
            shot(color_image)
            # 发送获取位姿的发布指令（一次）
            request_arm_state_publish()
            # 等待并保存位姿到 pose.txt（与图片序号对应）
            save_pose_for_counter(counter, timeout=5.0)
            counter += 1

finally:
    stop_event.set()
    try:
        pipeline.stop()
    except:
        pass
    cv2.destroyAllWindows()