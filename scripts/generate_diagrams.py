#!/usr/bin/env python3
"""
Generate academic-style technical diagrams for competition document.
Clean monochrome wireframe style suitable for formal technical reports.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'diagrams')
os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'STSong'],
    'font.size': 9,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.2,
})

# Academic palette — restrained grayscale with subtle accent
C = {
    'bg':          'white',
    'border':      '#333333',
    'fill_main':   '#F8F8F8',
    'fill_acc':    '#EEEEEE',
    'fill_dark':   '#E0E0E0',
    'text':        '#222222',
    'text_sub':    '#555555',
    'arrow':       '#444444',
    'line':        '#333333',
}


def new_fig(w=10, h=7):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    return fig, ax


def box(ax, x, y, w, h, text, facecolor=C['fill_main'], edgecolor=C['border'],
        fontsize=8, bold=False, lw=1.0):
    p = FancyBboxPatch((x - w/2, y - h/2), w, h,
                       boxstyle='round,pad=0.2', facecolor=facecolor,
                       edgecolor=edgecolor, linewidth=lw, zorder=3)
    ax.add_patch(p)
    lines = text.split('\n')
    for i, line in enumerate(lines):
        dy = y - (len(lines) - 1) * 4.5 + i * 9
        ax.text(x, dy if len(lines) > 1 else y, line, ha='center', va='center',
                fontsize=fontsize, fontweight='bold' if bold else 'normal',
                color=C['text'], zorder=4)


def dashed_box(ax, x, y, w, h, label, lw=0.8):
    rect = Rectangle((x - w/2, y - h/2), w, h, fill=False, edgecolor='#777777',
                     linewidth=lw, linestyle='--', zorder=1)
    ax.add_patch(rect)
    if label:
        ax.text(x - w/2 + 2, y + h/2 - 2.5, label, fontsize=7, color='#777777',
                va='top', zorder=5)


def arrow(ax, x1, y1, x2, y2, lw=1.2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=C['arrow'], lw=lw), zorder=2)


def darrow(ax, x1, y1, x2, y2):
    """Dashed arrow for feedback/data flow."""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color='#888888', lw=0.8,
                                linestyle='dashed'), zorder=1)


def title(ax, text, y=97):
    ax.text(50, y, text, fontsize=12, fontweight='bold', color=C['text'], ha='center')


def save(fig, name):
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path, facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f'  {name}')


# ═══════════════════════════════════════════════════════════════
# 1. SYSTEM ARCHITECTURE
# ═══════════════════════════════════════════════════════════════
def draw_architecture():
    fig, ax = new_fig(12, 8)
    title(ax, 'System Architecture: Three-Layer Hierarchical Control')

    # ── Layer labels (left side) ──
    for y, lbl in [(76, 'Perception'), (53, 'Decision'), (30, 'Execution')]:
        ax.text(2.5, y, lbl, fontsize=9, fontweight='bold', color=C['text_sub'],
                rotation=90, va='center', ha='center')

    # Perception layer (top)
    dashed_box(ax, 50, 76, 92, 20, '')
    box(ax, 20, 80, 22, 10, 'RealSense D435\nRGB-D Camera')
    box(ax, 45, 80, 24, 10, 'YOLOv8\nInstance Segmentation')
    box(ax, 72, 80, 26, 10, 'Template Matching\nContour IoU ≥ 0.85')
    box(ax, 33, 68, 20, 8, 'Hand-Eye Calibration\nTsai-Lenz AX=XB')
    box(ax, 56, 68, 18, 8, 'Coordinate\nTransform')
    arrow(ax, 31, 80-5, 33, 68+4)
    arrow(ax, 45, 80-5, 45, 68+4)
    arrow(ax, 72-13, 80-5, 72-13, 68+4)

    # Decision layer (middle)
    dashed_box(ax, 50, 53, 92, 20, '')
    box(ax, 22, 57, 26, 10, 'State Modeling\nBoard + Piece + Queue')
    box(ax, 52, 57, 28, 10, 'Dellacherie Heuristic\n6-Dim Evaluation → Top-K')
    box(ax, 48, 44, 24, 10, 'DQN Network\n211 → 512 → 256 → 128 → 400')
    arrow(ax, 35, 57, 38, 57)
    darrow(ax, 52, 57-5, 52, 44+5)

    # Execution layer (bottom)
    dashed_box(ax, 50, 30, 92, 20, '')
    box(ax, 18, 34, 24, 10, 'moveJ_P\nCartesian Trajectory')
    box(ax, 46, 34, 28, 10, 'Plan_State Monitor\n50 Hz Polling · Timeout 10s')
    box(ax, 74, 34, 24, 10, 'Arduino Pneumatic\nSerial RUN / STOP')
    box(ax, 32, 20, 20, 8, 'RM65-B Arm\n6-DOF ±0.02 mm')
    box(ax, 60, 20, 20, 8, 'Vacuum Gripper\n−85 kPa <10 ms')
    arrow(ax, 30, 34-5, 30, 20+4)
    arrow(ax, 46, 34-5, 40, 20+4)
    arrow(ax, 60, 34-5, 60, 20+4)

    # Inter-layer arrows
    arrow(ax, 22, 57+5, 18, 34-5)
    arrow(ax, 52, 57+5, 52, 44-4)

    save(fig, 'fig1_system_architecture.png')


# ═══════════════════════════════════════════════════════════════
# 2. ROS NODE GRAPH
# ═══════════════════════════════════════════════════════════════
def draw_ros_graph():
    fig, ax = new_fig(11, 7.5)
    title(ax, 'ROS Node Communication Architecture')

    # Hardware layer
    dashed_box(ax, 50, 85, 88, 13, 'Hardware')
    box(ax, 25, 87, 22, 6, 'RealSense D435\n/camera/color  /camera/depth')
    box(ax, 55, 87, 26, 6, 'RM65-B Arm\n/rm_driver/Arm_Current_State')
    box(ax, 82, 87, 20, 6, 'Arduino Uno\n/dev/ttyUSB0')

    # ROS Application layer
    dashed_box(ax, 50, 55, 88, 32, 'ROS Application Nodes')

    box(ax, 14, 70, 25, 10, 'yolo_detector\nVision Pipeline')
    box(ax, 44, 70, 28, 10, 'tetris_planner\nDecision Engine')
    box(ax, 76, 70, 28, 10, 'motion_controller\nMoveJ_P Executor')
    box(ax, 28, 48, 20, 8, 'transform\nTF Broadcaster')
    box(ax, 56, 48, 22, 8, 'arduino_bridge\nSerial Protocol')
    box(ax, 78, 48, 16, 8, 'takephoto\nCapture')

    arrow(ax, 26.5, 70, 30, 70)
    arrow(ax, 58, 70, 62, 70)
    arrow(ax, 14, 70-5, 22, 48+4)
    arrow(ax, 65, 70-5, 56, 48+4)

    # Topics row
    Y = 38
    topics = [(16, '/camera/*'), (35, '/vision/detections'),
              (56, '/planning/place_pose'), (76, '/rm_driver/MoveJ_P')]
    for x, name in topics:
        ax.text(x, Y, name, fontsize=7, color=C['text_sub'], ha='center',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=C['border'], lw=0.6))

    # Hardware → ROS arrows
    arrow(ax, 25, 85-3, 14, 70+5)
    arrow(ax, 55, 85-3, 76, 70+5)

    save(fig, 'fig2_ros_node_graph.png')


# ═══════════════════════════════════════════════════════════════
# 3. VISION PIPELINE
# ═══════════════════════════════════════════════════════════════
def draw_vision_pipeline():
    fig, ax = new_fig(12, 6.5)
    title(ax, 'Vision Pipeline: RGB-D Capture to 6-DOF Grasp Pose')

    top = [(10, 'D435 Capture\nRGB 1920×1080\nDepth 1280×720'),
           (30, 'YOLOv8\nInstance Segmentation\nmAP@0.5 = 93.5%'),
           (52, 'Contour Extraction\nUniform Arc-Length\nResampling'),
           (74, 'Template Matching\nCoarse 5° → Fine 1°\nIoU ≥ 0.85'),
           (92, 'Best Match\nClass + Center\n+ Rotation θ')]

    bot = [(16, 'Depth Alignment\nrs.align → 1:1 Pixel'),
           (38, 'Pixel → Camera\nIntrinsic Matrix K\n(u,v,d) → (X,Y,Z)'),
           (60, 'Hand-Eye Transform\nT_cam→base · P_cam\n= P_base'),
           (80, '6-DOF Grasp Pose\n(x, y, z, R, P, Y)\nClass-specific Offset'),
           (96, 'OFFSET_MAP\nL/l/T: grip ratio\nZ/z/I/O: center')]

    for x, txt in top:
        box(ax, x, 74, 19, 18, txt, fontsize=7)
    for x, txt in bot:
        box(ax, x, 44, 19, 18, txt, fontsize=7)

    for i in range(len(top)-1):
        arrow(ax, top[i][0]+9.5, 74, top[i+1][0]-9.5, 74)
    for i in range(len(bot)-1):
        arrow(ax, bot[i][0]+9.5, 44, bot[i+1][0]-9.5, 44)

    darrow(ax, top[0][0], 74-9, bot[0][0], 44+9)
    darrow(ax, top[3][0], 74-9, bot[3][0], 44+9)
    arrow(ax, bot[4][0]+9.5, 44, top[4][0], 74-9)

    save(fig, 'fig3_vision_pipeline.png')


# ═══════════════════════════════════════════════════════════════
# 4. HYBRID DECISION FLOW
# ═══════════════════════════════════════════════════════════════
def draw_decision_flow():
    fig, ax = new_fig(12, 8)
    title(ax, 'Hybrid Decision: Heuristic Filter + Deep Q-Network')

    # Input
    box(ax, 22, 85, 28, 10, 'Game State\nBoard (10×20) · Piece Queue')
    box(ax, 58, 85, 30, 10, 'Candidate Generation\nAll Valid (x, y, θ)\n≈ 400 Positions')
    box(ax, 88, 85, 18, 8, 'Action Space\n400-Dim')
    arrow(ax, 36, 85, 43, 85)
    arrow(ax, 73, 85, 79, 85)

    # Phase 1
    dashed_box(ax, 50, 63, 88, 18, 'Phase 1: Dellacherie Heuristic Filter')
    box(ax, 20, 67, 30, 10, 'Six Feature Evaluation:\nLanding Height · Rows Cleared\nHoles · Roughness\nWell Depth · Column Transitions')
    box(ax, 55, 67, 28, 10, 'Score All Candidates\nLinear Weighted Sum\nSort Descending')
    box(ax, 85, 67, 20, 10, 'Top-K Filter\nK = 10\nBest Positions')
    arrow(ax, 35, 67, 41, 67)
    arrow(ax, 69, 67, 75, 67)
    arrow(ax, 50, 85-5, 50, 63+9)

    # Phase 2
    dashed_box(ax, 50, 41, 88, 18, 'Phase 2: DQN Long-term Optimization')
    box(ax, 22, 45, 26, 10, 'State Encoding\n211-Dim Feature Vector')
    box(ax, 52, 45, 28, 10, 'Forward Pass\n3-Layer MLP\n512→256→128→Q(s,a)')
    box(ax, 82, 45, 22, 10, 'ε-Greedy Selection\nε = 0.05\nexploit max Q(s,a)')
    arrow(ax, 35, 45, 38, 45)
    arrow(ax, 66, 45, 71, 45)
    darrow(ax, 52, 45-5, 50, 63-9)

    # Output
    box(ax, 50, 23, 34, 10, 'Optimal Place Pose\n(x, y, θ) → motion_controller', bold=True)
    arrow(ax, 50, 45-5, 50, 23+5)

    # Metrics
    ax.text(50, 10, 'Heuristic: 0.8 ms/candidate    DQN Forward: 2.3 ms    Total Decision Latency: < 5 ms',
            fontsize=8, color=C['text_sub'], ha='center')

    save(fig, 'fig4_decision_flow.png')


# ═══════════════════════════════════════════════════════════════
# 5. PICK-AND-PLACE SEQUENCE
# ═══════════════════════════════════════════════════════════════
def draw_sequence():
    fig, ax = new_fig(12, 7)
    title(ax, 'Pick-and-Place Motion Sequence (9.8 s Cycle)')

    # Timeline axis
    ax.axhline(y=74, xmin=0.05, xmax=0.95, color=C['border'], lw=1.5, zorder=1)
    ax.text(3, 75, 't (s)', fontsize=8, fontweight='bold', color=C['text'])

    phases = [
        (9,  '0.0\nStart', C['fill_main']),
        (20, '1.2\nApproach', C['fill_main']),
        (33, '2.8\nGrasp\nSuck', C['fill_dark']),
        (47, '4.5\nLift', C['fill_main']),
        (62, '6.2\nTransport', C['fill_main']),
        (76, '7.8\nPlace\nRelease', C['fill_dark']),
        (89, '9.0\nReturn', C['fill_main']),
    ]

    for x, txt, fc in phases:
        box(ax, x, 64, 14, 18, txt, facecolor=fc, fontsize=7)
        ax.plot(x, 74, 'o', color=C['border'], markersize=6, zorder=3)

    for i in range(len(phases)-1):
        arrow(ax, phases[i][0]+7, 74, phases[i+1][0]-7, 74)

    # Gripper state bar
    ax.text(3, 48, 'Gripper:', fontsize=8, fontweight='bold', color=C['text_sub'])
    ax.barh(48, 38, height=2.5, left=20, color=C['fill_dark'], edgecolor=C['border'], lw=0.8)
    ax.barh(48, 22, height=2.5, left=62, color=C['fill_dark'], edgecolor=C['border'], lw=0.8)
    ax.text(39, 48, 'SUCK (active)', fontsize=7, color=C['text_sub'], ha='center', va='center')

    # Plan_State feedback
    ax.text(3, 38, 'Plan_State\nFeedback:', fontsize=8, fontweight='bold', color=C['text_sub'])
    ax.text(32, 38, '50 Hz Polling  →  wait_for_move()  →  Movement Complete  →  Timeout 10 s',
            fontsize=8, color=C['text_sub'], ha='center', va='center')

    # Summary metrics
    ax.text(50, 22, 'Approach 1.2 s  ·  Grasp 0.3 s  ·  Lift 0.5 s  ·  Transport 1.7 s  ·  Place 0.5 s  ·  Return 1.2 s  =  Total 9.8 s',
            fontsize=8.5, color=C['text'], ha='center',
            bbox=dict(facecolor=C['fill_main'], edgecolor=C['border'], boxstyle='round,pad=0.4', lw=0.8))

    ax.text(50, 8, 'Safety: Force Limit 50 N  ·  Collision Detection  ·  E-Stop < 10 ms',
            fontsize=7.5, color=C['text_sub'], ha='center')

    save(fig, 'fig5_pick_place_sequence.png')


# ═══════════════════════════════════════════════════════════════
# 6. DQN ARCHITECTURE
# ═══════════════════════════════════════════════════════════════
def draw_dqn():
    fig, ax = new_fig(12, 7.5)
    title(ax, 'Deep Q-Network Architecture: 211-D State → 400-D Q-Values')

    # Layer boxes
    box(ax, 10, 75, 16, 14, 'Input\n211 Neurons\nState Features', bold=True, lw=1.2)
    box(ax, 30, 75, 16, 14, 'Hidden 1\n512 Neurons\nReLU + BatchNorm')
    box(ax, 50, 75, 16, 14, 'Hidden 2\n256 Neurons\nReLU + BatchNorm')
    box(ax, 70, 75, 16, 14, 'Hidden 3\n128 Neurons\nReLU + BatchNorm')
    box(ax, 90, 75, 16, 14, 'Output\n400 Neurons\nQ(s, a) Values', bold=True, lw=1.2)

    for x in [18, 38, 58, 78]:
        arrow(ax, x, 75, x+4, 75)

    # State features breakdown
    ax.text(8, 56, 'Input Features (211-D):', fontsize=8, fontweight='bold', color=C['text'])
    features = [
        'Board matrix: 200-D (10 × 20 grid, one-hot occupancy per cell)',
        'Piece queue: 7-D (current piece + next 6, class encoding)',
        'Hole count: 1-D (number of empty cells with filled cells above)',
        'Column height (max): 1-D',
        'Bumpiness sum: 1-D (sum of adjacent column height differences)',
        'Completed lines: 1-D',
    ]
    for i, f in enumerate(features):
        ax.text(10, 50 - i*4.5, f'· {f}', fontsize=7.2, color=C['text_sub'])

    # Training
    ax.text(50, 28, 'Training: Experience Replay Buffer (10K)  ·  Target Network Sync (100 steps)  ·  γ = 0.99  ·  η = 1×10⁻⁴  ·  Adam Optimizer',
            fontsize=8, color=C['text'], ha='center',
            bbox=dict(facecolor=C['fill_main'], edgecolor=C['border'], boxstyle='round,pad=0.3', lw=0.6))

    # Bellman equation
    ax.text(50, 14, 'Bellman Update:  Q(s, a) ← Q(s, a) + α [ r + γ · max Q(s′, a′) − Q(s, a) ]',
            fontsize=9, color=C['text'], ha='center',
            bbox=dict(facecolor='white', edgecolor=C['border'], boxstyle='round,pad=0.4', lw=0.8))

    ax.text(50, 4, 'ε-greedy exploration: ε decays from 1.0 → 0.05 over 10,000 episodes',
            fontsize=8, color=C['text_sub'], ha='center')

    save(fig, 'fig6_dqn_architecture.png')


# ═══════════════════════════════════════════════════════════════
# 7. HAND-EYE CALIBRATION
# ═══════════════════════════════════════════════════════════════
def draw_handeye():
    fig, ax = new_fig(10.5, 7)
    title(ax, 'Hand-Eye Calibration: Tsai-Lenz Algorithm')

    steps = [
        (12, 80, 'Capture\nCalibration Images\n15–20 Pairs'),
        (32, 80, 'Chessboard Detection\n8×6 Inner Corners\nSubpixel Refinement'),
        (55, 80, 'Solve AX = XB\nTsai-Lenz Two-Step\nRotation → Translation'),
        (78, 80, 'Transform Matrix\nT_cam→base\n4×4 Homogeneous'),
        (93, 80, 'Validation\nReprojection Error\n< 0.5 px'),
    ]

    for x, y, txt in steps:
        box(ax, x, y, 18, 16, txt, fontsize=7)

    for i in range(len(steps)-1):
        arrow(ax, steps[i][0]+9, 80, steps[i+1][0]-9, 80)

    # AX=XB detail
    ax.text(50, 58, 'Core Equation:  A · X = X · B',
            fontsize=11, fontweight='bold', color=C['text'], ha='center')

    exp = [
        'A: Robot end-effector pose change between two observations (from forward kinematics)',
        'B: Camera pose change between two observations (from chessboard detection)',
        'X: Unknown hand-eye transformation matrix (camera frame → end-effector frame)',
        'Step 1: Solve rotation R_X from axis-angle representation via linear least squares',
        'Step 2: Solve translation t_X from linear system with known rotation',
    ]
    for i, e in enumerate(exp):
        ax.text(50, 52 - i*4.5, e, fontsize=7.5, color=C['text_sub'], ha='center')

    ax.text(50, 25, 'Result: 6-DOF Transform  ·  Position Accuracy ±1.5 mm  ·  Orientation Accuracy ±0.5°',
            fontsize=9, color=C['text'], ha='center',
            bbox=dict(facecolor=C['fill_main'], edgecolor=C['border'], boxstyle='round,pad=0.4', lw=0.8))

    save(fig, 'fig7_handeye_calibration.png')


if __name__ == '__main__':
    print('Generating academic-style diagrams...')
    draw_architecture()
    draw_ros_graph()
    draw_vision_pipeline()
    draw_decision_flow()
    draw_sequence()
    draw_dqn()
    draw_handeye()
    print(f'Done: {len(os.listdir(OUTPUT_DIR))} diagrams in {OUTPUT_DIR}')
