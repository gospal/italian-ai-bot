import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import random

# States for conversation handler
PHRASE, QUIZ, ANSWER = range(3)

# Italian phrases dictionary
italian_phrases = {
    "Hello": "Ciao",
    "Goodbye": "Arrivederci",
    "Thank you": "Grazie",
    "Please": "Per favore",
    "How are you?": "Come stai?",
    "I'm good": "Sto bene",
    "What is your name?": "Come ti chiami?",
    "My name is": "Mi chiamo"
}

# Quiz questions
quiz_questions = [
    {"question": "How do you say 'Hello' in Italian?", "answer": "Ciao"},
    {"question": "What does 'Grazie' mean?", "answer": "Thank you"},
    {"question": "How do you say 'Please' in Italian?", "answer": "Per favore"},
]

def start(update, context):
    """Start command handler"""
    user = update.message.from_user.first_name
    welcome_message = (
        f"Ciao {user}! 🇮🇹 Welcome to your Italian conversation learning bot!\n\n"
        "Commands available:\n"
        "/phrases - Learn common Italian phrases\n"
        "/quiz - Test your Italian knowledge\n"
        "/cancel - Stop current activity"
    )
    update.message.reply_text(welcome_message)
    return None

def phrases(update, context):
    """Show Italian phrases"""
    update.message.reply_text("Here are some common Italian phrases to learn:")
    phrase_list = "\n".join([f"{eng} - {ita}" for eng, ita in italian_phrases.items()])
    update.message.reply_text(phrase_list)
    update.message.reply_text("Type any English phrase from the list to hear it in Italian!")
    return PHRASE

def handle_phrase(update, context):
    """Handle user's phrase input"""
    user_input = update.message.text.strip()
    if user_input in italian_phrases:
        update.message.reply_text(f"In Italian, '{user_input}' is: {italian_phrases[user_input]}")
    else:
        update.message.reply_text("Sorry, I don't have that phrase. Try one from the list!")
    return PHRASE

def quiz(update, context):
    """Start a quiz"""
    question = random.choice(quiz_questions)
    context.user_data['current_answer'] = question['answer']
    update.message.reply_text(f"Quiz time! {question['question']}")
    return QUIZ

def handle_quiz_answer(update, context):
    """Check quiz answer"""
    user_answer = update.message.text.strip().lower()
    correct_answer = context.user_data['current_answer'].lower()
    
    if user_answer == correct_answer:
        update.message.reply_text("Correct! Ben fatto! 🎉 Want another? (yes/no)")
        return ANSWER
    else:
        update.message.reply_text(f"Sorry, that's wrong. The correct answer is '{correct_answer}'. Try again? (yes/no)")
        return ANSWER

def quiz_continue(update, context):
    """Handle quiz continuation"""
    response = update.message.text.lower()
    if response == 'yes':
        return quiz(update, context)
    else:
        update.message.reply_text("Thanks for practicing! Use /phrases or /quiz to continue learning.")
        return ConversationHandler.END

def cancel(update, context):
    """Cancel current conversation"""
    update.message.reply_text("Activity cancelled. Use /start to begin again!")
    return ConversationHandler.END

def main():
    """Main function to run the bot"""
    # Replace 'YOUR_TOKEN_HERE' with your actual Telegram Bot Token
    TOKEN = 'YOUR_TOKEN_HERE'
    
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('phrases', phrases),
            CommandHandler('quiz', quiz)
        ],
        states={
            PHRASE: [MessageHandler(Filters.text & ~Filters.command, handle_phrase)],
            QUIZ: [MessageHandler(Filters.text & ~Filters.command, handle_quiz_answer)],
            ANSWER: [MessageHandler(Filters.text & ~Filters.command, quiz_continue)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Add handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(conv_handler)

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN") or "YOUR_TOKEN_HERE"
    print(f"Using Telegram token: {TOKEN}")  # Add this line
    application = Application.builder().token(TOKEN).build()