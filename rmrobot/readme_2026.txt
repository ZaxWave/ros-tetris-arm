一、
#需要激活机械臂节点 需要进入机械臂工作空间

cd ~/ws_rmrobot/
source devel/setup.bash
roslaunch rm_control rm_control.launch

cd ~/ws_rmrobot/
source devel/setup.bash
rosrun rm_driver rm_driver



二、
进入control文件夹

1.拍照

python3 takephoto.py

2.识别

python3 pixel_to_camera1.py

3.转换到机械臂坐标系

python3 transform.py 

4.(验证)

（终端输入x y raw）
python3 move_xy.py   

(吸取和放置)
python3 




三、 其他

先 
   rostopic echo /rm_driver/Arm_Current_State

后  
 rostopic pub /rm_driver/GetArmState_Cmd rm_msgs/GetArmState_Command "command: ''"


rviz

roslaunch rm_bringup rm_robot.launch 















------------------------------
以下是一些注释



棋盘格位置
右下角   -0.18    -0.028
左上角   -0.44   -0.208


0.123

























