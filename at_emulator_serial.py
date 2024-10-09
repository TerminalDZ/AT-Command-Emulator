import serial
import threading
import time
import logging
from typing import Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ATCommandError(Exception):
  """Custom exception for AT command errors."""
  pass

class ATEmulator:
  """AT Command Emulator class."""

  def __init__(self, port: str, baudrate: int = 115200):
      """
      Initialize the emulator.
      :param port: Serial port to listen on.
      :param baudrate: Baud rate for serial communication.
      """
      self.port = port
      self.baudrate = baudrate
      self.serial_port = None
      self.running = False
      self.echo = True
      self.verbose = True
      self.quiet = False
      self.sms_mode = 1  # 0: PDU mode, 1: Text mode
      self.command_handlers = {
          'AT': self.handle_at,
          'ATE0': self.handle_ate0,
          'ATE1': self.handle_ate1,
          'ATI': self.handle_ati,
          'AT+GMI': self.handle_gmi,
          'AT+GMM': self.handle_gmm,
          'AT+GMR': self.handle_gmr,
          'AT+CGMI': self.handle_gmi,
          'AT+CGMM': self.handle_gmm,
          'AT+CGMR': self.handle_gmr,
          'AT+CSQ': self.handle_csq,
          'AT+CREG?': self.handle_creg,
          'AT+COPS?': self.handle_cops,  # Ensure this is correctly registered
          'AT+CMGF': self.handle_cmgf,
          'AT+CMGS': self.handle_cmgs,
          'AT+CMGR': self.handle_cmgr,
          'AT+CMGL': self.handle_cmgl,
          'AT+CMGD': self.handle_cmgd,
          'AT+CUSD': self.handle_cusd,
          'AT+CGATT': self.handle_cgatt,
          'AT+CIPSTATUS': self.handle_cipstatus,
          'AT+CIPSTART': self.handle_cipstart,
          'AT+CIPCLOSE': self.handle_cipclose,
      }
      self.simulated_state = {
          'manufacturer': 'Generic',
          'model': 'Modem 1.0',
          'revision': '1.0.0',
          'imei': '123456789012345',
          'imsi': '310150123456789',
          'operator': 'Mobilis',
          'signal_strength': 15,
          'registration_status': 1,
          'sms_storage': [],
          'gprs_attached': 0,
          'ip_status': 'IP INITIAL',
          # Add more simulated states here...
      }

  def start(self):
      """Start the emulator and open the serial port."""
      try:
          self.serial_port = serial.Serial(self.port, self.baudrate, timeout=1)
          self.running = True
          logging.info(f"Serial port {self.port} opened at baud rate {self.baudrate}.")
          self.listen()
      except serial.SerialException as e:
          logging.error(f"Error opening serial port: {e}")

  def stop(self):
      """Stop the emulator and close the serial port."""
      self.running = False
      if self.serial_port and self.serial_port.is_open:
          self.serial_port.close()
          logging.info("Serial port closed.")

  def listen(self):
      """Listen for incoming commands and process them."""
      thread = threading.Thread(target=self.read_loop, daemon=True)
      thread.start()

  def read_loop(self):
      """Read data from the serial port in a loop."""
      buffer = ''
      while self.running:
          if self.serial_port.in_waiting:
              data = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='ignore')
              buffer += data
              if '\r' in buffer or '\n' in buffer:
                  commands = buffer.strip().split('\r')
                  for cmd in commands:
                      if cmd:
                          self.process_command(cmd.strip())
                  buffer = ''
          time.sleep(0.1)

  def process_command(self, command: str):
      """Process a single AT command."""
      logging.info(f"Received command: {command}")
      if self.echo:
          self.send_response(command)
      # Correctly handle commands with '?' by splitting on '?' first
      base_command = command.split('=')[0].split('?')[0] + ('?' if '?' in command else '')
      handler = self.command_handlers.get(base_command, self.handle_unknown)
      try:
          response = handler(command)
          if response is not None:
              self.send_response(response)
          if not self.quiet:
              self.send_response('OK')
      except ATCommandError as e:
          self.send_response(f"ERROR: {e}")
      except Exception as e:
          logging.error(f"Unexpected error: {e}")
          self.send_response('ERROR')

  def send_response(self, response: str):
      """Send a response back over the serial port."""
      if self.verbose:
          response = f"\r\n{response}\r\n"
      else:
          response = f"{response}\r\n"
      self.serial_port.write(response.encode('utf-8'))

  # Command handlers

  def handle_at(self, command: str):
      """Handle basic AT command."""
      pass  # No action needed, OK will be sent automatically

  def handle_ate0(self, command: str):
      """Turn off echo."""
      self.echo = False

  def handle_ate1(self, command: str):
      """Turn on echo."""
      self.echo = True

  def handle_ati(self, command: str):
      """Display device information."""
      return f"{self.simulated_state['manufacturer']} {self.simulated_state['model']}"

  def handle_gmi(self, command: str):
      """Display manufacturer name."""
      return self.simulated_state['manufacturer']

  def handle_gmm(self, command: str):
      """Display device model."""
      return self.simulated_state['model']

  def handle_gmr(self, command: str):
      """Display firmware revision."""
      return self.simulated_state['revision']

  def handle_csq(self, command: str):
      """Display signal strength."""
      return f"+CSQ: {self.simulated_state['signal_strength']},99"

  def handle_creg(self, command: str):
      """Display network registration status."""
      return f"+CREG: 0,{self.simulated_state['registration_status']}"

  def handle_cops(self, command: str):
      """Display current operator."""
      return f'+COPS: 0,0,"{self.simulated_state["operator"]}",6'

  def handle_cmgf(self, command: str):
      """Set or display SMS message format."""
      if '=' in command:
          mode = command.split('=')[1]
          if mode in ['0', '1']:
              self.sms_mode = int(mode)
          else:
              raise ATCommandError("Invalid mode")
      else:
          return f"+CMGF: {self.sms_mode}"

  def handle_cmgs(self, command: str):
      """Send SMS message."""
      if self.sms_mode == 1:
          # Text mode
          self.send_response("> ")  # Prompt for input
          message = self.read_sms_message()
          self.simulated_state['sms_storage'].append({'status': 'SENT', 'message': message})
          return '+CMGS: 1'  # Return message reference
      else:
          # PDU mode
          raise ATCommandError("PDU mode not supported in this emulator")

  def handle_cmgr(self, command: str):
      """Read SMS message."""
      # Implement appropriate logic to read messages from storage
      return '+CMGR: "REC UNREAD","1234567890",,"21/09/01,12:34:56+00"\r\nHello, World!'

  def handle_cmgl(self, command: str):
      """List SMS messages."""
      # Implement appropriate logic to list messages
      return '+CMGL: 1,"REC UNREAD","1234567890",,"21/09/01,12:34:56+00"\r\nHello, World!'

  def handle_cmgd(self, command: str):
      """Delete SMS message."""
      # Implement appropriate logic to delete messages
      pass

  def handle_cusd(self, command: str):
      """Execute USSD command."""
      # Handle USSD commands
      return '+CUSD: 0,"Your balance is 10.00 USD",15'

  def handle_cgatt(self, command: str):
      """Attach or detach from GPRS service."""
      if '=' in command:
          state = command.split('=')[1]
          if state in ['0', '1']:
              self.simulated_state['gprs_attached'] = int(state)
          else:
              raise ATCommandError("Invalid state")
      else:
          return f"+CGATT: {self.simulated_state['gprs_attached']}"

  def handle_cipstatus(self, command: str):
      """Display IP status."""
      return f"STATE: {self.simulated_state['ip_status']}"

  def handle_cipstart(self, command: str):
      """Start TCP/IP connection."""
      self.simulated_state['ip_status'] = 'CONNECTED'
      return 'OK'

  def handle_cipclose(self, command: str):
      """Close TCP/IP connection."""
      self.simulated_state['ip_status'] = 'IP INITIAL'
      return 'CLOSE OK'

  def handle_unknown(self, command: str):
      """Handle unknown commands."""
      raise ATCommandError("Command not supported")

  def read_sms_message(self) -> str:
      """Read SMS message input from the user."""
      message = ''
      while True:
          data = self.serial_port.read(self.serial_port.in_waiting or 1).decode('utf-8', errors='ignore')
          if data:
              message += data
              if '\x1a' in message:  # Ctrl+Z to end input
                  message = message.replace('\x1a', '')
                  break
      return message.strip()

def main():
  emulator = ATEmulator(port='COM1', baudrate=9600)
  try:
      emulator.start()
      while True:
          time.sleep(1)
  except KeyboardInterrupt:
      logging.info("Stopping emulator.")
  finally:
      emulator.stop()

if __name__ == "__main__":
  main()