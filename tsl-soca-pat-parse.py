from dataclasses import dataclass # note: requires Python 3.7 or later
from typing import Dict, List

@dataclass
class MultiVarTest:
    """
    Test with multiple results.
    """
    test_name: str
    test_desc: str
    result_value: float
    results: Dict[str, float]
    result: bool
    test_threshold: float


@dataclass
class SocaRecord:
    """
    Soca record.
    """
    bar_code: str
    test_date: str
    scan_date: str
    user: str
    result: bool
    mode: str
    dept: str
    tests: List[MultiVarTest]

        
def parse_records(file_path: str):
    with open(file_path, "r") as f:
        file = f.read()

    lines = []
    # 12 line initial header
    skip_count = 12
    for line in file.splitlines(keepends=True):
        if skip_count > 0:
            skip_count -= 1
            continue
        if "Job Report,,,,,,,,,,,,,,,,,," in line:
            skip_count = 10
            continue
        elif line.startswith(",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,"):
            continue
        elif line.startswith(",,,,,BarCode,,,,,,,,Test Date,,,,,,,,,,,,Scan Date,,,,,,Case,,,,,,,,,User,,,,,,,,,,Result,,,,,,,Mode,,,,,,,,,,Dept,,,,,"):
            continue
        lines.append(line)

    # load records
    records = []
    iter_lines = iter(lines)
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
            'test_date': header_entries[1],
            'scan_date': header_entries[2],
            'user': header_entries[3],
            'result': header_entries[4],
            'mode': header_entries[5],
            'dept': header_entries[6]
        }

        # discard header line
        next(iter_lines)

        tests = []
        while True:
            try:
                next_line = next(iter_lines)
            except StopIteration:
                break
            test_info = list(filter(None, next_line.split(',')))
            if test_info[0] in ['Contin', 'Insulation']:
                test_name = test_info[0]
                test_desc = test_info[1]
                result_value = test_info[2]
                results = []
                results.append(test_info[-1])
                while True:
                    next_line = next(iter_lines)
                    if '"' not in next_line:
                        results.append(next_line)
                    else:
                        results.append(next_line.split('"')[0])
                        next_line = next_line.split('"', 1)[1]
                        break
                test_footer = list(filter(None, next_line.split(',')))
                next_line = ""
                test_result = test_footer[0]
                test_threshold = test_footer[1]
                tests.append(
                    MultiVarTest(
                        test_name=test_name,
                        test_desc=test_desc,
                        result_value=result_value,
                        results=results,
                        result=test_result,
                        test_threshold=test_threshold,
                    )
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
        
    return records




if __name__ == "__main__":
    fpath = "soca-pat.csv"
    records = parse_records(fpath)
    from pprint import pprint
    pprint(records[1])
    print(f"{len(records)} records parsed.")
