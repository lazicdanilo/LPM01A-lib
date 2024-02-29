from src.LPM01A import LPM01A

try:
    lpm = LPM01A("/dev/ttyACM0", 3864000)
    lpm.init_device(mode="ascii", voltage=3300, freq=5000, duration=0)
    lpm.start_capture()
    lpm.read_and_parse_data()
except KeyboardInterrupt:
    print("KeyboardInterrupt detected. Exiting...")
    lpm.stop_capture()
    lpm.deinit_capture()
    exit(0)
