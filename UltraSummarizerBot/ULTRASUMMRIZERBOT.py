from telethon import events
from telethon.sync import *
from telethon.errors.rpcerrorlist import PasswordHashInvalidError, PhoneCodeInvalidError, SessionPasswordNeededError, FloodWaitError 
import asyncio
from telethon.tl.types import InputPeerChannel
from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes,CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import re
from Signal import *
from AlarmType import *
from Filter import *
from db import *
from telegram import Bot
TOKEN: Final = '6789275807:AAFG9Y3WA-xCdH7p5V7Lf3LpQjhOKuhJIME'
BOT_USERNAME: Final = 'UltraSummarizerBot'
CHAT_ID = '-1002109419948'
MY_CHAT_ID = 1653117688

bot = None
client = None
phone = '+359877543669'
api_id = 7181035
api_hash = '03413b514dcbd241205bcfdcf8dbf92f'
phone_hash = None
db = None
last_button_pressed = None
buttons_set = None
handle_new_message_sim_bot_ultra = None
handle_new_message_hype_bot = None
filters_dict = {}

#Client initializing
async def client_passcode_sign_in(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global client

    try:
        password = update.message.text

        await client.sign_in(password = str(password))

        # await update.message.reply_text('Login successful. You can start bot now!')
        await bot.send_message(chat_id=MY_CHAT_ID, text = 'Login successful. You can start bot now!')
    except PasswordHashInvalidError:
        # await update.message.reply_text('Invalid passcode.')
        await bot.send_message(chat_id=MY_CHAT_ID, text = 'Invalid passcode.')
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

        # await update.message.reply_text('Login successful. You can start bot now!')
        await bot.send_message(chat_id=MY_CHAT_ID, text = 'Login successful. You can start bot now!')

    except SessionPasswordNeededError:
        last_button_pressed = 'passcode'

        # await update.message.reply_text('Please enter telegram passcode:')
        await bot.send_message(chat_id=MY_CHAT_ID, text = 'Please enter telegram passcode:')
    except PhoneCodeInvalidError:
        # await update.message.reply_text('Invalid code.')
        await bot.send_message(chat_id=MY_CHAT_ID, text = 'Invalid code.')
    except Exception as err:
        print(err)

async def client_initializer():
    global client
    global phone
    global api_id
    global api_hash
    global phone_hash
    global last_button_pressed
    
    client = None

    if (phone is None or api_id is None or api_hash is None):
        #await update.message.reply_text('Please set your telegram data:', reply_markup = InlineKeyboardMarkup(get_telegram_api_keyboard()))
        await bot.send_message(chat_id=MY_CHAT_ID, text = "Please set your telegram data:", reply_markup = InlineKeyboardMarkup(get_telegram_api_keyboard()))
        return

    try:
        client = TelegramClient(phone, api_id, api_hash)
        await client.connect()
        print(phone)

        if not await client.is_user_authorized():
            last_button_pressed = 'sent_code'

            phone_hash = await client.send_code_request(phone)

            #await update.message.reply_text('Please enter telegram code:')
            await bot.send_message(chat_id=MY_CHAT_ID, text = 'Please enter telegram code:')
      
    except FloodWaitError  as errr:
        print(errr)
    except Exception as error:
        print(error)

#Functions
def round(num):
    int_num = int(num)
    decimal = num - int_num

    if decimal >= 0.5:
        int_num +=1
    
    return int_num

def get_signal_index_by_address(address):
    global signals

    for i,signal in enumerate(signals):
        if signal.address == address:
            return i
        
    return None

def get_or_create_filter(user_id, chat_id):
    global filters_dict

    filter = filters_dict.get(user_id)
    
    if filter is None:
        print("chat_id in get filter keyboards: ",chat_id)
        filter = Filter(chat_id)
        filters_dict[user_id] = filter

    return filter

def basic_filters(filter, signal):
    if filter.mcap_from is not None and int(filter.mcap_from) > int(signal.mcap):
        return False
    if filter.mcap_to is not None and int(filter.mcap_to) < int(signal.mcap):    
        return False
    if filter.total_calls_from is not None and int(filter.total_calls_from) > int(signal.total_calls):
        return
    if filter.total_calls_to is not None and int(filter.total_calls_to) < int(signal.total_calls):
        return False
    
    if filter.sell_tax_from is not None and filter.sell_tax_to is not None and filter.buy_tax_from is not None and filter.buy_tax_to is not None:
        if signal.sell_tax is None or signal.buy_tax is None:
            return False
        if filter.sell_tax_from is not None and filter.sell_tax_from > signal.sell_tax:
            return False
        if filter.sell_tax_to is not None and filter.sell_tax_to < signal.sell_tax:
            return False
        if filter.buy_tax_from is not None and filter.buy_tax_from > signal.buy_tax:
            return False
        if filter.buy_tax_to is not None and filter.buy_tax_to < signal.buy_tax:
            return False
    
    return True

async def print_signal(signal):
    global bot
    global filters_dict

    print("new check")
    for user_id, filter in filters_dict.items():
        if not filter.is_started:
            continue
        print(user_id)
        if not basic_filters(filter, signal):
            continue

        if not filter.show_duplicates:
            user_signal = db.get_user_signal(user_id, signal.address)

            if user_signal is not None:
                continue

        if filter.signal_repetitions is not None:
            signals = db.get_signals_by_address(signal.address, limit = filter.signal_repetitions)
            
            not_valid = False
            for item in signals:
                if not basic_filters(filter, item):
                    not_valid = True
                    break
                
            if not_valid:
                continue

            if len(signals) < filter.signal_repetitions:
                continue
        
            if filter.time_from is not None and filter.time_to is not None:
                print("repeated signal")

                first_signal = signals[0]
                date_diff = first_signal.date - signal.date
                minutes_diff = round(date_diff.total_seconds() / 60)
                signal.calls += 1
                print(minutes_diff)
                if filter.time_from >= minutes_diff or filter.time_to <= minutes_diff:
                    continue

        if filter.very_high_hype_alerts:
            if signal.alarm_type is None or signal.alarm_type != AlarmType.VERY_HIGH:
                continue

        

        db.insert_user_signal(user_id, signal.address)

        if filter.send_to_group:
            await bot.send_message(chat_id=CHAT_ID, text = signal.text)
        else:
            await bot.send_message(chat_id=filter.chat_id, text = signal.text)

async def sniper():
    global db
    global client
    global handle_new_message_sim_bot_ultra
    global handle_new_message_hype_bot
    
    if client is None:
        await client_initializer()

    entity_hype_bot = await client.get_entity('https://t.me/onlyhypealarms')
    group_entity_hype_bot = InputPeerChannel(entity_hype_bot.id, entity_hype_bot.access_hash)

    @client.on(events.NewMessage(chats=group_entity_hype_bot))
    async def handle_new_message_hype_bot(event):
        address = re.search("\*\*Contract:  \*\* `(?P<address>[a-zA-Z0-9]{42})`", event.message.text).group('address') if re.search("\*\*Contract:  \*\* `(?P<address>[a-zA-Z0-9]{42})`", event.message.text) else None
        
        if address is None:
            return

        signal = db.get_last_signal_by_address(address)
        if signal is None:
            return
        
        signal.alarm_type = AlarmType.VERY_HIGH if re.search("\*\*Very High Hype Detected\*\*", event.message.text) else AlarmType.HIGH if re.search("\*\*High Hype Detected\*\*", event.message.text) else AlarmType.HIGH if re.search("\*\*Small Hype Detected\*\*", event.message.text) else None
        mcap = re.search("\*\*Current MC:  \*\* \$(?P<mcap>[0-9,.]+)", event.message.text).group('mcap') if re.search("\*\*Current MC:  \*\* \$(?P<mcap>[0-9,.]+)", event.message.text) else None
        
        if mcap is not None:
            signal.text += f"""
Hype Alarm Market Cap: {mcap}"""
        
        await print_signal(signal)

    entity_sim_bot_ultra = await client.get_entity('https://t.me/+8d_erKU1nm5iYjM8')
    group_entity_sim_bot_ultra = InputPeerChannel(entity_sim_bot_ultra.id, entity_sim_bot_ultra.access_hash)
    
    @client.on(events.NewMessage(chats=group_entity_sim_bot_ultra))
    async def handle_new_message_sim_bot_ultra(event):
        date = event.message.date
        #name = re.search("\*\*(?P<name>[\s\S]+) \*\* entry!", event.message.text).group('name')
        mcap = re.search("Market cap: \*\*\$(?P<mcap>[0-9,]+)\*\*", event.message.text).group('mcap').replace(',','') if re.search("Market cap: \*\*\$(?P<mcap>[0-9,]+)\*\*", event.message.text) else None
        total_calls = re.search("Total calls : \*\*(?P<total_calls>[0-9]+)\*\*", event.message.text).group('total_calls') if re.search("Total calls : \*\*(?P<total_calls>[0-9]+)\*\*", event.message.text) else 1
        address = re.search("Contract address : \s\*\*(?P<address>[a-zA-Z0-9]{42})\*\*", event.message.text).group('address') if re.search("Contract address : \s\*\*(?P<address>[a-zA-Z0-9]{42})\*\*", event.message.text) else None

        if re.search("\*\*DYOR/NFA\*\*: Automated report.", event.message.text):
            #Otto bot info
            report_address = re.search("]\(https://etherscan.io/token/(?P<address>[0-9a-zA-Z]{42})\)", event.message.text).group('address') if re.search("]\(https://etherscan.io/token/(?P<address>[0-9a-zA-Z]{42})\)", event.message.text) else None
            buy_tax = int(re.search("\*\*Tax\*\*: B: (?P<buy_tax>[0-9]+)%", event.message.text).group('buy_tax')) if re.search("\*\*Tax\*\*: B: (?P<buy_tax>[0-9]+)%", event.message.text) else None
            sell_tax = int(re.search("\*\*Tax\*\*: B: [0-9]+% \| S: (?P<sell_tax>[0-9]+)%", event.message.text).group('sell_tax')) if re.search("\*\*Tax\*\*: B: [0-9]+% \| S: (?P<sell_tax>[0-9]+)%", event.message.text) else None

            if report_address is not None and buy_tax is not None and sell_tax is not None:
                signal = db.get_last_signal_by_address(report_address)
                print(signal)
                if signal is not None:
                    signal.buy_tax = buy_tax
                    signal.sell_tax = sell_tax
                    print("in sell tax check")
                    await print_signal(signal)
        else:
            #Filters
            if address is None: 
                return
            
            signal = Signal(address, mcap, event.message.text, date, total_calls)

            db.insert_signal(signal)
            await print_signal(signal)
        
def get_filters_keyboard(user_id, chat_id) -> list:
    global db

    # filter = db.get_filter_by_user_id(user_id)
    filter = filters_dict.get(user_id)
    
    if filter is None:
        print("chat_id in get filter keyboards: ",chat_id)
        filter = Filter(chat_id)
        filters_dict[user_id] = filter

    return  [
        [InlineKeyboardButton("MCap From", callback_data='mcap_from'), InlineKeyboardButton("MCap To", callback_data='mcap_to')],
        [InlineKeyboardButton("Total Calls From", callback_data='total_calls_from'), InlineKeyboardButton("Total Calls To", callback_data='total_calls_to')],
        [InlineKeyboardButton("Sell Tax From", callback_data='sell_tax_from'), InlineKeyboardButton("Sell Tax To", callback_data='sell_tax_to')],
        [InlineKeyboardButton("Buy Tax From", callback_data='buy_tax_from'), InlineKeyboardButton("Buy Tax To", callback_data='buy_tax_to')],
        [InlineKeyboardButton("Time From", callback_data='time_from'), InlineKeyboardButton("Time To", callback_data='time_to')],
        [InlineKeyboardButton("Signal Repetitions", callback_data='signal_repetitions')],
        [InlineKeyboardButton("✅ Very High Hype Signals Only" if filter.very_high_hype_alerts else "❌ Very High Hype Signals Only", callback_data='very_high_hype_alerts')],
        [InlineKeyboardButton("✅ Show Duplicates" if filter.show_duplicates else "❌ Show Duplicates", callback_data='show_duplicates')],
        [InlineKeyboardButton("✅ Send To Group" if filter.send_to_group else "❌ Send To Group", callback_data='send_to_group')],
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
    #global db
    # db.update_filter_start(update.message.from_user.id, True)
    filter = get_or_create_filter(update.message.from_user.id, update.message.chat_id)
    filter.is_started = True



async def set_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Set filters:', reply_markup = InlineKeyboardMarkup(get_filters_keyboard(update.message.from_user.id, update.message.chat_id)))

async def check_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global db
    global filters_dict

    # filter = db.get_filter_by_user_id(update.message.from_user.id)
    filter = filters_dict.get(update.message.from_user.id)

    await update.message.reply_text(f"""MCap From: {'Not set' if filter.mcap_from is None else filter.mcap_from}
MCap To: {'Not set' if filter.mcap_to is None else filter.mcap_to}
Total Calls From: {'Not set' if filter.total_calls_from is None else filter.total_calls_from}
Total Calls To: {'Not set' if filter.total_calls_to is None else filter.total_calls_to}
Sell Tax From: {'Not set' if filter.sell_tax_from is None else filter.sell_tax_from}
Sell Tax To: {'Not set' if filter.sell_tax_to is None else filter.sell_tax_to}
Buy Tax From: {'Not set' if filter.buy_tax_from is None else filter.buy_tax_from}
Buy Tax To: {'Not set' if filter.buy_tax_to is None else filter.buy_tax_to}
Time From: {'Not set' if filter.time_from is None else filter.time_from}
Time To: {'Not set' if filter.time_to is None else filter.time_to}
Signal Repetitions: {'Not set' if filter.signal_repetitions is None else filter.signal_repetitions}
Very High Hype Alerts: {'Yes' if filter.very_high_hype_alerts else 'No'}
Show Duplicates: {'Yes' if filter.show_duplicates else 'No'}
Send To Group: {'Yes' if filter.send_to_group else 'No'}""")


async def stop_sniper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filter = get_or_create_filter(update.message.from_user.id, update.message.chat_id)
    filter.is_started = False
    # global db
    # print(update)
    # db.update_filter_start(update.message.from_user.id, False)
    # global client
    # global handle_new_message_sim_bot_ultra
    # global handle_new_message_hype_bot

    #client.remove_event_handler(handle_new_message_sim_bot_ultra)
    #client.remove_event_handler(handle_new_message_hype_bot)



#Buttons

async def filters_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_button_pressed
    global buttons_set
    global db
    global filters_dict
    global bot

    buttons_set = 'filters_buttons'

    query = update.callback_query
    await query.answer()
    last_button_pressed = query.data
    
    if query.data == 'show_duplicates' or query.data == 'very_high_hype_alerts' or query.data == 'reset_filters' or query.data == 'send_to_group':
        user_id = update.callback_query.from_user.id
        chat_id = update.callback_query.message.chat.id
        # filter = db.get_filter_by_user_id(user_id)
        filter = filters_dict.get(user_id)

        if filter is None:
            filter = Filter(update.callback_query.message.chat.id)
            filters_dict[user_id] = filter

        if query.data == 'show_duplicates':
            filter.show_duplicates = not filter.show_duplicates

            await query.edit_message_reply_markup(InlineKeyboardMarkup(get_filters_keyboard(user_id, chat_id)))
        elif query.data == 'very_high_hype_alerts':
            filter.very_high_hype_alerts = not filter.very_high_hype_alerts

            await query.edit_message_reply_markup(InlineKeyboardMarkup(get_filters_keyboard(user_id, chat_id)))
        elif query.data == 'send_to_group':
            filter.send_to_group = not filter.send_to_group

            await query.edit_message_reply_markup(InlineKeyboardMarkup(get_filters_keyboard(user_id, chat_id)))
        elif query.data == 'reset_filters':
            db.delete_user_signal(user_id)
            filters_dict.pop(user_id)

        # db.insert_filter(filter, user_id)
        
    else:
        await query.message.reply_text(f'Please enter {query.data}:')
  
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
    global db
    global last_button_pressed
    
    user_id = update.message.from_user.id
    #filter = db.get_filter_by_user_id(user_id)
    #filter.__setattr__(last_button_pressed, int(update.message.text))
    # globals()[last_button_pressed] = int(update.message.text)
    #db.insert_filter(filter, user_id)
    filter = filters_dict.get(user_id)

    if filter is None:
        filter = Filter(update.message.chat_id)
        filters_dict[user_id] = filter

    filter.__setattr__(last_button_pressed, int(update.message.text))

    await update.message.reply_text(f"{last_button_pressed} is set to {update.message.text}.")

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

    db = DB()
    bot = Bot(token=TOKEN)

    app = Application.builder().token(TOKEN).build()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(sniper())
    # loop.close()

    #Commands
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('set_filters', set_filters))
    app.add_handler(CommandHandler('check_filters', check_filters))
    app.add_handler(CommandHandler('stop_sniper', stop_sniper))
    app.add_handler(CallbackQueryHandler(filters_buttons, pattern = 'mcap_from|mcap_to|total_calls_from|total_calls_to|sell_tax_from|sell_tax_to|buy_tax_from|buy_tax_to|time_from|time_to|signal_repetitions|very_high_hype_alerts|show_duplicates|send_to_group|reset_filters'))
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

        # result = await client(GetDialogsRequest(
    #         offset_date=None,
    #         offset_id=0,
    #         offset_peer=InputPeerEmpty(),
    #         limit=200,
    #         hash = 0
    # ))
   

    # chat = next(x for x in result.chats if x.title == "SIM BOT ULTRA")    