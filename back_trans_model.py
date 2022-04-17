'''
Author: Zhengxiang (Jack) Wang 
GitHub: https://github.com/jaaack-wang 
About: A simple model for back translation
'''
from random import sample
from itertools import groupby
from utils import find_lang_code


class BackTranslate:
    '''A class method for back translation.
    
    Parameter:
        - translator (method): a translator that takes three inputs: 
            - (1) query (str): text to translate 
            - (2) src (str): source language of the text
            - (3) dst (str): destination language to translate the text into
        - lang_dic (dict): lang_dic used by the translator
        - dst_lang: default destination language
    
    #################
    Basic Usage:
    #################
    
    >>> from back_trans_model import BackTranslate
    >>> BT = BackTranslate(translator, lang_dic, dst_lang)
    >>> query = 'a string or a list of string'
    
    -----------------
    Back translation
    -----------------

    # if query is a str
    >>> BT.back_translate(query, src_lang=None, mid_lang=None, 
                            dst_lang=None, all_mid_lang=False, out_dict=False)
                            
    # if query is a list of str
    >>> BT.bulk_back_translate(query, src_lang=None, mid_lang=None, 
                            dst_lang=None, all_mid_lang=False, out_dict=False)
    
    Parameters explained:
        - src_lang (str or None): defaults to the dst_lang as in initialization.
        - mid_lang (list or str or None): mid_lang refers to the language(s) we 
            want the query translated into before they are translated back into the 
            dst_lang. Defaluts to a randomly selected translatable lang if not given. 
            If mid_lang is a list, see `all_mid_lang` below.
        - dst_lang (str or None): defaults to the dst_lang as in initialization
        - all_mid_lang (bool): if all_mid_lang is False and mid_lang is a list, then 
            there will be n (= num of mid_lang) times back translation for each one of 
            the these mid_lang. Otherwise, one query will only be translated once. But you 
            can combine mid_lang (list) wit all_mid_lang=True, to see how a query translated 
            through multiple languages and finally back into dst_lang looks like!
        - out_dict (bool): if True, returns a dict that logs the entire back translation process.
    
    
    -------------------------------------
    Back translation as text augmentation
    -------------------------------------
    
    # when you use `BT.augment`, it is assumed that the src_lang
    # and dst_lang are the same with dst_lang as in initialization.
    
    >>> BT.augment(query, mid_lang=None, out_per_text=1)
    
    Parameters explained:
        - query (str or list): if list, returns a list of augmented texts 
            for each query, which itself is a list.
        - mid_lang (list or str or None): if not given, randomly selects one for 
            every iteration. If a list, the back translation goes through all of them.
        - out_per_text (int): max output augmented texts per text. Please note that, if 
            out_per_text > 1, no matter whether mid_lang is given or not, from the second 
            iteration, mid_lang will be randomly selected to avoid producing same augmented text. 
            If mid_lang is given as a list, the randomly selected mid_lang will also be a list of same size. 
    '''
    
    def __init__(self, translator, lang_dic, dst_lang):
        self._translate = translator
        self.lang_dic = lang_dic
        self.lang_dic_rev = {v.lower(): k for k, v in lang_dic.items()}
        self.dst_lang = self._find_lang(dst_lang)    
        self.lang_list = list(self.lang_dic.keys())
        # to make sure the dst_lang will not be randomly selected as the mid_lang
        self.lang_list.remove(self.dst_lang) 
    
    def translate(self, query, src_lang=None, dst_lang=None):
        '''translate a query which must be a str.'''
        assert isinstance(query, str), 'query must be a str'
        if not src_lang:
            src_lang = 'auto'
        else:
            src_lang = self._find_lang(src_lang)
        if not dst_lang:
            dst_lang = self.dst_lang
        else:
            dst_lang = self._find_lang(dst_lang)
        
        try:
            return self._translate(query, src_lang, dst_lang)
        
        except Exception as e:
            print(f'\033[32mCannot translate "{query}" from {src_lang} to {dst_lang}\033[0m')
            print('Reason being: ', e)
            return 
    
    def bulk_transalte(self, query, src_lang, dst_lang):
        '''translate a list of queries which must be a list.'''
        assert isinstance(query, list), 'query must be a list'
        assert all(isinstance(q, str) for q in query), 'query must be a list of str when it\'s a list'
        
        out = []
        for q in query:
            out.append(self.translate(q, src_lang, dst_lang))
        return out
    
    def _find_lang(self, lang):
        '''Find proper lang code for a given input. An exception will be raised if no 
        exact match is found and with some printed possible suggetions if any.'''
        return find_lang_code(self.lang_dic, lang, self.lang_dic_rev, warning=True)
    
    def find_pos_lang(self, lang):
        '''Find possible lang code for a given input if any.'''
        return find_lang_code(self.lang_dic, lang, self.lang_dic_rev, warning=False)
    
    def _back_translate(self, query, src_lang, mid_lang, dst_lang, out_dict):
        '''The abstract func for back translation'''
        mid_lang = [mid_lang] if isinstance(mid_lang, str) else mid_lang
        mid_lang = [src_lang] + mid_lang + [dst_lang]
        
        if out_dict:
            out = {'srcLang': self.lang_dic[src_lang], 'originText': query}
            for i in range(len(mid_lang) - 2):
                query = self.translate(query, mid_lang[i], mid_lang[i+1])
                lang_key, text_key = 'transLang' + str(i+1), 'transText' + str(i+1)
                out.update({lang_key: self.lang_dic[mid_lang[i+1]], text_key: query})
            
            query = self.translate(query, mid_lang[-2], mid_lang[-1])
            out.update({'dstLang': self.lang_dic[mid_lang[-1]], 'finalText': query})
            return out
        
        for i in range(len(mid_lang) - 1):
            query = self.translate(query, mid_lang[i], mid_lang[i+1])
        return query
    
    def back_translate(self, query, 
                       src_lang=None, mid_lang=None, dst_lang=None,
                       all_mid_lang=False, out_dict=False):
        '''Returns back translated text for a query which must be a str. 
        
        Paratermers:
            - query (str): a text.
            - src_lang (None, str): if not given, defaults to the dst_lang as in the initialization.
            - mid_lang (None, str, list): a str or a list of str of lang names. If not given, randomly select one. 
            - dst_lang (None, str): if not given, defaults to the dst_lang as in the initialization.
            - all_mid_lang (bool): if mid_lang is a list and all_mid_lang=False, treat do back trans for 
                every mid_lang; otherwise, back translation will include all the mid langs.
            - out_dict (bool): if True, return a dic that logs the back translation process. 
        
        Returns:
            a dict that logs the back translation process, or a str that is the back translated text.
        '''
        if not src_lang:
            src_lang = self.dst_lang
        else:
            src_lang = self._find_lang(src_lang)
            
        if not mid_lang:
            mid_lang = sample(self.lang_list, 1)[0]
        elif isinstance(mid_lang, str):
            mid_lang = self._find_lang(mid_lang)
        elif isinstance(mid_lang, list):
            mid_lang = [self._find_lang(ml) for ml in mid_lang]
            
        if not dst_lang:
            dst_lang = self.dst_lang
        else:
            dst_lang = self._find_lang(dst_lang)
        
        if not all_mid_lang and isinstance(mid_lang, list):
            out = []
            for ml in mid_lang:
                res = self._back_translate(query, src_lang, ml, dst_lang, out_dict)
                out.append(res)
            return out
        
        return self._back_translate(query, src_lang, mid_lang, dst_lang, out_dict)
    
    def bulk_back_translate(self, query, 
                            src_lang=None, mid_lang=None, dst_lang=None, 
                            all_mid_lang=False, out_dict=False):
        '''Back translates a list of str'''
        
        assert isinstance(query, list), 'query must be a list'
        assert all(isinstance(q, str) for q in query), 'query must be a list of str when it\'s a list'
        out = []
        for q in query:
            out.append(self.back_translate(q, src_lang, mid_lang, dst_lang, all_mid_lang, out_dict))
        return out
    
    def _augment(self, query, mid_lang, out_per_text, mid_lang_num=1):
        '''Abstract func for augment. mid_lang_num defines the number of mid_lang to randomly generate.'''
        
        out = []
        for _ in range(out_per_text):
            mid_lang = sample(self.lang_list, mid_lang_num) if not mid_lang else mid_lang
            res = self._back_translate(query, self.dst_lang, mid_lang, self.dst_lang, False)
            if res and res != query:
                out.append(res)

            mid_lang = None
            
        if len(out) <= 1:
            return out
        
        out.sort()
        return [o for o,_ in groupby(out)] 
    
    
    def augment(self, query, mid_lang=None, out_per_text=1):
        '''Augments text(s) by back translation. Query text must be in the dst_lang as in initialization.         
        '''
        mid_lang_num = 1
        
        if not mid_lang:
            mid_lang = sample(self.lang_list, mid_lang_num)
        elif isinstance(mid_lang, str):
            mid_lang = self._find_lang(mid_lang)
        elif isinstance(mid_lang, list):
            mid_lang = [self._find_lang(ml) for ml in mid_lang]
            mid_lang_num = len(mid_lang)
        else:
            raise ValueError('mid_lang must be a str or a list of str')
        
        if isinstance(query, str):
            return self._augment(query, mid_lang, out_per_text, mid_lang_num)
        elif isinstance(query, list):
            assert all(isinstance(q, str) for q in query), 'query must be a list of str when it\'s a list'
            output = []
            for q in query:
                output.append(self._augment(q, mid_lang, out_per_text, mid_lang_num)) 
            return output
        
        else:
            raise TypeError('query must be a string or a list of string')
