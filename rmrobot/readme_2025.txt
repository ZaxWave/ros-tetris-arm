



1.拍照 takephoto.py

#需要激活相机节点

cd ~/realsense_ws
source devel/setup.bash
roslaunch realsense2_camera rs_camera.launch \
    align_depth:=true \
    color_width:=1920 color_height:=1080 color_fps:=30 \
    depth_width:=1280 depth_height:=720 depth_fps:=30
    
#↑↑↑↑↑↑↑↑↑↑↑参数一定要设置对  :(

#拍照
cd ~/realsense_ws
source devel/setup.bash
rosrun  realsense2_camera  takephoto.py


2.识别像素坐标

conda activate yolov8
yolo task=segment mode=predict model=/home/zhy/rmrobot/tetris/yolov8/best.pt source=/home/zhy/rmrobot/output/color imgsz=1920 save=True save_txt=True save_conf=True project=/home/zhy/rmrobot/tetris/yolov8/runs name=tetris_pred

cd /home/zhy/rmrobot/tetris/yolov8 
python3 visualize_yolo_degv2.py

3.转换成相机坐标系的坐标

#需要激活相机节点

cd ~/realsense_ws
source devel/setup.bash
roslaunch realsense2_camera rs_camera.launch \
    align_depth:=true \
    color_width:=1920 color_height:=1080 color_fps:=30 \
    depth_width:=1280 depth_height:=720 depth_fps:=30

cd ~/realsense_ws
source devel/setup.bash
rosrun  realsense2_camera  cameracoordinates.py


4.转换成基座坐标系的坐标

#需要激活机械臂节点 需要进入机械臂工作空间

cd ~/ws_rmrobot/
source devel/setup.bash
roslaunch rm_control rm_control.launch

cd ~/ws_rmrobot/
source devel/setup.bash
rosrun rm_driver rm_driver

cd ~/ws_rmrobot/
source devel/setup.bash
python3 /home/zhy/rmrobot/transform.py



5.
cd ~/ws_rmrobot/
source devel/setup.bash
roslaunch rm_control rm_control.launch

cd ~/ws_rmrobot/
source devel/setup.bash
rosrun rm_driver rm_driver

source devel/setup.bash
rosrun rm_65_demo test.py

source devel/setup.bash
rosrun rm_65_demo moveJ_P.py




6.

先 
   rostopic echo /rm_driver/Arm_Current_State

后  
 rostopic pub /rm_driver/GetArmState_Cmd rm_msgs/GetArmState_Command "command: ''"

















------------------------------
以下是一些注释



棋盘格位置
右下角   -0.18    -0.028
左上角   -0.44   -0.208


0.123

























