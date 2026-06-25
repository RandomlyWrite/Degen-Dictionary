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

def load_suggestions():
    try:
        with open(SUGGESTIONS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_suggestions(suggestions):
    with open(SUGGESTIONS_FILE, 'w') as f:
        json.dump(suggestions, f, indent=2)

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
            "`/suggest WORD | your definition | example sentence`\n\n"
            "*Example:*\n"
            "`/suggest REKT | Total financial wipeout | I went all in and got absolutely rekt`",
            parse_mode="Markdown"
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

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise ValueError("No BOT_TOKEN found! Set it as a Replit Secret.")
    app = Application.builder().token(token).build()
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(CommandHandler("suggest", suggest))
    print("Degen bot is awake and ready to explain your terrible financial decisions...")
    app.run_polling()

if __name__ == '__main__':
    main()
