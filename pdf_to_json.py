import fitz
import pdfplumber
import yaml
import json
import re
import sys
from pathlib import Path


def load_config(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def extract_text(page):
    return page.get_text()


def validate_page(title, expected_title):
    return expected_title.lower() in title.lower()


def extract_tables(pdf_path, page_number):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number]
        tables = page.extract_tables()
        return tables


def process(pdf_path, config):
    doc = fitz.open(pdf_path)
    result = {"pages": []}
    issues = []

    for i, page in enumerate(doc):
        text = extract_text(page)
        page_result = {"page": i+1, "text": text}

        # PAGE 1 DATE
        if i == 0:
            pattern = config['pages']['page1']['pattern']
            match = re.search(pattern, text)
            if match:
                page_result['date'] = match.group()
            else:
                issues.append(f"Page 1: date not found")

        # PAGE 3-4
        if i in [2,3]:
            expected = config['pages']['page3_4']['title']
            if not validate_page(text, expected):
                issues.append(f"Page {i+1}: title mismatch")

            tables = extract_tables(pdf_path, i)
            page_result['tables'] = tables

        # PAGE 5
        if i == 4:
            expected = config['pages']['page5']['title']
            if not validate_page(text, expected):
                issues.append("Page 5: title mismatch")
            tables = extract_tables(pdf_path, i)
            page_result['tables'] = tables

        # PAGE 7
        if i == 6:
            page_result['full_text_included'] = True

        # PAGE 8
        if i == 7:
            page_result['legend_expected'] = True

        result['pages'].append(page_result)

    result['validation_issues'] = issues
    return result


if __name__ == '__main__':
    pdf_path = sys.argv[1]
    config_path = sys.argv[2]
    output = sys.argv[3]

    config = load_config(config_path)
    result = process(pdf_path, config)

    with open(output, 'w') as f:
        json.dump(result, f, indent=2)

    if result['validation_issues']:
        print("VALIDATION FAILED:")
        for issue in result['validation_issues']:
            print("-", issue)
    else:
        print("VALIDATION PASSED")
