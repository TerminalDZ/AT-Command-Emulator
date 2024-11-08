import serial
import serial.tools.list_ports
import logging
import sys
from typing import Tuple, List, Optional
from datetime import datetime
import time

# Setup logging with more detailed error information
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler(f'serial_errors_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Set isDev to 1 to include "com0com" ports in the SIM ports list
isDev = 1

class SerialPortError(Exception):
    """Custom exception class for serial port related errors with detailed messages"""
    def __init__(self, message: str, error_code: Optional[int] = None):
        self.message = message
        self.error_code = error_code
        self.timestamp = datetime.now()
        super().__init__(self.message)

def format_error_message(error: Exception, context: str) -> str:
    """
    Format error messages in a consistent and detailed way
    
    Args:
        error (Exception): The exception that occurred
        context (str): Context where the error occurred
        
    Returns:
        str: Formatted error message
    """
    return f"Error in {context}: {str(error)}\nType: {type(error).__name__}"

def list_serial_ports() -> Tuple[List[str], List[str]]:
    """
    List all available serial ports and identify SIM USB ports if possible.
    
    Returns:
        Tuple[List[str], List[str]]: Available ports list and SIM ports list
        
    Raises:
        SerialPortError: If there's an error listing the ports
    """
    try:
        ports = serial.tools.list_ports.comports()
        if not ports:
            error_msg = "No serial ports detected on this system"
            logging.warning(error_msg)
            print(f"Warning: {error_msg}")
            return [], []

        available_ports = []
        sim_ports = []
        
        for port in ports:
            try:
                port_info = f"{port.device} - {port.description}"
                
                # Check for SIM or Modem in description
                if "SIM" in port.description or "Modem" in port.description:
                    port_info += " (SIM port)"
                    sim_ports.append(port.device)
                
                if isDev and ("com0com" in port.description or "Control" in port.description):
                    port_info += " (SIM port)"
                    sim_ports.append(port.device)
                
                available_ports.append(port_info)
                logging.debug(f"Port detected: {port_info}")
                
            except Exception as e:
                error_msg = format_error_message(e, f"processing port {port.device}")
                logging.error(error_msg)
                print(f"Error: {error_msg}")
                
        return available_ports, sim_ports
        
    except Exception as e:
        error_msg = format_error_message(e, "listing serial ports")
        logging.error(error_msg)
        raise SerialPortError(error_msg)
    
def open_serial_port(port: str, baudrate: int = 9600, retries: int = 3, delay: float = 2.0) -> Optional[serial.Serial]:
    """
    Tries to open a serial port with retry capability.
    
    Args:
        port (str): Serial port name
        baudrate (int): Baud rate for the port
        retries (int): Number of retries if the port fails to open
        delay (float): Delay in seconds between retries
    
    Returns:
        serial.Serial: Opened serial port object or None if it fails after retries
    """
    for attempt in range(retries):
        try:
            ser = serial.Serial(port, baudrate, timeout=1)
            logging.info(f"Successfully opened port: {port}")
            return ser
        except serial.SerialException as e:
            logging.error(f"Attempt {attempt + 1}: Failed to open port {port}: {e}")
            time.sleep(delay)
    
    logging.error(f"All attempts to open port {port} failed.")
    return None


def get_sim_operator(port: str) -> str:
    """
    Send AT+COPS? command to get the SIM operator name.
    
    Args:
        port (str): Serial port name
        
    Returns:
        str: SIM operator name
        
    Raises:
        SerialPortError: If there's an error communicating with the port
    """
    try:
        with serial.Serial(port, 9600, timeout=1) as ser:
            ser.write(b'AT+COPS?\r\n')
            response = ser.read(100).decode(errors='ignore')
            
            if "+COPS:" in response:
                parts = response.split(',')
                if len(parts) > 2:
                    operator_name = parts[2].strip().strip('"')
                    logging.info(f"Successfully found operator: {operator_name} for port {port}")
                    return operator_name
            
            error_msg = f"No operator information available for port {port}"
            logging.warning(error_msg)
            return "Unknown Operator"
            
    except serial.SerialException as e:
        error_msg = format_error_message(e, f"accessing port {port}")
        logging.error(error_msg)
        raise SerialPortError(f"Failed to access port {port}: {str(e)}")
    except Exception as e:
        error_msg = format_error_message(e, "getting SIM operator")
        logging.error(error_msg)
        raise SerialPortError(error_msg)

def send_at_command(command: str, port: str, message: Optional[str] = None) -> str:
    """
    Send an AT command to the specified serial port.
    
    Args:
        command (str): AT command to send
        port (str): Serial port
        message (Optional[str]): Message (if required)
        
    Returns:
        str: Device response
        
    Raises:
        SerialPortError: If there's an error sending the command
    """
    if not port:
        error_msg = "No port specified for AT command"
        logging.error(error_msg)
        raise SerialPortError(error_msg)
        
    try:
        ser = open_serial_port(port)
        if ser is None:
            raise SerialPortError(f"Failed to open port {port} after multiple attempts")
        with ser:
            # Send command
            ser.write(f"{command}\r\n".encode())
            logging.debug(f"Successfully sent command: {command}")

            # Read response
            response = ser.read(100).decode(errors='ignore')
            if not response:
                error_msg = "No response received from device"
                logging.warning(error_msg)
                print(f"Warning: {error_msg}")
            else:
                logging.info(f"Response received: {response}")

            # If there's a message, send it
            if message:
                ser.write(f"{message}\x1A".encode())
                logging.debug(f"Message sent: {message}")
                additional_response = ser.read(100).decode(errors='ignore')
                response += additional_response
            
            return response
        
    except serial.SerialException as e:
        error_msg = format_error_message(e, f"communicating with port {port}")
        logging.error(error_msg)
        raise SerialPortError(f"Communication error with port {port}: {str(e)}")
    except Exception as e:
        error_msg = format_error_message(e, "sending AT command")
        logging.error(error_msg)
        raise SerialPortError(error_msg)
    
def main():
    """Main program function with enhanced error handling"""
    try:
        print("Serial Port Communication Tool")
        print("-----------------------------")
        
        # List available ports
        available_ports, sim_ports = list_serial_ports()
        
        if not available_ports:
            print("Error: No serial ports were found on this system.")
            print("Please check your device connections and try again.")
            return
            
        print("\nAvailable serial ports:")
        for i, port_info in enumerate(available_ports):
            print(f"{i + 1}: {port_info}")

        # Handle SIM ports
        if sim_ports:
            print("\nDetected SIM ports:")
            sim_ports_with_operators = []
            
            for i, sim_port in enumerate(sim_ports):
                try:
                    operator_name = get_sim_operator(sim_port)
                    sim_ports_with_operators.append((sim_port, operator_name))
                    print(f"{i + 1}: {sim_port} (SIM port) - {operator_name}")
                except SerialPortError as e:
                    error_msg = f"Error with port {sim_port}: {str(e)}"
                    logging.error(error_msg)
                    print(f"Error: {error_msg}")
            
            if not sim_ports_with_operators:
                print("Warning: No accessible SIM ports found.")
        
        # Allow user to select any available port if no SIM ports detected
        while True:
            try:
                print("\nYou may select any available port to send AT commands.")
                port_index = int(input("Select a port number: ")) - 1
                if 0 <= port_index < len(available_ports):
                    selected_port = available_ports[port_index].split(" - ")[0]
                    break
                else:
                    print("Error: Invalid selection. Please enter a number between "
                          f"1 and {len(available_ports)}.")
            except ValueError:
                print("Error: Please enter a valid number.")
            except Exception as e:
                error_msg = format_error_message(e, "port selection")
                logging.error(error_msg)
                print(f"Error: {error_msg}")

        # Get AT command and message with validation
        while True:
            command = input("\nEnter AT command (e.g., AT+CMGF=1 for text mode): ").strip()
            if command.upper().startswith("AT"):
                break
            print("Error: Command must start with 'AT'. Please try again.")

        message = None
        if command.startswith("AT+CMGS="):
            message = input("Enter message content: ").strip()
            if not message:
                print("Warning: Empty message content")

        # Send command with comprehensive error handling
        try:
            print("\nSending command...")
            response = send_at_command(command, selected_port, message)
            print("\nDevice Response:")
            print("-----------------")
            print(response if response else "No response received")
        except SerialPortError as e:
            print(f"\nError sending command: {str(e)}")
            print("Please check your device connection and try again.")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        logging.info("Program terminated by user")
    except Exception as e:
        error_msg = format_error_message(e, "main program")
        logging.error(error_msg)
        print(f"\nCritical Error: {error_msg}")
        print("Please check the log file for more details.")

if __name__ == "__main__":
    main()
