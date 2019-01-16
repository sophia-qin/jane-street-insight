#!/usr/bin/python

# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py; sleep 1; done

from __future__ import print_function

import sys
import socket
import json
import time

# ~~~~~============== CONFIGURATION  ==============~~~~~
# replace REPLACEME with your team name!
team_name="SQUIRTLE"
# This variable dictates whether or not the bot is connecting to the prod
# or test exchange. Be careful with this switch!
test_mode = False

# This setting changes which test exchange is connected to.
# 0 is prod-like
# 1 is slower
# 2 is empty
test_exchange_index=0
prod_exchange_hostname="production"

port=25000 + (test_exchange_index if test_mode else 0)
exchange_hostname = "test-exch-" + team_name if test_mode else prod_exchange_hostname

# ~~~~~============== NETWORKING CODE ==============~~~~~
def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((exchange_hostname, port))
    return s.makefile('rw', 1)

def write_to_exchange(exchange, obj):
    json.dump(obj, exchange)
    exchange.write("\n")

def read_from_exchange(exchange):
    return json.loads(exchange.readline())


# ~~~~~============== MAIN LOOP ==============~~~~~

num_orders = 0
continue_bot = True
fair_value = 1
current_sell_num = 0
current_buy_num = 0
order_id = 0
exchange = None
vale_current_price = 0
valbz_current_buy_price = 0
valbz_current_sell_price = 0

#button-indication-ongoing
def add_to_exchange(price, size, direction, symbol, exchange):
    global order_id
    generate_order_id()
    #print({"type": "add", order_id: order_id, "symbol": symbol, "dir": direction, "price": price, "size": size})
    write_to_exchange(exchange, {"type": "add", "order_id": order_id, "symbol": symbol, "dir": direction, "price": price, "size": size}) 

def main():
    global exchange
    global order_id
    exchange = connect()
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    hello_from_exchange = read_from_exchange(exchange)
    # A common mistake people make is to call write_to_exchange() > 1
    # time for every read_from_exchange() response.
    # Since many write messages generate marketdata, this will cause an
    # exponential explosion in pending messages. Please, don't do that!
    print("The exchange replied:", hello_from_exchange, file=sys.stderr)

    while continue_bot:
        hello_from_exchange = read_from_exchange(exchange)
        print("The exchange replied:", hello_from_exchange, file=sys.stderr)
        read_message(hello_from_exchange)


def receive_fill_buy_vale(message):
    type = message["type"]
    direction = message["dir"]
    symbol = message["symbol"]
    if(type == "fill" and direction == "BUY" and symbol == "VALE"):
        return true
    return false

def receive_fill_sell_vale(message):
    type = message["type"]
    direction = message["dir"]
    if(type == "fill" and direction == "SELL" and symbol == "VALE"):
        return true
    return false

def read_message(message):
    type = message["type"] #exctracting the type of the message
    if(type == "book"):
        print("hi")
        parse_book(message)          

def parse_book(message):
    symbol = message["symbol"]
    if(symbol == "BOND"):
        bond(message)
    #if(symbol == "VALBZ"):
        #valbz(message)
    #if(symbol == "VALE"):
        #vale(message)
 
def valbz(message): 
    global valbz_current_buy_price, valbz_current_sell_price
    buy_list = message["buy"]
    sell_list = message["sell"]
    buy_prices_list = []
    sell_prices_list = []
    for count in range(0, len(buy_list)):
        buy_prices_list.append(buy_list[count][0])
    for count in range(0, len(sell_list)):
        sell_prices_list.append(sell_list[count][0])
    valbz_current_buy_price = find_highest_bid(buy_prices_list) #first on the buy side of the book
    valbz_current_sell_price = find_lowest_bid(sell_prices_list) #first on the sell side of the book
    if len(buy_prices_list) == 0 or len(sell_prices_list) == 0:
        return 
    buy_valbz(valbz_current_buy_price, 10)
    sell_valbz(valbz_current_sell_price, 10)

def vale_buy(message):
    global valbz_current_buy_price
    buy_list = message["buy"]
    buy_prices_list = []
    for count in range(0, len(buy_list)):
        buy_prices_list.append(buy_list[count][0])
    highest_buy_price = find_highest_bid(buy_prices_list) #first on the buy side of the book
    if len(buy_prices_list) == 0:
        print(empty)
        return 
    buy_vale(highest_buy_price + 1, 1)

def vale_sell(message):
    global valbz_current_sell_price
    sell_list = message["sell"]
    sell_prices_list = []
    for count in range(0, len(sell_list)):
        sell_prices_list.append(sell_list[count][0])
    lowest_sell_price = find_lowest_bid(sell_prices_list) #first on the sell side of the book
    if len(sell_prices_list) == 0:
        print(empty)
        return 
    sell_vale(lowest_sell_price - 1, 1)

def buy_valbz(price, size):
    global exchange
    print("buying " + str(price ) +  " " + str(size))
    add_to_exchange(price, size, "BUY", "VALBZ", exchange)

def sell_valbz(price, size):
    global exchange
    print("selling " + str(price ) +  " " + str(size))
    add_to_exchange(price, size, "SELL", "VALBZ", exchange)

def buy_vale(price, size):
    global exchange
    print("buying " + str(price ) +  " " + str(size))
    add_to_exchange(price, size, "BUY", "VALE", exchange)

def sell_vale(price, size):
    global exchange
    print("selling " + str(price ) +  " " + str(size))
    add_to_exchange(price, size, "SELL", "VALE", exchange)

def bond(message):
    buy_list = message["buy"]
    sell_list = message["sell"]
    buy_prices_list = []
    sell_prices_list = []
    for count in range(0, len(buy_list)):
        buy_prices_list.append(buy_list[count][0])
    for count in range(0, len(sell_list)):
        sell_prices_list.append(sell_list[count][0])
    highest_buy_price = find_highest_bid(buy_prices_list) #first on the buy side of the book
    lowest_sell_price = find_lowest_bid(sell_prices_list) #first on the sell side of the book
    if len(buy_prices_list) == 0 or len(sell_prices_list) == 0:
        return 
    buy_bond(highest_buy_price, 100)
    sell_bond(lowest_sell_price, 100)


def buy_bond(price, size):
    global exchange, current_buy_num
    current_buy_num += 1
    if price < 999:
        price = price + 1
    print("buying " + str(price ) +  " " + str(size))
    add_to_exchange(price, size, "BUY", "BOND", exchange)

    
def sell_bond(price, size):
    global exchange, current_sell_num
    current_sell_num -= 1
    if(price > 1001):
        price = price - 1
    print("selling " + str(price ) +  " " + str(size))
    add_to_exchange(price, size, "SELL", "BOND", exchange)  

def find_highest_bid(b_list):
    if len(b_list) == 0:
        return 
    return max(b_list)

def find_lowest_bid(s_list):
    if len(s_list) == 0:
        return
    return min(s_list)

def cancel_exchange(order_id):
    write_to_exchange(exchange, {"type": "cancel", "order_id": order_id})   

def generate_order_id():
    global order_id 
    order_id = order_id + 1

      
if __name__ == "__main__":
    main()
