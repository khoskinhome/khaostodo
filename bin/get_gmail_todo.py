#!/usr/bin/python

import json
import sys
import imaplib
import getpass
import email
import datetime
import re
import os


"""
 This script is for getting email "todo" notes , sent usually by yourself, to a gmail account that you have setup for the purpose. This gmail account needs to allow IMAP ( by default this isn't enable ). 

You also need to have Google's extra security switched off. ( I haven't worked out how to do Google's new security protocol yet ). To switch of google extra security see https://support.google.com/accounts/answer/6010255?hl=en

You probably wouldn't want to use your main email account, primarily because the password to the account is stored in a (hopefully) protected config file ( and you can't currently use the new security methods with this script, as mentioned above )

 So this script gets TODO emails that have the "Subject" prefixed with something like "TODOHOME" or "TODOWORK". ( Only one prefix config currently allowed, and for the way I work I don't see any benefit to having more )
These emails are then appended to a file somewhere, this file you edit in a text editor.
I process my todo file lists in text editor.

This script saves me from having to have an email client open. I just run it from a launcher shortcut on my gnome desktop ( using the "Application in Terminal" type ) and get the emails I've sent myself dumped in a text file. Magic !

So when I'm at work I can send an email with the Subject prefix of TODOHOME. My home machine is configured just to look for these . At work it is vice-versa.

It doesn't cope with multipart emails, but then I don't see the point of that. I can do all I want in non multipart emails. I can't currently thing why would I need attachments for this task.

Most of this code was blagged from http://www.voidynullness.net/blog/2013/07/25/gmail-email-with-python-via-imap/ . Thanks ! 

Some of it was by me "Kaptain Khaos"

There is a perl script that will dump out an example config ( yeah I'll write this in python too )

You really need to make the file permission to this directory very strict
 i.e chmod 700 /home/yourhome/.khaostodo/

If you use the bin/generate_json_conf.pl to generate a template conf,
 then that does change the directory permission to be restrictive.

"""

confdir  = os.environ['HOME'] + '/.khaostodo/'

with open(confdir + "gmail-todo.json", 'r' ) as data_file:
  conf_json = json.load(data_file)

todo_file_to_append_to= conf_json['todo_file_to_append_to']
gmail_email_address   = conf_json['gmail_email_address']
gmail_password        = conf_json['gmail_password']
subject_prefix        = conf_json['subject_prefix']

# TODO the conf is going to need a list of "approved sender" email address. So that you can avoid having your todo list being spammed.

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

        if re.match( r'%s' % subject_prefix  , msg['Subject'] ) :
            print "Appending to %s " % todo_file_to_append_to
            prtdate = msg['Date']
            date_tuple = email.utils.parsedate_tz(msg['Date'])
            if date_tuple:
                local_date = datetime.datetime.fromtimestamp(
                      email.utils.mktime_tz(date_tuple))
                prtdate = local_date.strftime("%a, %d %b %Y %H:%M:%S")

            with open(todo_file_to_append_to, "a") as myfile:
              myfile.write(
                    "\n####################\n"
                    + prtdate + "\n"
                    + msg['Subject']
                    + msg.get_payload()
                )
            M.store(num, '+FLAGS', '\\Deleted')
        else :
            print "NOT appending to %s " % todo_file_to_append_to
    M.expunge()

M = imaplib.IMAP4_SSL('imap.gmail.com')

try:
    M.login(gmail_email_address, gmail_password)
except imaplib.IMAP4.error:
    print "LOGIN FAILED!!! "
    sys.exit()

rv, data = M.select("INBOX")
if rv == 'OK':
    print "Processing mailbox...\n"
    process_mailbox(M)
    M.close()
M.logout()

raw_input ( "Press return/enter key to finish" )
