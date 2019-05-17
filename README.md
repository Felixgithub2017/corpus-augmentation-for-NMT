# corpus-augmentation-for-NMT

Corpus augmentation by long sentences segmentation and back-translation for NMT.

If you use the code, please cite this paper:
```
Zhang, J.; Matsumoto, T. Corpus Augmentation for Neural Machine Translation with Chinese-Japanese Parallel Corpora. Appl. Sci. 2019, 9, 2036.
```
1. use fast_align(https://github.com/clab/fast_align) to get the symmetrized.align.

For word-level, we use Mecab(http://taku910.github.io/mecab/) for Japanese and jieba(https://github.com/fxsjy/jieba) for Chinese.

Command example with language-ja and language-zh text file in word-level:

```
python3 parallelize.py -d ' ||| ' input-language-ja-file input-language-zh-file > text.ja-zh

build/fast_align -i text.ja-zh -d -o -v > forward.align

build/fast_align -i text.ja-zh -d -o -v -r > reverse.align

build/atools -i forward.align -j reverse.align -c grow-diag-final-and > symmetric.align
```

2. 
```
python3 jcsplit.py -m 0.5 -l log symmetrized.align input-language-ja-file input-language-zh-file output-language-ja-file output-language-zh-file -s 
```

option '-s' means to use the common Chinese character information.

For more details, please see the jcsplit.py file inside.

3. back-translate the output-language-zh-file with own NMT model

4. mix segments and the generate pseudo-source sentences.

```
python3 mix-segments.py --log_file log --source () --translated () --output () -n sentnum
```

The output file is the generated pseudo-source sentences.

5. extend the target-side language sentences corresponding to the generated pseudo-source language sentences

```
python3 mktarget.py input-language-ja-file sentnum > zh-mix-target
```

zh-mix-target is the extended target-side language sentences.

6. add the generated sentence pairs to the original parallel corpus

```
cat input-language-ja-file output-language-ja-file > train-ja-mixed-source

cat input-language-zh-file zh-mix-target > train-zh-extended-target 
```

Done
