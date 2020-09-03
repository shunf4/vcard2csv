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

column_dict = dict(column_order)

def get_info_list(vcard_filepath):
    vcard = {}
    with open(vcard_filepath, encoding="utf-8") as fp:
        vcard_text = fp.read()
    vcard_vobj = vobject.readOne(vcard_text)
    vcard_vobj.validate()
    
    splitted = vcard_text.replace("\n ", "").replace("\n\t", "").splitlines()
    line_i = -1
    line_num = len(splitted)
    for line in splitted:
        line_i += 1
        if line_i == 0:
            if line.upper() != "BEGIN:VCARD":
                raise ValueError(f'line.upper() != "BEGIN:VCARD" in {vcard_filepath}')
            continue
        elif line_i == 1:
            if line.upper() != "VERSION:3.0":
                raise ValueError(f'line.upper() != "VERSION:3.0" in {vcard_filepath}')
            continue
        elif line_i == line_num - 1:
            if line.upper() != "END:VCARD":
                raise ValueError(f'line.upper() != "END:VCARD" in {vcard_filepath}')
            continue
        
        line_splitted = line.split(":")
        if len(line_splitted) < 2:
            raise ValueError(f'len(line_splitted) < 2 in {vcard_filepath}')

        prop_param = line_splitted[0].strip()
        value = ''.join(line_splitted[1:]).strip()
        
        prop_param_splitted = prop_param.split(";")
        prop = prop_param_splitted[0].split(".")[-1].upper()
        param = "".join(list(map(lambda x:";" + (lambda y:(func_assert(len(y) == 2, 'len(y) == 2 failed'), y[0].upper() + "=" + y[1])[1])(x.split("=")), prop_param_splitted[1:])))
        
        if prop in column_dict:
            if prop == "UID":
                if (value + ".vcf").lower() != os.path.basename(vcard_filepath).lower():
                    logging.warning(f"UID in content doesn't match that in file name({value}) in {vcard_filepath}")

            vcard[prop] = vcard.get(prop, [])
            vcard[prop].append((param, value))
        else:
            logging.warning(f"unsupported property {prop} in {vcard_filepath}")

    ordered_vcard_info = []
    for column_prop, (column_header, column_replica_num) in column_order:
        current_prop_list = vcard.get(column_prop, [])
        if len(current_prop_list) > column_replica_num:
            logging.warning(f"insufficient prop {column_prop} capacity {column_replica_num}(needed {len(current_prop_list)}) in {vcard_filepath}")
        for replica_i in range(column_replica_num):
            if replica_i < len(current_prop_list):
                (current_param, current_value) = current_prop_list[replica_i]
            else:
                (current_param, current_value) = ("", "")
            ordered_vcard_info.append(current_param)
            ordered_vcard_info.append(current_value)

    return ordered_vcard_info

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
        description='Convert a bunch of vCard (.vcf) files to a single csv file.'
    )
    parser.add_argument(
        'read_dir',
        type=readable_directory,
        help='Directory to read vCard files from.'
    )
    parser.add_argument(
        'csv_file',
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

    vcard_pattern = os.path.join(args.read_dir, "*.vcf")
    vcards = sorted(glob.glob(vcard_pattern))
    if len(vcards) == 0:
        logging.error("no files ending with `.vcf` in directory `{}'".format(args.read_dir))
        sys.exit(2)
    else:
        print(f"{len(vcards)} files")

    wrapped = io.TextIOWrapper(args.csv_file, encoding="utf-8-sig", newline="")
    writer = csv.writer(wrapped, dialect='excel', delimiter=',')

    column_order_in_csv = []
    for column_prop, (column_header, column_replica_num) in column_order:
        for replica_i in range(column_replica_num):
            column_order_in_csv.append(column_header + ("" if column_replica_num <= 1 else f"{replica_i + 1}") + "_param")
            column_order_in_csv.append(column_header + ("" if column_replica_num <= 1 else f"{replica_i + 1}") + "_value")

    writer.writerow(column_order_in_csv)

    for i, vcard_path in enumerate(vcards):
        vcard_info = get_info_list(vcard_path)
        writer.writerow(vcard_info)
    
    wrapped.close()
    args.csv_file.close()
