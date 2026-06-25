# ╔══════════════════════════════════════════════════════════════╗
# ║           💎  DIAMOND PREMIUM BOT  💎                       ║
# ║           Telegram Bot — Premium Edition (Bug Fixed)        ║
# ╚══════════════════════════════════════════════════════════════╝

import logging
import sqlite3
import random
from datetime import datetime
from io import BytesIO

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters,
)
import qrcode
from PIL import Image, ImageDraw, ImageFont

# ════════════════════════════════════════════════
#  CONFIG
# ════════════════════════════════════════════════
BOT_TOKEN = "8929816627:AAFqOrK7Wwj-g7lW8MyoaG7qgFO5VYjP-os"
ADMIN_ID  = 8445317010
UPI_ID    = "alimturki10@oksbi"

BRAND = {
    "name"    : "Diamond Premium Hub",
    "tagline" : "India's #1 Trusted Diamond Store",
    "logo"    : "💎",
    "divider" : "━━━━━━━━━━━━━━━━━━━━━━",
    "thin"    : "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄",
    "star"    : "✦",
    "check"   : "✅",
    "warning" : "⚠️",
    "fire"    : "🔥",
    "crown"   : "👑",
    "rocket"  : "🚀",
    "card"    : "💳",
    "gift"    : "🎁",
    "lock"    : "🔒",
    "clock"   : "⏱️",
    "shield"  : "🛡️",
}

PLANS = {
    "100":  {
        "price"    : 100,
        "diamonds" : 10_000,
        "label"    : "10,000 Diamonds",
        "emoji"    : "🥉",
        "tag"      : "Starter",
        "note"     : "⚠️ No refund on Starter plan.",
    },
    "500":  {
        "price"    : 500,
        "diamonds" : 50_000,
        "label"    : "50,000 Diamonds",
        "emoji"    : "🥈",
        "tag"      : "Popular",
        "note"     : "✅ 100% refund if not hit.",
    },
    "1000": {
        "price"    : 1000,
        "diamonds" : 1_00_000,
        "label"    : "1,00,000 Diamonds",
        "emoji"    : "🥇",
        "tag"      : "Premium",
        "note"     : "✅ 100% refund if not hit.",
    },
}

# ════════════════════════════════════════════════
#  LOGGING
# ════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("diamond-bot")

# ════════════════════════════════════════════════
#  DATABASE  —  FIX #1: thread-safe connection
# ════════════════════════════════════════════════
DB = sqlite3.connect("bot.db", check_same_thread=False)
DB.row_factory = sqlite3.Row
C  = DB.cursor()

C.execute("""CREATE TABLE IF NOT EXISTS users(
  user_id   INTEGER PRIMARY KEY,
  username  TEXT,
  diamonds  INTEGER DEFAULT 0,
  joined_at TEXT DEFAULT CURRENT_TIMESTAMP
)""")
C.execute("""CREATE TABLE IF NOT EXISTS txns(
  txn_id     TEXT PRIMARY KEY,
  user_id    INTEGER,
  amount     INTEGER,
  diamonds   INTEGER,
  status     TEXT DEFAULT 'pending',
  created_at TEXT
)""")
C.execute("""CREATE TABLE IF NOT EXISTS cards(
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  data       TEXT NOT NULL,
  used       INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  used_at    TEXT,
  txn_id     TEXT,
  user_id    INTEGER
)""")
DB.commit()

# ════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════

def hdr(title: str) -> str:
    # FIX #2: Removed special Unicode box chars from *bold* — they break Markdown parser
    return (
        f"💎 *{BRAND['name']}*\n"
        f"_{BRAND['tagline']}_\n"
        f"{BRAND['divider']}\n"
        f"*{title}*\n"
        f"{BRAND['thin']}"
    )

def footer() -> str:
    return f"\n{BRAND['thin']}\n{BRAND['lock']} _Secure · Verified · Trusted_"

def new_txn_id() -> str:
    ts  = datetime.now().strftime("%y%m%d%H%M%S")
    rnd = random.randint(100, 999)
    return f"DIA{ts}{rnd}"   # FIX #3: removed dashes — regex filter was blocking DIA-xxx-xxx

def mask_card(line: str) -> str:
    digits = "".join(ch for ch in line if ch.isdigit())
    if len(digits) >= 12:
        masked = f"{digits[:4]} **** **** {digits[-4:]}"
        return line.replace(digits, masked, 1)
    return line[:6] + "****" + line[-4:] if len(line) > 14 else line

# ════════════════════════════════════════════════
#  QR — FIX #4: removed styled imports that crash on many servers
# ════════════════════════════════════════════════

def build_premium_qr(upi: str, amount: int, note: str) -> BytesIO:
    url = f"upi://pay?pa={upi}&am={amount}&tn={note}&cu=INR"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=3,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=(20, 20, 40), back_color=(255, 255, 255)).convert("RGB")

    qw, qh  = qr_img.size
    pad     = 30
    label_h = 70
    canvas  = Image.new("RGB", (qw + pad * 2, qh + pad * 2 + label_h), (18, 18, 30))

    # Top accent bar
    bar = Image.new("RGB", (qw + pad * 2, 8), (90, 40, 210))
    canvas.paste(bar, (0, 0))
    canvas.paste(qr_img, (pad, pad + 8))

    draw = ImageDraw.Draw(canvas)
    try:
        font_big   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    except Exception:
        font_big  = ImageFont.load_default()
        font_small = font_big

    cx      = (qw + pad * 2) // 2
    label_y = qh + pad + 16
    draw.text((cx, label_y),      f"💎 Pay Rs.{amount}  |  Diamond Premium", fill=(255, 215, 0),  font=font_big,   anchor="mm")
    draw.text((cx, label_y + 28), upi,                                        fill=(180, 180, 200), font=font_small, anchor="mm")

    buf = BytesIO()
    canvas.save(buf, "PNG")
    buf.seek(0)
    return buf

# ════════════════════════════════════════════════
#  HANDLERS
# ════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    C.execute("INSERT OR IGNORE INTO users(user_id, username) VALUES(?,?)", (u.id, u.username))
    DB.commit()

    name = u.first_name or "User"
    kb = [
        [InlineKeyboardButton(f"🥉 Starter  —  Rs.100  |  10,000 💎",   callback_data="plan_100")],
        [InlineKeyboardButton(f"🥈 Popular  —  Rs.500  |  50,000 💎",   callback_data="plan_500")],
        [InlineKeyboardButton(f"🥇 Premium  —  Rs.1000 | 1,00,000 💎",  callback_data="plan_1000")],
        [
            InlineKeyboardButton("💎 My Balance",  callback_data="my_balance"),
            InlineKeyboardButton("📋 How to Use",  callback_data="how_to_use"),
        ],
    ]
    msg = (
        f"{hdr(f'Welcome, {name}!')}\n\n"
        f"{BRAND['crown']} *Select your Diamond Plan below*\n\n"
        f"{BRAND['star']} Choose a plan, Get QR, Pay, Done!\n"
        f"{BRAND['shield']} Trusted by thousands of users across India.\n"
        f"{footer()}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))


async def plan_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "my_balance":
        C.execute("SELECT diamonds FROM users WHERE user_id=?", (q.from_user.id,))
        row      = C.fetchone()
        diamonds = row[0] if row and row[0] else 0
        return await q.answer(f"💎 Your balance: {diamonds:,} diamonds", show_alert=True)

    if q.data == "how_to_use":
        return await show_howto(q, context)

    if q.data == "back_main":
        return await go_back_main(q, context)

    # Plan selection
    key  = q.data.replace("plan_", "", 1)
    plan = PLANS.get(key)
    if not plan:
        return await q.edit_message_text("Invalid plan selected.")

    t = new_txn_id()
    C.execute(
        "INSERT INTO txns(txn_id,user_id,amount,diamonds,status,created_at) VALUES(?,?,?,?,?,?)",
        (t, q.from_user.id, plan["price"], plan["diamonds"], "pending", datetime.now().isoformat()),
    )
    DB.commit()

    img     = build_premium_qr(UPI_ID, plan["price"], t)
    caption = (
        f"{hdr('Payment QR Code')}\n\n"
        f"{plan['emoji']} *Plan      :* {plan['tag']}\n"
        f"💎 *Diamonds :* {plan['diamonds']:,}\n"
        f"💵 *Amount   :* Rs.{plan['price']}\n"
        f"🏦 *UPI ID   :* `{UPI_ID}`\n"
        f"🔖 *TXN ID   :* `{t}`\n\n"
        f"{BRAND['thin']}\n"
        f"_{plan['note']}_\n\n"
        f"*Steps:*\n"
        f"1) Scan QR or pay to UPI above.\n"
        f"2) Screenshot your payment.\n"
        f"3) Send screenshot here.\n"
        f"4) Admin will verify and approve. {BRAND['rocket']}\n"
        f"{footer()}"
    )
    await context.bot.send_photo(q.from_user.id, photo=img, caption=caption, parse_mode="Markdown")
    await q.edit_message_text(
        f"✅ QR generated for *{plan['tag']}* plan!\nCheck your chat for the payment QR code.",
        parse_mode="Markdown",
    )


async def show_howto(q, context):
    msg = (
        f"{hdr('How To Use')}\n\n"
        f"{BRAND['fire']} *Step-by-step Guide:*\n\n"
        f"*1. YouTube Live Method*\n"
        f"   Open YouTube Live stream.\n"
        f"   Tap Super Chat and view all methods.\n"
        f"   Add card: Number, MM/YY, CVV.\n"
        f"   Save. Name: `Zenix`\n"
        f"   Do NOT change country or address.\n\n"
        f"*2. Payment*\n"
        f"   Choose a plan from main menu.\n"
        f"   Pay via UPI QR generated.\n"
        f"   Screenshot your payment app.\n"
        f"   Send screenshot here. Done! ✅\n"
        f"{footer()}"
    )
    await q.edit_message_text(
        msg,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Back to Plans", callback_data="back_main")]]
        ),
    )


async def go_back_main(q, context):
    name = q.from_user.first_name or "User"
    kb = [
        [InlineKeyboardButton("🥉 Starter  —  Rs.100  |  10,000 💎",   callback_data="plan_100")],
        [InlineKeyboardButton("🥈 Popular  —  Rs.500  |  50,000 💎",   callback_data="plan_500")],
        [InlineKeyboardButton("🥇 Premium  —  Rs.1000 | 1,00,000 💎",  callback_data="plan_1000")],
        [
            InlineKeyboardButton("💎 My Balance", callback_data="my_balance"),
            InlineKeyboardButton("📋 How to Use", callback_data="how_to_use"),
        ],
    ]
    msg = (
        f"{hdr(f'Welcome, {name}!')}\n\n"
        f"{BRAND['crown']} *Select your Diamond Plan below*\n\n"
        f"{BRAND['star']} Choose a plan, Get QR, Pay, Done!\n"
        f"{BRAND['shield']} Trusted by thousands of users across India.\n"
        f"{footer()}"
    )
    await q.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))


async def payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        return
    uid = update.effective_user.id

    # FIX #5: also check 'submitted' so re-sends don't create ghost txns
    C.execute(
        "SELECT txn_id, amount, diamonds FROM txns WHERE user_id=? AND status IN ('pending','submitted') ORDER BY created_at DESC LIMIT 1",
        (uid,),
    )
    row = C.fetchone()
    if not row:
        return await update.message.reply_text(
            f"{BRAND['warning']} *No pending transaction found.*\n"
            f"Use /start and choose a plan first.",
            parse_mode="Markdown",
        )
    t, amount, diamonds = row[0], row[1], row[2]
    C.execute("UPDATE txns SET status='submitted' WHERE txn_id=?", (t,))
    DB.commit()

    admin_text = (
        f"{hdr('New Payment Proof')}\n\n"
        f"User ID : `{uid}`\n"
        f"Amount  : Rs.{amount}\n"
        f"Diamonds: {diamonds:,} 💎\n"
        f"TXN ID  : `{t}`\n\n"
        f"{BRAND['thin']}\n"
        f"To approve: /approve {t}\n"
        f"To reject : /reject {t}"
    )
    try:
        await context.bot.send_photo(
            ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=admin_text,
            parse_mode="Markdown",
        )
    except Exception as e:
        log.error(f"Admin photo send failed: {e}")
        await context.bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")

    await update.message.reply_text(
        f"{BRAND['check']} *Screenshot received!*\n\n"
        f"{BRAND['clock']} Admin is reviewing your payment.\n"
        f"You will be notified once approved.",
        parse_mode="Markdown",
    )

# ════════════════════════════════════════════════
#  ADMIN
# ════════════════════════════════════════════════

def parse_admin_cmd(text: str):
    t     = (text or "").strip()
    lower = t.lower()
    for prefix in ("/approve", "/reject", "/cc_add_bulk", "/cc_add", "/cc_list"):
        if lower.startswith(prefix):
            action = prefix.lstrip("/")
            rest   = t[len(prefix):].strip().lstrip("_").lstrip()
            return action, rest
    return None, None


async def admin_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    action, arg = parse_admin_cmd(update.message.text)
    if not action:
        return
    if action == "approve" and arg:
        await approve_txn(update, context, arg.split()[0])
    elif action == "reject" and arg:
        await reject_txn(update, context, arg.split()[0])
    elif action == "cc_add" and arg:
        await cc_add_one(update, context, arg)
    elif action == "cc_add_bulk":
        await cc_add_bulk(update, context)
    elif action == "cc_list":
        await cc_list(update, context)
    else:
        await update.message.reply_text(
            f"{hdr('Admin Panel')}\n\n"
            f"`/approve TXN` — Approve payment\n"
            f"`/reject  TXN` — Reject payment\n"
            f"`/cc_add  <card>` — Add card\n"
            f"`/cc_add_bulk` — Bulk add cards\n"
            f"`/cc_list` — View pool",
            parse_mode="Markdown",
        )


async def cc_add_one(update, context, line: str):
    C.execute("INSERT INTO cards(data) VALUES(?)", (line.strip(),))
    DB.commit()
    await update.message.reply_text(
        f"{BRAND['check']} Card added:\n`{mask_card(line.strip())}`",
        parse_mode="Markdown",
    )


async def cc_add_bulk(update, context):
    await update.message.reply_text(
        f"{BRAND['card']} *Bulk Add Mode Active*\n"
        f"Send cards one per line.\n"
        f"Send /done when finished.",
        parse_mode="Markdown",
    )
    context.user_data["bulk_mode"]  = True
    context.user_data["bulk_lines"] = []


async def bulk_collector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.user_data.get("bulk_mode"):
        return
    text = update.message.text or ""
    if text.strip().lower() in ("/done", "done"):
        lines = [ln.strip() for ln in context.user_data.get("bulk_lines", []) if ln.strip()]
        for ln in lines:
            C.execute("INSERT INTO cards(data) VALUES(?)", (ln,))
        DB.commit()
        context.user_data["bulk_mode"]  = False
        context.user_data["bulk_lines"] = []
        return await update.message.reply_text(
            f"{BRAND['check']} *{len(lines)} card(s) added* to pool.",
            parse_mode="Markdown",
        )
    else:
        context.user_data.setdefault("bulk_lines", []).extend(text.splitlines())
        await update.message.reply_text(
            f"Added {len(text.splitlines())} line(s). Continue or send /done.",
        )


async def cc_list(update, context):
    C.execute("SELECT COUNT(*) FROM cards WHERE used=0")
    available = C.fetchone()[0]
    C.execute("SELECT data FROM cards WHERE used=0 ORDER BY id LIMIT 5")
    sample = [f"`{mask_card(r[0])}`" for r in C.fetchall()]
    msg = (
        f"{hdr('Card Pool')}\n\n"
        f"Available: {available} cards\n\n"
        + ("\n".join(sample) if sample else "_No cards in pool yet._")
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


def pop_next_card(txn_id: str, user_id: int):
    C.execute("SELECT id, data FROM cards WHERE used=0 ORDER BY id LIMIT 1")
    row = C.fetchone()
    if not row:
        return None
    cid, data = row[0], row[1]
    C.execute(
        "UPDATE cards SET used=1, used_at=datetime('now'), txn_id=?, user_id=? WHERE id=?",
        (txn_id, user_id, cid),
    )
    DB.commit()
    return data


async def approve_txn(update, context, t: str):
    C.execute("SELECT user_id, amount, diamonds, status FROM txns WHERE txn_id=?", (t,))
    row = C.fetchone()
    if not row:
        return await update.message.reply_text(f"TXN `{t}` not found.", parse_mode="Markdown")
    uid, amount, diamonds, status = row[0], row[1], row[2], row[3]
    if status not in ("pending", "submitted"):
        return await update.message.reply_text(f"Already {status}.", parse_mode="Markdown")

    C.execute("UPDATE txns SET status='approved' WHERE txn_id=?", (t,))
    C.execute("UPDATE users SET diamonds = COALESCE(diamonds,0) + ? WHERE user_id=?", (diamonds, uid))
    DB.commit()

    card = pop_next_card(t, uid)

    if card:
        user_msg = (
            f"{hdr('Payment Approved!')}\n\n"
            f"{BRAND['check']} TXN ID  : `{t}`\n"
            f"💎 Diamonds Added: {diamonds:,}\n\n"
            f"{BRAND['gift']} *Your Card:*\n"
            f"`{card}`\n"
            f"{footer()}"
        )
    else:
        user_msg = (
            f"{hdr('Payment Approved!')}\n\n"
            f"{BRAND['check']} TXN ID  : `{t}`\n"
            f"💎 Diamonds Added: {diamonds:,}\n\n"
            f"{BRAND['warning']} No card in pool right now. Admin will send soon.\n"
            f"{footer()}"
        )

    try:
        await context.bot.send_message(uid, user_msg, parse_mode="Markdown")
    except Exception as e:
        log.error(f"Could not message user {uid}: {e}")

    admin_note = f"✅ Approved {t}" + ("" if card else " — WARNING: card pool is empty!")
    await update.message.reply_text(admin_note)


async def reject_txn(update, context, t: str):
    C.execute("SELECT user_id FROM txns WHERE txn_id=?", (t,))
    row = C.fetchone()
    if not row:
        return await update.message.reply_text(f"TXN `{t}` not found.", parse_mode="Markdown")
    uid = row[0]
    C.execute("UPDATE txns SET status='rejected' WHERE txn_id=?", (t,))
    DB.commit()
    try:
        await context.bot.send_message(
            uid,
            f"{hdr('Payment Rejected')}\n\n"
            f"TXN `{t}` has been rejected.\n"
            f"If this is an error, contact admin.\n"
            f"{footer()}",
            parse_mode="Markdown",
        )
    except Exception as e:
        log.error(f"Could not message user {uid}: {e}")
    await update.message.reply_text(f"Rejected {t}")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    C.execute("SELECT diamonds FROM users WHERE user_id=?", (uid,))
    row      = C.fetchone()
    diamonds = row[0] if row and row[0] else 0
    await update.message.reply_text(
        f"{hdr('Your Balance')}\n\n"
        f"User ID : `{uid}`\n"
        f"💎 Diamonds: *{diamonds:,}*\n"
        f"{footer()}",
        parse_mode="Markdown",
    )

# ════════════════════════════════════════════════
#  MAIN  —  FIX #6: handler order fixed
# ════════════════════════════════════════════════

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("balance", balance))

    # All inline button callbacks go through one handler
    app.add_handler(CallbackQueryHandler(plan_click))

    # Admin text commands (approve/reject/cc_*)
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"^/(approve|reject|cc_add|cc_add_bulk|cc_list)"),
        admin_router,
    ))

    # Bulk card collector (must be AFTER admin_router)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bulk_collector))

    # Payment screenshots
    app.add_handler(MessageHandler(filters.PHOTO, payment_proof))

    log.info("💎 Diamond Premium Bot — ONLINE")
    log.info(f"   Admin : {ADMIN_ID}")
    log.info(f"   UPI   : {UPI_ID}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
