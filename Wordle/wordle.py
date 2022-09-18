#!/usr/bin/python3.9

import argparse
import re
import string

WORD_LIST = '/home/meagan/Documents/Code/Wordle/enable.txt'
WORD_LENGTH = 5

class WordleHelper:

	def __init__(self, word_length=WORD_LENGTH, dictionary=WORD_LIST):
		if word_length < 1:
			raise AssertionError(f'Word length must be at least one, not {word_length}')

		self.word_length = word_length
		self.dictionary = dictionary

		self.positions = range(1, self.word_length + 1)
		self.position_strs = map(lambda i: str(i), self.positions)
		self.parser = self.get_parser()
		self.args = vars(self.parser.parse_args())

		self.correct = {}
		self.incorrect = {}
		self.validate_args()


		self.words = self.get_words()
		self.matches = self.filter_words()


	def get_parser(self):
		parser = argparse.ArgumentParser()

		options = {
			'include': 'letters present in the solution',
			'exclude': 'letters absent from the solution',
		}

		for option in sorted(options):
			parser.add_argument(
				'--' + option,
				help = options[option],
				type = str.lower,
				action = 'append',
			)

		for position in self.position_strs:
			parser.add_argument(
				'--is' + position,
				help = 'correct letter for position ' + position,
				type = str.lower,
				choices = string.ascii_lowercase,
				action = 'append',
			)
			parser.add_argument(
				'--not' + position,
				help = 'letter(s) not correct for position ' + position,
				type = str.lower,
				action = 'append',
			)

		return parser

	def validate_args(self):
		# Default missing arguments to empty lists.
		for arg in filter(lambda a: self.args[a] == None, self.args):
			self.args[arg] = []

		# Flatten each argument and remove duplicates.
		for arg in filter(lambda a: len(self.args[a]) > 0, self.args):
			self.args[arg] = sorted(set(list(''.join(self.args[arg]))))

		if len(self.args['include']) > self.word_length:
			self.parser.error('At most {word_length} letters may be included, but {included_count} were given ({included})'.format(
				word_length=self.word_length,
				included_count=len(self.args['include']),
				included=''.join(self.args['include']),
			))

		for position in self.positions:
			is_arg = 'is' + str(position)
			not_arg = 'not' + str(position)
			# Ensure that at most 1 letter has been specified as correct for each position...
			if len(self.args[is_arg]) > 1:
				self.parser.error('Specify at most one letter for --' + is_arg + '.')
			# ...and that it is not among the excluded letters.
			elif len(self.args[is_arg]) == 1:
				if self.args[is_arg][0] in self.args['exclude']:
					self.parser.error(f'"{self.args[is_arg][0]}" cannot both be excluded and correct for any position.')
				# Ignore the corresponding "not" argument if given.
				self.args[not_arg] = []
				self.correct[position] = self.args[is_arg]

			if len(self.args[not_arg]) > 0:
				self.incorrect[position] = self.args[not_arg]

		# Ensure that none of the included letters are also excluded.
		for letter in self.args['include']:
			if letter in self.args['exclude']:
				self.parser.error(f'"{letter}" cannot be both included and excluded.')

		return

	def get_words(self):
		with open(self.dictionary) as dictionary:
			words = filter(lambda word: len(word) == self.word_length, dictionary.read().splitlines())
		return words

	def filter_for_included(self, matches):
		for letter in self.args['include']:
			matches = filter(lambda word: re.search(letter, word), matches)
		return matches

	def filter_out_excluded(self, matches):
		if len(self.args['exclude']) > 0:
			pattern = re.compile('[' + ''.join(self.args['exclude']) + ']')
			matches = filter(lambda word: pattern.search(word) == None, matches)
		return matches

	def get_position_pattern(self, position, letters):
		pattern = list(map(lambda position: '.', self.positions))
		pattern[position - 1] = '[' + ''.join(letters) + ']'
		return '^' + ''.join(pattern) + '$'

	def filter_for_correct(self, matches):
		for position in self.correct:
			pattern = re.compile(self.get_position_pattern(position, self.correct[position]))
			matches = filter(lambda word: pattern.match(word), matches)
		return matches

	def filter_out_incorrect(self, matches):
		for position in self.incorrect:
			pattern = re.compile(self.get_position_pattern(position, self.incorrect[position]))
			matches = filter(lambda word: pattern.match(word) == None, matches)
		return matches

	def filter_words(self):
		matches = self.words

		# Start by filtering for words that include each of the required letters.
		matches = self.filter_for_included(matches)

		# Then require that each known correct letter appears in the corresponding position.
		matches = self.filter_for_correct(matches)

		# Next exclude any words where a known incorrect letter appears in the corresponding position.
		matches = self.filter_out_incorrect(matches)

		# Finally filter out words that include any of the excluded letters.
		matches = self.filter_out_excluded(matches)

		return list(matches)


helper = WordleHelper()

print(len(helper.matches))
print(helper.matches[0:10])
