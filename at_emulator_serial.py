import serial
import time
from typing import Tuple, Optional

class ATResponse:
    OK = "OK"
    CMS_ERROR_304 = "+CMS ERROR: 304"
    CMS_ERROR_305 = "+CMS ERROR: 305"
    NO_CARRIER = "NO CARRIER"
    ERROR = "ERROR"

class ATEmulator:
    def __init__(self):
        self.s_registers = [
            0, 0, 43, 13, 10, 8, 2, 50, 2, 6, 14, 95, 50
        ] + [0] * 5 + [0] + [0] * 6 + [5, 1] + [0] * 3 + [0] + [0] * 6 + [0, 20]
        self.current_s_register = 0
        self.echo = True
        self.verbose = True
        self.quiet = False
        self.result_code_format = 4
        self.cnmi_mode = 1
        self.cnmi_mt = 2
        self.cnmi_bm = 0
        self.cnmi_ds = 1
        self.cnmi_bfr = 0
        self.sms_mode = 1
        self.gprs_attached = 0
        self.message_reference = 0
        self.network_registration = 0
        self.sim_info = {
            "sim_name": "Ooredoo",
            "phone_number": "+213123456789",
            "ccid": "8988303000005737285",
            "imei": "359123456789012",
            "imsi": "310260123456789",
            "manufacturer": "U-Blox",
            "model": "SARA-R410M",
            "firmware": "M10.00.01",
            "balance": 1500
        }
        self.sms_inbox = []
        self.sms_outbox = []

    def process_command(self, command: str) -> Tuple[Optional[str], int]:
        if not command:
            return None, 0
        command = command.upper().strip()
        if not command.startswith("AT"):
            return None, ATResponse.ERROR
        parts = command[2:].split(";")
        response = None
        error = 0
        for part in parts:
            response, error = self._process_single_command(part)
            if error != 0:
                break
        return response, error

    def _process_single_command(self, command: str) -> Tuple[Optional[str], int]:
        if not command:
            return None, 0
        if command == "":
            return None, 0
        elif command == "I":
            return "C102", 0
        elif command in ["I1", "I2"]:
            return "63656C6572736D73", 0
        elif command == "I3" or command == "+CGMI":
            return self.sim_info["manufacturer"], 0
        elif command.startswith("+CMGF"):
            if command == "+CMGF=1":
                self.sms_mode = 1
                return None, 0
            elif command == "+CMGF=0":
                self.sms_mode = 0
                return None, 0
            else:
                return None, ATResponse.ERROR
        elif command == "I4" or command == "+CGMM":
            return self.sim_info["model"], 0
        elif command == "I5" or command == "+CGMR":
            return self.sim_info["firmware"], 0
        elif command == "+CIMI":
            return self.sim_info["imsi"], 0
        elif command == "+CCID":
            return self.sim_info["ccid"], 0
        elif command == "+CGSN":
            return self.sim_info["imei"], 0
        elif command == "+CNUM":
            return self.sim_info["phone_number"], 0
        elif command == "+COPS?":
            return f'+COPS: 0,0,"{self.sim_info["sim_name"]}",2', 0
        elif command == "E0":
            self.echo = False
            return None, 0
        elif command == "E1":
            self.echo = True
            return None, 0
        elif command == "V0":
            self.verbose = False
            return None, 0
        elif command == "V1":
            self.verbose = True
            return None, 0
        elif command == "Q0":
            self.quiet = False
            return None, 0
        elif command == "Q1":
            self.quiet = True
            return None, 0
        elif command.startswith("S"):
            return self._handle_s_register(command)
        elif command.startswith("+CMGS"):
            return self._handle_sms_command(command)
        elif command.startswith("*") and command.endswith("#"):
            return self._handle_ussd_command(command)
        return None, ATResponse.ERROR

    def _handle_s_register(self, command: str) -> Tuple[Optional[str], int]:
        if len(command) < 2:
            return None, ATResponse.ERROR
        if command[1:].isdigit():
            reg_num = int(command[1:])
            if 0 <= reg_num < len(self.s_registers):
                self.current_s_register = reg_num
                return None, 0
        if "?" in command:
            parts = command.split("?")
            reg_num = int(parts[0][1:]) if parts[0][1:].isdigit() else self.current_s_register
            if 0 <= reg_num < len(self.s_registers):
                return str(self.s_registers[reg_num]), 0
        if "=" in command:
            parts = command.split("=")
            reg_num = int(parts[0][1:]) if parts[0][1:].isdigit() else self.current_s_register
            if len(parts) > 1 and parts[1].isdigit():
                value = int(parts[1])
                if 0 <= reg_num < len(self.s_registers) and 0 <= value <= 255:
                    self.s_registers[reg_num] = value
                    return None, 0
        return None, ATResponse.ERROR

    def _handle_sms_command(self, command: str) -> Tuple[Optional[str], int]:
        if command == "+CMGS=?":
            return None, 0
        if command.startswith("+CMGS="):
            try:
                length = int(command[6:])
                if self.sms_mode == 0 and not (7 <= length <= 160):
                    return None, ATResponse.CMS_ERROR_304
                if self.sms_mode == 1 and length <= 0:
                    return None, ATResponse.CMS_ERROR_305
                self.message_reference = (self.message_reference + 1) % 256
                if self.message_reference == 0:
                    self.message_reference = 1
                return f"+CMGS: {self.message_reference}", 0
            except ValueError:
                return None, ATResponse.ERROR
        return None, ATResponse.ERROR

    def _handle_ussd_command(self, command: str) -> Tuple[Optional[str], int]:
        if command == "*200#":
            return f"Your current balance is {self.sim_info['balance']} DZD", 0
        elif command == "*123#":
            return "50 minutes remaining", 0
        return None, ATResponse.ERROR

def main():
    emulator = ATEmulator()
    try:
        ser = serial.Serial('COM14', 115200, timeout=1)
        buffer = ""
        while True:
            if ser.in_waiting:
                char = ser.read().decode('utf-8', errors='ignore')
                if char == '\r' or char == '\n':
                    if buffer:
                        if emulator.echo:
                            ser.write(f"{buffer}\r\n".encode('utf-8'))
                        response, error = emulator.process_command(buffer)
                        if not emulator.quiet:
                            if response:
                                if emulator.verbose:
                                    ser.write(f"\r\n{response}\r\n".encode('utf-8'))
                                else:
                                    ser.write(f"{response}\r\n".encode('utf-8'))
                            if emulator.verbose:
                                error_msg = ATResponse.ERROR if error != 0 else ATResponse.OK
                                ser.write(f"\r\n{error_msg}\r\n".encode('utf-8'))
                            else:
                                ser.write(f"{error}\r\n".encode('utf-8'))
                        buffer = ""
                else:
                    buffer += char
            time.sleep(0.01)
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
    finally:
        if 'ser' in locals():
            ser.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='AT Command Emulator (Serial)')
    parser.add_argument('--port', type=str, default='COM14', help='Serial port to use')
    parser.add_argument('--baudrate', type=int, default=115200, help='Baudrate for serial communication')
    args = parser.parse_args()
    try:
        import serial
    except ImportError:
        print("pyserial library is required. Please install it using:")
        print("pip install pyserial")
        exit(1)
    main()
