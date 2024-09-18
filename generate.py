import csv
import logging
import argparse
import os

from dataclasses import dataclass
from datetime import datetime
from typing import List
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

from config import Config, PrintMode, TextBlock, PhotoBlock, PageConfig
from facedetector import FaceDetector

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

pdfmetrics.registerFont(TTFont('Lato', './fonts/Lato-Regular.ttf'))

@dataclass
class StudentInfo:
    name: str
    date_of_birth: str
    nationality: str
    today: str
    img_destination: str
    section: str = Config.section
    university: str = Config.university


class Generate:
    """Class that facilitates generation of PDFs used to
    make ESN cards. Itcan output either PDF with text details 
    or with pohtos of the students."""

    students: List[StudentInfo] = list()
    args: argparse.Namespace

    def parse_arguments(self):
        """Load arguments from CLI"""
        parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('-i', '--imgpath', default=Config.imgpath,
                            help=f'Folder with images to be processed.')
        parser.add_argument('-p', '--csv',
                            dest="student_csv_path",
                            default=Config.student_csv_path,
                            help=f'CSV file with students and their details.')
        parser.add_argument('-o', '--output',
                            help=f'Output PDF file')
        parser.add_argument('-m', '--mode',
                            type=PrintMode, choices=list(PrintMode),
                            default=PrintMode.TEXT_ONLY,
                            help=f'Printing mode - text or images')
        return parser.parse_args()

    def __init__(self):
        """Main run of the program"""
        self.args = self.parse_arguments()
        self.students = self.load_students(self.args.student_csv_path)
        log.info(f"Loaded {len(self.students)} from csv file")
        date = datetime.now()

        if self.args.mode == PrintMode.TEXT_ONLY:
            filename = f"output-text-{date.strftime('%y_%m_%d_%H_%M')}.pdf"
            filepath = os.path.join(os.getcwd(), "output", filename)
            self.create_text_pdf(filepath)

        elif self.args.mode == PrintMode.PHOTO_ONLY:
            filename = f"output-photo-{date.strftime('%y_%m_%d_%H_%M')}.pdf"
            filepath = os.path.join(os.getcwd(), "output", filename)
            self.create_photo_pdf(filepath)


        log.info("Created PDF file with mode "
                 f"{self.args.mode} at {self.args.output}")

    def load_students(self, csv_path: str) -> List[StudentInfo]:
        """Loads processed data from intermediary students.cv file,
        this file was generated dy download_photos.py"""
        with open(csv_path, "r") as f:
            csv_reader = csv.reader(f)
            students = [StudentInfo(*line) for line in csv_reader]
        return students

    def generate_text_subtable(self, si: StudentInfo) -> Table:
        """Generates contents of single cell in a table used in text mode."""
        table_data = [[si.name, ""],
                      [si.nationality, si.date_of_birth],
                      [si.university, ""],
                      [si.section, si.today]]
        table = Table(table_data,
                      colWidths=(TextBlock.width1*mm, TextBlock.width2*mm),
                      rowHeights=[TextBlock.row_height*mm]*4)
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), TextBlock.font),
            ("FONTSIZE", (0, 0), (-1, -1), TextBlock.font_size),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0.5*mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0.5*mm)
        ]))
        return table

    def generate_photo_subtable(self, si: StudentInfo) -> Table:
        """Generates contents of single cell in a table used in photo mode."""
        img_detector = FaceDetector(si.img_destination, Config.casc_path)
        img_cropped = img_detector.run()
        img = Image(img_cropped,
                    width=PhotoBlock.width*mm,
                    height=PhotoBlock.height*mm)
        table_data = [[img], [f"{si.name}"]]
        table = Table(table_data,
                      colWidths=(PhotoBlock.width*mm),
                      rowHeights=[PhotoBlock.height*mm, 2*mm])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), PhotoBlock.font),
            ("FONTSIZE", (0, 0), (-1, -1), PhotoBlock.font_size*mm),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER")
        ]))
        return table

    def generate_text_table(self, students: List[StudentInfo]) -> List[Table]:
        """Generates data used to build table in text mode"""
        table_data = list()
        for student in students:
            table_data.append(self.generate_text_subtable(student))
        return table_data

    def generate_photo_table(self, students: List[StudentInfo]) -> List[Table]:
        """Generates data used to build table in photo mode"""
        table_data = list()
        for student in students:
            table_data.append(self.generate_photo_subtable(student))
        return table_data

    def create_text_pdf(self, output_path: os.path) -> None:
        """Generates a PDF when in text mode"""
        doc = SimpleDocTemplate(output_path,
                                pagesize=PageConfig.page_size,
                                leftMargin=PageConfig.margin_left,
                                rightMargin=PageConfig.margin_right,
                                topMargin=PageConfig.margin_top,
                                bottomMargin=PageConfig.margin_bottom)

        table_data = self.generate_text_table(self.students)

        # Number of columns that can fir in 210mm
        num_columns = 210 // TextBlock.width
        table_matrix = [table_data[i:i + num_columns]
                        for i in range(0, len(table_data), num_columns)]

        col_widths = [TextBlock.width * mm] * num_columns
        row_heights = [TextBlock.height * mm] * len(table_matrix)

        main_table = Table(table_matrix,
                           colWidths=col_widths,
                           rowHeights=row_heights)
        main_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("TOPPADDING", (0, 0), (-1, -1), 1*mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1*mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 1*mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1*mm),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        doc.build([main_table])

    def create_photo_pdf(self, output_path: os.path) -> None:
        """Generates a PDF when in photo mode"""
        doc = SimpleDocTemplate(output_path,
                                pagesize=PageConfig.page_size,
                                leftMargin=PageConfig.margin_left,
                                rightMargin=PageConfig.margin_right,
                                topMargin=PageConfig.margin_top,
                                bottomMargin=PageConfig.margin_bottom)

        table_data = self.generate_photo_table(self.students)

        # Number of columns that can fir in 210mm
        num_columns = 210 // (PhotoBlock.width+1)
        table_matrix = [table_data[i:i + num_columns]
                        for i in range(0, len(table_data), num_columns)]

        col_widths = [(PhotoBlock.width + 2) * mm] * num_columns
        row_heights = [(PhotoBlock.height + 4) * mm] * len(table_matrix)

        main_table = Table(table_matrix,
                           colWidths=col_widths,
                           rowHeights=row_heights)
        main_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("TOPPADDING", (0, 0), (-1, -1), 1*mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1*mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 1*mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1*mm),
        ]))
        doc.build([main_table])


if __name__ == "__main__":
    Generate()
