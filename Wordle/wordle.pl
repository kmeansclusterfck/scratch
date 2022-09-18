use strict;
use warnings;

use constant {
	WORDLIST => '/home/meagan/Documents/Code/Wordle/wordle-words.txt',
	LETTERCOUNT => 5,
};

use File::Slurp qw( read_file );
use Getopt::Long qw( GetOptions );
use List::AllUtils qw( uniq );



my %args = (
	INCLUDESTR => '',
	INCLUDE => [],
	EXCLUDESTR => '',
	EXCLUDE => [],
);

my %positions;
my %antipositions;

GetOptions(
	'include=s' => \$args{INCLUDESTR},
	'exclude=s' => \$args{EXCLUDESTR},
	(map {
		(
			"is${_}=s" => \$positions{$_},
			"not${_}=s" => \$antipositions{$_},
		)
	} (1 .. LETTERCOUNT())),
);



unless ($args{INCLUDESTR} || $args{EXCLUDESTR}) {
	print "At least one of --include or --exclude must be specified.\n" and exit;
}

for my $arg (qw( INCLUDE EXCLUDE )) {
	if ($args{"${arg}STR"}) {
		$args{$arg} = [ uniq sort { $a cmp $b } split //, lc($args{"${arg}STR"}) ];
	}
}

my @matches = read_file(WORDLIST(), chomp => 1);
die "Failed to load word list.\n" unless scalar(@matches);

for my $letter (@{ $args{INCLUDE} }) {
	@matches = grep { $_ =~ m/$letter/ } @matches;
}

for my $letter (@{ $args{EXCLUDE} }) {
	@matches = grep { $_ !~ m/$letter/ } @matches;
}

for my $position (grep { $positions{$_} } keys %positions) {
	for my $letter (split //, $positions{$position}) {
		my $pattern = _GetPositionPattern($position, $letter);
		@matches = grep { $_ =~ m/$pattern/ } @matches;
	}
}

for my $position (grep { $antipositions{$_} } keys %antipositions) {
	for my $letter (split //, $antipositions{$position}) {
		my $pattern = _GetPositionPattern($position, $letter);
		@matches = grep { $_ !~ m/$pattern/ } @matches;
	}
}

printf("%s words found with the following criteria:\n\t%s\n\n\t%s\n",
	scalar(@matches),
	join("\n\t", grep { $_ } (
		scalar(@{ $args{INCLUDE} })
			? sprintf('- including [%s]', join(', ', @{ $args{INCLUDE} }))
			: '',
		scalar(@{ $args{EXCLUDE} })
			? sprintf('- excluding [%s]', join(', ', @{ $args{EXCLUDE} }))
			: '',
	)),
	join("\n\t", @matches),
);

print _FormatFrequencies({
	FREQUENCIES => _CalculateFrequencies(\@matches),
	INCLUDE => $args{INCLUDE},
});

sub _CalculateFrequencies {
	my ($words) = @_;
	
	my %frequencies;
	$frequencies{$_} = {} for ('ANY', 1 .. LETTERCOUNT());
	
	for my $word (@{ $words }) {
		my @letters = split //, $word;
		my %any = ();
		for my $i (1 .. LETTERCOUNT()) {
			$frequencies{$i}->{$letters[$i - 1]} += 1;
			$any{$letters[$i - 1]} = 1;
		}
		$frequencies{ANY}->{$_} += 1 for keys %any;
	}
	
	return \%frequencies;
}

sub _FormatFrequencies {
	my ($args) = @_;
	_AssertFields($args, [qw( FREQUENCIES INCLUDE )]);

	my %frequencies = %{ $args->{FREQUENCIES} };
	my %include = map { $_ => 1 } @{ $args->{INCLUDE} };
	
	my $string = '';
	for my $frequency ('ANY', 1 .. LETTERCOUNT()) {
		
		$string .= sprintf("%s\n\t%s\n\n",
			$frequency,
			join("\n\t", map {
				sprintf('%s%s => %s',
					$include{$_} ? ' ' : '*',
					$_,
					$frequencies{$frequency}->{$_},
				)
			} reverse sort {
				$frequencies{$frequency}->{$a} <=> $frequencies{$frequency}->{$b}
			} keys %{ $frequencies{$frequency} }),
		);
	}
	
	return $string;
}

sub _GetPositionPattern {
	my ($position, $letter) = @_;
	my @pattern = ('.') x LETTERCOUNT();
	$pattern[$position - 1] = $letter;
	return sprintf('^%s$', join('', @pattern));
}

sub _AssertFields {
	my ($hashref, @args) = @_;
	die "Invalid arguments given.\n" unless $hashref && scalar(@args) >= 1 && scalar(@args) <= 2;

	my %keys = map { $_ => 1 } keys %{ $hashref };

	my %required = map { $_ => 1 } @{ $args[0] };
	for my $key (keys %required) {
		die "ASSERTION FAILED: $key is required\n" unless $keys{$key};
		delete $keys{$key};
	}
	
	my %valid = map { $_ => 1 } @{ $args[1] || [] };
	for my $key (keys %keys) {
		die "ASSERTION FAILED: $key is not valid\n" unless $valid{$key} || $required{$key};
	}
	
	return;
}

