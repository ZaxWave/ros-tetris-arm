# 第九届中国高校智能机器人创意大赛

专项赛一：基于ROS的单臂机器人 — 俄罗斯方块自动化拼接

## 项目简介

基于睿尔曼 RM65-B 六自由度协作机械臂与 Intel RealSense D435 深度相机，实现俄罗斯方块的全自动视觉识别、拼接决策与精准拾放。系统运行于 Ubuntu 20.04 + ROS Noetic。

## 目录结构

```
├── assets/images/         # 文档插图素材
├── docs/
│   ├── competition/       # 比赛规则、报名表、申报表
│   └── reports/           # 生成的技术报告 (.docx)
├── scripts/               # 文档生成脚本
├── rmrobot/
│   ├── control/           # 主控制脚本（运动控制、视觉流水线、坐标变换）
│   ├── handeye/           # 手眼标定（标定数据、标定脚本）
│   ├── tetris/yolov8/     # YOLOv8 实例分割模型与模板轮廓
│   ├── xipan/              # 气动吸盘串口控制（Arduino）
│   └── output/            # 运行时输出（已 gitignore）
└── .gitignore
```

## 系统架构

1. **视觉感知**：RealSense D435 → YOLOv8 实例分割 → 轮廓模板匹配（粗搜索 5° + 精搜索 1°）→ 像素转相机坐标
2. **坐标变换**：手眼标定矩阵 → 相机坐标系 → 机械臂基座坐标系
3. **拼接决策**：启发式评估 (Dellacherie) + 深度 Q 网络 (DQN) 混合架构
4. **运动控制**：Plan_State 反馈闭环 (50Hz 轮询) → MoveJ_P 笛卡尔空间轨迹执行

## 硬件配置

| 组件 | 型号 | 关键参数 |
|------|------|----------|
| 机械臂 | 睿尔曼 RM65-B | 6 DoF, 重复定位精度 ±0.02 mm |
| 深度相机 | Intel RealSense D435 | 1920×1080 @ 30fps |
| 计算平台 | Intel i7-9700 + RTX 2080 Ti | 16 GB RAM |
| 末端执行器 | 气动吸盘 (Arduino Uno) | 最大真空度 -85 kPa |
