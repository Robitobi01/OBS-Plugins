import contextlib
import subprocess
import socket

import obspython as obs

# Create a text source called "stat_counter" in OBS

update_freuqency = 1000  # in ms


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
    obs.timer_add(update_title, update_freuqency)


def script_description():
    desc = 'A script that provides spotify song titles!\n' \
           'Works by using the spotify application window name\n' \
           'Requires wmctrl and Python 3.6 to work\n' \
           'Create a text source called "song_title" (Case sensitive)\n'
    return desc


def script_unload():
    print('The script unloaded!')


def update_title():
    source = get_source_by_name('song_title')
    title = subprocess.run("wmctrl -pl | grep $(ps -ef | grep '[/]usr/share/spotify' | awk '{print $2}' | head -1)",
                           shell=True, stdout=subprocess.PIPE, timeout=1).stdout.decode('utf-8').strip()
    hostname = socket.gethostname()
    if hostname in title:
        title = title.split(socket.gethostname(), maxsplit=1)[1].strip()
        if title == 'Spotify Premium':
            title = ''
        title += ' ' * 25
    with create_obs_data() as settings:
        obs.obs_data_set_string(settings, 'text', title)
        obs.obs_source_update(source, settings)
