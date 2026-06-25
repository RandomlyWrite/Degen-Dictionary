import json
import os
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, InlineQueryHandler, ContextTypes
from uuid import uuid4

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

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise ValueError("No BOT_TOKEN found! Set it as a Replit Secret.")
    app = Application.builder().token(token).build()
    app.add_handler(InlineQueryHandler(inline_query))
    print("Degen bot is awake and ready to explain your terrible financial decisions...")
    app.run_polling()

if __name__ == '__main__':
    main()
