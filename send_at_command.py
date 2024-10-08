import serial

def send_at_command(command, message=None):
    with serial.Serial('COM18', 9600, timeout=1) as ser:
        ser.write(f"{command}\r\n".encode())  # إرسال الأمر الأساسي
        response = ser.read(100).decode()
        print(f"Response: {response}")
 
if __name__ == "__main__":
    command = input("Enter AT command (e.g. AT+CMGF=1 for text mode): ")
    message = input("Enter message (if applicable): ") if command.startswith("AT+CMGS=") else None
    send_at_command(command, message)
