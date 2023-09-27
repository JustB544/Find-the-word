# credit to https://www.ef.edu/english-resources/english-vocabulary/top-3000-words/ for the words

import requests
from secret import auth_key
from models import Words
from json import loads


def extract(file):
    """Returns contents of file"""
    f = open(file, "r")
    output = f.read()
    f.close()
    return output


def transform(string: str, split: str):
    """Takes a string and splits it by a specified split value"""
    words = []
    start = 0
    find = string.find(split)
    split_len = len(split)
    while (find != -1):
        words.append({"word": string[start:find], "length": find-start})
        start = find + split_len
        find = string.find(split, start)
    words.append({"word": string[start:], "length": len(string[start:])})
    start = find + split_len
    return words

def test_words(count, start=0):
    """Test words with api to see if they have an associated example"""
    headers = {
        "X-RapidAPI-Key": auth_key,
        "X-RapidAPI-Host": "wordsapiv1.p.rapidapi.com"
    }
    output = {"error": [], "fail": [], "success": []}
    for x in range(count):
        word = Words.query.get(x+1+start)
        if (word == None):
            break
        url = f"https://wordsapiv1.p.rapidapi.com/words/{word.word}/examples"
        try:
            response = requests.get(url, headers=headers)
            if (len(response.json()["examples"]) == 0):
                output["fail"].append(word.word)
            else:
                output["success"].append(word.word)
        except:
            output["error"].append(word.word)
    print("Failed: \n", output["fail"])
    print("Errors: \n", output["error"])
    print("Success: \n", output["success"])
    return output

def remove_words(words, bad_words):
    """Function that removes bad words from words
    
    words: file with words in csv format
    bad_words: file with a json array
    """
    _words = extract(words)
    _bad_words = loads(extract(bad_words))
    for word in _bad_words:
        _words = _words.replace(f",{word},", ",")
    with open("new_words.txt", "w") as f:
        f.write(_words)
# remove_words("words.txt", "bad_words.txt")
            

