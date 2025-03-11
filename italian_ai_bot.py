import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import random
import openai
import os
import json
from datetime import datetime
import assemblyai as aai
from gtts import gTTS
import io

# API setup
openai.api_key = os.getenv("OPENAI_API_KEY") or "YOUR_OPENAI_API_KEY"
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY") or "YOUR_ASSEMBLYAI_API_KEY"

# States for conversation handler
PHRASE, QUIZ, ANSWER, CHAT, FEEDBACK = range(5)

# Italian phrases with difficulty levels
italian_phrases = {
    "basic": {"Hello": "Ciao", "Goodbye": "Arrivederci", "Thank you": "Grazie", "Please": "Per favore"},
    "intermediate": {"How are you?": "Come stai?", "I'm good": "Sto bene"},
    "advanced": {"What is your name?": "Come ti chiami?", "My name is": "Mi chiamo"}
}

# Quiz questions with difficulty
quiz_questions = {
    "basic": [{"question": "How do you say 'Hello' in Italian?", "answer": "Ciao"}],
    "intermediate": [{"question": "What does 'Grazie' mean?", "answer": "Thank you"}],
    "advanced": [{"question": "Translate 'I’m going to the store' to Italian", "answer": "Vado al negozio"}]
}

# User data storage
user_progress = {}

def start(update, context):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id not in user_progress:
        user_progress[user_id] = {"level": "basic", "score": 0, "last_interaction": str(datetime.now())}

    welcome_message = (
        f"Ciao {user}! 🇮🇹 Welcome to your advanced Italian learning bot!\n"
        f"Your current level: {user_progress[user_id]['level']}\n\n"
        "Commands:\n"
        "/phrases - Learn phrases by level\n"
        "/quiz - Adaptive quizzes\n"
        "/chat - AI conversation (text or voice)\n"
        "/progress - Check your stats\n"
        "/cancel - Stop activity"
    )
    update.message.reply_text(welcome_message)
    return None

def phrases(update, context):
    user_id = update.message.from_user.id
    level = user_progress.get(user_id, {"level": "basic"})["level"]
    update.message.reply_text(f"Here are {level} Italian phrases:")
    phrase_list = "\n".join([f"{eng} - {ita}" for eng, ita in italian_phrases[level].items()])
    update.message.reply_text(phrase_list)
    update.message.reply_text("Type or say an English phrase from the list!")
    return PHRASE

def handle_phrase(update, context):
    user_id = update.message.from_user.id
    level = user_progress[user_id]["level"]
    user_input = update.message.text.strip() if update.message.text else transcribe_voice(update.message.voice)

    if user_input in italian_phrases[level]:
        response = f"In Italian: {italian_phrases[level][user_input]}"
        send_voice_response(update, context, response)
    else:
        update.message.reply_text("Not found in your level’s list. Try again!")
    return PHRASE

def quiz(update, context):
    user_id = update.message.from_user.id
    level = user_progress[user_id]["level"]
    question = random.choice(quiz_questions[level])
    context.user_data['current_answer'] = question['answer']
    context.user_data['current_question'] = question['question']
    update.message.reply_text(f"Quiz ({level}): {question['question']} (Reply with text or voice)")
    return QUIZ

def handle_quiz_answer(update, context):
    user_id = update.message.from_user.id
    user_answer = update.message.text.strip().lower() if update.message.text else transcribe_voice(update.message.voice).lower()
    correct_answer = context.user_data['current_answer'].lower()

    if user_answer == correct_answer:
        user_progress[user_id]["score"] += 10
        update_level(user_id)
        response = f"Correct! Score: {user_progress[user_id]['score']}. Another? (yes/no)"
        send_voice_response(update, context, response)
    else:
        response = f"Wrong. It’s '{correct_answer}'. Try again? (yes/no)"
        send_voice_response(update, context, response)
    return ANSWER

def update_level(user_id):
    score = user_progress[user_id]["score"]
    if score >= 50 and user_progress[user_id]["level"] == "basic":
        user_progress[user_id]["level"] = "intermediate"
    elif score >= 100 and user_progress[user_id]["level"] == "intermediate":
        user_progress[user_id]["level"] = "advanced"

def quiz_continue(update, context):
    response = update.message.text.lower() if update.message.text else transcribe_voice(update.message.voice).lower()
    if response == 'yes':
        return quiz(update, context)
    update.message.reply_text("Quiz ended. Try /chat or /phrases!")
    return ConversationHandler.END

def chat(update, context):
    user_id = update.message.from_user.id
    level = user_progress[user_id]["level"]
    update.message.reply_text(
        f"Practice Italian at your {level} level! Use text or voice, "
        "and I’ll respond in Italian with feedback. Say 'stop' to end."
    )
    return CHAT

def handle_chat(update, context):
    user_id = update.message.from_user.id
    user_input = update.message.text.strip().lower() if update.message.text else transcribe_voice(update.message.voice).lower()

    if user_input == "stop":
        update.message.reply_text("Chat ended. Check /progress or start again!")
        return ConversationHandler.END

    level = user_progress[user_id]["level"]
    prompt = (
        f"You are an Italian tutor. The user is at {level} level. "
        f"Respond in Italian to their input, matching their level. "
        f"If they use English, translate to Italian first, then respond. "
        f"Provide brief feedback on grammar or pronunciation if applicable. Input: '{user_input}'"
    )

    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150,
            temperature=0.8
        )
        ai_response = response.choices[0].text.strip()
        send_voice_response(update, context, ai_response)
        user_progress[user_id]["last_interaction"] = str(datetime.now())
    except Exception as e:
        update.message.reply_text(f"Errore: {str(e)}. Riprova!")

    return CHAT

def progress(update, context):
    user_id = update.message.from_user.id
    stats = user_progress.get(user_id, {"level": "basic", "score": 0, "last_interaction": "N/A"})
    update.message.reply_text(
        f"Your Progress:\nLevel: {stats['level']}\nScore: {stats['score']}\nLast Interaction: {stats['last_interaction']}"
    )
    return None

def transcribe_voice(voice):
    """Convert voice message to text using AssemblyAI"""
    config = aai.TranscriptionConfig(language_code="en-US")  # Use "it-IT" for Italian if spoken
    transcriber = aai.Transcriber()
    audio_file = voice.get_file().download_as_bytearray()
    with open("temp_audio.ogg", "wb") as f:
        f.write(audio_file)
    transcript = transcriber.transcribe("temp_audio.ogg", config=config)
    return transcript.text if transcript.text else "Sorry, I couldn’t understand."

def send_voice_response(update, context, text):
    """Send a voice message using gTTS"""
    tts = gTTS(text=text, lang="it")
    audio_file = io.BytesIO()
    tts.write_to_fp(audio_file)
    audio_file.seek(0)
    context.bot.send_voice(chat_id=update.effective_chat.id, voice=audio_file)

def cancel(update, context):
    update.message.reply_text("Activity cancelled. Back to /start!")
    return ConversationHandler.END

def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN") or "YOUR_TOKEN_HERE"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('phrases', phrases),
            CommandHandler('quiz', quiz),
            CommandHandler('chat', chat)
        ],
        states={
            PHRASE: [MessageHandler(Filters.text & ~Filters.command, handle_phrase),
                     MessageHandler(Filters.voice, handle_phrase)],
            QUIZ: [MessageHandler(Filters.text & ~Filters.command, handle_quiz_answer),
                   MessageHandler(Filters.voice, handle_quiz_answer)],
            ANSWER: [MessageHandler(Filters.text & ~Filters.command, quiz_continue),
                     MessageHandler(Filters.voice, quiz_continue)],
            CHAT: [MessageHandler(Filters.text & ~Filters.command, handle_chat),
                   MessageHandler(Filters.voice, handle_chat)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("progress", progress))
    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()