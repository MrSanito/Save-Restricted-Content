# BeastX Save Restricted Content Bot
# Official: @Beastx_Bots | Support: @Beastx_Support | Dev: @Godmrunal
# Original project credits are documented in README.md.

import os
import asyncio
import datetime
import time
import traceback
import threading
import logging
import signal
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger("BeastX")

import motor.motor_asyncio
from pyrogram import Client, filters, enums
from pyrogram.handlers import MessageHandler
from pyrogram.errors import (
    FloodWait, UserIsBlocked, InputUserDeactivated, UserAlreadyParticipant,
    InviteHashExpired, UsernameNotOccupied, InputUserDeactivated,
    UserNotParticipant, UserIsBlocked, PeerIdInvalid,
    ApiIdInvalid, PhoneNumberInvalid, PhoneCodeInvalid, PhoneCodeExpired,
    SessionPasswordNeeded, PasswordHashInvalid
)
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from asyncio.exceptions import TimeoutError
from http.server import BaseHTTPRequestHandler, HTTPServer

# =========================
# BeastX Configuration
# =========================
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                _k, _v = _k.strip(), _v.strip()
                if _k and _k not in os.environ:
                    os.environ[_k] = _v

def required_env(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


LOGIN_SYSTEM = str(os.environ.get("LOGIN_SYSTEM", "True")).lower() in ("true", "1", "yes", "on")
STRING_SESSION = os.environ.get("STRING_SESSION", "").strip() if not LOGIN_SYSTEM else None
BOT_TOKEN = required_env("BOT_TOKEN")
API_ID = int(required_env("API_ID"))
API_HASH = required_env("API_HASH")
ADMINS = int(required_env("ADMINS"))
CHANNEL_ID = os.environ.get("CHANNEL_ID", "").strip()
DB_URI = required_env("DB_URI")
DB_NAME = os.environ.get("DB_NAME", "beastxsavecontentbot").strip() or "beastxsavecontentbot"
WAITING_TIME = int(os.environ.get("WAITING_TIME", "10"))
ERROR_MESSAGE = str(os.environ.get("ERROR_MESSAGE", "True")).lower() in ("true", "1", "yes", "on")

if not LOGIN_SYSTEM and not STRING_SESSION:
    raise RuntimeError("STRING_SESSION is required when LOGIN_SYSTEM=False")

# =========================
# BeastX Database
# =========================
class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users

    def new_user(self, id, name):
        return {"id": id, "name": name, "session": None, "api_id": None, "api_hash": None}

    async def add_user(self, id, name):
        await self.col.insert_one(self.new_user(id, name))

    async def is_user_exist(self, id):
        user = await self.col.find_one({"id": int(id)})
        return bool(user)

    async def total_users_count(self):
        return await self.col.count_documents({})

    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        await self.col.delete_many({"id": int(user_id)})

    async def set_session(self, id, session):
        await self.col.update_one({"id": int(id)}, {"$set": {"session": session}})

    async def get_session(self, id):
        user = await self.col.find_one({"id": int(id)})
        return user.get("session") if user else None

    async def set_api_id(self, id, api_id):
        await self.col.update_one({"id": int(id)}, {"$set": {"api_id": api_id}})

    async def get_api_id(self, id):
        user = await self.col.find_one({"id": int(id)})
        return user.get("api_id") if user else None

    async def set_api_hash(self, id, api_hash):
        await self.col.update_one({"id": int(id)}, {"$set": {"api_hash": api_hash}})

    async def get_api_hash(self, id):
        user = await self.col.find_one({"id": int(id)})
        return user.get("api_hash") if user else None

db = Database(DB_URI, DB_NAME)

# =========================
# BeastX Account Session
# =========================
if STRING_SESSION and not LOGIN_SYSTEM:
    BeastXUser = Client("beastx", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
    BeastXUser.start()
else:
    BeastXUser = None

# =========================
# Help Text
# =========================
HELP_TXT = """**🌟 Help Menu**

**__FOR PRIVATE CHATS__**

__First send the invite link of the chat (unnecessary if the account of string session is already a member), then send the post link.__

**__FOR BOT CHATS__**

__Send a link with '/b/', bot username and message id.__

```text
https://t.me/b/botusername/4321
```

**__MULTI POSTS__**

__Send public/private post links using "from - to" to send multiple messages.__

```text
https://t.me/xxxx/1001-1010
https://t.me/c/xxxx/101 - 120
```

__Spaces in between do not matter.__"""

import os
import asyncio 
import pyrogram
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message 

class batch_temp(object):
    IS_BATCH = {}

async def downstatus(client, statusfile, message, chat):
    while True:
        if os.path.exists(statusfile):
            break

        await asyncio.sleep(3)
      
    while os.path.exists(statusfile):
        with open(statusfile, "r") as downread:
            txt = downread.read()
        try:
            await client.edit_message_text(chat, message.id, f"**Downloaded:** **{txt}**")
            await asyncio.sleep(10)
        except:
            await asyncio.sleep(5)


# upload status
async def upstatus(client, statusfile, message, chat):
    while True:
        if os.path.exists(statusfile):
            break

        await asyncio.sleep(3)      
    while os.path.exists(statusfile):
        with open(statusfile, "r") as upread:
            txt = upread.read()
        try:
            await client.edit_message_text(chat, message.id, f"**Uploaded:** **{txt}**")
            await asyncio.sleep(10)
        except:
            await asyncio.sleep(5)


# progress writer
def progress(current, total, message, type):
    with open(f'{message.id}{type}status.txt', "w") as fileup:
        fileup.write(f"{current * 100 / total:.1f}%")


# start command
@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
    buttons = [[
        InlineKeyboardButton("❣️ Developer", url = "https://t.me/Godmrunal")
    ],[
        InlineKeyboardButton('🔍 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url='https://t.me/Beastx_Support'),
        InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/Beastx_Bots')
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await client.send_message(
        chat_id=message.chat.id, 
        text=f"<b>👋 Hi {message.from_user.mention}, I am Save Restricted Content Bot, I can send you restricted content by its post link.\n\nFor downloading restricted content /login first.\n\nKnow how to use bot by - /help</b>", 
        reply_markup=reply_markup, 
        reply_to_message_id=message.id
    )
    return


# help command
@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    await client.send_message(
        chat_id=message.chat.id, 
        text=f"{HELP_TXT}"
    )

# cancel command
@Client.on_message(filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    batch_temp.IS_BATCH[message.from_user.id] = True
    await client.send_message(
        chat_id=message.chat.id, 
        text="**Batch Successfully Cancelled.**"
    )

def get_dump_chat():
    if not CHANNEL_ID:
        return None
    raw = str(CHANNEL_ID).strip()
    if not raw.startswith("-"):
        if raw.startswith("100"):
            raw = f"-{raw}"
        else:
            raw = f"-100{raw}"
    try:
        return int(raw)
    except ValueError:
        return None


def build_clean_reply_markup(msg: Message):
    if not msg or not msg.reply_markup:
        return None
    keyboard = getattr(msg.reply_markup, "inline_keyboard", None)
    if not keyboard:
        return None
    
    new_keyboard = []
    for row in keyboard:
        new_row = []
        for btn in row:
            text = (getattr(btn, "text", "") or "Link").strip()
            url = getattr(btn, "url", None)
            web_app = getattr(btn, "web_app", None)
            
            if url:
                new_row.append(InlineKeyboardButton(text=text, url=url))
            elif web_app and getattr(web_app, "url", None):
                new_row.append(InlineKeyboardButton(text=text, web_app=web_app))
            elif getattr(btn, "callback_data", None):
                cb_data = btn.callback_data
                if isinstance(cb_data, bytes):
                    cb_data = cb_data.decode("utf-8", errors="ignore")
                new_row.append(InlineKeyboardButton(text=text, callback_data=cb_data[:64]))
        if new_row:
            new_keyboard.append(new_row)
            
    if new_keyboard:
        logger.info("Reconstructed clean inline keyboard with %d row(s) for attachment", len(new_keyboard))
        return InlineKeyboardMarkup(new_keyboard)
    return None


@Client.on_message(filters.text & filters.private & ~filters.command(["start", "help", "cancel", "login", "logout"]))
async def save(client: Client, message: Message):
    # Joining chat
    if "https://t.me/+" in message.text or "https://t.me/joinchat/" in message.text:
        target_acc = None
        if LOGIN_SYSTEM == False:
            if BeastXUser is None:
                await client.send_message(message.chat.id, "String Session is not Set", reply_to_message_id=message.id)
                return
            target_acc = BeastXUser
        else:
            user_data = await db.get_session(message.from_user.id)
            if user_data is None:
                await message.reply("**For Joining Chat You Have To /login First.**")
                return
            api_id = int(await db.get_api_id(message.from_user.id))
            api_hash = await db.get_api_hash(message.from_user.id)
            try:
                target_acc = Client("saverestricted_join", session_string=user_data, api_hash=api_hash, api_id=api_id)
                await target_acc.connect()
            except Exception as e:
                return await message.reply(f"**Session error: {e}**")
        try:
            try:
                await target_acc.join_chat(message.text.strip())
            except UserAlreadyParticipant:
                await client.send_message(message.chat.id, "Chat already Joined", reply_to_message_id=message.id)
                return
            except InviteHashExpired:
                await client.send_message(message.chat.id, "Invalid or Expired Link", reply_to_message_id=message.id)
                return
            except Exception as e: 
                await client.send_message(message.chat.id, f"Error : {e}", reply_to_message_id=message.id)
                return
            await client.send_message(message.chat.id, "Chat Joined Successfully!", reply_to_message_id=message.id)
        finally:
            if LOGIN_SYSTEM == True and target_acc:
                try:
                    await target_acc.disconnect()
                except Exception:
                    pass
        return
    
    if "https://t.me/" in message.text:
        if batch_temp.IS_BATCH.get(message.from_user.id) == False:
            return await message.reply_text("**One Task Is Already Processing. Wait For Complete It. If You Want To Cancel This Task Then Use - /cancel**")
        
        cleaned_text = message.text.strip().rstrip("/")
        datas = cleaned_text.split("/")
        last_seg = datas[-1].split("?")[0].split("#")[0]
        temp = last_seg.split("-")
        try:
            fromID = int(temp[0].strip())
        except ValueError:
            return await message.reply_text("**Invalid message link format.**")
        try:
            toID = int(temp[1].strip())
        except Exception:
            toID = fromID

        if LOGIN_SYSTEM == True:
            user_data = await db.get_session(message.from_user.id)
            if user_data is None:
                await message.reply("**For Downloading Restricted Content You Have To /login First.**")
                return
            api_id = int(await db.get_api_id(message.from_user.id))
            api_hash = await db.get_api_hash(message.from_user.id)
            try:
                acc = Client("saverestricted", session_string=user_data, api_hash=api_hash, api_id=api_id)
                await acc.connect()
            except Exception:
                return await message.reply("**Your Login Session Expired. So /logout First Then Login Again By - /login**")
        else:
            if BeastXUser is None:
                await client.send_message(message.chat.id, f"**String Session is not Set**", reply_to_message_id=message.id)
                return
            acc = BeastXUser
				
        batch_temp.IS_BATCH[message.from_user.id] = False
        for msgid in range(fromID, toID+1):
            if batch_temp.IS_BATCH.get(message.from_user.id): break
            
            # private
            if "https://t.me/c/" in message.text:
                raw_chat = datas[4].strip()
                if raw_chat.startswith("-100"):
                    chatid = int(raw_chat)
                elif raw_chat.startswith("-"):
                    chatid = int("-100" + raw_chat.lstrip("-"))
                else:
                    chatid = int("-100" + raw_chat)
                try:
                    await handle_private(client, acc, message, chatid, msgid)
                except Exception as e:
                    if ERROR_MESSAGE == True:
                        await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)
    
            # bot
            elif "https://t.me/b/" in message.text:
                username = datas[4].strip()
                try:
                    await handle_private(client, acc, message, username, msgid)
                except Exception as e:
                    if ERROR_MESSAGE == True:
                        await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)
            
            # public
            else:
                username = datas[3].strip()

                try:
                    msg = await client.get_messages(username, msgid)
                except UsernameNotOccupied: 
                    await client.send_message(message.chat.id, "The username is not occupied by anyone", reply_to_message_id=message.id)
                    return
                if not msg or msg.empty:
                    logger.info("Public message ID %s is empty or deleted, skipping.", msgid)
                    continue
                dump_chat = get_dump_chat()
                dest_chat = dump_chat if dump_chat else message.chat.id
                reply_id = message.id if dest_chat == message.chat.id else None
                clean_markup = build_clean_reply_markup(msg)
                try:
                    await client.copy_message(dest_chat, msg.chat.id, msg.id, reply_to_message_id=reply_id, reply_markup=clean_markup)
                    logger.info("Copied public message ID %s to chat %s with attached buttons", msgid, dest_chat)
                except Exception as copy_err:
                    copy_err_str = str(copy_err)
                    if dump_chat and dest_chat == dump_chat and any(k in copy_err_str for k in ["CHANNEL_INVALID", "ChannelInvalid", "CHAT_WRITE_FORBIDDEN"]):
                        logger.warning("Dump channel %s failed (%s). Copying directly to user chat...", dest_chat, copy_err)
                        try:
                            await client.copy_message(message.chat.id, msg.chat.id, msg.id, reply_to_message_id=message.id, reply_markup=clean_markup)
                            await client.send_message(message.chat.id, "⚠️ **Notice:** Bot could not post in Dump Channel (Bot lacks Admin permissions). Delivered directly here.")
                            continue
                        except Exception:
                            pass
                    logger.warning("copy_message failed for public message ID %s (%s), falling back to handle_private", msgid, copy_err)
                    try:    
                        await handle_private(client, acc, message, username, msgid)               
                    except Exception as e:
                        logger.error("Error in handle_private for message ID %s: %s", msgid, e)
                        if ERROR_MESSAGE == True:
                            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

            # wait time
            await asyncio.sleep(WAITING_TIME)
        if LOGIN_SYSTEM == True:
            try:
                await acc.disconnect()
            except Exception:
                pass                				
        batch_temp.IS_BATCH[message.from_user.id] = True


async def get_message_with_cache(acc: Client, chatid, msgid: int) -> Message:
    try:
        return await acc.get_messages(chatid, msgid)
    except Exception as e:
        err_str = str(e)
        if "CHANNEL_INVALID" in err_str or "ChannelInvalid" in type(e).__name__:
            logger.info("Channel %s not resolved in session cache. Warming up dialogs to load peer access_hash...", chatid)
            found = False
            try:
                async for dialog in acc.get_dialogs(limit=250):
                    if dialog.chat and (dialog.chat.id == chatid or getattr(dialog.chat, "username", None) == chatid):
                        found = True
                        break
            except Exception as d_err:
                logger.warning("Dialogs warmup error: %s", d_err)
            
            try:
                return await acc.get_messages(chatid, msgid)
            except Exception as retry_err:
                if not found:
                    raise Exception(f"Source Channel Error: Your logged-in Telegram account has NOT joined this channel/group ({chatid}). Please join it first using the Telegram account logged into the bot.")
                raise Exception(f"Source Channel Error: Telegram could not fetch message {msgid} from channel {chatid} ({retry_err})")
        raise Exception(f"Source Channel Error: {e}")


# handle private
async def handle_private(client: Client, acc, message: Message, chatid, msgid: int):
    logger.info("Processing message ID %s from chat %s for user %s", msgid, chatid, message.from_user.id)
    msg: Message = await get_message_with_cache(acc, chatid, msgid)
    if not msg or msg.empty:
        logger.warning("Message ID %s is empty or deleted", msgid)
        return 
    msg_type = get_message_type(msg)
    if not msg_type:
        logger.warning("Unknown message type for message ID %s", msgid)
        return 
    
    dump_chat = get_dump_chat()
    reply_markup = build_clean_reply_markup(msg)
    if batch_temp.IS_BATCH.get(message.from_user.id): return 

    async def try_send(send_func, *args, **kwargs):
        primary_chat = dump_chat if dump_chat else message.chat.id
        reply_to_id = message.id if primary_chat == message.chat.id else None
        try:
            return await send_func(primary_chat, *args, reply_to_message_id=reply_to_id, **kwargs)
        except Exception as primary_err:
            primary_err_str = str(primary_err)
            if dump_chat and primary_chat == dump_chat and any(k in primary_err_str for k in ["CHANNEL_INVALID", "ChannelInvalid", "CHAT_WRITE_FORBIDDEN", "USER_BANNED_IN_CHANNEL", "ChatWriteForbidden"]):
                logger.warning("Dump channel %s failed (%s). Falling back to user chat %s...", dump_chat, primary_err, message.chat.id)
                res = await send_func(message.chat.id, *args, reply_to_message_id=message.id, **kwargs)
                try:
                    await client.send_message(message.chat.id, "⚠️ **Notice:** Bot could not post in the configured Dump Channel (Bot lacks Admin permissions). Delivered directly here instead.")
                except Exception:
                    pass
                return res
            raise primary_err

    if "Text" == msg_type:
        try:
            await try_send(client.send_message, msg.text, entities=msg.entities, reply_markup=reply_markup)
            logger.info("Sent text for message ID %s", msgid)
        except Exception as e:
            if reply_markup:
                try:
                    await try_send(client.send_message, msg.text, entities=msg.entities)
                except Exception:
                    pass
            logger.error("Error sending text for message ID %s: %s", msgid, e)
            if ERROR_MESSAGE == True:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        return

    smsg = await client.send_message(message.chat.id, '**Downloading**', reply_to_message_id=message.id)
    asyncio.create_task(downstatus(client, f'{message.id}downstatus.txt', smsg, message.chat.id))
    try:
        logger.info("Downloading %s for message ID %s...", msg_type, msgid)
        file = await acc.download_media(msg, progress=progress, progress_args=[message,"down"])
        if os.path.exists(f'{message.id}downstatus.txt'):
            os.remove(f'{message.id}downstatus.txt')
        logger.info("Finished downloading %s for message ID %s to %s", msg_type, msgid, file)
    except Exception as e:
        logger.error("Download failed for message ID %s: %s", msgid, e)
        if os.path.exists(f'{message.id}downstatus.txt'):
            os.remove(f'{message.id}downstatus.txt')
        if ERROR_MESSAGE == True:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML) 
        return await smsg.delete()
    if batch_temp.IS_BATCH.get(message.from_user.id): 
        if os.path.exists(file): os.remove(file)
        return 
    asyncio.create_task(upstatus(client, f'{message.id}upstatus.txt', smsg, message.chat.id))

    caption = msg.caption if msg.caption else None
    caption_entities = msg.caption_entities if msg.caption_entities else None
    if batch_temp.IS_BATCH.get(message.from_user.id): 
        if os.path.exists(file): os.remove(file)
        return 
            
    if "Document" == msg_type:
        try:
            ph_path = await acc.download_media(msg.document.thumbs[0].file_id)
        except Exception:
            ph_path = None
        
        try:
            try:
                await try_send(client.send_document, file, thumb=ph_path, caption=caption, caption_entities=caption_entities, progress=progress, progress_args=[message,"up"], reply_markup=reply_markup)
            except Exception:
                if reply_markup:
                    await try_send(client.send_document, file, thumb=ph_path, caption=caption, caption_entities=caption_entities, progress=progress, progress_args=[message,"up"])
                else:
                    raise
        except Exception as e:
            if ERROR_MESSAGE == True:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        if ph_path and os.path.exists(ph_path): 
            os.remove(ph_path)

    elif "Video" == msg_type:
        try:
            ph_path = await acc.download_media(msg.video.thumbs[0].file_id)
        except Exception:
            ph_path = None
        
        try:
            try:
                await try_send(client.send_video, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=ph_path, caption=caption, caption_entities=caption_entities, progress=progress, progress_args=[message,"up"], reply_markup=reply_markup)
            except Exception:
                if reply_markup:
                    await try_send(client.send_video, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=ph_path, caption=caption, caption_entities=caption_entities, progress=progress, progress_args=[message,"up"])
                else:
                    raise
        except Exception as e:
            if ERROR_MESSAGE == True:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        if ph_path and os.path.exists(ph_path): 
            os.remove(ph_path)

    elif "Animation" == msg_type:
        try:
            try:
                await try_send(client.send_animation, file, caption=caption, caption_entities=caption_entities, reply_markup=reply_markup)
            except Exception:
                if reply_markup:
                    await try_send(client.send_animation, file, caption=caption, caption_entities=caption_entities)
                else:
                    raise
        except Exception as e:
            if ERROR_MESSAGE == True:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        
    elif "Sticker" == msg_type:
        try:
            await try_send(client.send_sticker, file)
        except Exception as e:
            if ERROR_MESSAGE == True:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)     

    elif "Voice" == msg_type:
        try:
            try:
                await try_send(client.send_voice, file, caption=caption, caption_entities=caption_entities, progress=progress, progress_args=[message,"up"], reply_markup=reply_markup)
            except Exception:
                if reply_markup:
                    await try_send(client.send_voice, file, caption=caption, caption_entities=caption_entities, progress=progress, progress_args=[message,"up"])
                else:
                    raise
        except Exception as e:
            if ERROR_MESSAGE == True:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)

    elif "Audio" == msg_type:
        try:
            ph_path = await acc.download_media(msg.audio.thumbs[0].file_id)
        except Exception:
            ph_path = None

        try:
            try:
                await try_send(client.send_audio, file, thumb=ph_path, caption=caption, caption_entities=caption_entities, progress=progress, progress_args=[message,"up"], reply_markup=reply_markup)
            except Exception:
                if reply_markup:
                    await try_send(client.send_audio, file, thumb=ph_path, caption=caption, caption_entities=caption_entities, progress=progress, progress_args=[message,"up"])
                else:
                    raise
        except Exception as e:
            if ERROR_MESSAGE == True:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        
        if ph_path and os.path.exists(ph_path): 
            os.remove(ph_path)

    elif "Photo" == msg_type:
        try:
            try:
                await try_send(client.send_photo, file, caption=caption, caption_entities=caption_entities, reply_markup=reply_markup)
            except Exception:
                if reply_markup:
                    await try_send(client.send_photo, file, caption=caption, caption_entities=caption_entities)
                else:
                    raise
        except Exception as e:
            if ERROR_MESSAGE == True:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
    
    if os.path.exists(f'{message.id}upstatus.txt'): 
        os.remove(f'{message.id}upstatus.txt')
    if os.path.exists(file): 
        os.remove(file)
    try:
        await client.delete_messages(message.chat.id, [smsg.id])
    except Exception:
        pass
    logger.info("Upload complete and cleanup finished for message ID %s", msgid)


# get the type of message
def get_message_type(msg: pyrogram.types.messages_and_media.message.Message):
    try:
        msg.document.file_id
        return "Document"
    except:
        pass

    try:
        msg.video.file_id
        return "Video"
    except:
        pass

    try:
        msg.animation.file_id
        return "Animation"
    except:
        pass

    try:
        msg.sticker.file_id
        return "Sticker"
    except:
        pass

    try:
        msg.voice.file_id
        return "Voice"
    except:
        pass

    try:
        msg.audio.file_id
        return "Audio"
    except:
        pass

    try:
        msg.photo.file_id
        return "Photo"
    except:
        pass

    try:
        msg.text
        return "Text"
    except:
        pass

import traceback
from pyrogram.types import Message
from pyrogram import Client, filters
from asyncio.exceptions import TimeoutError
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)

SESSION_STRING_SIZE = 351

# Input filters used by the interactive login flow.
# Do not let slash commands such as /start or /help get consumed by bot.ask().
PLAIN_TEXT = filters.text & ~filters.regex(r"^/")
LOGIN_INPUT = PLAIN_TEXT | filters.command(["cancel"])
API_ID_INPUT = PLAIN_TEXT | filters.command(["skip", "cancel"])

async def logout(client, message):
    user_data = await db.get_session(message.from_user.id)
    if user_data is None:
        await message.reply("**You are not logged in.**")
        return
    await db.set_session(message.from_user.id, session=None)
    await db.set_api_id(message.from_user.id, api_id=None)
    await db.set_api_hash(message.from_user.id, api_hash=None)
    await message.reply("**Logout Successfully** ♦")

async def login_command(bot: Client, message: Message):
    user_data = await db.get_session(message.from_user.id)
    if user_data is not None:
        await message.reply("**Your Are Already Logged In. First /logout Your Old Session. Then Do Login.**")
        return 
    user_id = int(message.from_user.id)
    #await message.reply("**How To Create Api Id And Api Hash.**")
    api_id_msg = await bot.ask(user_id, "<b>Send Your API ID.\n\nClick On /skip To Skip This Process\n\nNOTE :- If You Skip This Then Your Account Ban Chance Is High.</b>", filters=API_ID_INPUT)
    if api_id_msg.text == "/cancel":
        return await api_id_msg.reply("<b>Process cancelled.</b>")
    if api_id_msg.text == "/skip":
        api_id = API_ID
        api_hash = API_HASH
    else:
        try:
            api_id = int(api_id_msg.text)
        except ValueError:
            await api_id_msg.reply("**Api id must be an integer, start your process again by /login**", quote=True, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 /login", url="https://t.me/" + (await bot.get_me()).username)]]))
            return
        api_hash_msg = await bot.ask(user_id, "**Now Send Me Your API HASH**", filters=LOGIN_INPUT)
        if api_hash_msg.text == "/cancel":
            return await api_hash_msg.reply("<b>Process cancelled.</b>")
        api_hash = api_hash_msg.text
        
    phone_number_msg = await bot.ask(chat_id=user_id, text="<b>Please send your phone number which includes country code</b>\n<b>Example:</b> <code>+13124562345, +9171828181889</code>", filters=LOGIN_INPUT)
    if phone_number_msg.text=='/cancel':
        return await phone_number_msg.reply('<b>process cancelled !</b>')
    phone_number = phone_number_msg.text
    client = Client("beastx_login", api_id=api_id, api_hash=api_hash, in_memory=True)
    await client.connect()
    await phone_number_msg.reply("Sending OTP...")
    try:
        code = await client.send_code(phone_number)
        phone_code_msg = await bot.ask(user_id, "Please check for an OTP in official telegram account. If you got it, send OTP here after reading the below format. \n\nIf OTP is `12345`, **please send it as** `1 2 3 4 5`.\n\n**Enter /cancel to cancel The Procces**", filters=LOGIN_INPUT, timeout=600)
    except PhoneNumberInvalid:
        await phone_number_msg.reply('`PHONE_NUMBER` **is invalid.**')
        return
    if phone_code_msg.text=='/cancel':
        return await phone_code_msg.reply('<b>process cancelled !</b>')
    try:
        phone_code = phone_code_msg.text.replace(" ", "")
        await client.sign_in(phone_number, code.phone_code_hash, phone_code)
    except PhoneCodeInvalid:
        await phone_code_msg.reply('**OTP is invalid.**')
        return
    except PhoneCodeExpired:
        await phone_code_msg.reply('**OTP is expired.**')
        return
    except SessionPasswordNeeded:
        two_step_msg = await bot.ask(user_id, '**Your account has enabled two-step verification. Please provide the password.\n\nEnter /cancel to cancel The Procces**', filters=LOGIN_INPUT, timeout=300)
        if two_step_msg.text=='/cancel':
            return await two_step_msg.reply('<b>process cancelled !</b>')
        try:
            password = two_step_msg.text
            await client.check_password(password=password)
        except PasswordHashInvalid:
            await two_step_msg.reply('**Invalid Password Provided**')
            return
    string_session = await client.export_session_string()
    await client.disconnect()
    if len(string_session) < SESSION_STRING_SIZE:
        return await message.reply('<b>invalid session sring</b>')
    try:
        user_data = await db.get_session(message.from_user.id)
        if user_data is None:
            uclient = Client("beastx_verify", session_string=string_session, api_id=api_id, api_hash=api_hash, in_memory=True)
            await uclient.connect()
            await db.set_session(message.from_user.id, session=string_session)
            await db.set_api_id(message.from_user.id, api_id=api_id)
            await db.set_api_hash(message.from_user.id, api_hash=api_hash)
            try:
                await uclient.disconnect()
            except:
                pass
    except Exception as e:
        return await message.reply_text(f"<b>ERROR IN LOGIN:</b> `{e}`")
    await bot.send_message(message.from_user.id, "<b>Account Login Successfully.\n\nIf You Get Any Error Related To AUTH KEY Then /logout first and /login again</b>")

from pyrogram.errors import InputUserDeactivated, UserNotParticipant, FloodWait, UserIsBlocked, PeerIdInvalid
from pyrogram import Client, filters
import asyncio
import datetime
import time

async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        return False, "Deleted"
    except UserIsBlocked:
        await db.delete_user(int(user_id))
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        return False, "Error"
    except Exception as e:
        return False, "Error"


@Client.on_message(filters.command("broadcast") & filters.user(ADMINS))
async def broadcast(bot, message):
    users = await db.get_all_users()
    b_msg = message.reply_to_message
    if not b_msg:
        return await message.reply_text("**Reply This Command To Your Broadcast Message**")
    sts = await message.reply_text(
        text='Broadcasting your messages...'
    )
    start_time = time.time()
    total_users = await db.total_users_count()
    done = 0
    blocked = 0
    deleted = 0
    failed =0

    success = 0
    async for user in users:
        if 'id' in user:
            pti, sh = await broadcast_messages(int(user['id']), b_msg)
            if pti:
                success += 1
            elif pti == False:
                if sh == "Blocked":
                    blocked += 1
                elif sh == "Deleted":
                    deleted += 1
                elif sh == "Error":
                    failed += 1
            done += 1
            if not done % 20:
                await sts.edit(f"Broadcast in progress:\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}")    
        else:
            # Handle the case where 'id' key is missing in the user dictionary
            done += 1
            failed += 1
            if not done % 20:
                await sts.edit(f"Broadcast in progress:\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}")    
    
    time_taken = datetime.timedelta(seconds=int(time.time()-start_time))
    await sts.edit(f"Broadcast Completed:\nCompleted in {time_taken} seconds.\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}")

HELP_TXT = """**🌟 Help Menu** 

**__FOR PRIVATE CHATS__**

__first send invite link of the chat (unnecessary if the account of string session already member of the chat)
then send post/s link__


**__FOR BOT CHATS__**

__send link with '/b/', bot's username and message id, you might want to install some unofficial client (like - Plus Messenger) to get the id like below__

```
https://t.me/b/botusername/4321
```

**__MULTI POSTS__**

__send public/private posts link as explained above with formate "from - to" to send multiple messages like below__


```
https://t.me/xxxx/1001-1010

https://t.me/c/xxxx/101 - 120
```

__note that space in between doesn't matter__"""

# =========================
# BeastX Bot
# =========================
class Bot(Client):
    def __init__(self):
        super().__init__(
            "beastx",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=None,
            workers=150,
            sleep_threshold=5,
        )

    async def start(self, *args, **kwargs):
        await super().start(*args, **kwargs)
        logger.info("BeastX Bot Started | @Beastx_Bots | Dev @Godmrunal")

    async def stop(self, *args):
        await super().stop()
        logger.info("BeastX Bot Stopped")


HEALTH_PORT = int(os.environ.get("PORT", 8000))


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, *args):
        pass  # silence noisy access logs


def _start_health_server():
    server = HTTPServer(("0.0.0.0", HEALTH_PORT), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("Health check server listening on port %s", HEALTH_PORT)





if __name__ == "__main__":
    bot = Bot()

    def sigint_handler(sig, frame):
        logger.info("Received signal %s (SIGINT / Ctrl+C). Shutting down cleanly...", sig)
        try:
            if bot.is_connected:
                asyncio.run(bot.stop())
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, sigint_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, sigint_handler)

    _start_health_server()
    # Register every command explicitly on the actual Bot instance.
    # The project was consolidated into one file, so decorators attached to
    # the base Client are not relied upon here.
    bot.add_handler(MessageHandler(
        send_start,
        filters.private & filters.command(["start"])
    ))
    bot.add_handler(MessageHandler(
        send_help,
        filters.private & filters.command(["help"])
    ))
    bot.add_handler(MessageHandler(
        send_cancel,
        filters.private & filters.command(["cancel"])
    ))
    bot.add_handler(MessageHandler(
        logout,
        filters.private & filters.command(["logout"])
    ))
    bot.add_handler(MessageHandler(
        login_command,
        filters.private & filters.command(["login"])
    ))
    bot.add_handler(MessageHandler(
        save,
        filters.private & filters.text & ~filters.command(["start", "help", "cancel", "login", "logout", "broadcast"])
    ))
    bot.add_handler(MessageHandler(
        broadcast,
        filters.command(["broadcast"]) & filters.user(ADMINS)
    ))

    try:
        bot.run()
    except (KeyboardInterrupt, SystemExit):
        logger.info("BeastX Bot stopped cleanly.")
