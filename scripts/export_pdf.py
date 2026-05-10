#!/usr/bin/env python3
"""Export docx to PDF via Word COM automation with optimal settings."""

import os
import sys

BASE = r'E:\Desktop\高校机器人创意大赛'
DOCX_PATH = os.path.join(BASE, '创意赛技术文档.docx')
PDF_PATH = os.path.join(BASE, '创意赛技术文档.pdf')

# Normalize paths for Windows
docx_abs = os.path.abspath(DOCX_PATH)
pdf_abs = os.path.abspath(PDF_PATH)

import win32com.client

word = win32com.client.Dispatch('Word.Application')
word.Visible = False
word.DisplayAlerts = 0

try:
    print(f'Opening: {docx_abs}')
    doc = word.Documents.Open(docx_abs)

    # Ensure all fields are updated (TOC, etc.)
    doc.Fields.Update()

    # Export as PDF with optimized settings
    doc.ExportAsFixedFormat(
        OutputFileName=pdf_abs,
        ExportFormat=17,  # wdExportFormatPDF
        OpenAfterExport=False,
        OptimizeFor=0,    # wdExportOptimizeForPrint (0=print, 1=onScreen)
        Range=0,          # wdExportAllDocument
        Item=0,           # wdExportDocumentContent
        IncludeDocProps=True,
        KeepIRM=True,
        CreateBookmarks=0,  # wdExportCreateHeadingBookmarks — creates PDF bookmarks from headings
        DocStructureTags=True,
        BitmapMissingFonts=True,
        UseISO19005_1=False,  # PDF/A — off, keeps smaller file
    )

    size_mb = os.path.getsize(pdf_abs) / 1024 / 1024
    print(f'Exported: {pdf_abs} ({size_mb:.1f} MB)')

finally:
    doc.Close(SaveChanges=0)
    word.Quit()
    print('Done.')
