#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from collections import defaultdict
import datetime
import logging
import unicodedata

# pip install python-telegram-bot
# https://github.com/python-telegram-bot/python-telegram-bot
# https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/README.md
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from startrek_fsm import TrekGame

CONTACTLIST_FN = 'startrekbot_contacts.tsv'
BOT_KEY = "PUT HERE API KEY";

def load_contacts(fn=None):
	if fn is None: fn = CONTACTLIST_FN
	contacts = set()
	try:
		for l in open(fn):
			z = l.strip()
			contacts.add(z)
	except:
		return set()
	return contacts

def save_contacts(contacts,fn=None):
	if fn is None: fn = CONTACTLIST_FN
	fh = open(fn,"w+")
	for k in contacts:
		print >>fh,str(k)
	fh.close()

def update_contacts(contacts,uu,fn=None):
	contacts.add(uu)
	save_contacts(contacts)
	return contacts

def bot_error(bot, update, error):
    logging.warn('BOT\tUpdate "%s" caused error "%s"' % (update, error))

def send_msg(bot,contact,msg,mono=True):
	if mono:
		msg = u"```\n"+msg+u"\n```"
	bot.sendMessage(contact, text=msg, parse_mode="Markdown", disable_web_page_preview=True)

def help_handler(bot, update):
	uu = update.message.chat_id
	logging.info("USER\tServe user '%s' with command '/help'" % (str(uu),) )
	send_msg(bot,uu,"As a captain of the Enterprise, you should to fly through the galaxy and hunt down a number of Klingon ships. Each game starts with a different number of Klingons, friendly starbases and stars, spread throughout the galaxy.",False)
	send_msg(bot,uu,"The galaxy map is arranged as an 8 by 8 grid of quadrants. Each quadrant is further divided into an 8 by 8 grid of sectors. The Enterprise's local surroundings can seen on a text-based map of the current quadrant's sectors.",False)
	send_msg(bot,uu,"Stars were represented with a `*`, Klingon ships as a `>!<`, star bases as an `<O>`, and the Enterprise itself with an `-O-`.",False)
	send_msg(bot,uu,"The user can also use the long-range scan, LRS, to print out an abbreviated map of the quadrants lying directly around the Enterprise, listing the number of stars, Klingons and starbases in each quadrant.",False)
	send_msg(bot,uu,"Klingon ships can be attacked with either phasers or photon torpedos. Phasers do not have to be aimed, but their power falls off with distance, requiring the player to estimate how much power to put into each shot. Also phasers can affect the Enterprise's shields.",False)
	send_msg(bot,uu,"Torpedoes do not suffer this drop in power and will destroy a Klingon ship with a single hit, but they have to be aimed using polar coordinates, so misses are possible. Movement, combat and shields all drain the energy supply of the Enterprise, which can be topped up again by flying to a starbase. In case the Enterprise is low on energy or torpedoes, the player could warp to a starbase to refuel and repair.",False)
	send_msg(bot,uu,"The game ends when the Enterprise is destroyed or all Klingons are destroyed.\n\nUse these digits to specify the direction for the movement/combat:\n\n",False)
	send_msg(bot,uu,"    7 8 9\n     \\|/  \n    4-o-6\n     /|\\  \n    1 2 3\n\n")
	send_msg(bot,uu,"Press /start to start a new game. Use /help to read this info again and /about to get a short story about original game.",False)

def about_handler(bot, update):
	uu = update.message.chat_id
	logging.info("USER\tServe user '%s' with command '/about'" % (str(uu),) )
	send_msg(bot,uu,"   _____________   ___ \n  / __/_  __/ _ | / _ \\\n _\ \  / / / __ |/ , _/\n/___/ /_/ /_/ |_/_/|_| \n       _________  ______ __\n      /_  __/ _ \/ __/ //_/\n       / / / , _/ _// ,<   \n      /_/ /_/|_/___/_/|_|  \n")
	send_msg(bot,uu,"Star Trek is a text-based computer game that puts the player in command of the USS Enterprise on a mission to hunt down and destroy an invading fleet of Klingon warships.\n",False)
	send_msg(bot,uu,"Trek developed out of a brainstorming session between Mike Mayfield and several high school friends in 1971. The original Star Trek television show had only recently ended its run and was still extremely popular. ",False)
	send_msg(bot,uu,"Mayfield and his \"geek friends\" wrote down a number of ideas for a game, and during the summer holidays he then started incorporating as many of them as he could on an SDS Sigma 7, using an illicitly borrowed account at the University of California, Irvine.\n\nThe original Sigma 7 version, and its descendants, were ported or copied to a wide variety of platforms. Several years later a lot of microcomputer versions appeared and were widely available and modified.\n\nStar Trek was reviewed in The Dragon magazine #38. Reviewer Mark Herro described the game in 1980 as \"one of the most popular (if not the most popular) computer games around.\"",False)
	send_msg(bot,uu,"This telegram version was built by [altsoph](http://altsoph.com) based on [a Python port](https://github.com/psychotimmy/trek-game) of the original game by [Tim Holyoake](http://www.tenpencepiece.net/).\nThanks to Evgeny Vasin and Ivan Yamshchikov for beta-testing.",False)
	send_msg(bot,uu,"_____________       _\n\\_(=====/_=_/___.--'-`--.__\n        \\ \\   `,--,-.__.---'\n      .--`\\\\--'../\n      '---._____.|]\n\n  ...dif-tor heh smusma...\n")
	send_msg(bot,uu,"\nPress /start to start a new game. Use /help to read about controls and /about to get this info again.",False)

def start_handler(bot, update):
	[fsm_objects,contacts] = bot.alt_data
	uu = update.message.chat_id
	if uu not in contacts: contacts = update_contacts(contacts,uu)
	logging.info("USER\tInit user '%s'" % (str(uu),) )
	fsm_objects[uu] = TrekGame()
	fsm_objects[uu].step()
	send_msg(bot,uu,fsm_objects[uu].result())
	bot.alt_data = [fsm_objects,contacts]

def command_handler(bot, update):
	[fsm_objects,contacts] = bot.alt_data
	uu = update.message.chat_id
	m = update.message.text
	if uu not in contacts: contacts = update_contacts(contacts,uu)
	if uu not in fsm_objects:
		start_handler(bot,update)
		return

	prev_state = fsm_objects[uu].get_state()
	fsm_objects[uu].step(m)
	if fsm_objects[uu].get_state() == 'main_cmd':
		fsm_objects[uu].step(clear = False)
	send_msg(bot,uu,fsm_objects[uu].result())
	escm = "".join(ch if unicodedata.category(ch)[0]!="C" else " " for ch in m[:min(len(m),128)])
	logging.info("USER\tUser`s '%s' command received: '%s'. State changed from '%s' to '%s'" % (str(uu),escm,prev_state,fsm_objects[uu].get_state()) )
	bot.alt_data = [fsm_objects,contacts]

def main():
	fsm_objects = dict()
	contacts = load_contacts()

	logging.basicConfig(filename='startrekbot_%s.log' % (datetime.datetime.now().strftime("%Y%m%d%H%M%S"),), 
						format='%(asctime)s\t%(levelname)s\t%(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)
	logging.info('STATUS\tStarted') 
	logging.info('STATUS\t%d contacts found' %(len(contacts,)))

	# Create the EventHandler and pass it your bot's token.
	updater = Updater(BOT_KEY)
	updater.bot.alt_data = [fsm_objects,contacts]
	# updater.bot.alt_data = [fsm_states,fsm_objects,contacts]
	dp = updater.dispatcher

	# on different commands - answer in Telegram
	dp.add_handler(CommandHandler("start", start_handler))
	dp.add_handler(CommandHandler("help",  help_handler))
	dp.add_handler(CommandHandler("about", about_handler))
	# on noncommand i.e message - echo the message on Telegram
	dp.add_handler(MessageHandler([Filters.text], command_handler))
	# log all errors
	dp.add_error_handler(bot_error)
	# Start the Bot
	updater.start_polling(poll_interval=0.2)
	# Run the bot until the you presses Ctrl-C or the process receives SIGINT,
	# SIGTERM or SIGABRT. This should be used most of the time, since
	# start_polling() is non-blocking and will stop the bot gracefully.
	updater.idle()

if __name__ == '__main__':
	main()
