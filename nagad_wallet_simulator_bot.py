"""
Wallet Simulator Telegram Bot
For learning/testing only. No real Nagad transactions are performed.
Every generated receipt is visibly marked SIMULATED / FAKE.
"""

import os
import io
import random
import string
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# 1) Put your Telegram bot token in the BOT_TOKEN environment variable.
# Never share your token publicly.
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

MENU = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📤 Send Money"), KeyboardButton("💵 Cash-Out")],
        [KeyboardButton("📊 Balance"), KeyboardButton("ℹ️ Help")],
    ],
    resize_keyboard=True,
)

# In-memory demo data. It resets when the bot restarts.
# Each Telegram user gets a separate simulated balance.
balances = {}
user_steps = {}
user_forms = {}


def get_balance(user_id: int) -> float:
    if user_id not in balances:
        balances[user_id] = 10000.00
    return balances[user_id]


def make_txn_id() -> str:
    return "SIM" + "".join(random.choices(string.digits, k=10))


def load_font(size: int, bold: bool = False):
    candidates = (
        ["/system/fonts/Roboto-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        if bold
        else ["/system/fonts/Roboto-Regular.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def create_receipt(kind: str, name: str, phone: str, amount: float, fee: float = 0.0) -> io.BytesIO:
    """Create a clearly watermarked illustrative receipt, not proof of payment."""
    width, height = 900, 1120
    img = Image.new("RGB", (width, height), "#fff7f0")
    draw = ImageDraw.Draw(img)

    orange = "#f36b21"
    dark = "#292929"
    muted = "#666666"

    # Header
    draw.rounded_rectangle((35, 35, width - 35, 230), radius=30, fill=orange)
    draw.text((75, 65), "WALLET SIMULATOR", font=load_font(42, True), fill="white")
    draw.text((75, 125), "ILLUSTRATIVE RECEIPT - NOT A PAYMENT", font=load_font(23, True), fill="white")
    draw.text((75, 175), "SIMULATED / FAKE", font=load_font(30, True), fill="white")

    # Main amount
    draw.text((65, 275), kind.upper(), font=load_font(30, True), fill=orange)
    draw.text((65, 330), f"BDT {amount:,.2f}", font=load_font(58, True), fill=dark)
    if fee:
        draw.text((65, 410), f"Illustrative fee: BDT {fee:,.2f}", font=load_font(25), fill=muted)

    txn = make_txn_id()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = [
        ("Status", "SIMULATED - NO MONEY MOVED"),
        ("Recipient / Agent", name[:36]),
        ("Number", phone[:25]),
        ("Demo Transaction ID", txn),
        ("Date & Time", now),
    ]
    y = 490
    for label, value in rows:
        draw.line((65, y, width - 65, y), fill="#e4d5cb", width=2)
        draw.text((70, y + 18), label, font=load_font(22), fill=muted)
        draw.text((70, y + 52), value, font=load_font(24, True), fill=dark)
        y += 105

    # Strong diagonal watermark
    watermark = Image.new("RGBA", img.size, (0, 0, 0, 0))
    wd = ImageDraw.Draw(watermark)
    wf = load_font(92, True)
    wd.text((105, 650), "SIMULATED / FAKE", font=wf, fill=(190, 40, 20, 70))
    watermark = watermark.rotate(28, resample=Image.Resampling.BICUBIC, center=(width // 2, height // 2))
    img = Image.alpha_composite(img.convert("RGBA"), watermark).convert("RGB")

    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((35, height - 125, width - 35, height - 35), radius=20, fill="#ffe0cc")
    draw.text((60, height - 105), "For testing/entertainment only.", font=load_font(25, True), fill=dark)
    draw.text((60, height - 68), "This is NOT an official Nagad receipt.", font=load_font(23), fill=dark)

    out = io.BytesIO()
    img.save(out, format="PNG")
    out.seek(0)
    out.name = "simulated_receipt.png"
    return out


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_balance(user_id)
    await update.message.reply_text(
        "🟠 Wallet Simulator Bot\n\n"
        "This is a SIMULATED demo. It cannot send/withdraw real money, "
        "check a real wallet balance, or verify real payments.\n\n"
        "Choose an option below. All receipts are marked SIMULATED / FAKE.",
        reply_markup=MENU,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "How to use:\n"
        "• Send Money: create a simulated send-money receipt\n"
        "• Cash-Out: create a simulated cash-out receipt\n"
        "• Balance: view this bot's demo balance\n\n"
        "No real payment occurs. Demo balance resets when the bot restarts.",
        reply_markup=MENU,
    )


async def begin_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: str):
    user_id = update.effective_user.id
    user_steps[user_id] = "amount"
    user_forms[user_id] = {"flow": flow}
    await update.message.reply_text(
        f"{flow} demo selected.\nEnter an amount in BDT (numbers only)."
    )


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text == "📤 Send Money":
        await begin_flow(update, context, "SEND MONEY")
        return
    if text == "💵 Cash-Out":
        await begin_flow(update, context, "CASH-OUT")
        return
    if text == "📊 Balance":
        balance = get_balance(user_id)
        await update.message.reply_text(
            f"📊 SIMULATED BALANCE\nBDT {balance:,.2f}\n\n"
            "This is only an internal demo value, not your real wallet balance.",
            reply_markup=MENU,
        )
        return
    if text == "ℹ️ Help":
        await help_command(update, context)
        return

    step = user_steps.get(user_id)
    form = user_forms.get(user_id, {})

    if not step:
        await update.message.reply_text("Choose an option from the menu, or send /start.", reply_markup=MENU)
        return

    if step == "amount":
        try:
            amount = float(text.replace(",", ""))
            if not (0.01 <= amount <= 100000000):
                raise ValueError
        except ValueError:
            await update.message.reply_text("Enter a valid amount greater than 0, e.g. 500")
            return
        form["amount"] = amount
        user_steps[user_id] = "name"
        await update.message.reply_text("Enter recipient / agent name (for the demo receipt):")
        return

    if step == "name":
        if len(text) < 1 or len(text) > 60:
            await update.message.reply_text("Enter a name between 1 and 60 characters.")
            return
        form["name"] = text
        user_steps[user_id] = "phone"
        await update.message.reply_text("Enter a phone number for the demo (you may use a fake number):")
        return

    if step == "phone":
        if len(text) < 3 or len(text) > 30:
            await update.message.reply_text("Enter a valid-looking demo number.")
            return
        form["phone"] = text
        flow = form["flow"]
        amount = form["amount"]
        fee = round(amount * 0.018, 2) if flow == "CASH-OUT" else 0.0
        receipt = create_receipt(flow, form["name"], form["phone"], amount, fee)
        caption = (
            "⚠️ SIMULATED / FAKE RECEIPT\n"
            "No real money was sent or withdrawn. Not valid as payment proof."
        )
        await update.message.reply_photo(photo=receipt, caption=caption, reply_markup=MENU)
        user_steps.pop(user_id, None)
        user_forms.pop(user_id, None)
        return


def main():
    if not BOT_TOKEN:
        raise SystemExit(
            "BOT_TOKEN is missing. Set it as an environment variable before running the bot."
        )

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    print("Wallet Simulator Bot is running. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
