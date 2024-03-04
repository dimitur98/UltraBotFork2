from telethon import events
from telethon.sync import *
from telethon.errors.rpcerrorlist import PasswordHashInvalidError, PhoneCodeInvalidError, SessionPasswordNeededError, FloodWaitError 
import asyncio
from telethon.tl.types import InputPeerChannel
from datetime import datetime
from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes,CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import re

TOKEN: Final = '6789275807:AAFG9Y3WA-xCdH7p5V7Lf3LpQjhOKuhJIME'
BOT_USERNAME: Final = 'UltraSummarizerBot'

client = None
phone = '+359877543669'
api_id = 7181035
api_hash = '03413b514dcbd241205bcfdcf8dbf92f'
phone_hash = None
mcap_from = None
mcap_to = None
total_calls_from = None
total_calls_to = None
last_button_pressed = None
buttons_set = None
handle_new_message = None
show_duplicates = False
addresses = list()

async def client_passcode_sign_in(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global client

    try:
        password = update.message.text

        await client.sign_in(password = str(password))

        await update.message.reply_text('Login successful. You can start bot now!')
    except PasswordHashInvalidError:
        await update.message.reply_text('Invalid passcode.')
    except Exception as err:
        print(err)

async def client_sign_in(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global client
    global phone
    global phone_hash
    global last_button_pressed
    
    try:
        code = update.message.text

        await client.sign_in(phone, str(code), phone_code_hash = phone_hash.phone_code_hash)

        last_button_pressed = None

        await update.message.reply_text('Login successful. You can start bot now!')
    except SessionPasswordNeededError:
        last_button_pressed = 'passcode'

        await update.message.reply_text('Please enter telegram passcode:')

    except PhoneCodeInvalidError:
        await update.message.reply_text('Invalid code.')
    except Exception as err:
        print(err)


async def client_initializer(update):
    global client
    global phone
    global api_id
    global api_hash
    global phone_hash
    global last_button_pressed

    client = None

    if (phone is None or api_id is None or api_hash is None):
        await update.message.reply_text('Please set your telegram data:', reply_markup = InlineKeyboardMarkup(get_telegram_api_keyboard()))
        return

    try:
        client = TelegramClient(phone, api_id, api_hash)
        await client.connect()
        print(phone)

        if not await client.is_user_authorized():
            last_button_pressed = 'sent_code'

            phone_hash = await client.send_code_request(phone)

            await update.message.reply_text('Please enter telegram code:')
            # code = input()

            # await client.sign_in(phone,code, phone_code_hash= phone_hash.phone_code_hash)
        
    except FloodWaitError  as errr:
        print(errr)
    except Exception as error:
        print(error)

async def sniper(update: Update):
    global client
    global handle_new_message
    
    if client is None:
        await client_initializer(update)
    # result = await client(GetDialogsRequest(
    #         offset_date=None,
    #         offset_id=0,
    #         offset_peer=InputPeerEmpty(),
    #         limit=200,
    #         hash = 0
    # ))
   

    # chat = next(x for x in result.chats if x.title == "SIM BOT ULTRA")
    entity = await client.get_entity('https://t.me/+8d_erKU1nm5iYjM8')
    group_entity = InputPeerChannel(entity.id, entity.access_hash)

    @client.on(events.NewMessage(chats=group_entity))
    async def handle_new_message(event):
        global mcap_from
        global mcap_to
        global total_calls_from
        global total_calls_to
        global addresses

        date = event.message.date
        #name = re.search("\*\*(?P<name>[\s\S]+) \*\* entry!", event.message.text).group('name')
        mcap = re.search("Market cap: \*\*\$(?P<mcap>[0-9,]+)\*\*", event.message.text).group('mcap').replace(',','') if re.search("Market cap: \*\*\$(?P<mcap>[0-9,]+)\*\*", event.message.text) else None
        total_calls = re.search("Total calls : \*\*(?P<total_calls>[0-9]+)\*\*", event.message.text).group('total_calls') if re.search("Total calls : \*\*(?P<total_calls>[0-9]+)\*\*", event.message.text) else 1
        address = re.search("Contract address : \s\*\*(?P<address>[a-zA-Z0-9]{42})\*\*", event.message.text).group('address') if re.search("Contract address : \s\*\*(?P<address>[a-zA-Z0-9]{42})\*\*", event.message.text) else None

        #Filters
        if mcap_from is not None and int(mcap_from) > int(mcap):
            return
        if mcap_to is not None and int(mcap_to) < int(mcap):
            return
        if total_calls_from is not None and int(total_calls_from) > int(total_calls):
            return
        if total_calls_to is not None and int(total_calls_to) < int(total_calls):
            return
        if not show_duplicates and address is not None and address in addresses:
            return

        await update.message.reply_text(event.message.text)

        addresses.append(address)

        print(f"""Date: {date}
{event.message.text}""")
        
        
def get_filters_keyboard() -> list:
    global show_duplicates

    return  [
        [InlineKeyboardButton("MCap From", callback_data='mcap_from'), InlineKeyboardButton("MCap To", callback_data='mcap_to')],
        [InlineKeyboardButton("Total Calls From", callback_data='total_calls_from'), InlineKeyboardButton("Total Calls To", callback_data='total_calls_to')],
        [InlineKeyboardButton("✅ Show Duplicates" if show_duplicates else "❌ Show Duplicates", callback_data='show_duplicates')],
        [InlineKeyboardButton("Reset Filters", callback_data='reset_filters')]    
    ]

def get_telegram_api_keyboard() -> list:
    global phone
    global api_id
    global api_hash

    return  [
        [InlineKeyboardButton(('✅' if phone else '❌') + 'Phone' , callback_data='phone'), InlineKeyboardButton(('✅' if api_id else '❌') + 'Api ID' , callback_data='api_id'), InlineKeyboardButton(('✅' if api_hash else '❌') + 'Api Hash' , callback_data='api_hash')]
    ]


#Comands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
     loop = asyncio.new_event_loop()
     asyncio.set_event_loop(loop)
     loop.run_until_complete(await sniper(update))
     loop.close()

async def set_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Set filters:', reply_markup = InlineKeyboardMarkup(get_filters_keyboard()))

async def check_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
     global mcap_from
     global mcap_to
     global total_calls_from
     global total_calls_to
     global show_duplicates

     await update.message.reply_text(f"""MCap From: {'Not set' if mcap_from is None else mcap_from}
MCap To: {'Not set' if mcap_to is None else mcap_to}
Total Calls From: {'Not set' if total_calls_from is None else total_calls_from}
Total Calls To: {'Not set' if total_calls_to is None else total_calls_to}
Show Duplicates: {'Yes' if show_duplicates else 'No'}""")


async def stop_sniper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global client
    global handle_new_message

    client.remove_event_handler(handle_new_message)


#Buttons

async def filters_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_button_pressed
    global show_duplicates
    global buttons_set

    buttons_set = 'filters_buttons'

    query = update.callback_query
    await query.answer()
    last_button_pressed = query.data

    if query.data == 'mcap_from':
        await query.message.reply_text("Please enter mcap from:")
    elif query.data == 'mcap_to':
        await query.message.reply_text("Please enter mcap to:")
    elif query.data == 'total_calls_from':
        await query.message.reply_text("Please enter total calls from:")
    elif query.data == 'total_calls_to':
        await query.message.reply_text("Please enter total calls to:")
    elif query.data == 'show_duplicates':
        show_duplicates = not show_duplicates

        await query.edit_message_reply_markup(InlineKeyboardMarkup(get_filters_keyboard()))    
    elif query.data == 'reset_filters':
        print("todo")   

async def telegram_api_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_button_pressed
    global show_duplicates
    global buttons_set
    
    buttons_set = 'telegram_api_buttons'

    query = update.callback_query
    await query.answer()
    last_button_pressed = query.data

    if query.data == 'phone':
        await query.message.reply_text("Please enter phone (starting with +359):")
    elif query.data == 'api_id':
        await query.message.reply_text("Please enter your Api Id:")
    elif query.data == 'api_hash':
        await query.message.reply_text("Please enter yor Api Hash:")


# Responses
async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global buttons_set
    global last_button_pressed

    button_handlers = {
        'filters_buttons': fiters_responses,
        'telegram_api_buttons': telegram_api_responses
    }
    
    if last_button_pressed is not None:
        if buttons_set in button_handlers:
            await button_handlers[buttons_set](update, context)

            buttons_set = None
            last_button_pressed = None
        else:
            if last_button_pressed == 'sent_code':
                await client_sign_in(update, context)
            elif last_button_pressed == 'passcode':
                await client_passcode_sign_in(update, context)

                last_button_pressed = None

    else:
        await update.message.reply_text("Please choose option first.")

async def fiters_responses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_button_pressed
    global mcap_from
    global mcap_to
    global total_calls_from
    global total_calls_to

    if last_button_pressed == 'mcap_from':
        mcap_from = update.message.text
    elif last_button_pressed == 'mcap_to':
        mcap_to = update.message.text
    elif last_button_pressed == 'total_calls_from':
        total_calls_from = update.message.text
    elif last_button_pressed == 'total_calls_to':
        total_calls_to = update.message.text
    
    input = update.message.text
    await update.message.reply_text(f"{last_button_pressed} is set to {input}.")

async def telegram_api_responses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_button_pressed
    global phone
    global api_id
    global api_hash
    
    if last_button_pressed == 'phone':
        phone = update.message.text
    elif last_button_pressed == 'api_id':
        api_id = update.message.text
    elif last_button_pressed == 'api_hash':
        api_hash = update.message.text
    
    input = update.message.text
    await update.message.reply_text(f"{last_button_pressed} is set to {input}.")
    
    await update.message.reply_text('Please set your telegram data:', reply_markup = InlineKeyboardMarkup(get_telegram_api_keyboard()))


#Errors
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}') 



#Start app
if __name__ == '__main__':
    print('Running...')
    app = Application.builder().token(TOKEN).build()
   
    #Commands
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('set_filters', set_filters))
    app.add_handler(CommandHandler('check_filters', check_filters))
    app.add_handler(CommandHandler('stop_sniper', stop_sniper))
    app.add_handler(CallbackQueryHandler(filters_buttons, pattern = 'mcap_from|mcap_to|total_calls_from|total_calls_to|show_duplicates|reset_filters'))
    app.add_handler(CallbackQueryHandler(telegram_api_buttons, pattern = 'phone|api_id|api_hash'))

    # #Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_input))

    #Errors
    app.add_error_handler(error)

    app.run_polling(poll_interval=3)

    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    # loop.run_until_complete(main())
    
    #loop.close()


    