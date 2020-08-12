import os
import argparse
import logging
import jinja2
from shutil import copytree, rmtree
from config import *
from glob import glob
import xmltodict
import json
import csv
import re


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


def get_displayable_platform_name(platform_name):
    return platform_name.replace('_', ' '). replace('-', ' (') + ')'


def build_summary_report(test_results):
    summary_report = {}
    summary_report['results'] = {}
    summary_report['summary'] = {
        'Tests': 0,
        'Time': 0
    }
    summary_report['summary']['statuses'] = {
    	'Passed': 0,
        'Failed': 0,
        'Error': 0,
        'Skipped': 0
    }
    xml_reports = glob(os.path.join(test_results, XML_REPORT_PATTERN))
    for xml_report_path in xml_reports:
        with open(xml_report_path, 'r') as file:
            xml_report = file.read()
        platform_name = os.path.split(xml_report_path)[1].replace('Test-', '').split('.')[0]
        summary_report['results'][platform_name] = xmltodict.parse(xml_report)

        for testcase in summary_report['results'][platform_name]['testsuites']['testsuite']['testcase']:
            if 'error' in testcase:
                testcase['status'] = 'error'
            elif 'failure' in testcase:
                testcase['status'] = 'failure'
            elif testcase['@result'] == 'suppressed':
                testcase['status'] = 'skipped'
            else:
                testcase['status'] = 'passed'

        # make platform name more readable
        displayable_platform_name = get_displayable_platform_name(platform_name)
        summary_report['results'][platform_name]['name'] = displayable_platform_name

        summary_report['summary']['statuses']['Passed'] += int(summary_report['results'][platform_name]['testsuites']['@tests']) \
        - int(summary_report['results'][platform_name]['testsuites']['@failures']) - int(summary_report['results'][platform_name]['testsuites']['@errors']) \
        - int(summary_report['results'][platform_name]['testsuites']['@disabled'])

        summary_report['summary']['statuses']['Failed'] += int(summary_report['results'][platform_name]['testsuites']['@failures'])
        summary_report['summary']['statuses']['Error'] += int(summary_report['results'][platform_name]['testsuites']['@errors'])
        summary_report['summary']['statuses']['Skipped'] += int(summary_report['results'][platform_name]['testsuites']['@disabled'])
        summary_report['summary']['Tests'] += int(summary_report['results'][platform_name]['testsuites']['@tests'])
        summary_report['summary']['Time'] += float(summary_report['results'][platform_name]['testsuites']['@time'])
    return summary_report


def build_detailed_reports(env, summary_report, output_dir):
    detailed_summary_template = env.get_template('detailed_summary_template.html')
    for platform in summary_report['results']:
        testgroup_duration = 0
        testcases_json = glob(os.path.join(output_dir, platform, '*.json'))
        for testcase_json in testcases_json:
            with open(testcase_json, 'r') as file:
                testcase_data = json.load(file)
            for testcase in summary_report['results'][platform]['testsuites']['testsuite']['testcase']:
                if os.path.split(testcase_json)[1].replace('.json', '') in testcase['@name']:
                    testcase['@time'] = testcase_data['summary_duration']
            testgroup_duration += testcase_data['summary_duration']
        summary_report['results'][platform]['testsuites']['@time'] = testgroup_duration
        detailed_summary_html = detailed_summary_template.render(title='Results of RIF performance tests ({})'.format(summary_report['results'][platform]['name']),
                                           report=summary_report['results'][platform]['testsuites']['testsuite'], platform_name=platform)
        save_html_report(detailed_summary_html, output_dir, DETAILED_REPORT_HTML.format(platform))


def build_testcase_reports(env, test_results, output_dir):
    testcase_template = env.get_template('testcase_template.html')
    logs = glob(os.path.join(test_results, CSV_FILE_PATTERN))
    for log in logs:
        platform_name = os.path.split(log)[1].replace('Test-', '').replace('.csv', '')
        platform_dir = os.path.join(output_dir, platform_name)
        if not os.path.exists(platform_dir):
            os.makedirs(platform_dir)
        with open(log) as file:
            lines = file.readlines()
        csv_lines = []
        for line in lines:
            # delete new line symbol and ; at the end
            line = line[0:-2]
            # replace spaces after column name or value
            line = re.sub(r'\s*;', ';', line)
            line = re.sub(r'\s*$', '', line)
            # if it isn't title with testcase name before next csv
            if len(line.split(';')) != 1:
                csv_lines.append(line)
            else:
                # check that it isn't first testcase
                if len(csv_lines) != 0:
                    # check that current testcase has some csv data
                    if len(csv_lines) != 1:
                        generate_testcase_reports(csv_lines, testcase_template, platform_dir, testcase_name, platform_name)
                    csv_lines.clear()
                testcase_name = line.replace(';', '')
    generate_testcase_reports(csv_lines, testcase_template, platform_dir, testcase_name, platform_name)


def generate_testcase_reports(csv_lines, testcase_template, platform_dir, testcase_name, platform_name):
    csv_reader = csv.DictReader(csv_lines, delimiter=';')
    converted_csv = { 'data': [ row for row in csv_reader ] }
    test_group_duration = 0
    for row in converted_csv['data']:
        for key, value in row.items():
            if 'Time' in key:
                test_group_duration += float(value)
                break
    converted_csv['summary_duration'] = test_group_duration
    testcase_html = testcase_template.render(
        title='{testcase} testcase details ({platform})'.format(testcase=testcase_name, platform=get_displayable_platform_name(platform_name)), 
        data=converted_csv
    )
    save_json_report(converted_csv, platform_dir, TESTCASE_REPORT_JSON.format(testcase_name))
    save_html_report(testcase_html, platform_dir, TESTCASE_REPORT_HTML.format(testcase_name))


def main():
    args = parse_args()
    prepare_results_dir(args.output_dir)

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('build_report', 'report/templates'),
        autoescape=True
    )
    build_testcase_reports(env, args.test_results, args.output_dir)
    summary_report = build_summary_report(args.test_results)

    build_detailed_reports(env, summary_report, args.output_dir)

    save_json_report(summary_report, args.output_dir, SUMMARY_REPORT_JSON)

    summary_template = env.get_template('summary_template.html')
    summary_html = summary_template.render(title='Results of RIF performance tests',
                                           report=summary_report)
    save_html_report(summary_html, args.output_dir, SUMMARY_REPORT_HTML)


if __name__ == '__main__':
    main()
