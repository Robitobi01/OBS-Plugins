import contextlib
import select
import socket
import struct
import time

import obspython as obs

# Create a text source called "stat_counter" in OBS

port = 8192
last_received_count = 0
text_template = ''
should_sync = False
current_count = 0
goal_count = 1
sample_time = 20
client_socket = None
last_values = {}

# Incase the sript gets reloaded
try:
    server_socket.close()
except:
    pass

server_socket = socket.socket()
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('127.0.0.1', port))
server_socket.listen()


@contextlib.contextmanager
def create_obs_data():
    data = obs.obs_data_create()
    yield data
    obs.obs_data_release(data)


@contextlib.contextmanager
def get_source_settings(source):
    settings = obs.obs_source_get_settings(source)
    yield settings
    if settings is not None:
        obs.obs_data_release(settings)


def get_source_by_name(name):
    sources = obs.obs_enum_sources()
    if sources is not None:
        for source in sources:
            if source is not None:
                source_id = obs.obs_source_get_id(source)
                source_name = obs.obs_source_get_name(source)
                if 'text_ft2_source' in source_id and source_name == name:
                    return source
    return None


def script_load(settings):
    print('The script just loaded!')
    global port
    obs.timer_add(game_tick, 50)
    source = get_source_by_name('stat_counter')
    with create_obs_data() as settings:
        obs.obs_data_set_string(settings, 'text', '0')
        obs.obs_data_set_int(settings, 'goalCount', 0)
        obs.obs_source_update(source, settings)


def script_properties():
    props = obs.obs_properties_create()
    obs.obs_properties_add_text(props, 'text', 'Displayed text', obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_int(props, 'goalCount', 'Number used as goal amount', 1, 2147483647, 1)
    obs.obs_properties_add_int(props, 'timespan', 'Seconds timespan to sample average', 1, 2147483647, 60)
    obs.obs_properties_add_bool(props, 'shouldSync',
                                'Should stats be synced to actual value instead of counting from 0?')
    return props


def script_description():
    desc = 'A script that provides a real-time stat counter for your stream!\n' \
           'Requires Cutelessmod 0.03+ and Python 3.6 to work\n\n' \
           'Create a text source called "stat_counter" (Case sensitive)\n' \
           'Enter the wanted text in the field below\n\n' \
           '%s will get replaced by the stat value\n' \
           '%g will get replaced by the defined goal\n' \
           '%p will get replaced by 2 digit % based on value and goal\n' \
           '%h will get replaced by the speed per h sampled over timespan'
    return desc


def script_update(settings):
    global text_template
    global should_sync
    global goal_count
    global sample_time
    text_template = obs.obs_data_get_string(settings, 'text')
    goal_count = obs.obs_data_get_int(settings, 'goalCount')
    sample_time = obs.obs_data_get_int(settings, 'timespan')
    should_sync = obs.obs_data_get_bool(settings, 'shouldSync')


def script_unload():
    print('The script unloaded!')


def game_tick():
    global server_socket
    global client_socket
    global counter_text
    global current_count
    global last_received_count
    source = get_source_by_name('stat_counter')

    now = int(time.time())

    for value in list(last_values):
        if value < now - sample_time:
            del last_values[value]

    # with get_source_settings(source) as settings:
    #     if settings is None:
    #         return
    #     current_text = obs.obs_data_get_string(settings, 'text')

    if select.select([server_socket], [], [], 0)[0]:
        (s, a) = server_socket.accept()
        print('Accepted connection from:' + str(a))
        if client_socket:
            client_socket.close()
        client_socket = s
    if client_socket:
        while select.select([client_socket], [], [], 0)[0]:
            # The Java OutputStream adds 2 length bytes when using writeUTF()
            data = None
            try:
                byte_count = struct.unpack('>h', client_socket.recv(2))[0]
                data = client_socket.recv(byte_count)
            except:
                print('Client disconnected!')
                try:
                    client_socket.close
                    client_socket = None
                    break
                except:
                    pass
            if data:
                data = data.decode('UTF-8')
                # print('Received data: ' + data)
            if data and 'increase stat: ' in data:
                amount = int(data.split('increase stat: ')[1])
                current_count += amount
                values = []
                if now in last_values:
                    values = last_values[now]
                values.append(amount)
                last_values[now] = values
            if data and 'sync stat: ' in data and should_sync:
                current_count = int(data.split('sync stat: ')[1])

    with create_obs_data() as settings:
        percent = 0
        average = 0
        if (current_count and goal_count):
            percent = round(max(current_count, 1) / (goal_count / 100), 2)
        if (last_values):
            for value_list in last_values.values():
                if (value_list):
                    average += sum(value_list)
        average *= (3600 / sample_time) / 1000
        average = min(average, 720000)
        average = str('{:05.2f}'.format(round(average, 2)))
        obs.obs_data_set_string(settings, 'text',
                                text_template.replace('%s', str(current_count)).replace('%g', str(goal_count)).replace(
                                    '%p', str(percent) + '%').replace('%h', average + 'k per hour'))
        obs.obs_source_update(source, settings)
