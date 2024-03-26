class Signal:
    address = None
    mcap = None
    text = None
    buy_tax = None
    sell_tax = None
    date = None
    total_calls = 1
    alarm_type = None

    def __init__(self, address, mcap, text, date, total_calls):
        self.address = address
        self.mcap = mcap
        self.text = text
        self.date = date
        self.total_calls = total_calls

    def toString(self):
        return f'address: {self.address} B: {self.buy_tax}, S: {self.sell_tax}'

    