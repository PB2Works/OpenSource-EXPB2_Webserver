import string
import random
import hashlib
from typing import Optional, TypeVar
from urllib.parse import unquote
from xml.etree import ElementTree

import aiohttp
from contextlib import asynccontextmanager

import aiosqlite

import config

def parseKVString(val: str) -> "dict[str, str]":
    ret = {}
    for pair in val.split("&"):
        if not ("=" in pair):
            continue
        key, _, value = pair.partition("=")
        ret[key] = value
    return ret

###############################################################

@asynccontextmanager
async def get_db():
    try:
        db = await aiosqlite.connect(config.db_filename)
        await db.execute("PRAGMA foreign_keys=ON;")
        yield db
    finally:
        await db.close()

async def dbCreateTables():
    async with get_db() as db:
        cursor = await db.cursor()
        await cursor.execute(
            """
            CREATE TABLE PB_USERS (
                login   VARCHAR(30) PRIMARY KEY,
                display VARCHAR(60),
                salt    VARCHAR(20),
                hash    TEXT,
                skins   VARCHAR(11),
                flags   INTEGER
            );
            """
        )
        await cursor.execute(
            """
            CREATE TABLE PB_SERVERS (
                key           VARCHAR(15) PRIMARY KEY,
                holder        VARCHAR(30) REFERENCES PB_USERS(login),
                holderDisplay VARCHAR(10)
            );
            """
        )
        await cursor.execute(
            """
            CREATE TABLE IP_TO_LOGIN_MAP (
                ip     VARCHAR(15),
                login  REFERENCES PB_USERS(login)
            );
            """
        )
        await db.commit()

#####################################################################################

class AuthorizeErrorCodes:
    DOESNT_EXIST = 0
    HASH_UNSUPPORTED = 1
    WRONG_PASSWORD = 2

class PlayerFlags:
    DEVELOPER     = 1 << 0
    ADMINISTRATOR = 1 << 1

class AuthorizedUser:
    def __init__(self, login: str, display: str, salt: str, hash: str, skins: str, flags: int):
        self.login = login
        self.display = display
        self.salt = salt
        self.hash = hash
        self.skins = skins
        self.flags = flags
    
    def isAdmin(self):
        return self.flags & PlayerFlags.ADMINISTRATOR

async def authorize(cursor: aiosqlite.Cursor, login: str, password: str):
    await cursor.execute(
        """
        SELECT display, salt, hash, skins, flags
        FROM PB_USERS
        WHERE login = ?
        """, 
        (login,)
    )
    row = await cursor.fetchone()
    if not row:
        return AuthorizeErrorCodes.DOESNT_EXIST
    
    display: str = row[0]
    salt   : str = row[1]
    hash   : str = row[2]
    skins  : str = row[3]
    flags  : int = row[4]
        
    alg, _, ahash = hash.partition(":")
    if alg == "sha256":
        nhash = hashlib.sha256((salt + password).encode()).hexdigest()
    else:
        return AuthorizeErrorCodes.HASH_UNSUPPORTED
    if nhash != ahash:
        return AuthorizeErrorCodes.WRONG_PASSWORD
    return AuthorizedUser(
        login = login,
        display = display,
        salt = salt,
        hash = hash,
        skins = skins,
        flags = flags
    )

async def dbCreateUser(
    db: aiosqlite.Connection,
    login: str,
    display: str,
    password: str,
    dmSkin: int,
    coopSkin: int,
    flags: int
):
    assert len(login) > 0, "Login is too short."
    assert len(display) > 0, "Display is too short."
    
    assert dmSkin < 100_000, "dmSkin is higher than 99,999"
    assert coopSkin < 100_000, "coopSkin is higher than 99,999"
    
    assert len(login) < 31, "Login length bypasses 30 limit."
    assert len(display) < 61, "Display length bypasses 60 limit."

    assert login.replace(" ", "").isalnum(), "Login isn't alphanumeric."
    assert password.isalnum(), "Password isn't alphanumeric."

    assert login.lower() == login, "Login is not lowercase."

    salt = "".join([random.choice(string.ascii_letters + string.digits) for _ in range(20)])
    hash = "sha256:" + hashlib.sha256((salt + password).encode()).hexdigest()

    cursor = await db.cursor()
    await cursor.execute(
        """
        SELECT login 
        FROM PB_USERS 
        WHERE login = ?
        """, 
        (login,)
    )
    assert not (await cursor.fetchone()), f"User `{login}` already exists."
    await cursor.execute(
        """
        INSERT INTO PB_USERS (login, display, salt, hash, skins, flags) 
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (login, display, salt, hash, f"{dmSkin}|{coopSkin}", flags)
    )
    await db.commit()

#############################################################################################

async def dbFetchServer(cursor: aiosqlite.Cursor, key: str):
    await cursor.execute(
        """
        SELECT holder, holderDisplay
        FROM PB_SERVERS
        WHERE key = ?
        """,
        (key,)
    )
    return await cursor.fetchone()

async def dbCreateServerKey(db: aiosqlite.Connection, holder: str):
    assert len(holder) < 30, "Holder login is too long."
    assert len(holder) > 0, "Holder login is inexistant."
    
    cursor = await db.cursor()
    await cursor.execute(
        """
        SELECT key
        FROM PB_SERVERS
        WHERE holder = ?
        """,
        (holder,)
    )
    
    row = await cursor.fetchone()
    assert not row, "There is already server key for holder."
    key = "".join([random.choice(string.digits + string.ascii_letters) for _ in range(15)])
    
    await cursor.execute("INSERT INTO PB_SERVERS VALUES (?, ?)", (key, holder))
    await db.commit()
    return key


###############################################################################################

def upgrade_xml(content: str):
    result = ElementTree.fromstring("<r>" + content + "</r>")
    for element in result.findall("trigger"):
        for i in range(1, 11):
            type = element.attrib.pop(f"actions_{i}_type", "-1")
            argA = element.attrib.pop(f"actions_{i}_targetA", "")
            argB = element.attrib.pop(f"actions_{i}_targetB", "")
            element.attrib[f"a{i}"] = f"{type}|{argA}|{argB}"
    return ElementTree.tostring(result).decode()[len("<r>"):-len("</r>")]

####################################################################################################
# QPACK AREA
####################################################################################################


base = "0123456789abcdefghijklmnopqrstuwxyzABCDEFGHIJKLMNOPQRSTUWXYZ_()$@~!.,*-+;:?<>/#%&"
patterns = []
cursor = 0


def add_rule(item1: str, item2: str = None):
    global cursor
    if not item2:
        item2 = "^" + base[cursor]
        cursor += 1
    patterns.append([item1, item2])


add_rule("^", "[^]")
add_rule('" /><player x="')
add_rule('" /><enemy x="')
add_rule('" /><door x="')
add_rule('" /><box x="')
add_rule('" /><gun x="')
add_rule('" /><pushf x="')
add_rule('" /><decor x="')
add_rule('" /><trigger enabled="true')
add_rule('" /><trigger enabled="false')
add_rule('" /><timer enabled="true')
add_rule('" /><timer enabled="false')
add_rule('" /><inf mark="')
add_rule(' /><bg x="')
add_rule(' /><lamp x="')
add_rule(' /><region x="')
add_rule('<player x="')
add_rule('" damage="')
add_rule('" maxspeed="')
add_rule('" model="gun_')
add_rule('" model="')
add_rule('" botaction="')
add_rule('" ondeath="')
add_rule('" actions_')
add_rule('_targetB="')
add_rule('_type="')
add_rule('_targetA="')
add_rule('" team="')
add_rule('" side="')
add_rule('" command="')
add_rule('" flare="')
add_rule('" power="')
add_rule('" moving="true')
add_rule('" moving="false')
add_rule('" tarx="')
add_rule('" tary="')
add_rule('" tox="')
add_rule('" toy="')
add_rule('" hea="')
add_rule('" hmax="')
add_rule('" incar="')
add_rule('" char="')
add_rule('" maxcalls="')
add_rule('" vis="false')
add_rule('" vis="true')
add_rule('" use_on="')
add_rule('" use_target="')
add_rule('" upg="0^')
add_rule('" upg="')
add_rule("^fgun_")
add_rule('" addx="')
add_rule('" addy="')
add_rule('" y="')
add_rule('" w="')
add_rule('" h="')
add_rule('" m="')
add_rule('" at="')
add_rule('" delay="')
add_rule('" target="')
add_rule('" stab="')
add_rule('" mark="')
add_rule("0^T0^3")
add_rule("0^x^y0^z0^h1^")
add_rule(
    "^m3^o-1^m3^p0^m3^n0^m4^o-1^m4^p0^m4^n0^m5^o-1^m5^p0^m5^n0^m6^o-1^m6^p0^m6^n0^m7^o-1^m7^p0^m7^n0^m8^o-1^m8^p0^m8^n0^m9^o-1^m9^p0^m9^n0^m10^o-1^m10^p0^m10^n0"
)
add_rule(
    "^m5^o-1^m5^p0^m5^n0^m6^o-1^m6^p0^m6^n0^m7^o-1^m7^p0^m7^n0^m8^o-1^m8^p0^m8^n0^m9^o-1^m9^p0^m9^n0^m10^o-1^m10^p0^m10^n0"
)
add_rule("^A0^B0^C130^D130^q")
add_rule('0^u0.4^t1"^')
add_rule("0^Q1")
add_rule("0^R")
add_rule("0^S")
add_rule("0^Q-")
add_rule("0^Q")
add_rule('" /><water x="')
add_rule('" forteam="')
add_rule("^Ttrue")
add_rule("true")
add_rule("false")
add_rule("^m2^o-1^m2^p0^m2^n0^)")
add_rule("pistol")
add_rule("rifle")
add_rule("shotgun")
add_rule("real_")


def qpack_compress(data: str):
    for i1, i2 in patterns:
        data = data.replace(i1, i2)
    return "<q." + data.replace("&", "[i]").replace("=", "[eq]")


def qpack_decompress(data: str):
    data = data.replace("[i]", "&").replace("[eq]", "=")
    for i1, i2 in patterns[::-1]:
        data = data.replace(i2, i1)
    if data[:3] == "<q.":
        data = data[3:]
    return data

#################################################################################

T = TypeVar("T")
def exget(dic: "dict[str, T]", key: str) -> Optional[T]:
    if not dic.get(key):
        return None
    return unquote(str(dic[key]))