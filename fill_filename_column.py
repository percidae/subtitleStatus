#!/usr/bin/python3
# -*- coding: utf-8 -*-

#==============================================================================
# This scripts fills the filename-column in the talk table
#
# Use this when a new event finally has video files and needs the filename
# field to be filled to sync srts to the cdn
#==============================================================================

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "subtitleStatus.settings")

import django
django.setup()

from www.models import Talk

my_talks = Talk.objects.filter(blacklisted = False)

for any_talk in my_talks:
    any_talk.fill_filename_field()
