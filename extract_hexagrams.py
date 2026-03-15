#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
九鬼_易経.TXT から64卦のデータをJSONとして抽出する
"""

import re
import json


def parse_hexagrams(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    text = data.decode('shift-jis', errors='replace')

    # ヘッダーパターン: 全角空白3つ以上 または 半角空白10以上
    # 例: 　　　　易経（１）乾為天(ﾃﾝ) or                     易断（５１）震為雷(ﾗｲ)
    pat = re.compile(
        r'(?:　{3,}| {10,})易[経断]（(\d+)）([^\n(【]+)(?:【[^】]*】)?\(([^)\n]+)\)',
        re.MULTILINE
    )
    matches = list(pat.finditer(text))
    print(f"Found {len(matches)} hexagram headers")

    hexagrams = {}

    for i, m in enumerate(matches):
        num = int(m.group(1))
        name = m.group(2).strip()
        reading = m.group(3).strip()

        # セクション範囲
        sec_start = m.end()
        sec_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section = text[sec_start:sec_end]

        # 爻ヘッダーパターン（文字化け・「、」省略ケースも対応）
        # 六→６(全角) / 九→９(全角) の文字化けも吸収
        SIX  = '[六６6]'   # 六 or ６(全角) or 6(半角)
        NINE = '[九９9]'   # 九 or ９(全角) or 9(半角)
        TWO  = '[二２2]'
        THREE= '[三３3]'
        FOUR = '[四４4]'
        FIVE = '[五５5]'
        yao_pat = re.compile(
            rf'^\s+(初{SIX}|初{NINE}|{SIX}{TWO}|{SIX}{THREE}|{SIX}{FOUR}|{SIX}{FIVE}'
            rf'|{NINE}{TWO}|{NINE}{THREE}|{NINE}{FOUR}|{NINE}{FIVE}|上{SIX}|上{NINE})は',
            re.MULTILINE
        )
        yms = list(yao_pat.finditer(section))

        # 全体解釈
        overall = section[:yms[0].start()].strip() if yms else section.strip()
        overall = re.sub(r'\s*\n\s*※[^\n]*(\n|$).*$', '', overall, flags=re.DOTALL).strip()

        # 全角/半角数字 → 漢字 の正規化（爻名用）
        _fw = str.maketrans('０１２３４５６７８９', '〇一二三四五六七八九')
        _hw_digit = str.maketrans('0123456789', '〇一二三四五六七八九')
        def normalize_yao_name(name):
            n = name.translate(_fw)  # 全角 → 漢字
            return n

        # 爻 位置マップ
        _pos_map = {
            '初': 0, '上': 5,
            '二': 1, '三': 2, '四': 3, '五': 4,
        }
        def yao_pos(raw_name):
            name = normalize_yao_name(raw_name)
            first = name[0]
            if first in ('初', '上'):
                return _pos_map[first]
            # 六N or 九N
            second = name[1] if len(name) > 1 else ''
            return _pos_map.get(second, -1)

        yaos = {}
        for j, ym in enumerate(yms):
            yao_name = ym.group(1)
            pos = yao_pos(yao_name)
            if pos < 0:
                continue
            end = yms[j + 1].start() if j + 1 < len(yms) else len(section)
            yao_text = section[ym.start():end].strip()
            yao_text = re.sub(r'\s*\n\s*※[^\n]*(\n|$).*$', '', yao_text, flags=re.DOTALL).strip()
            yaos[pos] = {'name': yao_name, 'text': yao_text}

        hexagrams[num] = {
            'number': num,
            'name': name,
            'reading': reading,
            'overall': overall,
            'yaos': yaos
        }

    return hexagrams


def main():
    filepath = '/Users/fujimuramasami/claude-projects/test/TEXT/九鬼_易経.TXT'
    output_path = '/Users/fujimuramasami/claude-projects/test/TEXT/hexagrams.json'

    hexagrams = parse_hexagrams(filepath)

    print(f"\nParsed {len(hexagrams)} hexagrams:")
    issues = []
    for num in sorted(hexagrams.keys()):
        h = hexagrams[num]
        yao_count = len(h['yaos'])
        status = "✓" if yao_count == 6 else f"! ({yao_count} yaos)"
        print(f"  #{num:2d} {h['name']}: overall={len(h['overall'])}ch, yaos={status}")
        if yao_count != 6:
            issues.append(num)

    # 抜けている番号チェック
    all_nums = set(range(1, 65))
    found_nums = set(hexagrams.keys())
    missing = all_nums - found_nums
    if missing:
        print(f"\nMissing hexagrams: {sorted(missing)}")
    if issues:
        print(f"Hexagrams with yao issues: {issues}")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(hexagrams, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {output_path}")
    print(f"Total: {len(hexagrams)}/64 hexagrams")


if __name__ == '__main__':
    main()
