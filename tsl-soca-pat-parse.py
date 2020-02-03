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
    continuity: MultiVarTest
    insulation: MultiVarTest

        
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
    while True:
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

        # contin
        test_info = list(filter(None, next(iter_lines).split(',')))
        if test_info[0] == 'Contin':
            contin_result_value = test_info[2]
            contin_results = []
            contin_results.append(test_info[-1])
            while True:
                test_result = list(filter(None, next(iter_lines).split(',')))
                if len(test_result) == 1:
                    contin_results.append(test_result[0])
                else:
                    contin_results.append(test_result[0])
                    test_info = test_result[1:]
                    break
            contin_result = test_info[0]
            contin_threshold = test_info[1]
            continuity_test = MultiVarTest(
                test_name='Contin',
                test_desc='Continuity Test',
                result_value=contin_result_value,
                results=contin_results,
                result=contin_result,
                test_threshold=contin_threshold,
            )
        else:
            continuity_test = None

        # ins
        test_info = list(filter(None, next(iter_lines).split(',')))
        if test_info[0] == 'Insulation':
            ins_result_value = test_info[2]
            ins_results = []
            ins_results.append(test_info[-1])
            while True:
                test_result = list(filter(None, next(iter_lines).split(',')))
                if len(test_result) == 1:
                    ins_results.append(test_result[0])
                else:
                    ins_results.append(test_result[0])
                    test_info = test_result[1:]
                    break
            ins_result = test_info[0]
            ins_threshold = test_info[1]
            ins_test = MultiVarTest(
                test_name='Insulation',
                test_desc='Insulation Test',
                result_value=ins_result_value,
                results=ins_results,
                result=ins_result,
                test_threshold=ins_threshold,
            )
        else:
            ins_test = None

        records.append(SocaRecord(
            **headers,
            continuity=continuity_test,
            insulation=ins_test,
        ))
        
    return records




if __name__ == "__main__":
    fpath = r"C:\Users\Tom Dufall\Documents\soca-pat.csv"
    records = parse_records(fpath)
    from pprint import pprint
    pprint(records[1])
    print("Done!")
