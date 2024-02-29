from time import sleep
from time import time
from enum import Enum
import re
from src.SerialCommunication import SerialCommunication
from src.CsvWriter import CsvWriter


class LPM01A:
    def __init__(self, port, baud_rate) -> None:
        """
        Initializes the LPM01A device with the given port and baud rate.

        Args:
            port (str): The port where the LPM01A device is connected.
            baud_rate (int): The baud rate for the serial communication.
        """
        self.serial_comm = SerialCommunication(port, baud_rate)
        self.serial_comm.open_serial()
        self.csv_writer = CsvWriter()
        self.csv_writer.write(
            "Current (uA), rx timestamp (ms), board timestamps (ms)\n"
        )

        self.mode = None

        self.board_timestamp_ms = 0
        self.capture_start_ms = 0
        self.num_of_captured_values = 0

    def _a_to_ua(self, a: float) -> float:
        """Converts the current from A to uA.

        Args:
            a (float): The current in A.
        """
        return a * 1_000_000

    def _read_and_parse_ascii(self) -> None:
        """
        Reads and parses the data from the LPM01A device in ASCII mode.
        """
        while True:
            response = self.serial_comm.receive_data()
            if not response:
                continue

            if "TimeStamp:" in response:
                print(
                    f"{response}. Num of received values: {self.num_of_captured_values}"
                )
                try:
                    split_response = response.split(",")
                    match = re.search("TimeStamp: (\d+)s (\d+)ms", split_response[0])
                    if match:
                        self.board_timestamp_ms = (
                            int(match.group(2)) + int(match.group(1)) * 1000
                        )
                except:
                    print(f"Error parsing timestamp: {response}")
                continue

            if "-" in response:
                exponent_sign = "-"
            elif "+" in response:
                exponent_sign = "+"

            try:
                split_response = response.split("-")
                try:
                    current = int(split_response[0])  # Extract the raw current value
                except ValueError:
                    current = int(split_response[0][2:])

                exponent = int(split_response[1])  # Extract the exponent value

                # Apply the exponent with the correct sign
                if exponent_sign == "+":
                    current = current * pow(10, exponent)
                else:
                    current = current * pow(10, ((-1) * exponent))

                current = round(self._a_to_ua(current))

                local_timestamp_ms = int(time() * 1000) - self.capture_start_ms
                self.csv_writer.write(
                    f"{current}, {local_timestamp_ms}, {self.board_timestamp_ms}\n"
                )
                self.num_of_captured_values += 1
            except:
                print(f"Error parsing data: {response}")

    def send_command_wait_for_response(
        self, command: str, expected_response: str = None, timeout_s: int = 5
    ) -> bool:
        """
        Sends a command to the LPM01A device and waits for a response.

        Args:
            command (str): The command to send to the LPM01A device.
            expected_response (str): The expected response from the LPM01A device.
            timeout_s (int): The timeout in seconds to wait for a response.
        """
        tick_start = time()
        self.serial_comm.send_data(command)
        while time() - tick_start < timeout_s:
            response = self.serial_comm.receive_data()
            if response == "":
                continue

            if expected_response:
                if response == expected_response:
                    return True
                else:
                    return False

            response = response.split("PowerShield > ack ")
            try:
                if response[1] == command:
                    return True
            except IndexError:
                return False

        return False

    def init_device(
        self,
        mode: str = "ascii",
        voltage: int = 3300,
        freq: int = 5000,
        duration: int = 0,
    ) -> None:
        """
        Initializes the LPM01A device with the given mode, voltage, frequency, and duration.

        Args:
            mode (str): The mode for the LPM01A device. Currently only supports "ascii".
            voltage (int): The voltage for the LPM01A device.
            freq (int): The frequency for the LPM01A device.
            duration (int): The duration for the LPM01A device.
        """

        self.mode = mode
        self.send_command_wait_for_response("htc")

        if self.mode == "ascii":
            self.send_command_wait_for_response(f"format ascii_dec")
        else:
            raise NotImplementedError
            self.send_command_wait_for_response(f"format bin_hexa")

        self.send_command_wait_for_response(f"volt {voltage}m")
        self.send_command_wait_for_response(f"freq {freq}")
        self.send_command_wait_for_response(f"acqtime {duration}")

    def start_capture(self) -> None:
        """
        Starts the capture of the LPM01A device.
        """
        self.send_command_wait_for_response("start")

    def stop_capture(self) -> None:
        """
        Stops the capture of the LPM01A device.
        """
        self.send_command_wait_for_response(
            "stop", expected_response="PowerShield > Acquisition completed"
        )
        self.send_command_wait_for_response("hrc")

    def deinit_capture(self) -> None:
        """
        Deinitializes the capture of the LPM01A device.
        """
        self.csv_writer.close()
        self.serial_comm.close_serial()

    def read_and_parse_data(self):
        self.capture_start_ms = int(time() * 1000)
        if self.mode == "ascii":
            self._read_and_parse_ascii()
        else:
            raise NotImplementedError
