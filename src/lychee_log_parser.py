#!/usr/bin/env python3

import argparse
import json
import logging
import os

# Error codes treated as an error 404..407 409..417 421..428 431 451
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
ENDC = '\033[0m'


class LycheeLogParser():
    def __init__(self):
        """
        Method initialize logger and parse input parameters.

        Raises:
            - SystemExit: Exits the program with status code 2 if invalid input
              parameters or log file path are detected.
        """
        self._error_codes = []
        description = (
            "Tool used to analyze Lychee link checker logs. Evaluates whether "
            "the problems detected by lychee are actual site or "
            "server problems."
        )
        self.create_input_parser(description)
        self._args = self._args_parser.parse_args()
        self.logger_setup(verbose=self._args.verbose)

        for code in self._args.error_codes:
            if ".." in code:
                try:
                    start, end = map(int, code.split(".."))
                    new_codes = range(start, end + 1)
                except ValueError:
                    self.log.error("Invalid input parameters!")
                    self._args_parser.print_help()
                    exit(2)
            else:
                try:
                    new_codes = [int(code)]
                except ValueError:
                    self.log.error("Invalid input parameters!")
                    self._args_parser.print_help()
                    exit(2)
            for new_code in new_codes:
                if new_code not in self._error_codes:
                    self._error_codes.append(new_code)

        self.log_path = os.path.join(os.getcwd(), self._args.log_path)
        if not os.path.exists(self.log_path):
            self.log.error("Check the path of the lychee log file!")
            self._args_parser.print_help()
            exit(2)

        self.log.debug(f"Error codes: {self._error_codes}")
        self.log.debug(f"Lychee log path: {self.log_path}")

    def create_input_parser(self, description: str):
        """
        Create input parameters parser.

        Args:
            description (str): Information about what the program does

        Returns:
            self.args (parser): parser handler
        """
        parser = argparse.ArgumentParser(description=description)
        parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Increase logs verbosity level"
        )
        parser.add_argument(
            "-t",
            "--ignore-timeouts",
            action="store_true",
            help="Ignore timeouts"
        )
        parser.add_argument(
            "-n",
            "--ignore-nocode-net-err",
            action="store_true",
            help="Ignore network errors without status codes"
        )
        parser.add_argument(
            "error_codes",
            type=str,
            nargs="+",
            help=("error codes that trigger failure, in the form of an "
                  "integer, a list of integers, or a range (e.g., 10..200) "
                  "Example: 503 400..404 999")
        )
        parser.add_argument(
            "-l",
            "--log-path",
            type=str,
            default="log.json",
            help="Relative path to the lychee json log file."
        )
        self._args_parser = parser

    def logger_setup(self, verbose=False):
        """
        Create logger based on the verbosity level.

        Args:
            verbose (bool): If True, set the logging level to DEBUG; otherwise
            set it to INFO.

        Returns:
            self.log (logger): logger handler
        """
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.log = logging.getLogger(__name__)

    def lychee_log_analyser(self):
        """
        Analyzes a Lychee log file, identifies and logs broken links along with
        relevant details.

        This method reads a Lychee log file in JSON format, extracts
        information about broken links, and logs the details. It categorizes
        broken links based on different criteria such as error codes, timeout,
        network errors, etc.

        Parameters:
        - self: Instance of the LycheeLogAnalyser class.

        Raises:
        - SystemExit: Exits the program with status code 0 if no broken links
          are found; otherwise, exits with status code 1.
        """
        broken_files = {}
        suggestions_for_files = {}
        github_job_summary = []
        # Complete list of broken urls
        broken_urls = []
        with open(self.log_path, "r") as log:
            json_log = json.load(log)

        if not json_log["fail_map"]:
            self.log.info("No links broken. Exiting...")
            exit(0)

        for file, error_data in json_log["fail_map"].items():
            # List of broken urls in a single file
            broken_links = []
            for error in error_data:
                faulty_link = error["url"]
                status_info = error["status"]["text"]
                try:
                    status_code = error["status"]["code"]
                except KeyError:
                    status_code = None
                try:
                    status_details = error["status"]["details"]
                except KeyError:
                    status_details = None

                if status_info == "Timeout" and self._args.ignore_timeouts:
                    continue

                if status_code and status_code in self._error_codes:
                    broken_urls.append(faulty_link)
                    broken_links.append(
                        {faulty_link: (status_info, status_code)}
                    )
                    continue

                if ("Cached" in status_info):
                    continue

                if ("Network error" in status_info and
                        self._args.ignore_nocode_net_err):
                    continue

                if not status_details:
                    broken_urls.append(faulty_link)
                    broken_links.append({faulty_link: (status_info, None)})
                    continue

                broken_urls.append(faulty_link)
                broken_links.append(
                    {faulty_link: (status_info, status_details)}
                )

            if broken_links:
                broken_files.update({file: broken_links})

        if not broken_files:
            self.log.info(f"{GREEN}{BOLD}No links broken. Exiting...{ENDC}")
            github_job_summary.append("# :heavy_check_mark: No links broken.")
            with open("github_job_summary.md", "w") as summary:
                summary.writelines(github_job_summary)
            exit(0)

        github_job_summary.append(
            "# :x:  Broken links found!\n"
        )
        self.log.error(f"{RED}Broken links found!{ENDC}")
        for file, broken_links in broken_files.items():
            github_job_summary.append("\n---\n\n")
            github_job_summary.append(f'## Broken links in "{file}"\n\n')
            self.log.error("---")
            self.log.error(f'{RED}{BOLD}Broken links in "{file}":{ENDC}')
            for error in broken_links:
                self.log.error("---")
                url = list(error)[0]
                info, details = error[url]
                github_job_summary.append(f"Broken link: **<{url}>**\n")
                self.log.error(f"{RED}Broken link: {url}{ENDC}")
                if details:
                    self.log.error(f"{RED}{info}: {details}{ENDC}")
                else:
                    self.log.error(f"{RED}{info}{ENDC}")
        github_job_summary.append("\n---\n")
        self.log.error("---")

        if not json_log["suggestion_map"]:
            with open("github_job_summary.md", "w") as summary:
                summary.writelines(github_job_summary)
            exit(1)

        for file, broken_links in json_log["suggestion_map"].items():
            suggestions = []
            for suggestion in broken_links:
                if suggestion["original"] not in broken_urls:
                    continue
                suggestions.append((suggestion["original"],
                                   suggestion["suggestion"]))
            if suggestions:
                suggestions_for_files.update({file: suggestions})

        if not suggestions_for_files:
            with open("github_job_summary.md", "w") as summary:
                summary.writelines(github_job_summary)
            exit(1)

        github_job_summary.append("\n## :bulb: Fix Suggestions\n\n")
        suggestion_description = (
            "Check if broken URL server is expired. "
            "If it's no longer available, you can fix "
            "broken links using the suggestions below:"
        )
        github_job_summary.append(f"{suggestion_description}\n")
        github_job_summary.append("\n---\n")
        self.log.info(suggestion_description)
        self.log.info("---")

        for file, fix_suggestions in suggestions_for_files.items():
            github_job_summary.append(f'\n## Suggestions for the "{file}"\n\n')
            self.log.info(f'Suggestions for the "{file}"')
            self.log.info("---")
            for suggestion in fix_suggestions:
                url_origin, url_suggestion = suggestion
                github_job_summary.append(f"{url_origin} - {url_suggestion}\n")
                self.log.info(
                    f"{BOLD}{RED}{url_origin} - {GREEN}{url_suggestion}{ENDC}"
                )
            github_job_summary.append("\n---\n")
            self.log.info("---")

        with open("github_job_summary.md", "w") as summary:
            summary.writelines(github_job_summary)
        exit(1)


if __name__ == "__main__":
    lychee_log_parse = LycheeLogParser()
    lychee_log_parse.lychee_log_analyser()
