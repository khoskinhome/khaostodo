#!/usr/bin/python

import json
import sys
import imaplib
import getpass
import email
import datetime
import re
import os
import getpass


"""
The Reason for this script
##########################
I like doing my todo notes in a text editor.

So this script is for getting email "TODO" notes, usually sent by yourself, possibly to a gmail account that you have setup for the purpose and appending them to a file defined in the JSON config.

These TODO emails have the "Subject" prefixed with something like "TODOHOME" or "TODOWORK". This prefix is defined in the JSON config.

So this script saves me from having an email client open, and copy-and-pasting. I just run it from a launcher shortcut on my gnome desktop ( using the "Application in Terminal" type ) and get the emails I've sent myself dumped in a text file, ready for my text editor. ( you really need the files being appended to have been saved before you run this script, otherwise you will get in a bit of a mess when the editor says something else has editted your unsaved file )

So when I'm at work I can send an email with the Subject prefix of TODOHOME. My home machine is configured just to look for these . At work it is vice-versa.


Google Settings
###############
This gmail account needs to allow IMAP ( by default this isn't enable ). See gmail help on the web.
 
You also need to have Google's extra security switched off. ( I haven't worked out how to do Google's new security protocol yet ). To switch of google extra security see https://support.google.com/accounts/answer/6010255?hl=en


Password
########
You can if you wish get this script to prompt for the password by either not defining it in the json config or having it defined as an empty-string.

If you do have the password in your config, then for your security you might want to create a gmail account just for your todo notes. Also you then really need to make the file permission to this directory very strict
 i.e chmod 700 /home/yourhome/.khaostodo/

If you use the bin/generate_json_conf.pl to generate a template conf,
 then that does change the config directory permissions to be restrictive.


Other things.
#############
If a message is multipart this script attempts to extra the text/plain part as the message body.

There is a perl script that will dump out an example config ( yeah I'll write this in python too )

I am sure you could adapt this script for other mail providers. Gmail works for me :)

A lot of the code here was copied (blagged!) from http://www.voidynullness.net/blog/2013/07/25/gmail-email-with-python-via-imap/ . Thanks !

Some of it was by me "Kaptain Khaos"

"""

conf={}

def press_return_exit():
    if ( conf['prompt_finish_return'] == 'y' ) :
        raw_input ( "Press return/enter key to finish" )
    sys.exit()

def get_config() :
    global conf

    # getting the config.
    confdir = os.environ['HOME'] + '/.khaostodo/'
    with open(confdir + "gmail-todo.json", 'r' ) as data_file:
      conf = json.load(data_file)

    conf['prompt_finish_return'] = conf.get('prompt_finish_return','Y').lower()

    conf['gmail_password']       = conf.get('gmail_password','')
    if ( not conf['gmail_password'] ) :
        conf['gmail_password'] = getpass.getpass("Input the gmail password for %s : " % conf['gmail_email_address'] )

    try :
        conf['gmail_email_address']    = conf['gmail_email_address']
    except KeyError as e:
        print "config file missing " , e
        press_return_exit()

    # the dispatch config.
    for pref in conf['dispatch'] :
        if (conf['dispatch'][pref]['delete'] == 'ask' \
            or conf['dispatch'][pref]['delete'] == '' ) :
                conf['dispatch'][pref]['delete'] \
                    = raw_input ( "For prefix %s Do you want to delete TODOs emails (in the mailbox) that get appended to the file ( yes/no OR y/n ) ? " % pref )

        if conf['dispatch'][pref]['delete'] == 'y' :
            conf['dispatch'][pref]['delete'] ='yes'

        if conf['dispatch'][pref]['delete'] == 'n' :
            conf['dispatch'][pref]['delete'] ='no'

        if ( conf['dispatch'][pref]['delete'] != 'yes' \
            and conf['dispatch'][pref]['delete'] != 'no' ) :
                print "For prefix %s , invalid entry for delete_messages %s" % ( pref , conf['dispatch'][pref]['delete'] )
                press_return_exit()

# TODO the conf is going to need a list of "approved sender" email address. So that you can avoid having your todo list being spammed.

def extract_text_plain(msg) :
    if ( msg.is_multipart()):
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                return part.get_payload()
    else :
        return msg.get_payload()

def extract_date(msg) :
    date_tuple = email.utils.parsedate_tz(msg['Date'])
    if date_tuple:
        local_date = datetime.datetime.fromtimestamp(
              email.utils.mktime_tz(date_tuple))
        return local_date.strftime("%a, %d %b %Y %H:%M:%S")
    else :
        return msg['Date']


def process_mailbox(M):
    rv, data = M.search(None, "ALL")
    if rv != 'OK':
        print "No messages found!"
        return

    for num in data[0].split():
        rv, data = M.fetch(num, '(RFC822)')
        if rv != 'OK':
            print "ERROR getting message", num
            return

        msg = email.message_from_string(data[0][1])
        print "#########################"
        print 'Message %s: %s' % (num, msg['Subject'])

        # TODO make sure the todo is only coming from approved sender emails . i.e. mine.
        # I don't want people to be able to spam my todo gmail account.

        for pref in conf['dispatch'] :
            if re.match( r'\s*%s' % pref , msg['Subject'] , re.IGNORECASE ) :
                print "Appending to %s " % conf['dispatch'][pref]['fileto']

                with open(conf['dispatch'][pref]['fileto'], "a") as myfile:
                  myfile.write(
                        "\n####################"
                        + "\n" + extract_date(msg)
                        + "\n" + msg['Subject']
                        + "\n" + extract_text_plain(msg)
                    )
                if conf['dispatch'][pref]['delete'].lower() == 'y' or conf['dispatch'][pref]['delete'].lower() == 'yes':
                    M.store(num, '+FLAGS', '\\Deleted')
            #else :
            #    print "NOT appending to %s " % conf['dispatch'][pref]['fileto']
    M.expunge()



def main () :
    M = imaplib.IMAP4_SSL('imap.gmail.com')
    try:
        M.login(conf['gmail_email_address'], conf['gmail_password'])
    except imaplib.IMAP4.error:
        print "LOGIN FAILED!!! %s " % conf['gmail_email_address']
        press_return_exit()

    rv, data = M.select("INBOX")
    if rv == 'OK':
        print "Processing mailbox...\n"
        process_mailbox(M)
        M.close()
    M.logout()

    press_return_exit()

#########################################
# run it :

get_config()
main()

