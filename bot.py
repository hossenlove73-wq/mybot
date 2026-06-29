import logging
import datetime
import os
import sys

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes,
)

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(__file__))

from config import BOT_TOKEN
from locales.strings import t
from utils.user_data import get_lang, set_lang, save_record, get_records, get_last
from utils.calculator import calculate
from utils.pdf_generator import make_pdf

logging.basicConfig(
    format="%(asctime)s — %(levelname)s — %(message)s",
    level=logging.INFO,
)

# Conversation states
SKEL, USAGE, AREA, FLOORS, CONFIRM = range(5)


# ── /start ────────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [[
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        InlineKeyboardButton("🇮🇷 فارسی",   callback_data="lang_fa"),
    ]]
    await update.message.reply_text(
        t("welcome", "en"), parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def cb_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = q.data.replace("lang_", "")
    set_lang(q.from_user.id, lang)
    await q.edit_message_text(t("lang_set", lang), parse_mode="Markdown")
    await q.message.reply_text(t("menu", lang), parse_mode="Markdown")


# ── /help ─────────────────────────────────────────────────────────────────────
async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(t("help", lang), parse_mode="Markdown")


# ── /estimate conversation ────────────────────────────────────────────────────
async def cmd_estimate(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    kb = [
        [InlineKeyboardButton(t("skel_RC",    lang), callback_data="sk_RC")],
        [InlineKeyboardButton(t("skel_STEEL", lang), callback_data="sk_STEEL")],
        [InlineKeyboardButton(t("skel_LBM",   lang), callback_data="sk_LBM")],
    ]
    await update.message.reply_text(
        t("ask_skeleton", lang), parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return SKEL


async def cb_skel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = get_lang(q.from_user.id)
    ctx.user_data["skel"] = q.data.replace("sk_", "")
    kb = [
        [InlineKeyboardButton(t("use_RES", lang), callback_data="us_RESIDENTIAL")],
        [InlineKeyboardButton(t("use_COM", lang), callback_data="us_COMMERCIAL")],
        [InlineKeyboardButton(t("use_OFF", lang), callback_data="us_OFFICE")],
    ]
    await q.edit_message_text(
        t("ask_usage", lang), parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return USAGE


async def cb_usage(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = get_lang(q.from_user.id)
    ctx.user_data["usage"] = q.data.replace("us_", "")
    await q.edit_message_text(t("ask_area", lang), parse_mode="Markdown")
    return AREA


async def msg_area(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    try:
        area = float(update.message.text.strip().replace(",", "."))
        if area <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(t("bad_area", lang), parse_mode="Markdown")
        return AREA
    ctx.user_data["area"] = area
    await update.message.reply_text(t("ask_floors", lang), parse_mode="Markdown")
    return FLOORS


async def msg_floors(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    try:
        floors = int(update.message.text.strip())
        if floors <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(t("bad_floors", lang), parse_mode="Markdown")
        return FLOORS

    skel  = ctx.user_data["skel"]
    usage = ctx.user_data["usage"]
    area  = ctx.user_data["area"]
    res   = calculate(area, floors, skel, usage)
    ctx.user_data["result"] = res

    skel_labels  = {"RC": "بتن مسلح (RC)", "STEEL": "اسکلت فلزی", "LBM": "دیوار باربر"}
    usage_labels = {"RESIDENTIAL": "مسکونی", "COMMERCIAL": "تجاری", "OFFICE": "اداری"}

    msg = (
        f"✅ *نتیجه برآورد پروژه*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏗 اسکلت: {skel_labels.get(skel, skel)}\n"
        f"🏠 کاربری: {usage_labels.get(usage, usage)}\n"
        f"📐 مساحت هر طبقه: {area:,.0f} m²\n"
        f"🔢 تعداد طبقات: {floors}\n"
        f"📏 زیربنای کل: {res['total_area']:,.0f} m²\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🪨 بتن:      `{res['concrete']:,.1f} m³`\n"
        f"🏭 سیمان:    `{res['cement']:,.0f} کیسه`\n"
        f"🔩 میلگرد:   `{res['rebar_ton']:,.2f} تن`\n"
        f"🏖 ماسه:     `{res['sand']:,.1f} m³`\n"
        f"🧱 آجر:      `{res['bricks']:,} عدد`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 هزینه کل: `${res['total_cost']:,.0f} USD`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"_شامل ۵٪ ضریب اتلاف طبق مبحث_"
    )

    kb = [[
        InlineKeyboardButton(t("btn_ok", lang), callback_data="cf_yes"),
        InlineKeyboardButton(t("btn_no", lang), callback_data="cf_no"),
    ]]
    await update.message.reply_text(
        msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return CONFIRM


async def cb_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    await q.answer()
    lang = get_lang(q.from_user.id)

    if q.data == "cf_yes":
        record = {
            "timestamp":  datetime.datetime.now().isoformat(),
            "skeleton":   ctx.user_data["skel"],
            "usage":      ctx.user_data["usage"],
            "floor_area": ctx.user_data["area"],
            "floors":     ctx.user_data.get("result", {}).get("total_area", 0) // max(ctx.user_data["area"], 1),
            "result":     ctx.user_data["result"],
        }
        save_record(q.from_user.id, record)
        await q.edit_message_text(t("confirmed", lang), parse_mode="Markdown")
    else:
        await q.edit_message_text(t("cancelled", lang), parse_mode="Markdown")

    return ConversationHandler.END


async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(t("cancelled", lang), parse_mode="Markdown")
    return ConversationHandler.END


# ── /history ──────────────────────────────────────────────────────────────────
async def cmd_history(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_lang(uid)
    recs = get_records(uid)
    if not recs:
        await update.message.reply_text(t("no_history", lang), parse_mode="Markdown")
        return

    SKEL_FA  = {"RC": "بتن مسلح", "STEEL": "فلزی", "LBM": "بنایی"}
    USAGE_FA = {"RESIDENTIAL": "مسکونی", "COMMERCIAL": "تجاری", "OFFICE": "اداری"}

    lines = [t("history_title", lang)]
    for i, rec in enumerate(reversed(recs[-5:]), 1):
        ts  = rec.get("timestamp", "")[:16].replace("T", " ")
        sk  = SKEL_FA.get(rec.get("skeleton", ""), "")
        us  = USAGE_FA.get(rec.get("usage", ""), "")
        ar  = rec.get("floor_area", 0)
        fl  = rec.get("floors", 0)
        co  = rec.get("result", {}).get("total_cost", 0)
        lines.append(f"*{i}.* {sk} — {us}\n   📅 {ts}\n   📐 {ar:,.0f} m² × {fl} طبقه\n   💰 ${co:,.0f}\n")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── /report ───────────────────────────────────────────────────────────────────
async def cmd_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_lang(uid)
    rec  = get_last(uid)
    if not rec:
        await update.message.reply_text(t("no_history", lang), parse_mode="Markdown")
        return
    await update.message.reply_text(t("gen_pdf", lang), parse_mode="Markdown")
    try:
        path = make_pdf(uid, rec)
        with open(path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=os.path.basename(path),
                caption=t("pdf_ready", lang),
            )
        os.remove(path)
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("estimate", cmd_estimate)],
        states={
            SKEL:    [CallbackQueryHandler(cb_skel,    pattern="^sk_")],
            USAGE:   [CallbackQueryHandler(cb_usage,   pattern="^us_")],
            AREA:    [MessageHandler(filters.TEXT & ~filters.COMMAND, msg_area)],
            FLOORS:  [MessageHandler(filters.TEXT & ~filters.COMMAND, msg_floors)],
            CONFIRM: [CallbackQueryHandler(cb_confirm, pattern="^cf_")],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
    )

    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(CommandHandler("report",  cmd_report))
    app.add_handler(CallbackQueryHandler(cb_lang, pattern="^lang_"))
    app.add_handler(conv)

    print("✅ ربات در حال اجراست...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
