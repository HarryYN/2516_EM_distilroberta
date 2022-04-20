# Implementation from https://dev.to/davidisrawi/build-a-quick-summarizer-with-python-and-nltk

   
import numpy as np
import os
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize, sent_tokenize

from .dataset import get_tokenizer

class Summarizer:
    def __init__(self, task_config, lm):
        self.config = task_config
        self.tokenizer = get_tokenizer(lm=lm)
        self.len_cache = {}

    def _create_frequency_table(self, text_string) -> dict:
        """
        we create a dictionary for the word frequency table.
        For this, we should only use the words that are not part of the stopWords array.
        Removing stop words and making frequency table
        Stemmer - an algorithm to bring words to its root word.
        :rtype: dict
        """
        stopWords = set(stopwords.words("english"))
        words = word_tokenize(text_string)
        ps = PorterStemmer()

        freqTable = dict()
        for word in words:
            word = ps.stem(word)
            if word in stopWords:
                continue
            if word in freqTable:
                freqTable[word] += 1
            else:
                freqTable[word] = 1

        return freqTable


    def _score_sentences(self, sents, freqTable) -> dict:
        """
        score a sentence by its words
        Basic algorithm: adding the frequency of every non-stop word in a sentence divided by total no of words in a sentence.
        :rtype: dict
        """

        sentenceValue = dict()

        for word in sents:
            # word_count_in_sentence = (len(word_tokenize(word)))
            word_count_in_sentence_except_stop_words = 0
            for wordValue in freqTable:
                if wordValue in word.lower():
                    word_count_in_sentence_except_stop_words += 1
                    if word in sentenceValue:
                        sentenceValue[word] += freqTable[wordValue]
                    else:
                        sentenceValue[word] = freqTable[wordValue]

            if word in sentenceValue:
                sentenceValue[word] = sentenceValue[word] / word_count_in_sentence_except_stop_words

        return sentenceValue


    def _find_average_score(self, sentenceValue) -> int:
        """
        Find the average score from the sentence value dictionary
        :rtype: int
        """
        sumValues = 0
        for entry in sentenceValue:
            sumValues += sentenceValue[entry]

        # Average value of a sentence from original text
        average = (sumValues / len(sentenceValue))

        return average

    def get_len(self, word):
        """Return the sentence_piece length of a token.
        """
        if word in self.len_cache:
            return self.len_cache[word]
        length = len(self.tokenizer.tokenize(word))
        self.len_cache[word] = length
        return length

    def _generate_summary(self, freq_table, words, label, sentenceValue, threshold, max_len):
        summary = ''
        total_len = 0

        for word in words:
            if word in ['COL', 'VAL']:
              summary += word + ' '
            elif word in sentenceValue and sentenceValue[word] <= (5*threshold):
              summary += word + " "

            if self.get_len(word) + total_len > max_len:
              break
            total_len += self.get_len(word)

        if summary == "":
          for word in words:
            summary += word + " "

        return summary


    def transform(self, row, max_len):

        sentA, sentB, label = row.strip().split('\t')
        
        # 1 Create the word frequency table
        freq_table_A = self._create_frequency_table(sentA)
        freq_table_B = self._create_frequency_table(sentB)

        # 2 Tokenize the sentences

        word_sent_A = word_tokenize(sentA) 
        word_sent_B = word_tokenize(sentB) 

        # 3 Important Algorithm: score the sentences
        sentence_scores_A = self._score_sentences(word_sent_A, freq_table_A)
        sentence_scores_B = self._score_sentences(word_sent_B, freq_table_B)

        # 4 Find the threshold
        threshold_A = self._find_average_score(sentence_scores_A)
        threshold_B = self._find_average_score(sentence_scores_B)

        # 5 Important Algorithm: Generate the summary
        summary_A = self._generate_summary(freq_table_A, word_sent_A, label, sentence_scores_A, threshold_A, max_len)
        summary_B = self._generate_summary(freq_table_B, word_sent_B, label, sentence_scores_B, threshold_B, max_len)

        summary = summary_A + "\t" + summary_B + "\t" + label + "\n"


    def transform_file(self, input_fn, max_len, overwrite=False):
        """Summarize all lines of a tsv file.
        Run the summarizer. If the output already exists, just return the file name.
        Args:
            input_fn (str): the input file name
            max_len (int, optional): the max sequence len
            overwrite (bool, optional): if true, then overwrite any cached output
        Returns:
            str: the output file name
        """
        out_fn = input_fn + '.su'
        if not os.path.exists(out_fn) or \
            os.stat(out_fn).st_size == 0 or overwrite:
            with open(out_fn, 'w') as fout:
                for line in open(input_fn):
                    fout.write(self.transform(line, max_len=max_len))
        return out_fn