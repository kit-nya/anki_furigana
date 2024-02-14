from __future__ import annotations

import os

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QVBoxLayout, QSpinBox
from anki.notes import Note
from aqt import gui_hooks, mw, qconnect

import xml.etree.ElementTree as ET

import json

SETTING_SRC_FIELD = "kanji_field"
SETTING_FURI_DEST_FIELD = "furigana_field"
SETTING_KANA_DEST_FIELD = "kana_field"
SETTING_TYPE_DEST_FIELD = "type_field"
SETTING_MEANING_FIELD = "definition_field"
SETTING_NUM_DEFS = "number_of_defs"

def load_xml_file(filepath):
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        return root
    except FileNotFoundError:
        print(f"File {filepath} not found.")
        return None
    except ET.ParseError:
        print(f"Error parsing the file {filepath}.")
        return None

def search_def(root, keb_text, def_limit = 0):
    return_val = ""
    for entry in root.iter('entry'):
        for keb in entry.iter('keb'):  # iterate over all 'keb' children of 'entry'
            if keb.text == keb_text:  # compare the text of the 'keb' element with the text you're looking for
                # Gather glosses from each sense
                for i, sense in enumerate(entry.iter('sense'), start=1):
                    glosses = [gloss.text for gloss in sense.iter('gloss')]
                    gloss_text = '; '.join(glosses)
                    return_val += (f"{i}: {gloss_text}<br>")
                    def_limit = def_limit - 1
                    if def_limit == 0:
                        break
                return return_val[:-4] if return_val.endswith("<br>") else return_val
    return return_val[:-4] if return_val.endswith("<br>") else return_val

def search_reb(root, keb_text):
    # Assuming root is an ElementTree instance, and element names are as per your code base
    for entry in root.iter('entry'):
        keb = entry.find('k_ele/keb')
        if keb is not None and keb.text == keb_text:
            return entry.findall('r_ele/reb')[0].text.strip()
    return ""

def search_pos(root, keb_text):
    pos_values = set()
    for entry in root.iter('entry'):
        keb = entry.find('k_ele/keb')
        if keb is not None and keb.text == keb_text:
            pos_elements = entry.findall('sense/pos')
            for pos in pos_elements:
                # Check if <!ENTITY> in tag text and replace with full string
                pos_text = pos.text
                if pos_text and "&" in pos_text and ';' in pos_text:
                    entity_value = pos_text.replace('&', '').replace(';', '')
                    full_string = root.docinfo.internalDTD.entities.get(entity_value)
                    pos_values.add(full_string if full_string else pos_text)
                else:
                    pos_values.add(pos_text)
    return '; '.join(pos_values)

def search_furigana(data, target_text):
    for obj in data:
        if obj['text'] == target_text:
            furigana = obj['furigana']
            result = ""
            last_no_kanji = False
            for f in furigana:
                if "rt" in f:
                    if last_no_kanji:
                        result += " "
                    result += f['ruby']
                    result += "[" + f['rt'] + "]"
                else:
                    result += f['ruby']
                    last_no_kanji = True
            return result
    return ""


def parts_of_speech_conversion(input: str)-> str:
    outputStr = ""
    if "noun" in input.lower():
        outputStr += "名詞、"
    if "godan" in input.lower():
        outputStr += "五段、"
    if "ichidan" in input.lower():
        outputStr += "一段、"
    if "suru" in input.lower():
        outputStr += "する、"
    if input.startswith("transitive verb") or " transitive verb" in input.lower():
        outputStr += "他動詞、"
    if "intransitive verb" in input.lower():
        outputStr += "自動詞、"
    if "adjective (keiyoushi)" in input.lower():
        outputStr += "いー形容詞、"
    if "adjectival nouns" in input.lower():
        outputStr += "なー形容詞、"
    return outputStr.strip("、")

previous_srcTxt = None
def onFocusLost(changed: bool, note: Note, current_field_index: int) -> bool:
    # if note.note_type()["name"] == "Japanese2":
    #     return changed
    fields = mw.col.models.field_names(note.note_type())
    modified_field = fields[current_field_index]
    if modified_field == config[SETTING_SRC_FIELD]:
        srcTxt = mw.col.media.strip(note[modified_field])
        if srcTxt != "" and (previous_srcTxt is None or srcTxt != previous_srcTxt):
            if insert_if_empty(fields, note, SETTING_FURI_DEST_FIELD, search_furigana(jmdict_furi_data, srcTxt)):
                changed = True
            if insert_if_empty(fields, note, SETTING_MEANING_FIELD, search_def(jmdict_data, srcTxt, config[SETTING_NUM_DEFS])):
                changed = True
            if insert_if_empty(fields, note, SETTING_KANA_DEST_FIELD, search_reb(jmdict_data, srcTxt)):
                changed = True
            if insert_if_empty(fields, note, SETTING_TYPE_DEST_FIELD, parts_of_speech_conversion(search_pos(jmdict_data, srcTxt))):
                changed = True
    return changed


def insert_if_empty(fields: list, note: Note, dest_config: str, new_text: str):
    if new_text == "":
        return False
    dest_field = config[dest_config]
    if dest_field in fields:
        if note[dest_field] == "":
            note[dest_field] = new_text
        return True

def settings_dialog():
    dialog = QDialog(mw)
    dialog.setWindowTitle("Furigana Addon")
    
    # Input Field
    box_query = QHBoxLayout()
    label_query = QLabel("Input field:")
    text_query = QLineEdit("")
    text_query.setMinimumWidth(200)
    box_query.addWidget(label_query)
    box_query.addWidget(text_query)

    # All the output stuff
    box_furigana = QHBoxLayout()
    label_furigana = QLabel("Furigana field:")
    text_furigana = QLineEdit("")
    text_furigana.setMinimumWidth(200)
    box_furigana.addWidget(label_furigana)
    box_furigana.addWidget(text_furigana)

    box_def = QHBoxLayout()
    label_def = QLabel("Definition field:")
    text_def = QLineEdit("")
    text_def.setMinimumWidth(200)
    box_def.addWidget(label_def)
    box_def.addWidget(text_def)

    box_kana = QHBoxLayout()
    label_kana = QLabel("Kana field:")
    text_kana = QLineEdit("")
    text_kana.setMinimumWidth(200)
    box_kana.addWidget(label_kana)
    box_kana.addWidget(text_kana)

    box_type = QHBoxLayout()
    label_type = QLabel("Type field:")
    text_type = QLineEdit("")
    text_type.setMinimumWidth(200)
    box_type.addWidget(label_type)
    box_type.addWidget(text_type)

    box_def_nums = QHBoxLayout()
    label_def_nums = QLabel("Number of Defs:")
    text_def_nums = QSpinBox()
    text_def_nums.setMinimumWidth(200)
    box_def_nums.addWidget(label_def_nums)
    box_def_nums.addWidget(text_def_nums)

    ok = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
    cancel = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
    # config = mw.addonManager.getConfig(__name__)

    def init_configui():
        text_query.setText(config.get(SETTING_SRC_FIELD, "not_set"))
        text_furigana.setText(config.get(SETTING_FURI_DEST_FIELD, "not_set"))
        text_def.setText(config.get(SETTING_MEANING_FIELD, "not_set"))
        text_kana.setText(config.get(SETTING_KANA_DEST_FIELD, "not_set"))
        text_type.setText(config.get(SETTING_TYPE_DEST_FIELD, "WordType"))
        text_def_nums.setValue(config.get(SETTING_NUM_DEFS, 5))

    def save_config():
        config[SETTING_SRC_FIELD] = text_query.text()
        config[SETTING_FURI_DEST_FIELD] = text_furigana.text()
        config[SETTING_MEANING_FIELD] = text_def.text()
        config[SETTING_KANA_DEST_FIELD] = text_kana.text()
        config[SETTING_TYPE_DEST_FIELD] = text_type.text()
        config[SETTING_NUM_DEFS] = text_def_nums.value()
        mw.addonManager.writeConfig(__name__, config)
        dialog.close()

    def layout_everything():
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        layout.addLayout(box_query)
        layout.addLayout(box_furigana)
        layout.addLayout(box_kana)
        layout.addLayout(box_def)
        layout.addLayout(box_type)
        layout.addLayout(box_def_nums)

        layout.addWidget(ok)
        layout.addWidget(cancel)

    init_configui()
    ok.clicked.connect(save_config)
    cancel.clicked.connect(dialog.close)

    layout_everything()

    dialog.exec()


def init_menu():
    action = QAction("Furigana Addon Settings", mw)
    qconnect(action.triggered, settings_dialog)
    mw.form.menuTools.addAction(action)



gui_hooks.editor_did_unfocus_field.append(onFocusLost)

file_path = os.path.join(os.path.dirname(__file__), "dicts/")

with open(os.path.join(file_path +'JmdictFurigana.json'), 'r', encoding='utf-8-sig') as f:
    jmdict_furi_data = json.load(f)


# Usage
jmdict_data = load_xml_file(os.path.join(file_path + 'JMdict_e.xml'))
if jmdict_data is not None:
    print(f"Successfully loaded XML file. Root tag is '{jmdict_data.tag}'.")
else:
    print("Failed to load XML file.")
from aqt import mw
config = mw.addonManager.getConfig(__name__)
init_menu()
print(search_pos(jmdict_data,"料理"))