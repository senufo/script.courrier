# -*- coding: utf-8 -*-

"""
kodi script for read mail on IMAP/POP server.
"""
# Modules xbmc
import xbmc
import xbmcgui
import xbmcaddon
import os, re, glob
from re import compile as Pattern
import sys
import time
import poplib, imaplib
import string

import email
from email.Parser import Parser as EmailParser
from email.utils import parseaddr
from email.Header import decode_header

# Script html2text.py in resources/lib
# from html2text import *
import html2text

author     = "Senufo"
scriptid   = "script.courrier"
scriptname = "Courrier"

Addon      = xbmcaddon.Addon(scriptid)

version    = Addon.getAddonInfo('version')
language   = Addon.getLocalizedString
scriptpath = Addon.getAddonInfo('path').decode('utf-8')

skindir    = xbmc.getSkinDir()

DEBUG_LOG = Addon.getSetting('Debug')
if 'true' in DEBUG_LOG: DEBUG_LOG = -1 #loglevel == 1 (DEBUG, shows all)
else: DEBUG_LOG = 1 #(NONE, nothing at all is logged)
xbmc.log(("[%s] : DEBUG_LOG : %s" % (scriptid,DEBUG_LOG)),DEBUG_LOG)
xbmc.log(("[%s] : skindir : %s, scriptpath : %s" % (scriptid,skindir,scriptpath)),DEBUG_LOG)# DEBUG_LOG = True

# Defaults options for html2text module
UNICODE_SNOB = Addon.getSetting('UNICODE_SNOB')                  # UNICODE_SNOB=0
ESCAPE_SNOB = Addon.getSetting('ESCAPE_SNOB')                    # ESCAPE_SNOB=0
LINKS_EACH_PARAGRAPH = Addon.getSetting('LINKS_EACH_PARAGRAPH')  # LINKS_EACH_PARAGRAPH=0
BODY_WIDTH = Addon.getSetting('BODY_WIDTH')                      # BODY_WIDTH=78
SKIP_INTERNAL_LINKS = Addon.getSetting('SKIP_INTERNAL_LINKS')    # SKIP_INTERNAL_LINKS=True
if 'true' in SKIP_INTERNAL_LINKS: SKIP_INTERNAL_LINKS = True
else: SKIP_INTERNAL_LINKS = False
INLINE_LINKS = Addon.getSetting('INLINE_LINKS')                  # INLINE_LINKS=True
if 'true' in INLINE_LINKS: INLINE_LINKS = True
else: INLINE_LINKS = False
GOOGLE_LIST_INDENT = Addon.getSetting('GOOGLE_LIST_INDENT')      # GOOGLE_LIST_INDENT=36
IGNORE_ANCHORS = Addon.getSetting('IGNORE_ANCHORS')              # IGNORE_ANCHORS=False
if 'true' in IGNORE_ANCHORS: IGNORE_ANCHORS = True
else: IGNORE_ANCHORS = False
IGNORE_IMAGES = Addon.getSetting('IGNORE_IMAGES')                # IGNORE_IMAGES=True
if 'true' in IGNORE_IMAGES: IGNORE_IMAGES = True
else: IGNORE_IMAGES = False
IGNORE_EMPHASIS = Addon.getSetting('IGNORE_EMPHASIS')            # IGNORE_EMPHASIS=False
if 'true' in IGNORE_EMPHASIS: IGNORE_EMPHASIS = True
else: IGNORE_EMPHASIS = False


# Directory for attached file(s)
# Test if directory for attached file exist
try:
    tmp = "%s/%s" % (scriptpath, 'tmp')
    xbmc.log(("[%s] : 97: Directory of attached files : %s " % (scriptid, tmp)), DEBUG_LOG)
    DATA_PATH = xbmc.translatePath(tmp)
except Exception, e:
    xbmc.log(("[%s] : 100: error : %s" % (scriptid, e)), DEBUG_LOG)
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)
# if directory exist remove all files
else:
    files = glob.glob("%s/%s" % (DATA_PATH, '*'))
    for f in files:
        try:
            os.remove(f)
            xbmc.log(("[%s] : 109: f : %s" % (scriptid, f)), DEBUG_LOG)
        except:
            xbmc.log(('[%s] : 111: no file' % scriptid), DEBUG_LOG)

#Addon = xbmcaddon.Addon(scriptid)
# get actioncodes from keymap.xml/ keys.h
ACTION_PREVIOUS_MENU = 10
ACTION_SELECT_ITEM     = 7
ACTION_MOVE_LEFT       = 1
ACTION_MOVE_RIGHT      = 2
ACTION_MOVE_UP         = 3
ACTION_MOVE_DOWN       = 4
ACTION_PAGE_UP         = 5
ACTION_PAGE_DOWN       = 6
ACTION_NUMBER1         = 59
ACTION_NUMBER2         = 60
ACTION_VOLUME_UP       = 88
ACTION_VOLUME_DOWN     = 89
ACTION_REWIND          = 78
ACTION_FASTFORWARD     = 77

# Buttons ID in script-courrier-main.xml
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
MAX_SIZE_MSG = int(Addon.getSetting('max_msg_size'))
SEARCH_PARAM = Addon.getSetting('search_param')
BACKGROUND   = Addon.getSetting('background')

# Test if BACKGROUND is defined
if not BACKGROUND:
    BACKGROUND = 'SKINDEFAULT.jpg'


class MailWindow(xbmcgui.WindowXML):
    """
    Display main window for read mail.
    """
    def __init__(self, *args, **kwargs):
        """
        init position variable.
        """
        # variable for position in the msg
        self.position = 0

    def onInit(self):
        """
        Initialize parameters.
        """
        self.getControl(EMAIL_LIST).reset()
        for i in [1, 2, 3]:
            id = 'name' + str(i)
            NOM = Addon.getSetting(id)
            Button_Name = 1000 + i
            if NOM:
                self.getControl(Button_Name).setLabel(NOM)
            else:
                self.getControl(Button_Name).setEnabled(False)
        self.checkEmail(Addon.getSetting('name1'))


# Verify mails and display subjects and expeditors
# Alias is name server POP or IMAP
    def checkEmail(self, alias):
        """
        Check mail on POP or IMAP server.
        """
        # debug( 'ALIAS = %s ' % alias )
        self.getControl(STATUS_LABEL).setLabel('%s ...' % alias)

        # Empty the list of subject messages
        # self.listControl.reset()
        self.USER = ''
        self.NOM = ''
        self.SERVER = ''
        self.PASSWORD = ''
        self.PORT = ''
        self.SSL = ''
        self.TYPE = ''
        self.FOLDER = ''
        # Get list of the 3 servers in settings.xml
        for i in [1, 2, 3]:
            NOM = Addon.getSetting('name%i' % i)
            USER = Addon.getSetting('user%i' % i)
            NOM = Addon.getSetting('name%i' % i)
            SERVER = Addon.getSetting('server%i' % i)
            PASSWORD = Addon.getSetting('pass%i' % i)
            PORT = Addon.getSetting('port%i' % i)
            SSL = Addon.getSetting('ssl%i' % i) == "true"
            TYPE = Addon.getSetting('type%i' % i)
            FOLDER = Addon.getSetting('folder%i' % i)
            # Search selected server
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
                    # Select server type
                    if '0' in self.TYPE:  # POP3
                        self.getPopMails()
                    if '1' in self.TYPE:  # IMAP
                        self.getImapMails()
                except Exception, e:
                    xbmc.log(('[%s] : Error Server Type : %s' % (scriptid, str(e))), DEBUG_LOG)
                    dialog = xbmcgui.DialogProgress()
                    dialog.create(Addon.getLocalizedString(id=614),
                                  Addon.getLocalizedString(id=620) % self.SERVER)
                    time.sleep(5)
                    dialog.close()

    def getPopMails(self):
        """
        Get mail on POP server with poplib.
        """
        dialog = xbmcgui.DialogProgress()
        dialog.create(Addon.getLocalizedString(id=614),
                      Addon.getLocalizedString(id=610))  # Inbox, Logging in
        if self.SSL:
            mail = poplib.POP3_SSL(str(self.SERVER), int(self.PORT))
        else:  # 'POP3'
            mail = poplib.POP3(str(self.SERVER), int(self.PORT))
        mail.user(str(self.USER))
        mail.pass_(str(self.PASSWORD))
	try:
		(numEmails, mailboxsize) = mail.stat()
	except Exception, e:
		xbmc.log(("[%s] : Erreur stat : %s<=" % str(e)), DEBUG_LOG)
        xbmc.log(("[%s] : 258 : You have %d emails " % numEmails), DEBUG_LOG)
        # Display the number of msg
        self.getControl(NX_MAIL).setLabel('%d msg(s)' % numEmails)
        dialog.close()
        if numEmails == 0:
            dialogOK = xbmcgui.Dialog()
            dialogOK.ok("%s" % self.NOM,
                        Addon.getLocalizedString(id=612))  # no mail
            self.getControl(EMAIL_LIST).reset()
        else:
            dialog.create(Addon.getLocalizedString(id=613),  # Inbox
                          Addon.getLocalizedString(id=615) + str(numEmails) + # You have
                          Addon.getLocalizedString(id=616)) # emails
            # Retrieve list of mails
            resp, items, octets = mail.list()
            xbmc.log(("[%s] : 272: resp %s, %s " % (resp, items)), DEBUG_LOG)
            dialog.close()
            # Get all messages for display
            progressDialog = xbmcgui.DialogProgress()
            progressDialog.create(Addon.getLocalizedString(id=617),  # Message(s)
                                  Addon.getLocalizedString(id=618))  # Get mail
            i = 0
            # Reset ListBox msg
            self.getControl(EMAIL_LIST).reset()
            self.emails = []
            for item in items:
                i = i + 1
                id, size = string.split(item)
                up = (i*100)/numEmails
                progressDialog.update(up,
                                      Addon.getLocalizedString(id=618),  # Get mail
                                      Addon.getLocalizedString(id=619))  # Please wait

                # If the maximum size is exceeded doxnload only 50 lines
                if (MAX_SIZE_MSG == 0) or (size < MAX_SIZE_MSG):
                    resp, text, octets = mail.retr(id)
                else:
                    resp, text, octets = mail.top(id, 300)
                att_file = ':'
                text = string.join(text, "\n")
                self.processMails(text, att_file)
            progressDialog.close()
            # Display the first mail of the list
            self.getControl(EMAIL_LIST).selectItem(0)

    def processMails(self, text, att_file):
        """
        Parse mail for display in XBMC.
        """
        myemail = email.message_from_string(text)
        p = EmailParser()
        msgobj = p.parsestr(text)
        if msgobj['Subject'] is not None:
            decodefrag = decode_header(msgobj['Subject'])
            subj_fragments = []
            for s, enc in decodefrag:
                # Encode subject in UTF-8
                if enc:
                    s = unicode(s, enc).encode('utf8', 'replace')
                subj_fragments.append(s)
            subject = ''.join(subj_fragments)
        else:
            subject = None
        date = Addon.getLocalizedString(32132)
        if msgobj['Date'] is not None:
            date += msgobj['Date']
        Sujet = subject
        realname = parseaddr(msgobj.get('From'))[1]
        xbmc.log(("[%s] : 325: SUJET : %s " % (scriptid, Sujet)), DEBUG_LOG)
        body = None
        html = None
        counter = -1
        attached_images = []
        for part in msgobj.walk():
            content_disposition = part.get("Content-Disposition", None)
            prog = re.compile('attachment')
            # Retrieve attached files names
            if prog.search(str(content_disposition)):
                file_att = str(content_disposition)
                filename = part.get_filename()
                counter += 1
                att_path = os.path.join(DATA_PATH, filename)
                pattern = re.compile('png|jpg|gif')
                if pattern.search(str(att_path)):
                    xbmc.log(("[%s] : 341: File : %s" % (scriptid, att_path)), DEBUG_LOG)
                    fp = open(att_path, 'wb')
                    fp.write(part.get_payload(decode=True))
                    fp.close()
                    attached_images.append(att_path)
                    xbmc.log(("[%s] : 347: ATTACHED :%s" % (scriptid, attached_images)), DEBUG_LOG)
                pattern = Pattern(r"\"(.+)\"")
                att_file += str(pattern.findall(file_att))
            # Treat text/plain msg
            if part.get_content_type() == "text/plain":
                if body is None:
                    body = ""
                    try:
                        # If no defined charset
                        if (part.get_content_charset() is None):
                            # Decode charset and encode in UTF-8
                            body += unicode(part.get_payload(decode=True)).encode('utf8', 'replace')
                        else:
                            # Decode charset and encode in UTF-8
                            body += unicode(
                                part.get_payload(decode=True),
                                part.get_content_charset(),
                                'replace'
                                ).encode('utf8', 'replace')
                    except Exception, e:
                        # body += "Erreur unicode : %s" % e
                        body += part.get_payload(decode=True)
                    #xbmc.log(("[%s] : 369: BODY = %s " % (scriptid, body)), DEBUG_LOG)
            elif part.get_content_type() == "text/html":
                # Define defaults parameters for html2text object
                h = html2text.HTML2Text()
                h.unicode_snob = int(UNICODE_SNOB)                  # UNICODE_SNOB=0
                h.escape_snob = int(ESCAPE_SNOB)                    # ESCAPE_SNOB=0
                h.links_each_paragraph = int(LINKS_EACH_PARAGRAPH)  # LINKS_EACH_PARAGRAPH=0
                h.body_width = int(BODY_WIDTH)                      # BODY_WIDTH=78
                h.skip_internal_links = bool(SKIP_INTERNAL_LINKS)   # SKIP_INTERNAL_LINKS=True
                h.inline_links = bool(INLINE_LINKS)                 # INLINE_LINKS=True
                h.google_list_indent = int(GOOGLE_LIST_INDENT)      # GOOGLE_LIST_INDENT=36
                h.ignore_links = bool(IGNORE_ANCHORS)               # IGNORE_ANCHORS=False
                h.ignore_images = bool(IGNORE_IMAGES)               # IGNORE_IMAGES=True
                h.ignore_emphasis = bool(IGNORE_EMPHASIS)           # IGNORE_EMPHASIS=False

                if html is None:
                    html = ""
                try:
                    # Test to try fix error unicode
                    # 'ascii' codec can't decode byte 0xc5 in position 32: ordinal not in range(128)
                    # debug ("CHARSET = %s " % part.get_content_charset())
                    if (part.get_content_charset() is None):
                        raw_html = part.get_payload(decode=True)
                        try:
                            html = h.handle(raw_html)
                        # Try to fix error unicode if no charset defined
                        except Exception, e:
                            xbmc.log(("[%s] : 395: Error : %s, CHARSET = %s " % (scriptid, e, part.get_content_charset())), DEBUG_LOG)
                            raw_html = raw_html.decode('utf-8', 'replace')
                            html = h.handle(raw_html)
                            xbmc.log(("[%s] : 398: RAW_HTML None OK" % scriptid), DEBUG_LOG)
                    else:
                        # Decode in UTF-8 with kown charset
                        raw_html = part.get_payload(decode=True)
                        charset_msg = part.get_content_charset()
                        xbmc.log(("[%s] : 404: CHARSET text/html = %s " % (scriptid, part.get_content_charset())), DEBUG_LOG)
                        try:
                            html = raw_html.decode(charset_msg)
                            html = h.handle(html)
                        except Exception, e:
                            xbmc.log(("[%s] : 408: HTML error : %s\n" % (scriptid, e)), DEBUG_LOG)
                            # html = htlm2text(raw_html)
                            xbmc.log(("[%s] : 410: HTML OK : %s\n" % (scriptid, html)), DEBUG_LOG)
                except Exception, e:
                    xbmc.log(("[%s] : 412: ERROR HTML = %s , %s" % (scriptid, str(e), charset_msg)), DEBUG_LOG)

            realname = parseaddr(msgobj.get('From'))[1]
        Sujet = subject
        description = '*'
        # if text/plain Body is define
        if (body):
            try:
                description += body.encode('utf-8', 'replace')
            except Exception, e:
                xbmc.log(("[%s] : 422: Error Body text/plain : %s " % (scriptid, e)), DEBUG_LOG)
                description += body.decode('utf-8', 'replace')
        # if text/html html is define
        if (html):
            try:
                # debug('Charset : %s ' % charset_msg)
                description += html.encode('utf-8', 'replace')
            except Exception, e:
                xbmc.log(("[%s] : 430: DESC error : %s" % (scriptid, str(e))), DEBUG_LOG)
        # Nb of lines msg for scroll text
        self.nb_lignes = description.count("\n")
        listitem = xbmcgui.ListItem(label2=realname, label=Sujet)
        listitem.setProperty("realname", realname)
        att_file = Addon.getLocalizedString(32133) + att_file
	try:
	    xbmc.log(("[%s] : 437: attached files : %s" % (scriptid, att_file)), DEBUG_LOG)
	except:
	    xbmc.log(("[%s] : 458: Erreur code ASCII" % scriptid), DEBUG_LOG)
        listitem.setProperty("date", date)
        listitem.setProperty("att_files", att_file)
        description = description + '*'
        listitem.setProperty("message", description)
    # Verify if att_path exist
        if 'attached_images' in locals():
            counter = 0
            for name_image in attached_images:
                xbmc.log(('[%s] : 448: attached %s ' % (scriptid, attached_images)), DEBUG_LOG)
                counter += 1
                xbmc.log(('[%s] : 450: image%s, IMAGE : %s ' % (scriptid, counter, name_image)), DEBUG_LOG)
                listitem.setProperty(('image%s' % counter), name_image)

        # Add the background
        police_sel = listitem.getProperty('font')
        xbmc.log(('[%s] : 421: font : %s ' % (scriptid, police_sel)), DEBUG_LOG)
        listitem.setProperty('background', BACKGROUND)
        listitem.setProperty('font', 'Font_channels')
        listitem.setProperty('couleur', 'yellow')

        #textColor = self.getControl(MSG_BODY).getProperty('textColor')
        #police_sel = self.getControl(MSG_BODY).getProperty('font')
        #xbmc.log(('[%s] : 426: font : %s, Color : %s ' % (scriptid, police_sel, textColor)), DEBUG_LOG)
        self.getControl(EMAIL_LIST).addItem(listitem)

    def getImapMails(self):
        """
        Get mail form IMAP server.
        """
        dialog = xbmcgui.DialogProgress()
        dialog.create(Addon.getLocalizedString(id=614),
                      Addon.getLocalizedString(id=610))  # Inbox,Logging in
        # Reset ListBox msg
        # self.getControl( EMAIL_LIST ).reset()
        self.emails = []
        try:
            if self.SSL:
                imap = imaplib.IMAP4_SSL(str(self.SERVER), int(self.PORT))
            else:
                imap = imaplib.IMAP4(str(self.SERVER), int(self.PORT))
            att_file = ':'
            imap.login(self.USER, self.PASSWORD)
            imap.select(self.FOLDER)
        # Search new mail, Filter examples : UNSEEN, ALL, ....
            # numEmails = len(imap.search(None, 'UnSeen')[1][0].split())
            # numEmails = len(imap.search(None, 'ALL')[1][0].split())
            numEmails = len(imap.search(None, SEARCH_PARAM)[1][0].split())
            xbmc.log(("[%s] : 478: You have %d emails IMAP" % (scriptid,numEmails)), DEBUG_LOG)
            # Display number of msg
            self.getControl(NX_MAIL).setLabel('%d msg(s)' % numEmails)
            dialog.close()
            if numEmails == 0:
                dialogOK = xbmcgui.Dialog()
                dialogOK.ok("%s" % self.NOM,
                            Addon.getLocalizedString(id=612))  # no mail
                self.getControl(EMAIL_LIST).reset()
            else:
                progressDialog2 = xbmcgui.DialogProgress()
                progressDialog2.create(Addon.getLocalizedString(id=617),  # Message(s)
                                       Addon.getLocalizedString(id=618))  # Get mail
                i = 0
#        ##Retrieve list of mails
                typ, data = imap.search('UTF-8', SEARCH_PARAM)
                # typ, data = imap.search(None, 'UnSeen')
                # typ, data = imap.search(None, 'ALL')
                for num in data[0].split():
                    i = i + 1
                    typ, data = imap.fetch(num, '(RFC822)')
                    up = (i*100)/numEmails
                    progressDialog2.update(up,
                                           Addon.getLocalizedString(id=618),  # Get mail
                                           Addon.getLocalizedString(id=619))  # Please wait
                    xbmc.log(("[%s] : 508: UP = %d " % (scriptid, up)), DEBUG_LOG)
                    text = data[0][1].strip()
                    self.processMails(text, att_file)
                progressDialog2.close()
            # Display first mail of the list
            self.getControl(EMAIL_LIST).selectItem(0)
            imap.logout
        except Exception, e:
            xbmc.log(('[%s] : 516: IMAP exception : %s' % (scriptid, str(e))), DEBUG_LOG)

    def onAction(self, action):
        """
        Select action after remote control.
        """
        # debug( "ID Action %d" % action.getId() )
        # debug( "Code Action %d" % action.getButtonCode() )
        if action == ACTION_PREVIOUS_MENU:
            self.close()
        if action == ACTION_MOVE_UP:
            controlId = action.getId()
        if action == ACTION_MOVE_DOWN:
            controlId = action.getButtonCode()
        if action == ACTION_FASTFORWARD:  # PageUp
            if (self.position > 0):
                self.position = self.position - 1
            self.getControl(MSG_BODY).scroll(self.position)
            xbmc.log(("[%s] : 534: Position F = %d " % (scriptid, self.position)), DEBUG_LOG)
        if (action == ACTION_REWIND):  # PageUp
            if (self.position <= self.nb_lignes):
                self.position = self.position + 1
            self.getControl(MSG_BODY).scroll(self.position)
            xbmc.log(("[%s] : 539: Position R = %d " % (scriptid, self.position)), DEBUG_LOG)

    def onClick(self, controlId):
        """Action on click button"""
        # debug( "onClick controId = %d " % controlId )
        if (controlId in [SERVER1, SERVER2, SERVER3]):
            label = self.getControl(controlId).getLabel()
            self.checkEmail(label)
        elif (controlId == QUIT):
            self.close()

#Create window for display mails
if (skindir != 'skin.aeonmq7'):
    defaultSkin = 'Default'
else:
    defaultSkin = skindir
mydisplay = MailWindow("script-courrier-main.xml", scriptpath, defaultSkin)
mydisplay .doModal()
del mydisplay
