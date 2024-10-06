from __future__ import annotations
import asyncio

from typing import Optional
import os
import json
import string
import random
import flask
import async_timeout
import xml.etree.ElementTree as ET

import uvicorn
import fastapi
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette import websockets

import utils
from utils import authorize, AuthorizedUser, AuthorizeErrorCodes, exget
import config

maps = list(map(lambda name: name.replace('.xml', ''), os.listdir('./maps')))
dm_skins = [1,2,3,4,6,7,8,9,11,12,13,14,15,16,17,18,19,21,22,23,24,25,26,
	27,28,29,31,32,33,34,35,36,37,41,42,43,44,45,46,47,48,49,61,
	69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,
	90,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,
	145,146,147,148,149,150]
tdm_skins = [73, 75, 77, 79, 81, 83, 85, 87, 89]

app = fastapi.FastAPI(
	title = config.name,
	docs_url=None,
	redoc_url=None
)
flapp = flask.Flask(__name__) # For templated HTML

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/crossdomain.xml")
async def get_crossdomain() -> str:
	return fastapi.Response(
		"""
		<cross-domain-policy>
			<!-- <allow-access-from domain="*" to-ports="80" secure="false" /> -->
			<allow-access-from domain="*" to-ports="80,10000-10100,8880" secure="false"/>
		</cross-domain-policy>
	""",
		media_type="application/xml",
	)

@app.get("/play")
async def get_play():
	return RedirectResponse(url="./static/resource/pb2_re34_alt_p.app.zip")

async def login_user(login, password):
	async with utils.get_db() as db:
		user = await authorize(await db.cursor(), login, password)
		if user not in AECT:
			return user

	return None

async def try_login(login, password):
	user = await login_user(login, password)
	return user != None

async def showPage(name, request):
	cookies = request.cookies
	logged_in = False

	login = None
	password = None
	skin1 = "1"
	skin2 = "1"
	display = ""
	if 'l' in cookies:
		login = cookies['l']
	if 'p' in cookies:
		password = cookies['p']

	if login != None and password != None:
		user = await login_user(login, password)
		if user != None:
			logged_in = True
			skin1, skin2 = user.skins.split('|')
			display = user.display

	output = None
	with flapp.app_context():
		output = flask.render_template(name + ".html", logged_in=logged_in, login=login, nickname=display, skin1=skin1, skin2=skin2) 
	return HTMLResponse(content=output, status_code=200)

@app.get("/login", response_class=HTMLResponse)
async def showLoginPage(request: fastapi.Request):
	return await showPage("login", request)

@app.get("/members", response_class=HTMLResponse)
async def showMembersPage(request: fastapi.Request):
	return await showPage("members", request)

@app.get("/register", response_class=HTMLResponse)
async def showRegisterPage(request: fastapi.Request):
	return await showPage("register", request)

@app.get("/account", response_class=HTMLResponse)
async def showAccountPage(request: fastapi.Request):
	return await showPage("account", request)

@app.get("/", response_class=HTMLResponse)
async def showIndexPage(request: fastapi.Request):
	return await showPage("index", request)

###############################################################################################

# AuthorizedErrorCodeTranslation
AECT = {
	AuthorizeErrorCodes.DOESNT_EXIST: "Account doesn't exist",
	AuthorizeErrorCodes.HASH_UNSUPPORTED: "Hash isn't supported.",
	AuthorizeErrorCodes.WRONG_PASSWORD: "Password is wrong."
}

#############################################################

tokens: dict[str, AuthorizedUser] = {}
loginToToken: dict[str, str] = {}

def invalidateToken(token: str):
	if token in tokens:
		del loginToToken[tokens[token].login]
		del tokens[token]

def respondText(text: str):
	return fastapi.Response(text)

def respondTextError(text: str):
	return PlainTextResponse(text, status_code = 403)

def respondTextSuccess(text: str):
	return PlainTextResponse(text, status_code = 200)

@app.post("/token.php")
async def handle_token(request: fastapi.Request):
	try:
		data = utils.parseKVString((await request.body()).decode())
	except UnicodeDecodeError:
		return respondText("error|Web: Unable to decode body.")

	req: Optional[str] = exget(data, "rq")
	token: Optional[str] = exget(data, "tok")
	login: Optional[str] = exget(data, "l")
	password: Optional[str] = exget(data, "p")

	if not (req in ["extract", "create"]):
		return respondText("error|Web: Unsupported action.")
	
	if (req == "create") and ((not login) or (not password)):
		return respondText("error|Web: One of credential is empty.")
	if (req == "extract") and (not token):
		return respondText("error|Web: Token isn't passed.")
	
	if req == "extract":
		if not (token in tokens):
			return respondText("error|Web: Token doesn't exist.")
		data = tokens[token]
		invalidateToken(token)
		return respondText("ok|" + json.dumps([
			data.login,
			data.display,
			data.skins,
			data.flags
		]))
	else:
		if not login.replace(" ", "").isalnum():
			return respondText("error|Web: Login is not alphanumeric.")
		if not password.isalnum():
			return respondText("error|Web: Password is not alphanumeric.")
		if len(login) > 30:
			return respondText("error|Web: Login is too long.")
		
		async with utils.get_db() as db:
			result = await authorize(await db.cursor(), login, password)

		if result in AECT:
			return respondText("error|Web: " + AECT[result])
		
		if login in loginToToken:
			return respondText("ok|" + loginToToken[login])
		token = "".join([random.choice(string.ascii_letters + string.digits) for _ in range(config.token_length)])
		while token in tokens:
			token = "".join([random.choice(string.ascii_letters + string.digits) for _ in range(config.token_length)])
		
		tokens[token] = result
		loginToToken[login] = token
		asyncio.get_running_loop().call_later(
			config.token_timeout,
			invalidateToken,
			token
		)
		return respondText("ok|" + token)


class GameServer:
	def __init__(self, name: str, host: str, port: int, holder: str, holderDisplay: str):
		self.name = name
		self.host = host
		self.port = port
		self.holder = holder
		self.holderDisplay = holderDisplay
		self.totalConnected = 0

gameServers: list[GameServer] = []

@app.websocket("/server")
async def server_ws(websocket: fastapi.WebSocket):
	await websocket.accept()
	newServer = None
	try:
		async with async_timeout.timeout(5):
			data = await websocket.receive_json()
		key = data["key"]
		async with utils.get_db() as db:
			holder = await utils.dbFetchServer(await db.cursor(), key)
			if not holder:
				return await websocket.send_json({"error": "Key is invalid."})
		if not data["name"].replace(".", "").replace(" ", "").isalnum():
			return await websocket.send_json({"error": "Name is not alphanumeric."})

		newServer = GameServer(
			name          = data["name"],
			host          = websocket.client.host,
			port          = int(data["port"]),
			holder        = holder[0],
			holderDisplay = holder[1]
		)
		if newServer.host == "127.0.0.1":
			newServer.host = config.localhostTo
		for server in gameServers:
			if server.name == newServer.name:
				return await websocket.send_json({"error": "Name is taken."})
			elif server.host == newServer.host:
				if server.port == newServer.port:
					return await websocket.send_json({"error": "Host+Port is taken."})
		
		gameServers.append(newServer)
		await websocket.send_json({"approved": "auth"})

		while True:
			message_data = await websocket.receive_text()
			data = json.loads(message_data)
			rq = data["rq"]
			if rq == "updateStat":
				newServer.totalConnected = int(data["tc"])
				await websocket.send_json({"approved": "updateStat"})
			else:
				await websocket.send_json({"error": "Unknown request."})
	except websockets.WebSocketDisconnect:
		pass
	finally:
		try:
			await websocket.close()
		except RuntimeError:
			pass
		if newServer != None:
			gameServers.remove(newServer)

async def fetch_mapdata(map_id: str, use_pb2: bool = True) -> str:
	mapdata = "<not_published />"
	if map_id in maps:
		with open(f"./maps/{map_id}.xml", "r") as f:
			mapdata = f.read()
		
		if "actions_1_type" in mapdata:
			mapdata = utils.upgrade_xml(mapdata)
			with open(f"./maps/{map_id}.xml", "w") as f:
				f.write(mapdata)
	elif use_pb2:
		pass # TODO: PB2 requesting here
	return mapdata

@app.post("/server.php")
async def server_post(request: fastapi.Request):
	try:
		data = utils.parseKVString((await request.body()).decode())
	except UnicodeDecodeError:
		return respondText("")
	rq = exget(data, "rq")
	if not (rq in ["srvrs", "cmap"]):
		return respondText("")
	if rq == "srvrs":
		response = []
		for index in range(len(gameServers)):
			server = gameServers[index]
			
			displayedName = f"-{server.totalConnected} players- by {server.holderDisplay}"
			displayedName = f"{server.name[:(41 - len(displayedName))]} {displayedName}"

			response.append("|".join([
				displayedName,
				server.host,
				str(server.port),
				str(index)
			]))
		return respondText(";".join(response))
	
	elif rq == "cmap":
		map_id = exget(data, "cmap")
		if not map_id:
			return
		mapdata = await fetch_mapdata(map_id)
		return respondText(utils.qpack_compress(mapdata))


@app.post("/mapdata")
async def get_mapdata(request: fastapi.Request):
	try:
		data = utils.parseKVString((await request.body()).decode())
	except UnicodeDecodeError:
		return respondText("")
	mapID: Optional[str] = exget(data, "mapID")
	if not mapID:
		return respondText("")
	mapdata = await fetch_mapdata(mapID)
	# TODO: Obfuscate mapdata.
	return respondText(utils.qpack_compress(mapdata))

@app.post('/map.php')
async def get_map(request: fastapi.Request):
	try:
		data = utils.parseKVString((await request.body()).decode())
	except UnicodeDecodeError:
		return respondText("")
	mapID: Optional[str] = exget(data, "id")

	if not mapID:
		return ALE_respond("Invalid map name", ALE_MAP_DECLINED)
	if mapID not in maps:
		return ALE_respond("Map doesn't exist", ALE_MAP_DECLINED)
	
	login: Optional[str] = exget(data, "l")
	password: Optional[str] = exget(data, "p")

	if (not login) or (not password):
		return ALE_respond("Login or password is not passed.", ALE_LOGIN_DECLINED)
	if (not login.replace(" ", "").isalnum()) or (not password.isalnum()):
		return ALE_respond("Login or password is not alphanumeric.", ALE_LOGIN_DECLINED)
	
	async with utils.get_db() as db:
		user = await authorize(await db.cursor(), login, password)
	if user in AECT:
		return ALE_respond(AECT[user], ALE_LOGIN_DECLINED)
	
	if not user.isAdmin():
		if not mapID.startswith(f"{user.login}-"):
			return ALE_respond("You are not permitted to access this map.", ALE_MAP_DECLINED)

	mapdata = await fetch_mapdata(mapID, use_pb2 = False)
	if mapdata == "<not_published />":
		return ALE_respond("Map is not published.", ALE_MAP_DECLINED)
	
	return ALE_respond(mapdata.replace('\n', '&#xA;'), 200)

@app.post("/register")
async def register_account(request: fastapi.Request):
	try:
		data = json.loads((await request.body()).decode())
	except:
		return respondTextError("Cannot understand the body.")
	
	login: Optional[str] = exget(data, "login")
	password: Optional[str] = exget(data, "password")
	dm_skin: Optional[str] = exget(data, "skin1")
	tdm_skin: Optional[str] = exget(data, "skin2")


	if (not login) or (not password):
		return respondTextError("Credentials are not passed.")
	if not (8 < len(login) < 31):
		return respondTextError("Login is too long or too short.(8 < x < 31)")
	if (not dm_skin) or (not tdm_skin):
		return respondText("Skins are not passed.")
	if not dm_skin.isnumeric() or not tdm_skin.isnumeric():
		return respondTextError("Skin IDs are not numbers.")
	if (int(dm_skin) not in dm_skins) or (int(tdm_skin) not in tdm_skins):
		return respondTextError("Invalid skin.")
	if not password.isalnum():
		return respondTextError("Password is not alphanumeric.")
	if not login.replace(" ", "").isalnum():
		return respondTextError("Login is not alphanumeric.")
	if login.count(" ") > 1:
		return respondTextError("Login cannot have more than 1 space.")
	if not (login.lower() == login):
		return respondTextError("Login MUST be lowercase.")
	if not (login.strip() == login):
		return respondTextError("If you want to have spaces, have it between characters, not at end.")

	async with utils.get_db() as db:
		cursor = await db.cursor()
		await cursor.execute("SELECT login FROM IP_TO_LOGIN_MAP WHERE ip = ?", (request.client.host,))
		login_ = await cursor.fetchone()
		if login_:
			return respondTextError("You already have account: " + login_[0])
		# TODO: This seems rather error prone
		try:
			await utils.dbCreateUser(db, login, login, password, int(dm_skin), int(tdm_skin), 0)
		except Exception as message:
			return respondTextError(f"{message}")
		await cursor.execute("INSERT INTO IP_TO_LOGIN_MAP VALUES (?, ?)", (request.client.host, login))
		await db.commit()
	return respondTextSuccess("Created account successfully.")

@app.post("/login")
async def login_account(request: fastapi.Request):
	try:
		data = json.loads((await request.body()).decode())
	except:
		return respondTextError("Cannot understand the body.")
	
	login: Optional[str] = exget(data, "login")
	password: Optional[str] = exget(data, "password")

	if (not login) or (not password):
		return respondTextError("Credentials are not passed.")

	if not await try_login(login, password):
		return respondTextError("Wrong username or passowrd")

	return respondTextSuccess("Logged in!")

@app.post("/account")
async def modify_account(request: fastapi.Request):
	try:
		data = json.loads((await request.body()).decode())
	except:
		return respondTextError("Cannot understand the body.")

	allowed_characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789()[]!@#$%^&*-_+=\\|/?,.<>\'"';

	login: Optional[str] = exget(data, "login")
	password: Optional[str] = exget(data, "password")
	dm_skin: Optional[str] = exget(data, "skin1")
	tdm_skin: Optional[str] = exget(data, "skin2")
	display: Optional[str] = exget(data, "display")

	if not display:
		return respondTextError("Display name is not passed.")

	if len(display) > 32:
		return respondTextError("Display name is longer than 32 characters")

	for c in display:
		if not c in allowed_characters:
			return respondTextError(f"Display name contains forbidden character: {c}")

	if (not login) or (not password):
		return respondTextError("Credentials are not passed.")

	if (not dm_skin) or (not tdm_skin):
		return respondTextError("Skins are not passed.")

	if not dm_skin.isnumeric() or not tdm_skin.isnumeric():
		return respondTextError("Skin IDs are not numbers.")
	skin1 = int(dm_skin)
	skin2 = int(tdm_skin)

	if (skin1 not in dm_skins) or (skin2 not in tdm_skins):
		return respondTextError("Invalid skin.")

	async with utils.get_db() as db:
		cursor = await db.cursor()
		user = await authorize(cursor, login, password)
		if user in AECT:
			return respondTextError(f"{AECT[user]}")
		
		newSkins = f"{skin1}|{skin2}"
		if len(newSkins) > 11:
			return respondTextError("Skin somehow goes beyond 11 length? Shouldn't happen")
	
		await cursor.execute("UPDATE PB_USERS SET skins = ?, display = ? WHERE login = ?", (newSkins, display, login))
		await db.commit()
		return respondTextSuccess("Account modified.")
	


@app.get("/whatismyip")
async def whatismyip(request: fastapi.Request):
	return respondText(f"I see you as {request.client.host}")

def ALE_respond(text: str, statusCode: int):
	return fastapi.Response(
		text,
		statusCode,
		{"Access-Control-Allow-Origin": "*"}
	)
ALE_LOGIN_DECLINED = 401
ALE_MAP_DECLINED = 400

known_tags = [
	"box",
	"door",
	"region",
	"pushf",
	"bg",
	"image",
	"water",
	"decor",
	"player",
	"enemy",
	"vehicle",
	"gun",
	"lamp",
	"barrel",
	"trigger",
	"timer",
	"inf",
	"song",
	"lua"
]

@app.post("/upload_map.php")
async def ale_map_upload(request: fastapi.Request):
	try:
		data = utils.parseKVString((await request.body()).decode())
	except UnicodeDecodeError:
		return respondText("")
	
	login: Optional[str] = exget(data, "l")
	password: Optional[str] = exget(data, "p")
	map_name: Optional[str] = exget(data, "mapname")
	map_data: Optional[str] = exget(data, "mapdata")

	if (not login) or (not password):
		return ALE_respond("Login/Password is empty.", ALE_LOGIN_DECLINED)
	elif (not login.replace(" ", "").isalnum()) or (not password.isalnum()):
		return ALE_respond("Login/Password is not alphanumeric.", ALE_LOGIN_DECLINED)
	elif (not map_name) or (not map_data):
		return ALE_respond("Mapname/Mapdata is empty.", ALE_MAP_DECLINED)
	elif (not map_name.replace("-", "").isalnum()):
		return ALE_respond("Mapname is not alphanumeric.", ALE_MAP_DECLINED)

	async with utils.get_db() as db:
		user = await authorize(await db.cursor(), login, password)

	if user in AECT:
		return ALE_respond(AECT[user], ALE_LOGIN_DECLINED)
	
	if (not user.isAdmin()) and (not map_name.startswith(user.login + "-")):
		return ALE_respond(f"Map doesn't begin with `{user.login}-`.", ALE_MAP_DECLINED)

	try:
		tree = ET.fromstring("<r>" + map_data + "</r>")
	except ET.ParseError:
		return ALE_respond("Cannot parse mapdata.", ALE_MAP_DECLINED)
	
	for element in tree:
		if len(element):
			return ALE_respond("XML is formed abnormally.", ALE_MAP_DECLINED)
		if not (element.tag in known_tags):
			return ALE_respond(f"Abnormal element `{element.tag}` found in XML.", ALE_MAP_DECLINED)

	with open(f"./maps/{map_name}.xml", "w") as f:
		f.write(map_data)
		if map_name not in maps:
			maps.append(map_name)
	return ALE_respond("Uploaded.", 200)

@app.post("/maplist.php")
async def get_maplist(request: fastapi.Request):
	try:
		data = utils.parseKVString((await request.body()).decode())
	except UnicodeDecodeError:
		return respondText("")
	
	login: Optional[str] = exget(data, "l")
	password: Optional[str] = exget(data, "p")

	if (not login) or (not password):
		return ALE_respond("Login/Password is empty.", ALE_LOGIN_DECLINED)
	elif (not login.replace(" ", "").isalnum()) or (not password.isalnum()):
		return ALE_respond("Login/Password is not alphanumeric.", ALE_LOGIN_DECLINED)

	async with utils.get_db() as db:
		user = await authorize(await db.cursor(), login, password)

	if user in AECT:
		return ALE_respond(AECT[user], ALE_LOGIN_DECLINED)
	
	# TODO: Figure out which maps to show depending on perms
	# TODO: Maybe don't send all maps at once but have filters, pages, etc.
	shown_maps = maps

	return ALE_respond("Available maps:\n" + '\n'.join(shown_maps), 200)

uvicorn.run(
	app,
	host = config.ip,
	port = config.port
)
