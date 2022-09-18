#!/usr/bin/python3.9

from abc import abstractmethod

import argparse
import re
import string

WORD_LIST = '/home/meagan/Documents/Code/Wordle/enable.txt'
WORD_LENGTH = 5
MAX_GUESSES = 6

ANSI_RESET = "\u001b[0m"

class Chatty:
	is_chatty = True

	def narrate(self, message):
		if self.is_chatty:
			try:
				print(message)
			except BaseException as err:
				print(f"Unexpected {err=}, {type(err)=}")
			
	@abstractmethod
	def stringify(self):
		pass

class Printer:
	def __init__(self, total_width, column_width, margin):
		for arg in total_width, column_width, margin:
			if arg < 1:
				raise AssertionError(f'Total width, column width, and margin must all be at least 1, not ({total_width}, {column_width}, {margin})')

		if column_width > total_width:
			raise AssertionError(f'Column width ({column_width}) cannot be greater than total width ({total_width}).')
		
		self.total_width = total_width
		self.column_width = column_width
		self.margin = margin
		self.columns = self._init_columns()
		
	
	def _init_columns(self):
		columns = 1
		while ((columns + 1) * self.column_width) + (columns * self.margin_width) <= self.total_width:
			columns += 1
		
		return columns

class Tile:

	sigils = {
		'^': {
			'name': 'absent',
			'color': "\u001b[40;1m",
		},
		'*': {
			'name': 'present',
			'color': "\u001b[43;1m",
		},
		'+': {
			'name': 'correct',
			'color': "\u001b[42;1m",
		}
	}


	def __init__(self, tile):
		if len(tile) != 2 or tile[0] not in self.sigils or tile[1].lower() not in string.ascii_lowercase:
			raise AssertionError('Each tile must be represented as a sigil ({sigils}) followed by a letter, not "{given}"'.format(
				sigils=', '.join(self.sigils.keys()),
				given=letter,
			))
		self.sigil = tile[0]
		self.letter = tile[1]

	def status(self):
		return self.sigils[self.sigil]['name']

	def stringify(self):
		return f"{self.sigils[self.sigil]['color']} {self.letter.upper()} {ANSI_RESET}"
		

class WordleHelper(Chatty):

	def __init__(self, word_length=WORD_LENGTH, dictionary=WORD_LIST):
		if word_length < 1:
			raise AssertionError(f'Word length must be at least one, not {word_length}')

		self.word_length = word_length
		self.dictionary = dictionary

		self.positions = range(1, self.word_length + 1)

		self.include = set([])
		self.exclude = set([])
		self.correct = {}
		self.incorrect = {}
		self.matches = self._get_words()


	def update_args(self, correct, present, absent):
		if len(correct) + len(present) + len(absent) != self.word_length:
			raise AssertionError(f'Expected exactly {self.word_length} tiles but got {len(correct) + len(present) + len(absent)}.')
			
		for status in (correct, present, absent):
			for position in status:
				status[position] = status[position].lower()
				if status[position] not in string.ascii_lowercase:
					raise AssertionError(f'Expected a lowercase letter but got {status[position]}')
		
		for position in correct:
			self._update_correct(position, correct[position])

		for position in present:
			self._update_present(position, present[position])

		for position in absent:
			self._update_absent(position, absent[position])
			

	def _update_correct(self, position, letter):
		letter = letter.lower()
		if position not in self.correct:
			self.correct[position] = [letter]
		elif self.correct[position][0] != letter:
			raise AssertionError(f'Position {position} cannot contain both "{self.correct[position][0]}" and "{letter}"')
		
		self._update_include(letter)


	def _update_present(self, position, letter):
		letter = letter.lower()
		if position not in self.incorrect:
			self.incorrect[position] = set([])

		self.incorrect[position].add(letter)
		self._update_include(letter)


	def _update_absent(self, position, letter):
		letter = letter.lower()	
		if letter not in self.include:
			self.exclude.add(letter)


	def _update_include(self, letter):
		self.include.add(letter)
		if len(self.include) > self.word_length:
			raise AssertionError('At most {word_length} letters may be included, but {included_count} were given ({included})'.format(
				word_length=self.word_length,
				included_count=len(self.include),
				included=''.join(self.include),
			))


	def _get_words(self):
		with open(self.dictionary) as dictionary:
			words = filter(lambda word: len(word) == self.word_length, dictionary.read().splitlines())
		return list(words)


	def _filter_for_included(self, matches):
		for letter in self.include:
			self.narrate(f'{list(matches)[0:10]}')
			
			matches = list(filter(lambda word: re.search(letter, word), matches))
			
			self.narrate(f"\t\tafter filtering to include {letter}: {sum(1 for _ in matches)}")
		return matches


	def _filter_out_excluded(self, matches):
		if len(self.exclude) > 0:
			pattern = re.compile('[' + ''.join(self.exclude) + ']')
			matches = list(filter(lambda word: pattern.search(word) is None, matches))
		return matches


	def _get_position_pattern(self, position, letters):
		pattern = list(map(lambda position: '.', self.positions))
		pattern[position - 1] = '[' + ''.join(letters) + ']'
		return '^' + ''.join(pattern) + '$'

	def _filter_for_correct(self, matches):
		for position in self.correct:
			pattern = re.compile(self._get_position_pattern(position, self.correct[position]))
			matches = list(filter(lambda word: pattern.match(word), matches))
		return matches

	def _filter_out_incorrect(self, matches):
		for position in self.incorrect:
			pattern = re.compile(self._get_position_pattern(position, self.incorrect[position]))
			matches = list(filter(lambda word: pattern.match(word) is None, matches))
		return matches


	def filter_words(self):
		self.matches = self._filter_words(self.matches)


	def _filter_words(self, matches):

		self.narrate(f"\tbefore filtering: {sum(1 for _ in matches)}")

		# Start by filtering for words that include each of the required letters.
		matches = self._filter_for_included(matches)

		self.narrate(f"\tafter _filter_for_included: {sum(1 for _ in matches)}")

		# Then require that each known correct letter appears in the corresponding position.
		matches = self._filter_for_correct(matches)

		self.narrate(f"\tafter _filter_for_correct: {sum(1 for _ in matches)}")

		# Next exclude any words where a known incorrect letter appears in the corresponding position.
		matches = self._filter_out_incorrect(matches)

		self.narrate(f"\tafter _filter_out_incorrect: {sum(1 for _ in matches)}")

		# Finally filter out words that include any of the excluded letters.
		matches = self._filter_out_excluded(matches)

		self.narrate(f"\tafter _filter_out_excluded: {sum(1 for _ in matches)}")

		return list(matches)

	def describe(self):
		return "\n".join([
			f'include: {sorted(self.include)}',
			f'exclude: {sorted(self.exclude)}',
			f'correct: {self.correct}',
			f'incorrect: {self.incorrect}',
			f'{len(self.matches)} possible matches',
			"\n".join(map(lambda match: f"\t{match}", self.matches)),
		])
		


class CommandLine:

	def __init__(self, word_length=WORD_LENGTH, max_guesses=MAX_GUESSES, dictionary=WORD_LIST):
		if word_length < 1 or max_guesses < 1:
			raise AssertionError(f'Word length and guesses must each be at least one, not {word_length} and {guesses}')
		self.word_length = word_length
		self.max_guesses = max_guesses
		self.guesses = []
		self.helper = WordleHelper(self.word_length, dictionary)


	def _parse_input(self, guess):
		parts = re.split('\s+', guess)
		if len(parts) != self.word_length:
			raise AssertionError(f'Guess must include exactly {self.word_length} space-separated tiles, e.g. +s ^o *l ^i ^d')
		
		return list(map(lambda part: Tile(part), parts))


	def _handle_next_guess(self, guess):
		tiles = self._parse_input(guess)
		
		correct = {}
		present = {}
		absent = {}
		for i in range(self.word_length):
			status, letter = tiles[i].status(), tiles[i].letter
			if status == 'correct':
				correct[i + 1] = letter
			elif status == 'present':
				present[i + 1] = letter
			elif status == 'absent':
				absent[i + 1] = letter
			else:
				raise AssertionError(f'Tile status "{status}" not recognized')

		self.helper.update_args(correct, present, absent)
		self.helper.filter_words()
		self.guesses.append(tiles)
		print(self.helper.describe())
		print(self.stringify())


	def prompt(self):
		while len(self.guesses) < self.max_guesses:
			try:
				self._handle_next_guess(input(f'Guess {len(self.guesses) + 1}: ').lower())
			except AssertionError as err:
				print(f"{str(err)}")
				

	def stringify(self):
		return "\n".join(map(lambda guess: ''.join(map(lambda tile: tile.stringify(), guess)), self.guesses))

cl = CommandLine()
cl.prompt()
