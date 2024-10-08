import serial

def send_at_command(command, message=None):
    with serial.Serial('COM15', 9600, timeout=1) as ser:
        ser.write(f"{command}\r\n".encode())  # إرسال الأمر الأساسي
        response = ser.read(100).decode()
        print(f"Response: {response}")
        
        # إذا كان الأمر هو AT+CMGS، نرسل الرسالة ثم ننهي برمز Ctrl+Z
        if command.startswith("AT+CMGS=") and message:
            ser.write(f"{message}\r".encode())  # إرسال الرسالة الفعلية
            ser.write(b'\x1A')  # إرسال رمز Ctrl+Z (0x1A) لإنهاء الرسالة
            response = ser.read(100).decode()  # قراءة الرد بعد إرسال الرسالة
            print(f"Response after sending message: {response}")

if __name__ == "__main__":
    command = input("Enter AT command (e.g. AT+CMGF=1 for text mode): ")
    message = input("Enter message (if applicable): ") if command.startswith("AT+CMGS=") else None
    send_at_command(command, message)
