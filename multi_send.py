import serial
import time
from binascii import unhexlify


port = 'COM6'  
baudrate = 9600

commands = [

'AT',
#'AT+CREG?', 
#'AT+COPS?', 
#'AT+CMGL="ALL"',
#'AT+CMGF=1',
#'AT+CPMS',
'AT+CSCS=?',
'At+CSCS="IRA"',
'AT+CSCS?',
'AT+CUSD=1,"54C983460", 15', #AT+CUSD=1,"*200#", 15



]

with serial.Serial(port, baudrate, timeout=1) as ser:
  time.sleep(2)  

  for command in commands:
      ser.write((command + '\r\n').encode())  
      time.sleep(3)  
      response = ser.read(ser.in_waiting or 1).decode() 
      print(f"Response for '{command}': {response}") 

  ser.close()      

