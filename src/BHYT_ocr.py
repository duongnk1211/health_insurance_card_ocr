import re

import cv2
import numpy as np
import pytesseract
from PIL import Image
from rich import print
from unidecode import unidecode

pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'
class CardInfoExtractor(object):
    LANG = 'vie'

    def __init__(self, oem, psm):
        self.config = f'--oem {oem} --psm {psm}'
        print('Init Card Info Extractor!')
    
    def extract(self, img):
        # preprocess
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 19, 33)

        pil_img = self.convert_cv_to_pillow(thresh)
        infos = pytesseract.image_to_string(pil_img, config=self.config, lang=self.LANG)
        output = {
            'id': None,
            'name': '',
            'dob': '',
            'gender': '',
            'address': '',
            'address2': '',
            'expire': '',
            'fiveyears': '',
            'issue_by': ''
        }
        infos = infos.split('\n')
        cleaned = self.clean_infos(infos)
        contents = self.find_contents(cleaned)
        output.update(contents)

        return self.convert_output(output)
    
    def clean_infos(self, infos):
        cleaned = []
        pattern =r'[^a-zA-Z0-9 /ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơƯĂẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼỀỀỂẾưăạảấầẩẫậắằẳẵặẹẻẽềềểỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪễệỉịọỏốồổỗộớờởỡợụủứừỬỮỰỲỴÝỶỸửữựỳýỵỷỹ]' 
        for info in infos:
            cleaned_info = re.sub(pattern, '', info)
            cleaned_info = re.sub(r'\s+', ' ', cleaned_info)
            chars = cleaned_info.split(' ')
            chars = [c for c in chars if len(c) > 1]
            cleaned_info = ' '.join(chars)
            if len(cleaned_info) > 0:
                cleaned.append(cleaned_info)
        
        return cleaned
    
    def find_card_number(self, infos, unsigns):
        ids = [i for i,s in enumerate(unsigns) if r'so' in s.lower()]
        for i in ids:
            id_str = infos[i]
            id_str = re.sub(r'[^0-9]', '', id_str)
            if not id_str.strip():
                continue
            else:
                return id_str
        return None

    def find_card_number_new(self, infos, nospaces):
        id_card = None
        ids = [i for i,s in enumerate(nospaces) if r'so' in s.lower()]
        for i in ids:
            id_str = infos[i]
            id_str = re.sub(r'[^0-9]', '', id_str)
            if not id_str.strip():
                continue
            else:
                id_card = id_str
                break
        
        if id_card == None:
            ids = [i for i,s in enumerate(nospaces) if r'dn' in s.lower()]
            for i in [1, 2,3,4]:
                id_str = nospaces[i]
                id_str = re.sub(r'[^0-9]', '', id_str)
                if not id_str.strip():
                    continue
                else:
                    id_card = id_str
                    break
            if id_card != None:
                id_card = "dn" + id_card
        return id_card

    def find_namecard(self, nospaces, infos, unsigns):
        full_name = None
        names = [i for i,s in enumerate(nospaces) if r'hovaten' in s.lower()]
        if len(names) > 0:
            name = infos[names[0]]
            flat = unsigns[names[0]].lower()
            index = flat.index('ten')
            chars = name[index+3:].strip().split(' ')
            chars = [c for c in chars if c.isupper()]
            full_name = ' '.join(chars)
        if full_name == None:
            names = [i for i,s in enumerate(nospaces) if r'hova' in s.lower()]
            if len(names) > 0:
                name = infos[names[0]]
                flat = unsigns[names[0]].lower()
                index = flat.index('ten')
                chars = name[index+3:].strip().split(' ')
                chars = [c for c in chars if c.isupper()]
                full_name = ' '.join(chars)
        if full_name == None:
            names = [i for i,s in enumerate(nospaces) if r'vaten' in s.lower()]
            if len(names) > 0:
                name = infos[names[0]]
                flat = unsigns[names[0]].lower()
                index = flat.index('ten')
                chars = name[index+3:].strip().split(' ')
                chars = [c for c in chars if c.isupper()]
                full_name = ' '.join(chars)
        
        if full_name == None:
            names = [i for i,s in enumerate(nospaces) if r'ten' in s.lower()]
            if len(names) > 0:
                name = infos[names[0]]
                flat = unsigns[names[0]].lower()
                index = flat.index('ten')
                chars = name[index+3:].strip().split(' ')
                chars = [c for c in chars if c.isupper()]
                full_name = ' '.join(chars)

        return full_name

    def find_dob(self, nospaces, infos):
        dob_result = None
        dobs = [i for i,s in enumerate(nospaces) if r'sinh' in s.lower()]
        if len(dobs) > 0:
            dob = infos[dobs[0]]
            pattern = r"\d{2}/\d{2}/\d{4}"
            match = re.search(pattern, dob)
            if match:
                dob_result = match.group()
        
        if dob_result == None:
            dobs = [i for i,s in enumerate(nospaces) if r'ngays' in s.lower()]
            if len(dobs) > 0:
                dob = infos[dobs[0]]
                pattern = r"\d{2}/\d{2}/\d{4}"
                match = re.search(pattern, dob)
                if match:
                    dob_result = match.group()

        return dob_result

    def find_gender(self, nospaces, unsigns):
        gender_result = None
        genders = [i for i,s in enumerate(nospaces) if r'gioi' in s.lower() or r'tinh' in s.lower()]
        if len(genders) > 0:
            flat = unsigns[genders[0]].lower()
            if 'gioi' in flat:
                index = flat.index('gioi')
                tail = flat[index+5:]
            else:
                index = flat.index('tinh')
                tail = flat[index+4:]

            if 'nu' in tail:
                gender_result = r'Nữ'
            elif 'nam' in tail:
                gender_result = r'Nam'
        return gender_result
    
    def find_address(self,nospaces, infos, unsigns):
        address_result = None
        adds = [i for i,s in enumerate(nospaces) if r'diachi' in s.lower()]
        if len(adds) > 0:
            address = infos[adds[0]]
            flat = unsigns[adds[0]].lower()
            index = flat.index('dia chi')
            address_result = address[index+7:].strip()
        return address_result
    
    def find_address2(self,nospaces, infos, unsigns):
        address_result = None
        adds = [i for i,s in enumerate(nospaces) if r'kcb' in s.lower()]
        if len(adds) > 0:
            address = infos[adds[0]]
            flat = unsigns[adds[0]].lower()
            if 'bd' in flat:
                index = flat.index('bd')
                address_result = address[index+2:].strip()
            else:
                index = flat.index('kcb')
                address_result = address[index+3:].strip()
        return address_result
    
    def find_expired(self, nospaces, infos, unsigns):
        expired_result = None
        ids = [i for i,s in enumerate(nospaces) if r'sudung' in s.lower()]
        if len(ids) > 0:
            expired = infos[ids[0]]
            pattern = r"\d{2}/\d{2}/\d{4}"
            matches = re.findall(pattern, expired)
            if matches:
                expired_result = matches[-1]
        if expired_result == None:
            ids = [i for i,s in enumerate(nospaces) if r'giatri' in s.lower()]
            if len(ids) > 0:
                expired = infos[ids[0]]
                pattern = r"\d{2}/\d{2}/\d{4}"
                matches = re.findall(pattern, expired)
                if matches:
                    expired_result = matches[-1]

        if expired_result == None:
            ids = [i for i,s in enumerate(nospaces) if r'trisu' in s.lower()]
            if len(ids) > 0:
                expired = infos[ids[0]]
                pattern = r"\d{2}/\d{2}/\d{4}"
                matches = re.findall(pattern, expired)
                if matches:
                    expired_result = matches[-1]
        if expired_result == None:
            ids = [i for i,s in enumerate(nospaces) if r'tungay' in s.lower()]
            if len(ids) > 0:
                expired = infos[ids[0]]
                pattern = r"\d{2}/\d{2}/\d{4}"
                matches = re.findall(pattern, expired)
                if matches:
                    expired_result = matches[-1]
        return expired_result
        
    def find_years(self, nospaces, infos, unsigns):
        years_result = None
        ids = [i for i,s in enumerate(nospaces) if r'5nam' in s.lower()]
        if not ids:
            ids = [i for i,s in enumerate(nospaces) if r'thoidiem' in s.lower()]
        if len(ids) > 0:
            text = infos[ids[0]]
            pattern = r"\d{2}/\d{2}/\d{4}"
            matches = re.findall(pattern, text)
            if matches:
                years_result = matches[-1]
        return years_result

    def find_change_card(self, nospaces, infos, unsigns):
        change_card = None
        ids = [i for i,s in enumerate(nospaces) if r'bhyt' in s.lower()]
        if len(ids) > 0:
            text = infos[ids[0]]
            flat = unsigns[ids[0]].lower()
            index = flat.index('bhyt')
            change_card = text[index+4:].strip()
        return change_card

    def find_contents(self, infos):
        unsigns = [unidecode(s) for s in infos]
        nospaces = [re.sub(r'\s', '', s.lower()) for s in unsigns]
        output = {}

        # find card number
        id_str = self.find_card_number_new(infos, nospaces)
        output['id'] = id_str
        
        # find name
        full_name = self.find_namecard(nospaces, infos, unsigns)
        output['name'] = full_name
       
        # find dob
        dobs_result = self.find_dob( nospaces, infos)
        output['dob'] = dobs_result
        
        # find gender
        gender_result = self.find_gender(nospaces, unsigns)
        output['gender'] = gender_result

        # find expired
        expire_result = self.find_expired(nospaces, infos, unsigns)
        output['expire'] = expire_result
       
        # find 05 years
        years_result = self.find_years(nospaces, infos, unsigns)
        output['fiveyears'] = years_result
        
        return output

    def convert_cv_to_pillow(self, cv_img: np.ndarray):
        if len(cv_img.shape) > 2:
            rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        else:
            rgb_img = cv_img.copy()

        return Image.fromarray(rgb_img)

    def fix_last_name(self, name):
        fname = 'templates/common_last_name.txt'
        words = name.split()
        words[0] = unidecode(words[0]).upper()
        with open(fname, encoding="utf8") as f:
            last_name_list = f.readlines()
        last_name_list = [x.strip().upper() for x in last_name_list]
        last_name_decode = [unidecode(x) for x in last_name_list]
        if words[0] in last_name_decode:
            words[0] = last_name_list[last_name_decode.index(words[0])]
        text = ' '.join(words)
        return text
    
    def convert_output(self, output):
        converted = {
            'Số': output['id'],
            'Họ và Tên': output['name'],
            'Ngày sinh': output['dob'],
            'Giới tính': output['gender'],
            'Giá trị sử dụng': output['expire'],
            'Thời điểm đủ 05 năm liên tục': output['fiveyears']
        }

        return converted