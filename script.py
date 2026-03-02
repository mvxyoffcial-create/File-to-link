class Script:

    START_TXT = """<b>ʜᴇʏ, {}! {}</b>
<b>ɪ'ᴍ ᴀ ᴘᴏᴡᴇʀғᴜʟ ғɪʟᴇ ʟɪɴᴋ ʙᴏᴛ 🔗</b>
<b>ɪ ᴄᴀɴ ᴄᴏɴᴠᴇʀᴛ ғɪʟᴇs ɪɴᴛᴏ sʜᴀʀᴀʙʟᴇ ᴅɪʀᴇᴄᴛ ʟɪɴᴋs 📂</b>
<b>ᴊᴜsᴛ sᴇɴᴅ ᴍᴇ ᴀ ғɪʟᴇ — ᴀɴᴅ ɢᴇᴛ ɪᴛs ᴅɪʀᴇᴄᴛ ᴅᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋ 🚀</b>"""

    GSTART_TXT = """<b>ʜᴇʏ, {}! {}</b>
<b>ɪ'ᴍ ᴀ ғᴀsᴛ & sᴍᴀʀᴛ ғɪʟᴇ ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴏʀ ʙᴏᴛ 🤖</b>
<b>ᴄᴏɴᴠᴇʀᴛ ғɪʟᴇs ᴛᴏ ᴅɪʀᴇᴄᴛ ʟɪɴᴋs ɪɴ sᴇᴄᴏɴᴅs ⚡</b>
<b>ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴏʀ sᴇɴᴅ ᴀ ғɪʟᴇ ᴛᴏ sᴛᴀʀᴛ 📤</b>"""

    HELP_TXT = """<b>✨ ʜᴏᴡ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ғɪʟᴇ ʟɪɴᴋ ✨
1️⃣ sᴇɴᴅ ᴀɴʏ ғɪʟᴇ 📂
2️⃣ ᴄʜᴏᴏꜱᴇ 🔒 Pᴇʀᴍᴀɴᴇɴᴛ ᴏʀ ⏰ 24ʜʀ ʟɪɴᴋ
3️⃣ ɢᴇᴛ ʏᴏᴜʀ ᴅɪʀᴇᴄᴛ ᴅᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋ 🔗

📌 ғᴇᴀᴛᴜʀᴇs:
➤ ɪɴsᴛᴀɴᴛ ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛɪᴏɴ ⚡
➤ sᴜᴘᴘᴏʀᴛs ᴀʟʟ ғɪʟᴇ ᴛʏᴘᴇs 📁
➤ ᴘᴇʀᴍᴀɴᴇɴᴛ & 24ʜʀ ʟɪɴᴋs 🔒
➤ ᴅɪʀᴇᴄᴛ sʜᴀʀɪɴɢ 🚀

🚀 sᴛᴀʀᴛ ɴᴏᴡ!</b>"""

    ABOUT_TXT = """<b>╭────[ ᴍʏ ᴅᴇᴛᴀɪʟs ]────⍟
├⍟ Mʏ Nᴀᴍᴇ : <a href=https://t.me/{0}>{1}</a>
├⍟ Dᴇᴠᴇʟᴏᴘᴇʀ : <a href=https://t.me/Venuboyy>@Venuboyy</a>
├⍟ Lɪʙʀᴀʀʏ : <a href='https://docs.pyrogram.org/'>ᴘʏʀᴏɢʀᴀᴍ</a>
├⍟ Lᴀɴɢᴜᴀɢᴇ : <a href='https://www.python.org/'>ᴘʏᴛʜᴏɴ 𝟹</a>
├⍟ Dᴀᴛᴀʙᴀsᴇ : <a href='https://www.mongodb.com/'>ᴍᴏɴɢᴏ ᴅʙ</a>
├⍟ Bᴏᴛ Sᴇʀᴠᴇʀ : <a href='https://heroku.com/'>ʜᴇʀᴏᴋᴜ</a>
├⍟ Fᴇᴀᴛᴜʀᴇ : ғɪʟᴇ ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴏʀ 🔗
├⍟ Bᴜɪʟᴅ Sᴛᴀᴛᴜs : ᴠ2.0 [ ꜱᴛᴀʙʟᴇ ]
╰───────────────⍟</b>"""

    # {badge} = 🔒 Pᴇʀᴍᴀɴᴇɴᴛ  OR  ⏰ 24ʜʀ
    LINK_TXT = """<b>𝗬𝗼𝘂𝗿 𝗟𝗶𝗻𝗸 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 ! {badge}</b>

📂 <b>Fɪʟᴇ ɴᴀᴍᴇ</b> : <code>{file_name}</code>

📦 <b>Fɪʟᴇ ꜱɪᴢᴇ</b> : <code>{file_size}</code>

📥 <b>Dᴏᴡɴʟᴏᴀᴅ</b> :
<code>{download_url}</code>

🖥 <b>Wᴀᴛᴄʜ</b> :
<code>{watch_url}</code>

🔗 <b>Sʜᴀʀᴇ</b> :
<code>{share_url}</code>

{expiry_note}"""

    FORCE_SUB_TXT = """<b>⚠️ ʏᴏᴜ ɴᴇᴇᴅ ᴛᴏ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ!</b>

<b>ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴀʟʟ ᴄʜᴀɴɴᴇʟꜱ ʙᴇʟᴏᴡ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴛʀʏ ᴀɢᴀɪɴ 👇</b>"""

    INFO_TXT = """<b>➲First Name:</b> {first_name}
<b>➲Last Name:</b> {last_name}
<b>➲Telegram ID:</b> <code>{user_id}</code>
<b>➲Data Centre:</b> {dc_id}
<b>➲User Name:</b> {username}
<b>➲User 𝖫𝗂𝗇𝗄:</b> <a href="tg://user?id={user_id}">Click Here</a>"""

    STATS_TXT = """<b>📊 Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs</b>

👥 <b>Tᴏᴛᴀʟ Usᴇʀs:</b> <code>{users}</code>
📁 <b>Tᴏᴛᴀʟ Fɪʟᴇs:</b> <code>{files}</code>
🔒 <b>Pᴇʀᴍᴀɴᴇɴᴛ:</b> <code>{permanent}</code>
⏰ <b>Tᴇᴍᴘ (24ʜ):</b> <code>{temp}</code>"""

    BROADCAST_TXT = """<b>📢 Bʀᴏᴀᴅᴄᴀsᴛ Fɪɴɪsʜᴇᴅ!</b>

✅ Sᴜᴄᴄᴇss: <code>{success}</code>
❌ Fᴀɪʟᴇᴅ: <code>{failed}</code>
👥 Tᴏᴛᴀʟ: <code>{total}</code>"""

    CHOOSE_LINK_TYPE = """<b>📂 Fɪʟᴇ ʀᴇᴄᴇɪᴠᴇᴅ!</b>

<b>ᴄʜᴏᴏꜱᴇ ʟɪɴᴋ ᴛʏᴘᴇ:</b>

🔒 <b>Pᴇʀᴍᴀɴᴇɴᴛ</b> — ʟɪɴᴋ ɴᴇᴠᴇʀ ᴇxᴘɪʀᴇs
⏰ <b>24ʜʀ</b> — ʟɪɴᴋ ᴇxᴘɪʀᴇs ᴀғᴛᴇʀ 24 ʜᴏᴜʀs"""
