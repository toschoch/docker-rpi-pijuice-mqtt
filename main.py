
import paho.mqtt.client as mqtt
import os
from urllib.parse import urlparse
import logging
import shutil
from apscheduler.schedulers.blocking import BlockingScheduler

if os.path.isfile('.env'):
    from dotenv import load_dotenv
    load_dotenv()

import sys
sys.path.append('/usr/lib/python3.5/dist-packages')  # temporary hack to import the piJuice module

from wrapper import pijuice

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

service_name = "mqtt-pijuice"
device_name = os.environ['BALENA_DEVICE_NAME_AT_INIT']
mqtt_broker_address = urlparse(os.environ['MQTT_BROKER_ADDRESS'])

# Start the SDK
balena_api_key_env_var = 'BALENASDK_API_KEY'
if balena_api_key_env_var in os.environ:
    log.info("balena sdk key found, try to connect...")
    from balena import Balena
    balena = Balena()
    balena.auth.login_with_token(os.environ[balena_api_key_env_var])
else:
    balena = None


# mqtt client
# credentials
log.info("create mqtt client...")
credentials = os.environ.get('MQTT_CREDENTIALS', ':')
if os.path.isfile(credentials):
    with open(credentials, 'r') as fp:
        username, pw = fp.read().split(':')
else:
    username, pw = credentials.split(':')

# Create client
client = mqtt.Client(client_id="{}/{}".format(device_name, service_name))
if len(username) > 0:
    client.username_pw_set(username, pw)
client.enable_logger()
client.reconnect_delay_set(min_delay=1, max_delay=120)

log.info("connect to mqtt broker...")
client.connect(mqtt_broker_address.hostname,
               mqtt_broker_address.port, 60)


def publish_battery_data(juice):
    topic = "{}/battery/charge".format(device_name)
    client.publish(topic, juice['charge'], qos=1, retain=True)

    topic = "{}/battery/temperature".format(device_name)
    client.publish(topic, juice['temperature'], qos=1, retain=True)

    topic = "{}/battery/voltage".format(device_name)
    client.publish(topic, juice['vbat'], qos=1, retain=True)

    topic = "{}/battery/current".format(device_name)
    client.publish(topic, juice['ibat'], qos=1, retain=True)

    topic = "{}/power/input".format(device_name)
    client.publish(topic, juice['power_input'], qos=1, retain=True)

    topic = "{}/pijuice/io/voltage".format(device_name)
    client.publish(topic, juice['vio'], qos=1, retain=True)

    topic = "{}/pijuice/io/current".format(device_name)
    client.publish(topic, juice['iio'], qos=1, retain=True)

    topic = "{}/pijuice/power/input".format(device_name)
    client.publish(topic, juice['power_input_board'], qos=1, retain=True)


# Get all parameters and return as a dictionary
def get_battery_paremeters(pijuice):
    juice = {}

    charge = pijuice.status.GetChargeLevel()
    juice['charge'] = charge['data'] if charge['error'] == 'NO_ERROR' else charge['error']

    # Temperature [C]
    temperature = pijuice.status.GetBatteryTemperature()
    juice['temperature'] = temperature['data'] if temperature['error'] == 'NO_ERROR' else temperature['error']

    # Battery voltage  [V]
    vbat = pijuice.status.GetBatteryVoltage()
    juice['vbat'] = vbat['data'] / 1000 if vbat['error'] == 'NO_ERROR' else vbat['error']

    # Battery current [A]
    ibat = pijuice.status.GetBatteryCurrent()
    juice['ibat'] = ibat['data'] / 1000 if ibat['error'] == 'NO_ERROR' else ibat['error']

    # I/O voltage [V]
    vio = pijuice.status.GetIoVoltage()
    juice['vio'] = vio['data'] / 1000 if vio['error'] == 'NO_ERROR' else vio['error']

    # I/O current [A]
    iio = pijuice.status.GetIoCurrent()
    juice['iio'] = iio['data'] / 1000 if iio['error'] == 'NO_ERROR' else iio['error']

    # Get power input (if power connected to the PiJuice board)
    status = pijuice.status.GetStatus()
    juice['power_input'] = status['data']['powerInput'] if status['error'] == 'NO_ERROR' else status['error']

    # Get power input (if power connected to the Raspberry Pi board)
    status = pijuice.status.GetStatus()
    juice['power_input_board'] = status['data']['powerInput5vIo'] if status['error'] == 'NO_ERROR' else status['error']

    return juice


def update_tag(tag, variable):
    # update device tags
    balena.models.tag.device.set(os.environ['BALENA_DEVICE_UUID'], str(tag), str(variable))


polling_interval = int(os.environ.get('POLLING_INTERVAL', '5'))
log.info("start main loop with polling interval {}s...".format(polling_interval))

# start mqtt client in other thread
log.info("start mqtt client loop...")
client.loop_start()

scheduler = BlockingScheduler()


def read_and_publish_battery_data():

    # Read battery data
    battery_data = get_battery_paremeters(pijuice)
    log.debug("battery data: {}".format(battery_data))

    # publish on mqtt
    publish_battery_data(battery_data)


def update_balena_device_tags():
    log.info("update balena device tags ...")
    battery_data = get_battery_paremeters(pijuice)
    # Update tags
    for key, value in battery_data.items():
        update_tag(key, value)


def publish_free_space():
    free_bytes = shutil.disk_usage('/data').free

    topic = "{}/disk/1/free".format(device_name)
    client.publish(topic, free_bytes, qos=1, retain=True)


job = scheduler.add_job(read_and_publish_battery_data, 'interval', seconds=polling_interval)
job = scheduler.add_job(publish_free_space, 'interval', minutes=1)

if balena is not None:
    job_balena = scheduler.add_job(update_balena_device_tags, 'interval', minutes=10)

scheduler.start()