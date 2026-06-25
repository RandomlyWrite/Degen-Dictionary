import json
import os
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, InlineQueryHandler, CommandHandler, ContextTypes
from uuid import uuid4

SUGGESTIONS_FILE = 'suggestions.json'

def load_dictionary():
    try:
        with open('dictionary.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: dictionary.json not found!")
        return {}
    except json.JSONDecodeError:
        print("Error: dictionary.json is broken JSON.")
        return {}

def save_dictionary(d):
    with open('dictionary.json', 'w') as f:
        json.dump(d, f, indent=2)

def load_suggestions():
    try:
        with open(SUGGESTIONS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_suggestions(suggestions):
    with open(SUGGESTIONS_FILE, 'w') as f:
        json.dump(suggestions, f, indent=2)

def is_admin(user_id: int) -> bool:
    admin_id = os.environ.get("ADMIN_ID")
    if not admin_id:
        return False
    return str(user_id) == str(admin_id)

degen_dict = load_dictionary()

def search_terms(query: str) -> list:
    if not query:
        return []
    starts = []
    contains = []
    for term in degen_dict:
        if term.startswith(query):
            starts.append(term)
        elif query in term:
            contains.append(term)
    return starts + contains

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.upper().strip()
    results = []
    matches = search_terms(query)
    for term in matches[:50]:
        entry = degen_dict[term]
        pronunciation = entry.get("pronunciation", "")
        definition = entry.get("definition", "No definition provided")
        example = entry.get("example", "")
        lines = [f"*{term}*"]
        if pronunciation:
            lines.append(f"_{pronunciation}_")
        lines.append("")
        lines.append(definition)
        if example:
            lines.append("")
            lines.append(f"💬 _{example}_")
        message_text = "\n".join(lines)
        preview = definition[:80] + ("..." if len(definition) > 80 else "")
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=term,
                description=preview,
                input_message_content=InputTextMessageContent(
                    message_text,
                    parse_mode="Markdown"
                )
            )
        )
    await update.inline_query.answer(results, cache_time=10)

async def suggest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "📖 *How to suggest a word:*\n\n"
            "`/suggest WORD | definition | example`\n\n"
            "*Example:*\n"
            "/suggest REKT | Slang for wrecked\\. Total financial wipeout\\. | I went all in on that coin and got absolutely rekt\\.",
            parse_mode="MarkdownV2"
        )
        return

    text = " ".join(context.args)
    parts = [p.strip() for p in text.split("|")]

    if len(parts) < 2:
        await update.message.reply_text(
            "Please include at least a word and a definition, separated by `|`\n\n"
            "Example: `/suggest REKT | Total financial wipeout`",
            parse_mode="Markdown"
        )
        return

    word = parts[0].upper().strip()
    definition = parts[1].strip() if len(parts) > 1 else ""
    example = parts[2].strip() if len(parts) > 2 else ""
    suggested_by = update.effective_user.username or str(update.effective_user.id)

    if not word or not definition:
        await update.message.reply_text("Word and definition can't be empty.")
        return

    suggestions = load_suggestions()
    suggestions[word] = {
        "definition": definition,
        "example": example,
        "suggested_by": suggested_by
    }
    save_suggestions(suggestions)

    await update.message.reply_text(
        f"✅ Thanks! *{word}* has been submitted for review.",
        parse_mode="Markdown"
    )

async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Admin only.")
        return

    suggestions = load_suggestions()
    if not suggestions:
        await update.message.reply_text("No pending suggestions.")
        return

    lines = [f"📋 *{len(suggestions)} pending suggestion(s):*\n"]
    for word, entry in suggestions.items():
        lines.append(f"*{word}*")
        lines.append(entry["definition"])
        if entry.get("example"):
            lines.append(f"💬 _{entry['example']}_")
        if entry.get("suggested_by"):
            lines.append(f"👤 @{entry['suggested_by']}")
        lines.append("")

    lines.append("Use `/approve WORD` or `/reject WORD` to manage.")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Admin only.")
        return

    if not context.args:
        await update.message.reply_text("Usage: `/approve WORD`", parse_mode="Markdown")
        return

    word = " ".join(context.args).upper().strip()
    suggestions = load_suggestions()

    if word not in suggestions:
        await update.message.reply_text(
            f"*{word}* not found in suggestions.", parse_mode="Markdown"
        )
        return

    entry = suggestions.pop(word)
    degen_dict[word] = {
        "pronunciation": entry.get("pronunciation", ""),
        "definition": entry["definition"],
        "example": entry.get("example", "")
    }
    save_dictionary(degen_dict)
    save_suggestions(suggestions)

    await update.message.reply_text(
        f"✅ *{word}* approved and added to the dictionary!", parse_mode="Markdown"
    )

async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Admin only.")
        return

    if not context.args:
        await update.message.reply_text("Usage: `/reject WORD`", parse_mode="Markdown")
        return

    word = " ".join(context.args).upper().strip()
    suggestions = load_suggestions()

    if word not in suggestions:
        await update.message.reply_text(
            f"*{word}* not found in suggestions.", parse_mode="Markdown"
        )
        return

    suggestions.pop(word)
    save_suggestions(suggestions)

    await update.message.reply_text(
        f"❌ *{word}* rejected and removed.", parse_mode="Markdown"
    )

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Your Telegram ID is: `{update.effective_user.id}`",
        parse_mode="Markdown"
    )

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise ValueError("No BOT_TOKEN found! Set it as a Replit Secret.")
    app = Application.builder().token(token).build()
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(CommandHandler("suggest", suggest))
    app.add_handler(CommandHandler("review", review))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("reject", reject))
    app.add_handler(CommandHandler("myid", myid))
    print("Degen bot is awake and ready to explain your terrible financial decisions...")
    app.run_polling()

if __name__ == '__main__':
    main()
