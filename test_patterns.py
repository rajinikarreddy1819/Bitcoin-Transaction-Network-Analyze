from pattern_matcher import PatternMatcher
from btn_parser import BTN_Parser

parser = BTN_Parser()
parser.load_from_file('data/sample_transactions.csv')
parser.parse_transactions()

matcher = PatternMatcher(parser)
matches = matcher.detect_patterns()

print(f'Found {len(matches)} matching patterns:')
for pattern_type in set(m['pattern'] for m in matches):
    count = sum(1 for m in matches if m['pattern'] == pattern_type)
    print(f'- {pattern_type}: {count} matches')
