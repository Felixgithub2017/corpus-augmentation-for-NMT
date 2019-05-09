# parallelize: 原言語と目的言語のファイルを1つの対訳TSVファイルにまとめる
# Usage: python parallelize source target

import argparse

def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', help='source language file')
    parser.add_argument('target', help='target language file')
    parser.add_argument('-d', '--delimiter', default='\t',
                        help='delimiter (default: "\t")')
    return parser.parse_args()

def main():
    args = get_arguments()
    delim = '\t'
    if args.delimiter:
        delim = args.delimiter
    with open(args.source, 'r') as fsrc, \
         open(args.target, 'r') as ftgt:
        for src_line, tgt_line in zip(fsrc, ftgt): 
            src_line = src_line.strip()
            tgt_line = tgt_line.strip()
            par_line = src_line + delim + tgt_line
            print(par_line)

if __name__ == '__main__':
    main()
