
import serial
import time

port = '/dev/ttyUSB0'  
# 根据实际情况修改， 查看串口   ls /dev/ttyACM* /dev/ttyUSB*  ；再者，可以先插上usb：    dmesg | grep tty
#气泵黄线接9，那个什么阀黄线接8
baudrate = 9600

try:
    print(f"尝试连接串口 {port}...")
    with serial.Serial(port, baudrate, timeout=2) as ser:
        
        print("串口连接成功！发送指令：RUN")
        
        time.sleep(1.6)  # 等待 Arduino 初始化，这一步绝对不能删！！！！
        
        ser.write(b'RUN\n')
        
        print("指令已发送：RUN")

#------------------以上是代码主体，下面没用--------------------------


        # while True:
        #     line = ser.readline().decode('utf-8').strip()
        #     if line:
        #         print("Arduino回应：", line)
        #     else:
        #         break

except serial.SerialException as e:
    print("❌ 串口打开失败！可能原因：")
    
    
#如果打开失败，很大可能权限问题，  
#运行： sudo usermod -a -G dialout $USER
#然后重启

