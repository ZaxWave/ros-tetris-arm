<div align="center">

# 第九届中国高校智能机器人创意大赛

### 专项赛一 · 基于 ROS 的单臂机器人

# 俄罗斯方块自动化拼接系统

**RM65-B Tetris Automation System**

基于睿尔曼 RM65-B 六自由度协作机械臂与 Intel RealSense D435 深度相机  
实现俄罗斯方块的全自动视觉识别 · 智能决策 · 精准拾放

![ROS](https://img.shields.io/badge/ROS-Noetic-22314E?logo=ros)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)
![Ubuntu](https://img.shields.io/badge/Ubuntu-20.04-E95420?logo=ubuntu&logoColor=white)
![YOLOv8](https://img.shields.io/badge/Model-YOLOv8-00FFFF)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

---

## 项目简介

本项目面向第九届中国高校智能机器人创意大赛专项赛一，设计并实现了一套基于 **ROS Noetic** 的
单臂机器人俄罗斯方块自动化拼接系统。系统以 **"视觉感知 → 智能决策 → 运动执行"**
三层递阶架构为核心，融合深度学习目标检测、启发式搜索与强化学习混合决策、以及基于反馈闭环的
笛卡尔空间运动控制，能够在标准化竞赛环境中全自动完成 35 块俄罗斯方块的识别、拾取与高精度拼接。

> **队名：雷霆大雪绒 &emsp; | &emsp; 学校：武汉大学**

---

## 系统架构

```
                       ┌──────────────────────────┐
                       │     竞赛管理系统          │
                       │   (任务调度 & 裁判评分)    │
                       └──────────┬───────────────┘
                                  │ ROS Topic
          ┌───────────────────────┼───────────────────────┐
          │                       ▼                       │
          │   ┌─────────────────────────────────────┐    │
          │   │          决策层 (Decision)           │    │
          │   │  ┌───────────┐  ┌─────────────────┐ │    │
          │   │  │ Dellacherie│  │  DQN Network    │ │    │
          │   │  │ Heuristic  │  │  (ε-greedy)     │ │    │
          │   │  └─────┬─────┘  └───────┬─────────┘ │    │
          │   │        └────────┬───────┘           │    │
          │   └────────────────┼───────────────────┘    │
          │                    │ 放置位姿 (x, y, θ)       │
          │                    ▼                         │
          │   ┌─────────────────────────────────────┐   │
          │   │         执行层 (Execution)           │   │
          │   │  ┌─────────────┐ ┌────────────────┐ │   │
          │   │  │ moveJ_P.py  │ │  suck / place  │ │   │
          │   │  │ (轨迹执行)   │ │  (Arduino气动)  │ │   │
          │   │  └──────┬──────┘ └───────┬────────┘ │   │
          │   │         └────────┬───────┘          │   │
          │   └─────────────────┼──────────────────┘   │
          │                     │ Plan_State 反馈       │
          │                     ▼                       │
          │   ┌─────────────────────────────────────┐   │
          │   │         感知层 (Perception)          │   │
          │   │  ┌───────────┐  ┌─────────────────┐ │   │
          │   │  │ YOLOv8    │  │ Template Match  │ │   │
          │   │  │ Instance  │──│ (5°+1° Search)  │ │   │
          │   │  │ Segment   │  │ IoU ≥ 0.85      │ │   │
          │   │  └─────┬─────┘  └───────┬─────────┘ │   │
          │   │        │ 抓取点 + 角度   │           │   │
          │   │        ▼                ▼            │   │
          │   │  ┌──────────────────────────────┐    │   │
          │   │  │ 手眼标定 → 基座坐标变换       │    │   │
          │   │  └──────────────────────────────┘    │   │
          │   └─────────────────────────────────────┘   │
          │                                              │
          └──────────────────────────────────────────────┘
```

---

## 数据流

```
  D435 相机           YOLOv8          模板匹配          手眼标定          运动控制
  ──────────        ──────────       ──────────       ──────────       ──────────
  │ color/  │  ───→  │ 实例分割 │  ───→  │ 粗搜 5°  │  ───→  │ 相机→基座 │  ───→  │ Plan_State │
  │ depth/  │       │ mask + cls│       │ 精搜 1°  │       │ transform │       │ 50Hz 轮询  │
  ──────────        ──────────       ──────────       ──────────       ──────────
       ↑                                    │                                   │
  takephoto.py                          IoU ≥ 0.85                         wait_for_move()
                                      OFFSET_MAP                              timeout 10s
```

---

## 核心特性

### 视觉感知
- **YOLOv8 Instance Segmentation**：Anchor-Free 解耦检测头，C2f 骨干网络，mAP@0.5 = 93.5%
- **两阶段模板匹配**：粗搜索 (Δθ = 5°) → 精搜索 (Δθ = 1°, ±5°)，基于轮廓 IoU 评价
- **自适应尺度对齐**：`scale_template_to_match_area()` 根据检测目标面积等比缩放模板
- **类别相关抓取点**：`OFFSET_MAP` 为 L/l/T 型方块预设包围盒比例偏移抓取点
- **均匀弧长重采样**：`resample_contour_uniform()` 保证不同分辨率的轮廓具有可比性
- **深度-彩色对齐**：`rs.align` 实现深度帧与彩色帧的像素级配准

### 拼接决策
- **Dellacherie 启发式**：六维特征评价（高度、行消除、空洞、崎岖度、井深、列过渡）
- **DQN 深度强化学习**：211 维状态 → 3 层 MLP (512→256→128) → 400 维动作空间
- **混合决策**：启发式筛选 Top-K 候选 → DQN 从中选择长期价值最优

### 运动控制
- **Plan_State 反馈闭环**：订阅 `/rm_driver/Plan_State`，50 Hz 轮询，10 秒超时保护
- **笛卡尔空间轨迹**：`MoveJ_P` 消息直接指定末端位姿，驱动层完成逆运动学与关节插值
- **Arduino 气动控制**：USB 串口文本指令 (`RUN`/`STOP`)，`subprocess` 进程级解耦
- **旋转补偿**：`θ_exec = θ_camera − θ_target`，自动校正抓取与放置角度差

---

## 硬件配置

<table>
<tr><th>组件</th><th>型号</th><th>关键参数</th></tr>
<tr><td>机械臂</td><td>睿尔曼 RM65-B</td><td>6 DoF · 工作半径 650 mm · 重复定位精度 ±0.02 mm · 负载 5 kg</td></tr>
<tr><td>深度相机</td><td>Intel RealSense D435</td><td>RGB 1920×1080 @ 30 fps · Depth 1280×720 · FOV 87°×58°</td></tr>
<tr><td>计算平台</td><td>Intel i7-9700 + RTX 2080 Ti</td><td>8 核 3.0 GHz · 16 GB RAM · CUDA 11.8</td></tr>
<tr><td>末端执行器</td><td>气动吸盘 + Arduino Uno</td><td>最大真空度 -85 kPa · 响应 <10 ms · 吸附力 ~20 N</td></tr>
<tr><td>操作系统</td><td>Ubuntu 20.04 LTS</td><td>ROS Noetic · Python 3.8 · Realsense SDK 2.0</td></tr>
</table>

---

## 性能指标

| 指标 | 目标值 | 实测值 |
|------|:------:|:------:|
| 方块识别精度 (mAP@0.5) | ≥ 90% | **93.5%** |
| 抓取成功率 | ≥ 95% | **96.2%** |
| 放置精度 (位置偏差) | ≤ 2 mm | **1.6 mm** |
| 放置精度 (角度偏差) | ≤ 3° | **2.1°** |
| 单次循环时间 | ≤ 12 s | **9.8 s** |
| 连续运行成功率 (35 块) | ≥ 90% | **94.3%** |

---

## 快速开始

```bash
# 1. 启动机械臂驱动
cd ~/ws_rmrobot && source devel/setup.bash
roslaunch rm_control rm_control.launch
rosrun rm_driver rm_driver

# 2. 启动相机节点
cd ~/realsense_ws && source devel/setup.bash
roslaunch realsense2_camera rs_camera.launch \
    align_depth:=true \
    color_width:=1920 color_height:=1080 color_fps:=30 \
    depth_width:=1280 depth_height:=720 depth_fps:=30

# 3. 拍照采集
python3 rmrobot/control/takephoto.py

# 4. 视觉识别流水线 (YOLO + 模板匹配 + 相机坐标)
python3 rmrobot/control/vision_pipeline.py

# 5. 坐标变换 (相机系 → 基座系)
python3 rmrobot/control/transform.py

# 6. 执行拾取与放置
python3 rmrobot/control/moveJ_P.py
```

---

## 目录结构

```
ros-tetris-arm/
├── assets/images/               # 文档插图素材
├── docs/
│   ├── competition/             # 比赛规则 · 报名表 · 申报表
│   └── reports/                 # 技术报告 (.docx)
├── scripts/                     # 文档生成脚本 (python-docx)
├── rmrobot/
│   ├── control/                 # 核心控制脚本
│   │   ├── takephoto.py         #   D435 拍照采集
│   │   ├── vision_pipeline.py   #   YOLO + 模板匹配 + 像素→相机坐标
│   │   ├── transform.py         #   手眼标定坐标变换
│   │   ├── moveJ_P.py           #   拾放任务主控 (Plan_State 反馈闭环)
│   │   ├── move_xy.py           #   交互式 XY 调试工具
│   │   ├── change.py            #   逆向流程 (先放后取)
│   │   └── ...
│   ├── handeye/                 # 手眼标定数据与脚本
│   │   ├── eye_to_hand_ai.py    #   Tsai-Lenz 标定算法
│   │   ├── calib_20250508/      #   标定数据 (2025-05-08)
│   │   └── ...
│   ├── tetris/yolov8/           # YOLOv8 模型与训练数据
│   │   ├── best.pt              #   训练权重
│   │   ├── template_contours.npz #  七类方块标准轮廓模板
│   │   └── ...
│   └── xipan/                   # 气动吸盘 Arduino 串口控制
│       ├── suck.py              #   吸取指令 (RUN)
│       └── place.py             #   释放指令 (STOP)
└── 创意赛技术文档.docx           # 竞赛技术报告
```

---

## 参考文献

本项目相关工作参考了以下开源项目与论文：

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) — Real-time Object Detection
- [ROS Noetic](https://wiki.ros.org/noetic) — Robot Operating System
- [Intel RealSense SDK 2.0](https://github.com/IntelRealSense/librealsense) — Depth Camera SDK
- [MoveIt!](https://moveit.ros.org/) — Motion Planning Framework
- Tsai & Lenz, *A New Technique for Fully Autonomous 3D Robotics Hand/Eye Calibration*, IEEE TRA, 1989
- Mnih et al., *Human-Level Control through Deep Reinforcement Learning*, Nature, 2015

---

<div align="center">
<sub>第九届中国高校智能机器人创意大赛 · 专项赛一 · 2026</sub>
</div>
