# coding=utf-8
import os
import json, time
import threading
import cv2
import numpy as np
from PIL import Image
from PyQt5 import QtGui
from PyQt5.QtWidgets import QLabel, QSizePolicy
from qt_thread_updater import get_updater
from src import config as co
from src.BHTY_detect import CardDetection
from src.BHYT_ocr import CardInfoExtractor

class Main:
    def __init__(self, MainGUI):
        self.MainGUI = MainGUI
        self.camera = None
        self.image = None
        self.ret = False
        self.start_camera = True
        self.template1 = cv2.imread('templates/old-form-template.png', cv2.IMREAD_COLOR)
        self.template2 = cv2.imread('templates/new-form-template.png', cv2.IMREAD_COLOR)
        self.detector = CardDetection(template1=self.template1, template2=self.template2, img_size=720, threshold=0.2, side_cond=0.2)
        self.extactor = CardInfoExtractor(oem=2, psm=6)

    def img_cv_2_qt(self, img_cv):
        height, width, channel = img_cv.shape
        bytes_per_line = channel * width
        img_qt = QtGui.QImage(img_cv, width, height, bytes_per_line, QtGui.QImage.Format_RGB888).rgbSwapped()
        return QtGui.QPixmap.fromImage(img_qt)
    
    def auto_camera(self):
        self.camera = cv2.VideoCapture(co.CAMERA_DEVICE) 
        self.ret, frame = self.camera.read()
        self.start_camera = True
        while self.ret and self.start_camera:
            try:
                ret, frame = self.camera.read()
                if ret:
                    self.image = frame.copy()
                    get_updater().call_latest(self.MainGUI.label_Image.setPixmap, self.img_cv_2_qt(frame))
            except Exception as e:
                print("Bug: ", e)

    def capture_image(self):
        if self.image is not None and self.ret and self.start_camera:
            image = self.image.copy()
            self.tesseract_ocr_vn(image)
            self.close_camera()
            get_updater().call_latest(self.MainGUI.label_Image.setPixmap, self.img_cv_2_qt(image))
        else:
            self.MainGUI.MessageBox_signal.emit("Không tìm thấy Camera/Video !", "error")
    
    def manual_image(self, image_file):
        image = cv2.imread(image_file)
        self.tesseract_ocr_vn(image)
        get_updater().call_latest(self.MainGUI.label_Image.setPixmap, self.img_cv_2_qt(image))

    def tesseract_ocr_vn(self,image):
        card_new, nb_matches_new= self.detector.detect(image, template='new')
        card_old, nb_matches_old= self.detector.detect(image, template='old')
        
        if card_new is not None:
            contents_new = self.extactor.extract(card_new)
            
        if card_old is not None:
            contents_old = self.extactor.extract(card_old)

        if card_new is not None and card_old is None:
            self.MainGUI.text_resutl.clear()
            for k,v in contents_new.items():
                if k=="Giá trị sử dụng" and v is None:
                    continue
                if k=="Thời điểm đủ 05 năm liên tục" and v is None:
                    continue
                self.MainGUI.text_resutl.insertPlainText(f'{k}: {v} \n')
                if k=="Giá trị sử dụng" and v is not None:
                    break
                
        elif card_new is None and card_old is not None:
            self.MainGUI.text_resutl.clear()
            for k,v in contents_old.items():
                if k=="Giá trị sử dụng" and v is None:
                    continue
                if k=="Thời điểm đủ 05 năm liên tục" and v is None:
                    continue
                self.MainGUI.text_resutl.insertPlainText(f'{k}: {v} \n')
                if k=="Giá trị sử dụng" and v is not None:
                    break
                 
        elif card_new is not None and card_old is not None:
            self.MainGUI.text_resutl.clear()
            for (k0,v0), (k1,v1) in zip(contents_new.items(), contents_old.items()):
                if k0=="Giá trị sử dụng" and v0 is None and v1 is None:
                    continue
                if k0=="Thời điểm đủ 05 năm liên tục" and v0 is None and v1 is None:
                    continue
                
                v = v0 if (v0 is not None and v1 is None) else v1 if (v0 is None and v1 is not None) else None
                if v0 is not None and v1 is not None:
                    if nb_matches_new > nb_matches_old:
                        v = v0
                    else:
                        v = v1
                if v is not None:
                    self.MainGUI.text_resutl.insertPlainText(f'{k1}: {v} \n')
                if k1=="Giá trị sử dụng" and v is not None:
                    break         
        else:
            self.MainGUI.MessageBox_signal.emit("Không tìm thấy thẻ!", "error")

    def close_camera(self):
        try:
            self.start_camera = False
            time.sleep(0.5)
            if self.ret:
                self.camera.release()
            self.camera = None
            self.ret = False
        except Exception as e:
                print("Bug: ", e)
