## Plugins for Open Broadcaster Software

### stat_plugin
Displays a text string based on information send by [CutelessMod](https://github.com/Nessiesson/CutelessMod). Information from the game is send over with a local TCP connection on port 8192. Requires a text source called `stat_counter` where the string will be displayed.
* `%s` will be replaced by the stat value send over from CutelessMod
* `%g` will be set to the defined goal in the plugin settings
* `%p` will get replaced by a 2 digit % based on value and goal
* `%h` will be replaced by the speed per h sampled over the configured time span

For example `Pickuses: %s/%g %p | %hk per h` will get displayed as `Pickuses: 87348/100000 87.35% | 23.33k per hour`


### spotify_plugin
Shows the current playing song title from a linux spotify premium client. Requires a text source called `song_title` where the song title will be put. Based on reading the song title from the window title via wmctrl. Update frequency defaults to 1s but can be adjusted via the variable `update_freuqency`.    