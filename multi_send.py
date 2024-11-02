import serial
import time

port = 'COM18'  
baudrate = 9600

# قائمة الأوامر التي سيتم إرسالها
commands = [
  #"AT+CUSD=?",  # تحقق من دعم USSD
  #"AT+CUSD?",   # تحقق من حالة USSD
  #"AT+CUSD=0",  # إلغاء USSD
  #'AT+CSCS="GSM"',  # تعيين مجموعة الأحرف
  #'AT+CUSD=1,"*100#"',  # استبدل *100# بكود USSD آخر
  #  'AT+CUSD=1,"*500#",15'
   'AT+COPS=2',
'AT+COPS=?'
]

with serial.Serial(port, baudrate, timeout=1) as ser:
  time.sleep(2)  

  for command in commands:
      ser.write((command + '\r\n').encode())  
      time.sleep(1)  
      response = ser.read(ser.in_waiting or 1).decode() 
      print(f"Response for '{command}': {response}") 