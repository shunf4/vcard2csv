#!/usr/bin/env python
import vobject
import glob
import csv
import argparse
import os.path
import sys
import logging
import collections
import io
import schema
import re

RE_TEL_1 = re.compile(r'^(\d+-)+\d+$')

def func_assert(sth, msg):
    assert sth, msg

column_order = schema.SCHEMA

column_dict = dict(column_order)

def process_vcard(row):
    row_iter = iter(row)
    result = []

    for (column_prop, (column_header, column_replica_num)) in column_order:
        current_entries = []
        tels = []
        for replica_i in range(column_replica_num):
            param = next(row_iter)
            value = next(row_iter)
            if param == "" and value == "":
                if column_prop == "TEL":
                    pass
                else:
                    current_entries.append(param)
                    current_entries.append(value)
            else:
                if column_prop == "FN":
                    fn = value
                    current_entries.append(param)
                    current_entries.append(value)
                elif column_prop == "N":
                    full_name = "".join(value.split(";"))
                    if full_name.strip() == "":
                        full_name = fn
                    value = ";" + full_name + ";;;"
                    current_entries.append(param)
                    current_entries.append(value)
                elif column_prop == "TEL":
                    tels.append((param, value))
                else:
                    current_entries.append(param)
                    current_entries.append(value)

        if column_prop == "TEL":
            tels.sort(key=lambda x: len(x[1]))

            tels_str = repr(tels)

            for replica_i in range(column_replica_num):
                if replica_i >= len(tels):
                    current_entries.append("")
                    current_entries.append("")
                    continue

                (param, value) = tels[replica_i]
                if RE_TEL_1.fullmatch(value):
                    value = value.replace("-", "")
                    current_entries.append(param)
                    current_entries.append(value)
                else:
                    print(f"TEL: other phone no.s: {tels_str}")
                    replaced = input(f"enter formatted phone no. for {value}: ")
                    if replaced == "":
                        current_entries.append(param)
                        current_entries.append(value)
                    else :
                        current_entries.append(param)
                        current_entries.append(replaced)
                

        result.extend(current_entries)
            
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Convert a single csv file to a bunch of vCard (.vcf) files.'
    )
    parser.add_argument(
        'input_csv_file',
        type=argparse.FileType('rb'),
        help='Input file'
    )
    parser.add_argument(
        'output_csv_file',
        type=argparse.FileType('wb'),
        help='Output file',
    )
    parser.add_argument(
        '-i',
        '--info',
        help='Logging with more info',
        dest="loglevel",
        default=logging.WARNING,
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        '-d',
        '--debug',
        help='Enable debugging logs',
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
    )
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)

    wrapped_input = io.TextIOWrapper(args.input_csv_file, encoding="utf-8-sig", newline="")
    reader = csv.reader(wrapped_input, dialect='excel', delimiter=',')

    wrapped_output = io.TextIOWrapper(args.output_csv_file, encoding="utf-8-sig", newline="")
    writer = csv.writer(wrapped_output, dialect='excel', delimiter=',')

    column_order_in_csv = []
    for column_prop, (column_header, column_replica_num) in column_order:
        for replica_i in range(column_replica_num):
            column_order_in_csv.append(column_header + ("" if column_replica_num <= 1 else f"{replica_i + 1}") + "_param")
            column_order_in_csv.append(column_header + ("" if column_replica_num <= 1 else f"{replica_i + 1}") + "_value")

    writer.writerow(column_order_in_csv)

    next(reader)
    for row in reader:
        vcard_info = process_vcard(row)
        writer.writerow(vcard_info)
    
    wrapped_output.close()
    wrapped_input.close()
    args.output_csv_file.close()
    args.input_csv_file.close()
