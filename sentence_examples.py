import csv
import pickle
from datetime import datetime

class JapaneseSentenceLib:
    def __init__(self):
        self.sentences = {}

    # Data locations...
    # Sentence id [tab] Lang [tab] Text [tab] Username [tab] Date added [tab] Date last modified
    def load_sentences_from_file(self, filepath):
        with open(filepath, 'r') as file:
            reader = csv.reader(file, delimiter='\t')
            for line in reader:
                add_sentence = Sentence(line)
                self.sentences[int(add_sentence.id)] = add_sentence

    def find_example_sentences_by_word(self, word, limit = 10):
        sentences = []
        for sentence in self.sentences.values():
            if word in sentence.text:
                sentences.append(sentence)

        sentences = sorted(sentences, key=lambda x: x.date_added)
        if len(sentences) > limit:
            return sentences[:limit]
        return sentences

    def find_example_sentences_by_word_formatted(self, word, limit = 10):
        sentences = self.find_example_sentences_by_word(word, limit)
        output_str_ary = []
        for sentence in sentences:
            output_str_ary.append(sentence.text)
        return "<br>".join(output_str_ary)

    def load_sentence_rating_data(self, file):
        with open(file, 'r') as file:
            reader = csv.reader(file, delimiter='\t')
            for line in reader:
                sentence = self.get_sentence_by_id(line[1])
                if sentence:
                    if line[2] == '1':
                        sentence.add_positive_rating()
                    elif line[2] == '0':
                        sentence.add_undecided_rating()
                    elif line[2] == '-1':
                        sentence.add_negative_rating()

    def get_sentence_by_id(self, id):
        if int(id) in self.sentences:
            return self.sentences[int(id)]
        return None

    def save_pickle_file(self, data_file):
        with open(data_file, 'wb') as file:
            pickle.dump(self.sentences, file)

    def load_pickle_file(self, data_file):
        with open(data_file, 'rb') as file:
            self.sentences = pickle.load(file)

class Sentence:
    def __init__(self, data):
        self.id = data[0]
        self.lang = data[1]
        self.text = data[2]
        self.username = data[3]
        self.date_added = data[4]
        self.date_modified = data[5]
        # Fixes up the ones without an added date
        if self.date_added == '\\N':
            self.date_added = self.date_modified
        if self.date_modified == '\\N':
            self.date_modified = self.date_added
        if self.date_added in ['0000-00-00 00:00:00', '\\N']:
            self.date_added = '2008-01-26 18:04:24'
        if self.date_modified in ['0000-00-00 00:00:00', '\\N']:
            self.date_modified = '2008-01-26 18:04:24'
        self.date_modified = datetime.strptime(self.date_modified, '%Y-%m-%d %H:%M:%S')
        self.date_added = datetime.strptime(self.date_added, '%Y-%m-%d %H:%M:%S')
        self.total_ratings = 0
        self.positive_rating = 0
        self.negative_rating = 0

    def add_positive_rating(self):
        self.positive_rating = self.positive_rating + 1
        self.total_ratings = self.total_ratings + 1

    def add_undecided_rating(self):
        self.total_ratings = self.total_ratings + 1

    def add_negative_rating(self):
        self.negative_rating = self.negative_rating + 1
        self.total_ratings = self.total_ratings + 1

    def get_rating_percentage(self):
        if self.total_ratings == 0:
            return 100
        return self.positive_rating / self.total_ratings * 100