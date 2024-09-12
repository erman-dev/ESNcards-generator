import cv2
import logging
import os
import pickle
import numpy as np

from PIL import Image, ImageFile, ExifTags, ImageOps
from io import BytesIO
from typing import List

from config import PhotoBlock

log = logging.getLogger(__name__)


class FaceDetector:
    def expand_rects(self, rects: List[List[int]]) -> List[List[int]]:
        # Expand the square around a face by some relative size to make space for the rest of the head
        # move x0 and y0 by 12.5% of the height and width
        rects[:, :2] -= (rects[:, 2:] >> 2)
        # expand the square size by 50%
        rects[:, 2:] += (rects[:, 2:] >> 1).astype(int)

        # Expand the square into a rectangle to fit the face with body.
        # Use aspect ratio computed from photo size.
        # TODO we count with height being biger than width here...
        ratio = (PhotoBlock.height / PhotoBlock.width)

        # After the expansion, eyes would be in the middle of the photo,
        # so the rectangle is moved more to the bottom than to the top.
        rects[:, 3] = (rects[:, 3] * ratio).astype(int)
        rects[:, 1] -= rects[:, 3] >> 3  # by 12.5% of the offset to the top

        # Fix negative coordinates
        # Mask only negative values and make them positive
        negCoords = np.negative(rects[:, :2] * (rects[:, :2] < 0))
        # Add negative part to the oposite coordinates
        rects[:, 2:] += negCoords
        rects[rects < 0] = 0

        return rects

    def detect_faces(self, img: cv2.typing.MatLike, cascade: cv2.CascadeClassifier, expand: bool = True) -> List[List[int]]:
        rects = cascade.detectMultiScale(
            img,
            scaleFactor=1.01,
            minNeighbors=50,
            minSize=(100, 100),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        if len(rects) == 0:
            return []

        if expand:
            rects = self.expand_rects(rects)

        # Add x and y coordinates to the width and height of the square to get second coordinates
        rects[:, 2:] += rects[:, :2]

        # Make sure the rectangle is not larger than the image
        h, w = img.shape
        rects[rects[..., 2] > w, 2] = w
        rects[rects[..., 3] > h, 3] = h

        return rects

    def crop_image(self, img: ImageFile, rect: List[int]) -> cv2.typing.MatLike:
        return img.crop(rect)

    def hist_eq_clahe(self, img: cv2.typing.MatLike) -> cv2.typing.MatLike:
        img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(2, 2))
        img_yuv[:, :, 0] = clahe.apply(img_yuv[:, :, 0])
        img_out = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
        return img_out

    def hist_eq_heq_yuv(self, img: cv2.typing.MatLike) -> cv2.typing.MatLike:
        img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
        # Histogram equalisation on the Y-channel
        img_yuv[:, :, 0] = cv2.equalizeHist(img_yuv[:, :, 0])
        img_out = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
        return img_out

    def hist_eq_heq_hsv(self, img: cv2.typing.MatLike) -> cv2.typing.MatLike:
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # Histogram equalisation on the V-channel
        img_hsv[:, :, 2] = cv2.equalizeHist(img_hsv[:, :, 2])
        img_out = cv2.cvtColor(img_hsv, cv2.COLOR_HSV2BGR)
        return img_out

    def save_image(self, img: ImageFile) -> BytesIO:
        buf = BytesIO()
        rgb_img = img.convert("RGB")
        rgb_img.save(buf, format="JPEG")
        buf.seek(0)
        return buf

    def decide_multiple_faces(self, img_path, img, rects: List[List[int]]) -> List[List[int]]:

        # Load previous decions dict
        if os.path.exists("decisions.pickle"):
            with open("decisions.pickle", "rb") as f:
                prev_decisions = pickle.load(f)
        else:
            prev_decisions = dict()

        # Return previous decion if in dict
        if img_path in prev_decisions.keys():
            decision = prev_decisions[img_path]
            log.info(
                f"Returning previous decision from database: [{decision}]")
            return rects[decision]

        # Manual decision as fallback
        # Create folder fo all of the different possible detections
        decision_folder = os.path.join(os.getcwd(), "decisions")
        if not os.path.isdir(decision_folder):
            os.makedirs(decision_folder)

        # Crop each detection and save it under index.jpg
        for idx, rect in enumerate(rects):
            crop = self.crop_image(img, rect)
            filename = os.path.join(decision_folder, f"{idx}.jpg")
            crop.save(filename)

        # Let the user choose
        selected = int(input("Picture number: "))
        for idx in range(len(rects)):
            os.remove(os.path.join(decision_folder, f"{idx}.jpg"))

        # Save the decision
        prev_decisions[img_path] = selected
        with open("decisions.pickle", "wb+") as f:
            pickle.dump(prev_decisions, f, protocol=pickle.HIGHEST_PROTOCOL)

        return rects[selected]

    def run(self) -> BytesIO:

        log.info(f"Processing '{self.img_path}'")

        # Convert to grayscale
        pil_gray = self.pil_img.convert('L')
        gray = np.array(pil_gray)
        gray = cv2.equalizeHist(gray)

        # Run facial recognition
        rects = self.detect_faces(gray, self.face_cascade)
        log.debug(f"Found {len(rects)} faces in {self.img_path}")

        if len(rects) == 0:
            return self.save_image(self.pil_img)
        elif len(rects) == 1:
            rect = rects[0]
        else:
            log.warn("Found multiple faces. Choose the right one from the folder 'decisions' and then write the number of the chosen picture here")
            rect = self.decide_multiple_faces(
                self.img_path, self.pil_img, rects)

        cropped_img = self.crop_image(self.pil_img, rect)

        return self.save_image(cropped_img)

    def __init__(self, img_path: os.path, casc_path: os.path) -> None:
        pil_img = Image.open(img_path)
        pil_img = ImageOps.exif_transpose(pil_img)
        self.pil_img = pil_img
        self.img_path = img_path
        self.face_cascade = cv2.CascadeClassifier(casc_path)
