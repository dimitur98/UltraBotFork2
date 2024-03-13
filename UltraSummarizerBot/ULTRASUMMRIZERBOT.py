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
from Signal import *
from AlarmType import *
from telegram import Bot

TOKEN: Final = '6789275807:AAFG9Y3WA-xCdH7p5V7Lf3LpQjhOKuhJIME'
BOT_USERNAME: Final = 'UltraSummarizerBot'
CHAT_ID = '-1002109419948'

bot = None
client = None
phone = '+359877543669'
api_id = 7181035
api_hash = '03413b514dcbd241205bcfdcf8dbf92f'
phone_hash = None
mcap_from = None
mcap_to = None
total_calls_from = None
total_calls_to = None
sell_tax_from = None
sell_tax_to = None
buy_tax_from = None
buy_tax_to = None
time_from = None
time_to = None
signal_repetitions = None
very_high_hype_alerts = True
show_duplicates = False
send_to_group = False
last_button_pressed = None
buttons_set = None
handle_new_message_sim_bot_ultra = None
handle_new_message_hype_bot = None
signals = list()
addresses = list()

#Client initializing
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


async def print_signal(update, signal, date = None):
    global bot
    global sell_tax_from
    global sell_tax_to
    global buy_tax_from
    global buy_tax_to
    global time_from
    global time_to
    global signal_repetitions
    global very_high_hype_alerts
    global send_to_group

    print(f'address: {signal.address}, date: {signal.date}, calls: {signal.calls}')
    if sell_tax_from is not None and sell_tax_to is not None and buy_tax_from is not None and buy_tax_to is not None:
        print(1)
        if signal.sell_tax is None or signal.buy_tax is None:
            return
        if sell_tax_from is not None and sell_tax_from > signal.sell_tax:
            return
        if sell_tax_to is not None and sell_tax_to < signal.sell_tax:
            return
        if buy_tax_from is not None and buy_tax_from > signal.buy_tax:
            return
        if buy_tax_to is not None and buy_tax_to < signal.buy_tax:
            return

    if time_from is not None and time_to is not None and signal_repetitions is not None and date is not None:
                print("repeated signal")
                print(f"date:{date}")
                date_diff = date - signal.date
                minutes_diff = round(date_diff.total_seconds() / 60)
                signal.calls += 1
                print(minutes_diff)
                if signal.calls != signal_repetitions or time_from >= minutes_diff or time_to <= minutes_diff:
                    return
                
    if very_high_hype_alerts:
        if signal.alarm_type is None or signal.alarm_type != AlarmType.VERY_HIGH:
            return
    
    if not show_duplicates and signal.is_sent:
        return
        
    signal.is_sent = True

    if send_to_group:
        await bot.send_message(chat_id=CHAT_ID, text = signal.text)
    else:
        print(1)
        await update.message.reply_text(signal.text)

async def sniper(update: Update):
    global client
    global handle_new_message_sim_bot_ultra
    global handle_new_message_hype_bot
    
    if client is None:
        await client_initializer(update)

    entity_hype_bot = await client.get_entity('https://t.me/onlyhypealarms')
    group_entity_hype_bot = InputPeerChannel(entity_hype_bot.id, entity_hype_bot.access_hash)

    @client.on(events.NewMessage(chats=group_entity_hype_bot))
    async def handle_new_message_hype_bot(event):
        address = re.search("\*\*Contract:  \*\* `(?P<address>[a-zA-Z0-9]{42})`", event.message.text).group('address') if re.search("\*\*Contract:  \*\* `(?P<address>[a-zA-Z0-9]{42})`", event.message.text) else None
        if address is None:
            return

        i = get_signal_index_by_address(address)
        if i is None:
            return
        
        signal = signals[i]
        signal.alarm_type = AlarmType.VERY_HIGH if re.search("\*\*Very High Hype Detected\*\*", event.message.text) else AlarmType.HIGH if re.search("\*\*High Hype Detected\*\*", event.message.text) else AlarmType.HIGH if re.search("\*\*Small Hype Detected\*\*", event.message.text) else None
        mcap = re.search("\*\*Current MC:  \*\* \$(?P<mcap>[0-9,.]+)", event.message.text).group('mcap') if re.search("\*\*Current MC:  \*\* \$(?P<mcap>[0-9,.]+)", event.message.text) else None
        
        if mcap is not None:
            signal.text += f"""
Hape Alarm Market Cap: {mcap}"""
        
        await print_signal(update, signal)

    entity_sim_bot_ultra = await client.get_entity('invitation link')
    group_entity_sim_bot_ultra = InputPeerChannel(entity_sim_bot_ultra.id, entity_sim_bot_ultra.access_hash)
    
    @client.on(events.NewMessage(chats=group_entity_sim_bot_ultra))
    async def handle_new_message_sim_bot_ultra(event):
        global mcap_from
        global mcap_to
        global total_calls_from
        global total_calls_to
        global sell_tax_from
        global sell_tax_to
        global buy_tax_from
        global buy_tax_to
        global time_from
        global time_to
        global signal_repetitions
        global addresses
        global signals

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

            if report_address is not None and buy_tax is not None and sell_tax is not None and len(signals) > 0:
                i = get_signal_index_by_address(report_address)

                if i is not None:
                    signal = signals[i]
                    signal.buy_tax = buy_tax
                    signal.sell_tax = sell_tax
                    print("in sell tax check")
                    await print_signal(update, signal, date = None)
        else:
            #Filters
            if address is None: 
                return
            
            i = get_signal_index_by_address(address)
            if time_from is not None and time_to is not None and signal_repetitions is not None and i is not None:
                print("in check for repeat")
                await print_signal(update, signals[i], date)
            else:
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
                
                signal = Signal(address, event.message.text, date)
                print("in check for signal")
                # print(event.message.message)
                await print_signal(update, signal)
 
                addresses.append(address)
                signals.append(signal)

        
        
def get_filters_keyboard() -> list:
    global very_high_hype_alerts
    global show_duplicates
    global send_to_group

    return  [
        [InlineKeyboardButton("MCap From", callback_data='mcap_from'), InlineKeyboardButton("MCap To", callback_data='mcap_to')],
        [InlineKeyboardButton("Total Calls From", callback_data='total_calls_from'), InlineKeyboardButton("Total Calls To", callback_data='total_calls_to')],
        [InlineKeyboardButton("Sell Tax From", callback_data='sell_tax_from'), InlineKeyboardButton("Sell Tax To", callback_data='sell_tax_to')],
        [InlineKeyboardButton("Buy Tax From", callback_data='buy_tax_from'), InlineKeyboardButton("Buy Tax To", callback_data='buy_tax_to')],
        [InlineKeyboardButton("Time From", callback_data='time_from'), InlineKeyboardButton("Time To", callback_data='time_to')],
        [InlineKeyboardButton("Signal Repetitions", callback_data='signal_repetitions')],
        [InlineKeyboardButton("✅ Very High Hype Signals Only" if very_high_hype_alerts else "❌ Very High Hype Signals Only", callback_data='very_high_hype_alerts')],
        [InlineKeyboardButton("✅ Show Duplicates" if show_duplicates else "❌ Show Duplicates", callback_data='show_duplicates')],
        [InlineKeyboardButton("✅ Send To Group" if send_to_group else "❌ Send To Group", callback_data='send_to_group')],
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
    global sell_tax_from
    global sell_tax_to
    global buy_tax_from
    global buy_tax_to
    global time_from
    global time_to
    global signal_repetitions
    global very_high_hype_alerts
    global show_duplicates
    global send_to_group

    await update.message.reply_text(f"""MCap From: {'Not set' if mcap_from is None else mcap_from}
MCap To: {'Not set' if mcap_to is None else mcap_to}
Total Calls From: {'Not set' if total_calls_from is None else total_calls_from}
Total Calls To: {'Not set' if total_calls_to is None else total_calls_to}
Sell Tax From: {'Not set' if sell_tax_from is None else sell_tax_from}
Sell Tax To: {'Not set' if sell_tax_to is None else sell_tax_to}
Buy Tax From: {'Not set' if buy_tax_from is None else buy_tax_from}
Buy Tax To: {'Not set' if buy_tax_to is None else buy_tax_to}
Time From: {'Not set' if time_from is None else time_from}
Time To: {'Not set' if time_to is None else time_to}
Signal Repetitions: {'Not set' if signal_repetitions is None else signal_repetitions}
Very High Hype Alerts: {'Yes' if very_high_hype_alerts else 'No'}
Show Duplicates: {'Yes' if show_duplicates else 'No'}
Send To Group: {'Yes' if send_to_group else 'No'}""")


async def stop_sniper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global client
    global handle_new_message_sim_bot_ultra
    global handle_new_message_hype_bot

    client.remove_event_handler(handle_new_message_sim_bot_ultra)
    client.remove_event_handler(handle_new_message_hype_bot)



#Buttons

async def filters_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_button_pressed
    global very_high_hype_alerts
    global show_duplicates
    global send_to_group
    global buttons_set

    buttons_set = 'filters_buttons'

    query = update.callback_query
    await query.answer()
    last_button_pressed = query.data

    if query.data == 'show_duplicates':
        show_duplicates = not show_duplicates

        await query.edit_message_reply_markup(InlineKeyboardMarkup(get_filters_keyboard()))
    elif query.data == 'very_high_hype_alerts':
        very_high_hype_alerts = not very_high_hype_alerts

        await query.edit_message_reply_markup(InlineKeyboardMarkup(get_filters_keyboard()))
    elif query.data == 'send_to_group':
        send_to_group = not send_to_group

        await query.edit_message_reply_markup(InlineKeyboardMarkup(get_filters_keyboard()))
    elif query.data == 'reset_filters':
        print("todo") 
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
    global last_button_pressed
    
    globals()[last_button_pressed] = int(update.message.text)
    
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
    bot = Bot(token=TOKEN)
    app = Application.builder().token(TOKEN).build()
    
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

    #to do
    #clear filters by unnececcary int
    #check if otto messgaes match address,total_calls,mcap regex for sim bot ultra messages


    