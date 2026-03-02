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
2️⃣ ᴡᴀɪᴛ ғᴏʀ ᴘʀᴏᴄᴇssɪɴɢ ⏳
3️⃣ ɢᴇᴛ ʏᴏᴜʀ ᴅɪʀᴇᴄᴛ ᴅᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋ 🔗

📌 ғᴇᴀᴛᴜʀᴇs:
➤ ɪɴsᴛᴀɴᴛ ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛɪᴏɴ ⚡
➤ sᴜᴘᴘᴏʀᴛs ᴀʟʟ ғɪʟᴇ ᴛʏᴘᴇs 📁
➤ ғᴀsᴛ & sᴇᴄᴜʀᴇ 🔒
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
├⍟ Bᴜɪʟᴅ Sᴛᴀᴛᴜs : ᴠ1.0 [ ꜱᴛᴀʙʟᴇ ]
╰───────────────⍟</b>"""

    LINK_TXT = """<b>𝗬𝗼𝘂𝗿 𝗟𝗶𝗻𝗸 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 !</b>

📂 <b>Fɪʟᴇ ɴᴀᴍᴇ</b> : <code>{file_name}</code>

📦 <b>Fɪʟᴇ ꜱɪᴢᴇ</b> : <code>{file_size}</code>

📥 <b>Dᴏᴡɴʟᴏᴀᴅ</b> : {download_url}

🖥 <b>Wᴀᴛᴄʜ</b> : {watch_url}

🔗 <b>Sʜᴀʀᴇ</b> : {share_url}


⚠️ <b>ʟɪɴᴋ ᴡɪʟʟ ᴇxᴘɪʀᴇ ᴡɪᴛʜɪɴ 𝟤𝟦ʜʀꜱ, ᴜꜱᴇ ᴘʀᴇᴍɪᴜᴍ ᴄʀᴇᴅɪᴛꜱ ᴛᴏ ɢᴇᴛ ᴘᴇʀᴍᴀɴᴇɴᴛ ʟɪɴᴋꜱ!! 😊</b>"""

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
📁 <b>Tᴏᴛᴀʟ Fɪʟᴇs:</b> <code>{files}</code>"""

    BROADCAST_TXT = """<b>📢 Bʀᴏᴀᴅᴄᴀsᴛ Fɪɴɪsʜᴇᴅ!</b>

✅ Sᴜᴄᴄᴇss: <code>{success}</code>
❌ Fᴀɪʟᴇᴅ: <code>{failed}</code>
👥 Tᴏᴛᴀʟ: <code>{total}</code>"""
