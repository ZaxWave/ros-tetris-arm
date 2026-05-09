import os
import cv2
import numpy as np
from math import cos, sin, radians



# ---------- 工具函数 ----------
def rotate_points(points, angle_deg, center=(0, 0)):
    """将点集绕指定中心旋转一定角度"""
    angle_rad = radians(angle_deg)
    rot_mat = np.array([[cos(angle_rad), -sin(angle_rad)],
                        [sin(angle_rad),  cos(angle_rad)]], dtype=np.float32)
    return np.dot(points - center, rot_mat.T) + center

def contour_centroid(contour):
    """计算轮廓质心"""
    M = cv2.moments(contour)
    if M['m00'] == 0:
        return np.array([0, 0])
    return np.array([M['m10'] / M['m00'], M['m01'] / M['m00']])

def contour_to_mask(contour, shape=(256, 256)):
    """将轮廓转为二值掩膜"""
    mask = np.zeros(shape, dtype=np.uint8)
    cv2.fillPoly(mask, [contour.astype(np.int32)], 1)
    return mask

def iou_between_contours(contour1, contour2, mask_shape=(256, 256)):
    """计算两个轮廓的 IoU"""
    mask1 = contour_to_mask(contour1, mask_shape)
    mask2 = contour_to_mask(contour2, mask_shape)
    intersection = np.logical_and(mask1, mask2).sum()
    union = np.logical_or(mask1, mask2).sum()
    if union == 0:
        return 0
    return intersection / union

def scale_template_to_match_area(template, target_contour):
    """根据面积缩放模板轮廓，使其与目标轮廓面积一致"""
    template_area = cv2.contourArea(template.astype(np.float32))
    target_area = cv2.contourArea(target_contour.astype(np.float32))

    if template_area <= 0 or target_area <= 0:
        return template  # 不缩放

    scale_factor = np.sqrt(target_area / template_area)
    template_center = contour_centroid(template)
    scaled = (template - template_center) * scale_factor + template_center
    return scaled


def resample_contour_uniform(contour, num_points=100):
    """
    对闭合多边形轮廓 contour 进行均匀重采样，返回 num_points 个点
    contour: shape (N,2) 多边形顶点，闭合（第一个点和最后一个点可以不同）
    num_points: 目标采样点数
    """
    contour = contour.reshape(-1, 2)
    # 计算每条边向量和长度
    edges = np.roll(contour, -1, axis=0) - contour  # (N,2)
    edge_lengths = np.linalg.norm(edges, axis=1)  # (N,)
    perimeter = edge_lengths.sum()
    if perimeter == 0:
        return np.repeat(contour[0:1], num_points, axis=0).astype(np.float32)
    
    # 计算每个采样点在周长上的位置，均匀分布
    sample_distances = np.linspace(0, perimeter, num_points, endpoint=False)
    
    resampled_points = []
    edge_index = 0
    acc_length = edge_lengths[0]

    for dist in sample_distances:
        # 找出采样点在哪条边上
        while dist > acc_length and edge_index < len(edge_lengths) - 1:
            edge_index += 1
            acc_length += edge_lengths[edge_index]
        prev_acc_length = acc_length - edge_lengths[edge_index]

        # 当前点在该边上的比例
        ratio = (dist - prev_acc_length) / edge_lengths[edge_index] if edge_lengths[edge_index] > 0 else 0
        p = contour[edge_index] + ratio * edges[edge_index]
        resampled_points.append(p)
    
    return np.array(resampled_points, dtype=np.float32)

def resample_contour(contour, num_points=100):
    return resample_contour_uniform(contour, num_points)


def normalize_template_contour(contour):
    """标准化模板轮廓格式"""
    # 处理OpenCV轮廓格式 (n, 1, 2) -> (n, 2)
    if len(contour.shape) == 3 and contour.shape[1] == 1:
        contour = contour.squeeze(1)
    contour = contour.reshape(-1, 2)
    return contour.astype(np.float32)

def draw_closed_contour(image, contour, color, thickness=2):
    """手动绘制闭合轮廓，确保所有点都连接"""
    contour = contour.astype(np.int32)
    for i in range(len(contour)):
        pt1 = tuple(contour[i])
        pt2 = tuple(contour[(i + 1) % len(contour)])
        cv2.line(image, pt1, pt2, color, thickness)


# ---------- 加载模板 ----------
template_path = r"/home/zhy/rmrobot/tetris/yolov8/template_contours.npz"
try:
    template_data = np.load(template_path, allow_pickle=True)
    template_contours = {}
    
    # 标准化所有模板轮廓格式
    for k, v in template_data.items():
        normalized_contour = normalize_template_contour(v)
        template_contours[k] = normalized_contour
        print(f"✅ 加载模板 '{k}': {normalized_contour.shape} 点数: {len(normalized_contour)}")
    
    print(f"🎯 成功加载 {len(template_contours)} 个模板")
except Exception as e:
    print(f"❌ 模板加载失败: {e}")
    exit(1)

# ---------- 配置路径 ----------
image_dir = r"/home/zhy/rmrobot/output/color"
label_dir = r"/home/zhy/rmrobot/tetris/yolov8/runs/tetris_pred/labels"
save_dir = r"/home/zhy/rmrobot/output/centroid"
os.makedirs(save_dir, exist_ok=True)

# 类别定义与偏移
class_names = {0: "O", 1: "L", 2: "l", 3: "T", 4: "z", 5: "Z", 6: "I"}
offset_map = {
    "L": (-10, 30),
    "l": (10, 30),
    "T": (0, 0),
    "Z": (0, 0),
    "z": (0, 0),
    "O": (0, 0),
    "I": (0, 0)
}

img_width, img_height = 1920, 1080

scale_size = 256  # 所有轮廓统一缩放到 256x256 区域
# 平移中心、缩放到固定范围（单位框）对齐
def normalize_contour_for_iou(contour, target_size=256):
    contour = contour - contour_centroid(contour)
    min_xy = contour.min(axis=0)
    max_xy = contour.max(axis=0)
    wh = max_xy - min_xy
    if (wh == 0).any():
        return np.zeros_like(contour)
    scale = target_size / max(wh)
    return ((contour - min_xy) * scale).astype(np.int32)

# ---------- 主处理 ----------
processed_count = 0
for txt_file in os.listdir(label_dir):
    if not txt_file.endswith(".txt"):
        continue

    name = os.path.splitext(txt_file)[0]
    image_path = os.path.join(image_dir, f"{name}.png")
    label_path = os.path.join(label_dir, txt_file)
    save_path = os.path.join(save_dir, f"{name}.jpg")

    if not os.path.exists(image_path):
        continue

    image = cv2.imread(image_path)
    if image is None:
        print(f"⚠️ 无法读取图像: {image_path}")
        continue

    detection_count = 0
    
    with open(label_path, 'r') as f:

        center_info_lines = []  # 每张图像保存的所有中心点信息

        for idx, line in enumerate(f, start=1):
            parts = line.strip().split()
            if len(parts) < 7:
                continue

            cls_id = int(parts[0])
            class_name = class_names.get(cls_id, None)
            if class_name not in template_contours:
                print(f"⚠️ 跳过未知类别: {class_name} (ID: {cls_id})")
                continue

            polygon = list(map(float, parts[1:]))
            polygon = polygon[:len(polygon) // 2 * 2]
            if len(polygon) < 6:
                continue

            # 转换为绝对坐标
            abs_points = []
            for i in range(0, len(polygon), 2):
                x = int(polygon[i] * img_width)
                y = int(polygon[i + 1] * img_height)
                abs_points.append([x, y])
            detected_contour = np.array(abs_points, dtype=np.int32)

            # 获取并处理模板
            # template = template_contours[class_name].copy()
            template = template_contours[class_name].copy()
            template = scale_template_to_match_area(template, detected_contour) 

            
            # 重采样以便比较
            detected_resampled = resample_contour(detected_contour, num_points=100)
            template_resampled = resample_contour(template, num_points=100)

            template_center = contour_centroid(template_resampled)
            centered_template = template_resampled - template_center
            target_center = contour_centroid(detected_resampled)

            # 计算模板初始姿态（移动到目标中心，但不旋转）
            initial_template_aligned = template_resampled - template_center + target_center

            # 先用5度步长粗搜索
            best_score = -1
            best_angle = 0
            best_rotated = None

            for angle in range(0, 360, 5):
                rotated = rotate_points(centered_template, angle)
                aligned = rotated + target_center

                norm1 = normalize_contour_for_iou(detected_resampled)
                norm2 = normalize_contour_for_iou(aligned)

                score = iou_between_contours(norm1, norm2, mask_shape=(scale_size, scale_size))

                if score > best_score:
                    best_score = score
                    best_angle = angle
                    best_rotated = aligned.copy()

            # 在粗搜索结果附近做1度步长精细搜索，±5度范围
            fine_best_score = best_score
            fine_best_angle = best_angle
            fine_best_rotated = best_rotated

            start_angle = max(best_angle - 5, 0)
            end_angle = min(best_angle + 5, 359)

            for angle in range(start_angle, end_angle + 1, 1):
                rotated = rotate_points(centered_template, angle)
                aligned = rotated + target_center

                norm2 = normalize_contour_for_iou(aligned)

                score = iou_between_contours(norm1, norm2, mask_shape=(scale_size, scale_size))

                if score > fine_best_score:
                    fine_best_score = score
                    fine_best_angle = angle
                    fine_best_rotated = aligned.copy()

            # 用精细搜索的结果覆盖粗搜索结果
            best_score = fine_best_score
            best_angle = fine_best_angle
            best_rotated = fine_best_rotated


            if best_rotated is None:
                continue

            final_center = contour_centroid(best_rotated.astype(np.int32))


            # 原始模板质心
            template_center = contour_centroid(template_resampled)

            # 偏移量
            dx, dy = offset_map.get(class_name, (0, 0))
            offset_point = template_center + np.array([dx, dy])  # 偏移点（相对模板质心偏移）

            # 将偏移点绕模板质心旋转best_angle度
            rotated_offset_point = rotate_points(offset_point.reshape(1,2), best_angle, center=template_center).reshape(2,)

            # 最终吸取点位置 = 旋转后的偏移点 + (检测轮廓质心 - 模板质心)
            target_center = contour_centroid(detected_resampled)
            final_grasp_point = rotated_offset_point + (target_center - template_center)

            print(f"class={class_name}, best_angle={best_angle}, final_grasp_point={final_grasp_point}")

            # 绘制可视化
            # 1. 绘制检测到的轮廓 (绿色)
            draw_closed_contour(image, detected_contour, (0, 255, 0), thickness=2)
            
            # 2. 绘制模板初始姿态 (蓝色虚线)
            initial_template_points = initial_template_aligned.astype(np.int32)
            for i in range(len(initial_template_points)):
                pt1 = tuple(initial_template_points[i])
                pt2 = tuple(initial_template_points[(i + 1) % len(initial_template_points)])
                # 绘制虚线效果
                cv2.line(image, pt1, pt2, (255, 0, 0), 1)
            
            # 3. 绘制匹配后的最佳模板姿态 (红色)
            best_template_points = best_rotated.astype(np.int32)
            draw_closed_contour(image, best_template_points, (0, 0, 255), thickness=2)
            
            # 4. 绘制质心和信息
            cv2.circle(image, tuple(final_grasp_point.astype(int)), 6, (255, 0, 0), -1)
            # 保存中心点信息到列表
            info_line = f"{class_name} {best_angle}deg Score:{best_score:.3f} Center:({int(final_grasp_point[0])},{int(final_grasp_point[1])})"
            center_info_lines.append(info_line)

            # 5. 在质心附近显示角度信息
            info_text = f"{idx}:{class_name} {best_angle}deg (Score:{best_score:.3f})"
            cv2.putText(image, info_text, (int(final_grasp_point[0] + 10), int(final_grasp_point[1] - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(image, info_text, (int(final_grasp_point[0] + 10), int(final_grasp_point[1] - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

            print(f"[{name}] 类别:{class_name} 匹配角度: {best_angle}° 匹配得分: {best_score:.3f}")
            detection_count += 1

    # 添加图例
    if detection_count > 0:
        legend_y = 30
        cv2.putText(image, "Green: Detected", (10, legend_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(image, "Blue: Template Initial", (10, legend_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        cv2.putText(image, "Red: Template Matched", (10, legend_y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    cv2.imwrite(save_path, image)
    # 保存中心点信息到TXT
    txt_out_path = os.path.join(save_dir, f"{name}_centers.txt")
    with open(txt_out_path, 'w') as out_f:
        for line in center_info_lines:
            out_f.write(line + "\n")

    processed_count += 1
    
    if processed_count % 10 == 0:
        print(f"📊 已处理 {processed_count} 张图像...")

print(f"✅ 所有旋转中心、角度和模板初始姿态已可视化并保存到: {save_dir}")
print(f"📊 总共处理了 {processed_count} 张图像")