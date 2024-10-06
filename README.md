# PB2Works Expanded PB2 Authority Webserver

This is webserver, responsible for:
- Managing the database
- Managing login tokens.
- Managing maps
- Allowing map designers to modify their maps using ALE
- Serving mapdata to game servers that do not have mapdata for specified map.
- Managing server list
- Managing users.
- Handling registration page.

Those qualities are the reason we hardcoded authority webserver, it is better to have only 1 authority webserver that has all those qualities in order to ensure consistent gameplay between different game servers.

If you want to self host authority webserver, here it is:

First of all, you need python, once you have installed it, run `pip install -r requirements.txt` in this directory, and wait for it to complete.

Now write `python -m asyncio` IN SAME DIRECTORY and write: 
```py
>>> import asyncio
>>> import utils
>>> await utils.dbCreateTables()
```

There should be `db.sqlite` in your directory now. You can now run webserver by `python webserver.py`

You might also want to edit `config.py` if you are hosting this on a VPS which also houses your game server.