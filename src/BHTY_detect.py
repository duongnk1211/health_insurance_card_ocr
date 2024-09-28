import cv2
import numpy as np
from PIL import Image

def limit_size(img, limit=720):
    hei, wid = img.shape[:2]
    ratio = min(limit/wid, limit/hei)

    return cv2.resize(img, (int(ratio*wid), int(ratio*hei)))


def distance(pt1, pt2):
    return np.sqrt((pt1[0]-pt2[0])**2 + (pt1[1]-pt2[1])**2)


class CardDetection(object):
    def __init__(self, template1, template2, img_size: int, threshold: float, side_cond: float):
        self.detector = cv2.BRISK.create()
        self.matcher = cv2.BFMatcher.create(normType=cv2.NORM_HAMMING, crossCheck=True)
        self.template_old = self._init_template(template1, img_size)
        self.template_new = self._init_template(template2, img_size)
        self.threshold = threshold
        self.side_cond = side_cond
        print('Init card detector!')

    def detect(self, img: np.ndarray, template='old'):
        if template == 'old':
            template = self.template_old.copy()
        else:
            template = self.template_new.copy()
        # check the input image shape
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        # convert BGR to GRAY
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # detect keypoints and descriptors
        keypoints, descriptors = self.detector.detectAndCompute(gray, None)
        # print(f'Number of detected keypoints: {len(keypoints)}')

        # match keypoints from input and template
        matches = self.matcher.match(queryDescriptors=template['descriptors'], trainDescriptors=descriptors)
        # sort matches order to distance and limit matches
        matches = sorted(matches, key=lambda m: m.distance)
        nb_matches = int(self.threshold * len(matches))
        matches = matches[:nb_matches]
        # print(f'Number of selected matches: {nb_matches}')

        # calculate homography to estimate transform matrix
        pts = np.zeros((2, nb_matches, 2), dtype=np.float32)
        for i, m in enumerate(matches):
            pts[0, i, :] = template['keypoints'][m.queryIdx].pt
            pts[1, i, :] = keypoints[m.trainIdx].pt
        M, _ = cv2.findHomography(srcPoints=pts[1], dstPoints=pts[0], method=cv2.RANSAC)

        # verify and return
        if not self._verify_card(M, img_size=template['size']):
            return None, nb_matches
        card = cv2.warpPerspective(src=img, M=M, dsize=template['size'])

        return card, nb_matches
    
    def _verify_card(self, matrix, img_size):
        wid, hei = img_size
        # inverse matrix
        inv_M = np.linalg.pinv(matrix)
        # init coordinates (4 corners)
        dst = np.array([[[0, 0], [wid, 0], [wid, hei], [0, hei]]], dtype=np.float32)
        src = cv2.perspectiveTransform(dst, inv_M)

        # if src polygon is not convex
        if not cv2.isContourConvex(src):
            return False

        # calculate 4 sides of polygon
        tl, tr, br, bl = src[0].tolist()
        top_wid = distance(tl, tr)
        bottom_wid = distance(bl, br)
        left_hei = distance(tl, bl)
        right_hei = distance(tr, br)

        # check side length
        if min(top_wid, bottom_wid) < self.side_cond * max(top_wid, bottom_wid):
            return False
        if min(left_hei, right_hei) < self.side_cond * max(left_hei, right_hei):
            return False

        return True
    
    def _init_template(self, img: np.ndarray, img_size: int):
        # check the input shape and limit image size
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        img = limit_size(img, limit=img_size)
        im_h, im_w = img.shape[:2]

        # convert BGR to GRAY
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # detect keypoints and descriptors
        keypoints, descriptors = self.detector.detectAndCompute(gray, None)
        template = {'keypoints': keypoints, 'descriptors': descriptors, 'size': (im_w, im_h)}

        return template