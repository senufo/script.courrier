# -*- coding: utf-8 -*-
"""
kodi script for read mail on IMAP/POP server
"""
#Script pour consulter ses mails
#Senufo, 2011 (c)
#
# Date : mercredi 30 novembre 2011, 19:14:13 (UTC+0100)
# $Author: Senufo $

#Modules xbmc
import xbmc, xbmcgui
import xbmcaddon
import os, re
from BeautifulSoup import *

#import BeautifulSoup
from re import compile as Pattern

__author__     = "Senufo"
__scriptid__   = "script.program.courrier"
__scriptname__ = "Courrier"

__addon__      = xbmcaddon.Addon(__scriptid__)

__cwd__        = __addon__.getAddonInfo('path')
__version__    = __addon__.getAddonInfo('version')
__language__   = __addon__.getLocalizedString

__profile__    = xbmc.translatePath( __addon__.getAddonInfo('profile') )
__resource__   = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) )

__skindir__    = xbmc.getSkinDir()

sys.path.append (__resource__)

import sys
import time
from time import gmtime, strftime
import poplib, imaplib
import string


import email
from email.Parser import Parser as EmailParser
from email.utils import parseaddr
from email.Header import decode_header
#import mimetypes

DEBUG_LOG = __addon__.getSetting( 'debug' )
if 'true' in DEBUG_LOG : DEBUG_LOG = True
else: DEBUG_LOG = False

#Function Debug
def debug(msg):
    """
    print message if DEBUG_LOG == True
    """
    if DEBUG_LOG == True: print " [%s] : %s " % (__scriptid__, msg)

debug(('SKIN DIR = %s, profile = %s, ressources = %s ' % (__skindir__,__profile__,__resource__) ))

#Script html2text.py in resources/lib
from html2text import *
#Use configuration file if exist notifier service
#try:
#    Addon = xbmcaddon.Addon('service.notifier')
    #Verify file configuration exist
    #if not load file config courrier
#    if not (Addon.getSetting( 'name1' )):
#        Addon = xbmcaddon.Addon(__addon__)
#except:
Addon = xbmcaddon.Addon(__scriptid__)
#Load msg translate script.mail
Addon_traduc = xbmcaddon.Addon(__scriptid__)
#get actioncodes from keymap.xml/ keys.h
ACTION_PREVIOUS_MENU = 10
ACTION_SELECT_ITEM = 7
ACTION_MOVE_LEFT       =   1
ACTION_MOVE_RIGHT      =   2
ACTION_MOVE_UP         =   3
ACTION_MOVE_DOWN       =   4
ACTION_PAGE_UP         =   5
ACTION_PAGE_DOWN       =   6
ACTION_NUMBER1         =   59
ACTION_NUMBER2         =   60
ACTION_VOLUME_UP       =   88
ACTION_VOLUME_DOWN     =   89
ACTION_REWIND          =   78
ACTION_FASTFORWARD     =   77

#Buttons ID in script-courrier-main.xml
STATUS_LABEL = 100
NX_MAIL      = 101
MSG_BODY     = 102
EMAIL_LIST   = 120
SCROLL_BAR   = 121
MSG_BODY     = 102
SERVER1      = 1001
SERVER2      = 1002
SERVER3      = 1003
QUIT         = 1004
FILE_ATT     = 1005
MAX_SIZE_MSG = int(Addon.getSetting( 'max_msg_size' ))
SEARCH_PARAM = Addon.getSetting( 'search_param' )

class MailWindow(xbmcgui.WindowXML):
    """
    Display main window for read mail
    """
    def __init__(self, *args, **kwargs):

        #variable for position in the msg
        self.position = 0

    def onInit( self ):
        """
        Initialize parameters
        """

        self.getControl( EMAIL_LIST ).reset()
        for i in [1, 2, 3]:
            id = 'name' + str(i)
            NOM =  Addon.getSetting( id )
            Button_Name = 1000 + i
            if NOM:
                self.getControl( Button_Name ).setLabel( NOM )
            else:
                self.getControl( Button_Name ).setEnabled(False)
        self.checkEmail(Addon.getSetting( 'name1' ))



#Verify mails and display subjects and expeditors
#Alias is name server POP or IMAP
    def checkEmail(self, alias):
        """
        Check mail on POP or IMAP server
        """
        #debug( 'ALIAS = %s ' % alias )
        self.getControl( STATUS_LABEL ).setLabel( '%s ...' % alias )

        #Empty the list of subject messages
        #self.listControl.reset()
        self.USER = ''
        self.NOM = ''
        self.SERVER = ''
        self.PASSWORD = ''
        self.PORT = ''
        self.SSL = ''
        self.TYPE = ''
        self.FOLDER = ''
        #Get list of the 3 servers in settings.xml
        for i in [1, 2, 3]:
            NOM = Addon.getSetting( 'name%i' % i )
            USER = Addon.getSetting( 'user%i' % i )
            NOM =  Addon.getSetting( 'name%i' % i )
            SERVER = Addon.getSetting( 'server%i' % i )
            PASSWORD =  Addon.getSetting( 'pass%i' % i )
            PORT =  Addon.getSetting( 'port%i' % i )
            SSL = Addon.getSetting( 'ssl%i' % i ) == "true"
            TYPE = Addon.getSetting( 'type%i' % i )
            FOLDER = Addon.getSetting( 'folder%i' % i )
            #Search selected server
            if (alias == NOM):
                self.NOM = NOM
                self.SERVER = SERVER
                self.USER = USER
                self.PORT = PORT
                self.PASSWORD = PASSWORD
                self.TYPE = TYPE
                self.SSL = SSL
                self.FOLDER = FOLDER
                try:
                    #Select server type
                    if '0' in self.TYPE:  #POP3
                        self.getPopMails()
                    if '1' in self.TYPE: #IMAP
                        self.getImapMails()
                except Exception, e:
                    debug( str( e ) )
                    dialog = xbmcgui.DialogProgress()
                    dialog.create(Addon_traduc.getLocalizedString(id=614),
                          Addon_traduc.getLocalizedString(id=620) % self.SERVER)
                    time.sleep(5)
                    dialog.close()

    def getPopMails(self):
        """
        Get mail on POP server with poplib
        """
        dialog = xbmcgui.DialogProgress()
        dialog.create(Addon_traduc.getLocalizedString(id=614),
                      Addon_traduc.getLocalizedString(id=610))#Inbox, Logging in
        if self.SSL:
            mail = poplib.POP3_SSL(str(self.SERVER), int(self.PORT))
        else:  #'POP3'
            mail = poplib.POP3(str(self.SERVER), int(self.PORT))
        mail.user(str(self.USER))
        mail.pass_(str(self.PASSWORD))
        numEmails = mail.stat()[0]

        debug( "You have", numEmails, "emails" )
        #Display the number of msg
        self.getControl( NX_MAIL ).setLabel( '%d msg(s)' % numEmails )
        dialog.close()
        if numEmails == 0:
            dialogOK = xbmcgui.Dialog()
            dialogOK.ok("%s" % self.NOM,
                        Addon_traduc.getLocalizedString(id=612)) #no mail
            self.getControl( EMAIL_LIST ).reset()
        else:             #Inbox                           #You have
                                #emails
            dialog.create(Addon_traduc.getLocalizedString(id=613),
                Addon_traduc.getLocalizedString(id=615) + str(numEmails) + Addon_traduc.getLocalizedString(id=616))
            #Retrieve list of mails
            resp, items, octets = mail.list()
            debug( "resp %s, %s " % (resp, items))
            dialog.close()
            #Get all messages for display
            progressDialog = xbmcgui.DialogProgress()
                              #Message(s)                       #Get mail
            progressDialog.create(Addon_traduc.getLocalizedString(id=617),
                                  Addon_traduc.getLocalizedString(id=618))
            i = 0
            #Reset ListBox msg
            self.getControl( EMAIL_LIST ).reset()
            self.emails = []
            for item in items:
                i = i + 1
                id, size = string.split(item)
                up = (i*100)/numEmails    #Get mail             Please wait
                progressDialog.update(up,
                                      Addon_traduc.getLocalizedString(id=618),
                                      Addon_traduc.getLocalizedString(id=619))

                #If the maximum size is exceeded doxnload only 50 lines
                if (MAX_SIZE_MSG == 0) or (size < MAX_SIZE_MSG):
                    resp, text, octets = mail.retr(id)
                else:
                    resp, text, octets = mail.top(id, 300)
                att_file = ':'
                text = string.join(text, "\n")
                self.processMails(text, att_file)
            progressDialog.close()
            #Display the first mail of the list
            self.getControl( EMAIL_LIST ).selectItem(0)

    def processMails(self, text, att_file):
        """
        Parse mail for display in XBMC
        """
        myemail = email.message_from_string(text)
        p = EmailParser()
        msgobj = p.parsestr(text)
        if msgobj['Subject'] is not None:
            decodefrag = decode_header(msgobj['Subject'])
            subj_fragments = []
            for s , enc in decodefrag:
                if enc:
                    s = unicode(s , enc).encode('utf8','replace')
                subj_fragments.append(s)
            subject = ''.join(subj_fragments)
        else:
            subject = None
        if msgobj['Date'] is not None:
            date = msgobj['Date']
        else:
            date = '--'
        Sujet = subject
        realname = parseaddr(msgobj.get('From'))[1]

        body = None
        html = None
	#Repertory for attached file(s)
	detach_dir = '/tmp/'
        counter = -1 
	attached_images = []
        for part in msgobj.walk():
            content_disposition = part.get("Content-Disposition", None)
            prog = re.compile('attachment')
            #Retrieve attached files names 
            if prog.search(str(content_disposition)):
                file_att = str(content_disposition)
		#########################################################################
                filename = part.get_filename()
		counter += 1
        	att_path = os.path.join(detach_dir, filename)
                pattern = re.compile('png|jpg')
		if pattern.search(str(att_path)):
                    debug(("File : %s" % (att_path)))
                    fp = open(att_path, 'wb')
	            fp.write(part.get_payload(decode=True))
                    fp.close()
                    attached_images.append(att_path)
		    debug(("ATTACHED :%s" % attached_images))
		##########################################################################
		#debug(("ATT : %s" % (file_att)))
		#debug(part)
                pattern = Pattern(r"\"(.+)\"")
                att_file +=  str(pattern.findall(file_att))
            if part.get_content_type() == "text/plain":
		if body is None:
                    body = ""
                try :
                    #If no defined charset
                    if (part.get_content_charset() is None):
                        body +=  part.get_payload(decode=True)
                    else:
                        body += unicode(
                           part.get_payload(decode=True),
                           part.get_content_charset(),
                           'replace'
                           ).encode('utf8','replace')
                except Exception, e:
                    body += "Erreur unicode"
                    debug( "BODY = %s " % body)
            elif part.get_content_type() == "text/html":
                if html is None:
                    html = ""
                try :
                    unicode_coded_entities_html = unicode(BeautifulStoneSoup(html,
                            convertEntities=BeautifulStoneSoup.HTML_ENTITIES))

                    html += unicode_coded_entities_html
                    html = html2text(html)
                except Exception, e:
                    html += "Erreur unicode html"
                    #debug( "HTML = %s " % html )
            realname = parseaddr(msgobj.get('From'))[1]
        Sujet = subject
        description = ' '
        if (body):
            description = str(body)
        else:
            try:
                html = html.encode('ascii','replace')
                description = str(html)
            except Exception, e:
                debug( str(e) )
        #Nb of lines msg for scroll text
        self.nb_lignes = description.count("\n")

        listitem = xbmcgui.ListItem( label2=realname, label=Sujet)
        listitem.setProperty( "realname", realname )
        date += att_file
	debug(("attached files : %s" % att_file))
        listitem.setProperty( "date", date )
        listitem.setProperty( "message", description )
	#Verify if att_path exist
        if 'attached_images' in locals():
           counter = 0
           for name_image in attached_images:
              #debug(('attached %s ' % attached_images))
	      counter += 1 
              debug(('image%s, IMAGE : %s ' % (counter,name_image)))
              listitem.setProperty( ('image%s' % counter), name_image )
        self.getControl( EMAIL_LIST ).addItem( listitem )

    def getImapMails(self):
        """
        Get mail form IMAP server
        """
        dialog = xbmcgui.DialogProgress()
        dialog.create(Addon_traduc.getLocalizedString(id=614),
                      Addon_traduc.getLocalizedString(id=610))#Inbox,Logging in
        #Reset ListBox msg
        #self.getControl( EMAIL_LIST ).reset()
        self.emails = []
        try:
            if self.SSL:
                imap = imaplib.IMAP4_SSL(str(self.SERVER), int(self.PORT))
            else:
                imap = imaplib.IMAP4(str(self.SERVER), int(self.PORT))
            att_file = ':'
            imap.login(self.USER, self.PASSWORD)
            imap.select(self.FOLDER)
	    #Search new mail, Filter examples : UNSEEN, ALL, ....
            #numEmails = len(imap.search(None, 'UnSeen')[1][0].split())
            #numEmails = len(imap.search(None, 'ALL')[1][0].split())
            numEmails = len(imap.search(None, SEARCH_PARAM )[1][0].split())
            debug( ("You have %d emails IMAP" % numEmails) )
            #Display number of msg
            self.getControl( NX_MAIL ).setLabel( '%d msg(s)' % numEmails )
            dialog.close()
            if numEmails == 0:
                dialogOK = xbmcgui.Dialog()
                dialogOK.ok("%s" % self.NOM,
                            Addon_traduc.getLocalizedString(id=612)) #no mail
                self.getControl( EMAIL_LIST ).reset()
            else:
                progressDialog2 = xbmcgui.DialogProgress()
                                  #Message(s)                       #Get mail
                progressDialog2.create(Addon_traduc.getLocalizedString(id=617),
                                       Addon_traduc.getLocalizedString(id=618))
                i = 0
        ##Retrieve list of mails
                typ, data = imap.search('UTF-8', SEARCH_PARAM)
                #typ, data = imap.search(None, 'UnSeen')
                #typ, data = imap.search(None, 'ALL')
                for num in data[0].split():
                    i = i + 1
                    typ, data = imap.fetch(num, '(RFC822)')
                    up = (i*100)/numEmails    #Get mail              Please wait
                    progressDialog2.update(up,
                                       Addon_traduc.getLocalizedString(id=618),
                                       Addon_traduc.getLocalizedString(id=619))
                    #debug( "UP = %d " % up )
                    text = data[0][1].strip()
                    self.processMails(text, att_file)
                progressDialog2.close()
            #Display first mail of the list
            self.getControl( EMAIL_LIST ).selectItem(0)
            imap.logout
        except Exception, e:
            debug( 'IMAP exception' )
            debug( str( e ) )
            debug( 'IMAP exception' )


    def onAction(self, action):
        #debug( "ID Action %d" % action.getId() )
        #debug( "Code Action %d" % action.getButtonCode() )
        if action == ACTION_PREVIOUS_MENU:
            self.close()
        if action == ACTION_MOVE_UP:
            controlId = action.getId()
        if action == ACTION_MOVE_DOWN:
            controlId = action.getButtonCode()
        if action == ACTION_FASTFORWARD: #PageUp
            if (self.position > 0):
                self.position = self.position - 1
            self.getControl( MSG_BODY ).scroll(self.position)
            debug( "Position F = %d " % self.position )
        if (action == ACTION_REWIND): #PageUp
            if (self.position <= self.nb_lignes):
                self.position = self.position + 1
            self.getControl( MSG_BODY ).scroll(self.position)
            debug( "Position R = %d " % self.position )

    def onClick( self, controlId ):
        #debug( "onClick controId = %d " % controlId )
        if (controlId in [SERVER1, SERVER2, SERVER3]):
            label = self.getControl( controlId ).getLabel()
            self.checkEmail(label)
        elif (controlId == QUIT):
            self.close()

mydisplay = MailWindow( "script-courrier-main.xml" , __cwd__, "Default")
mydisplay .doModal()
del mydisplay
