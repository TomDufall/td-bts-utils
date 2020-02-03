from dataclasses import dataclass # note: requires Python 3.7 or later
from datetime import datetime
from typing import Dict, List


WEEKDAY_DATETIME_FORMAT = "%d-%m-%y %a %H:%M"

@dataclass
class MultiVarTest:
    """
    Test with multiple results.
    """
    name: str
    description: str
    result_value: float
    results: Dict[str, float]
    result: str
    threshold: float

    def get_result(self, index: int) -> float:
        i = "{:03d}".format(index)
        return self.results.get(i)

    @property
    def is_pass(self) -> bool:
        if self.result == "PASS":
            return True
        return False


@dataclass
class SocaRecord:
    """
    Soca record.
    """
    bar_code: str
    test_date: datetime
    scan_date: datetime
    user: str
    result: str
    mode: str
    dept: str
    tests: Dict[str, MultiVarTest]

    @property
    def is_pass(self) -> bool:
        if self.result == "PASS":
            return True
        return False


@dataclass
class SocaPatJob:
    """
    Structure for the job report export from the soca PAT tester.
    """
    company: str
    print_date: datetime
    job_code: str
    description: str
    create_date: datetime
    load_date: datetime
    client: str
    records: List[SocaRecord]


def parse_records(file_path: str) -> SocaPatJob:
    job_dict = {}

    with open(file_path, "r") as f:
        file = f.read()

    lines = []
    skip_count = 0
    start = True

    for line in file.splitlines(keepends=True):
        if skip_count > 0:
            skip_count -= 1
            continue
        if "Job Report,,,,,,,,,,,,,,,,,," in line:
            if start == True:
                start = False
            else:
                skip_count = 10
            continue
        elif line.startswith(",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,"):
            continue
        elif line.startswith(",,,,,BarCode,,,,,,,,Test Date,,,,,,,,,,,,Scan Date,,,,,,Case,,,,,,,,,User,,,,,,,,,,Result,,,,,,,Mode,,,,,,,,,,Dept,,,,,"):
            continue
        lines.append(line)

    iter_lines = iter(lines)

    # extract job info from initial header
    job_dict['company'] = \
        list(filter(None, next(iter_lines).split(",")))[0].split(' : ', 1)[1]
    print_date_str = list(filter(None, next(iter_lines).split(",")))[1]
    job_dict['print_date'] = datetime.strptime(
        print_date_str, "Printed on %d/%m/%Y  at  %H:%M:%S"
    )
    next(iter_lines)
    job_header = next(iter_lines).split(",")
    job_dict['job_code'] = job_header[3]
    job_dict['description'] = job_header[10]
    job_dict['create_date'] = datetime.strptime(job_header[37], "%d/%m/%Y %H:%M")
    job_dict['load_date'] = datetime.strptime(job_header[47], "%d %b %Y %H:%M")
    job_dict['client'] = job_header[67]

    # load records
    records = []
    next_line = ""
    while True:
        if next_line:
            header_str = next_line
            next_line = ""
        else:
            try:
                header_str = next(iter_lines)
            except StopIteration:
                break

        if 'BTS' not in header_str:
            continue
        header_entries = list(filter(None, header_str.split(",")))
        headers = {
            'bar_code': header_entries[0],
            'test_date': datetime.strptime(
                header_entries[1], WEEKDAY_DATETIME_FORMAT
            ),
            'scan_date': datetime.strptime(
                header_entries[2], WEEKDAY_DATETIME_FORMAT
            ),
            'user': header_entries[3],
            'result': header_entries[4],
            'mode': header_entries[5],
            'dept': header_entries[6]
        }

        # discard header line
        next(iter_lines)

        tests = {}
        while True:
            try:
                next_line = next(iter_lines)
            except StopIteration:
                break
            test_info = list(filter(None, next_line.split(',')))
            if test_info[0] in ['Contin', 'Insulation']:
                name = test_info[0]
                description = test_info[1]
                result_value = float(test_info[2])
                result_strings = []
                result_strings.append(test_info[-1].strip('"'))
                while True:
                    next_line = next(iter_lines)
                    if '"' not in next_line:
                        result_strings.append(next_line)
                    else:
                        result_strings.append(next_line.split('"')[0])
                        next_line = next_line.split('"', 1)[1]
                        break
                results = {}
                for item in result_strings:
                    key, value = item.split(" : ")
                    results[key] = float(value)
                test_footer = list(filter(None, next_line.split(',')))
                next_line = ""
                test_result = test_footer[0]
                test_threshold = float(test_footer[1])
                tests[name] = MultiVarTest(
                    name=name,
                    description=description,
                    result_value=result_value,
                    results=results,
                    result=test_result,
                    threshold=test_threshold,
                )
                next_line = ""
            else:
                break

        records.append(
            SocaRecord(
                **headers,
                tests=tests,
            )
        )

    result = SocaPatJob(**job_dict, records=records)
    print(f"{len(result.records)} records parsed.")
    return result


if __name__ == "__main__":
    fpath = "soca-pat.csv"
    job = parse_records(fpath)
