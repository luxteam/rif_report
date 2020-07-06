import os
import argparse
import logging
import jinja2
from shutil import copytree
from config import *
from glob import glob
import xmltodict
import json


logging.basicConfig(filename='report_building.log', level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s')
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_results', required=True)
    parser.add_argument('--output_dir', required=True)

    return parser.parse_args()


def save_json_report(report, output_dir, file_name):
    with open(os.path.abspath(os.path.join(output_dir, file_name)), "w", encoding='utf8') as file:
        json.dump(report, file, indent=4, sort_keys=True)            


def save_html_report(report, output_dir, file_name):
    with open(os.path.abspath(os.path.join(output_dir, file_name)), 'w', encoding='utf8') as file:
        file.write(report)


def prepare_results_dir(output_dir):
    try:
        copytree(os.path.join('report', 'resources'),
                 os.path.join(output_dir, 'resources'))
        logger.info('Report resources were copied successfully')
    except Exception as err:
        logger.error('Fail during copying report resources: {}'.format(str(err)))


def build_summary_template(test_results):
    summary_report = {}
    xml_reports = glob(os.path.join(test_results, XML_REPORT_PATTERN))
    for xml_report_path in xml_reports:
        with open(xml_report_path, 'r') as file:
            xml_report = file.read()
        platform_name = os.path.split(xml_report_path)[1].replace('Test-', '').split('.')[0]
        summary_report[platform_name] = xmltodict.parse(xml_report)
    return summary_report


def main():
    args = parse_args()
    prepare_results_dir(args.output_dir)

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('build_report', 'report/templates'),
        autoescape=True
    )
    summary_report = build_summary_template(args.test_results)
    save_json_report(summary_report, args.output_dir, SUMMARY_REPORT_JSON)

    summary_template = env.get_template('summary_template.html')
    summary_html = summary_template.render(title='Results of RIF performance tests',
                                           text='some text')
    save_html_report(summary_html, args.output_dir, SUMMARY_REPORT_HTML)


if __name__ == '__main__':
    main()
