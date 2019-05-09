'''
jc-split.py:
    日本語ファイルと中国語ファイルの文を単語アラインメントを利用して
    短い文（部分文）に分割する
使い方:
    $ python jc-split.py [ -l ログファイル ] アラインメントデータ 入力日本語ファイル 入力中国語ファイル 出力日本語ファイル 出力中国語ファイル
#                                logfile     alignment-file  input-language-A-file input-language-B-file output-language-A-file output-language-B-file 
History:
2018/12/30 - fullオプション使用時の短文出力処理の修正 fix the option -f 
2018/11/25 - 全角スペースの両側が漢字か仮名なら分割点として使用する fix bugs with the Japanese Full-width Space 
xx2018/11/18 - 片方が部分文に分割されない場合もログに残すように変更 (jcsplit.py) fix bugs of one-to-one corresponding sentences 
2018/10/21 - セグメントの漢字共有率を考慮するオプションを追加 (jc-split-n-cc.py) add the option of using common Chinese characters
2018/10/17 - バグ修正 (jc-split-n-v2.py) fix bugs
2018/10/05 - セグメントアラインメントの閾値オプションを追加 (jc-split-n.py)  add the option of alignment threshold
2018/05/07 - 最初のバージョン (jc-split.py)  the first version
'''
import argparse
import sys
import os

# delimiters
DELIMS = ',，;:、；：'  #（）／'
WIDE_SPACE = '\u3000'
DELIMS += WIDE_SPACE

# output threshold
DEFAULT_MINIMUM_RATE = 0.5
# Simplify Japanese Kanji
DO_SIMPLIFY = False
# Japanese Kanji -> Simplified Chaninese Character mapping file
MAPFILE = 'simple.map'
COMMON_CHAR_WEIGHT = 0.5 #1.0

global kanhan_map
kanhan_map = {}

def load_hankan_map():
    global kanhan_map
    path = os.path.dirname(os.path.abspath(__file__)) + "/" + MAPFILE
    with open(path, 'r') as f:
        for line in f:
            kanji, hanzi = line.strip().split(',')
            kanhan_map[kanji] = hanzi


def is_kanji(c):
    return c >= '\u4e00' and c <= '\u9fea'

def is_kana(c):
    return c >= '\u3040' and c <= '\u30ff'

def is_alpha(c):
    return (c >= '\uff21' and c <= '\uff3a') or \
        (c >= '\uff41' and c <= '\uff5a') or \
        (c >= 'A' and c <= 'z')

def simplify(str):
    global kanhan_map
    kanjis = [ c for c in str.strip() if is_kanji(c) ]
    chars = [ kanhan_map[c] if c in kanhan_map else c for c in kanjis ]
    return ''.join(chars).strip()


def common_char_rate(str_zh, str_ja):
    hanzi_zh = [ c for c in str_zh if is_kanji(c) ]
    hanzi_ja = [ c for c in str_ja if is_kanji(c) ]
    denom = len(hanzi_zh) + len(hanzi_ja)
    if denom == 0:
        rate = 0
    else:
        shared_hanzi = [ c for c in hanzi_zh if c in hanzi_ja ]
        num = len(shared_hanzi) * 2
        rate = num / denom

    return rate
    
def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('alignment',
                        help='alignment data')
    parser.add_argument('input_japanese_file',
                        help='input Japanese file')
    parser.add_argument('input_chinese_file',
                        help='input Chinese file')
    parser.add_argument('output_japanese_file',
                        help='output Japanese file')
    parser.add_argument('output_chinese_file',
                        help='output Chinese file')
    parser.add_argument('-l', '--log_file', required=True,
                        help='log file')
    parser.add_argument('-m', '--minimum_rate',
                        help='minimum rate')
    parser.add_argument('-s', '--simplify', action='store_true',
                        help='simplify Japanese kanjis')
    parser.add_argument('-f', '--full', action='store_true',
                        help='log all sentences')
    
    return parser.parse_args()

# ファイル名
#ALIGNMENT_FILE = 'dev-symmetrized.align'
#INPUT_JP_FILE = 'dev-ja.tok'
#INPUT_CH_FILE = 'dev-cn.tok'
#OUTPUT_JP_FILE = 'dev-ja.seg'
#OUTPUT_CH_FILE = 'dev-cn.seg'
#LOG_FILE = 'log'


class Token:
    def __init__(self, id, text, a_tokens=[], a_segment=None):
        self.id = id
        self.text = text
        self.hanzi = simplify(text)
        self.a_tokens = a_tokens    # alignment (counter part tokens)
        self.a_segment = a_segment  # counter part segment


class Segment:
    def __init__(self, id, tokens):
        self.id = id
        self.tokens = tokens
        self.segment_align_dist = {}  # counter part segments (dict)
        self.segment_alignments = []
    
    def text(self):
        token_texts = [t.text for t in self.tokens]
        return ' '.join(token_texts)

    def hanzi(self):
        hanzi_texts = [ t.hanzi for t in self.tokens ]
        return ''.join(hanzi_texts)


class Sentence:
    def __init__(self, text, delims, alignment):
        self.segments = []
        tokens = []
        segment_id = 0
        token_text_list = text.strip().split(' ')
        n_tokens = len(token_text_list)

        for i in range(n_tokens):
            token_text = token_text_list[i]
            # token alignment
            a_tokens = []
            if i in alignment:
                a_tokens = alignment[i]
            token = Token(id=i, text=token_text, a_tokens=a_tokens)

            tokens.append(token)

            if token_text in delims or (i + 1 == n_tokens):
                # end of segment
                if token_text == WIDE_SPACE:
                    if i == 0 or i == n_tokens - 1:
                        continue
                    prev_char = token_text_list[i-1][-1]
                    next_char = token_text_list[i+1][0]
                    # print(prev_char, is_alpha(prev_char), next_char, is_alpha(next_char))
                    if is_alpha(prev_char) and is_alpha(prev_char):
                        continue
                segment = Segment(id=segment_id, tokens=tokens)
                self.segments.append(segment)
                segment_id += 1
                tokens = []
    
    def segment_from_token(self, token_id):
        seg_id = None
        for seg in self.segments:
            if token_id <= seg.tokens[-1].id:
                seg_id = seg.id
                break
        return seg_id

    def calc_segment_dist(self, other_sentence, minimum_rate, do_simplify):
        for i, seg in enumerate(self.segments):
            n_tokens = 0
            for t in seg.tokens:
                if t.a_tokens:
                    # counter part exists
                    for a_token in t.a_tokens:
                        n_tokens += 1
                        other_seg = other_sentence.segment_from_token(a_token)
                        if other_seg in self.segments[i].segment_align_dist:
                            self.segments[i].segment_align_dist[other_seg] += 1
                        else:
                            self.segments[i].segment_align_dist[other_seg] = 1
            # convert 'occurence count' to 'rate'
            #n_tokens = len(seg.tokens)

            for key in self.segments[i].segment_align_dist:
                freq = self.segments[i].segment_align_dist[key]
                self.segments[i].segment_align_dist[key] = round(freq / n_tokens, 2)
            
            # add common character rate
            if do_simplify:
                hanzi1 = self.segments[i].hanzi()
                for key in self.segments[i].segment_align_dist:
                    # DEBUG
                    try:
                        hanzi2 = other_sentence.segments[key].hanzi()
                    except TypeError:
                        print('type(key):', type(key), file=sys.stderr)
                        print('hanzi1 =', hanzi1, file=sys.stderr)
                        print('key =', key, file=sys.stderr)
                        print('i =', i, file=sys.stderr)
                        print('segments[i].segment_align_dist:', self.segments[i].segment_align_dist, file=sys.stderr)
                        exit()
                    ccr = common_char_rate(hanzi1, hanzi2)
                    if ccr > 0.5:
                        self.segments[i].segment_align_dist[key] += ccr * COMMON_CHAR_WEIGHT
                
            # sort
            sorted_dist = sorted(self.segments[i].segment_align_dist.items(), \
                                    key=lambda x:x[1], reverse=True)
            self.segments[i].segment_align_dist = sorted_dist

            # 最大値のみ記録
            #if len(sorted_dist) > 0 and sorted_dist[0][1] > minimum_rate:
            #    self.segments[i].segment_alignment = sorted_dist[0][0]
            
            # minimum_rate以上の全てを記録
            for j in range(len(sorted_dist)):
                if sorted_dist[j][1] >= minimum_rate:
                    self.segments[i].segment_alignments.append(sorted_dist[j][0])

    def text(self):
        text = ''
        for seg in self.segments:
            text += seg.text()
        return text

    @classmethod
    def get_segment_pairs(cls, sentence1, sentence2):
        pairs = set()
        for seg1 in sentence1.segments:
            for a in seg1.segment_alignments:
                pairs.add((seg1.id, a))
        for seg2 in sentence2.segments:
            for a in seg2.segment_alignments:
                pairs.add((a, seg2.id))

        ordered_pairs = sorted(pairs, key=lambda x:x[0])

        segment_pairs = []
        for pair in ordered_pairs:
            used = []
            for i, seg_pair in enumerate(segment_pairs):
                if pair[0] in seg_pair[0]:
                    segment_pairs[i][1].append(pair[1])
                    used.append(i)
                elif pair[1] in seg_pair[1]:
                    segment_pairs[i][0].append(pair[0])
                    used.append(i)
            if not used:
                segment_pairs.append([[pair[0]], [pair[1]]])
            elif len(used) > 1:
                # len(used) should be 2
                assert len(used) == 2, 'len(used)={0}'.format(len(used))
                # merge pairs
                idx0 = used[0]
                idx1 = used[1]
                # segment_pairs[idx0][0] += segment_pairs[idx1][0]
                for i in segment_pairs[idx1][0]:
                    if i not in segment_pairs[idx0][0]:
                        segment_pairs[idx0][0].append(i)
                #segment_pairs[idx0][1] += segment_pairs[idx1][1]
                for i in segment_pairs[idx1][1]:
                    if i not in segment_pairs[idx0][1]:
                        segment_pairs[idx0][1].append(i)
                del segment_pairs[idx1]

        # sort
        for i in range(len(segment_pairs)):
            for j in [0, 1]:
                segment_pairs[i][j] = sorted(segment_pairs[i][j])

        return segment_pairs

    def print_segment_dist(self, file=sys.stdout):
        for seg in self.segments:
            print('{0}: {1}'.format(seg.id, seg.segment_align_dist), file=file)


def make_alignment_dicts(alignment_text):
    j2c_align = {}
    c2j_align = {}
    aligns = alignment_text.strip().split(' ')
    for pair in aligns:
        a = pair.split('-')
        if len(a) == 2:
            j = int(a[0])
            c = int(a[1])
            # 10-8 10-9 のように多対一，一対多の場合もある
            if j in j2c_align:
                j2c_align[j].append(c)
            else:
                j2c_align[j] = [c]
            if c in c2j_align:
                c2j_align[c].append(j)
            else:
                c2j_align[c] = [j]

    return j2c_align, c2j_align


def split_sentence(jp_line, ch_line, alignment_text, minimum_rate, do_simplify):
    '''
    Split sentence into sub-sentences, and return sub-sentence pairs to output
    :param jp_line: japanese tokenized sentence
    :param ch_line: chinese tokenized sentences
    :param alignment: aligment
    :return: sub-sentence pairs to output
    '''

    j2c_align, c2j_align = make_alignment_dicts(alignment_text)

    jp_sentence = Sentence(text=jp_line, delims=DELIMS, alignment=j2c_align)
    ch_sentence = Sentence(text=ch_line, delims=DELIMS, alignment=c2j_align)

    jp_sentence.calc_segment_dist(ch_sentence, minimum_rate, do_simplify)
    ch_sentence.calc_segment_dist(jp_sentence, minimum_rate, do_simplify)


    segment_pairs = Sentence.get_segment_pairs(jp_sentence, ch_sentence)

    return segment_pairs, jp_sentence, ch_sentence


if __name__ == '__main__':
    load_hankan_map()
    # TEST
    #jp_line = 'Ｙｕｋｏｎ や 北西 領域 ， Ｈｕｄｓｏｎ や Ｊａｍｅｓ 湾 ， 北部 ケベック ， ラブラドール ， グリーンランド の 汚染 物質 に関する 情報 を ， 文献 ， 組織 ， 研究 者 から 広範囲 に 収集 し た 。 '
    #ch_line = '有关 Ｙｕｋｏｎ 和 西北 领域 、 Ｈｕｄｓｏｎ 和 Ｊａｍｅｓ 湾 、 北部 魁北克 、 拉布拉多 、 Ｇｒｅｅｎｌａｎｄ 的 污染 物质 的 信息 从 文献 、 组织 、 研究者 方面 进行 了 大 范围 的 收集 。'
    #alignment_text = '0-1 1-2 2-3 3-4 4-5 5-6 6-7 7-8 8-9 9-10 10-11 11-12 12-13 13-14 13-15 14-15 15-16 16-17 17-18 18-19 19-0 20-21 21-20 22-24 23-23 24-24 25-25 26-26 27-27 27-28 28-27 29-22 30-31 30-32 32-34 33-29 33-30 34-30 35-35'

    args = get_arguments()
    minimum_rate = DEFAULT_MINIMUM_RATE
    if args.minimum_rate:
        minimum_rate = float(args.minimum_rate)
    do_simplify = False
    if args.simplify or DO_SIMPLIFY:
        do_simplify = True
    with open(args.alignment) as fin_align, \
        open(args.input_japanese_file, 'r', encoding='utf-8') as fin_jp, \
        open(args.input_chinese_file, 'r', encoding='utf-8') as fin_ch, \
        open(args.output_japanese_file, 'w', encoding='utf-8') as fout_jp, \
        open(args.output_chinese_file, 'w', encoding='utf-8') as fout_ch:

        flog = sys.stdout
        if args.log_file:
            flog = open(args.log_file, 'w', encoding='utf-8')

        sentence_no = 0
        n_split = 0
        n_not_split = 0
        n_short_sentence = 0

        while True:
            sentence_no += 1
            # DEBUG
            if sentence_no == 9: #849:
                dummy = 'same'

            alignment = fin_align.readline()
            if not alignment:
                break
            jp_line = fin_jp.readline()
            ch_line = fin_ch.readline()

            segment_pairs, jp_sentence, ch_sentence = \
                split_sentence(jp_line, ch_line, alignment, minimum_rate, do_simplify)

            if len(segment_pairs) <= 1:
                # sentence not split
                n_not_split += 1
                if not args.full:
                    continue
            else:
                n_split += 1
                n_short_sentence += len(segment_pairs)

            # DEBUG
            if flog:
                print('#{0}'.format(sentence_no), file=flog)
                print('Japanese:', jp_sentence.text(), file=flog)
                print('Chinese: ', ch_sentence.text(), file=flog)
                print('--', file=flog)
                print('J -> C', file=flog)
                jp_sentence.print_segment_dist(flog)
                print('C -> J', file=flog)
                ch_sentence.print_segment_dist(flog)

                print('Mapping:', segment_pairs, file=flog)
                print('----', file=flog)

            if len(segment_pairs) <= 1:
                continue

            segment_text_pairs = []
            for pair in segment_pairs:
                jp_segs = pair[0]
                jp_seg_text = ''
                for seg_id in jp_segs:
                    seg = jp_sentence.segments[seg_id]
                    jp_seg_text += ' ' + seg.text()
                    if flog:
                        print('J{0}: {1}'.format(seg_id, seg.text()), file=flog)
                jp_seg_text = jp_seg_text.strip()

                ch_segs = pair[1]
                ch_seg_text = ''
                for seg_id in ch_segs:
                    seg = ch_sentence.segments[seg_id]
                    ch_seg_text += ' ' + seg.text()
                    if flog:
                        print('C{0}: {1}'.format(seg_id, seg.text()), file=flog)
                ch_seg_text = ch_seg_text.strip()

                print('--', file=flog)

                segment_text_pairs.append((jp_seg_text, ch_seg_text))

            for pair in segment_text_pairs:
                print(pair[0], file=fout_jp)
                print(pair[1], file=fout_ch)
                # if flog:
                #     print('J:', pair[0], file=flog)
                #     print('C:', pair[1], file=flog)
                #     print('===========', file=flog)

            #if args.log_file:
            #    print(seg_align_jp, file=flog)
            #    if len(untranslated) > 0:
            #        print('* Untranslated segment(s):', file=flog)
            #        for s in untranslated:
            #            print(s, file=flog)
            #    print('=======', file=flog)
        print('\n{0} of {1} sentences were split into {2} short sentences.'.format(
            n_split, n_split+n_not_split, n_short_sentence), file=flog)
        if args.log_file:
            flog.close()
