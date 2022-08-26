import pyopenjtalk
import re
from unidecode import unidecode
from pypinyin import pinyin, Style

# Regular expression matching Japanese without punctuation marks:
_japanese_characters = re.compile(r'[A-Za-z\d\u3005\u3040-\u30ff\u4e00-\u9fff\uff11-\uff19\uff21-\uff3a\uff41-\uff5a\uff66-\uff9d]')

# Regular expression matching non-Japanese characters or punctuation marks:
_japanese_marks = re.compile(r'[^A-Za-z\d\u3005\u3040-\u30ff\u4e00-\u9fff\uff11-\uff19\uff21-\uff3a\uff41-\uff5a\uff66-\uff9d]')

_japanese_vowels = ['a', 'i', 'u', 'e', 'o']

_hatsuon = ['N']

_revision_jp = {
    'shi': 'xi',
    'sha': 'xya',
    'shu': 'xyu',
    'sho': 'xyo',
    'chi': 'qi',
    'tsu': 'cu',
    'cha': 'qya',
    'chu': 'qyu',
    'cho': 'qyo',
    'r': 'l',
    'ja': 'jya',
    'ju': 'jyu',
    'jo': 'jyo',
    'N': 'ŋ',
}

_revision_ch = {
    'e': 'ə',
    'ie': 'ye',
    'ia': 'ya',
    'iu': 'you',
    'ui': 'uei',
    'io': 'yo',
    'ng': 'ŋ',
    'an': 'æn',
    'zh': 'ʤ',
    'ch': 'ʧ',
    'sh': 'ʃ',
    'yu': 'yv',
    'zi': 'zɪ',
    'ci': 'cɪ',
    'si': 'sɪ',
    '。': '.',
    '，': ',',
    '？': '?',
    '！': '!',
}

def japanese_cleaner_1(text):
  '''Pipeline for notating accent in Japanese text.'''
  '''Reference https://r9y9.github.io/ttslearn/latest/notebooks/ch10_Recipe-Tacotron.html'''
  sentences = re.split(_japanese_marks, text)
  marks = re.findall(_japanese_marks, text)
  text = ''
  for i, sentence in enumerate(sentences):
    if re.match(_japanese_characters, sentence):
      if text!='':
        text+='#'
      labels = pyopenjtalk.extract_fullcontext(sentence)
      for n, label in enumerate(labels):
        phoneme = re.search(r'\-([^\+]*)\+', label).group(1)
        if phoneme not in ['sil','pau']:
          text += phoneme.replace('cl','Q')
        else:
          continue
        n_moras = int(re.search(r'/F:(\d+)_', label).group(1))
        a1 = int(re.search(r"/A:(\-?[0-9]+)\+", label).group(1))
        a2 = int(re.search(r"\+(\d+)\+", label).group(1))
        a3 = int(re.search(r"\+(\d+)/", label).group(1))
        if re.search(r'\-([^\+]*)\+', labels[n + 1]).group(1) in ['sil','pau']:
          a2_next=-1
        else:
          a2_next = int(re.search(r"\+(\d+)\+", labels[n + 1]).group(1))
        # Accent phrase boundary
        if a3 == 1 and a2_next == 1:
          text += '#'
        # Falling
        elif a1 == 0 and a2_next == a2 + 1 and a2 != n_moras:
          text += '↓'
        # Rising
        elif a2 == 1 and a2_next == 2:
          text += '↑'
    if i<len(marks):
      text += unidecode(marks[i]).replace(' ','')
  if re.match('[A-Za-z]',text[-1]):
    text += '.'
  return text

def japanese_cleaner_2(text):
  new_text = ''
  length = len(text)
  for i, char in enumerate(text):
    char = char.replace('A', 'a').replace('I', 'i').replace('U', 'u').replace('E', 'e').replace('O', 'o')
    new_text += char
    if (i+1 < length) and char in _japanese_vowels:
      new_text += ' '
    elif char == 'N':
      new_text += ' '
    else:
      continue
  return new_text


def add_tone(text, low=True):
  new_text = []
  length = len(text)
  for i, char in enumerate(text):
    new_text.append(char)
    if char in (_japanese_vowels + _hatsuon):
      if low:
        new_text.append('1')
      else:
        new_text.append('3')
    else:
      continue
  return ''.join(new_text)

def japanese_cleaner_3(text):
  parts = text.split('#')
  new_text = ''
  for part in parts:
    # low high 
    if '↑' in part and '↓' not in part:
      sub_parts = part.split('↑')
      sub_part1 = add_tone(sub_parts[0], True)
      sub_part2 = add_tone(sub_parts[1], False)
      sub_text = sub_part1 + sub_part2
      new_text += sub_text
    # high low
    elif '↑' not in part and '↓' in part:
      sub_parts = part.split('↓')
      sub_part1 = add_tone(sub_parts[0], False)
      sub_part2 = add_tone(sub_parts[1], True)
      sub_text = sub_part1 + sub_part2
      new_text += sub_text
    # low high low
    else:
      sub_parts = re.split('↑|↓', part)
      sub_part1 = add_tone(sub_parts[0], True)
      sub_part2 = add_tone(sub_parts[1], False)
      sub_part3 = add_tone(sub_parts[2], True)
      sub_text = sub_part1 + sub_part2 + sub_part3
      new_text += sub_text

  # revision
  for item in _revision_jp.items():
    old = item[0]
    new = item[1]
    new_text = new_text.replace(old, new)
  
  return new_text

def japanese_cleaner_pipe(text):
  text = japanese_cleaner_1(text)
  text = japanese_cleaner_2(text)
  text = japanese_cleaner_3(text)

  return text


def chinese_cleaner_pipe(text):
  phones = []
  for phone in pinyin(text, style=Style.TONE3):
    phone = phone[0]
    for item in _revision_ch.items():
      old = item[0]
      new = item[1]
      phone = phone.replace(old, new)
    phones.append(phone)
  return " ".join(phones)

def chipanese_cleaners(text, lang):
  if lang == 'ch':
    return chinese_cleaner_pipe(text)
  elif lang == 'jp':
    return japanese_cleaner_pipe(text)
  else:
    raise ValueError ('Unsupported language type!')
