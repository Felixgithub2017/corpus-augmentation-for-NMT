import argparse
import sys

LOG_FILE = 'train/log50'
SRC_SHORT_SENTENCE_FILE = 'train/train-zh-short50.char'
TRANSLATED_TGT_SHORT_SENTENCE_FILE = 'train/train-ja2zh-short50.char'

global translated_segments
translated_segments = []


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--log_file', required=True,
                        help='Input log file')
    parser.add_argument('-s', '--source', required=True,
                        help='Source short sentence file')
    parser.add_argument('-t', '--translated', required=True,
                        help='Translated target short sentence file')
    parser.add_argument('-o', '--output',
                        help='Output file')
    parser.add_argument('-n', '--number', required=True,
                        help='sentence ID and number of short sentences')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Debug mode')
    parser.add_argument('-r', '--reverse', action='store_true',
                        help='from Chinese to Japanese')
    return parser.parse_args()


def split_numbers(s):
    if ',' in s:
        numbers = s.split(',')
        return [ int(c) for c in numbers]
    else:
        return [ int(s) ]


def check_continuous_ascending_order(l):
    # リストの要素が昇順かつ連続か確認する
    dummy = list(range(l[-1]+1))
    result = (l == dummy)
    return  result
    # result = True
    # prev = -1
    # for num in l:
    #     if num <= prev:
    #         result = False
    #         break
    #     prev = num
    # return result


def is_complicated(mapping_list):
    '''
    不連続か，順序が入れ替わるようなマッピングならTrueを返す
    '''
    complicated = False
    left = []
    right = []
    for pair in mapping_list:
        left += pair[0]
        right += pair[1]
    if not check_continuous_ascending_order(left) or \
            not check_continuous_ascending_order(right):
        complicated = True
    return complicated


def parse_mapping_text(mapping_text, reverse):
    '''
    "[[[0], [0]], [[1], [1,2]], [[2,3], [3]]]" のような文字列をリストに変換する
    '''
    line = mapping_text
    mapping_list = []
    while len(line) > 8:
        left_bracket = line.find('[[')
        right_bracket = line.find(']]')
        if left_bracket < 0 or right_bracket < 0:
            # 終了
            break
        line = line[line.index('[[')+2:]
        left = split_numbers((line[:line.index(']')]))
        line = line[line.index(']')+2:]
        right = split_numbers((line[line.index('[')+1:line.index(']')]))
        line = line[line.index(']]')+3:]
        if reverse:
            # chinese to japanese
            mapping_list.append((right, left))
        else:
            # japanese to chinese
            mapping_list.append((left, right))
    return mapping_list


def get_mappings_from_log(log_file, reverse):
    # セグメントの対応をlogファイルから取得する
    mappings_list = []
    with open(log_file, 'r', encoding='utf-8') as flog:
        for line in flog:
            line = line.strip()
            if line.startswith('#'):
                sentence_id = int(line[1:])
                continue
            if line.startswith('Mapping:'):
                mapping_text = line[10:-1].strip()
                mappings = parse_mapping_text(mapping_text, reverse)
                mappings_list.append((sentence_id, mappings))
    return mappings_list


def read_translated_segments(trans_seg_file):
    global translated_segments
    with open(trans_seg_file, 'r', encoding='utf-8') as f:
        translated_segments = f.read().strip().split('\n')


def mix_sentences(sentence_pairs, fout, debug_mode):
    ''' 一部を機械翻訳結果と入れ替える '''
    for i in range(len(sentence_pairs)):
        for j in range(len(sentence_pairs)):
            # j番目のショートセンテンスを入れ替える
            if i == j:
                # 対応する中国語文の日本語訳
                if debug_mode:
                    print('【', end='', file=fout)
                print(sentence_pairs[j][1], end=' ', file=fout)
                if debug_mode:
                    print('】', end=' ', file=fout)
            else:
                # 元の日本語文
                print(sentence_pairs[j][0], end=' ', file=fout)
        print(file=fout)


def main():
    global translated_segments

    args = get_arguments()
    if args.log_file:
        log_file = args.log_file
    else:
        log_file = LOG_FILE
    
    if args.source:
        source_short_file = args.source
    else:
        source_short_file = SRC_SHORT_SENTENCE_FILE
    
    if args.translated:
        trans_short_file = args.translated
    else:
        trans_short_file = TRANSLATED_TGT_SHORT_SENTENCE_FILE

    if args.output:
        fout = open(args.output, 'w')
    else:
        fout = sys.stdout

    if args.number:
        fnum = open(args.number, 'w')
    else:
        fnum = sys.stderr
        
    mappings_list = get_mappings_from_log(log_file, args.reverse)
    
    id_nshort_pairs = []

    with open(source_short_file, 'r', encoding='utf-8') as f_src, \
         open(trans_short_file, 'r', encoding='utf-8') as f_trn:
        comp_count = 0
        for (sentence_id, mappings) in mappings_list:
            n_short_sentences = len(mappings)
            complicated = is_complicated(mappings)
            if complicated:
                # skip if segment alignment is complicated
                for _ in range(n_short_sentences):
                    src_short_sentence = f_src.readline().strip()
                    trn_short_sentence = f_trn.readline().strip()
                comp_count += 1
            else:
                id_nshort_pairs.append((sentence_id, n_short_sentences))
                sentence_pairs = []
                for _ in range(n_short_sentences):
                    src_short_sentence = f_src.readline().strip()
                    trn_short_sentence = f_trn.readline().strip()
                    sentence_pairs.append((src_short_sentence, trn_short_sentence))               
                mix_sentences(sentence_pairs, fout, args.debug)
    print('Number of removed sentences:', comp_count)

    for sentence_id, n_short_sentences in id_nshort_pairs:
        print('{0} {1}'.format(sentence_id, n_short_sentences), file=fnum)
    

if __name__ == '__main__':
    main()
