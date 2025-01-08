import csv
import json
import re

class Japanese_Dictionary:
    def __init__(self, mapping_file: str, json_file: str):
        with open(json_file, 'r', encoding='UTF-8') as json_file:
            self.dictionary = json.load(json_file)
        self.mappings = self.get_mapping(mapping_file)

    def get_mapping(self, mapping_file):
        with open(mapping_file, 'r', encoding='ShiftJIS') as tsv_file:
            reader = csv.reader(tsv_file, delimiter='\t')
            mapping_array = {}
            for row in reader:
                if len(row) < 2:
                    continue
                value = row[0][1:]
                try:
                    value = int(value, 16)
                except ValueError:
                    continue
                if row[1] != "-":
                    unicode_string = row[1][1:]
                    unicode_character = chr(int(unicode_string, 16))
                    mapping_array[value] = unicode_character
                else:
                    try:
                        mapping_array[value] = row[2]
                    except IndexError:
                        continue
            return mapping_array

    def replace_placeholders(self, text: str, replacements: dict) -> str:
        def replacer(match):
            key = int(match.group(1))
            return replacements.get(key, match.group())
        # Adjusted pattern to match any letter before the underscore
        pattern = re.compile(r'\{\{\w+_(\d+)\}\}')
        result = pattern.sub(replacer, text)
        return result

    def lookup_word(self, lookup_word: str):
        # '【食べる】'
        for entry in self.dictionary['subbooks'][0]['entries']:
            if '【' + lookup_word + '】' in entry['heading']:
                return self.replace_placeholders(entry['text'], self.mappings)