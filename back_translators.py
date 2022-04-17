from back_trans_model import BackTranslate
from random import randint
from hashlib import md5
import requests
from utils import getLangDict
# if googletrans is installed, uses it to access google translate, 
# otherwise, uses another simple web-scraping based func (may be less reliable)
from utils import gTransByRegex
try:
    from googletrans import Translator
    googletransExists = True
except:
    googletransExists = False
    
    
LangDict = getLangDict()


class BaiduBackTranslator(BackTranslate):
    '''Back Translator based on Baidu Translate. You need to apply for 
    the access to the API before using this back translator.
    
    Apply at: https://fanyi-api.baidu.com/product/11. However, an unregistered 
    Chinese domestic phone number is needed for the application.
    
    Parameter:
        - appid (str): App ID for the access to the Baidu Translate API.
        - secretKey (str) : secret key to the appid for the access to the Baidu Translate API.
        - dst_lang (str): dst_lang
        - apiLink (str or None): the customized link to generate a vaild url to access the translation service.
        - lang_dic (str or None): lang_dic (lang code and name pairs) for Baidu Translate. If not given, uses 
            the `BaiduCommonLangDict` as in `langDict.json`. 
    '''
    
    def __init__(self, appid, secretKey, dst_lang, apiLink=None, lang_dic=None):
        self.appid = appid
        self.secretKey = secretKey
        if not apiLink:
            self.apiLink = 'https://fanyi-api.baidu.com/api/trans/vip/translate'
        if not lang_dic:
            lang_dic = LangDict['BaiduCommonLangDict']
        super().__init__(self._translate, lang_dic, dst_lang)
    
    def _translate(self, query, src_lang, dst_lang):
        
        salt = randint(12345, 123456)
        sign = self.appid + query + str(salt) + self.secretKey
        sign = md5(sign.encode('utf-8')).hexdigest()
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {'appid': self.appid, 'q': query, 'from': src_lang, 
                   'to': dst_lang, 'salt': salt, 'sign': sign}
        
        r = requests.post(self.apiLink, headers=headers, params=payload)
        result = r.json()
        out = []
        for res in result['trans_result']:
            out.append(res['dst'])
        return '\n'.join(out)
    

class GoogleBackTranslator(BackTranslate):
    '''Back Translator based on Google Translate. If you do not have `googletrans` installed, 
    another simple web-scraping func will be used to access Google Translate. 
    
    Parameter:
        - dst_lang (str): dst_lang
        - lang_dic (str or None): lang_dic (lang code and name pairs) for Google Translate. 
            If not given, uses the `GoogleLangDict` as in `langDict.json`. 
        - use_googletrans (bool): whether to use googletrans to access Google Translate if 
            it is installed. Defaults to True.
    '''
    def __init__(self, dst_lang, lang_dict=None, use_googletrans=True):
        if not lang_dict:
            lang_dict = LangDict['GoogleLangDict'] 
        
        if not googletransExists:        
            use_googletrans = False
        
        if use_googletrans:
            self._translate = lambda q, sl, dl: Translator().translate(q, dl, sl).text
        else:
            self._translate = lambda query, src_lang, dst_lang: gTransByRegex(query, src_lang, dst_lang)
        
        super().__init__(self._translate, lang_dict, dst_lang)


class PapagoBackTranslator(BackTranslate):
    '''Back Translator based on Papago Translate. You need to apply for 
    the access to the API before using this back translator.
    
    Apply at: https://developers.naver.com/products/papago/nmt/nmt.md. 
    
    Parameter:
        - clientId (str): client Id for the access to the Papago Translate API.
        - secretKey (str) : client Key to the client Id for the access to the Papago Translate API.
        - dst_lang (str): dst_lang
        - apiLink (str or None): the customized link to generate a vaild url to access the translation service.
        - lang_dic (str or None): lang_dic (lang code and name pairs) for Papago Translate. If not given, uses 
            the `PapagoLangDict` as in `langDict.json`. 
    '''
    def __init__(self, clientId, clientKey, dst_lang, apiLink=None, lang_dict=None):
        self.headers = {'X-Naver-Client-Id': clientId, 
                       'X-Naver-Client-Secret': clientKey, 
                       'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        if not apiLink:
            self.apiLink = 'https://openapi.naver.com/v1/papago/n2mt'
        
        if not lang_dict:
            lang_dict = LangDict['PapagoLangDict']
        
        super().__init__(self._translate, lang_dict, dst_lang)
        
    def _translate(self, query, src_lang, dst_lang):
        payload = {'text': query, 'source': src_lang, 'target': dst_lang}
        r = requests.post(self.apiLink, headers=self.headers, data=payload)
        result = r.json()
        return result['message']['result']['translatedText']
