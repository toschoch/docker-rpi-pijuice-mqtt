import logging
import os
import time
log = logging.getLogger(__name__)
try:
    from pijuice import PiJuice

    log.info("connect to pijuice...")
    pijuice = PiJuice(1, 0x14)
    while not os.path.exists('/dev/i2c-1'):
        log.info("Waiting to identify PiJuice...")
        time.sleep(1)

except (ImportError, FileNotFoundError):

    log.info("use pijuice mock...")
    import wrapper.pijuice_mock.status
    import wrapper.pijuice_mock as pijuice

