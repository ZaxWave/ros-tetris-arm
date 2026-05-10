#!/usr/bin/env python3
"""
Generate professional technical diagrams for competition document.
All diagrams use consistent wireframe box-arrow style at 300 DPI.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Arc, Rectangle
import numpy as np
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'diagrams')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Global Style ──────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 10,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.15,
})

# Color Palette (professional navy-blue theme)
C = {
    'bg':          '#FAFBFC',
    'border':      '#2C3E50',
    'fill_main':   '#EBF0F5',
    'fill_accent': '#D4E6F1',
    'fill_decision':'#D5F5E3',
    'fill_exec':   '#FDEBD0',
    'fill_percept':'#E8DAEF',
    'fill_hw':     '#F2F3F4',
    'fill_dqn':    '#D6EAF8',
    'text':        '#1B2631',
    'text_sub':    '#566573',
    'arrow':       '#5D6D7E',
    'accent':      '#2471A3',
    'accent2':     '#1E8449',
    'accent3':     '#B03A2E',
}

BOX_STYLE = dict(boxstyle='round,pad=0.25', edgecolor=C['border'],
                 facecolor=C['fill_main'], linewidth=1.2)
BOX_ACCENT = dict(boxstyle='round,pad=0.25', edgecolor=C['accent'],
                  facecolor=C['fill_accent'], linewidth=1.5)

def new_fig(w=10, h=6.5):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    ax.set_facecolor(C['bg'])
    fig.patch.set_facecolor(C['bg'])
    return fig, ax

def box(ax, x, y, w, h, text, facecolor=C['fill_main'], edgecolor=C['border'],
        fontsize=9, fontweight='normal', text_color=C['text'], linewidth=1.2):
    """Draw a rounded box with centered text."""
    p = FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle='round,pad=0.3',
                       facecolor=facecolor, edgecolor=edgecolor, linewidth=linewidth, zorder=3)
    ax.add_patch(p)
    lines = text.split('\n')
    for i, line in enumerate(lines):
        ly = y - (len(lines) - 1) * 4.5 + i * 9
        ax.text(x, ly if len(lines) > 1 else y, line, ha='center', va='center',
                fontsize=fontsize, fontweight=fontweight, color=text_color, zorder=4)
    return p

def arrow(ax, x1, y1, x2, y2, color=C['arrow'], lw=1.5, style='->'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                connectionstyle='arc3,rad=0'), zorder=2)

def dashed_box(ax, x, y, w, h, label, color='#7F8C8D', lw=1.0):
    """Draw a dashed outline box with a label."""
    rect = Rectangle((x - w/2, y - h/2), w, h, fill=False, edgecolor=color,
                     linewidth=lw, linestyle='--', zorder=1)
    ax.add_patch(rect)
    ax.text(x - w/2 + 2.5, y + h/2 - 3, label, fontsize=7, color=color, va='top', zorder=5)
    return rect

def section_label(ax, x, y, text, color=C['text_sub']):
    ax.text(x, y, text, fontsize=11, fontweight='bold', color=color, ha='center', va='center')

def save(fig, name):
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path, facecolor=C['bg'], edgecolor='none')
    plt.close(fig)
    print(f'  Saved: {path}')

# ═══════════════════════════════════════════════════════════════
# 1. SYSTEM ARCHITECTURE DIAGRAM (3-Layer)
# ═══════════════════════════════════════════════════════════════
def draw_system_architecture():
    fig, ax = new_fig(12, 8.5)

    # ── Title ──
    ax.text(50, 97, 'System Architecture: Perception → Decision → Execution',
            fontsize=14, fontweight='bold', color=C['text'], ha='center')

    # ── Layer 3: Perception (Top, y=65-85) ──
    dashed_box(ax, 50, 75, 92, 24, 'Perception Layer', color=C['accent'])
    box(ax, 18, 78, 23, 10, 'RealSense D435\nRGB-D Camera', C['fill_percept'], C['border'], 8)
    box(ax, 44, 78, 24, 10, 'YOLOv8\nInstance Segment', C['fill_percept'], C['border'], 8)
    box(ax, 70, 78, 26, 10, 'Template Matching\n5°+1° Contour IoU', C['fill_percept'], C['border'], 8)
    box(ax, 30, 68, 22, 8, 'Hand-Eye Calib.\nTsai-Lenz', C['fill_percept'], C['border'], 7)
    box(ax, 55, 68, 20, 8, 'Camera→Base\nTransform', C['fill_percept'], C['border'], 7)

    arrow(ax, 30, 78 + 5, 31.5, 78 + 5 + 2)  # D435 → YOLO
    arrow(ax, 56.5, 78, 56.5, 68 + 4)         # YOLO → Template
    arrow(ax, 70, 78 - 5, 65, 68 + 4)         # Template → Transform

    # ── Layer 2: Decision (Middle, y=42-62) ──
    dashed_box(ax, 50, 52, 92, 22, 'Decision Layer', color='#1E8449')
    box(ax, 30, 56, 25, 10, 'State Modeling\nBoard + Piece + Queue', C['fill_decision'], C['border'], 8)
    box(ax, 60, 56, 28, 10, 'Dellacherie Heuristic\n6-Dim Eval → Top-K', C['fill_decision'], C['border'], 8)
    box(ax, 45, 44, 24, 10, 'DQN Network\n211→512→256→128→400', C['fill_dqn'], C['accent'], 8)
    box(ax, 18, 44, 18, 10, 'Piece Classifier\nL/l/T/Z/z/I/O', C['fill_decision'], C['border'], 7)

    arrow(ax, 42.5, 56, 46, 56)            # State → Dellacherie
    arrow(ax, 60, 56 - 5, 57, 44 + 5)      # Dellacherie → DQN
    arrow(ax, 45, 44 + 5, 42, 56 - 5)      # feedback

    # ── Layer 1: Execution (Bottom, y=18-40) ──
    dashed_box(ax, 50, 29, 92, 24, 'Execution Layer', color=C['accent3'])
    box(ax, 22, 33, 24, 10, 'Motion Controller\nmoveJ_P Cartesian', C['fill_exec'], C['border'], 8)
    box(ax, 50, 33, 26, 10, 'Plan_State Monitor\n50Hz Polling · 10s Timeout', C['fill_exec'], C['border'], 8)
    box(ax, 76, 33, 24, 10, 'Arduino Pneumatic\nUSB Serial RUN/STOP', C['fill_exec'], C['border'], 8)
    box(ax, 36, 21, 22, 10, 'RM65-B Arm\n6-DOF ±0.02mm', C['fill_hw'], C['border'], 7)
    box(ax, 64, 21, 22, 10, 'Vacuum Gripper\n-85kPa <10ms', C['fill_hw'], C['border'], 7)

    arrow(ax, 22 + 12, 33 + 5, 50 - 13, 33 + 5)   # Motion → Monitor
    arrow(ax, 50 + 13, 33 + 5, 76 - 12, 33 + 5)    # Monitor → Arduino
    arrow(ax, 50, 33 - 5, 36, 21 + 5)               # Monitor → RM65
    arrow(ax, 76, 33 - 5, 64, 21 + 5)               # Arduino → Gripper

    # ── Inter-layer arrows ──
    arrow(ax, 30, 68 - 4, 30, 56 + 5, C['accent'], 1.8)
    arrow(ax, 55, 68 - 4, 55, 56 + 5, C['accent'], 1.8)
    arrow(ax, 18, 44 - 4, 22, 33 + 5, '#1E8449', 1.8)
    arrow(ax, 60, 44 - 4, 60, 33 + 5, '#1E8449', 1.8)

    # ── Side labels ──
    ax.text(4, 75, 'Perception', fontsize=9, fontweight='bold', color=C['accent'], rotation=90, va='center')
    ax.text(4, 52, 'Decision', fontsize=9, fontweight='bold', color='#1E8449', rotation=90, va='center')
    ax.text(4, 29, 'Execution', fontsize=9, fontweight='bold', color=C['accent3'], rotation=90, va='center')

    save(fig, 'fig1_system_architecture.png')


# ═══════════════════════════════════════════════════════════════
# 2. ROS NODE COMMUNICATION GRAPH
# ═══════════════════════════════════════════════════════════════
def draw_ros_node_graph():
    fig, ax = new_fig(11, 8)

    ax.text(50, 97, 'ROS Node Communication Architecture',
            fontsize=14, fontweight='bold', color=C['text'], ha='center')

    # Hardware block
    dashed_box(ax, 50, 84, 80, 14, 'Hardware', color='#7F8C8D')
    box(ax, 28, 86, 22, 6, 'RealSense D435\n/camera/*', C['fill_percept'], C['border'], 7)
    box(ax, 55, 86, 24, 6, 'RM65-B Arm\n/rm_driver/*', C['fill_exec'], C['border'], 7)
    box(ax, 78, 86, 20, 6, 'Arduino Uno\n/dev/ttyUSB0', C['fill_exec'], C['border'], 7)

    # ROS Nodes (middle)
    dashed_box(ax, 50, 55, 80, 32, 'ROS Nodes (Python 3.8)', color=C['accent'])

    # Node boxes
    box(ax, 18, 68, 28, 10, 'yolo_detector\nVision Pipeline Node', C['fill_percept'], C['border'], 8)
    box(ax, 50, 68, 30, 10, 'tetris_planner\nDecision Engine', C['fill_decision'], C['border'], 8)
    box(ax, 82, 68, 30, 10, 'motion_controller\nMoveJ_P Executor', C['fill_exec'], C['border'], 8)
    box(ax, 34, 48, 22, 8, 'transform\nTF Broadcaster', C['fill_percept'], C['border'], 7)
    box(ax, 62, 48, 24, 8, 'arduino_bridge\nSerial Bridge', C['fill_exec'], C['border'], 7)
    box(ax, 80, 48, 18, 8, 'takephoto\nCapture', C['fill_percept'], C['border'], 7)

    # Topics (bottom area)
    ax.text(50, 35, 'ROS Topics & Services', fontsize=10, fontweight='bold', color=C['text_sub'], ha='center')

    topics = [
        (12, '/camera/color/image_raw', C['accent']),
        (32, '/camera/aligned_depth', C['accent']),
        (52, '/vision/detections', C['accent']),
        (72, '/planning/place_pose', '#1E8449'),
        (88, '/rm_driver/MoveJ_P', C['accent3']),
    ]
    for x, name, col in topics:
        ax.text(x, 30, name, fontsize=6.5, color=col, ha='center',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=col, alpha=0.7, lw=0.8))

    # Arrows between nodes
    arrow(ax, 32, 68, 35, 68)   # yolo → planner
    arrow(ax, 65, 68, 67, 68)   # planner → motion
    arrow(ax, 18, 68 - 5, 34, 48 + 4)  # yolo → transform
    arrow(ax, 50, 68 - 5, 50, 48 + 4)  # planner → ?
    arrow(ax, 67, 68 - 5, 62, 48 + 4)   # motion → arduino

    # Hardware → Nodes
    arrow(ax, 28, 86 - 3, 18, 68 + 5, color=C['arrow'], lw=1.2, style='->')
    arrow(ax, 55, 86 - 3, 82, 68 + 5, color=C['arrow'], lw=1.2, style='->')

    save(fig, 'fig2_ros_node_graph.png')


# ═══════════════════════════════════════════════════════════════
# 3. VISION PIPELINE FLOW CHART
# ═══════════════════════════════════════════════════════════════
def draw_vision_pipeline():
    fig, ax = new_fig(12, 7.5)

    ax.text(50, 97, 'Vision Pipeline: RGB-D Capture → 6-DOF Grasp Pose',
            fontsize=14, fontweight='bold', color=C['text'], ha='center')

    # Flow boxes arranged horizontally in two rows
    y_top, y_bot = 72, 48
    boxes_top = [
        (12, 'D435 Camera\nCapture', C['fill_hw']),
        (30, 'YOLOv8\nInstance Seg.', C['fill_percept']),
        (50, 'Mask → Contour\nArc-Length Resample', C['fill_percept']),
        (70, 'Template Match\nCoarse 5° → Fine 1°', C['fill_percept']),
        (88, 'Best Match\nIoU ≥ 0.85', C['fill_percept']),
    ]
    boxes_bot = [
        (16, 'Depth Align\nrs.align', C['fill_hw']),
        (36, 'Pixel → Camera\nIntrinsics', C['fill_percept']),
        (56, 'Hand-Eye\nTransform', C['fill_percept']),
        (76, '6-DOF Grasp\n(x,y,z,R,P,Y)', C['fill_exec']),
        (92, 'OFFSET_MAP\nClass-specific Offset', C['fill_exec']),
    ]

    for x, txt, fc in boxes_top:
        box(ax, x, y_top, 17, 13, txt, fc, C['border'], 7.5)
    for x, txt, fc in boxes_bot:
        box(ax, x, y_bot, 17, 13, txt, fc, C['border'], 7.5)

    # Arrows between top boxes
    for i in range(len(boxes_top)-1):
        arrow(ax, boxes_top[i][0] + 8.5, y_top, boxes_top[i+1][0] - 8.5, y_top, C['accent'], 1.5)

    # Arrows between bottom boxes
    for i in range(len(boxes_bot)-1):
        arrow(ax, boxes_bot[i][0] + 8.5, y_bot, boxes_bot[i+1][0] - 8.5, y_bot, C['accent'], 1.5)

    # Cross-layer arrows
    arrow(ax, 12, y_top - 6.5, 16, y_bot + 6.5, C['text_sub'], 1.2, '-')
    arrow(ax, 70, y_top - 6.5, 76, y_bot + 6.5, C['text_sub'], 1.2, '-')

    # Legend
    ax.text(50, 28, 'YOLOv8 mAP@0.5 = 93.5%  |  Template IoU ≥ 0.85  |  Grasp Success = 96.2%',
            fontsize=9, color=C['text_sub'], ha='center',
            bbox=dict(facecolor=C['fill_accent'], edgecolor=C['accent'], boxstyle='round,pad=0.4'))

    save(fig, 'fig3_vision_pipeline.png')


# ═══════════════════════════════════════════════════════════════
# 4. HYBRID DECISION FLOW
# ═══════════════════════════════════════════════════════════════
def draw_decision_flow():
    fig, ax = new_fig(12, 8)

    ax.text(50, 97, 'Hybrid Decision Strategy: Heuristic + Deep Reinforcement Learning',
            fontsize=14, fontweight='bold', color=C['text'], ha='center')

    # Inputs
    box(ax, 18, 82, 22, 10, 'Game State\nBoard Matrix (10×20)\n+ Piece Queue', C['fill_hw'], C['border'], 8)
    box(ax, 50, 82, 28, 10, 'Candidate Generation\nAll Valid Positions\nper Piece (≈400)', C['fill_accent'], C['border'], 8)
    box(ax, 82, 82, 22, 8, 'Action Space\n400-Dim\n(x, y, θ)', C['fill_accent'], C['border'], 7)

    arrow(ax, 29, 82, 36, 82)
    arrow(ax, 64, 82, 71, 82)

    # Phase 1: Heuristic
    dashed_box(ax, 50, 60, 88, 20, 'Phase 1 — Dellacherie Heuristic Filter', color='#1E8449')
    box(ax, 22, 65, 30, 10, '6-Dimensional Eval\nLanding Height · Rows Cleared\nHoles · Roughness\nWell Depth · Column Trans.', C['fill_decision'], C['border'], 7.5)
    box(ax, 54, 65, 25, 10, 'Score All Candidates\nLinear Weighted Sum\nSort Descending', C['fill_decision'], C['border'], 7.5)
    box(ax, 82, 65, 20, 10, 'Top-K Filter\nK = 10\nBest Positions', C['fill_decision'], C['border'], 7.5)

    arrow(ax, 37, 65, 41.5, 65)
    arrow(ax, 66.5, 65, 72, 65)

    # Phase 2: DQN
    dashed_box(ax, 50, 40, 88, 18, 'Phase 2 — DQN Long-term Optimization', color=C['accent'])
    box(ax, 25, 44, 25, 10, 'State Encoding\n211-Dim Feature Vector', C['fill_dqn'], C['accent'], 7.5)
    box(ax, 52, 44, 28, 10, 'DQN Forward\n3-Layer MLP\n512→256→128→Q(s,a)', C['fill_dqn'], C['accent'], 7.5)
    box(ax, 80, 44, 22, 10, 'ε-Greedy Select\nε=0.05 exploit\nSelect max Q', C['fill_dqn'], C['accent'], 7.5)

    arrow(ax, 37.5, 44, 38, 44)
    arrow(ax, 66, 44, 69, 44)

    # Output
    box(ax, 50, 22, 32, 10, 'Optimal Place Pose\n(x, y, θ)\nSent to Motion Controller', C['fill_exec'], C['border'], 9, 'bold')

    arrow(ax, 50, 44 - 5, 50, 22 + 5, C['accent3'], 2.0)
    arrow(ax, 25, 40 - 2, 22, 65 - 5, C['arrow'], 1.2, '-')  # feedback

    # Metrics
    ax.text(50, 8, 'Heuristic: 0.8ms/candidate  |  DQN: 2.3ms forward pass  |  Total Decision: <5ms',
            fontsize=8.5, color=C['text_sub'], ha='center')

    save(fig, 'fig4_decision_flow.png')


# ═══════════════════════════════════════════════════════════════
# 5. PICK-AND-PLACE SEQUENCE DIAGRAM
# ═══════════════════════════════════════════════════════════════
def draw_pick_place_sequence():
    fig, ax = new_fig(12, 7.5)

    ax.text(50, 97, 'Pick-and-Place Motion Sequence (9.8s Cycle)',
            fontsize=14, fontweight='bold', color=C['text'], ha='center')

    # Timeline
    ax.axhline(y=75, xmin=0.06, xmax=0.94, color=C['border'], lw=2, zorder=1)
    ax.text(3, 76, 't', fontsize=9, fontweight='bold', color=C['text'])

    # Phases
    phases = [
        (10,  '0.0s\nStart', C['fill_hw']),
        (22,  '1.2s\nApproach\nHome→Pre-grasp', C['fill_percept']),
        (36,  '2.8s\nGrasp\nLower & Suck', C['fill_exec']),
        (50,  '4.5s\nLift\nPre-grasp→Safe Z', C['fill_exec']),
        (65,  '6.2s\nTransport\nMove to Target', C['fill_exec']),
        (79,  '7.8s\nPlace\nLower & Release', C['fill_exec']),
        (91,  '9.0s\nReturn\nRetract to Home', C['fill_exec']),
    ]

    for x, txt, fc in phases:
        box(ax, x, 65, 14, 16, txt, fc, C['border'], 7)
        ax.plot(x, 75, 'o', color=C['accent'], markersize=8, zorder=3)

    # Phase arrows
    for i in range(len(phases) - 1):
        arrow(ax, phases[i][0] + 7, 75, phases[i+1][0] - 7, 75, C['accent'], 1.8)

    # Gripper state bar
    ax.text(2, 48, 'Gripper', fontsize=8, fontweight='bold', color=C['text_sub'])
    ax.barh(48, 38, height=3, left=22, color=C['fill_exec'], edgecolor=C['border'], linewidth=1)
    ax.barh(48, 14, height=3, left=65, color=C['fill_exec'], edgecolor=C['border'], linewidth=1)
    ax.text(41, 48, 'SUCK (RUN)', fontsize=7, color=C['text_sub'], ha='center', va='center')
    ax.text(72, 48, 'RELEASE (STOP)', fontsize=7, color=C['text_sub'], ha='center', va='center')

    # Plan_State feedback
    ax.text(2, 38, 'Plan_State', fontsize=8, fontweight='bold', color=C['text_sub'])
    ax.text(30, 38, '50 Hz Polling  ──  wait_for_move()  ──  10s Timeout Guard',
            fontsize=7.5, color=C['text_sub'], ha='center', va='center')

    # Key metrics below
    metrics_text = (
        'Approach 1.2s  |  Grasp 0.3s  |  Lift 0.5s  |  Transport 1.7s  |  Place 0.5s  |  Return 1.2s  |  Total Cycle 9.8s'
    )
    ax.text(50, 18, metrics_text, fontsize=8, color=C['text'], ha='center',
            bbox=dict(facecolor=C['fill_accent'], edgecolor=C['accent'], boxstyle='round,pad=0.5'))

    # Safety annotations
    ax.text(50, 5, 'Safety: Force Limit 50N  |  Collision Detection  |  Emergency Stop <10ms',
            fontsize=7.5, color=C['accent3'], ha='center')

    save(fig, 'fig5_pick_place_sequence.png')


# ═══════════════════════════════════════════════════════════════
# 6. DQN NETWORK ARCHITECTURE
# ═══════════════════════════════════════════════════════════════
def draw_dqn_architecture():
    fig, ax = new_fig(12, 7.5)

    ax.text(50, 97, 'DQN Network Architecture: 211-D State → 400-D Q-Values',
            fontsize=14, fontweight='bold', color=C['text'], ha='center')

    # Input layer
    box(ax, 10, 78, 16, 12, 'Input Layer\n211 Neurons\nState Features', C['fill_percept'], C['border'], 8, 'bold')

    # Hidden layers
    layers = [(30, 'Hidden 1', '512 Neurons\nReLU + BN', C['fill_dqn']),
              (50, 'Hidden 2', '256 Neurons\nReLU + BN', C['fill_dqn']),
              (70, 'Hidden 3', '128 Neurons\nReLU + BN', C['fill_dqn'])]

    for x, name, desc, fc in layers:
        box(ax, x, 78, 16, 12, f'{name}\n{desc}', fc, C['accent'], 8)

    # Output layer
    box(ax, 90, 78, 16, 12, 'Output Layer\n400 Neurons\nQ(s, a) Values', C['fill_exec'], C['border'], 8, 'bold')

    # Arrows between layers
    for x1, x2 in [(18, 22), (38, 42), (58, 62), (78, 82)]:
        arrow(ax, x1, 78, x2, 78, C['accent'], 2.0)

    # Feature breakdown
    ax.text(10, 63, 'State Features (211-D)', fontsize=9, fontweight='bold', color=C['text'])

    features = [
        'Board Matrix: 200-D (10×20 grid, one-hot occupancy)',
        'Piece Queue: 7-D (current + next 6 pieces, class encoding)',
        'Hole Count: 1-D',
        'Column Heights: 1-D (max height)',
        'Bumpiness: 1-D (sum of adj. height diffs)',
        'Lines Cleared: 1-D',
    ]
    for i, feat in enumerate(features):
        ax.text(12, 58 - i * 4.5, f'• {feat}', fontsize=7, color=C['text_sub'], va='center')

    # Training params
    params_text = (
        'Training: Experience Replay Buffer (10K)  |  Target Network (sync every 100 steps)  |  γ=0.99  |  lr=1e-4  |  Adam Optimizer'
    )
    ax.text(50, 30, params_text, fontsize=8, color=C['text'], ha='center',
            bbox=dict(facecolor=C['fill_accent'], edgecolor=C['accent'], boxstyle='round,pad=0.4'))

    # Q-value formula
    ax.text(50, 15, 'Bellman Update: Q(s,a) ← Q(s,a) + α[r + γ·max Q(s\',a\') − Q(s,a)]',
            fontsize=9, color=C['accent'], ha='center',
            bbox=dict(facecolor='white', edgecolor=C['accent'], boxstyle='round,pad=0.5'))

    # ε-greedy annotation
    ax.text(50, 5, 'ε-greedy: ε decays from 1.0 → 0.05 over 10K episodes',
            fontsize=8, color=C['text_sub'], ha='center')

    save(fig, 'fig6_dqn_architecture.png')


# ═══════════════════════════════════════════════════════════════
# 7. HAND-EYE CALIBRATION FLOW (bonus)
# ═══════════════════════════════════════════════════════════════
def draw_handeye_flow():
    fig, ax = new_fig(10, 7.5)

    ax.text(50, 97, 'Hand-Eye Calibration: Tsai-Lenz Algorithm',
            fontsize=14, fontweight='bold', color=C['text'], ha='center')

    steps = [
        (15, 82, 'Capture\nCalib Images\n(15-20 pairs)', C['fill_hw']),
        (35, 82, 'Detect\nChessboard\n(8×6 corners)', C['fill_percept']),
        (55, 82, 'Solve\nAX = XB\nTsai-Lenz', C['fill_decision']),
        (75, 82, 'Transform\nCamera→Base\nMatrix 4×4', C['fill_exec']),
        (90, 82, 'Validate\nReprojection\nError < 0.5px', C['fill_exec']),
    ]

    for x, y, txt, fc in steps:
        box(ax, x, y, 16, 13, txt, fc, C['border'], 7.5)

    for i in range(len(steps)-1):
        arrow(ax, steps[i][0] + 8, 82, steps[i+1][0] - 8, 82, C['accent'], 1.5)

    # AX = XB explanation
    ax.text(50, 65, 'Tsai-Lenz Core:  A · X = X · B',
            fontsize=12, fontweight='bold', color=C['accent'], ha='center')

    explanations = [
        'A: Robot end-effector pose change (from forward kinematics)',
        'B: Camera pose change (from chessboard detection)',
        'X: Unknown hand-eye transform (camera → end-effector)',
        'Solution: Two-step — rotation first (axis-angle), then translation (least squares)',
    ]
    for i, exp in enumerate(explanations):
        ax.text(50, 58 - i * 5, exp, fontsize=7.5, color=C['text_sub'], ha='center')

    ax.text(50, 32, 'Calibration Result: 6-DOF Transform with Position ±1.5mm  ·  Orientation ±0.5°',
            fontsize=9, color=C['text'], ha='center',
            bbox=dict(facecolor=C['fill_accent'], edgecolor=C['accent'], boxstyle='round,pad=0.5'))

    save(fig, 'fig7_handeye_calibration.png')


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print('Generating professional diagrams...')
    draw_system_architecture()
    draw_ros_node_graph()
    draw_vision_pipeline()
    draw_decision_flow()
    draw_pick_place_sequence()
    draw_dqn_architecture()
    draw_handeye_flow()
    print(f'Done! {len(os.listdir(OUTPUT_DIR))} diagrams saved to {OUTPUT_DIR}')
