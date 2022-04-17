'''
Author: Zhengxiang (Jack) Wang 
GitHub: https://github.com/jaaack-wang 
About: utils for back translation
'''
import json
import re
import html
from urllib import parse
import requests


def getLangDict(path='langDict.json'):
    '''Gets the Lang Dict for three translators: Baidu, Google, Papago.
    
    The returned dict includes three core dicts of lang code and name pairs. Keys:
        - GoogleLangDict
        - BaiduCommonLangDict
        - PapagoLangDict
        
    In addition, there are two versions of complete lang dicts for Baidu 
    Translator, both in Chinese and in English. Keys:
        - BaiduLangDict_EN
        - BaiduLangDict_ZH
    
    However, please note that, although Baidu supports translating all the languages 
    exisiting in the complete lang dict, but langs not included in the `BaiduCommonLangDict` 
    have very few translatable directions, which is not good for back transaltion. 
    
     The key `CommonLangList` will return a list of common language names, which may be good 
     for filtering some uncommon languages in lang dicts for other translators. 
     '''
    return json.load(open(path, 'r'))    

    
def _find_pos_lang_code(dic, lang, rev_dic=None):
    '''Backward rough matching by deleting one char in the end at a time 
    to find a str, either in the lang code or name, that matches.'''
    if not rev_dic:
        rev_dic = {v.lower(): k for k, v in dic.items()}
        
    lang_lower = lang.lower()
    if len(lang) == 1:
        return {c: l for l, c in rev_dic.items() if l[0] == lang_lower}
    
    for i in range(len(lang)-1, 0, -1):
        pos_code = [c for c in dic.keys() if lang[:i] in c]
        if pos_code:
            return {c: dic[c] for c in pos_code}
        pos_lang = [l for l in rev_dic.keys() if lang_lower[:i] in l]
        if pos_lang:
            return {rev_dic[l]: l for l in pos_lang}
    return 


def find_lang_code(dic, lang, rev_dic=None, warning=False):
    '''Find lang code if there is an exact match available; otherwise, 
    raises an exception and prints out possible suggestions based on str overlap.'''
    assert isinstance(lang, str), f'lang "{lang}" must be str, not {type(lang)}'
    if lang in dic:
        return lang
    
    lang_lower = lang.lower()
    if not rev_dic:
        rev_dic = {v.lower(): k for k, v in dic.items()}    

    for k, v in dic.items():
        if lang_lower == k.lower():
            print(f'\033[32mReturning lang code [{k}] for "{lang}" ({v}) \033[0m')
            return rev_dic[v.lower()]
        if lang_lower == v.lower():
            print(f'\033[32mReturning lang code [{k}] for "{lang}" ({v}) \033[0m')
            return k
    
    pos = _find_pos_lang_code(dic, lang, rev_dic)
    if pos:
        print(f'\033[46mBy "{lang}", are you looking for {pos} ?')
    
    if warning:
        raise ValueError(f'Lang code not found for "{lang}"')

        
def gTransByRegex(text, src_lang, dst_lang):
    '''A simple web crawling method for accessing Google Translate (may 
    not be realiable and ethical for large-scale translation). 
    '''
    gTransTmpUrl = 'http://translate.google.cn/m?q=%s&tl=%s&sl=%s'
    text = parse.quote(text)
    url = gTransTmpUrl % (text, dst_lang, src_lang)
    
    r = requests.get(url)
    tar_ptn = r'(?s)class="(?:t0|result-container)">(.*?)<'
    result = re.findall(tar_ptn, r.text)
    
    return html.unescape(result[0])
