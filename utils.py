import os
from os.path import dirname, abspath, realpath
import importlib
from tempfile import mkstemp
from uuid import uuid4

import requests
from aqt import mw


CURRENT_DIR = dirname(abspath(realpath(__file__)))


def path_to(*args):
    return os.path.join(CURRENT_DIR, *args)


def get_config():
    return mw.addonManager.getConfig(__name__)


def get_note_query(note):
    field_names = mw.col.models.field_names(note.note_type())
    query_field = field_names.index(get_config()["query_field"])
    return note.fields[query_field]


def get_note_image_field_index(note):
    field_names = mw.col.models.field_names(note.note_type())
    return field_names.index(get_config()["image_field"])

def report(text):
    if importlib.util.find_spec("aqt"):
        from aqt.utils import showWarning
        showWarning(text, title="Anki Image Search vDuck")
    else:
        print(text)
