#!/usr/bin/python2
# -*- coding: utf-8 -*-

import email
import imaplib
import re
import html2text
import os
from re import compile as Pattern

import email
from email.Parser import Parser as EmailParser
from email.utils import parseaddr
from email.Header import decode_header

USER = 'fce.valeins@libertysurf.fr'
PASSWORD = 'umr5536'

imap = imaplib.IMAP4('imap.aliceadsl.fr')
att_file = ':'
#imap.login(USER, PASSWORD)
imap.login('fce.valeins@libertysurf.fr', 'umr5536')
imap.select('INBOX')
#Search new mail, Filter examples : UNSEEN, ALL, ....
#numEmails = len(imap.search(None, 'UnSeen')[1][0].split())
numEmails = len(imap.search(None, 'ALL')[1][0].split())
#numEmails = len(imap.search(None, '(FROM "samsung.com")' )[1][0].split())
print( ("You have %d emails IMAP" % numEmails) )
i = 0
##Retrieve list of mails
#typ, data = imap.search('UTF-8', SEARCH_PARAM)
#typ, data = imap.search(None, 'UnSeen')
#typ, data = imap.search(None, 'ALL')
#typ, data = imap.search(None, '(FROM "samsung.com")')
#for num in data[0].split():
#    i = i + 1
#    typ, data = imap.fetch(num, '(RFC822)')
#    up = (i*100)/numEmails    #Get mail              Please wait
#    text = data[0][1].strip()
#    parse()
    #print ('TEXT : %s ' % text)
#imap.logout

def parse():
 
 global text
 global att_file

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
 print ("FROM : %s SUJET : %s " % (Sujet,realname))
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
            #print(("File : %s" % (att_path)))
            fp = open(att_path, 'wb')
            fp.write(part.get_payload(decode=True))
            fp.close()
            attached_images.append(att_path)
            #print(("ATTACHED :%s" % attached_images))
	##########################################################################
	#print(("ATT : %s" % (file_att)))
	#print(part)
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
            #print ("BODY : %s " % body)
        except Exception:
            body += "Erreur unicode"
            print( "BODY Erreur = %s " % body)
    elif part.get_content_type() == "text/html":
        if html is None:
            html = ""
        try :
            #Test to try fix error unicode 
            #'ascii' codec can't decode byte 0xc5 in position 32: ordinal not in range(128)
            print ("CHARSET = %s " % part.get_content_charset())
            if (part.get_content_charset() is None):
                raw_html = part.get_payload(decode=True)
                #raw_html.upper()
                #raw_html = raw_html.encode('utf-8','replace')
                print("RAW_HTML None 126")
                try :
                  html = html2text.html2text(raw_html)
                except Exception, e:
                  print ("Error 130 : %s" % e)
                  raw_html = raw_html.decode('utf-8','replace')
                  html = html2text.html2text(raw_html)
                  print("RAW_HTML None OK")
            else:
                raw_html = part.get_payload(decode=True)
                charset_msg = part.get_content_charset()
                #unicode(
                #   part.get_payload(decode=True),
                #   part.get_content_charset(),
                #   'ignore'
                #   ).encode('utf8','ignore')
                #print("RAW_HTML 126 : %s" % raw_html)
                html = raw_html.decode(charset_msg)
                html = html2text.html2text(html)
                print ("HTML OK\n")
                #print ("=========================\n%s\n-----------------------\n" % html)
        except Exception, e:
            #html += "Erreur unicode html"
            print( "ERROR HTML = %s " % (str(e)))
            print( "ERROR HTML =============================  ")
            #print ("PART PAYLOAD %s " % part.get_payload(decode=True))
            #raw_html = 	part.get_payload(decode=True)
            #unicode_coded_entities_html = unicode(BeautifulStoneSoup(raw_html,
            #                convertEntities=BeautifulStoneSoup.HTML_ENTITIES))
            #print ('unicode_coded : %s ' % unicode_coded_entities_html)
            #html += unicode_coded_entities_html
            #html = raw_html	
            #print( "==> HTML avant html2text = %s <==" % html )
            #html = html2text.html2text(raw_html)
            #print( "%s" % html )
        #except Exception, e:
         #   html += "Erreur unicode html"
            print( "ERROR HTML = %s " % (str(e)))
            #print( "==> HTML = %s <==" % html )
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
                print( str(e) )
        #Nb of lines msg for scroll text
        nb_lignes = description.count("\n")

        date += att_file
        #print(("attached files : %s" % att_file))
	#Verify if att_path exist
        if 'attached_images' in locals():
           counter = 0
           for name_image in attached_images:
              #print(('attached %s ' % attached_images))
              counter += 1 
              #print(('image%s, IMAGE : %s ' % (counter,name_image)))
    
##Retrieve list of mails
#typ, data = imap.search('UTF-8', SEARCH_PARAM)
#typ, data = imap.search(None, 'UnSeen')
typ, data = imap.search(None, 'ALL')
#typ, data = imap.search(None, '(FROM "samsung.com")')
for num in data[0].split():
    i = i + 1
    typ, data = imap.fetch(num, '(RFC822)')
    up = (i*100)/numEmails    #Get mail              Please wait
    text = data[0][1].strip()
    parse()
    #print ('TEXT : %s ' % text)
imap.logout
