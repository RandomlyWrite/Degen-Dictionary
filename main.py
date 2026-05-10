import json
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, InlineQueryHandler, ContextTypes
from uuid import uuid4
from keep_alive import keep_alive # This is the missing piece that fixes your error!

# Load the dictionary from the JSON file
def load_dictionary():
    try:
        with open('dictionary.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print("Error: dictionary.json not found! Your portfolio is going to zero.")
        return {}
    except json.JSONDecodeError:
        print("Error: Your JSON is broken. Did you forget a comma before getting liquidated?")
        return {}

degen_dict = load_dictionary()

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get what the user typed and clean it up
    query = update.inline_query.query.upper().strip() 
    results = []

    # Check if the typed word is in our dictionary vault
    if query in degen_dict:
        entry = degen_dict[query]
        pronunciation = entry.get("pronunciation", "No pronunciation provided")
        definition = entry.get("definition", "No definition provided")
        example = entry.get("example", "No example provided")

        # Format the message using Markdown
        message_text = f"**{query}** (_{pronunciation}_)\n\n**Definition:** {definition}\n\n**Example:** _{example}_"

        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"{query}",
                description=definition[:60] + "...", # Short preview for the pop-up list
                input_message_content=InputTextMessageContent(message_text, parse_mode="Markdown")
            )
        )

    await update.inline_query.answer(results)

def main():
    # Start the background web server to keep the bot alive 24/7
    keep_alive()

    # Replace the text below with your actual BotFather token!
    app = Application.builder().token("8402376687:AAEiJ8FHNE_3omsPqU08RW4mCWH2nvHYeVA").build()

    # Add the handler
    app.add_handler(InlineQueryHandler(inline_query))

    print("Degen bot is awake and ready to explain your terrible financial decisions...")
    app.run_polling()

if __name__ == '__main__':
    main()
