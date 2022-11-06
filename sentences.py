import re
import requests
from bs4 import BeautifulSoup


def load_sentences_local() -> list:
    """Local store with sentences
    """
    sentences = [
        {"text": "When my time comes. Forget the wrong that I’ve done.",
         "level": 2},
        {"text": "In a hole in the ground there lived a hobbit.",
         "level": 3},
        {"text": "The sky the port was the color of television, tuned to a dead channel.",
         "level": 2},
        {"text": "I love the smell of napalm in the morning.",
         "level": 1},
        {"text": "The man in black fled across the desert, and the gunslinger followed.",
         "level": 1},
        {"text": "The Consul watched as Kassad raised the death wand.",
         "level": 2},
        {"text": "If you want to make enemies, try to change something.",
         "level": 3},
        {"text": "We're not gonna take it. Oh no, we ain't gonna take it. We're not gonna take it anymore",
         "level": 2},
        {"text": "I learned very early the difference between knowing the name of something and knowing something.",
         "level": 3}
    ]

    return sentences


def load_sentences_remote(user_word: str) -> list:
    """Parsing sentences from site
    https://sentence.yourdictionary.com
    using word from user
    """
    cleaner = re.compile('<.*?>')
    response = requests.get(f"https://sentence.yourdictionary.com/{user_word}", timeout=5)
    soup = BeautifulSoup(response.text, 'html.parser')
    sentence_list = []
    sentence_list_with_level = []
    parsed_sentences_examples = soup.find_all(
        'p', attrs={"class": "sentence-item__text"})

    for sentence in parsed_sentences_examples:
        sentence_list.append(re.sub(cleaner, '', str(sentence)))

    for sentence in sentence_list:
        length_sentence = len(sentence)
        if length_sentence <= 50:
            sentence_list_with_level.append({"text": sentence, "level": 1})
        if length_sentence > 50 and length_sentence < 100:
            sentence_list_with_level.append({"text": sentence, "level": 2})
        if length_sentence > 100 and length_sentence < 300:
            sentence_list_with_level.append({"text": sentence, "level": 3})

    return sentence_list_with_level
