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

def func_assert(sth, msg):
    assert sth, msg

column_order = schema.SCHEMA

column_order_remap = list(map(lambda x: (x[1][0], (x[0], x[1][1])), column_order))

column_dict = dict(column_order)

def create_vcard(row):
    sio = io.StringIO(newline="\n")
    sio.writelines(["BEGIN:VCARD\n", "VERSION:3.0\n"])
    row_iter = iter(row)
    for (column_prop, (column_header, column_replica_num)) in column_order:
        for replica_i in range(column_replica_num):
            param = next(row_iter)
            value = next(row_iter)
            if param == "" and value == "":
                continue
            sio.write(f"{column_prop}{param}:{value}\n")
            
    sio.writelines(["END:VCARD\n"])
    vcard_text = sio.getvalue()
    sio.close()

    vcard_vobj = vobject.readOne(vcard_text)
    vcard_vobj.validate()
    
    return (vcard_vobj.uid.value, vcard_text)

def readable_directory(path):
    if not os.path.isdir(path):
        raise argparse.ArgumentTypeError(
            'not an existing directory: {}'.format(path))
    if not os.access(path, os.R_OK):
        raise argparse.ArgumentTypeError(
            'not a readable directory: {}'.format(path))
    return path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Convert a single csv file to a bunch of vCard (.vcf) files.'
    )
    parser.add_argument(
        'input_csv_file',
        type=argparse.FileType('rb'),
        help='Input file',
    )
    parser.add_argument(
        'write_dir',
        type=readable_directory,
        help='Directory to write vCard files to.'
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

    next(reader)
    for row in reader:
        (uid, text) = create_vcard(row)
        with open(os.path.join(args.write_dir, f"{uid}.vcf"), "w", encoding="utf-8", newline="\r\n") as f:
            f.write(text)

