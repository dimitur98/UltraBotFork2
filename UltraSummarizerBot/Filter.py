class Filter:
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
    very_high_hype_alerts = False
    high_hype_alerts = False
    medium_hype_alerts = False
    show_duplicates = False
    chat_id = None
    is_started = False
    send_to_group = False

    def __init__(self, chat_id):
        print(chat_id)
        self.chat_id = chat_id