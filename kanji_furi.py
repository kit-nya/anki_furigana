from __future__ import annotations

import json
import os
import xml.etree.ElementTree as Et
import pickle

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QVBoxLayout, QSpinBox
from anki.notes import Note
from aqt import gui_hooks, qconnect, mw

from . import japanese_dictionary

SETTING_SRC_FIELD = "kanji_field"
SETTING_FURI_DEST_FIELD = "furigana_field"
SETTING_KANA_DEST_FIELD = "kana_field"
SETTING_TYPE_DEST_FIELD = "type_field"
SETTING_MEANING_FIELD = "definition_field"
SETTING_NUM_DEFS = "number_of_defs"
SETTING_JAPAN_DEST_FIELD = "Definition"

# This is used to prevent excessive lookups
previous_srcTxt = None

dicts_path = os.path.join(os.path.dirname(__file__), "dicts/")


def load_xml_file(filepath):
    try:
        tree = Et.parse(filepath)
        root = tree.getroot()
        return root
    except FileNotFoundError:
        print(f"File {filepath} not found.")
        return None
    except Et.ParseError:
        print(f"Error parsing the file {filepath}.")
        return None


def build_dict_from_xml(root):
    output = {}
    for entry in root.iter('entry'):
        parts_of_speech_values = set()
        keb_entries = set()
        for keb_entry in entry.findall('k_ele/keb'):
            keb_entries.add(keb_entry.text)
        pos_elements = entry.findall('sense/pos')
        for pos in pos_elements:
            # Check if <!ENTITY> in tag text and replace with full string
            pos_text = pos.text
            if pos_text and "&" in pos_text and ';' in pos_text:
                entity_value = pos_text.replace('&', '').replace(';', '')
                full_string = root.docinfo.internalDTD.entities.get(entity_value)
                parts_of_speech_values.add(full_string if full_string else pos_text)
            else:
                parts_of_speech_values.add(pos_text)

        senses = {}
        for i, sense in enumerate(entry.iter('sense'), start=1):
            glosses = [gloss.text for gloss in sense.iter('gloss')]
            gloss_text = '; '.join(glosses)
            senses[i] = f"{i}: {gloss_text}"
        reb = entry.findall('r_ele/reb')[0].text.strip()
        for ke in keb_entries:
            if ke not in output:
                output[ke] = {"parts_of_speech_values": '; '.join(parts_of_speech_values),
                              "senses": senses, "reb": reb}
    return output

def get_senses(dict_item, limit=5):
    numbers = list(range(1, limit+1))
    arry = []
    for number in numbers:
        if number in dict_item["senses"]:
            arry.append(dict_item["senses"][number])
    return "<br>".join(arry)

def search_def(root, keb_text, def_limit=0):
    return_val = ""
    for entry in root.iter('entry'):
        for keb in entry.iter('keb'):  # iterate over all 'keb' children of 'entry'
            if keb.text == keb_text:  # compare the text of the 'keb' element with the text you're looking for
                # Gather glosses from each sense
                for i, sense in enumerate(entry.iter('sense'), start=1):
                    glosses = [gloss.text for gloss in sense.iter('gloss')]
                    gloss_text = '; '.join(glosses)
                    return_val += f"{i}: {gloss_text}<br>"
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
            for fu in furigana:
                if "rt" in fu:
                    if last_no_kanji:
                        result += " "
                    result += fu['ruby']
                    result += "[" + fu['rt'] + "]"
                else:
                    result += fu['ruby']
                    last_no_kanji = True
            return result
    return ""


def parts_of_speech_conversion(input_str: str) -> str:
    output_str = ""
    if "noun" in input_str.lower():
        output_str += "名詞、"
    if "godan" in input_str.lower():
        output_str += "五段、"
    if "ichidan" in input_str.lower():
        output_str += "一段、"
    if "suru" in input_str.lower():
        output_str += "する、"
    if input_str.startswith("transitive verb") or " transitive verb" in input_str.lower():
        output_str += "他動詞、"
    if "intransitive verb" in input_str.lower():
        output_str += "自動詞、"
    if "adjective (keiyoushi)" in input_str.lower():
        output_str += "いー形容詞、"
    if "adjectival nouns" in input_str.lower():
        output_str += "なー形容詞、"
    return output_str.strip("、")


def on_focus_lost(changed: bool, note: Note, current_field_index: int) -> bool:
    # Get the field names
    fields = mw.col.models.field_names(note.note_type())
    # Get the modified field
    modified_field = fields[current_field_index]
    # Check if it's the same as config, if so proceed
    if modified_field == config[SETTING_SRC_FIELD]:
        # Strip for good measure
        src_txt = mw.col.media.strip(note[modified_field])
        if src_txt != "" and (previous_srcTxt is None or src_txt != previous_srcTxt):
            # Added the field checks for people who don't have all fields for whatever reason
            if config.get(SETTING_FURI_DEST_FIELD) in fields:
                if insert_if_empty(fields, note, SETTING_FURI_DEST_FIELD, search_furigana(jmdict_furi_data, src_txt)):
                    changed = True
            jmdict_info = dict_data.get(src_txt, None)
            if jmdict_info is not None:
                if config.get(SETTING_MEANING_FIELD) in fields:
                    def_num = config[SETTING_NUM_DEFS]
                    if insert_if_empty(fields, note, SETTING_MEANING_FIELD,
                                       get_senses(jmdict_info, def_num)):
                        changed = True
                if config.get(SETTING_KANA_DEST_FIELD) in fields:
                    if insert_if_empty(fields, note, SETTING_KANA_DEST_FIELD, jmdict_info.get("reb", "")):
                        changed = True
                if config.get(SETTING_TYPE_DEST_FIELD) in fields:
                    if insert_if_empty(fields, note, SETTING_TYPE_DEST_FIELD,
                                       parts_of_speech_conversion(jmdict_info.get("parts_of_speech_values", ""))):
                        changed = True
            if config.get(SETTING_JAPAN_DEST_FIELD) in fields:
                jpdef = dictionary.lookup_word(src_txt)
                if jpdef is not None:
                    if insert_if_empty(fields, note, SETTING_JAPAN_DEST_FIELD, jpdef):
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

    box_jp_def = QHBoxLayout()
    label_jp_def = QLabel("JP Def field:")
    text_jp_def = QLineEdit("")
    text_jp_def.setMinimumWidth(200)
    box_jp_def.addWidget(label_jp_def)
    box_jp_def.addWidget(text_jp_def)

    ok = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
    cancel = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)

    def init_configui():
        text_query.setText(config.get(SETTING_SRC_FIELD, "not_set"))
        text_furigana.setText(config.get(SETTING_FURI_DEST_FIELD, "not_set"))
        text_def.setText(config.get(SETTING_MEANING_FIELD, "not_set"))
        text_kana.setText(config.get(SETTING_KANA_DEST_FIELD, "not_set"))
        text_type.setText(config.get(SETTING_TYPE_DEST_FIELD, "WordType"))
        text_jp_def.setText(config.get(SETTING_JAPAN_DEST_FIELD, "jp_def"))
        text_def_nums.setValue(config.get(SETTING_NUM_DEFS, 5))

    def save_config():
        config[SETTING_SRC_FIELD] = text_query.text()
        config[SETTING_FURI_DEST_FIELD] = text_furigana.text()
        config[SETTING_MEANING_FIELD] = text_def.text()
        config[SETTING_KANA_DEST_FIELD] = text_kana.text()
        config[SETTING_TYPE_DEST_FIELD] = text_type.text()
        config[SETTING_JAPAN_DEST_FIELD] = text_jp_def.text()
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
        layout.addLayout(box_jp_def)

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


def get_field_names_array():
    array = [config.get(SETTING_SRC_FIELD), config.get(SETTING_FURI_DEST_FIELD), config.get(SETTING_KANA_DEST_FIELD),
             config.get(SETTING_TYPE_DEST_FIELD), config.get(SETTING_MEANING_FIELD), config.get(SETTING_JAPAN_DEST_FIELD)]
    return array


def clear_fields(editor):
    fields = mw.col.models.field_names(editor.note.note_type())
    dest_fields = get_field_names_array()
    for field in fields:
        if field in dest_fields:
            editor.note[field] = ""
    editor.loadNote()


def editor_button_setup(buttons, editor):
    icons_path = os.path.join(os.path.dirname(__file__), "icons/")
    clear_icon = "icons8-clear-50.png"
    clear_icon_path = os.path.join(icons_path, clear_icon)
    btn = editor.addButton(clear_icon_path,
                           'clear_fields',
                           clear_fields,
                           tip='Clear fields')
    buttons.append(btn)


# GUI Hooks
gui_hooks.editor_did_unfocus_field.append(on_focus_lost)
gui_hooks.editor_did_init_buttons.append(editor_button_setup)

# Dictionary Furigana Dictionary
with open(os.path.join(dicts_path + 'JmdictFurigana.json'), 'r', encoding='utf-8-sig') as f:
    jmdict_furi_data = json.load(f)

# JMDict Data Load
data_file = os.path.join(dicts_path + 'dill.pkl') # DIctionary LLoad?
# Check to see if we already have a file
if os.path.isfile(data_file):
    # Open the pickle file and load the data
    with open(data_file, 'rb') as file:
        dict_data = pickle.load(file)
else:
    # No pickle file found, so we build the array and save for next time. This takes a few seconds.
    jmdict_data = load_xml_file(os.path.join(dicts_path + 'JMdict_e.xml'))
    if jmdict_data is not None:
        print(f"Successfully loaded XML file. Root tag is '{jmdict_data.tag}'.")
    else:
        print("Failed to load XML file.")
    dict_data = build_dict_from_xml(jmdict_data)
    jmdict_data = None
    with open(data_file, "wb") as file:
        pickle.dump(dict_data, file)

file = os.path.join(dicts_path + "DAIJISEN.map")
dict_file = os.path.join(dicts_path + "daijisen.json")
json_obj = None

dictionary = japanese_dictionary.Japanese_Dictionary(file, dict_file)


# Create config variable
config = mw.addonManager.getConfig(__name__)

# Add the options to the menu
init_menu()