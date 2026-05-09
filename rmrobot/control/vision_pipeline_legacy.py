#!/usr/bin/env python3
"""
拍照 → YOLO检测 → 模板匹配 → 相机坐标（D435，一步完成）
直接读 color/ depth/ 目录，检测+匹配+坐标转换全在内存里完成，不落中间文件。
"""

import os
import cv2
import numpy as np
from math import cos, sin, radians
from ultralytics import YOLO

# ============================================
# D435 相机内参
# ============================================
# FX = 1347.7448018527473
# FY = 1345.846468627119
# CX = 976.9897843406013
# CY = 565.441474784754

FX=1365.3359375  
FY=1364.189208984375
CX=977.5836181640625  
CY=547.8250122070312


# ============================================
# 路径配置
# ============================================
MODEL_PATH    = "/home/zhy/rmrobot/tetris/yolov8/best.pt"
TEMPLATE_PATH = "/home/zhy/rmrobot/tetris/yolov8/template_contours.npz"
COLOR_DIR     = "/home/zhy/rmrobot/output/color"
DEPTH_DIR     = "/home/zhy/rmrobot/output/depth"
SAVE_DIR      = "/home/zhy/rmrobot/output/camerabase"
os.makedirs(SAVE_DIR, exist_ok=True)

IMG_W, IMG_H = 1920, 1080

CLASS_NAMES = {0: "O", 1: "L", 2: "l", 3: "T", 4: "z", 5: "Z", 6: "I"}
OFFSET_MAP = {
    "L": (-10, 30), "l": (10, 30), "T": (0, 0),
    "Z": (0, 0), "z": (0, 0), "O": (0, 0), "I": (0, 0),
}

# ============================================
# 工具函数
# ============================================
def rotate_points(points, angle_deg, center=(0, 0)):
    angle_rad = radians(angle_deg)
    rot_mat = np.array([[cos(angle_rad), -sin(angle_rad)],
                        [sin(angle_rad),  cos(angle_rad)]], dtype=np.float32)
    return np.dot(points - center, rot_mat.T) + center

def contour_centroid(contour):
    M = cv2.moments(contour)
    if M['m00'] == 0:
        return np.array([0, 0])
    return np.array([M['m10'] / M['m00'], M['m01'] / M['m00']])

def contour_to_mask(contour, shape=(256, 256)):
    mask = np.zeros(shape, dtype=np.uint8)
    cv2.fillPoly(mask, [contour.astype(np.int32)], 1)
    return mask

def iou_between_contours(contour1, contour2, mask_shape=(256, 256)):
    mask1 = contour_to_mask(contour1, mask_shape)
    mask2 = contour_to_mask(contour2, mask_shape)
    intersection = np.logical_and(mask1, mask2).sum()
    union = np.logical_or(mask1, mask2).sum()
    return intersection / union if union > 0 else 0

def scale_template_to_match_area(template, target_contour):
    template_area = cv2.contourArea(template.astype(np.float32))
    target_area = cv2.contourArea(target_contour.astype(np.float32))
    if template_area <= 0 or target_area <= 0:
        return template
    scale_factor = np.sqrt(target_area / template_area)
    template_center = contour_centroid(template)
    return (template - template_center) * scale_factor + template_center

def resample_contour_uniform(contour, num_points=100):
    contour = contour.reshape(-1, 2)
    edges = np.roll(contour, -1, axis=0) - contour
    edge_lengths = np.linalg.norm(edges, axis=1)
    perimeter = edge_lengths.sum()
    if perimeter == 0:
        return np.repeat(contour[0:1], num_points, axis=0).astype(np.float32)
    sample_distances = np.linspace(0, perimeter, num_points, endpoint=False)
    resampled = []
    edge_index, acc_length = 0, edge_lengths[0]
    for dist in sample_distances:
        while dist > acc_length and edge_index < len(edge_lengths) - 1:
            edge_index += 1
            acc_length += edge_lengths[edge_index]
        prev_acc = acc_length - edge_lengths[edge_index]
        ratio = (dist - prev_acc) / edge_lengths[edge_index] if edge_lengths[edge_index] > 0 else 0
        resampled.append(contour[edge_index] + ratio * edges[edge_index])
    return np.array(resampled, dtype=np.float32)

def resample_contour(contour, num_points=100):
    return resample_contour_uniform(contour, num_points)

def normalize_template_contour(contour):
    if len(contour.shape) == 3 and contour.shape[1] == 1:
        contour = contour.squeeze(1)
    return contour.reshape(-1, 2).astype(np.float32)

def draw_closed_contour(image, contour, color, thickness=2):
    contour = contour.astype(np.int32)
    for i in range(len(contour)):
        cv2.line(image, tuple(contour[i]), tuple(contour[(i+1) % len(contour)]), color, thickness)

def normalize_contour_for_iou(contour, target_size=256):
    contour = contour - contour_centroid(contour)
    min_xy = contour.min(axis=0)
    max_xy = contour.max(axis=0)
    wh = max_xy - min_xy
    if (wh == 0).any():
        return np.zeros_like(contour)
    scale = target_size / max(wh)
    return ((contour - min_xy) * scale).astype(np.int32)

def pixel2camera(u, v, depth):
    X = (u - CX) * depth / FX
    Y = (v - CY) * depth / FY
    Z = depth
    return X, Y, Z

def match_template(detected_contour, class_name):
    """模板匹配：返回 (best_rotated, best_angle, best_score, final_grasp_point, initial_aligned)"""
    template = template_contours[class_name].copy()
    template = scale_template_to_match_area(template, detected_contour)

    detected_resampled = resample_contour(detected_contour)
    template_resampled = resample_contour(template)

    template_center = contour_centroid(template_resampled)
    centered_template = template_resampled - template_center
    target_center = contour_centroid(detected_resampled)

    initial_aligned = template_resampled - template_center + target_center

    norm1 = normalize_contour_for_iou(detected_resampled)

    # 粗搜索（5°步长）
    best_score, best_angle, best_rotated = -1, 0, None
    for angle in range(0, 360, 5):
        rotated = rotate_points(centered_template, angle)
        aligned = rotated + target_center
        norm2 = normalize_contour_for_iou(aligned)
        score = iou_between_contours(norm1, norm2)
        if score > best_score:
            best_score, best_angle, best_rotated = score, angle, aligned.copy()

    # 精细搜索（1°步长，±5°）
    for angle in range(max(best_angle - 5, 0), min(best_angle + 5, 359) + 1, 1):
        rotated = rotate_points(centered_template, angle)
        aligned = rotated + target_center
        norm2 = normalize_contour_for_iou(aligned)
        score = iou_between_contours(norm1, norm2)
        if score > best_score:
            best_score, best_angle, best_rotated = score, angle, aligned.copy()

    if best_rotated is None:
        return None, 0, 0, None, None

    # 计算抓取点
    dx, dy = OFFSET_MAP.get(class_name, (0, 0))
    offset_point = template_center + np.array([dx, dy])
    rotated_offset = rotate_points(offset_point.reshape(1, 2), best_angle, center=template_center).reshape(2,)
    final_grasp_point = rotated_offset + (target_center - template_center)

    return best_rotated, best_angle, best_score, final_grasp_point, initial_aligned

# ============================================
# 加载资源
# ============================================
print("Loading YOLO model...")
model = YOLO(MODEL_PATH)
print(f"Model loaded: {MODEL_PATH}")

template_data = np.load(TEMPLATE_PATH, allow_pickle=True)
template_contours = {}
for k, v in template_data.items():
    template_contours[k] = normalize_template_contour(v)
    print(f"Loaded template '{k}': {template_contours[k].shape}")
print(f"Total {len(template_contours)} templates loaded.\n")

# ============================================
# 主处理：遍历 color 目录下所有图片
# ============================================
processed_count = 0

for fname in sorted(os.listdir(COLOR_DIR)):
    if not fname.lower().endswith((".png", ".jpg", ".jpeg")):
        continue

    name = os.path.splitext(fname)[0]  # e.g. 1, 2, 3

    color_path  = os.path.join(COLOR_DIR, fname)
    depth_path  = os.path.join(DEPTH_DIR, fname)
    vis_path    = os.path.join(SAVE_DIR, f"{name}.jpg")
    output_path = os.path.join(SAVE_DIR, f"{name}.txt")

    # 读深度图
    if not os.path.exists(depth_path):
        print(f"[SKIP] 深度图缺失: {depth_path}")
        continue
    raw_depth = cv2.imread(depth_path, cv2.IMREAD_UNCHANGED)
    if raw_depth is None:
        print(f"[SKIP] 无法读取深度图: {depth_path}")
        continue
    depth_map = raw_depth.astype(np.float32) * 0.001 if raw_depth.dtype == np.uint16 else raw_depth.astype(np.float32)

    # 读彩色图
    image = cv2.imread(color_path)
    if image is None:
        print(f"[SKIP] 无法读取图像: {color_path}")
        continue

    # ---------- YOLO 检测 ----------
    results = model(color_path, imgsz=IMG_W, verbose=False)
    result = results[0]

    if result.masks is None:
        print(f"[SKIP] {name}: 未检测到任何目标")
        continue

    camcoords_lines = []
    detection_count = 0

    for idx, (mask_xy, cls_id_tensor) in enumerate(zip(result.masks.xy, result.boxes.cls), start=1):
        cls_id = int(cls_id_tensor.item())
        class_name = CLASS_NAMES.get(cls_id)
        if class_name not in template_contours:
            continue

        # mask_xy 已经是绝对像素坐标的顶点
        polygon = mask_xy.astype(np.int32)
        if len(polygon) < 4:
            continue

        # ---------- 模板匹配 ----------
        best_rotated, best_angle, best_score, grasp_point, initial_aligned = match_template(polygon, class_name)
        if grasp_point is None:
            continue

        u, v = int(grasp_point[0]), int(grasp_point[1])

        # ---------- 深度查表 + 像素→相机坐标 ----------
        if 0 <= v < depth_map.shape[0] and 0 <= u < depth_map.shape[1]:
            d = float(depth_map[v, u])
            cam_x, cam_y, cam_z = pixel2camera(u, v, d)
            camcoords_lines.append(f"{class_name} {cam_x:.6f} {cam_y:.6f} {cam_z:.6f} {best_angle}")
        else:
            print(f"[WARN] 像素({u},{v}) 越界，跳过")
            continue

        # ---------- 可视化 ----------
        draw_closed_contour(image, polygon, (0, 255, 0), thickness=2)         # 绿色：检测轮廓
        # 蓝色虚线：模板初始位姿（未旋转）
        init_pts = initial_aligned.astype(np.int32)
        for i in range(len(init_pts)):
            cv2.line(image, tuple(init_pts[i]), tuple(init_pts[(i+1) % len(init_pts)]), (255, 0, 0), 1)
        draw_closed_contour(image, best_rotated.astype(np.int32), (0, 0, 255), thickness=2)  # 红色：匹配模板
        cv2.circle(image, (u, v), 6, (255, 0, 0), -1)                       # 蓝色：抓取点
        info_text = f"{idx}:{class_name} {best_angle}deg Z={cam_z:.3f}m"
        cv2.putText(image, info_text, (u + 10, v - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(image, info_text, (u + 10, v - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

        print(f"[{name}] {class_name} angle={best_angle}deg score={best_score:.3f} "
              f"pixel=({u},{v}) depth={d:.3f}m camera=({cam_x:.3f},{cam_y:.3f},{cam_z:.3f})")
        detection_count += 1

    # 保存
    if camcoords_lines:
        # 图例
        cv2.putText(image, "Green: Detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(image, "Blue: Template Initial", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        cv2.putText(image, "Red: Template Matched", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        with open(output_path, 'w') as f:
            f.write("\n".join(camcoords_lines) + "\n")
        cv2.imwrite(vis_path, image)
        print(f"[DONE] {name}: {detection_count} targets → {output_path}")
    else:
        print(f"[SKIP] {name}: 无法匹配任何模板")

    processed_count += 1

print(f"\nAll done. Processed {processed_count} images, results in {SAVE_DIR}")
