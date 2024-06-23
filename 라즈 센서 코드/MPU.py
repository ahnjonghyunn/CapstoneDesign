import smbus         
from time import sleep 
import math  
import RPi.GPIO as GPIO

GPIO.setwarnings(False)

PWR_MGMT_1   = 0x6B
SMPLRT_DIV   = 0x19
CONFIG       = 0x1A
GYRO_CONFIG  = 0x1B
INT_ENABLE   = 0x38
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F
GYRO_XOUT_H  = 0x43
GYRO_YOUT_H  = 0x45
GYRO_ZOUT_H  = 0x47

LED_PIN = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

bus = smbus.SMBus(1) 
Device_Address = 0x68 

def MPU_Init():
    bus.write_byte_data(Device_Address, SMPLRT_DIV, 7)
    
    bus.write_byte_data(Device_Address, PWR_MGMT_1, 1)

    bus.write_byte_data(Device_Address, CONFIG, 0)

    bus.write_byte_data(Device_Address, GYRO_CONFIG, 24)

    bus.write_byte_data(Device_Address, INT_ENABLE, 1)

def read_raw_data(addr):
    high = bus.read_byte_data(Device_Address, addr)
    low = bus.read_byte_data(Device_Address, addr + 1)
    
    value = ((high << 8) | low)
    
    if value > 32768:
        value = value - 65536
    return value

def get_accel_data():
    acc_x = read_raw_data(ACCEL_XOUT_H)
    acc_y = read_raw_data(ACCEL_YOUT_H)
    acc_z = read_raw_data(ACCEL_ZOUT_H)
    
    Ax = acc_x / 16384.0
    Ay = acc_y / 16384.0
    Az = acc_z / 16384.0
    
    return Ax, Ay, Az

def apply_moving_average(data, window_size=5):
    if len(data) < window_size:
        return sum(data) / len(data)
    return sum(data[-window_size:]) / window_size

accData = [0, 0, 0]
window_size = 10

try:
    MPU_Init()
    x_data, y_data, z_data = [], [], []
    for i in range(10):
        Ax, Ay, Az = get_accel_data()
        x_data.append(Ax)
        y_data.append(Ay)
        z_data.append(Az)
        accData[0] += Ax
        accData[1] += Ay
        accData[2] += Az
        sleep(0.1)
    
    accData[0] /= 10
    accData[1] /= 10
    accData[2] /= 10
    
    print("Initial Acceleration Data:", accData)
    
    threshold = 0.2  
    duration = 1 
    check_interval = 0.01 
    required_samples = int(duration / check_interval) 
    
    while True:
        shock_detected = False
        for _ in range(required_samples):
            Ax, Ay, Az = get_accel_data()
            x_data.append(Ax)
            y_data.append(Ay)
            z_data.append(Az)
            
            Ax = apply_moving_average(x_data, window_size)
            Ay = apply_moving_average(y_data, window_size)
            Az = apply_moving_average(z_data, window_size)

            acceleration_magnitude = math.sqrt((Ax - accData[0])**2 + (Ay - accData[1])**2 + (Az - accData[2])**2)
            
            if acceleration_magnitude >= threshold:
                shock_detected = True
                break 
            sleep(check_interval)
        
        if shock_detected:
            print("<<<<< 충격 발생 >>>>>")
            GPIO.output(LED_PIN, GPIO.HIGH)
        else:
            GPIO.output(LED_PIN, GPIO.LOW)
        sleep(0.1)  

except KeyboardInterrupt:
    pass
