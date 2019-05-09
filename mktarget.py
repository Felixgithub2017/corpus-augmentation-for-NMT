'''
mktarget.py: reads mixed source and sentence number, and makes target file
'''

import argparse
import sys

def getargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('target_file', help='target file')
    parser.add_argument('sentence_number_file', help='sentence number file')
    return parser.parse_args()

def main():
    args = getargs()
    with open(args.target_file, 'r', encoding='utf-8') as f:
        target_sentences = f.read().strip().split('\n')
    with open(args.sentence_number_file, 'r', encoding='utf-8') as f:
        for line in f:
            sentence_id, count = line.strip().split()
            sentence_index = int(sentence_id) - 1
            count = int(count)
            for _ in range(count):
                print(target_sentences[sentence_index])

if __name__ == '__main__':
    main()
