import serial
import time

# إعدادات المنفذ التسلسلي
port = 'COM18'  # يمكنك تغيير هذا إلى المنفذ الذي تريده
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

# فتح المنفذ التسلسلي
with serial.Serial(port, baudrate, timeout=1) as ser:
  time.sleep(2)  # الانتظار لبضع ثوانٍ للتأكد من أن الاتصال جاهز

  for command in commands:
      ser.write((command + '\r\n').encode())  # إرسال الأمر
      time.sleep(1)  # الانتظار قليلاً قبل قراءة الرد
      response = ser.read(ser.in_waiting or 1).decode()  # قراءة الرد
      print(f"Response for '{command}': {response}")  # طباعة الرد