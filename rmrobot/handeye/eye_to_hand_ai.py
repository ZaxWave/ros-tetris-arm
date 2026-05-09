import cv2
import numpy as np
import json
import os
from pathlib import Path

# 相机坐标转机器人坐标
def convert_cam_pose_to_robot(cam_target,  basetocam):
    """
    将相机坐标系下的位姿（x,y,z,rx,ry,rz）转换为机器人坐标系下位姿
    :param cam_x, cam_y, cam_z: 相机坐标系下平移分量 (mm)
    :param cam_rx, cam_ry, cam_rz: 相机坐标系下体轴ZYX欧拉角 (度)
    :param camera2base: 相机到机器人基坐标系的变换矩阵（4x4齐次矩阵，来自手眼标定）
    :return: 机器人坐标系下的平移(x,y,z)和欧拉角(rx,ry,rz)（体轴ZYX，度）
    """
    # 1. 构建相机坐标系下的齐次变换矩阵
    cam_translation = np.array(cam_target[:3])
    cam_euler = np.array(cam_target[3:])
    # 使用体轴ZYX欧拉角转旋转矩阵（需确保与相机位姿定义一致）
    R_cam = euler_xyz_to_rotation_matrix(cam_euler)  # 需保留之前新增的此函数
    T_cam = build_transform_matrix(R_cam, cam_translation)  # 复用现有函数
    
    # 2. 转换到机器人坐标系：机器人位姿 = camera2base矩阵 * 相机位姿矩阵
    T_robot = basetocam @ T_cam
    
    # 3. 提取机器人坐标系下的平移分量
    robot_x, robot_y, robot_z = T_robot[:3, 3].flatten()
    
    # 4. 提取旋转矩阵并转换为体轴ZYX欧拉角（复用现有函数）
    R_robot = T_robot[:3, :3]
    robot_rx, robot_ry, robot_rz = rotation_matrix_to_euler_zyx(R_robot)
    basetotarget = robot_x, robot_y, robot_z,robot_rx, robot_ry, robot_rz

    return (basetotarget)

# 新增：旋转矩阵转体轴ZYX欧拉角（度）
def rotation_matrix_to_euler_zyx(R):
    """
    将旋转矩阵转换为体轴ZYX顺序的欧拉角（rx, ry, rz），单位为度
    体轴ZYX：先绕自身Z轴旋转rz，再绕自身Y轴旋转ry，最后绕自身X轴旋转rx
    """
    # 确保旋转矩阵的数值稳定性
    R = np.clip(R, -1.0, 1.0)
    
    # 计算ry
    ry = np.arcsin(-R[2, 0])
    
    # 避免 gimbal lock（当ry为±90度时）
    if np.isclose(np.abs(ry), np.pi/2):
        rz = 0.0
        rx = np.arctan2(R[0, 1], R[1, 1])
    else:
        # 计算rx和rz
        rx = np.arctan2(R[2, 1], R[2, 2])
        rz = np.arctan2(R[1, 0], R[0, 0])
    
    # 转换为度并返回（rx, ry, rz）
    return np.rad2deg([rx, ry, rz])

# 工具函数：欧拉角转旋转矩阵（原有）
def euler_xyz_to_rotation_matrix(euler_angles_degrees):
    # rx, ry, rz = np.radians(euler_angles_degrees)
    rx, ry, rz = euler_angles_degrees
    
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(rx), -np.sin(rx)],
        [0, np.sin(rx), np.cos(rx)]
    ])
    
    Ry = np.array([
        [np.cos(ry), 0, np.sin(ry)],
        [0, 1, 0],
        [-np.sin(ry), 0, np.cos(ry)]
    ])
    
    Rz = np.array([
        [np.cos(rz), -np.sin(rz), 0],
        [np.sin(rz), np.cos(rz), 0],
        [0, 0, 1]
    ])
    
    return Rz @ Ry @ Rx

# 工具函数：构建齐次变换矩阵（原有）
def build_transform_matrix(rotation, translation):
    transform = np.eye(4)
    transform[:3, :3] = rotation
    transform[:3, 3] = translation.flatten()
    return transform

# 数据加载函数：加载标定图像（原有）
def load_images(image_folder):
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    image_paths = []
    
    for ext in image_extensions:
        image_paths.extend(Path(image_folder).glob(f'*{ext}'))
    
    image_paths = sorted(image_paths)
    
    if len(image_paths) == 0:
        raise Exception(f"在文件夹 {image_folder} 中未找到图像文件")
    
    print(f"找到 {len(image_paths)} 张图像")
    
    calibration_images = []
    for img_path in image_paths:
        img = cv2.imread(str(img_path))
        if img is not None:
            calibration_images.append(img)
            print(f"已加载图像: {img_path.name}")
        else:
            print(f"警告: 无法加载图像 {img_path}")
    
    return calibration_images

# 数据加载函数：加载机器人位姿（原有）
def load_robot_poses(pose_file):
    if not os.path.exists(pose_file):
        raise Exception(f"位姿文件不存在: {pose_file}")
    
    robot_poses = []
    
    with open(pose_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"读取到 {len(lines)} 行数据")
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        parts = [p.strip() for p in line.split(',')]
        
        if len(parts) != 6:
            print(f"警告: 第 {i+1} 行格式错误（需6个元素，实际{len(parts)}个），跳过")
            continue
        
        try:
            # x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
            x, y, z = float(parts[0]) * 1000, float(parts[1]) * 1000, float(parts[2]) * 1000
            rx, ry, rz = float(parts[3]), float(parts[4]), float(parts[5])  
            
            R = euler_xyz_to_rotation_matrix([rx, ry, rz])
            T = build_transform_matrix(R, np.array([x, y, z]))
            robot_poses.append(T)
            
            print(f"已加载位姿 {i+1}: [{x:.2f}, {y:.2f}, {z:.2f}, {rx:.2f}, {ry:.2f}, {rz:.2f}]")
        
        except ValueError as e:
            print(f"警告: 第 {i+1} 行解析错误: {e}，跳过")
    
    print(f"成功加载 {len(robot_poses)} 个有效位姿")
    return robot_poses

# 棋盘格检测函数（原有）
def detect_chessboard_corners(images, chessboard_size, square_size, show_detection=True):
    objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:chessboard_size[0], 
                          0:chessboard_size[1]].T.reshape(-1, 2)
    objp *= square_size
    
    objpoints = []
    imgpoints = []
    valid_indices = []
    
    print("开始检测棋盘格角点...")
    
    for i, img in enumerate(images):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        ret, corners = cv2.findChessboardCorners(gray, chessboard_size, 
                                               cv2.CALIB_CB_ADAPTIVE_THRESH + 
                                               cv2.CALIB_CB_NORMALIZE_IMAGE + 
                                               cv2.CALIB_CB_FAST_CHECK)
        
        if ret:
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            
            objpoints.append(objp)
            imgpoints.append(corners_refined)
            valid_indices.append(i)
            
            print(f"图像 {i+1}: 成功检测到角点")
            
            if show_detection:
                img_display = img.copy()
                cv2.drawChessboardCorners(img_display, chessboard_size, corners_refined, ret)
                cv2.putText(img_display, f"Image {i+1}: Detected", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow('Chessboard Detection', img_display)
                cv2.waitKey(500)
        else:
            print(f"图像 {i+1}: 未检测到角点")
    
    if show_detection:
        cv2.destroyAllWindows()
    
    print(f"角点检测完成: {len(objpoints)}/{len(images)} 张图像有效")
    
    return objpoints, imgpoints, valid_indices

# 相机内参标定函数（原有）
def calibrate_camera_intrinsic(objpoints, imgpoints, image_shape):
    print("开始相机内参标定...")
    
    ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, image_shape, None, None)
    
    if not ret:
        raise Exception("相机内参标定失败")
    
    mean_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], 
                                        camera_matrix, dist_coeffs)
        error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
        mean_error += error
    
    mean_error /= len(objpoints)
    
    print(f"相机内参标定完成!")
    print(f"重投影误差: {mean_error:.3f} 像素")
    print(f"相机内参矩阵:\n{camera_matrix}")
    print(f"畸变系数: {dist_coeffs.flatten()}")
    
    return camera_matrix, dist_coeffs, mean_error

# 棋盘格位姿估计函数（原有）
def estimate_chessboard_poses(objpoints, imgpoints, valid_indices, camera_matrix, dist_coeffs):
    camera_poses = []
    
    print("开始估计棋盘格位姿...")
    
    for i, (objp, imgp) in enumerate(zip(objpoints, imgpoints)):
        ret, rvec, tvec = cv2.solvePnP(objp, imgp, camera_matrix, dist_coeffs)
        
        if ret:
            R, _ = cv2.Rodrigues(rvec)
            camera_pose = build_transform_matrix(R, tvec)
            camera_poses.append(camera_pose)
            
            print(f"图像 {valid_indices[i]+1}: 位姿估计成功")
        else:
            print(f"图像 {valid_indices[i]+1}: 位姿估计失败")
            camera_poses.append(None)
    
    return camera_poses

# 手眼标定核心函数（原有）
def hand_eye_calibration(camera_poses, robot_poses, valid_indices):
    valid_camera_poses = []
    valid_robot_poses = []
    
    for idx in valid_indices:
        if idx < len(camera_poses) and idx < len(robot_poses):
            if camera_poses[idx] is not None:
                valid_camera_poses.append(camera_poses[idx])
                valid_robot_poses.append(robot_poses[idx])
    
    if len(valid_camera_poses) < 10:
        raise Exception(f"有效数据不足: {len(valid_camera_poses)}，至少需要10组")
    
    print(f"使用 {len(valid_camera_poses)} 组有效数据进行手眼标定")
    

    A_relative = []
    B_relative = []
    
    for i in range(1, len(valid_robot_poses)):
        # A_i = np.linalg.inv(valid_robot_poses[i-1])
        A_i = (valid_robot_poses[i-1])  
        B_i = (valid_camera_poses[i-1]) 

        
        A_relative.append(A_i)
        B_relative.append(B_i)
    
    print(f"使用 {len(A_relative)} 组相对运动进行标定")
    
    try:
        R_base2cam, t_base2cam = cv2.calibrateHandEye(      #眼在手外，得到的是base到cam的变换矩阵，眼在手上，得到是tcp（法兰末端）到can的变换矩阵
            [pose[:3, :3] for pose in A_relative],
            [pose[:3, 3] for pose in A_relative],
            [pose[:3, :3] for pose in B_relative], 
            [pose[:3, 3] for pose in B_relative],
            method=cv2.CALIB_HAND_EYE_HORAUD
        )
        
        if R_base2cam is None or t_base2cam is None:
            raise Exception("手眼标定返回了空结果")
            
        if np.any(np.isnan(R_base2cam)) or np.any(np.isnan(t_base2cam)):
            raise Exception("手眼标定结果包含无效值")
        
    except Exception as e:
        raise Exception(f"手眼标定计算失败: {str(e)}")
    
    base2camera = build_transform_matrix(R_base2cam, t_base2cam)
    
    print("手眼标定完成!")
    
    return base2camera

# 标定验证函数（原有）
def verify_calibration_by_axxb(camera_poses, robot_poses, valid_indices, base2camera):
    if base2camera is None:
        raise Exception("请先进行手眼标定，确保已得到手眼变换矩阵X（camera2base）")
    if not isinstance(base2camera, np.ndarray) or base2camera.shape != (4, 4):
        raise Exception("手眼变换矩阵X（base2camera）格式错误，需为4×4齐次矩阵")
    
    valid_robot = []
    valid_cam = []
    
    for idx in valid_indices:
        if 0 <= idx < len(robot_poses) and 0 <= idx < len(camera_poses):
            if robot_poses[idx] is not None and camera_poses[idx] is not None:
                valid_robot.append(robot_poses[idx])
                valid_cam.append(camera_poses[idx])
    
    if len(valid_robot) < 2:
        raise Exception(f"有效位姿数量不足（需≥2组，实际{len(valid_robot)}组），无法计算相对变换")
    
    print(f"开始基于AX=XB验证标定精度，共使用 {len(valid_robot)} 组有效位姿，计算 {len(valid_robot)-1} 组相对变换...")

    X = base2camera
    relative_errors = []

    for i in range(1, len(valid_robot)):
        T_tcp_prev = valid_robot[i-1]
        T_tcp_curr = valid_robot[i]
        # A_i = T_tcp_curr @ np.linalg.inv(T_tcp_prev)
        A_i = np.linalg.inv(T_tcp_curr) @ T_tcp_prev  #眼在手上#######################################################################################

        T_cam_prev = valid_cam[i-1]
        T_cam_curr = valid_cam[i]
        B_i = T_cam_curr @ np.linalg.inv(T_cam_prev)
 
 

        AX = A_i @ X
        XB = X @ B_i

        R_AX = AX[:3, :3]
        R_XB = XB[:3, :3]
        R_diff = R_AX @ R_XB.T
        trace = np.clip(np.trace(R_diff), -1.0 + 1e-8, 3.0 - 1e-8)
        rot_error_rad = np.arccos((trace - 1) / 2)
        rot_error_deg = np.rad2deg(rot_error_rad)

        t_AX = AX[:3, 3]
        t_XB = XB[:3, 3]
        trans_error = np.linalg.norm(t_AX - t_XB)

        relative_errors.append((rot_error_deg, trans_error))
        print(f"第{i}组相对变换验证：旋转误差 = {rot_error_deg:.3f} 度, 平移误差 = {trans_error:.3f} mm")

    rot_errors = [err[0] for err in relative_errors]
    trans_errors = [err[1] for err in relative_errors]

    avg_rot = np.mean(rot_errors)
    max_rot = np.max(rot_errors)
    avg_trans = np.mean(trans_errors)
    max_trans = np.max(trans_errors)

    print("\n" + "="*50)
    print("AX=XB标定验证精度统计")
    print("="*50)
    print(f"参与验证的相对变换组数：{len(relative_errors)} 组")
    print(f"平均旋转误差：{avg_rot:.3f} 度")
    print(f"最大旋转误差：{max_rot:.3f} 度")
    print(f"平均平移误差：{avg_trans:.3f} mm")
    print(f"最大平移误差：{max_trans:.3f} mm")
    print("="*50)

    return avg_rot, avg_trans, max_rot, max_trans


# 结果保存函数（更新）
def save_calibration_results(output_dir, camera_matrix, dist_coeffs, camera2base, base2camera, chessboard_size, square_size):
    Path(output_dir).mkdir(exist_ok=True)
    
    # 保存相机内参（原有）
    if camera_matrix is not None and dist_coeffs is not None:
        camera_data = {
            'camera_matrix': camera_matrix.tolist(),
            'dist_coeffs': dist_coeffs.tolist(),
            'chessboard_size': chessboard_size,
            'square_size': square_size
        }
        
        with open(f"{output_dir}/camera_intrinsic.json", 'w') as f:
            json.dump(camera_data, f, indent=2)
        print(f"相机内参已保存到 {output_dir}/camera_intrinsic.json")
    
    # 保存手眼标定结果（更新）
    if camera2base is not None and base2camera is not None:
        # 计算基坐标到相机的欧拉角（体轴ZYX）
        base2camera_rot = base2camera[:3, :3]
        rx, ry, rz = rotation_matrix_to_euler_zyx(base2camera_rot)
        
        # 提取平移分量
        tx, ty, tz = base2camera[:3, 3]
        
        hand_eye_data = {
            'camera2base': camera2base.tolist(),
            'base2camera': base2camera.tolist(),
            'base2camera_euler_zyx': {
                'rx_deg': float(rx),
                'ry_deg': float(ry),
                'rz_deg': float(rz),
                'tx_mm': float(tx),
                'ty_mm': float(ty),
                'tz_mm': float(tz)
            },
            'camera_matrix': camera_matrix.tolist() if camera_matrix is not None else None,
            'dist_coeffs': dist_coeffs.tolist() if dist_coeffs is not None else None,
            'chessboard_size': chessboard_size,
            'square_size': square_size
        }
        
        # 保存到JSON文件
        with open(f"{output_dir}/hand_eye_calibration.json", 'w') as f:
            json.dump(hand_eye_data, f, indent=2)
        print(f"手眼标定结果已保存到 {output_dir}/hand_eye_calibration.json")
        
        # 单独保存欧拉角到文本文件
        with open(f"{output_dir}/base2camera_euler_zyx.txt", 'w') as f:
            f.write("基坐标到相机的变换（体轴ZYX欧拉角）：\n")
            f.write(f"平移分量 (mm):\n")
            f.write(f"tx = {tx:.6f}\n")
            f.write(f"ty = {ty:.6f}\n")
            f.write(f"tz = {tz:.6f}\n\n")
            f.write(f"旋转分量 (度，体轴ZYX顺序):\n")
            f.write(f"rx = {rx:.6f}\n")
            f.write(f"ry = {ry:.6f}\n")
            f.write(f"rz = {rz:.6f}\n")
        print(f"基坐标到相机的欧拉角已保存到 {output_dir}/base2camera_euler_zyx.txt")

# 完整标定流程函数（原有）
def run_complete_calibration(image_folder, pose_file, output_dir="calibration_results", 
                            chessboard_size=(11, 8), square_size=15.0):
    print("=" * 50)
    print("开始完整的眼在手外标定流程")
    print("=" * 50)
    
    # 步骤1: 加载数据
    print("\n步骤1: 加载数据")
    calibration_images = load_images(image_folder)
    robot_poses = load_robot_poses(pose_file)
    
    # 数据数量匹配处理
    num_images = len(calibration_images)
    num_poses = len(robot_poses)
    if num_images != num_poses:
        print(f"警告: 图像数量 ({num_images}) 与位姿数量 ({num_poses}) 不匹配")
        min_count = min(num_images, num_poses)
        calibration_images = calibration_images[:min_count]
        robot_poses = robot_poses[:min_count]
        print(f"使用前 {min_count} 组数据进行标定")
    
    # 步骤2: 检测棋盘格角点
    print("\n步骤2: 检测棋盘格角点")
    objpoints, imgpoints, valid_indices = detect_chessboard_corners(
        calibration_images, chessboard_size, square_size, show_detection=False)
    
    if len(objpoints) < 10:
        raise Exception(f"有效图像数量不足: {len(objpoints)}，至少需要10张")
    
    # 步骤3: 相机内参标定
    print("\n步骤3: 相机内参标定")
    image_shape = calibration_images[0].shape[:2][::-1]  # (width, height)
    camera_matrix, dist_coeffs, _ = calibrate_camera_intrinsic(objpoints, imgpoints, image_shape)
    
    # 步骤4: 估计棋盘格位姿
    print("\n步骤4: 估计棋盘格在相机坐标系中的位姿")
    camera_poses = estimate_chessboard_poses(objpoints, imgpoints, valid_indices, camera_matrix, dist_coeffs)
    
    # 筛选有效的机器人位姿
    valid_robot_poses = [robot_poses[i] for i in valid_indices]
    
    # 步骤5: 手眼标定
    print("\n步骤5: 手眼标定")
    base2camera = hand_eye_calibration(camera_poses, valid_robot_poses, range(len(camera_poses)))
    
    # 新增：显示基坐标到相机的欧拉角结果
    rx, ry, rz = rotation_matrix_to_euler_zyx(base2camera[:3, :3])
    tx, ty, tz = base2camera[:3, 3]
    print("\n基坐标到相机的变换（体轴ZYX欧拉角）：")
    print(f"平移分量 (mm): tx={tx:.3f}, ty={ty:.3f}, tz={tz:.3f}")
    print(f"旋转分量 (度): rx={rx:.3f}, ry={ry:.3f}, rz={rz:.3f}")
    
    # 步骤6: 验证标定精度
    print("\n步骤6: 验证标定精度")
    verify_calibration_by_axxb(camera_poses, valid_robot_poses, valid_indices, base2camera)
    
    # 步骤7: 保存结果
    print("\n步骤7: 保存标定结果")
    save_calibration_results(output_dir, camera_matrix, dist_coeffs, base2camera, base2camera, chessboard_size, square_size)
    
    print("\n" + "=" * 50)
    print("标定流程完成!")
    print("=" * 50)

    
    valid_cam_target = (100.0, 50.0, 200.0, 0.0, 0.0, 60.0)  # x,y,z,rx,ry,rz
    result = convert_cam_pose_to_robot(valid_cam_target, base2camera)


    print(f"机器人坐标系下目标位姿: {result}")

# 使用示例
def main():
    # 运行完整标定流程
    run_complete_calibration(
        image_folder="./calibration_images",  # 包含标定图像的文件夹
        pose_file="./calibration_images/pose.txt",  # 机器人位姿文件
        output_dir="./",  # 输出目录
        chessboard_size=(8, 11),  # 棋盘格角点数量
        square_size=20.0  # 方格实际尺寸(mm)
    )



main()



