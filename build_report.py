import os
import argparse
import logging
import jinja2
from shutil import copytree, rmtree
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
    if os.path.exists(os.path.join(output_dir, 'resources')):
        rmtree(os.path.join(output_dir, 'resources'), True)

    try:
        copytree(os.path.join('report', 'resources'),
                 os.path.join(output_dir, 'resources'))
        logger.info('Report resources were copied successfully')
    except Exception as err:
        logger.error('Fail during copying report resources: {}'.format(str(err)))


def build_summary_report(test_results):
    summary_report = {}
    summary_report['results'] = {}
    summary_report['summary'] = {
        'Tests': 0,
        'Time': 0
    }
    summary_report['summary']['statuses'] = {
    	'Passed': 0,
        'Failures': 0,
        'Errors': 0,
        'Disabled': 0
    }
    xml_reports = glob(os.path.join(test_results, XML_REPORT_PATTERN))
    for xml_report_path in xml_reports:
        with open(xml_report_path, 'r') as file:
            xml_report = file.read()
        platform_name = os.path.split(xml_report_path)[1].replace('Test-', '').split('.')[0]
        summary_report['results'][platform_name] = xmltodict.parse(xml_report)

        # make platform name more readable
        displayable_platform_name = platform_name.replace('_', ' '). replace('-', ' (') + ')'
        summary_report['results'][platform_name]['name'] = displayable_platform_name

        summary_report['summary']['statuses']['Passed'] += int(summary_report['results'][platform_name]['testsuites']['@tests']) \
        - int(summary_report['results'][platform_name]['testsuites']['@failures']) - int(summary_report['results'][platform_name]['testsuites']['@errors']) \
        - int(summary_report['results'][platform_name]['testsuites']['@disabled'])

        summary_report['summary']['statuses']['Failures'] += int(summary_report['results'][platform_name]['testsuites']['@failures'])
        summary_report['summary']['statuses']['Errors'] += int(summary_report['results'][platform_name]['testsuites']['@errors'])
        summary_report['summary']['statuses']['Disabled'] += int(summary_report['results'][platform_name]['testsuites']['@disabled'])
        summary_report['summary']['Tests'] += int(summary_report['results'][platform_name]['testsuites']['@tests'])
        summary_report['summary']['Time'] += float(summary_report['results'][platform_name]['testsuites']['@time'])
    return summary_report


def build_detailed_reports(env, summary_report, output_dir):
    detailed_summary_template = env.get_template('detailed_summary_template.html')
    for platform in summary_report['results']:
        detailed_summary_html = detailed_summary_template.render(title='Results of RIF performance tests ({})'.format(summary_report['results'][platform]['name']),
                                           report=summary_report['results'][platform])
        save_html_report(detailed_summary_html, output_dir, platform + '_detailed.html')


def main():
    args = parse_args()
    prepare_results_dir(args.output_dir)

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('build_report', 'report/templates'),
        autoescape=True
    )
    summary_report = build_summary_report(args.test_results)
    save_json_report(summary_report, args.output_dir, SUMMARY_REPORT_JSON)

    summary_template = env.get_template('summary_template.html')
    summary_html = summary_template.render(title='Results of RIF performance tests',
                                           report=summary_report)
    save_html_report(summary_html, args.output_dir, SUMMARY_REPORT_HTML)


    build_detailed_reports(env, summary_report, args.output_dir)


if __name__ == '__main__':
    main()
