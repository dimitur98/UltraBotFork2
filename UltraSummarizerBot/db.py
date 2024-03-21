import sqlite3
from Filter import *
from functools import lru_cache, wraps
from dbutils.pooled_db import PooledDB
from Signal import *
from UserSignal import *
from datetime import datetime

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S%z"

class DB:
    DB_NAME = "ultra_summarizer_bot"
    pool = None

    def __init__(self):
        self.pool = PooledDB(self.create_db_connection, mincached=1, maxcached=10, maxshared=3, maxconnections=10)

        self.create_table_filter()
        self.create_table_signal()
        self.create_user_signal()     
    
    #Cache
    def memoize(func):
        cache = {}

        @wraps(func)
        def wrapper(*args):
            if args in cache:
                return cache[args]
            else:
                result = func(*args)
                cache[args] = result
                return result

        return wrapper
    #insert functions
    def insert_signal(self, signal):
        sql = """INSERT INTO signal
        (
            address,
            mcap,
            text,
            sell_tax,
            buy_tax,
            date,
            total_calls
        )
        VALUES(
            :address,
            :mcap,
            :text,
            :sell_tax,
            :buy_tax,
            :date,
            :total_calls
        );
        """
        query_params = {
            "address": signal.address,
            "mcap": signal.mcap,
            "text": signal.text,
            "sell_tax": signal.sell_tax,
            "buy_tax":signal.buy_tax,
            "date": signal.date,
            "total_calls": signal.total_calls
        }

        self.execute_sql(sql, query_params = query_params)
    
    def insert_filter(self, filter, user_id):
        sql = """INSERT OR REPLACE INTO filter
        (
            user_id,
            mcap_from,
            mcap_to,
            total_calls_from,
            total_calls_to,
            sell_tax_from,
            sell_tax_to,
            buy_tax_from,
            buy_tax_to,
            time_from,
            time_to,
            signal_repetitions,
            very_high_hype_alerts,
            high_hype_alerts,
            medium_hype_alerts,
            show_duplicates,
            chat_id,
            is_started
        )
        VALUES(
            :user_id,
            :mcap_from,
            :mcap_to,
            :total_calls_from,
            :total_calls_to,
            :sell_tax_from,
            :sell_tax_to,
            :buy_tax_from,
            :buy_tax_to,
            :time_from,
            :time_to,
            :signal_repetitions,
            :very_high_hype_alerts,
            :high_hype_alerts,
            :medium_hype_alerts,
            :show_duplicates,
            :chat_id,
            :is_started
        );
        """
        query_params = {
            "user_id": user_id,
            "mcap_from": filter.mcap_from,
            "mcap_to": filter.mcap_to,
            "total_calls_from":filter.total_calls_from,
            "total_calls_to": filter.total_calls_to,
            "sell_tax_from": filter.sell_tax_from,
            "sell_tax_to":filter.sell_tax_to,
            "buy_tax_from":filter.buy_tax_from,
            "buy_tax_to":filter.buy_tax_to,
            "time_from":filter.time_from,
            "time_to":filter.time_to,
            "signal_repetitions":filter.signal_repetitions,
            "very_high_hype_alerts":filter.very_high_hype_alerts,
            "high_hype_alerts":filter.high_hype_alerts,
            "medium_hype_alerts":filter.medium_hype_alerts,
            "show_duplicates": filter.show_duplicates,
            "chat_id": filter.chat_id,
            "is_started": filter.is_started
        }
        
        self.execute_sql(sql, query_params = query_params)
   
    def insert_user_signal(self, user_id, signal_address, is_sent = True):
        sql = """INSERT INTO user_signal
        (
            user_id,
            signal_address,
            is_sent
        )
        VALUES(
            :user_id,
            :signal_address,
            :is_sent
        );
        """
        query_params = {
            "signal_address": signal_address,
            "user_id": user_id,
            "is_sent": is_sent
        }

        self.execute_sql(sql, query_params = query_params)
   
    #update functions
    def update_signal_tax(self, address, sell_tax, buy_tax):
        sql = """UPDATE signal SET
            sell_tax = :sell_tax,
            buy_tax = :buy_tax
        WHERE address = :address"""

        query_params = {
            "address": address,
            "sell_tax": sell_tax,
            "buy_tax": buy_tax
        }

        self.execute_sql(sql, query_params = query_params)

    def update_filter_start(self, user_id, is_started):
        sql = """UPDATE filter SET
            is_started = :is_started
        WHERE user_id = :user_id"""

        query_params = {
            "user_id": user_id,
            "is_started": is_started
        }

        self.execute_sql(sql, query_params = query_params)

    #get by functions
    @memoize
    def get_filter_by_user_id(self, user_id):
        sql = """SELECT * FROM filter WHERE user_id = :user_id"""
        response = self.execute_sql_fetch_one(sql, query_params = {"user_id": user_id})

        if response is None:
            response = Filter()

        return response
    
    def get_first_signal_by_address(self, address):
        sql = """SELECT * FROM signal WHERE address = :address ORDER BY date"""
        response = self.execute_sql_fetch_one(sql, query_params = {"address": address})
        if response is not None:
            return Signal(response[1], response[7], response[2], datetime.strptime(response[5], DATETIME_FORMAT), response[6])

        return response
    
    def get_last_signal_by_address(self, address):
        sql = """SELECT * FROM signal WHERE address = :address ORDER BY date DESC"""

        response = self.execute_sql_fetch_one(sql, query_params = {"address": address})

        if response is not None:
            return Signal(response[1], response[7], response[2], datetime.strptime(response[5], DATETIME_FORMAT), response[6])

        return response
    
    def get_signals_by_address(self, address, limit = None):
        sql = """SELECT * FROM signal WHERE address = :address ORDER BY date DESC"""

        if limit is not None:
            sql += """LIMIT :limit"""

        response = self.execute_sql_fetch_one(sql, query_params = {"address": address, "limit": limit})

        if response is not None:
            signals = list()

            for signal in response:
                signals.append(Signal(signal[1], signal[7], signal[2], datetime.strptime(signal[5], DATETIME_FORMAT), signal[6]))
            
            return signals

        return response
    
    def get_user_signal(self, user_id, address, is_sent = True):
        sql = """SELECT * FROM user_signal WHERE user_id = :user_id AND address = :address AND is_sent = @is_sent"""

        response = self.execute_sql_fetch_one(sql, query_params = {"user_id": user_id, "address": address, "is_sent": is_sent})

        if response is not None:
            return UserSignal(response[1], response[2], is_sent = response[3])

        return response
    
    #delete functions
    def delete_user_signal(self, user_id):
        sql = """DELETE FROM user_signal WHERE user_id = :user_id"""

        self.execute_sql(sql, query_params = { "user_id", user_id })

    def delete_filter(self, user_id):
        sql = """DELETE FROM filter WHERE user_id = :user_id"""

        self.execute_sql(sql, query_params = { "user_id", user_id })

    #Create db tables
    def create_table_signal(self):
        sql = """ CREATE TABLE IF NOT EXISTS signal(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        address TEXT NOT NULL,
        text TEXT NOT NULL,
        sell_tax REAL,
        buy_tax REAL,
        date TIMESTAMP NOT NULL,
        total_calls INTEGER NOT NULL
        )
        """
        self.execute_sql(sql)

    def create_table_filter(self):
        sql = """ CREATE TABLE IF NOT EXISTS filter(
        user_id INTEGER PRIMARY KEY,
        mcap_from INTEGER,
        mcap_to INTEGER,
        total_calls_from INTEGER,
        total_calls_to INTEGER,
        sell_tax_from INTEGER,
        sell_tax_to INTEGER,
        buy_tax_from INTEGER,
        buy_tax_to INTEGER,
        time_from INTEGER,
        time_to INTEGER,
        signal_repetitions INTEGER,
        very_high_hype_alerts BOOLEAN,
        high_hype_alerts BOOELAN,
        medium_hype_alerts BOOLEAN,
        show_duplicates BOOLEAN,
        chat_id INTEGER,
        is_started BOOLEAN
        )
        """
        self.execute_sql(sql)

    def create_user_signal(self):
        sql = """ CREATE TABLE IF NOT EXISTS user_signal(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        signal_address TEXT NOT NULL,
        is_sent BOOLEAN NOT NULL)
        """
        self.execute_sql(sql)

    #db connection
    def create_db_connection(self):
        con = sqlite3.connect(self.DB_NAME,detect_types= sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

        return con

    def execute_sql(self, sql, query_params = None):
        conn = self.pool.connection()
        cursor = conn.cursor()

        if query_params is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, query_params)

        conn.commit()
        cursor.close()
        conn.close()

    def execute_sql_fetch_one(self, sql, query_params = None):
        conn = self.pool.connection()
        cursor = conn.cursor()

        if query_params is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, query_params)

        result = cursor.fetchone()

        cursor.close()
        conn.close()

        return result
    
    def execute_sql_fetch_all(self, sql, query_params = None):
        conn = self.pool.connection()
        cursor = conn.cursor()

        if query_params is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, query_params)

        result = cursor.fetchall()

        cursor.close()
        conn.close()

        return result
    
    
