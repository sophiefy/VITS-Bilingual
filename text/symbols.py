_pad        = '_'
_punctuation = ',.!?-~'
_letters = 'Qabcdefghijklmnopqrstuvwxyz'
_letters_ipa = 'ŋəæʤʧʃɪ '
_numbers = '1234'

# Export all symbols:
symbols = [_pad] + list(_punctuation) + list(_letters) + list(_letters_ipa) + list(_numbers)

# Special symbol ids
SPACE_ID = symbols.index(" ")