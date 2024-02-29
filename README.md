# LPM01A-lib

## Description

This is a Python library for the [X-NUCLEO-LPM01A](https://www.st.com/en/evaluation-tools/x-nucleo-lpm01a.html) STM32 Power shield, Nucleo expansion board for power consumption measurement.

For more information about the X-NUCLEO-LPM01A communication protocol please refer to the [UM2269 Getting started with PowerShield firmware](https://www.st.com/resource/en/user_manual/dm00418905-getting-started-with-powershield-firmware-stmicroelectronics.pdf)

## Prerequisites

- [PySerial](https://pypi.org/project/pyserial/)

## Usage

```python
from src.LPM01A import LPM01A


lpm = LPM01A("/dev/ttyACM0", 3864000)
lpm.init_device(mode="ascii", voltage=3300, freq=5000, duration=0)
lpm.start_capture()
lpm.read_and_parse_data()
```

## Limitations

As this driver can work with ASCII mode only, the acquisition frequency of the LPM01A is limited to maximum of 50k samples / second.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
