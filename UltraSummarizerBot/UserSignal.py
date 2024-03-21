class UserSignal:
    user_id = None
    signal_address = None
    is_sent = False

    def __init__(self, user_id, signal_address, is_sent = False):
        self.user_id = user_id
        self.signal_address = signal_address
        self.is_sent = is_sent