class Signal:
    address = None
    text = None
    buy_tax = None
    sell_tax = None
    date = None
    calls = 1
    alarm_type = None
    is_sent = False
    is_in_time_range = False

    def __init__(self, address, text, date):
        self.address = address
        self.text = text
        self.date = date

    def toString(self):
        return f'address: {self.address} B: {self.buy_tax}, S: {self.sell_tax}'

    