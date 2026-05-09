import serial
import time

port = '/dev/ttyUSB0'  # 请根据实际设备路径修改
baudrate = 9600

try:
    print(f"尝试连接串口 {port}...")
    with serial.Serial(port, baudrate, timeout=2) as ser:
        
        print("串口连接成功！发送指令：STOP")
        
       # time.sleep(1.0)  # 等待 Arduino 初始化完成，不能省略
        
        ser.write(b'STOP\n')
        
        print("指令已发送：STOP")

except serial.SerialException as e:
    print("❌ 串口打开失败！")
