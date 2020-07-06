import os
import argparse
import logging
import jinja2
from shutil import copytree
from config import *


logging.basicConfig(filename='report_building.log', level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s')
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_results', required=True)
    parser.add_argument('--output_dir', required=True)

    return parser.parse_args()


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


def main():
    args = parse_args()
    prepare_results_dir(args.output_dir)

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('build_report', 'report/templates'),
        autoescape=True
    )
    summary_template = env.get_template('summary_template.html')
    summary_html = summary_template.render(title='Results of RIF performance tests',
                                           text='some text')
    save_html_report(summary_html, args.output_dir, SUMMARY_REPORT_HTML)


if __name__ == '__main__':
    main()
