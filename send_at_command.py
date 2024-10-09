import serial
import serial.tools.list_ports

# Set isDev to 1 to include "com0com" ports in the SIM ports list
isDev = 1

def list_serial_ports():
  """List all available serial ports and identify SIM USB ports if possible."""
  ports = serial.tools.list_ports.comports()
  available_ports = []
  sim_ports = []

  for port in ports:
      port_info = f"{port.device} - {port.description}"
      
      # Check for SIM or Modem in description
      if "SIM" in port.description or "Modem" in port.description:
          port_info += " (this is port sim)"
          sim_ports.append(port.device)
      
      # If isDev is 1, also check for "com0com" in description
      if isDev and "com0com" in port.description:
          port_info += " (this is port sim)"
          sim_ports.append(port.device)

      if isDev and "Control" in port.description:
        port_info += " (this is port sim)"
        sim_ports.append(port.device)
      
      available_ports.append(port_info)

  return available_ports, sim_ports

def get_sim_operator(port):
  """Send AT+COPS? command to get the SIM operator name."""
  try:
      with serial.Serial(port, 9600, timeout=1) as ser:
          ser.write(b'AT+COPS?\r\n')
          response = ser.read(100).decode(errors='ignore')
          # Extract operator name from response
          if "+COPS:" in response:
              parts = response.split(',')
              if len(parts) > 2:
                  operator_name = parts[2].strip().strip('"')
                  return operator_name
  except serial.SerialException as e:
      print(f"Error opening serial port {port}: {e}")
  return "Unknown Operator"

def send_at_command(command, message=None, port=''):
  """Send an AT command to the specified serial port."""
  if not port:
      print("No port specified.")
      return

  try:
      with serial.Serial(port, 9600, timeout=1) as ser:
          ser.write(f"{command}\r\n".encode())
          response = ser.read(100).decode(errors='ignore')  # Ignore decoding errors
          print(f"Response: {response}")
  except serial.SerialException as e:
      print(f"Error opening serial port {port}: {e}")

if __name__ == "__main__":
  # List available ports
  available_ports, sim_ports = list_serial_ports()
  if not available_ports:
      print("No serial ports found.")
  else:
      print("Available serial ports:")
      for i, port_info in enumerate(available_ports):
          print(f"{i + 1}: {port_info}")

      # Prompt the user to select a SIM port
      if sim_ports:
          print("\nPlease select a SIM port:")
          sim_ports_with_operators = []
          for i, sim_port in enumerate(sim_ports):
              operator_name = get_sim_operator(sim_port)
              sim_ports_with_operators.append((sim_port, operator_name))
              print(f"{i + 1}: {sim_port} (SIM port) - {operator_name}")

          while True:
              try:
                  port_index = int(input("Select a SIM port by number: ")) - 1
                  if 0 <= port_index < len(sim_ports_with_operators):
                      selected_port = sim_ports_with_operators[port_index][0]  # Use sim_ports directly
                      break
                  else:
                      print("Invalid selection. Please try again.")
              except ValueError:
                  print("Invalid input. Please enter a number.")
      else:
          print("No SIM ports available for selection.")

      # Get AT command and message
      command = input("Enter AT command (e.g. AT+CMGF=1 for text mode): ")
      message = input("Enter message (if applicable): ") if command.startswith("AT+CMGS=") else None

      # Send the command
      send_at_command(command, message, selected_port)