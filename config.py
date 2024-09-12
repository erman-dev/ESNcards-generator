from enum import Enum
import os
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4


class Config:
    section: str = "ESN VUT Brno"
    university: str = "VUT Brno"
    imgpath: os.path = os.path.join(os.getcwd(), "pictures")
    student_csv_path: os.path = os.path.join(os.getcwd(), "students.csv")
    output: os.path = os.path.join(os.getcwd(), "output.pdf")
    casc_path: os.path = "./haarcascade_frontalface_default.xml"


class PageConfig:
    """Settings for page size and margins"""
    page_size = A4
    margin_left = 10
    margin_right = 10
    margin_top = 10
    margin_bottom = 10


class PhotoBlock:
    """Desired photo size in mm"""
    width = 26
    height = 35
    font_size = 1.5
    font = "Lato"


class TextBlock:
    """Expected max text block size in mm"""
    width = 44
    height = 32
    row_height = 7.9
    width1 = 29
    width2 = width-width1
    font_size = 8
    font = "Lato"
    # STARE ESN KARTY
    # width = 47
    # height = 27
    # row_height = 7
    # width1 = 32
    # width2 = width-width1
    # font_size = 8
    # font = "Lato"


class PrintMode(Enum):
    PHOTO_ONLY = 'photo'  # Printing only images to normal paper
    TEXT_ONLY = 'text'    # Printing only descriptions to transparent foil

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value
