﻿#!/usr/bin/python3
# -*- coding: utf-8 -*-

#==============================================================================
# This scripts checks for the flag "needs_automatic_syncing" in the database
# If a subtitle has that flag it downloads it and converts it to a pure
# transcript
# Afterwards it sends the file as attachment to an email address and resets
# the flag in the database
#==============================================================================

import os
import sys
import urllib
import re

# E-Mail-Stuff
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
#from email.mime.image import MIMEImage
from email import encoders

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "subtitleStatus.settings")

import django
django.setup()
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from www.models import Talk, Language, Subtitle

# Search for subtitles with set flag "needs_automatic_syncing"
my_subtitles = Subtitle.objects.filter(needs_automatic_syncing = True)

FROM = "localhost@subtitles.ber.c3voc.de"
TO = ""
TEXT = []
TEXT.append("These Subtitle-Files need your attention: ")

for any in my_subtitles:
    language = any.language.lang_amara_short
    amara_key = any.talk.amara_key
    slug = any.talk.slug
    url = "https://www.amara.org/api2/partners/videos/"+amara_key+"/languages/"+str(language)+"/subtitles/?format=srt"
    
    request = urllib.request.Request(url)
    response = urllib.request.urlopen(request)
    file_content = response.read()
    # Convert from bytes object to string object
    file_content = str(file_content,encoding = "UTF-8")
    
    # Split in single lines:
    text_content = file_content.splitlines()
    
    transcript = []
    # Ignore first two lines and check lines afterwards
    transcript.append(text_content[2]+"\n")
    if text_content[3] == "":
        i = 3
    elif text_content[4] == "":
        i = 4
    elif text_content[5] == "":
        i = 5
    
    # Check rest of whole file
    while i < len(text_content):
        # If line is empty jump two down
        if(text_content[i] == ""):
            transcript.append("\n")
            i += 3
        # If line ist not empty save to future output
        else:
            transcript.append(text_content[i]+"\n")
            i += 1
            
    filename = slug+"."+str(language)+".transcript"
    folder = "./downloads/"
    
    # Save File in ./downloads
    file = open(folder+filename,mode = "w",encoding = "utf-8")
    for line in transcript:
        line = re.sub("<i>","*",line)
        line = re.sub("</i>","*",line)
        file.write(line)
    file.close()
    
    # Building the email
    msg = MIMEMultipart()
    filename = folder+filename
    #print(filename)
    
    # Build attachment File for email an attach
    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(open(filename, 'rb').read())
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment',filename=os.path.split(filename)[1])
    msg.attach(attachment)
    
    # Build text for email with important Links
    text = MIMEText("Talk: "+any.talk.title+"\n"+
        "Bitte auf Youtube laden und syncen lassen!\n\n"+
        "Video-Adresse: "+any.talk.link_to_video_file+"\n"+
        "Amara-Adresse: "+"www.amara.org/videos/"+any.talk.amara_key+"/", "plain")
    msg.attach(text)
    msg["Subject"] = "Transcript needs your attention: "+str(any.talk.frab_id_talk)+' "'+any.talk.title+'"'
    msg["From"] = FROM
    msg["To"] = TO
    s = smtplib.SMTP('localhost')
    s.send_message(msg)
    s.quit()
    any.needs_automatic_syncing = False
    any.save()
    
    