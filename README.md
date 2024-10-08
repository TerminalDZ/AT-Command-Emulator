# AT Command Emulator

## Overview

The AT Command Emulator simulates the behavior of a GSM modem, allowing users to send and receive AT commands. It supports various network and SMS functionalities such as sending SMS, querying modem information, and managing S-registers. A Python script is provided to interact with the emulator via a serial interface.

## Features

- **SIM Information**: Pre-configured SIM details including:
  - Name, phone number, CCID, IMEI, IMSI, manufacturer, and model.
- **AT Command Support**: Supports common commands like:
  - `AT+CGMI`, `AT+CGMM`, `AT+CMGS`, and more.
- **SMS Handling**:
  - Supports Text and PDU SMS modes with error handling and message references.
- **S-register Simulation**:
  - Manage and modify S-register values for advanced control.
- **USSD Support**:
  - Execute USSD commands to query SIM-related data (e.g., balance check).

## Requirements

- **Python** 3.x
- **pyserial** library (Install using `pip install pyserial`)
- **Virtual COM Port Software**:
  - For **Windows**: Use `com0com` or similar tools.
  - For **Linux**: Use `socat` to create virtual COM ports.

---

## Setup Instructions

### 1. Install `pyserial`

To install the required `pyserial` library, use the following command:

```bash
pip install pyserial
```

### 2. Setting Up Virtual COM Ports (Windows)

Download and install `com0com` to create virtual COM ports on Windows.
Use the `com0com` setup utility to create a pair of connected virtual ports (e.g., COM14 and COM15).

Alternatively, for Linux, you can use `socat` to create virtual COM ports:

```bash
sudo socat PTY,link=/dev/ttyS14 PTY,link=/dev/ttyS15
```

### 3. Running the AT Command Emulator

To start the AT Command Emulator, run the following command:

```bash
python at_emulator.py --port COM14 --baudrate 115200
```

This will initialize the emulator on the specified COM port (e.g., COM14 with a baud rate of 115200).

### 4. Sending AT Commands

You can send AT commands using any terminal or the provided `send_at_command.py` script. Here’s a basic example of sending an AT command:

```bash
python send_at_command.py
```

Once the script is running, you can enter AT commands (e.g., `AT+CGMI`) to get the modem manufacturer information.

---

## Supported AT Commands

Below is a list of common AT commands supported by the emulator:

| Command  | Description                             |
| -------- | --------------------------------------- |
| AT       | Basic test command, returns `OK`.       |
| AT+CGMI  | Get the modem manufacturer.             |
| AT+CGMM  | Get the modem model.                    |
| AT+CGMR  | Get the firmware version.               |
| AT+CMGS  | Send an SMS message (Text or PDU mode). |
| AT+COPS? | Query operator selection.               |
| AT+CREG? | Check network registration status.      |
| AT+CNUM  | Get the phone number of the modem.      |
| AT+CCID  | Get the SIM card CCID.                  |
| \*200#   | USSD to check balance.                  |
| \*123#   | USSD to check available minutes.        |

More advanced commands are supported and can be handled based on your use case.

---

## Example Python Code to Send AT Commands

Here’s a simple Python script to send AT commands to the emulator:

```python
import serial

def send_at_command(command: str, port: str = 'COM14', baudrate: int = 115200):
    try:
        with serial.Serial(port, baudrate, timeout=1) as ser:
            ser.write(f"{command}\r\n".encode())
            response = ser.read(100).decode()
            print(f"Response: {response}")
    except serial.SerialException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_at_command("AT+CGMI")
```

### Running the Script

To run the script and send AT commands:

```bash
python send_at_command.py
```

Enter any valid AT command (e.g., `AT+CGMI`) when prompted to receive a response.

---

## Troubleshooting

- **Cannot open COM port:** Ensure that the correct COM port is specified and that it is not being used by another application.
- **No response to AT commands:** Check if the emulator is running correctly and that the baud rate matches the settings used in the terminal or script.
- **AT command errors:** Some AT commands may not be fully supported, depending on the emulator's capabilities.
